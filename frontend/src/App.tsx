import React from "react";
import { BrowserRouter } from "react-router-dom";
import { HelmetProvider } from "react-helmet-async";
import { AuthProvider } from "@/context/AuthContext";
import { ToastProvider } from "@/components/ToastProvider";
import { AppRouter } from "@/router/AppRouter";

export const App: React.FC = () => {
  return (
    <HelmetProvider>
      <BrowserRouter>
        <AuthProvider>
          <ToastProvider>
            <AppRouter />
          </ToastProvider>
        </AuthProvider>
      </BrowserRouter>
    </HelmetProvider>
  );
};