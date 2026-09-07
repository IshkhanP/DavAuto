import React from "react";
import { NavLink, Outlet } from "react-router-dom";
import { Logo } from "@/components/Logo";

const items = [
  { to: "/super-admin", label: "Dashboard", end: true },
  { to: "/super-admin/admins", label: "Administrators" },
  { to: "/super-admin/roles", label: "Roles & Permissions" },
  { to: "/super-admin/users", label: "Users" },
  { to: "/super-admin/categories", label: "Categories" },
  { to: "/super-admin/makes", label: "Makes & Models" },
  { to: "/super-admin/locations", label: "Locations" },
  { to: "/super-admin/promotions", label: "Promotions" },
  { to: "/super-admin/audit-logs", label: "Audit Logs" },
  { to: "/super-admin/settings", label: "Settings" },
];

export const SuperAdminLayout: React.FC = () => {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "260px 1fr", minHeight: "100vh", background: "#0a0a0a", color: "#e5e7eb" }}>
      <aside style={{
        background: "#050505", padding: 16, position: "sticky", top: 0, height: "100vh",
        display: "flex", flexDirection: "column", borderRight: "1px solid #1f1f1f",
      }} className="sa-aside">
        <div style={{ padding: "8px 4px 24px" }}>
          <Logo size={28} variant="light" />
          <div style={{ marginTop: 16, fontSize: 11, letterSpacing: 2, fontWeight: 700, color: "#2563eb", textTransform: "uppercase" }}>
            Super Admin
          </div>
        </div>
        <nav style={{ display: "flex", flexDirection: "column", gap: 4, overflowY: "auto" }}>
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
        <div style={{ marginTop: 16, fontSize: 12, color: "#6b7280" }}>
          <NavLink to="/" style={{ color: "#9ca3af" }}>← Back to site</NavLink>
        </div>
      </aside>

      <main style={{ padding: "1.5rem" }}>
        <Outlet />
      </main>

      <style>{`
        @media (max-width: 900px) {
          body > #root > div { grid-template-columns: 1fr !important; }
          .sa-aside { position: static !important; height: auto !important; }
        }
      `}</style>
    </div>
  );
};