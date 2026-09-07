import React, { useState } from "react";
import { adminService } from "@/services";
import { useAsync } from "@/hooks/useAsync";
import { ErrorState, LoadingBlock } from "@/components/States";
import { formatDateTime } from "@/utils/format";
import toast from "react-hot-toast";

export const AdminReportsPage: React.FC = () => {
  const [status, setStatus] = useState<string>("PENDING");
  const [page, setPage] = useState(1);

  const { data, loading, error, reload } = useAsync(
    () => adminService.reports({ status, page, limit: 20 }),
    [status, page]
  );

  const resolve = async (id: string, action: string) => {
    try {
      await adminService.resolveReport(id, { status: "RESOLVED", action });
      toast.success("Report resolved");
      reload();
    } catch {
      toast.error("Could not resolve");
    }
  };

  return (
    <div style={{ padding: 24 }}>
      <h1 style={{ color: "#fff", marginBottom: 16 }}>Reports</h1>

      <div className="row" style={{ gap: 6, marginBottom: 12 }}>
        {["PENDING", "REVIEWING", "RESOLVED", "REJECTED"].map((s) => (
          <button key={s} className={`btn btn-sm ${status === s ? "btn-primary" : "btn-outline"}`} onClick={() => { setStatus(s); setPage(1); }}>
            {s}
          </button>
        ))}
      </div>

      {loading ? <LoadingBlock /> : error ? <ErrorState onRetry={reload} /> : (
        <div style={{ background: "#161616", borderRadius: 12, overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", color: "#fff", minWidth: 700 }}>
            <thead>
              <tr style={{ background: "#0f0f0f" }}>
                <th style={th}>Reason</th>
                <th style={th}>Description</th>
                <th style={th}>Created</th>
                <th style={th}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map((r: any) => (
                <tr key={r.id} style={{ borderTop: "1px solid #1f1f1f" }}>
                  <td style={td}>{r.reason}</td>
                  <td style={td}>{r.description || "—"}</td>
                  <td style={td}>{formatDateTime(r.created_at)}</td>
                  <td style={td}>
                    <div style={{ display: "flex", gap: 4 }}>
                      {r.car_id && <button className="btn btn-sm btn-outline" onClick={() => resolve(r.id, "hide_listing")}>Hide listing</button>}
                      {r.reported_user_id && <button className="btn btn-sm btn-danger" onClick={() => resolve(r.id, "suspend_user")}>Suspend user</button>}
                      <button className="btn btn-sm btn-ghost" onClick={() => resolve(r.id, "")}>Mark resolved</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

const th: React.CSSProperties = { padding: 12, textAlign: "left", fontSize: 12, color: "#9ca3af", textTransform: "uppercase" };
const td: React.CSSProperties = { padding: 12, fontSize: 14, color: "#e5e7eb" };