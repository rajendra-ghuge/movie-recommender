import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

const IMAGE_BASE = "https://image.tmdb.org/t/p/w500";
const API_BASE = "http://localhost:8000";

const MovieCard = ({ movie, highlightGenres = [] }) => {
  const navigate = useNavigate();
  const [posterPath, setPosterPath] = useState(movie.poster_path);
  const [loadingPoster, setLoadingPoster] = useState(!movie.poster_path);

  useEffect(() => {
    // If we don't have a poster path, fetch it asynchronously
    if (!posterPath) {
      const fetchPoster = async () => {
        try {
          const res = await axios.get(`${API_BASE}/movie/${movie.movie_id}/poster`);
          if (res.data.poster_path) {
            setPosterPath(res.data.poster_path);
          }
        } catch (err) {
          console.error(`Failed to fetch poster for ${movie.movie_id}:`, err);
        } finally {
          setLoadingPoster(false);
        }
      };
      fetchPoster();
    }
  }, [movie.movie_id, posterPath]);

  return (
    <div 
      className="movie-card" 
      onClick={() => navigate(`/movie/${movie.movie_id}`, { state: { movie: { ...movie, poster_path: posterPath } } })}
    >
      <div className={`poster-wrapper ${loadingPoster ? "loading" : ""}`}>
        {posterPath ? (
          <img 
            src={`${IMAGE_BASE}${posterPath}`} 
            alt={movie.title} 
            className="fade-in"
          />
        ) : (
          <div className="poster-placeholder">
            {loadingPoster ? "Fetching..." : "No Poster"}
          </div>
        )}
      </div>
      <div className="card-body">
        <div className="card-title">{movie.title}</div>
        <div className="card-text">
          <strong>Genre:</strong>{" "}
          {movie.genres.map((genre, i) => (
            <span key={i} className={highlightGenres.includes(genre) ? "highlight" : ""}>
              {genre}{i < movie.genres.length - 1 ? ", " : ""}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};

export default MovieCard;
