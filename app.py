from flask import Flask, request, jsonify, render_template, url_for, redirect, make_response
import jwt

app = Flask(__name__)
app.config['SECRET_KEY'] = '14a0458f42584319bdeed320286f6dd5'

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/login', methods=['POST'])
def login():
    auth = request.get_json()
    if auth and auth['username'] == 'admin' and auth['password'] == 'password':
        token = jwt.encode({'user': auth['username'],
                            'password': auth['password']}, app.config['SECRET_KEY'])  
        return jsonify({'token': token})
    
    return jsonify({'error': 'Invalid username or password'}), 401

@app.route('/protected', methods=['GET'])
def protected():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': 'Token is missing'}), 401
    
    try:
        data = jwt.decode(token, app.config['SECRET_KEY'])
        return jsonify({'message': f'Hello, {data["username"]}'}, 200)
    except:
        return jsonify({'error': 'Token is invalid'}), 403


if __name__ == '__main__':
    app.run(debug=True)