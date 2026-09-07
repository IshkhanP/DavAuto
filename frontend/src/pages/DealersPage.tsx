import React from "react";
import { Link } from "react-router-dom";
import { dealersService } from "@/services";
import { useAsync } from "@/hooks/useAsync";
import { ErrorState, LoadingBlock } from "@/components/States";

export const DealersPage: React.FC = () => {
  const { data, loading, error, reload } = useAsync(() => dealersService.list(), []);

  return (
    <div className="container" style={{ padding: "2rem 1.25rem" }}>
      <h1 style={{ marginBottom: 8 }}>Dealers</h1>
      <p className="muted text-sm" style={{ marginBottom: 24 }}>Trusted dealerships on BlackSharkCars.</p>

      {loading ? <LoadingBlock /> : error ? <ErrorState onRetry={reload} /> : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 16 }}>
          {(data ?? []).map((d) => (
            <Link key={d.id} to={`/dealers/${d.id}`} className="card" style={{
              padding: 18, display: "flex", flexDirection: "column", gap: 12,
            }}>
              <div className="row" style={{ gap: 12 }}>
                <div style={{
                  width: 52, height: 52, background: "var(--color-black)", color: "#fff",
                  borderRadius: 12, display: "flex", alignItems: "center", justifyContent: "center",
                  fontWeight: 800, fontSize: 20,
                }}>
                  {d.business_name?.[0]?.toUpperCase()}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 700, fontSize: 16 }}>{d.business_name}</div>
                  <div className="text-sm muted">{d.city}{d.country ? `, ${d.country}` : ""}</div>
                </div>
                {d.is_verified && <span className="badge badge-green">Verified</span>}
              </div>
              <p className="text-sm muted" style={{
                display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical",
                overflow: "hidden",
              }}>
                {d.description || "Authorized dealer"}
              </p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
};