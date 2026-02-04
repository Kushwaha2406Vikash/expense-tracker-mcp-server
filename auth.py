
import hashlib
from fastmcp.server.dependencies import get_http_headers
from db import get_db


async def get_user():
    db = await get_db()
    users = db["users"]

    headers = get_http_headers()  # OK (sync, cheap)

    auth = headers.get("authorization")
   # print(auth)

    if not auth or not auth.startswith("Bearer "):
        raise Exception("Authorization header missing or invalid")

    token = auth.split(" ", 1)[1].strip()

    hashed = hashlib.sha256(token.encode()).hexdigest()

    user = await users.find_one({  # 🔥 CHANGED (await added)
        "api_key_hash": hashed,
        "is_active": True
    })

    if not user:
        raise Exception("Invalid API Key")

    return str(user["_id"]) 
