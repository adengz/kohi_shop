from flask import Flask, request, jsonify, abort
import json
from flask_cors import CORS

from .database.models import db, db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
# db_drop_and_create_all()

# ROUTES

@app.route('/drinks', methods=['GET'])
def get_all_drinks():
    drinks = Drink.query.order_by(Drink.id).all()
    return jsonify({'success': True, 'drinks': [d.short() for d in drinks]})


@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail(payload):
    drinks = Drink.query.order_by(Drink.id).all()
    return jsonify({'success': True, 'drinks': [d.long() for d in drinks]})


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def add_drink(payload):
    data = request.get_json()
    drink = Drink()
    try:
        drink.title = data['title']
        drink.recipe = json.dumps(data['recipe'])
    except KeyError:
        abort(400)

    try:
        drink.insert()
    except:
        db.session.rollback()
        abort(500)
    return jsonify({'success': True, 'drinks': [drink.long()]})


@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(payload, id):
    drink = Drink.query.get(id)
    if not drink:
        abort(404)

    data = request.get_json()
    try:
        drink.title = data['title']
        drink.recipe = json.dumps(data['recipe'])
    except KeyError:
        abort(400)

    try:
        drink.update()
    except:
        db.session.rollback()
        abort(500)
    return jsonify({'success': True, 'drinks': [drink.long()]})

'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload, id):
    drink = Drink.query.get(id)
    if not drink:
        abort(404)

    try:
        drink.delete()
    except:
        abort(500)
    return jsonify({'success': True, 'delete': id})


# Error Handling

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        'success': False,
        'error': 422,
        'message': 'Unprocessable'
    }), 422


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 404,
        'message': 'Not found'
    }), 404


@app.errorhandler(500)
def server_error(error):
    return jsonify({
        'success': False,
        'error': 500,
        'message': 'Internal server error'
    }), 500


@app.errorhandler(AuthError)
def auth_error(ex):
    response = {'success': False}
    response.update(ex.error)
    return jsonify(response), ex.status_code
