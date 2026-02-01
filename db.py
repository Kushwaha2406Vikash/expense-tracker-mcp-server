import os
from pymongo import MongoClient 
from dotenv import load_dotenv 

load_dotenv()



try:
    # Create client (SYNC)
    client = MongoClient(os.getenv("MONGODB_URI"))

    # Select DB & collection
    db = client["expense_tracker"]
    users = db["users"]   
    expense=db["expense"]

except Exception as e:
    raise Exception(f"The following error occurred: {e}")
