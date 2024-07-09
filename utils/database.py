from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os
from datetime import datetime
import httpx  # Ensure httpx is imported

# Load environment variables from .env file
load_dotenv()

# Get the MongoDB URI from environment variables
uri = os.getenv("MONGO_URI")
print(f"MongoDB URI: {uri}")  # Verify the loaded URI

if not uri:
    raise ValueError("MONGO_URI environment variable not set.")

# Create a new client and connect to the server
try:
    client = MongoClient(uri, server_api=ServerApi('1'))
    db = client['orange_strategy_db']
    chats_collection = db['chats']

    # Send a ping to confirm a successful connection
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    raise

def sanitize_chat_data(data):
    """Sanitize chat data by removing non-serializable objects."""
    if isinstance(data, dict):
        sanitized_data = {}
        for key, value in data.items():
            sanitized_data[key] = sanitize_chat_data(value)
        return sanitized_data
    elif isinstance(data, list):
        return [sanitize_chat_data(item) for item in data]
    elif isinstance(data, (str, int, float, bool, type(None))):
        return data
    elif isinstance(data, httpx.AsyncClient):
        return "AsyncClient object removed"  # Example handling for AsyncClient objects
    else:
        return str(data)  # Convert non-serializable objects to string

def save_chat(industry, client_name, purpose, messages):
    chat_document = {
        'industry': industry,
        'client': client_name,
        'purpose': purpose,
        'messages': sanitize_chat_data(messages),
        'timestamp': datetime.utcnow()
    }
    try:
        result = chats_collection.insert_one(chat_document)
        print(f"Chat saved with ID: {result.inserted_id}")
        return result.inserted_id
    except Exception as e:
        print(f"Error saving chat: {e}")
        return None

def get_recent_chats(industry, client_name, purpose, limit=5):
    try:
        chats = list(chats_collection.find(
            {'industry': industry, 'client': client_name, 'purpose': purpose},
            sort=[('timestamp', -1)],
            limit=limit
        ))
        print(f"Retrieved {len(chats)} chats")
        return chats
    except Exception as e:
        print(f"Error retrieving recent chats: {e}")
        return []
