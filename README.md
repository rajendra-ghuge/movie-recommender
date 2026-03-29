# 🎬 Moviees4U - Personalized Movie Recommender

A state-of-the-art movie recommendation platform featuring a **Reinforcement Learning-based recommendation engine**, a persistent user history system, and a modern, responsive React interface.

## ✨ Features
- **Smart Personalization**: Uses "Recency Bias" and "Genre Boosting" to adapt to your taste instantly (starting from your very first interaction).
- **Global Search**: Find any movie in the 5,000+ title database with instant suggestions.
- **Movie Details**: Full metadata including overviews, genres, cast, and embedded YouTube trailers.
- **User Dashboard**: Track your Watched, Liked, Disliked, and Bookmarked movies.
- **Lightweight & Fast**: Optimized API responses and intelligent poster caching.

---

## 🚀 Quick Start (Installation)

### 1. Prerequisites
- **Python 3.9+**
- **Node.js 18+**

### 2. Backend Setup (FastAPI)
```bash
cd backend
# Create a virtual environment (optional but recommended)
python -m venv venv
./venv/Scripts/activate  # Windows
source venv/bin/activate # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Initialize the database (creates users and default admin)
python app/db.py

# Start the server
uvicorn app.main:app --reload
```

### 3. Frontend Setup (React + Vite)
```bash
cd frontend/movie-app
npm install
npm run dev
```

---

## 🔑 Default Credentials
- **Admin Email**: `admin@gmail.com`
- **Password**: `123456`

---

## 🛠️ Logic & Architecture
- **Recommendation DNA**: The system converts movie metadata into high-dimensional vectors. Your "User DNA" is a weighted average of these vectors, which **decays over time** so the system always remembers what you like *now*.
- **Database**: Powered by SQLite for zero-configuration portability.
- **Frontend**: Built with Vite and React for maximum performance.

Enjoy your personal cinema! 🍿
