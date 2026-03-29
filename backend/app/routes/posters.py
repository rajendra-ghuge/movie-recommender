from fastapi import APIRouter
from app.services.recommender import get_poster

router = APIRouter()

@router.get("/movie/{movie_id}/poster")
async def fetch_poster_by_id(movie_id: int):
    """
    Dedicated endpoint for fetching a single movie poster.
    Enables frontend lazy-loading for better perceived performance.
    """
    path = get_poster(movie_id)
    return {"movie_id": movie_id, "poster_path": path}
