import React from "react";
import { Link } from "react-router-dom";
import { adminService } from "@/services";
import { useAsync } from "@/hooks/useAsync";
import { ErrorState, LoadingBlock } from "@/components/States";

const Card: React.FC<{ label: string; value: number | string; color?: string }> = ({ label, value, color }) => (
  <div style={{
    background: "#161616", color: "#fff", border: "1px solid #1f1f1f",
    padding: 18, borderRadius: 12, display: "flex", flexDirection: "column", gap: 6,
  }}>
    <span style={{ color: "#9ca3af", fontSize: 13 }}>{label}</span>
    <span style={{ fontSize: 28, fontWeight: 800, color }}>{value}</span>
  </div>
);

export const AdminDashboardPage: React.FC = () => {
  const { data, loading, error, reload } = useAsync(() => adminService.stats(), []);

  if (loading) return <LoadingBlock />;
  if (error) return <ErrorState onRetry={reload} />;
  if (!data) return null;

  return (
    <div style={{ padding: 24 }}>
      <h1 style={{ color: "#fff", marginBottom: 24 }}>Admin Dashboard</h1>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 12, marginBottom: 32 }}>
        <Card label="Total Users" value={data.total_users} />
        <Card label="Active Users" value={data.active_users} color="var(--color-green)" />
        <Card label="Total Listings" value={data.total_listings} />
        <Card label="Active Listings" value={data.active_listings} color="var(--color-green)" />
        <Card label="Pending Listings" value={data.pending_listings} color="var(--color-amber)" />
        <Card label="Sold Listings" value={data.sold_listings} />
        <Card label="Dealers" value={data.total_dealers} />
        <Card label="Pending Reports" value={data.pending_reports} color="var(--color-red)" />
        <Card label="New Users (30d)" value={data.new_users_last_30d} />
        <Card label="New Listings (30d)" value={data.new_listings_last_30d} />
      </div>

      <h2 style={{ color: "#fff", marginBottom: 16 }}>Quick actions</h2>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12 }}>
        <QuickAction to="/admin/listings?status=PENDING" title="Review pending listings" subtitle={`${data.pending_listings} awaiting moderation`} />
        <QuickAction to="/admin/reports" title="Handle reports" subtitle={`${data.pending_reports} open reports`} />
        <QuickAction to="/admin/users" title="Manage users" subtitle={`${data.total_users} users total`} />
      </div>
    </div>
  );
};

const QuickAction: React.FC<{ to: string; title: string; subtitle: string }> = ({ to, title, subtitle }) => (
  <Link to={to} style={{
    background: "#161616", border: "1px solid #1f1f1f", borderRadius: 12,
    padding: 16, color: "#fff", textDecoration: "none", display: "block",
  }}>
    <h3 style={{ fontSize: 16 }}>{title}</h3>
    <p style={{ color: "#9ca3af", fontSize: 13, marginTop: 4 }}>{subtitle}</p>
  </Link>
);