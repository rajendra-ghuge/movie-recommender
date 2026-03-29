import sqlite3
import os
from passlib.context import CryptContext

# Database file path
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "movies.db")

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    # Ensure data directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)
    
    # Create interactions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS interactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        movie_id INTEGER NOT NULL,
        action TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)
    
    # Check if default admin exists
    cursor.execute("SELECT * FROM users WHERE username = ?", ("admin@gmail.com",))
    if not cursor.fetchone():
        hashed_password = pwd_context.hash("123456")
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("admin@gmail.com", hashed_password))
        print("Default admin user created: admin@gmail.com / 123456")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
