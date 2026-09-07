// BlackSharkCars logo: black shark silhouette with automotive accent.
import React from "react";

interface LogoProps {
  size?: number;
  withText?: boolean;
  variant?: "dark" | "light";
}

export const Logo: React.FC<LogoProps> = ({ size = 36, withText = true, variant = "dark" }) => {
  const textColor = variant === "dark" ? "#050505" : "#ffffff";
  return (
    <div style={{ display: "inline-flex", alignItems: "center", gap: 10 }}>
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width={size}
        height={size}
        viewBox="0 0 64 64"
        aria-hidden="true"
      >
        <rect width="64" height="64" rx="14" fill="#050505" />
        {/* shark body */}
        <path
          d="M9 40 C 18 28, 30 24, 38 26 L 48 18 L 50 26 L 58 30 L 50 36 L 56 44 L 46 42 L 42 46 C 30 50, 18 48, 9 40 Z"
          fill="#FFFFFF"
        />
        {/* gill */}
        <path d="M22 36 L 28 38 L 22 40 Z" fill="#050505" />
        {/* fin */}
        <path d="M30 28 L 36 18 L 40 28 Z" fill="#2563EB" />
        {/* eye */}
        <circle cx="48" cy="32" r="2" fill="#050505" />
        {/* tail teeth / wheel mark */}
        <circle cx="16" cy="44" r="4" fill="#050505" stroke="#FFFFFF" strokeWidth="2" />
        <circle cx="16" cy="44" r="1.5" fill="#FFFFFF" />
      </svg>
      {withText && (
        <span
          style={{
            fontFamily: "Inter, sans-serif",
            fontWeight: 800,
            letterSpacing: "-0.02em",
            fontSize: size * 0.5,
            color: textColor,
          }}
        >
          BlackShark<span style={{ color: "#2563EB" }}>Cars</span>
        </span>
      )}
    </div>
  );
};