from fastapi import APIRouter, Query, Path, Request
from app.services.recommender import get_movies_paginated, search_movies, get_movie_details

router = APIRouter()

@router.get("/movies")
def get_movies(request: Request, page: int = 1, limit: int = 20):
    return get_movies_paginated(request.app.state.movies, page, limit)

@router.get("/search")
def search_movies_api(request: Request, query: str = Query(..., min_length=1), limit: int = 5):
    return search_movies(request.app.state.movies, query, limit)

@router.get("/movie/{movie_id}/details")
def get_movie_details_api(movie_id: int = Path(...)):
    return get_movie_details(movie_id)