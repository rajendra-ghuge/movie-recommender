from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from app.db import get_db_connection, pwd_context

router = APIRouter()

class UserAuth(BaseModel):
    username: str
    password: str

@router.post("/signup")
def signup(user_auth: UserAuth):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    hashed_password = pwd_context.hash(user_auth.password)
    
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                       (user_auth.username, hashed_password))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return {"id": user_id, "username": user_auth.username, "message": "User created successfully"}
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=400, detail="Username already exists or invalid data")

@router.post("/login")
def login(user_auth: UserAuth):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE username = ?", (user_auth.username,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    if not pwd_context.verify(user_auth.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    return {"id": user["id"], "username": user["username"], "message": "Login successful"}
