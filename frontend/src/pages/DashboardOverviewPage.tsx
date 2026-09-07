import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { carsService, favoritesService } from "@/services";
import { CarCard, CarCardGridSkeleton } from "@/components/CarCard";

export const DashboardOverviewPage: React.FC = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState<{ active: number; pending: number; sold: number; favorites: number } | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        // Fetch just the totals (limit=1) for each status and the favorites count,
        // all in parallel. The backend paginates by total count, so a single-row
        // request still returns the count without pulling the data.
        const [active, pending, sold, favs] = await Promise.all([
          carsService.mine({ status: "ACTIVE", page: 1, limit: 1 }),
          carsService.mine({ status: "PENDING", page: 1, limit: 1 }),
          carsService.mine({ status: "SOLD", page: 1, limit: 1 }),
          favoritesService.list(1, 1),
        ]);
        if (!cancelled) setStats({
          active: active.total,
          pending: pending.total,
          sold: sold.total,
          favorites: favs.total,
        });
      } catch {
        // silent fail in dashboard
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  return (
    <div>
      <h1 style={{ marginBottom: 8 }}>Welcome back, {user?.full_name?.split(" ")[0]} 👋</h1>
      <p className="muted text-sm" style={{ marginBottom: 24 }}>Here's what's happening with your listings.</p>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 12, marginBottom: 24 }}>
        <StatCard label="Active Listings" value={stats?.active} href="/dashboard/listings?status=ACTIVE" />
        <StatCard label="Pending" value={stats?.pending} href="/dashboard/listings?status=PENDING" />
        <StatCard label="Sold" value={stats?.sold} href="/dashboard/listings?status=SOLD" />
        <StatCard label="Favorites" value={stats?.favorites} href="/dashboard/favorites" />
      </div>

      <div className="row" style={{ gap: 12, marginBottom: 24 }}>
        <Link to="/dashboard/listings/new" className="btn btn-primary">
          + Create new listing
        </Link>
        <Link to="/dashboard/listings" className="btn btn-outline">Manage listings</Link>
      </div>

      <div className="card" style={{ padding: 20 }}>
        <h3 style={{ marginBottom: 8 }}>Tips for sellers</h3>
        <ul style={{ margin: 0, paddingLeft: 18, lineHeight: 1.8, color: "var(--color-text-muted)" }}>
          <li>Use clear, well-lit photos to attract more buyers.</li>
          <li>Set a competitive price based on the market value.</li>
          <li>Respond to messages quickly to close deals faster.</li>
        </ul>
      </div>
    </div>
  );
};

const StatCard: React.FC<{ label: string; value?: number; href: string }> = ({ label, value, href }) => (
  <Link to={href} className="card" style={{
    padding: 18, borderRadius: 12, textDecoration: "none", color: "inherit",
    display: "flex", flexDirection: "column", gap: 6,
  }}>
    <span className="text-sm muted">{label}</span>
    <span style={{ fontSize: 28, fontWeight: 800 }}>{value ?? "—"}</span>
  </Link>
);