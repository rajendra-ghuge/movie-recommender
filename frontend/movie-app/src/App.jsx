import React from "react";
import { Routes, Route } from "react-router-dom";
import MovieRecommender from "./MovieRecommender";
import MovieDetail from "./MovieDetail";
import Login from "./Login";
import Signup from "./Signup";
import Profile from "./Profile";
import ProtectedRoute from "./ProtectedRoute";

function App() {
  return (
    <div className="App">
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route 
          path="/" 
          element={
            <ProtectedRoute>
              <MovieRecommender />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/movie/:id" 
          element={
            <ProtectedRoute>
              <MovieDetail />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/profile" 
          element={
            <ProtectedRoute>
              <Profile />
            </ProtectedRoute>
          } 
        />
      </Routes>
    </div>
  );
}

export default App;