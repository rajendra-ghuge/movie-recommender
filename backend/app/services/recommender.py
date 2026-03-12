import pandas as pd
import numpy as np

import tensorflow as tf
API_KEY = "91bf51262562175c39d392b02c5fd963"

import requests

def get_poster(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}"
    try:
        res = requests.get(url, timeout=5).json()
        print(f"Fetching poster for Movie ID: {movie_id} - Status: {res.get('status_code', 'N/A')}")
        return res.get("poster_path")
    except Exception as e:
        print(f"Error fetching poster for {movie_id}: {e}")
        return None

def get_movie_details(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&append_to_response=videos"
    try:
        res = requests.get(url, timeout=5).json()
        
        # Get rating
        rating = res.get("vote_average", "N/A")
        if isinstance(rating, float):
            rating = round(rating, 1)

        # Get trailer key (Look for YouTube trailer)
        trailer_key = None
        if "videos" in res and "results" in res["videos"]:
            videos = res["videos"]["results"]
            for video in videos:
                if video.get("site") == "YouTube" and video.get("type") == "Trailer":
                    trailer_key = video.get("key")
                    break

        return {"rating": rating, "trailer_key": trailer_key}
    except Exception as e:
        print(f"Error fetching details for {movie_id}: {e}")
        return {"rating": "N/A", "trailer_key": None}

def get_movies_paginated(movies: pd.DataFrame, page: int, limit: int):
    start = (page - 1) * limit
    end = start + limit

    movie_titles = movies["title"].iloc[start:end].tolist()

    return {
        "movies": movie_titles,
        "has_more": end < len(movies)
    }

def search_movies(movies: pd.DataFrame, query: str, limit: int = 5):
    if not query:
        return {"movies": []}
    
    matches = movies[movies["title"].str.contains(query, case=False, na=False)]
    return {
        "movies": matches["title"].head(limit).tolist()
    }
    

import concurrent.futures

def recommend_movies(movies: pd.DataFrame, movie_tensor, movie_name: str, skip: int = 0, limit: int = 8):

    if movie_name not in movies["title"].values:
        return {"recommendations": []}

    idx = movies[movies["title"] == movie_name].index[0]

    # ✅ TensorFlow cosine similarity (dot product)
    query_vector = movie_tensor[idx]

    similarity = tf.linalg.matmul(
        movie_tensor,
        tf.expand_dims(query_vector, axis=1)
    )

    similarity = tf.squeeze(similarity).numpy()

    # ✅ get limit movies after skip, because first is same movie
    movie_indices = sorted(
        list(enumerate(similarity)),
        reverse=True,
        key=lambda x: x[1]
    )[skip + 1 : skip + limit + 1]

    matched_movies = [movies.iloc[i[0]] for i in movie_indices]
    movie_ids = [int(m["movie_id"]) for m in matched_movies]

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(movie_ids)) as executor:
        posters = list(executor.map(get_poster, movie_ids))

    recommendations = []

    def safe_list(val):
        if isinstance(val, list):
            return val
        if isinstance(val, np.ndarray):
            return val.tolist()
        if pd.isna(val):
            return []
        return [str(val)]

    searched_movie_genres = set(safe_list(movies.iloc[idx].get("genres", [])))
    searched_movie_cast = set(safe_list(movies.iloc[idx].get("cast", [])))

    for index, movie in enumerate(matched_movies):
        rec_genres = safe_list(movie.get("genres", []))
        rec_cast = safe_list(movie.get("cast", []))

        shared_genres = list(searched_movie_genres.intersection(set(rec_genres)))
        shared_cast = list(searched_movie_cast.intersection(set(rec_cast)))

        recommendations.append({
            "movie_id": movie_ids[index],
            "title": str(movie["title"]),
            "poster_path": posters[index],
            "genres": rec_genres,
            "cast": rec_cast,
            "overview": safe_list(movie.get("overview", [])),
            "shared_genres": shared_genres,
            "shared_cast": shared_cast
        })

    return {"recommendations": recommendations}

def recommend_by_text(movies: pd.DataFrame, movie_tensor, cv, query: str, skip: int = 0, limit: int = 8):
    if not query or not query.strip():
        return {"recommendations": []}

    # Transform text to numerical vector using the CountVectorizer
    query_vector = cv.transform([query]).toarray()
    
    # Normalize query vector safely using L2 norm
    query_norm = np.linalg.norm(query_vector)
    if query_norm > 0:
        query_vector = query_vector / query_norm
        
    query_tensor = tf.convert_to_tensor(query_vector, dtype=tf.float32)

    # Compute cosine similarity
    similarity = tf.linalg.matmul(
        movie_tensor,
        tf.transpose(query_tensor)
    )

    similarity = tf.squeeze(similarity).numpy()

    # Get limit matches after skip
    movie_indices = sorted(
        list(enumerate(similarity)),
        reverse=True,
        key=lambda x: x[1]
    )[skip : skip + limit]

    matched_movies = [movies.iloc[i[0]] for i in movie_indices]
    movie_ids = [int(m["movie_id"]) for m in matched_movies]

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(movie_ids)) as executor:
        posters = list(executor.map(get_poster, movie_ids))

    recommendations = []
    
    def safe_list(val):
        if isinstance(val, list):
            return val
        if isinstance(val, np.ndarray):
            return val.tolist()
        if pd.isna(val):
            return []
        return [str(val)]

    for index, movie in enumerate(matched_movies):
        rec_genres = safe_list(movie.get("genres", []))
        rec_cast = safe_list(movie.get("cast", []))

        # We don't have a "searched movie" to compare against for strict text search, 
        # so shared metrics will just be empty
        recommendations.append({
            "movie_id": movie_ids[index],
            "title": str(movie["title"]),
            "poster_path": posters[index],
            "genres": rec_genres,
            "cast": rec_cast,
            "overview": safe_list(movie.get("overview", [])),
            "shared_genres": [],
            "shared_cast": []
        })

    return {"recommendations": recommendations}