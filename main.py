
from fastmcp import FastMCP
from auth import get_user
from fastmcp.dependencies import Depends
from db import get_db
from bson import ObjectId
from prompt import guide
import os
import json
import asyncio  

mcp = FastMCP("ExpenceTracker")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CATEGORIES_PATH = os.path.join(BASE_DIR, "resources", "categories.json")
OPERATION_PATH = os.path.join(BASE_DIR, "resources", "operation.json")


@mcp.prompt()
def llmPrompt():
    return guide()


# =========================
# ADD EXPENSE
# =========================
@mcp.tool()
async def add_expense(
    date: str,
    amount: float,
    category: str,
    subcategory="",
    note="",
    user_id: str = Depends(get_user)
):
    db = await get_db()
    expense = db["expense"]

    if not user_id:
        raise Exception("User Not found! API Key Invalid")

    await expense.insert_one({  # 🔥 CHANGED (await)
        "user_id": user_id,
        "date": date,
        "amount": float(amount),
        "category": category,
        "subcategory": subcategory,
        "note": note
    })

    return {
        "status": "ok",
        "message": "Item added successfully"
    }


# =========================
# LIST EXPENSES
# =========================
@mcp.tool()
async def list_expenses(start_date:str, end_date:str, user_id: str = Depends(get_user)):
    db = await get_db()
    expense = db["expense"]

    cursor = expense.find(
        {
            "user_id": user_id,
            "date": {"$gte": start_date, "$lte": end_date}
        }
    ).sort("date", -1)

    documents = await cursor.to_list(length=None)  

    return [
        {
            "expense_id": str(d["_id"]),
            "date": d["date"],
            "amount": d["amount"],
            "category": d["category"],
            "subcategory": d.get("subcategory", ""),
            "note": d.get("note", "")
        }
        for d in documents  # 🔥 CHANGED (cursor → documents)
    ]


# =========================
# SUMMARIZE EXPENSE
# =========================
@mcp.tool()
async def summarize_expense(
    start_date:str,
    end_date:str,
    category=None,
    user_id: str = Depends(get_user),
):
    db = await get_db()
    expense = db["expense"]

    match_stage = {
        "user_id": user_id,
        "date": {"$gte": start_date, "$lte": end_date}
    }

    if category:
        match_stage["category"] = category

    pipeline = [
        {"$match": match_stage},
        {
            "$group": {
                "_id": "$category",
                "total_amount": {"$sum": "$amount"}
            }
        },
        {"$sort": {"_id": 1}}
    ]

    cursor = expense.aggregate(pipeline)
    results = await cursor.to_list(length=None)  

    return [
        {
            "category": doc["_id"],
            "total_amount": doc["total_amount"]
        }
        for doc in results
    ]


# =========================
# EDIT EXPENSE
# =========================
@mcp.tool()
async def edit_expense(
    expense_id,
    date=None,
    amount=None,
    category=None,
    subcategory=None,
    note=None,
    user_id: str = Depends(get_user)
):
    db = await get_db()
    expense = db["expense"]

    try:
        expense_obj_id = ObjectId(expense_id)
    except Exception:
        return {"error": "Invalid expense_id format"}

    update_fields = {}

    if date is not None:
        update_fields["date"] = date
    if amount is not None:
        update_fields["amount"] = float(amount)
    if category is not None:
        update_fields["category"] = category
    if subcategory is not None:
        update_fields["subcategory"] = subcategory
    if note is not None:
        update_fields["note"] = note

    if not update_fields:
        return {"error": "No fields provided to update"}

    result = await expense.update_one(  
        {
            "_id": expense_obj_id,
            "user_id": user_id
        },
        {"$set": update_fields}
    )

    if result.matched_count == 0:
        return {"error": "Expense not found or not authorized"}

    return {
        "status": "updated",
        "message": "Item updated successfully"
    }


# =========================
# DELETE EXPENSE
# =========================
@mcp.tool()
async def delete_expense(expense_id, user_id: str = Depends(get_user)):
    db = await get_db()
    expense = db["expense"]

    try:
        expense_obj_id = ObjectId(expense_id)
    except Exception:
        return {"error": "Invalid expense_id format"}

    result = await expense.delete_one({  # 🔥 CHANGED
        "_id": expense_obj_id,
        "user_id": user_id
    })

    if result.deleted_count == 0:
        return {"error": "Expense not found or not authorized"}

    return {
        "status": "success",
        "message": "Item deleted successfully"
    }


# =========================
# RESOURCES (NON-BLOCKING FILE IO)
# =========================
@mcp.resource("expense:///categories", mime_type="application/json")
async def get_categories_data():
    default_categories = {
        "categories": [
            "Food & Dining",
            "Transportation",
            "Shopping",
            "Entertainment",
            "Bills & Utilities",
            "Healthcare",
            "Travel",
            "Education",
            "Business",
            "Other"
        ]
    }

    try:
        return await asyncio.to_thread(  
            lambda: open(CATEGORIES_PATH, "r", encoding="utf-8").read()
        )
    except FileNotFoundError:
        return json.dumps(default_categories, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.resource("expense:///expense_operation", mime_type="application/json")
async def expense_operation():
    try:
        return await asyncio.to_thread(  
            lambda: open(OPERATION_PATH, "r", encoding="utf-8").read()
        )
    except Exception as e:
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)
