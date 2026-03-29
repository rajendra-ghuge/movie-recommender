import React, { useEffect, useState, useRef } from "react";
import axios from "axios";
import { useNavigate, useLocation } from "react-router-dom";
import Header from "./Header";
import MovieCard from "./MovieCard";
import "./MovieRecommender.css";

const API_BASE = "http://localhost:8000";

function MovieRecommender() {
  const [selectedMovie, setSelectedMovie] = useState("");
  const [recommendations, setRecommendations] = useState([]);
  const [personalMovies, setPersonalMovies] = useState([]);
  const [personalReason, setPersonalReason] = useState("");

  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const hasTriggeredSuggest = useRef(false);
  const userId = localStorage.getItem("user_id");
  const username = localStorage.getItem("username");


  // Pagination and infinite scroll state
  const [skip, setSkip] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(false);

  // Track active query independently of input fields to ensure appendages are consistent
  const [activeQuery, setActiveQuery] = useState("");
  const [activeIsExact, setActiveIsExact] = useState(false);

  const initialFetchDone = useRef(false);

  // 1. Initial Data Fetch (Personalized & Trending)
  useEffect(() => {
    const fetchInitial = async () => {
      if (!userId) return;
      
      const fetchPersonalizedMovies = async () => {
        try {
          const isDiscoveryMode = location.state?.forceDiscover;
          if (isDiscoveryMode) {
            setActiveQuery(""); // Clear search when discovering
            setRecommendations([]);
          }
          
          const endpoint = isDiscoveryMode 
            ? `${API_BASE}/recommendations/discover?limit=12`
            : `${API_BASE}/recommendations/personalized?user_id=${userId}&limit=12`;
          
          const res = await axios.get(endpoint);
          setPersonalMovies(res.data.recommendations || []);
          setPersonalReason(res.data.reason || "");
        } catch (err) {
          console.error("Failed to fetch personalized movies:", err);
        }
      };
      fetchPersonalizedMovies();
    };

    fetchInitial();
  }, [userId, location.state?.forceDiscover]);

  // 2. Handle Search from Navigation State
  useEffect(() => {
    if (location.state?.searchMovie && !hasTriggeredSuggest.current) {
      const { searchMovie, isExact } = location.state;
      handleSuggest(searchMovie, false, 0, isExact);
      hasTriggeredSuggest.current = true;
      // Clear state silently
      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

  // 3. Fetch more when skip changes
  useEffect(() => {
    if (skip > 0) {
      handleSuggest(null, true, skip);
    }
  }, [skip]);

  const handleSelectMovie = (movie) => {
    setSelectedMovie(movie);
    setSearchQuery(movie);
    setShowDropdown(false);

    // Auto fetch recommendations when selected
    handleSuggest(movie, false, 0, true);
  };

  // Handle "Suggest More Like This" from Detail Page (must be after handleSelectMovie)
  useEffect(() => {
    if (location.state?.suggestMovie && !hasTriggeredSuggest.current) {
      handleSelectMovie(location.state.suggestMovie);
      hasTriggeredSuggest.current = true;
      // Clear state so it doesn't re-trigger on back/forward
      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

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
        url = `${API_BASE}/recommend?movie=${encodeURIComponent(queryToUse)}&user_id=${userId || ""}&skip=${currentSkip}&limit=12`;
      } else {
        url = `${API_BASE}/recommend-text?query=${encodeURIComponent(queryToUse)}&user_id=${userId || ""}&skip=${currentSkip}&limit=12`;
      }

      const res = await axios.get(url);
      const newRecs = res.data.recommendations || [];

      if (newRecs.length === 0 || newRecs.length < 12) {
        setHasMore(false);
      }

      if (isAppend) {
        setRecommendations(prev => [...prev, ...newRecs]);
      } else {
        setRecommendations(newRecs);
      }
    } catch (err) {
      console.error("Search failed:", err);
      setRecommendations([]);
      setHasMore(false);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="home-page">
      <Header onSearch={(query, isExact) => handleSuggest(query, false, 0, isExact)} />
      
      <div className="container">
        {personalMovies.length > 0 && !activeQuery && (
          <div className="personal-recommendations-section">
            <h2 className="section-title">
              {personalReason === "personalized" ? "✨ Recommended For You" : "🎲 Discover Movies"}
            </h2>
            <div className="card-grid">
              {personalMovies.map((movie, index) => (
                <MovieCard 
                  key={`personal-${movie.movie_id}-${index}`} 
                  movie={movie} 
                  highlightGenres={movie.shared_genres} 
                />
              ))}
            </div>
            <div className="section-divider"></div>
          </div>
        )}

        <div className="search-feed-section">
          {activeQuery && (
            <>
              <h2 className="section-title">Results for "{activeQuery}"</h2>
              <div className="card-grid">
                {recommendations.length > 0 ? (
                  recommendations.map((movie, index) => (
                    <MovieCard 
                      key={`search-${movie.movie_id}-${index}`} 
                      movie={movie} 
                      highlightGenres={movie.shared_genres} 
                    />
                  ))
                ) : (
                  !loading && <p className="no-results">No results found for "{activeQuery}".</p>
                )}
              </div>
            </>
          )}
        </div>

        {hasMore && recommendations.length > 0 && activeQuery && (
          <div style={{ textAlign: "center", marginTop: "20px", paddingBottom: "40px" }}>
            <button 
              type="button"
              className="suggest-btn" 
              onClick={() => setSkip(prevSkip => prevSkip + 12)}
              disabled={loading}
            >
              {loading ? "Loading results..." : "Show More Results"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default MovieRecommender;