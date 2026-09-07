// Toaster provider wrapper.
import React from "react";
import { Toaster } from "react-hot-toast";

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <>
    {children}
    <Toaster
      position="top-right"
      toastOptions={{
        style: {
          background: "#0a0a0a",
          color: "#fff",
          borderRadius: 10,
          fontWeight: 500,
          fontSize: 14,
        },
      }}
    />
  </>
);