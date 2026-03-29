import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import axios from "axios";
import "./Header.css";

const API_BASE = "http://localhost:8000";

const Header = ({ onSearch }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const selectionMade = React.useRef(false);
  
  const username = localStorage.getItem("username");
  const userId = localStorage.getItem("user_id");

  // Handle search input changes
  useEffect(() => {
    if (selectionMade.current) {
      selectionMade.current = false;
      return;
    }

    const delayDebounceFn = setTimeout(async () => {
      if (searchQuery.trim().length > 1) {
        try {
          const res = await axios.get(
            `${API_BASE}/search?query=${searchQuery}&user_id=${userId}`
          );
          setSearchResults(res.data.movies);
          setShowDropdown(true);
        } catch (err) {
          console.error(err);
        }
      } else {
        setSearchResults([]);
        setShowDropdown(false);
      }
    }, 300);

    return () => clearTimeout(delayDebounceFn);
  }, [searchQuery, userId]);

  const handleSelectMovie = (movie) => {
    const movieTitle = movie.title || movie;
    selectionMade.current = true;
    setSearchQuery(movieTitle);
    setShowDropdown(false);
    
    if (location.pathname === "/") {
      if (onSearch) onSearch(movieTitle, true);
    } else {
      navigate("/", { state: { searchMovie: movieTitle, isExact: true } });
    }
  };

  const handleSearchSubmit = (e) => {
    if (e.key === "Enter" && searchQuery.trim()) {
      setShowDropdown(false);
      if (location.pathname === "/") {
        if (onSearch) onSearch(searchQuery, false);
      } else {
        navigate("/", { state: { searchMovie: searchQuery, isExact: false } });
      }
    }
  };

  return (
    <header className="main-header">
      <div className="header-content">
        <div className="logo" onClick={() => navigate("/", { state: null })}>
          <span className="logo-icon">🎬</span>
          <h1 className="logo-text">Moviees4U</h1>
        </div>

        <div className="search-bar-container">
          <div className="search-input-wrapper">
            <span className="search-icon">🔍</span>
            <input
              type="text"
              className="header-search-input"
              placeholder="Search for movies..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={handleSearchSubmit}
              onFocus={() => { if (searchResults.length > 0) setShowDropdown(true); }}
              onBlur={() => setTimeout(() => setShowDropdown(false), 200)}
            />
          </div>
          
          {showDropdown && searchResults.length > 0 && (
            <ul className="header-search-results">
              {searchResults.map((movie, index) => (
                <li
                  key={movie.movie_id || index}
                  className="header-search-item"
                  onMouseDown={(e) => {
                    e.preventDefault();
                    handleSelectMovie(movie);
                  }}
                >
                  {movie.title || movie}
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="header-actions-right">
          <div 
            className="header-dice" 
            title="Discover Something New" 
            onClick={(e) => {
              e.stopPropagation();
              navigate("/", { state: { forceDiscover: Date.now() } });
            }}
          >
            🎲
          </div>
          <div className="header-user-profile" title="View Profile" onClick={() => navigate("/profile")}>
            <div className="header-avatar">👤</div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
