from flask import Flask, request, jsonify, render_template, url_for, redirect, make_response
import jwt
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = '14a0458f42584319bdeed320286f6dd5'

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/login', methods=['POST'])
def login():
    auth = request.get_json()

    if auth and auth.get('username') == 'admin' and auth.get('password') == 'password':
        token = jwt.encode({
            'username': auth['username'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)  # Token expires in 30 minutes
        }, app.config['SECRET_KEY'], algorithm='HS256')

        return jsonify({'token': token})

    return jsonify({'message': 'Invalid credentials!'}), 401

@app.route('/protected', methods=['GET'])
def protected():
    token = request.headers.get('Authorization')

    if not token:
        return jsonify({'message': 'Token is missing!'}), 403

    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return jsonify({'message': f'Welcome, {data["username"]}!'})
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token has expired!'}), 403
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid token!'}), 403


if __name__ == '__main__':
    app.run(debug=True)