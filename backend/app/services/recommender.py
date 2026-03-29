import pandas as pd
import numpy as np

import tensorflow as tf
API_KEY = "91bf51262562175c39d392b02c5fd963"

import requests

POSTER_CACHE = {}

def get_poster(movie_id):
    if movie_id in POSTER_CACHE:
        return POSTER_CACHE[movie_id]
        
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}"
    try:
        res = requests.get(url, timeout=5).json()
        path = res.get("poster_path")
        POSTER_CACHE[movie_id] = path
        print(f"Fetching poster for Movie ID: {movie_id} - STATUS: {res.get('status_code', 'OK')}")
        return path
    except Exception as e:
        print(f"Error fetching poster for {movie_id}: {e}")
        return None

def get_movie_details(movies: pd.DataFrame, movie_id: int):
    try:
        # Get basic details from the TMDB DataFrame
        movie_row = movies[movies["movie_id"] == movie_id]
        if movie_row.empty:
            return {"error": "Movie not found"}
        
        movie_data = movie_row.iloc[0].to_dict()
        
        # Ensure fields are converted to lists if needed
        def safe_list(val):
            if isinstance(val, list):
                return val
            if isinstance(val, np.ndarray):
                return val.tolist()
            if pd.isna(val):
                return []
            return [str(val)]

        movie_info = {
            "movie_id": int(movie_data["movie_id"]),
            "title": str(movie_data["title"]),
            "genres": safe_list(movie_data.get("genres", [])),
            "cast": safe_list(movie_data.get("cast", [])),
            "overview": " ".join(safe_list(movie_data.get("overview", []))) if isinstance(movie_data.get("overview"), (list, np.ndarray)) else str(movie_data.get("overview", "No overview available.")),
        }

        # Fetch extra details (rating and trailer) from TMDB API
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&append_to_response=videos"
        res = requests.get(url, timeout=5).json()
        
        # Get rating
        rating = res.get("vote_average", "N/A")
        if isinstance(rating, (int, float)):
            rating = round(rating, 1)

        # Get poster path if not available
        poster_path = res.get("poster_path")
        movie_info["poster_path"] = poster_path

        # Get trailer key (Look for YouTube trailer)
        trailer_key = None
        if "videos" in res and "results" in res["videos"]:
            videos = res["videos"]["results"]
            for video in videos:
                if video.get("site") == "YouTube" and video.get("type") == "Trailer":
                    trailer_key = video.get("key")
                    break

        movie_info["rating"] = rating
        movie_info["trailer_key"] = trailer_key

        return movie_info
    except Exception as e:
        print(f"Error fetching details for {movie_id}: {e}")
        return {"error": "Failed to fetch movie details"}

def get_movies_paginated(movies: pd.DataFrame, page: int, limit: int):
    start = (page - 1) * limit
    end = start + limit
    
    sub_df = movies.iloc[start:end]
    
    def safe_list(val):
        if isinstance(val, list): return val
        if isinstance(val, np.ndarray): return val.tolist()
        if pd.isna(val): return []
        return [str(val)]

    movie_list = []
    for _, movie in sub_df.iterrows():
        m_id = int(movie["movie_id"])
        movie_list.append({
            "movie_id": m_id,
            "title": str(movie["title"]),
            "poster_path": None,
            "genres": safe_list(movie.get("genres", [])),
            "cast": safe_list(movie.get("cast", [])),
            "overview": " ".join(safe_list(movie.get("overview", []))) if isinstance(movie.get("overview"), (list, np.ndarray)) else str(movie.get("overview", "")),
        })

    return {
        "movies": movie_list,
        "has_more": end < len(movies)
    }

def search_movies(movies: pd.DataFrame, query: str, limit: int = 5):
    if not query:
        return {"movies": []}
    
    matches = movies[movies["title"].str.contains(query, case=False, na=False)].head(limit)
    
    def safe_list(val):
        if isinstance(val, list): return val
        if isinstance(val, np.ndarray): return val.tolist()
        if pd.isna(val): return []
        return [str(val)]

    movie_list = []
    for _, movie in matches.iterrows():
        m_id = int(movie["movie_id"])
        movie_list.append({
            "movie_id": m_id,
            "title": str(movie["title"]),
            "poster_path": None,
            "genres": safe_list(movie.get("genres", [])),
            "cast": safe_list(movie.get("cast", [])),
            "overview": " ".join(safe_list(movie.get("overview", []))) if isinstance(movie.get("overview"), (list, np.ndarray)) else str(movie.get("overview", "")),
        })

    return {
        "movies": movie_list
    }
    

import concurrent.futures
from app.db import get_db_connection

from datetime import datetime
import math

def get_user_preference_vector(movies: pd.DataFrame, movie_tensor, user_id: int):
    """
    Builds a user preference vector and returns a set of interacted movie IDs.
    Includes Recency Bias (Time Decay).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT movie_id, action, timestamp FROM interactions WHERE user_id = ?", (user_id,))
    interactions = cursor.fetchall()
    conn.close()

    interacted_ids = {row["movie_id"] for row in interactions}

    if not interactions:
        return None, set(), []

    weights = {"watched": 1, "liked": 3, "disliked": -3, "bookmarked": 2}
    
    user_vector = tf.zeros_like(movie_tensor[0], dtype=tf.float32)
    total_weight = 0
    recent_genres = []

    # Sort interactions by timestamp to identify recent genres
    sorted_interactions = sorted(interactions, key=lambda x: str(x["timestamp"]), reverse=True)
    
    now = datetime.now()

    for i, inter in enumerate(sorted_interactions):
        m_id = inter["movie_id"]
        action = inter["action"]
        weight = weights.get(action, 0)
        
        # Recency Bias: Decay older interactions
        # We'll use a simple index-based decay or time-based
        # For this version, let's use time-based decay
        try:
            inter_time = datetime.strptime(inter["timestamp"], '%Y-%m-%d %H:%M:%S')
            days_old = (now - inter_time).days
            time_decay = math.exp(-0.05 * days_old) # 5% decay per day
        except:
            time_decay = 1.0

        # Multiplier: Latest interactions are louder (index 0,1,2 gets 2x, 1.5x)
        recency_multiplier = 1.0
        if i == 0: recency_multiplier = 2.0
        elif i < 3: recency_multiplier = 1.5

        effective_weight = weight * time_decay * recency_multiplier
        
        match = movies[movies["movie_id"] == m_id]
        if not match.empty:
            idx = match.index[0]
            movie_vec = movie_tensor[idx]
            user_vector += movie_vec * effective_weight
            total_weight += abs(effective_weight)
            
            # Capture genres for genre-boost logic
            if i < 5 and action in ["liked", "watched"]:
                gs = match.iloc[0].get("genres", [])
                if isinstance(gs, list): recent_genres.extend(gs)

    if total_weight == 0:
        return None, interacted_ids, []

    # Normalize user vector
    user_vector = user_vector / tf.norm(user_vector)
    return user_vector, interacted_ids, recent_genres

def recommend_movies(movies: pd.DataFrame, movie_tensor, movie_name: str, user_id: int = None, skip: int = 0, limit: int = 10):
    if movie_name not in movies["title"].values:
        return {"recommendations": []}

    idx = movies[movies["title"] == movie_name].index[0]
    query_vector = movie_tensor[idx]
    query_movie_id = int(movies.iloc[idx]["movie_id"])

    # Content-based similarity
    content_sim = tf.linalg.matmul(
        movie_tensor,
        tf.expand_dims(query_vector, axis=1)
    )
    content_sim = tf.squeeze(content_sim)

    # RL Re-ranking
    user_pref_vector = None
    interacted_ids = set()
    recent_genres = []
    if user_id:
        user_pref_vector, interacted_ids, recent_genres = get_user_preference_vector(movies, movie_tensor, user_id)

    final_scores = content_sim
    if user_pref_vector is not None:
        user_pref_sim = tf.linalg.matmul(
            movie_tensor,
            tf.expand_dims(user_pref_vector, axis=1)
        )
        user_pref_sim = tf.squeeze(user_pref_sim)
        final_scores = 0.7 * content_sim + 0.3 * user_pref_sim

    final_scores = final_scores.numpy()
    
    def safe_list(val):
        if isinstance(val, list): return val
        if isinstance(val, np.ndarray): return val.tolist()
        if pd.isna(val): return []
        return [str(val)]

    # Apply Genre Boost to final_scores (Numpy version)
    if user_id and recent_genres:
        from collections import Counter
        top_recent_genres = set([g for g, _ in Counter(recent_genres).most_common(2)])
        
        # Boost movies matching top recent genres
        for i in range(len(final_scores)):
            m_genres = set(safe_list(movies.iloc[i].get("genres", [])))
            if top_recent_genres.intersection(m_genres):
                final_scores[i] *= 1.2 # 20% boost for trending genres

    # Get more candidates than limit to allow for filtering
    all_indices = sorted(
        list(enumerate(final_scores)),
        reverse=True,
        key=lambda x: x[1]
    )

    # Filter out: 
    # 1. The query movie itself
    # 2. Movies user has already watched/liked
    recommendations = []

    searched_movie_genres = set(safe_list(movies.iloc[idx].get("genres", [])))

    # Track how many we've skipped to implement pagination
    found_count = 0
    
    for i, score in all_indices:
        movie = movies.iloc[i]
        m_id = int(movie["movie_id"])
        
        # Exclude self and interacted movies
        if m_id == query_movie_id or m_id in interacted_ids:
            continue
            
        found_count += 1
        if found_count <= skip:
            continue
            
        if len(recommendations) >= limit:
            break
            
        rec_genres = safe_list(movie.get("genres", []))
        shared_genres = list(searched_movie_genres.intersection(set(rec_genres)))

        recommendations.append({
            "movie_id": m_id,
            "title": str(movie["title"]),
            "poster_path": None,
            "genres": rec_genres,
            "cast": safe_list(movie.get("cast", [])),
            "overview": " ".join(safe_list(movie.get("overview", []))) if isinstance(movie.get("overview"), (list, np.ndarray)) else str(movie.get("overview", "")),
            "shared_genres": shared_genres
        })
    return {"recommendations": recommendations}

def get_discovery_suggestions(movies: pd.DataFrame, limit: int = 12):
    """
    Returns a completely random sample of movies for discovery.
    """
    random_sample = movies.sample(n=limit)
    recommendations = []
    
    def safe_list(val):
        if isinstance(val, list): return val
        if isinstance(val, np.ndarray): return val.tolist()
        if pd.isna(val): return []
        return [str(val)]

    for _, movie in random_sample.iterrows():
        m_id = int(movie["movie_id"])
        recommendations.append({
            "movie_id": m_id,
            "title": str(movie["title"]),
            "poster_path": None,
            "genres": safe_list(movie.get("genres", [])),
            "cast": safe_list(movie.get("cast", [])),
            "overview": " ".join(safe_list(movie.get("overview", []))) if isinstance(movie.get("overview"), (list, np.ndarray)) else str(movie.get("overview", "")),
            "shared_genres": []
        })
    return {"recommendations": recommendations, "reason": "discover"}

def get_personalized_suggestions(movies: pd.DataFrame, movie_tensor, user_id: int, limit: int = 12):
    """
    Returns personalized recommendations based on the user's history.
    Reacts after 3 interactions for better confidence.
    """
    user_pref_vector, interacted_ids, recent_genres = get_user_preference_vector(movies, movie_tensor, user_id)

    def safe_list(val):
        if isinstance(val, list): return val
        if isinstance(val, np.ndarray): return val.tolist()
        if pd.isna(val): return []
        return [str(val)]

    # If NEW user (history < 3), return random movies
    if len(interacted_ids) < 3 or user_pref_vector is None:
        random_sample = movies.sample(n=limit)
        recommendations = []
        for _, movie in random_sample.iterrows():
            m_id = int(movie["movie_id"])
            recommendations.append({
                "movie_id": m_id,
                "title": str(movie["title"]),
                "poster_path": None,
                "genres": safe_list(movie.get("genres", [])),
                "cast": safe_list(movie.get("cast", [])),
                "overview": " ".join(safe_list(movie.get("overview", []))) if isinstance(movie.get("overview"), (list, np.ndarray)) else str(movie.get("overview", "")),
                "shared_genres": []
            })
        return {"recommendations": recommendations, "reason": "discover"}

    # Similarity between preference vector and all movies
    user_pref_sim = tf.linalg.matmul(
        movie_tensor,
        tf.expand_dims(user_pref_vector, axis=1)
    )
    user_pref_sim = tf.squeeze(user_pref_sim).numpy()
    
    # Genre boost for personalized feed
    from collections import Counter
    top_recent_genres = set([g for g, _ in Counter(recent_genres).most_common(2)])
    
    final_scores = user_pref_sim.copy()
    for i in range(len(final_scores)):
        m_genres = set(safe_list(movies.iloc[i].get("genres", [])))
        if top_recent_genres.intersection(m_genres):
            final_scores[i] *= 1.3 # 30% boost for current interests

    # Get top recommendations
    all_indices = sorted(
        list(enumerate(final_scores)),
        reverse=True,
        key=lambda x: x[1]
    )

    recommendations = []
    for i, score in all_indices:
        movie = movies.iloc[i]
        m_id = int(movie["movie_id"])
        
        # Exclude interacted movies
        if m_id in interacted_ids:
            continue
            
        if len(recommendations) >= limit:
            break

        recommendations.append({
            "movie_id": m_id,
            "title": str(movie["title"]),
            "poster_path": None,
            "genres": safe_list(movie.get("genres", [])),
            "cast": safe_list(movie.get("cast", [])),
            "overview": " ".join(safe_list(movie.get("overview", []))) if isinstance(movie.get("overview"), (list, np.ndarray)) else str(movie.get("overview", "")),
            "shared_genres": list(top_recent_genres.intersection(set(safe_list(movie.get("genres", [])))))
        })

    return {
        "recommendations": recommendations, 
        "reason": "personalized",
        "trending_genres": list(top_recent_genres)
    }

def recommend_by_text(movies: pd.DataFrame, movie_tensor, cv, query: str, user_id: int = None, skip: int = 0, limit: int = 10):
    def safe_list(val):
        if isinstance(val, list): return val
        if isinstance(val, np.ndarray): return val.tolist()
        if pd.isna(val): return []
        return [str(val)]

    if not query or not query.strip():
        return {"recommendations": []}

    # Space-Smart Query: Add joined version for actor/director matching
    processed_query = query.lower()
    if " " in query:
        joined_query = query.replace(" ", "").lower()
        processed_query = f"{processed_query} {joined_query}"
        
    query_vector = cv.transform([processed_query]).toarray()
    query_norm = np.linalg.norm(query_vector)
    if query_norm > 0:
        query_vector = query_vector / query_norm
    query_tensor = tf.convert_to_tensor(query_vector, dtype=tf.float32)

    content_sim = tf.linalg.matmul(
        movie_tensor,
        tf.transpose(query_tensor)
    )
    content_sim = tf.squeeze(content_sim)

    # RL Re-ranking
    user_pref_vector = None
    interacted_ids = set()
    recent_genres = []
    if user_id:
        user_pref_vector, interacted_ids, recent_genres = get_user_preference_vector(movies, movie_tensor, user_id)

    final_scores = content_sim
    if user_pref_vector is not None:
        user_pref_sim = tf.linalg.matmul(
            movie_tensor,
            tf.expand_dims(tf.convert_to_tensor(user_pref_vector), axis=1)
        )
        user_pref_sim = tf.squeeze(user_pref_sim)
        final_scores = 0.7 * content_sim + 0.3 * user_pref_sim

    final_scores = final_scores.numpy()
    
    # Apply Genre Boost to final_scores (Numpy version)
    if user_id and recent_genres:
        from collections import Counter
        top_recent_genres = set([g for g, _ in Counter(recent_genres).most_common(2)])
        
        # Boost movies matching top recent genres
        for i in range(len(final_scores)):
            m_genres = set(safe_list(movies.iloc[i].get("genres", [])))
            if top_recent_genres.intersection(m_genres):
                final_scores[i] *= 1.2 # 20% boost for trending genres

    all_indices = sorted(
        list(enumerate(final_scores)),
        reverse=True,
        key=lambda x: x[1]
    )

    recommendations = []
    found_count = 0
    for i, score in all_indices:
        movie = movies.iloc[i]
        m_id = int(movie["movie_id"])
        
        # Exclude interacted movies
        if m_id in interacted_ids:
            continue
            
        found_count += 1
        if found_count <= skip:
            continue
            
        if len(recommendations) >= limit:
            break

        recommendations.append({
            "movie_id": m_id,
            "title": str(movie["title"]),
            "poster_path": None,
            "genres": safe_list(movie.get("genres", [])),
            "cast": safe_list(movie.get("cast", [])),
            "overview": " ".join(safe_list(movie.get("overview", []))) if isinstance(movie.get("overview"), (list, np.ndarray)) else str(movie.get("overview", "")),
            "shared_genres": []
        })

    return {"recommendations": recommendations}