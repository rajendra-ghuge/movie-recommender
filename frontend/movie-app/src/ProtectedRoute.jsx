import React from "react";
import { Navigate } from "react-router-dom";

const ProtectedRoute = ({ children }) => {
  const userId = localStorage.getItem("user_id");

  if (!userId) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

export default ProtectedRoute;
