from flask import Flask, request, jsonify, render_template, url_for, redirect, make_response
import jwt
import datetime
from flask_mysqldb import MySQL
import MySQLdb.cursors
from functools import wraps
import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = '14a0458f42584319bdeed320286f6dd5'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'flask-midterm'

mysql = MySQL(app)

# Configurations
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit file size to 16MB
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'jpg', 'jpeg', 'png'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Utility function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

@app.route('/add-book', methods=['POST'])
def add_book():
    cur = mysql.connection.cursor()
    data = request.get_json()
    cur.execute("INSERT INTO books (id, name, description) VALUES (%s, %s, %s)", (data['id'], data['name'], data['description']))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Book added!', 'data': data})

@app.route('/get-books', methods=['GET'])
def get_books():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM books")
    data = cur.fetchall()
    cur.close()
    return jsonify({'books':data})

@app.route('/get-book/<int:id>', methods=['GET'])
def get_book(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM books WHERE id = %s", (id,))
    data = cur.fetchall()
    cur.close()
    if not data:
        # Return 404 error if no book is found
        return jsonify({"error": f"Book with ID {id} not found"}), 404
    return jsonify({'book':data})

@app.route('/update-book/<int:id>', methods=['PUT'])
@protected_route
def update_book(id):
    cur=mysql.connection.cursor()
    # First, check if the book with the given ID exists
    cur.execute("SELECT * FROM books WHERE id = %s", (id,))
    existing_book = cur.fetchall()
    
    if not existing_book:
        cur.close()
        return jsonify({"error": f"Book with ID {id} not found"}), 404
    data = request.get_json()
    cur.execute("UPDATE books SET name = %s, description = %s WHERE id = %s", (data['name'], data['description'], id))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Book updated!', 'data': data})

@app.route('/delete-book/<int:id>', methods=['DELETE'])
@protected_route
def delete_book(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM books WHERE id = %s", (id,))
    existing_book = cur.fetchall()
    
    if not existing_book:
        cur.close()
        return jsonify({"error": f"Book with ID {id} not found"}), 404
    cur.execute("DELETE FROM books WHERE id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Book deleted!'})

# Upload endpoint
@app.route('/upload-file', methods=['POST'])
def upload_file():
    # Check if the request contains the file part
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']

    # Check if the file has a valid filename
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Check if the file type is allowed
    if file and allowed_file(file.filename):
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        try:
            cur = mysql.connection.cursor()
            cur.execute(
                "INSERT INTO uploaded_files (filepath, uploaded_time) VALUES (%s, %s)",
                (filepath, datetime.datetime.now())
            )
            mysql.connection.commit()
            cur.close()
        except Exception as e:
            mysql.connection.rollback()
            return jsonify({"error": "Failed to save file info in the database", "details": str(e)}), 500

        return jsonify({"message": "File uploaded and info saved successfully!"}), 201

    return jsonify({"error": "File type not allowed"}), 400

# Error handler for files that exceed the size limit
@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({"error": "File is too large. Maximum allowed size is 16 MB."}), 413





if __name__ == '__main__':
    app.run(debug=True)