import os
from datetime import timedelta

# Secret key for JWT encoding/decoding. In production, use a secure key and store it safely.
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# This is a simple in-memory user store. In a real application, you'd use a database.
users_db = {
    "testuser": {"username": "testuser", "password": "testpass"},
    "kavya@montaigne.co": {"username": "kavya@montaigne.co", "password": "kavya@msbs"},
    "media@montaigne.co": {"username": "media@montaigne.co", "password": "media@msbs"},
    "rohith@montaigne.co": {"username": "rohith@montaigne.co", "password": "rohith@msbs"}
}