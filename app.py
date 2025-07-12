from flask import Flask, request, jsonify, session, redirect, render_template
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = '42b3e56fa34b98cf62e29da2f09a5c41be04dc5e3fd2aeec8761f9431c44b9f0'
CORS(app, supports_credentials=True)

DB_FILE = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# Auto-create table if not exists
def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return redirect('/signup')

@app.route('/signup')
@app.route('/signup.html')
def signup():
    return render_template('signup.html')

@app.route('/api/register', methods=['POST'])
def register():
    full_name = request.form.get('fullName')
    phone = request.form.get('phone', '').strip().replace('+234', '')
    address = request.form.get('address')
    nin_number = request.form.get('ninNumber')
    password = request.form.get('password')
    nin_photo = request.files.get('ninPhoto')

    if not all([full_name, phone, address, nin_number, password, nin_photo]):
        return jsonify({'success': False, 'message': 'All fields are required'}), 400

    if not nin_photo.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        return jsonify({'success': False, 'message': 'Invalid image file'}), 400

    uploads_folder = os.path.join(os.getcwd(), 'uploads')
    os.makedirs(uploads_folder, exist_ok=True)
    photo_path = os.path.join(uploads_folder, f"{phone}_{nin_photo.filename}")
    nin_photo.save(photo_path)

    try:
        conn = get_db_connection()
        conn.execute("INSERT INTO users (phone, password) VALUES (?, ?)", (phone, password))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Registered successfully'})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'message': 'Phone already registered'}), 409

@app.route('/api/signin', methods=['POST'])
def signin():
    data = request.json
    phone = data.get('phone', '').strip().replace('+234', '')
    password = data.get('password', '').strip()

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE phone = ?", (phone,)).fetchone()
    conn.close()

    if user and password == user['password']:
        session['signed_in'] = True
        session['phone'] = phone
        session['login_time'] = datetime.now().isoformat()
        return jsonify({'success': True, 'message': 'Signed in'})
    else:
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out'})
    
@app.route('/index')
@app.route('/index.html')  # Catch direct .html too
def index():
    return render_template('index.html')

  
@app.route('/signin')
@app.route('/signin.html')
def signin_page():
    return render_template('signin.html')
    
@app.route('/api/session', methods=['GET'])
def session_check():
    if session.get('signed_in'):
        return jsonify({'signed_in': True, 'phone': session.get('phone')})
    else:
        return jsonify({'signed_in': False})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)