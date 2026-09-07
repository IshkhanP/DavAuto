import React from "react";
import { Link } from "react-router-dom";
import { Logo } from "./Logo";

export const Footer: React.FC = () => {
  return (
    <footer className="app-footer">
      <div className="container">
        <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr 1fr", gap: "2rem" }} className="footer-grid">
          <div>
            <Logo size={32} variant="light" />
            <p style={{ marginTop: 12, color: "#9ca3af", fontSize: 14, maxWidth: 320 }}>
              BlackSharkCars is the modern automotive marketplace. Find your next car, sell with confidence,
              and connect with trusted dealers and sellers.
            </p>
          </div>
          <div>
            <h4 style={{ color: "#fff", marginBottom: 12, fontSize: 14 }}>Explore</h4>
            <FooterLink to="/cars">Buy Cars</FooterLink>
            <FooterLink to="/sell">Sell Your Car</FooterLink>
            <FooterLink to="/dealers">Dealers</FooterLink>
          </div>
          <div>
            <h4 style={{ color: "#fff", marginBottom: 12, fontSize: 14 }}>Company</h4>
            <FooterLink to="/about">About</FooterLink>
            <FooterLink to="/contact">Contact</FooterLink>
            <FooterLink to="/terms">Terms</FooterLink>
            <FooterLink to="/privacy">Privacy</FooterLink>
          </div>
          <div>
            <h4 style={{ color: "#fff", marginBottom: 12, fontSize: 14 }}>Help</h4>
            <FooterLink to="/help">Help Center</FooterLink>
            <FooterLink to="/safety">Safety Tips</FooterLink>
          </div>
        </div>

        <div style={{ borderTop: "1px solid #2a2a2a", paddingTop: 16, marginTop: 32, color: "#6b7280", fontSize: 13, textAlign: "center" }}>
          © 2025 BlackSharkCars. All rights reserved.
        </div>
      </div>

      <style>{`
        @media (max-width: 768px) {
          .footer-grid { grid-template-columns: 1fr 1fr !important; }
        }
      `}</style>
    </footer>
  );
};

const FooterLink: React.FC<{ to: string; children: React.ReactNode }> = ({ to, children }) => (
  <Link to={to} style={{ display: "block", color: "#9ca3af", padding: "4px 0", fontSize: 14 }}>
    {children}
  </Link>
);