import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    '''
    Set up CORS. Allow '*' for origins.
    '''
    CORS(app, resources={'/': {'origins': '*'}})

    '''
    Useing the after_request decorator to set Access-Control-Allow
    '''

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PATCH,POST,DELETE,OPTIONS')
        return response

    ''' 
    Create an endpoint to handle GET requests 
    for all available categories.
    '''

    @app.route('/categories')
    def retrieve_categories():
        current_categories = Category.query.all()

        if len(current_categories) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'categories':
                {category.id : category.type for category in current_categories}
        })

    '''
    Create an endpoint to handle GET requests for questions, 
    including pagination (every 10 questions). 
    This endpoint should return a list of questions, 
    number of total questions, current category, categories. 
    '''

    @app.route('/questions')
    def retrieve_questions():
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)

        current_categories = Category.query.all()

        if len(current_questions) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(selection),
            'categories': {category.id : category.type for category in current_categories},
            'currentCategory': None
        })

    '''
    Create an endpoint to DELETE question using a question ID. 
    '''

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()
            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify({
                'success': True,
                'deleted': question_id,
                'questions': current_questions,
                'total_questions': len(Question.query.all())
            })

        except:
            abort(422)

    '''
    Create an endpoint to POST a new question, 
    which will require the question and answer text, 
    category, and difficulty score. 
    '''

    @app.route('/questions', methods=['POST'])
    def create_question():
        body = request.get_json()

        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_category = body.get('category', None)
        new_difficulty = body.get('difficulty', None)

        try:
            question = Question(question=new_question, answer=new_answer, category=new_category,
                                difficulty=new_difficulty)
            question.insert()

            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify({
                'success': True,
                'created': question.id,
                'questions': current_questions,
                'total_questions': len(Question.query.all())
            })

        except:
            abort(422)

    '''
    Create a POST endpoint to get questions based on a search term. 
    It should return any questions for whom the search term 
    is a substring of the question.  
    '''

    @app.route('/questions/search', methods=['POST'])
    def search_questions():
        body = request.get_json()
        search_term = body.get('searchTerm')
        try:
            selection = Question.query.filter(
                Question.question.ilike(f'%{search_term}%')).all()

            if len(selection) == 0:
                abort(404)

            paginated_questions = paginate_questions(request, selection)

            return jsonify({
                'success': True,
                'questions': paginated_questions,
                'total_questions': len(selection)
            })
        except:
            abort(404)

    '''
    Create a GET endpoint to get questions based on category.
    '''

    @app.route('/categories/<int:category_id>/questions')
    def retrieve_questions_by_category(category_id):
        try:
            selection = Question.query.filter(Question.category == category_id).all()

            return jsonify({
                'success': True,
                'questions': [question.format() for question in selection],
                'total_questions': len(selection),
                'current_category': category_id
            })
        except:
            abort(404)

    '''
    Create a POST endpoint to get questions to play the quiz. 
    This endpoint should take category and previous question parameters 
    and return a random questions within the given category, 
    if provided, and that is not one of the previous questions. 
    '''

    @app.route('/quizzes', methods=['POST'])
    def play_quiz():
        try:
            body = request.get_json()
            quiz_category = body.get('quiz_category')
            previous_questions = body.get('previous_questions')

            if (quiz_category is None) or (previous_questions is None):
                abort(400)

            if quiz_category['id'] == 0:
                questions = Question.query.all()
            else:
                questions = Question.query.filter_by(category=quiz_category['id']).all()

            def get_random_question():
                return questions[random.randint(0, len(questions) - 1)]
            next_question = get_random_question()

            for next_question.id in previous_questions:
                continue

            return jsonify({
                'success': True,
                'question': next_question.format()
            })
        except:
            abort(422)

    '''
    Create error handlers for all expected errors 
    including 404, 422, 400 and 500. 
    '''

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

    @app.errorhandler(500)
    def server_error(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "internet server error"
        }), 500

    return app
