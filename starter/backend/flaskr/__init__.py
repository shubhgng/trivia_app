from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_cors import CORS
import random
import os
from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE
    questions = [question.format() for question in selection]
    current_question = questions[start:end]
    return current_question


def create_app(test_config=None):
    app = Flask(__name__)
    setup_db(app)

    '''
    Set up CORS. Allow '*' for origins. Delete the
    sample route after completing the TODOs
    '''
    cors = CORS(app, resource={r"/api/*": {"origins": "*"}})

    '''
    Use the after_request decorator to set Access-Control-Allow
    '''
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow_Methods',
                             'GET, POST, PATCH, DELETE, OPTIONS')
        return response

    '''
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of
    the screen for three pages.Clicking on the page numbers
    should update the questions.
    '''

    @app.route('/questions', methods=['GET'])
    def get_questions():
        selection = Question.query.all()
        questions_paginated = paginate_questions(request, selection)

        if len(questions_paginated) == 0:
            abort(404)

        categories = Category.query.all()
        formatted_categories = [category.format() for category in categories]
        returned_categories = [category['type'] for category
                               in formatted_categories]

        return jsonify({
            'success': True,
            'questions': questions_paginated,
            'total_questions': len(selection),
            'categories': returned_categories,
            'current categories': None
        })

    '''
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question,
    the question will be removed.This removal will persist in
    the database and when you refresh the page.
    '''
    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_questions(question_id):
        question = Question.query.filter(
                    Question.id == question_id).one_or_none()

        if not question:
            abort(404)

        try:
            question.delete()
            selection = Question.query.order_by(Question.id).all()
            current_question = paginate_questions(request, selection)

            return jsonify({
                'success': True,
                'deleted': question_id,
                'questions': current_question,
                'total_books': len(Question.query.all())
            })
        except e:
            abort(422)

    '''
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.
    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at
    the end of the last page of the questions list in the
    "List" tab
    '''

    @app.route('/questions', methods=['POST'])
    def create_questions():
        body = request.get_json()

        if not body:
            abort(400)
        else:
            new_question = body.get('question', None)
            new_answer = body.get('answer', None)
            new_category = body.get('category', None)
            new_difficulty = body.get('difficulty', None)

        if not new_question:
            abort(400)

        if not new_answer:
            abort(400)

        if not new_category:
            abort(400)

        if not new_difficulty:
            abort(400)

        try:
            question = Question(
                    question=new_question,
                    answer=new_answer,
                    category=new_category,
                    difficulty=new_difficulty,
                    )
            question.insert()

            questions = Question.query.all()
            formatted_questions = [question.format() for question in questions]

            return jsonify({
                'success': True,
                'created': question.id,
                'questions': formatted_questions,
                'total_questions': len(formatted_questions),
                })
        except e:
            abort(422)

    '''
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    curl command: curl http://127.0.0.1:5000/questions/search -X POST -H
    "Content-Type: application/json" -d '{"searchTerm":"which"}'

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    '''

    @app.route('/questions/search', methods=['POST'])
    def search_question():
        body = request.get_json()

        if not body:
            abort(400)

        search_term = body.get('searchTerm', None)
        questions = Question.query.filter(
                    Question.question.ilike('%{}%'.format(search_term))).all()

        if not questions:
            abort(404)

        questions_found = [question.format() for question in questions]
        selections = Question.query.order_by(Question.id).all()

        categories = Category.query.all()
        formatted_categories = [category.format() for category in categories]
        returned_categories = [cat['type'] for cat in formatted_categories]

        return jsonify({
            'success': True,
            'questions': questions_found,
            'total_questions': len(selections),
            'categories': returned_categories
        })

    # Create an endpoint to handle GET requests for all available categories.

    @app.route('/categories', methods=['GET'])
    def get_categories():
        categories = Category.query.all()

        if not categories:
            abort(404)

        categories_all = [category.format() for category in categories]

        length = len(categories_all)
        categories = {}
        for i in range(length):
            temp = categories_all[i]
            categories[temp['id']] = temp['type']

        return jsonify({
            'success': True,
            'categories': categories
        })

    '''
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    '''

    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def retrieve_questions_by_category(category_id):
        try:
            questions = Question.query.filter(
                    Question.category == str(category_id+1)).all()

            return jsonify({
                'success': True,
                'questions': [question.format() for question in questions],
                'total_questions': len(questions),
                'current_category': category_id
            })

        except e:
            abort(404)

    '''
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    '''

    @app.route('/quizzes', methods=['POST'])
    def play_quiz():
        try:
            body = request.get_json()
            if not ('quiz_category' in body and 'previous_questions' in body):
                abort(422)

            category = body.get('quiz_category')
            previous_questions = body.get('previous_questions')

            if category['type'] == 'click':
                available_questions = Question.query.filter(
                        Question.id.notin_((previous_questions))).all()
            else:
                available_questions = Question.query.filter_by(
                        category=category['id']).filter(Question.id.notin_((
                            previous_questions))).all()
                new_question = available_questions[random.randrange(
                        0, len(available_questions))].format() if len(
                            available_questions) > 0 else None
            return jsonify({
                'success': True,
                'question': new_question
            })
        except NameError:
            abort(422)

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "Not found"
            }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "bad request"
        }), 400

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            "success": False,
            "error": 405,
            "message": "method not allowed"
        }), 405

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "internal server error"
        }), 500
    return app
