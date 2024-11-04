from flask import Flask, request, jsonify
import jwt
import datetime
from flask_mysqldb import MySQL
from functools import wraps
import datetime
import os
from error_handlers import handle_400, handle_401, handle_403, handle_404, handle_413, handle_500

app = Flask(__name__)

# Register error handlers
app.register_error_handler(400, lambda e: handle_400(e))
app.register_error_handler(401, lambda e: handle_401(e))
app.register_error_handler(403, lambda e: handle_403(e))
app.register_error_handler(404, lambda e: handle_404(e))
app.register_error_handler(413, lambda e: handle_413(e))
app.register_error_handler(500, lambda e: handle_500(e))

#Database connection Configurations
app.config['SECRET_KEY'] = '14a0458f42584319bdeed320286f6dd5'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'flask-midterm'

mysql = MySQL(app)

# File Uppload Configurations
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit file size to 16MB
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'jpg', 'jpeg', 'png'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Utility function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Protected route decorator to check if the request has a valid token and the role is admin
def protected_route(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Check if the request has a token in the header
        token = request.headers.get('x-access-token')
        
        if not token:
            return handle_403(error_msg="Token is missing!")
        
        try:
            # Decode the token and check if the role is admin
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            if data.get('role') != 'admin':
                return handle_403(error_msg="Admin access required!")
        except jwt.ExpiredSignatureError:
            return handle_401(error_msg="Token has expired!")
        except jwt.InvalidTokenError:
            return handle_401(error_msg="Invalid token!")
        
        return f(*args, **kwargs)
    
    return decorated

#Login endpoint to generate token for the admin
@app.route('/login', methods=['POST'])
def login():
    auth = request.get_json()
    # Check if the username and password are correct for the admin against the database
    curr = mysql.connection.cursor()
    if auth:
        curr.execute("SELECT * FROM users WHERE username = %s AND password = %s", (auth['username'], auth['password']))
    
    if curr.rowcount > 0:
        token = jwt.encode({
            'username': auth['username'],
            'role': 'admin',
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)  # Token expires in 30 minutes
        }, app.config['SECRET_KEY'], algorithm='HS256')

        return jsonify({'token': token})

    return handle_401(error_msg="Invalid credentials!")

#Public endpoint: Add book endpoint to add a book to the database
@app.route('/add-book', methods=['POST'])
def add_book():
    cur = mysql.connection.cursor()
    data = request.get_json()
    cur.execute("INSERT INTO books (id, name, description) VALUES (%s, %s, %s)", (data['id'], data['name'], data['description']))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Book added!', 'data': data})

#Public endpoint: Get books endpoint to get all books from the database
@app.route('/get-books', methods=['GET'])
def get_books():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM books")
    data = cur.fetchall()
    cur.close()
    return jsonify({'books':data})

#Public endpoint: Get book endpoint to get a book by ID from the database
@app.route('/get-book/<int:id>', methods=['GET'])
def get_book(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM books WHERE id = %s", (id,))
    data = cur.fetchall()
    cur.close()
    if not data:
        # Return 404 error if no book is found
        return handle_404(error_msg=f"Book with ID {id} not found")
    return jsonify({'book':data})

#Protected endpoint: Update book endpoint to update a book by ID in the database. Only the admin can update the book details
@app.route('/update-book/<int:id>', methods=['PUT'])
@protected_route
def update_book(id):
    cur=mysql.connection.cursor()
    # First, check if the book with the given ID exists
    cur.execute("SELECT * FROM books WHERE id = %s", (id,))
    existing_book = cur.fetchall()
    
    if not existing_book:
        cur.close()
        return handle_404(error_msg=f"Book with ID {id} not found")
    data = request.get_json()
    cur.execute("UPDATE books SET name = %s, description = %s WHERE id = %s", (data['name'], data['description'], id))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Book updated!', 'data': data})

#Protected endpoint: Delete book endpoint to delete a book by ID from the database. Only the admin can delete the book
@app.route('/delete-book/<int:id>', methods=['DELETE'])
@protected_route
def delete_book(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM books WHERE id = %s", (id,))
    existing_book = cur.fetchall()
    
    if not existing_book:
        cur.close()
        return handle_404(error_msg=f"Book with ID {id} not found")
    cur.execute("DELETE FROM books WHERE id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Book deleted!'})

# Upload endpoint
@app.route('/upload-file', methods=['POST'])
def upload_file():
    # Check if the request contains the file part
    if 'file' not in request.files:
        return handle_400(error_msg="No file part")

    file = request.files['file']

    # Check if the file has a valid filename
    if file.filename == '':
        return handle_400(error_msg="No selected file")

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
            return handle_500(error_msg=f"Failed to save file info in the database. Details: {str(e)}")

        return jsonify({"message": "File uploaded and info saved successfully!"}), 201
    return handle_400(error_msg="File type not allowed")

if __name__ == '__main__':
    app.run(debug=True)