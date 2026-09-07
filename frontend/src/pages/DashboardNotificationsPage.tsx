import React from "react";
import { Link } from "react-router-dom";
import { notificationsService } from "@/services";
import { useAsync } from "@/hooks/useAsync";
import { EmptyState, ErrorState, LoadingBlock } from "@/components/States";
import { formatDateTime, timeAgo } from "@/utils/format";
import toast from "react-hot-toast";

export const DashboardNotificationsPage: React.FC = () => {
  const { data, loading, error, reload } = useAsync(() => notificationsService.list(1, 100), []);

  if (loading) return <LoadingBlock />;
  if (error) return <ErrorState onRetry={reload} />;

  const list = data?.items ?? [];

  const markRead = async (id: string) => {
    try {
      await notificationsService.markRead(id);
      reload();
    } catch {}
  };

  const markAll = async () => {
    try {
      await notificationsService.markAllRead();
      reload();
      toast.success("All notifications marked as read");
    } catch {}
  };

  return (
    <div>
      <div className="row-between" style={{ marginBottom: 16 }}>
        <div>
          <h1>Notifications</h1>
          <p className="text-sm muted">{data?.total} total</p>
        </div>
        <button className="btn btn-outline btn-sm" onClick={markAll}>Mark all read</button>
      </div>

      {list.length === 0 ? (
        <EmptyState title="Nothing yet" description="You'll see notifications when you receive messages or status updates." />
      ) : (
        <div className="card" style={{ overflow: "hidden" }}>
          {list.map((n) => (
            <Link
              key={n.id}
              to={n.data?.car_id ? `/cars/${n.data.car_id}` : "#"}
              onClick={() => markRead(n.id)}
              style={{
                display: "block", padding: 14, borderBottom: "1px solid var(--color-border)",
                background: n.is_read ? "#fff" : "rgba(37, 99, 235, 0.04)",
              }}
            >
              <div className="row-between">
                <div style={{ fontWeight: 700 }}>{n.title}</div>
                <span className="text-sm muted">{timeAgo(n.created_at)}</span>
              </div>
              {n.body && <p className="text-sm muted" style={{ marginTop: 4 }}>{n.body}</p>}
              <div className="text-sm muted" style={{ marginTop: 4, fontSize: 12 }}>{formatDateTime(n.created_at)}</div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
};