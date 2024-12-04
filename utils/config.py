# utils/config.py

import os
from datetime import timedelta
from pinecone import Pinecone, ServerlessSpec
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Secret key for JWT encoding/decoding. In production, use a secure key and store it safely.
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OpenAI Client Initialization
openai_api_key = os.getenv('OPENAI_API_KEY')
client = openai.OpenAI(api_key=openai_api_key)

# This is a simple in-memory user store. In a real application, you'd use a database.
users_db = {
    "testuser": {"username": "testuser", "password": "testpass"},
    "kavya@montaigne.co": {"username": "kavya@montaigne.co", "password": "kavya@msbs"},
    "media@montaigne.co": {"username": "media@montaigne.co", "password": "media@msbs"},
    "rohith@montaigne.co": {"username": "rohith@montaigne.co", "password": "rohith@msbs"},
    "moksh@montaigne.co": {"username": "moksh@montaigne.co", "password": "moksh@msbs"},
    "kharvannan@montaigne.co": {"username": "kharvannan@montaigne.co", "password": "kharvannan@msbs"},
    "jahnavi@montaigne.co": {"username": "jahnavi@montaigne.co", "password": "jahnavi@msbs"},
    "kshiti@montaigne.co": {"username": "kshiti@montaigne.co", "password": "kshiti@msbs"},
}


# Ensure the Pinecone index is created
pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
index_name = 'muniverse'

# Ensure Pinecone index exists or create it
if index_name not in pc.list_indexes().names():
    pc.create_index(name=index_name, dimension=1536, metric='cosine', spec=ServerlessSpec(cloud='aws', region='us-west-2'))
index = pc.Index(f"{index_name}")
