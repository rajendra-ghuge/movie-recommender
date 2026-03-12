import traceback
from app.services.recommender import recommend_movies

try:
    print(recommend_movies("Dangal"))
except Exception as e:
    traceback.print_exc()
