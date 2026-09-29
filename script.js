// Online Library Management System - LocalStorage Based

// ==================== KEY CONSTANTS ====================
const STORAGE_USERS = 'library_users';
const STORAGE_CURRENT_USER = 'library_current_user';
const STORAGE_ISSUED_BOOKS = 'library_issued_books';

// ==================== SAMPLE DATA ====================
const sampleBooks = [
    {
        id: 'book-001',
        title: 'Introduction to Algorithms',
        author: 'Thomas H. Cormen',
        isbn: '978-0262033848',
        category: 'Computer Science',
        totalCopies: 5,
        availableCopies: 4,
        description: 'Comprehensive introduction to modern computer algorithms'
    },
    {
        id: 'book-002',
        title: 'Clean Code',
        author: 'Robert C. Martin',
        isbn: '978-0132350884',
        category: 'Software Engineering',
        totalCopies: 3,
        availableCopies: 0,
        description: 'Handbook of elegant code'
    },
    {
        id: 'book-003',
        title: 'Design Patterns',
        author: 'Gang of Four',
        isbn: '978-0201633610',
        category: 'Software Engineering',
        totalCopies: 8,
        availableCopies: 6,
        description: 'Essential guide to design patterns'
    },
    {
        id: 'book-004',
        title: 'The Art of Computer Programming',
        author: 'Donald E. Knuth',
        isbn: '978-0321751041',
        category: 'Computer Science',
        totalCopies: 6,
        availableCopies: 3,
        description: 'Classic programming reference'
    },
    {
        id: 'book-005',
        title: 'Database System Concepts',
        author: 'Abraham Silberschatz',
        isbn: '978-0073523323',
        category: 'Database',
        totalCopies: 4,
        availableCopies: 2,
        description: 'Comprehensive database textbook'
    }
];

// ==================== USER FUNCTIONS ====================

// Initialize users in localStorage if empty
function initUsers() {
    const users = localStorage.getItem(STORAGE_USERS);
    if (!users) {
        // Sample users for testing
        const defaultUsers = [
            { id: 'user-001', firstName: 'John', lastName: 'Doe', email: 'john@university.edu', studentId: '2024001234', role: 'student', password: 'password123' },
            { id: 'user-002', firstName: 'Sarah', lastName: 'Johnson', email: 'sarah@library.edu', studentId: 'LIB001', role: 'librarian', password: 'admin123' },
            { id: 'user-003', firstName: 'Alice', lastName: 'Brown', email: 'alice@university.edu', studentId: '2024005678', role: 'student', password: 'password123' }
        ];
        localStorage.setItem(STORAGE_USERS, JSON.stringify(defaultUsers));
    }
}

// Register a new user
function registerUser(formData) {
    initUsers();
    
    const users = JSON.parse(localStorage.getItem(STORAGE_USERS) || '[]');
    
    // Check if email or student ID already exists
    const emailExists = users.some(user => user.email === formData.email);
    const studentIdExists = users.some(user => user.studentId === formData.studentId);
    
    if (emailExists) {
        return { success: false, message: 'Email already registered' };
    }
    
    if (studentIdExists) {
        return { success: false, message: 'Student ID already exists' };
    }
    
    const newUser = {
        id: 'user-' + Date.now(),
        ...formData,
        createdAt: new Date().toISOString()
    };
    
    users.push(newUser);
    localStorage.setItem(STORAGE_USERS, JSON.stringify(users));
    
    return { success: true, message: 'Registration successful!' };
}

// Login user
function login_user(email, password) {
    initUsers();
    
    const users = JSON.parse(localStorage.getItem(STORAGE_USERS) || '[]');
    
    const user = users.find(u => u.email === email && u.password === password);
    
    if (user) {
        localStorage.setItem(STORAGE_CURRENT_USER, JSON.stringify(user));
        return { success: true, user: user };
    }
    
    return { success: false, message: 'Invalid email or password' };
}

// Get current logged in user
function getCurrentUser() {
    const user = localStorage.getItem(STORAGE_CURRENT_USER);
    return user ? JSON.parse(user) : null;
}

// Logout current user
function logout() {
    localStorage.removeItem(STORAGE_CURRENT_USER);
    return true;
}

// Check if user is logged in
function isLoggedIn() {
    return !!getCurrentUser();
}

// ==================== BOOK FUNCTIONS ====================

// Get all books
function getBooks() {
    const books = localStorage.getItem(STORAGE_ISSUED_BOOKS);
    if (!books) {
        localStorage.setItem(STORAGE_ISSUED_BOOKS, JSON.stringify(sampleBooks));
        return sampleBooks;
    }
    return JSON.parse(books);
}

// Get book by ID
function getBookById(bookId) {
    const books = getBooks();
    return books.find(book => book.id === bookId);
}

// Get available books
function getAvailableBooks() {
    const books = getBooks();
    return books.filter(book => book.availableCopies > 0);
}

// ==================== ISSUE/RETURN FUNCTIONS ====================

// Issue a book to current user
function issueBook(bookId, userId) {
    const books = getBooks();
    const bookIndex = books.findIndex(book => book.id === bookId);
    
    if (bookIndex === -1) {
        return { success: false, message: 'Book not found' };
    }
    
    if (books[bookIndex].availableCopies <= 0) {
        return { success: false, message: 'No copies available' };
    }
    
    // Decrement available copies
    books[bookIndex].availableCopies--;
    localStorage.setItem(STORAGE_ISSUED_BOOKS, JSON.stringify(books));
    
    // Save issue record
    saveIssueRecord(bookId, userId);
    
    return { 
        success: true, 
        message: 'Book issued successfully',
        dueDate: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toLocaleDateString()
    };
}

// Save issue record
function saveIssueRecord(bookId, userId) {
    let issuedBooks = JSON.parse(localStorage.getItem('library_user_issues_' + userId) || '[]');
    
    issuedBooks.push({
        bookId: bookId,
        issueDate: new Date().toISOString(),
        dueDate: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString(),
        returnDate: null,
        fine: 0
    });
    
    localStorage.setItem('library_user_issues_' + userId, JSON.stringify(issuedBooks));
}

// Get issued books for current user
function getIssuedBooks() {
    const currentUser = getCurrentUser();
    if (!currentUser) return [];
    
    const issuedBooks = JSON.parse(localStorage.getItem('library_user_issues_' + currentUser.id) || '[]');
    
    // Enrich with book details
    return issuedBooks.map(issue => ({
        ...issue,
        book: getBookById(issue.bookId)
    })).filter(issue => issue.book && issue.returnDate === null);
}

// Return a book
function returnBook(issueId, userId) {
    const issuedBooks = JSON.parse(localStorage.getItem('library_user_issues_' + userId) || '[]');
    const issueIndex = issuedBooks.findIndex(issue => issue.id === issueId);
    
    if (issueIndex === -1) {
        return { success: false, message: 'Issue record not found' };
    }
    
    const issue = issuedBooks[issueIndex];
    const books = getBooks();
    const bookIndex = books.findIndex(book => book.id === issue.bookId);
    
    if (bookIndex === -1) {
        return { success: false, message: 'Book not found' };
    }
    
    // Increment available copies
    books[bookIndex].availableCopies++;
    localStorage.setItem(STORAGE_ISSUED_BOOKS, JSON.stringify(books));
    
    // Mark as returned
    issuedBooks[issueIndex].returnDate = new Date().toISOString();
    localStorage.setItem('library_user_issues_' + userId, JSON.stringify(issuedBooks));
    
    return { success: true, message: 'Book returned successfully' };
}

// Calculate fine for overdue book (assuming $0.50 per day)
function calculateFine(dueDate) {
    const due = new Date(dueDate);
    const today = new Date();
    
    if (today <= due) return 0;
    
    const daysOverdue = Math.floor((today - due) / (1000 * 60 * 60 * 24));
    return daysOverdue * 0.50;
}

// Initialize sample data
initUsers();