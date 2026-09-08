import React, { useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { Logo } from "./Logo";
import { useAuth } from "@/context/AuthContext";
import { notificationsService } from "@/services";
import { useAsync } from "@/hooks/useAsync";

const navLinks = [
  { to: "/cars", label: "Buy Cars" },
  { to: "/dealers", label: "Dealers" },
];

export const Header: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  const { data: unread } = useAsync(async () => {
    if (!user) return { unread: 0 };
    try {
      return await notificationsService.unreadCount();
    } catch {
      return { unread: 0 };
    }
  }, [user?.id]);

  const handleLogout = async () => {
    await logout();
    navigate("/");
  };

  return (
    <header className="app-header">
      <div className="container" style={{ display: "flex", alignItems: "center", justifyContent: "space-between", height: 64 }}>
        <Link to="/" aria-label="Home">
          <Logo size={32} />
        </Link>

        <nav style={{ display: "flex", gap: 8, alignItems: "center" }} className="hide-mobile">
          {navLinks.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              style={({ isActive }) => ({
                padding: "8px 14px",
                borderRadius: 8,
                fontWeight: 600,
                color: isActive ? "var(--color-blue)" : "var(--color-text)",
              })}
            >
              {l.label}
            </NavLink>
          ))}
          {user && (
            <>
              <NavLink to="/favorites" style={({ isActive }) => ({ padding: "8px 14px", borderRadius: 8, color: isActive ? "var(--color-blue)" : "var(--color-text)", fontWeight: 600 })}>
                Favorites
              </NavLink>
              <NavLink to="/messages" style={({ isActive }) => ({ padding: "8px 14px", borderRadius: 8, color: isActive ? "var(--color-blue)" : "var(--color-text)", fontWeight: 600 })}>
                Messages
              </NavLink>
            </>
          )}
        </nav>

        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <Link to="/sell" className="btn btn-primary hide-mobile">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            Sell Your Car
          </Link>

          {user ? (
            <div style={{ position: "relative" }}>
              <button onClick={() => setMenuOpen((v) => !v)} className="btn btn-outline hide-mobile" aria-haspopup="menu" style={{ display: "flex", alignItems: "center", gap: 8, padding: "4px 10px 4px 4px" }}>
                {user.avatar_url ? (
                  <img src={user.avatar_url} alt={user.full_name} style={{ width: 28, height: 28, borderRadius: "50%", objectFit: "cover" }} />
                ) : (
                  <div style={{ width: 28, height: 28, borderRadius: "50%", background: "var(--color-black)", color: "#fff", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, fontSize: 12 }}>
                    {user.full_name?.[0]?.toUpperCase()}
                  </div>
                )}
                {unread && unread.unread > 0 && (
                  <span style={{
                    width: 8, height: 8, background: "var(--color-red)", borderRadius: "50%", display: "inline-block"
                  }} />
                )}
                <span>{user.full_name.split(" ")[0]}</span>
              </button>
              <button onClick={() => setMenuOpen((v) => !v)} className="btn btn-ghost show-mobile" aria-label="Menu">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
              </button>
              {menuOpen && (
                <div
                  onMouseLeave={() => setMenuOpen(false)}
                  style={{
                    position: "absolute", right: 0, top: "110%", minWidth: 220,
                    background: "#fff", border: "1px solid var(--color-border)", borderRadius: 12,
                    boxShadow: "var(--shadow-md)", padding: 6, zIndex: 100,
                  }}
                >
                  <Link to="/dashboard" onClick={() => setMenuOpen(false)} style={menuItemStyle}>Dashboard</Link>
                  <Link to="/dashboard/listings" onClick={() => setMenuOpen(false)} style={menuItemStyle}>My Listings</Link>
                  <Link to="/dashboard/favorites" onClick={() => setMenuOpen(false)} style={menuItemStyle}>Favorites</Link>
                  <Link to="/dashboard/messages" onClick={() => setMenuOpen(false)} style={menuItemStyle}>Messages</Link>
                  <Link to="/dashboard/notifications" onClick={() => setMenuOpen(false)} style={menuItemStyle}>
                    Notifications {unread && unread.unread > 0 && <span className="badge badge-red">{unread.unread}</span>}
                  </Link>
                  <Link to="/dashboard/profile" onClick={() => setMenuOpen(false)} style={menuItemStyle}>Profile</Link>
                  {/*
                    NOTE: previously showed BOTH an "Admin" link and a
                    "Super Admin" link to super admins, which is exactly the
                    "two dashboards" confusion being fixed. Now a super admin
                    only ever sees a single "Super Admin" entry point (which
                    itself links out to /admin/listings and /admin/reports
                    when needed). A plain ADMIN (not super admin) still sees
                    the Admin link as before.
                  */}
                  {user.roles.includes("ADMIN") && !user.roles.includes("SUPER_ADMIN") && (
                    <Link to="/admin" onClick={() => setMenuOpen(false)} style={menuItemStyle}>Admin</Link>
                  )}
                  {user.roles.includes("SUPER_ADMIN") && (
                    <Link to="/super-admin" onClick={() => setMenuOpen(false)} style={menuItemStyle}>Super Admin</Link>
                  )}
                  <hr style={{ border: 0, borderTop: "1px solid var(--color-border)", margin: "4px 0" }} />
                  <button onClick={handleLogout} style={{ ...menuItemStyle, width: "100%", textAlign: "left" }}>Logout</button>
                </div>
              )}
            </div>
          ) : (
            <>
              <Link to="/login" className="btn btn-ghost hide-mobile">Login</Link>
              <Link to="/register" className="btn btn-blue hide-mobile">Register</Link>
              <Link to="/login" className="btn btn-ghost show-mobile" aria-label="Login">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
              </Link>
            </>
          )}
        </div>
      </div>

      <style>{`
        .hide-mobile { display: inline-flex; }
        .show-mobile { display: none; }
        @media (max-width: 768px) {
          .hide-mobile { display: none !important; }
          .show-mobile { display: inline-flex !important; }
        }
      `}</style>
    </header>
  );
};

const menuItemStyle: React.CSSProperties = {
  display: "block",
  padding: "10px 12px",
  borderRadius: 8,
  fontWeight: 500,
  color: "var(--color-text)",
};
