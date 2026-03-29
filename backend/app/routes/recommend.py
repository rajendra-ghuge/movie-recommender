from fastapi import APIRouter, Request, Query
from app.services.recommender import recommend_movies, recommend_by_text, get_personalized_suggestions, get_discovery_suggestions

router = APIRouter()

@router.get("/recommendations/discover")
def discovery_recommendations_api(request: Request, limit: int = 12):
    return get_discovery_suggestions(
        request.app.state.movies, 
        limit
    )

@router.get("/recommendations/personalized")
def personalized_recommendations_api(request: Request, user_id: int = Query(...), limit: int = 12):
    return get_personalized_suggestions(
        request.app.state.movies, 
        request.app.state.movie_tensor, 
        user_id,
        limit
    )

@router.get("/recommend")
def recommend_movies_api(request: Request, movie: str, user_id: int = Query(None), skip: int = 0, limit: int = 10):
    return recommend_movies(
        request.app.state.movies, 
        request.app.state.movie_tensor, 
        movie, 
        user_id,
        skip, 
        limit
    )

@router.get("/recommend-text")
def recommend_by_text_api(request: Request, query: str, user_id: int = Query(None), skip: int = 0, limit: int = 10):
    return recommend_by_text(
        request.app.state.movies, 
        request.app.state.movie_tensor, 
        request.app.state.cv, 
        query, 
        user_id,
        skip, 
        limit
    )