from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel
from app.db import get_db_connection

router = APIRouter()

class Interaction(BaseModel):
    user_id: int
    movie_id: int
    action: str

@router.post("/track")
def track_interaction(interaction: Interaction):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Check if the EXACT SAME action exists
        cursor.execute("""
            SELECT id FROM interactions 
            WHERE user_id = ? AND movie_id = ? AND action = ?
        """, (interaction.user_id, interaction.movie_id, interaction.action))
        
        existing = cursor.fetchone()
        
        if existing:
            # TOGGLE OFF: If it exists, remove it
            cursor.execute("DELETE FROM interactions WHERE id = ?", (existing["id"],))
            conn.commit()
            conn.close()
            return {"status": "success", "message": f"Interaction {interaction.action} removed (Toggle Off)"}

        # 2. MUTUAL EXCLUSIVITY: Handle Like vs Dislike
        if interaction.action == "liked":
            cursor.execute("DELETE FROM interactions WHERE user_id = ? AND movie_id = ? AND action = 'disliked'", 
                           (interaction.user_id, interaction.movie_id))
        elif interaction.action == "disliked":
            cursor.execute("DELETE FROM interactions WHERE user_id = ? AND movie_id = ? AND action = 'liked'", 
                           (interaction.user_id, interaction.movie_id))
        
        # 3. Prevent duplicate "watched" or "bookmarked" (if not already handled by toggle logic)
        # For "watched", people might watch multiple times, but 
        # let's assume we want only one entry for simplicity in the profile categories.
        if interaction.action in ["watched", "bookmarked"]:
             cursor.execute("DELETE FROM interactions WHERE user_id = ? AND movie_id = ? AND action = ?", 
                            (interaction.user_id, interaction.movie_id, interaction.action))

        # 4. Insert NEW action
        cursor.execute("INSERT INTO interactions (user_id, movie_id, action) VALUES (?, ?, ?)", 
                       (interaction.user_id, interaction.movie_id, interaction.action))
        
        conn.commit()
        conn.close()
        return {"status": "success", "message": f"Interaction {interaction.action} toggled ON"}
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profile")
def get_user_profile(request: Request, user_id: int = Query(...)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Define categorized data
    profile = {
        "watched": [],
        "liked": [],
        "disliked": [],
        "bookmarked": []
    }
    
    # Query for distinct interactions
    cursor.execute("""
        SELECT DISTINCT movie_id, action FROM interactions 
        WHERE user_id = ? 
        ORDER BY timestamp DESC
    """, (user_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    movies_df = request.app.state.movies
    
    for row in rows:
        mv_id = row["movie_id"]
        action = row["action"]
        
        # Get title from dataframe
        match = movies_df[movies_df["movie_id"] == mv_id]
        if match.empty:
            title = f"Unknown (ID: {mv_id})"
        else:
            title = match.iloc[0]["title"]

        movie_info = {"id": mv_id, "title": title}
        
        if action == "watched" and movie_info not in profile["watched"]:
            profile["watched"].append(movie_info)
        elif action == "liked" and movie_info not in profile["liked"]:
            profile["liked"].append(movie_info)
        elif action == "disliked" and movie_info not in profile["disliked"]:
            profile["disliked"].append(movie_info)
        elif action == "bookmarked" and movie_info not in profile["bookmarked"]:
            profile["bookmarked"].append(movie_info)
            
    return profile
