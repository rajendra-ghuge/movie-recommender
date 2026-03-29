import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import Header from "./Header";
import "./Profile.css";

const API_BASE = "http://localhost:8000";

const Accordion = ({ title, items, isOpen, onToggle }) => {
  const navigate = useNavigate();
  return (
    <div className={`accordion ${isOpen ? "open" : ""}`}>
      <div className="accordion-header" onClick={onToggle}>
        <h3>{title} ({items.length})</h3>
        <span>{isOpen ? "-" : "+"}</span>
      </div>
      {isOpen && (
        <div className="accordion-content">
          {items.length > 0 ? (
            <div className="profile-movie-list">
              {items.map((movie) => (
                <div 
                  key={movie.id} 
                  className="profile-movie-item"
                  onClick={() => navigate(`/movie/${movie.id}`)}
                  style={{ cursor: "pointer" }}
                >
                  <span className="movie-name">{movie.title}</span>
                  <span className="movie-id">ID: {movie.id}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="no-items">No items found in this category.</p>
          )}
        </div>
      )}
    </div>
  );
};

function Profile() {
  const [profileData, setProfileData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [openSection, setOpenSection] = useState("watched");
  const navigate = useNavigate();
  const userId = localStorage.getItem("user_id");
  const username = localStorage.getItem("username");

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const res = await axios.get(`${API_BASE}/profile?user_id=${userId}`);
        setProfileData(res.data);
      } catch (err) {
        console.error("Failed to fetch profile:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, [userId]);

  const handleLogout = () => {
    localStorage.clear();
    navigate("/login");
  };

  if (loading) return <div className="loading">Loading profile...</div>;

  return (
    <div className="profile-page">
      <Header />
      <div className="profile-container">
        <div className="profile-main-header">
          <h1>{username}</h1>
          <p>User ID: {userId}</p>
        </div>

        <div className="profile-sections">
          <Accordion
            title="Watched"
            items={profileData.watched}
            isOpen={openSection === "watched"}
            onToggle={() => setOpenSection(openSection === "watched" ? null : "watched")}
          />
        <Accordion
          title="Liked"
          items={profileData.liked}
          isOpen={openSection === "liked"}
          onToggle={() => setOpenSection(openSection === "liked" ? null : "liked")}
        />
        <Accordion
          title="Disliked"
          items={profileData.disliked}
          isOpen={openSection === "disliked"}
          onToggle={() => setOpenSection(openSection === "disliked" ? null : "disliked")}
        />
        <Accordion
          title="Bookmarked"
          items={profileData.bookmarked}
          isOpen={openSection === "bookmarked"}
          onToggle={() => setOpenSection(openSection === "bookmarked" ? null : "bookmarked")}
        />
      </div>
      <div className="profile-footer">
          <button className="logout-btn-large" onClick={handleLogout}>Logout from Account</button>
      </div>
    </div>
  </div>
  );
}

export default Profile;
