import React, { useState } from "react";
import { superAdminService } from "@/services";
import { useAsync } from "@/hooks/useAsync";
import { ErrorState, LoadingBlock } from "@/components/States";
import { formatDateTime } from "@/utils/format";

export const SuperAdminAuditLogsPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [action, setAction] = useState("");
  const { data, loading, error, reload } = useAsync(
    () => superAdminService.auditLogs({ action: action || undefined, page, limit: 50 }),
    [action, page]
  );

  return (
    <div>
      <h1 style={{ color: "#fff", marginBottom: 16 }}>Audit Logs</h1>

      <input
        className="input"
        placeholder="Filter by action (e.g. ADMIN_APPROVED_LISTING)"
        value={action}
        onChange={(e) => setAction(e.target.value)}
        style={{ maxWidth: 360, marginBottom: 16, background: "#0a0a0a", color: "#fff", borderColor: "#1f1f1f" }}
      />

      {loading ? <LoadingBlock /> : error ? <ErrorState onRetry={reload} /> : (
        <div style={{ background: "#161616", borderRadius: 12, overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", color: "#fff" }}>
            <thead>
              <tr style={{ background: "#0f0f0f" }}>
                <th style={th}>Action</th>
                <th style={th}>Resource</th>
                <th style={th}>IP</th>
                <th style={th}>When</th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map((log: any) => (
                <tr key={log.id} style={{ borderTop: "1px solid #1f1f1f" }}>
                  <td style={td}>
                    <code style={{ background: "#0f0f0f", padding: "2px 6px", borderRadius: 4, fontSize: 12 }}>{log.action}</code>
                  </td>
                  <td style={td}>
                    {log.resource_type && <>{log.resource_type}: {log.resource_id}</>}
                  </td>
                  <td style={td}>{log.ip_address || "—"}</td>
                  <td style={td}>{formatDateTime(log.created_at)}</td>
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
const td: React.CSSProperties = { padding: 12, fontSize: 13, color: "#e5e7eb" };