from fastapi import APIRouter, Request
from app.services.recommender import recommend_movies, recommend_by_text

router = APIRouter()

@router.get("/recommend")
def recommend(request: Request, movie: str, skip: int = 0, limit: int = 12):
    return recommend_movies(request.app.state.movies, request.app.state.movie_tensor, movie, skip, limit)

@router.get("/recommend-text")
def recommend_text(request: Request, query: str, skip: int = 0, limit: int = 12):
    return recommend_by_text(request.app.state.movies, request.app.state.movie_tensor, request.app.state.cv, query, skip, limit)