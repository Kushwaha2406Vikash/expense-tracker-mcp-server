import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()
client: AsyncIOMotorClient | None = None
db = None

async def get_db():
    global client, db

    if db is not None:
        return db

    mongo_uri = os.getenv("MONGODB_URI")
    if not mongo_uri:
        raise RuntimeError("MONGODB_URI environment variable not set")

    client = AsyncIOMotorClient(
        mongo_uri,
        maxPoolSize=20,      # 🔥 handles concurrent requests
        minPoolSize=5
    )

    db = client["expense_tracker"]
   # print("Database connect Successfully") 
    return db

