import React, { useEffect, useState } from "react";
import { useParams, useLocation, useNavigate } from "react-router-dom";
import axios from "axios";
import Header from "./Header";
import "./MovieDetail.css";

const IMAGE_BASE = "https://image.tmdb.org/t/p/w500";
const API_BASE = "http://localhost:8000";

function MovieDetail() {
    const { id } = useParams();
    const location = useLocation();
    const navigate = useNavigate();
    
    // Try to get movie data from location state first (passed from home page)
    const [movie, setMovie] = useState(location.state?.movie || null);
    const [loading, setLoading] = useState(!movie);
    const [error, setError] = useState(null);
    const userId = localStorage.getItem("user_id");

    useEffect(() => {
        const fetchAllDetails = async () => {
            try {
                // If we don't have the movie object or its fields, fetch everything from our new backend endpoint
                const res = await axios.get(`${API_BASE}/movie/${id}/details`);
                
                if (res.data.error) {
                    setError(res.data.error);
                } else {
                    setMovie(res.data);
                }
            } catch (err) {
                console.error("Failed to fetch movie details:", err);
                setError("Failed to load movie details.");
            } finally {
                setLoading(false);
            }
        };

        // Scroll to top on mount
        window.scrollTo(0, 0);

        // Fetch even if we have movie, but we might only have partial data
        // Actually, our updated backend returns EVERYTHING, so it's a good source of truth
        fetchAllDetails();
    }, [id, userId]);

    const handleTrack = async (action) => {
        try {
            const res = await axios.post(`${API_BASE}/track`, {
                user_id: parseInt(userId),
                movie_id: parseInt(id),
                action: action
            });
            alert(res.data.message);
        } catch (err) {
            console.error(`Failed to track ${action}:`, err);
        }
    };

    if (loading && !movie) {
        return <div className="loading-container">Loading movie details...</div>;
    }

    if (error) {
        return (
            <div className="error-container">
                <h2>Error</h2>
                <p>{error}</p>
                <button onClick={() => navigate("/")} className="back-btn">Back to Home</button>
            </div>
        );
    }

    if (!movie) return null;

    return (
        <div className="movie-detail-page">
            <Header />
            <div className="movie-detail-container">

                {/* Simplified header for back button and rating */}
                <div className="detail-subheader">
                    <div className="header-buttons">
                        <button type="button" className="back-btn" onClick={() => navigate("/")}>
                            &larr; Back to Home
                        </button>
                    </div>
                    <div className="detail-rating">
                        <span role="img" aria-label="star">⭐</span> {movie.rating !== null ? movie.rating : "N/A"}
                    </div>
                </div>

                {/* Content area */}
                <div className="detail-content">
                    <div className="detail-poster">
                        <img
                            src={movie.poster_path ? `${IMAGE_BASE}${movie.poster_path}` : "https://via.placeholder.com/500x750?text=No+Poster+Available"}
                            alt={movie.title}
                        />
                    </div>

                    <div className="detail-info">
                        <h1 className="detail-title">{movie.title}</h1>

                        <div className="detail-metadata">
                            <div className="detail-row">
                                <strong>Genre:</strong> {Array.isArray(movie.genres) ? movie.genres.join(", ") : "N/A"}
                            </div>
                            <div className="detail-row">
                                <strong>Cast:</strong> {Array.isArray(movie.cast) ? movie.cast.join(", ") : "N/A"}
                            </div>
                        </div>

                        <div className="interaction-buttons">
                            <button className="icon-btn watch" title="Mark as Watched" onClick={() => handleTrack("watched")}>👁️ Watch</button>
                            <button className="icon-btn like" title="Like" onClick={() => handleTrack("liked")}>👍 Like</button>
                            <button className="icon-btn dislike" title="Dislike" onClick={() => handleTrack("disliked")}>👎 Dislike</button>
                            <button className="icon-btn bookmark" title="Bookmark" onClick={() => handleTrack("bookmarked")}>🔖 Bookmark</button>
                            <button 
                                className="icon-btn suggest" 
                                title="Discover More Like This" 
                                onClick={() => navigate("/", { state: { suggestMovie: movie.title, isExact: true } })}
                            >
                                🔍 More Like This
                            </button>
                        </div>

                        <div className="detail-overview">
                            <h3>Overview</h3>
                            <p>{movie.overview || "No overview available."}</p>
                        </div>

                        {/* Trailer embed */}
                        <div className="trailer-container">
                            {loading ? (
                                <div className="trailer-placeholder">Updating details...</div>
                            ) : movie.trailer_key ? (
                                <iframe
                                    className="trailer-iframe"
                                    src={`https://www.youtube.com/embed/${movie.trailer_key}`}
                                    title={`${movie.title} Trailer`}
                                    frameBorder="0"
                                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                    allowFullScreen
                                ></iframe>
                            ) : (
                                <div className="trailer-placeholder">No trailer available</div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default MovieDetail;
