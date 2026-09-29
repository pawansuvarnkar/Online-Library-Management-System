from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

DATABASE = 'library.db'

def get_db_connection():
    """Create a database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with required tables."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            student_id TEXT UNIQUE NOT NULL,
            role TEXT NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create issued_books table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS issued_books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            issue_date TEXT NOT NULL,
            due_date TEXT NOT NULL,
            return_date TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Create books table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            isbn TEXT NOT NULL,
            category TEXT NOT NULL,
            total_copies INTEGER NOT NULL,
            available_copies INTEGER NOT NULL,
            description TEXT
        )
    ''')
    
    # Insert sample books if not exists
    sample_books = [
        ('book-001', 'Introduction to Algorithms', 'Thomas H. Cormen', '978-0262033848', 'Computer Science', 5, 4, 'Comprehensive introduction to modern computer algorithms'),
        ('book-002', 'Clean Code', 'Robert C. Martin', '978-0132350884', 'Software Engineering', 3, 0, 'Handbook of elegant code'),
        ('book-003', 'Design Patterns', 'Gang of Four', '978-0201633610', 'Software Engineering', 8, 6, 'Essential guide to design patterns'),
        ('book-004', 'The Art of Computer Programming', 'Donald E. Knuth', '978-0321751041', 'Computer Science', 6, 3, 'Classic programming reference'),
        ('book-005', 'Database System Concepts', 'Abraham Silberschatz', '978-0073523323', 'Database', 4, 2, 'Comprehensive database textbook')
    ]
    
    for book in sample_books:
        cursor.execute('''
            INSERT OR IGNORE INTO books (id, title, author, isbn, category, total_copies, available_copies, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', book)
    
    # Insert sample users if not exists
    sample_users = [
        ('John', 'Doe', 'john@university.edu', '2024001234', 'student', 'password123'),
        ('Sarah', 'Johnson', 'sarah@library.edu', 'LIB001', 'librarian', 'admin123'),
        ('Alice', 'Brown', 'alice@university.edu', '2024005678', 'student', 'password123')
    ]
    
    for user in sample_users:
        cursor.execute('''
            INSERT OR IGNORE INTO users (first_name, last_name, email, student_id, role, password)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', user)
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        
        if user and user['password'] == password:
            session['user_id'] = user['id']
            session['user_email'] = user['email']
            session['user_role'] = user['role']
            
            if user['role'] == 'librarian':
                return redirect(url_for('librarian_dashboard'))
            return redirect(url_for('dashboard'))
        
        flash('Invalid email or password', 'error')
        return redirect(url_for('login'))
    
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form.get('firstName')
        last_name = request.form.get('lastName')
        email = request.form.get('email')
        student_id = request.form.get('studentId')
        role = request.form.get('role')
        password = request.form.get('password')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if email or student_id already exists
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        if cursor.fetchone():
            conn.close()
            flash('Email already registered', 'error')
            return redirect(url_for('register'))
        
        cursor.execute('SELECT id FROM users WHERE student_id = ?', (student_id,))
        if cursor.fetchone():
            conn.close()
            flash('Student ID already exists', 'error')
            return redirect(url_for('register'))
        
        # Insert new user
        cursor.execute('''
            INSERT INTO users (first_name, last_name, email, student_id, role, password)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (first_name, last_name, email, student_id, role, password))
        
        conn.commit()
        conn.close()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_email', None)
    session.pop('user_role', None)
    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session.get('user_role') == 'librarian':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get user info
    cursor.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    
    # Get issued books for this user
    cursor.execute('''
        SELECT * FROM issued_books 
        WHERE user_id = ? AND return_date IS NULL
    ''', (session['user_id'],))
    issued_books = cursor.fetchall()
    
    # Get all books
    cursor.execute('SELECT * FROM books')
    books = cursor.fetchall()
    
    conn.close()
    
    return render_template('dashboard.html', 
                          user=dict(user) if user else None, 
                          issued_books=[dict(book) for book in issued_books],
                          books=[dict(book) for book in books])


@app.route('/librarian-dashboard')
def librarian_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session.get('user_role') != 'librarian':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get user info
    cursor.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    
    # Get stats
    cursor.execute('SELECT COUNT(*) as count FROM users')
    total_users = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) as count FROM books')
    total_books = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) as count FROM issued_books WHERE return_date IS NULL')
    books_issued = cursor.fetchone()['count']
    
    conn.close()
    
    return render_template('librarian-dashboard.html', 
                          user=dict(user) if user else None,
                          total_users=total_users,
                          total_books=total_books,
                          books_issued=books_issued,
                          total_fines=0)


@app.route('/catalog')
def catalog():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session.get('user_role') == 'librarian':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get user info
    cursor.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    
    # Get books
    available_only = request.args.get('available') == 'true'
    if available_only:
        cursor.execute('SELECT * FROM books WHERE available_copies > 0')
    else:
        cursor.execute('SELECT * FROM books')
    
    books = cursor.fetchall()
    conn.close()
    
    return render_template('catalog.html', 
                          user=dict(user) if user else None, 
                          books=[dict(book) for book in books],
                          available_only=available_only)


@app.route('/book/<book_id>')
def book_details(book_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session.get('user_role') == 'librarian':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get user info
    cursor.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    
    # Get book
    cursor.execute('SELECT * FROM books WHERE id = ?', (book_id,))
    book = cursor.fetchone()
    conn.close()
    
    if not book:
        return redirect(url_for('catalog'))
    
    return render_template('book-details.html', user=dict(user) if user else None, book=dict(book))


@app.route('/borrow/<book_id>', methods=['POST'])
def borrow_book(book_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session.get('user_role') == 'librarian':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get user
    cursor.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    
    # Get book
    cursor.execute('SELECT * FROM books WHERE id = ?', (book_id,))
    book = cursor.fetchone()
    
    if not book or book['available_copies'] <= 0:
        conn.close()
        return redirect(url_for('catalog'))
    
    # Check if user already has this book
    cursor.execute('''
        SELECT * FROM issued_books 
        WHERE user_id = ? AND book_id = ? AND return_date IS NULL
    ''', (user['id'], book_id))
    
    if cursor.fetchone():
        conn.close()
        return redirect(url_for('catalog'))
    
    # Issue book
    cursor.execute('''
        INSERT INTO issued_books (book_id, user_id, issue_date, due_date, return_date)
        VALUES (?, ?, ?, ?, ?)
    ''', (book_id, user['id'], '2026-09-28', '2026-10-12', None))
    
    # Update available copies
    cursor.execute('UPDATE books SET available_copies = available_copies - 1 WHERE id = ?', (book_id,))
    
    conn.commit()
    conn.close()
    
    return redirect(url_for('catalog'))


@app.route('/return/<issue_id>', methods=['POST'])
def return_book(issue_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session.get('user_role') == 'librarian':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get issue
    cursor.execute('SELECT * FROM issued_books WHERE id = ?', (issue_id,))
    issue = cursor.fetchone()
    
    if not issue or issue['user_id'] != session['user_id']:
        conn.close()
        return redirect(url_for('dashboard'))
    
    # Update return date
    cursor.execute('''
        UPDATE issued_books SET return_date = ? WHERE id = ?
    ''', ('2026-09-28', issue_id))
    
    # Update available copies
    cursor.execute('UPDATE books SET available_copies = available_copies + 1 WHERE id = ?', (issue['book_id'],))
    
    conn.commit()
    conn.close()
    
    return redirect(url_for('dashboard'))


@app.route('/librarian/catalog')
def librarian_catalog():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session.get('user_role') != 'librarian':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get user info
    cursor.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    
    # Get books
    cursor.execute('SELECT * FROM books')
    books = cursor.fetchall()
    conn.close()
    
    return render_template('librarian-catalog.html', 
                          user=dict(user) if user else None, 
                          books=[dict(book) for book in books])


# Initialize database on startup
with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(debug=True)