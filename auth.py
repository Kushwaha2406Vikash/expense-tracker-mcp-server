import hashlib 
from fastmcp.server.dependencies import get_http_headers
from db import users 


def get_user():
    headers = get_http_headers() 
    
    token = headers.get("secrete")  


    if not token:
        raise Exception("API_KEY not found in environment")

    hashed = hashlib.sha256(token.encode()).hexdigest()

    user = users.find_one({
        "api_key_hash": hashed,
        "is_active": True
    })

    if not user:
        raise Exception("Invalid API Key")

    return user["_id"] 