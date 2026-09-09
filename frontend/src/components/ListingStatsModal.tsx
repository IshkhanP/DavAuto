// Shows a simple per-day view count for one of the seller's listings —
// "how many people saw your post today / this week" — backed by
// GET /cars/{id}/views/daily.
import React, { useEffect, useState } from "react";
import { carsService } from "@/services";
import type { CarDailyView } from "@/types";

interface ListingStatsModalProps {
  carId: string;
  carLabel: string;
  onClose: () => void;
}

export const ListingStatsModal: React.FC<ListingStatsModalProps> = ({ carId, carLabel, onClose }) => {
  const [data, setData] = useState<CarDailyView[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(false);
    carsService
      .dailyViews(carId, 14)
      .then((rows) => {
        if (!cancelled) setData(rows);
      })
      .catch(() => {
        if (!cancelled) setError(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [carId]);

  const today = data && data.length > 0 ? data[data.length - 1] : undefined;
  const total = data?.reduce((sum, d) => sum + d.count, 0) ?? 0;
  const max = Math.max(1, ...(data ?? []).map((d) => d.count));

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 480 }}>
        <h2 style={{ marginBottom: 4 }}>Views — {carLabel}</h2>
        <p className="text-sm muted" style={{ marginBottom: 16 }}>
          How many people viewed this listing each day over the last two weeks.
        </p>

        {loading ? (
          <div className="skeleton" style={{ height: 160 }} />
        ) : error ? (
          <p className="text-sm" style={{ color: "var(--color-red)" }}>Could not load stats.</p>
        ) : (
          <>
            <div className="row" style={{ gap: 32, marginBottom: 20 }}>
              <div>
                <div className="text-sm muted">Today</div>
                <div style={{ fontSize: 28, fontWeight: 800 }}>{today?.count ?? 0}</div>
              </div>
              <div>
                <div className="text-sm muted">Last 14 days</div>
                <div style={{ fontSize: 28, fontWeight: 800 }}>{total}</div>
              </div>
            </div>
            <div style={{ display: "flex", alignItems: "flex-end", gap: 4, height: 120 }}>
              {(data ?? []).map((d) => (
                <div
                  key={d.view_date}
                  style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}
                >
                  <div
                    title={`${d.view_date}: ${d.count} view${d.count === 1 ? "" : "s"}`}
                    style={{
                      width: "100%",
                      height: `${Math.max(4, (d.count / max) * 100)}px`,
                      background: "var(--color-blue)",
                      borderRadius: 4,
                    }}
                  />
                  <span style={{ fontSize: 9, color: "var(--color-text-muted)" }}>
                    {d.view_date.slice(5)}
                  </span>
                </div>
              ))}
            </div>
          </>
        )}

        <div className="row" style={{ justifyContent: "flex-end", marginTop: 20 }}>
          <button className="btn btn-outline" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
};
