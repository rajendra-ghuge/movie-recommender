import React, { useEffect, useState } from "react";
import axios from "axios";
import "./MovieDetail.css";

const IMAGE_BASE = "https://image.tmdb.org/t/p/w500";
const API_BASE = "http://localhost:8000";

function MovieDetail({ movie, onClose, onSuggestMore }) {
    const [details, setDetails] = useState({ rating: null, trailer_key: null });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchDetails = async () => {
            if (!movie.movie_id) {
                setLoading(false);
                return;
            }
            try {
                const res = await axios.get(`${API_BASE}/movie/${movie.movie_id}/details`);
                setDetails(res.data);
            } catch (err) {
                console.error("Failed to fetch movie details:", err);
            } finally {
                setLoading(false);
            }
        };

        fetchDetails();
    }, [movie]);

    return (
        <div className="movie-detail-overlay">
            <div className="movie-detail-container">

                {/* Header with back button */}
                <div className="detail-header">
                    <div className="header-buttons" style={{ display: "flex", gap: "10px" }}>
                        <button type="button" className="back-btn" onClick={onClose}>
                            &larr; Back to Suggestions
                        </button>
                        <button type="button" className="suggest-more-btn" onClick={() => onSuggestMore(movie.title)}>
                            Suggest More Like This
                        </button>
                    </div>
                    <div className="detail-rating">
                        <span role="img" aria-label="star">⭐</span> {details.rating !== null ? details.rating : "N/A"}
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

                        {/* Trailer embed */}
                        <div className="trailer-container">
                            {loading ? (
                                <div className="trailer-placeholder">Loading trailer...</div>
                            ) : details.trailer_key ? (
                                <iframe
                                    className="trailer-iframe"
                                    src={`https://www.youtube.com/embed/${details.trailer_key}`}
                                    title={`${movie.title} Trailer`}
                                    frameBorder="0"
                                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                    allowFullScreen
                                ></iframe>
                            ) : (
                                <div className="trailer-placeholder">No trailer available</div>
                            )}
                        </div>

                        <div className="detail-metadata">
                            <div className="detail-row">
                                <strong>Genre:</strong> {movie.genres?.join(", ") || "N/A"}
                            </div>
                            <div className="detail-row">
                                <strong>Cast:</strong> {movie.cast?.join(", ") || "N/A"}
                            </div>
                        </div>

                        <div className="detail-overview">
                            <h3>Overview</h3>
                            <p>{Array.isArray(movie.overview) ? movie.overview.join(" ") : movie.overview || "No overview available."}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default MovieDetail;
