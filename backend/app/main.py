from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.routes import movies, recommend
from data.preprocessing import preprocessing, get_similarity

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load and preprocess data on startup
    print("Loading datasets and calculating similarity tensors...")
    df, movies_df = preprocessing()
    movie_tensor, cv = get_similarity(df)
    
    # Store globally in app state
    app.state.movies = movies_df
    app.state.movie_tensor = movie_tensor
    app.state.cv = cv
    print("Done! Application is ready.")
    
    yield
    
    # Cleanup on shutdown
    app.state.movies = None
    app.state.movie_tensor = None
    app.state.cv = None

app = FastAPI(lifespan=lifespan)


# Allow React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(movies.router)
app.include_router(recommend.router)