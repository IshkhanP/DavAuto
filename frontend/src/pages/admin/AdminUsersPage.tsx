import React, { useState } from "react";
import { adminService } from "@/services";
import { useAsync } from "@/hooks/useAsync";
import { ErrorState, LoadingBlock } from "@/components/States";
import { formatDate } from "@/utils/format";
import toast from "react-hot-toast";

export const AdminUsersPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const { data, loading, error, reload } = useAsync(
    () => adminService.users({ q, page, limit: 24 }),
    [q, page]
  );

  const suspend = async (id: string) => {
    if (!confirm("Suspend this user?")) return;
    try {
      await adminService.updateUser(id, { status: "SUSPENDED" });
      toast.success("User suspended");
      reload();
    } catch {
      toast.error("Could not suspend");
    }
  };

  const restore = async (id: string) => {
    try {
      await adminService.updateUser(id, { status: "ACTIVE" });
      toast.success("User restored");
      reload();
    } catch {
      toast.error("Could not restore");
    }
  };

  return (
    <div style={{ padding: 24 }}>
      <h1 style={{ color: "#fff", marginBottom: 16 }}>Users</h1>

      <input
        className="input"
        placeholder="Search by name or email..."
        value={q}
        onChange={(e) => setQ(e.target.value)}
        style={{ maxWidth: 360, marginBottom: 16 }}
      />

      {loading ? <LoadingBlock /> : error ? <ErrorState onRetry={reload} /> : (
        <div style={{ background: "#161616", borderRadius: 12, overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", color: "#fff", minWidth: 800 }}>
            <thead>
              <tr style={{ background: "#0f0f0f" }}>
                <th style={th}>Name</th>
                <th style={th}>Email</th>
                <th style={th}>Roles</th>
                <th style={th}>Listings</th>
                <th style={th}>Status</th>
                <th style={th}>Last login</th>
                <th style={th}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map((u: any) => (
                <tr key={u.id} style={{ borderTop: "1px solid #1f1f1f" }}>
                  <td style={td}>{u.full_name}</td>
                  <td style={td}>{u.email}</td>
                  <td style={td}>
                    <div className="row" style={{ gap: 4 }}>
                      {u.roles.map((r: string) => <span key={r} className="badge">{r}</span>)}
                    </div>
                  </td>
                  <td style={td}>{u.cars_count}</td>
                  <td style={td}>
                    <span className={`badge ${u.status === "ACTIVE" ? "badge-green" : u.status === "SUSPENDED" ? "badge-amber" : "badge-red"}`}>
                      {u.status}
                    </span>
                  </td>
                  <td style={td}>{u.last_login_at ? formatDate(u.last_login_at) : "—"}</td>
                  <td style={td}>
                    {u.status === "ACTIVE" ? (
                      <button className="btn btn-sm btn-outline" onClick={() => suspend(u.id)}>Suspend</button>
                    ) : (
                      <button className="btn btn-sm btn-blue" onClick={() => restore(u.id)}>Restore</button>
                    )}
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