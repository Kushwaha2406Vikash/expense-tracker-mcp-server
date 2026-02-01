import hashlib
from fastmcp.server.dependencies import get_http_headers
from db import get_db

def get_user():
    db = get_db()
    users = db["users"]

    headers = get_http_headers()

    auth = headers.get("authorization")  

    if not auth or not auth.startswith("Bearer "):
        raise Exception("Authorization header missing or invalid")

    token = auth.split(" ", 1)[1].strip()

    hashed = hashlib.sha256(token.encode()).hexdigest()

    user = users.find_one({
        "api_key_hash": hashed,
        "is_active": True
    })

    if not user:
        raise Exception("Invalid API Key")

    return user["_id"]
