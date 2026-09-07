import React from "react";
import { Link } from "react-router-dom";
import { adminService } from "@/services";
import { useAsync } from "@/hooks/useAsync";
import { ErrorState, LoadingBlock } from "@/components/States";

export const SuperAdminDashboardPage: React.FC = () => {
  const { data, loading, error } = useAsync(() => adminService.stats(), []);
  if (loading) return <LoadingBlock />;
  if (error) return <ErrorState />;
  if (!data) return null;

  const tiles = [
    { label: "Users", value: data.total_users, href: "/super-admin/users", color: "#2563eb" },
    { label: "Listings", value: data.total_listings, href: "/super-admin/users", color: "#16a34a" },
    { label: "Dealers", value: data.total_dealers, href: "/super-admin/users", color: "#f59e0b" },
    { label: "Pending Reports", value: data.pending_reports, href: "/super-admin/audit-logs", color: "#dc2626" },
    { label: "New Users (30d)", value: data.new_users_last_30d, href: "/super-admin/audit-logs", color: "#9ca3af" },
    { label: "New Listings (30d)", value: data.new_listings_last_30d, href: "/super-admin/audit-logs", color: "#9ca3af" },
  ];

  return (
    <div>
      <h1 style={{ color: "#fff", marginBottom: 24 }}>Super Admin</h1>
      <p style={{ color: "#9ca3af", marginBottom: 32 }}>Complete system control. Every action is logged in the audit trail.</p>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 12, marginBottom: 32 }}>
        {tiles.map((t) => (
          <Link key={t.label} to={t.href} style={{
            background: "#161616", border: "1px solid #1f1f1f", padding: 18,
            borderRadius: 12, color: "#fff", textDecoration: "none",
            display: "flex", flexDirection: "column", gap: 6,
          }}>
            <span style={{ color: "#9ca3af", fontSize: 13 }}>{t.label}</span>
            <span style={{ fontSize: 28, fontWeight: 800, color: t.color }}>{t.value}</span>
          </Link>
        ))}
      </div>

      <h2 style={{ color: "#fff", marginBottom: 16 }}>Manage</h2>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12 }}>
        <ManageCard to="/super-admin/admins" title="Administrators" desc="Create and manage admin accounts" />
        <ManageCard to="/super-admin/roles" title="Roles & Permissions" desc="Build custom roles" />
        <ManageCard to="/super-admin/categories" title="Categories" desc="Vehicle types" />
        <ManageCard to="/super-admin/makes" title="Makes & Models" desc="Catalog" />
        <ManageCard to="/super-admin/locations" title="Locations" desc="Countries, cities" />
        <ManageCard to="/super-admin/promotions" title="Promotions" desc="Packages and pricing" />
        <ManageCard to="/super-admin/audit-logs" title="Audit Logs" desc="Every super-admin action" />
        <ManageCard to="/super-admin/settings" title="Site Settings" desc="System configuration" />
      </div>
    </div>
  );
};

const ManageCard: React.FC<{ to: string; title: string; desc: string }> = ({ to, title, desc }) => (
  <Link to={to} style={{
    background: "#161616", border: "1px solid #1f1f1f", borderRadius: 12,
    padding: 16, color: "#fff", textDecoration: "none", display: "block",
  }}>
    <h3 style={{ fontSize: 16 }}>{title}</h3>
    <p style={{ color: "#9ca3af", fontSize: 13, marginTop: 4 }}>{desc}</p>
  </Link>
);