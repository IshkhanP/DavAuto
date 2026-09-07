import React from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { Header } from "@/components/Header";
import { useAuth } from "@/context/AuthContext";

const items = [
  { to: "/dashboard", label: "Overview", icon: "🏠", end: true },
  { to: "/dashboard/listings", label: "My Listings", icon: "🚗" },
  { to: "/dashboard/listings/new", label: "Create Listing", icon: "➕" },
  { to: "/dashboard/favorites", label: "Favorites", icon: "❤️" },
  { to: "/dashboard/messages", label: "Messages", icon: "💬" },
  { to: "/dashboard/notifications", label: "Notifications", icon: "🔔" },
  { to: "/dashboard/profile", label: "Profile", icon: "👤" },
  { to: "/dashboard/settings", label: "Settings", icon: "⚙️" },
];

export const DashboardLayout: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  return (
    <div style={{ display: "flex", flexDirection: "column", minHeight: "100vh", background: "var(--color-bg-soft)" }}>
      <Header />
      <div className="container" style={{ display: "grid", gridTemplateColumns: "240px 1fr", gap: "1.5rem", padding: "1.5rem 1.25rem" }}>
        <aside style={{
          background: "#fff", border: "1px solid var(--color-border)", borderRadius: 12,
          padding: 16, height: "fit-content", position: "sticky", top: 80,
        }} className="dashboard-aside">
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
            <div style={{
              width: 40, height: 40, borderRadius: "50%",
              background: "var(--color-black)", color: "#fff",
              display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700,
            }}>
              {user?.full_name?.[0]?.toUpperCase() ?? "U"}
            </div>
            <div>
              <div style={{ fontWeight: 700 }}>{user?.full_name}</div>
              <div className="text-sm muted">{user?.email}</div>
            </div>
          </div>
          <nav style={{ display: "flex", flexDirection: "column", gap: 2 }}>
            {items.map((it) => (
              <NavLink
                key={it.to}
                to={it.to}
                end={it.end as any}
                style={({ isActive }) => ({
                  display: "flex", alignItems: "center", gap: 10,
                  padding: "10px 12px", borderRadius: 8,
                  background: isActive ? "var(--color-light-gray)" : "transparent",
                  color: isActive ? "var(--color-text)" : "var(--color-text-muted)",
                  fontWeight: 600, fontSize: 14,
                })}
              >
                <span style={{ width: 20 }}>{it.icon}</span>
                {it.label}
              </NavLink>
            ))}
          </nav>
        </aside>

        <main>
          <Outlet />
        </main>
      </div>

      <style>{`
        @media (max-width: 900px) {
          .container { grid-template-columns: 1fr !important; }
          .dashboard-aside { position: static !important; }
        }
      `}</style>
    </div>
  );
};