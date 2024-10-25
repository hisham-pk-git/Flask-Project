from flask import Flask, request, jsonify, render_template, url_for, redirect, make_response
import jwt
import datetime
from flask_mysqldb import MySQL
import MySQLdb.cursors
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = '14a0458f42584319bdeed320286f6dd5'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'flask-midterm'

mysql = MySQL(app)

@app.route('/')
def hello_world():
    return 'Hello, World!'

def protected_route(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-token')
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 403
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            if data.get('role') != 'admin':
                return jsonify({'message': 'Admin access required!'}), 403
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!'}), 401
        
        return f(*args, **kwargs)
    
    return decorated

@app.route('/get-users', methods=['GET'])
def get_users():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM test")
    data = cur.fetchall()
    cur.close()
    return jsonify({'users':data})

@app.route('/login', methods=['POST'])
def login():
    auth = request.get_json()

    if auth and auth.get('username') == 'admin' and auth.get('password') == 'password':
        token = jwt.encode({
            'username': auth['username'],
            'role': 'admin',
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)  # Token expires in 30 minutes
        }, app.config['SECRET_KEY'], algorithm='HS256')

        return jsonify({'token': token})

    return jsonify({'message': 'Invalid credentials!'}), 401

@app.route('/update-book', methods=['PUT'])

@app.route('/add-book', methods=['POST'])
@protected_route
def add_book():
    cur = mysql.connection.cursor()
    data = request.get_json()
    cur.execute("INSERT INTO books (id, name, description) VALUES (%s, %s, %s)", (data['id'], data['name'], data['description']))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Book added!', 'data': data})





if __name__ == '__main__':
    app.run(debug=True)