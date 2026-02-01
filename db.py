import os
from pymongo import MongoClient

client = None
db = None

def get_db():
    global client, db

    if db is not None:
        return db

    mongo_uri = os.getenv("MONGODB_URI")

    if not mongo_uri:
        raise RuntimeError("MONGODB_URI environment variable not set")

    client = MongoClient(mongo_uri)
    db = client["expense_tracker"]

    return db
