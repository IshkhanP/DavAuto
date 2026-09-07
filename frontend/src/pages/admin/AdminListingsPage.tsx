import React, { useState } from "react";
import { adminService } from "@/services";
import { useAsync } from "@/hooks/useAsync";
import { ErrorState, LoadingBlock } from "@/components/States";
import { formatCurrency, formatMileage, fuelLabel, timeAgo } from "@/utils/format";
import toast from "react-hot-toast";

export const AdminListingsPage: React.FC = () => {
  const [status, setStatus] = useState<string>("PENDING");
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const { data, loading, error, reload } = useAsync(
    () => adminService.listings({ status, page, limit: 20 }),
    [status, page]
  );

  const toggleSelect = (id: string) => {
    setSelected((prev) => {
      const n = new Set(prev);
      if (n.has(id)) n.delete(id); else n.add(id);
      return n;
    });
  };

  const act = async (id: string, action: string) => {
    try {
      if (action === "approve") await adminService.approve(id);
      else if (action === "reject") await adminService.reject(id, prompt("Reason?") || "");
      else if (action === "feature") await adminService.feature(id, true);
      toast.success("Listing updated");
      reload();
    } catch {
      toast.error("Could not update listing");
    }
  };

  const bulk = async (action: string) => {
    if (selected.size === 0) return;
    try {
      const res = await adminService.bulkAction(Array.from(selected), action);
      toast.success(`${res.affected} listings updated`);
      setSelected(new Set());
      reload();
    } catch {
      toast.error("Bulk action failed");
    }
  };

  return (
    <div style={{ padding: 24 }}>
      <div className="row-between" style={{ marginBottom: 16 }}>
        <h1 style={{ color: "#fff" }}>Listings</h1>
      </div>

      <div className="row" style={{ gap: 6, marginBottom: 12, flexWrap: "wrap" }}>
        {["PENDING", "ACTIVE", "REJECTED", "SOLD", "PAUSED"].map((s) => (
          <button key={s} className={`btn btn-sm ${status === s ? "btn-primary" : "btn-outline"}`} onClick={() => { setStatus(s); setPage(1); setSelected(new Set()); }}>
            {fuelLabel(s)}
          </button>
        ))}
      </div>

      {selected.size > 0 && (
        <div className="row" style={{ gap: 8, marginBottom: 12, padding: 12, background: "#161616", borderRadius: 10 }}>
          <span style={{ color: "#9ca3af" }}>{selected.size} selected</span>
          <button className="btn btn-sm btn-blue" onClick={() => bulk("approve")}>Approve</button>
          <button className="btn btn-sm btn-outline" onClick={() => bulk("hide")}>Hide</button>
          <button className="btn btn-sm btn-outline" onClick={() => bulk("feature")}>Feature</button>
          <button className="btn btn-sm btn-danger" onClick={() => bulk("delete")}>Delete</button>
          <button className="btn btn-sm btn-ghost" onClick={() => setSelected(new Set())}>Clear</button>
        </div>
      )}

      {loading ? <LoadingBlock /> : error ? <ErrorState onRetry={reload} /> : (
        <div style={{ background: "#161616", borderRadius: 12, overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", color: "#fff", minWidth: 900 }}>
            <thead>
              <tr style={{ background: "#0f0f0f" }}>
                <th style={th}></th>
                <th style={th}>Car</th>
                <th style={th}>Seller</th>
                <th style={th}>Price</th>
                <th style={th}>Status</th>
                <th style={th}>Created</th>
                <th style={th}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map((c: any) => (
                <tr key={c.id} style={{ borderTop: "1px solid #1f1f1f" }}>
                  <td style={td}>
                    <input type="checkbox" checked={selected.has(c.id)} onChange={() => toggleSelect(c.id)} />
                  </td>
                  <td style={td}>
                    <div style={{ fontWeight: 700 }}>{c.make_name} {c.model_name}</div>
                    <div className="text-sm" style={{ color: "#9ca3af" }}>{c.year} · {formatMileage(c.mileage)}</div>
                  </td>
                  <td style={td}>{c.seller?.full_name}</td>
                  <td style={td}>{formatCurrency(c.price, c.currency)}</td>
                  <td style={td}>{fuelLabel(c.status)}</td>
                  <td style={td}>{timeAgo(c.created_at)}</td>
                  <td style={td}>
                    <div style={{ display: "flex", gap: 4 }}>
                      {c.status === "PENDING" && <>
                        <button className="btn btn-sm btn-blue" onClick={() => act(c.id, "approve")}>Approve</button>
                        <button className="btn btn-sm btn-danger" onClick={() => act(c.id, "reject")}>Reject</button>
                      </>}
                      <button className="btn btn-sm btn-outline" onClick={() => act(c.id, "feature")}>Feature</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {data && data.total_pages > 1 && (
        <div className="row" style={{ marginTop: 16, gap: 6, justifyContent: "center" }}>
          {Array.from({ length: data.total_pages }).map((_, i) => (
            <button key={i} className={`btn btn-sm ${page === i + 1 ? "btn-primary" : "btn-outline"}`} onClick={() => setPage(i + 1)}>{i + 1}</button>
          ))}
        </div>
      )}
    </div>
  );
};

const th: React.CSSProperties = { padding: 12, textAlign: "left", fontSize: 12, color: "#9ca3af", textTransform: "uppercase" };
const td: React.CSSProperties = { padding: 12, fontSize: 14, color: "#e5e7eb" };