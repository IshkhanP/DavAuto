// Protected route components. Frontend UX only — backend must always re-check.
import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

export const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div style={{ minHeight: "60vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <span className="loading-spinner" />
      </div>
    );
  }
  if (!user) {
    return <Navigate to={`/login?redirect=${encodeURIComponent(location.pathname)}`} replace />;
  }
  return <>{children}</>;
};

export const AdminRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, loading, hasAnyPermission } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div style={{ minHeight: "60vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <span className="loading-spinner" />
      </div>
    );
  }
  if (!user) {
    return <Navigate to={`/login?redirect=${encodeURIComponent(location.pathname)}`} replace />;
  }
  // Admin / Super Admin / any user with admin permission
  const isAdmin = user.roles.includes("ADMIN") || user.roles.includes("SUPER_ADMIN") || hasAnyPermission("VIEW_USERS", "VIEW_LISTINGS");
  if (!isAdmin) {
    return <Navigate to="/" replace />;
  }
  return <>{children}</>;
};

export const SuperAdminRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div style={{ minHeight: "60vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <span className="loading-spinner" />
      </div>
    );
  }
  if (!user) {
    return <Navigate to={`/login?redirect=${encodeURIComponent(location.pathname)}`} replace />;
  }
  if (!user.roles.includes("SUPER_ADMIN")) {
    return <Navigate to="/" replace />;
  }
  return <>{children}</>;
};