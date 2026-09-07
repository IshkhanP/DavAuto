import React from "react";
import { NavLink, Outlet } from "react-router-dom";
import { Logo } from "@/components/Logo";

const items = [
  { to: "/admin", label: "Dashboard", end: true },
  { to: "/admin/listings", label: "Listings" },
  { to: "/admin/reports", label: "Reports" },
  { to: "/admin/users", label: "Users" },
];

export const AdminLayout: React.FC = () => {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "240px 1fr", minHeight: "100vh", background: "#f5f6f8" }}>
      <aside style={{
        background: "#0a0a0a", color: "#fff", padding: 16, position: "sticky", top: 0, height: "100vh",
        display: "flex", flexDirection: "column",
      }} className="admin-aside">
        <div style={{ padding: "8px 4px 24px" }}>
          <Logo size={28} variant="light" />
          <div style={{ marginTop: 16, fontSize: 11, letterSpacing: 2, fontWeight: 700, color: "#9ca3af", textTransform: "uppercase" }}>
            Admin Console
          </div>
        </div>
        <nav style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          {items.map((it) => (
            <NavLink
              key={it.to}
              to={it.to}
              end={it.end as any}
              style={({ isActive }) => ({
                padding: "10px 12px", borderRadius: 8,
                background: isActive ? "rgba(37, 99, 235, 0.18)" : "transparent",
                color: isActive ? "#fff" : "#9ca3af",
                fontWeight: 600, fontSize: 14,
              })}
            >
              {it.label}
            </NavLink>
          ))}
        </nav>
        <div style={{ marginTop: "auto", fontSize: 12, color: "#6b7280" }}>
          <NavLink to="/" style={{ color: "#9ca3af" }}>← Back to site</NavLink>
        </div>
      </aside>

      <main>
        <Outlet />
      </main>

      <style>{`
        @media (max-width: 900px) {
          body > #root > div { grid-template-columns: 1fr !important; }
          .admin-aside { position: static !important; height: auto !important; }
        }
      `}</style>
    </div>
  );
};