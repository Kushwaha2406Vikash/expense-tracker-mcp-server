from fastmcp import FastMCP 
from auth import get_user

from db import get_db
from bson import ObjectId 
from prompt import guide 
import os

mcp = FastMCP("ExpenceTracker") 

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CATEGORIES_PATH = os.path.join(BASE_DIR, "resources", "categories.json")
OPERATION_PATH  = os.path.join(BASE_DIR, "resources", "operation.json") 



@mcp.prompt() 
def llmPrompt():
    return guide() 

@mcp.tool()
def add_expense(date:str,amount:float,category:str,subcategory="",note=""):
    db = get_db()
    expense = db["expense"]
    user_id = get_user()
    
    if not user_id:
        raise Exception("User Not found! API Key Invalid")

    
    result = expense.insert_one({
        "user_id": user_id,
        "date": date,
        "amount": float(amount),
        "category": category,
        "subcategory": subcategory,
        "note": note
    })

    return {
        "status": "ok",
        "message": "Item add Successfully",
        
    }


@mcp.tool()
def list_expenses(start_date, end_date):
    db = get_db()
    expense = db["expense"]

    user_id = get_user()
    cursor = expense.find(
        {
            "user_id": user_id,
            "date": {"$gte": start_date, "$lte": end_date}
        }
    ).sort("date", -1)

    return [
        {
            "expense_id": str(d["_id"]),   
            "date": d["date"],
            "amount": d["amount"],
            "category": d["category"],
            "subcategory": d.get("subcategory", ""),
            "note": d.get("note", "")
        }
        for d in cursor
    ]

# ---------------- SUMMARIZE ----------------
@mcp.tool()
def summarize_expense(start_date, end_date, category=None):
    db = get_db()
    expense = db["expense"]
    user_id = get_user()

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

    result = expense.aggregate(pipeline)

    return [
        {
            "category": doc["_id"],
            "total_amount": doc["total_amount"]
        }
        for doc in result
    ]


@mcp.tool()
def edit_expense(expense_id,date=None,amount=None,category=None,subcategory=None,note=None):
    db = get_db()
    expense = db["expense"] 
    user_id = get_user()
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

    result = expense.update_one(
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
        "message": "Item Update Successfully"
    }


@mcp.tool()
def delete_expense(expense_id):
    db = get_db()
    expense = db["expense"]
    user_id = get_user()

    try:
        expense_obj_id = ObjectId(expense_id)
    except Exception:
        return {"error": "Invalid expense_id format"}

    result = expense.delete_one(
        {
            "_id": expense_obj_id,
            "user_id": user_id   
        }
    )

    if result.deleted_count == 0:
        return {"error": "Expense not found or not authorized"}

    return {
        "status": "Success",
        "message": "Item Deleted Successfully"
    }



@mcp.resource("expense:///categories", mime_type="application/json")
def get_categories_data():

    try:
        # Provide default categories if file doesn't exist
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
            with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            import json
            return json.dumps(default_categories, indent=2)
    except Exception as e:
        return f'{{"error": "Could not load categories: {str(e)}"}}'
    

@mcp.resource("expense:///expense_operation", mime_type="application/json")
def expense_operation():
    try:
        with open(OPERATION_PATH, "r", encoding="utf-8") as f:
            return f.read()
    
    except Exception as e:
        return f'{{"error": "Could not load categories: {str(e)}"}}'      


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)

