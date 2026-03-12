import React, { useEffect, useState, useRef } from "react";
import axios from "axios";
import "./MovieRecommender.css";
import MovieDetail from "./MovieDetail";

const IMAGE_BASE = "https://image.tmdb.org/t/p/w500";
const API_BASE = "http://localhost:8000";

function MovieRecommender() {
  const [selectedMovie, setSelectedMovie] = useState("");
  const [recommendations, setRecommendations] = useState([]);

  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);

  // New state to track if a specific movie's details are being viewed
  const [selectedDetailMovie, setSelectedDetailMovie] = useState(null);

  // Pagination and infinite scroll state
  const [skip, setSkip] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(false);

  // Track active query independently of input fields to ensure appendages are consistent
  const [activeQuery, setActiveQuery] = useState("");
  const [activeIsExact, setActiveIsExact] = useState(false);

  // Fetch more when skip changes
  useEffect(() => {
    if (skip > 0) {
      handleSuggest(null, true, skip);
    }
  }, [skip]);

  // Fetch search results when query changes
  useEffect(() => {
    const delayDebounceFn = setTimeout(async () => {
      if (searchQuery.trim().length > 0 && searchQuery !== selectedMovie) {
        try {
          const res = await axios.get(
            `${API_BASE}/search?query=${searchQuery}`
          );
          setSearchResults(res.data.movies);
          setShowDropdown(true);
        } catch (err) {
          console.log(err);
        }
      } else {
        setSearchResults([]);
        setShowDropdown(false);
      }
    }, 300); // 300ms debounce

    return () => clearTimeout(delayDebounceFn);
  }, [searchQuery]);

  const handleSelectMovie = (movie) => {
    setSelectedMovie(movie);
    setSearchQuery(movie);
    setShowDropdown(false);

    // Auto fetch recommendations when selected
    handleSuggest(movie, false, 0, true);
  };

  // Fetch recommendations
  const handleSuggest = async (movieToSearch, isAppend = false, currentSkip = 0, forceExactMatch = null) => {
    let queryToUse;
    let isExact;

    if (isAppend) {
      // Use locked parameters when getting more pages
      queryToUse = activeQuery;
      isExact = activeIsExact;
    } else {
      queryToUse = movieToSearch || searchQuery;
      if (!queryToUse) return;

      if (forceExactMatch !== null) {
        isExact = forceExactMatch;
      } else {
        isExact = queryToUse === selectedMovie || searchResults.includes(queryToUse);
      }

      setSkip(0);
      setHasMore(true);
      setActiveQuery(queryToUse);
      setActiveIsExact(isExact);
      setRecommendations([]); // Immediately clear old data so user sees loading state

      // Scroll to top when performing a fresh search
      window.scrollTo({ top: 0, behavior: "smooth" });
    }

    setLoading(true);
    try {
      let url;
      if (isExact) {
        url = `${API_BASE}/recommend?movie=${queryToUse}&skip=${currentSkip}&limit=12`;
      } else {
        url = `${API_BASE}/recommend-text?query=${queryToUse}&skip=${currentSkip}&limit=12`;
      }

      const res = await axios.get(url);
      const newRecs = res.data.recommendations;

      if (newRecs.length === 0 || newRecs.length < 12) {
        setHasMore(false);
      }

      if (isAppend) {
        setRecommendations(prev => [...prev, ...newRecs]);
      } else {
        setRecommendations(newRecs);
      }
    } catch (err) {
      console.log(err);
    }
    setLoading(false);
  };

  return (
    <div className="container">
      <h2 className="title">🎬 Moviees4U</h2>

      <div className="search-container">
        <input
          type="text"
          className="search-input"
          placeholder="Search for a movie..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onFocus={() => {
            if (searchResults.length > 0) setShowDropdown(true);
          }}
          onBlur={() => setTimeout(() => setShowDropdown(false), 200)}
        />
        {showDropdown && searchResults.length > 0 && (
          <ul className="search-results">
            {searchResults.map((movie, index) => (
              <li
                key={index}
                className="search-result-item"
                onMouseDown={(e) => {
                  e.preventDefault(); // Prevent onBlur from firing
                  handleSelectMovie(movie);
                }}
              >
                {movie}
              </li>
            ))}
          </ul>
        )}
      </div>

      <button type="button" className="suggest-btn" onClick={() => handleSuggest()}>
        Suggest Movies
      </button>

      <div className="card-grid">
        {recommendations.map((movie, index) => {
          const cardProps = {
            key: index,
            className: "movie-card",
            onClick: () => setSelectedDetailMovie(movie),
            style: { cursor: "pointer" }
          };

          return (
            <div {...cardProps}>
              <img
                src={movie.poster_path ? `${IMAGE_BASE}${movie.poster_path}` : "https://via.placeholder.com/500x750?text=No+Poster+Available"}
                alt={movie.title}
              />
              <div className="card-body">
                <div className="card-title">{movie.title}</div>

                <div className="card-text">
                  <strong>Genre:</strong>{" "}
                  {movie.genres.map((genre, i) => (
                    <span key={i} className={movie.shared_genres?.includes(genre) ? "highlight" : ""}>
                      {genre}{i < movie.genres.length - 1 ? ", " : ""}
                    </span>
                  ))}
                </div>

                <div className="card-text">
                  <strong>Cast:</strong>{" "}
                  {/* Always show shared cast members, and pad with regular cast members up to 3 total */}
                  {(() => {
                    const shared = movie.shared_cast || [];
                    let toShow = [...shared];

                    if (toShow.length < 3) {
                      const nonShared = movie.cast.filter(actor => !shared.includes(actor));
                      toShow = [...toShow, ...nonShared.slice(0, 3 - toShow.length)];
                    }

                    return toShow.map((actor, i) => (
                      <span key={i} className={shared.includes(actor) ? "highlight" : ""}>
                        {actor}{i < toShow.length - 1 ? ", " : ""}
                      </span>
                    ));
                  })()}
                </div>



              </div>
            </div>
          );
        })}
      </div>

      {hasMore && recommendations.length > 0 && (
        <div style={{ textAlign: "center", marginTop: "20px" }}>
          <button 
            type="button"
            className="suggest-btn" 
            onClick={() => setSkip(prevSkip => prevSkip + 12)}
            disabled={loading}
          >
            {loading ? "Loading more movies..." : "Show More"}
          </button>
        </div>
      )}

      {selectedDetailMovie && (
        <MovieDetail
          movie={selectedDetailMovie}
          onClose={() => setSelectedDetailMovie(null)}
          onSuggestMore={(movieTitle) => {
            setSearchQuery(movieTitle);
            setSelectedMovie(movieTitle);
            handleSuggest(movieTitle, false, 0, true);
            setSelectedDetailMovie(null);
          }}
        />
      )}
    </div>
  );
}

export default MovieRecommender;