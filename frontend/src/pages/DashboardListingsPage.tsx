import React, { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { carsService } from "@/services";
import { useAsync } from "@/hooks/useAsync";
import { EmptyState, ErrorState, LoadingBlock } from "@/components/States";
import { QuickAddListingModal } from "@/components/QuickAddListingModal";
import { ListingStatsModal } from "@/components/ListingStatsModal";
import { formatCurrency, formatDate, formatMileage, statusLabel, timeAgo } from "@/utils/format";
import type { CarCard as CarCardData, PaginatedResponse } from "@/types";
import toast from "react-hot-toast";

export const DashboardListingsPage: React.FC = () => {
  const [params] = useSearchParams();
  const status = params.get("status") || undefined;
  const [page, setPage] = useState(1);
  const navigate = useNavigate();

  const [showQuickAdd, setShowQuickAdd] = useState(false);
  const [statsFor, setStatsFor] = useState<{ id: string; label: string } | null>(null);

  const { data, loading, error, reload } = useAsync<PaginatedResponse<CarCardData>>(
    () => carsService.mine({ status, page, limit: 12 }),
    [status, page]
  );

  const setStatus = async (id: string, newStatus: string) => {
    try {
      await carsService.setStatus(id, newStatus);
      toast.success(`Status updated to ${statusLabel(newStatus)}`);
      reload();
    } catch {
      toast.error("Could not update status");
    }
  };

  const onDelete = async (id: string) => {
    if (!confirm("Delete this listing?")) return;
    try {
      await carsService.remove(id);
      toast.success("Listing deleted");
      reload();
    } catch {
      toast.error("Could not delete");
    }
  };

  const onDuplicate = async (id: string) => {
    try {
      const newCar = await carsService.duplicate(id);
      toast.success("Listing duplicated (draft)");
      navigate(`/dashboard/listings/${newCar.id}/edit`);
    } catch {
      toast.error("Could not duplicate");
    }
  };

  return (
    <div>
      <div className="row-between" style={{ marginBottom: 16 }}>
        <div>
          <h1>My Listings</h1>
          <p className="text-sm muted">Manage your vehicles.</p>
        </div>
        <div className="row" style={{ gap: 8 }}>
          <button className="btn btn-outline" onClick={() => setShowQuickAdd(true)}>
            + Quick Add
          </button>
          <Link to="/dashboard/listings/new" className="btn btn-primary">+ New listing</Link>
        </div>
      </div>

      <div className="row" style={{ gap: 6, marginBottom: 16, flexWrap: "wrap" }}>
        <FilterTab label="All" status={undefined} />
        <FilterTab label="Active" status="ACTIVE" />
        <FilterTab label="Pending" status="PENDING" />
        <FilterTab label="Sold" status="SOLD" />
        <FilterTab label="Paused" status="PAUSED" />
        <FilterTab label="Draft" status="DRAFT" />
      </div>

      {loading ? <LoadingBlock /> :
        error ? <ErrorState onRetry={reload} /> :
          (data?.items.length ?? 0) === 0 ? (
            <EmptyState
              title="No listings yet"
              description="Create your first listing to get started."
              action={{ label: "Create listing", onClick: () => navigate("/dashboard/listings/new") }}
            />
          ) : (
            <div className="card" style={{ overflow: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 760 }}>
                <thead>
                  <tr style={{ background: "var(--color-bg-soft)", textAlign: "left" }}>
                    <th style={th}>Car</th>
                    <th style={th}>Price</th>
                    <th style={th}>Status</th>
                    <th style={th}>Views</th>
                    <th style={th}>Favorites</th>
                    <th style={th}>Created</th>
                    <th style={th}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {data!.items.map((c) => (
                    <tr key={c.id} style={{ borderTop: "1px solid var(--color-border)" }}>
                      <td style={td}>
                        <div className="row" style={{ gap: 10 }}>
                          <div style={{ width: 64, height: 48, background: "#1f1f1f", borderRadius: 6, overflow: "hidden" }}>
                            {c.main_image && <img src={c.main_image} alt="" style={{ width: "100%", height: "100%", objectFit: "cover" }} />}
                          </div>
                          <div>
                            <Link to={`/cars/${c.id}`} style={{ fontWeight: 600 }}>{c.make} {c.model}</Link>
                            <div className="text-sm muted">{c.year} · {formatMileage(c.mileage)}</div>
                          </div>
                        </div>
                      </td>
                      <td style={td}>{formatCurrency(c.price, c.currency)}</td>
                      <td style={td}><StatusBadge status={c.status} /></td>
                      <td style={td}>
                        <button
                          className="btn btn-ghost btn-sm"
                          style={{ padding: "2px 6px" }}
                          onClick={() => setStatsFor({ id: c.id, label: `${c.make} ${c.model}` })}
                          title="See how many people viewed this listing per day"
                        >
                          {c.views_count} · Stats
                        </button>
                      </td>
                      <td style={td}>{c.favorites_count}</td>
                      <td style={td}>{timeAgo(c.published_at)}</td>
                      <td style={td}>
                        <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                          <Link to={`/dashboard/listings/${c.id}/edit`} className="btn btn-ghost btn-sm">Edit</Link>
                          {c.status === "ACTIVE" && <button className="btn btn-ghost btn-sm" onClick={() => setStatus(c.id, "PAUSED")}>Pause</button>}
                          {(c.status === "PAUSED" || c.status === "DRAFT") && <button className="btn btn-ghost btn-sm" onClick={() => setStatus(c.id, "ACTIVE")}>{c.status === "DRAFT" ? "Publish" : "Activate"}</button>}
                          {c.status !== "SOLD" && <button className="btn btn-ghost btn-sm" onClick={() => setStatus(c.id, "SOLD")}>Mark sold</button>}
                          <button className="btn btn-ghost btn-sm" onClick={() => onDuplicate(c.id)}>Duplicate</button>
                          <button className="btn btn-ghost btn-sm" onClick={() => onDelete(c.id)} style={{ color: "var(--color-red)" }}>Delete</button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

      {data && data.total_pages > 1 && (
        <div className="row" style={{ marginTop: 16, justifyContent: "center", gap: 6 }}>
          {Array.from({ length: data.total_pages }).map((_, i) => (
            <button
              key={i}
              onClick={() => setPage(i + 1)}
              className={`btn btn-sm ${page === i + 1 ? "btn-primary" : "btn-outline"}`}
            >
              {i + 1}
            </button>
          ))}
        </div>
      )}

      {showQuickAdd && (
        <QuickAddListingModal
          onClose={() => setShowQuickAdd(false)}
          onCreated={(carId) => {
            setShowQuickAdd(false);
            navigate(`/dashboard/listings/${carId}/edit`);
          }}
        />
      )}

      {statsFor && (
        <ListingStatsModal
          carId={statsFor.id}
          carLabel={statsFor.label}
          onClose={() => setStatsFor(null)}
        />
      )}
    </div>
  );
};

const FilterTab: React.FC<{ label: string; status?: string }> = ({ label, status }) => {
  const [params, setParams] = useSearchParams();
  const active = (params.get("status") || undefined) === status;
  return (
    <button
      className={`btn btn-sm ${active ? "btn-primary" : "btn-outline"}`}
      onClick={() => {
        const p = new URLSearchParams(params);
        if (status) p.set("status", status); else p.delete("status");
        setParams(p);
      }}
    >
      {label}
    </button>
  );
};

const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const colorMap: Record<string, string> = {
    ACTIVE: "badge-green",
    PENDING: "badge-amber",
    SOLD: "badge-red",
    PAUSED: "badge",
    DRAFT: "badge",
    REJECTED: "badge-red",
    EXPIRED: "badge",
  };
  return <span className={`badge ${colorMap[status] || ""}`}>{statusLabel(status)}</span>;
};

const th: React.CSSProperties = { padding: "12px 12px", fontSize: 13, color: "var(--color-text-muted)", textTransform: "uppercase", letterSpacing: 0.4 };
const td: React.CSSProperties = { padding: "12px 12px", fontSize: 14, verticalAlign: "middle" };
