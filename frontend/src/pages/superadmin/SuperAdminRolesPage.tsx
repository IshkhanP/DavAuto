import React, { useState } from "react";
import { superAdminService } from "@/services";
import { useAsync } from "@/hooks/useAsync";
import { ErrorState, LoadingBlock } from "@/components/States";
import toast from "react-hot-toast";
import type { Permission, Role } from "@/types";

export const SuperAdminRolesPage: React.FC = () => {
  const { data, loading, error, reload } = useAsync(() => superAdminService.roles({ limit: 100 }), []);
  const perms = useAsync(() => superAdminService.permissions(), []);

  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ name: "", slug: "", description: "", permission_ids: [] as string[] });
  const [submitting, setSubmitting] = useState(false);

  const create = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      await superAdminService.createRole(form);
      toast.success("Role created");
      setShowCreate(false);
      setForm({ name: "", slug: "", description: "", permission_ids: [] });
      reload();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Could not create role");
    } finally {
      setSubmitting(false);
    }
  };

  const togglePerm = (id: string) => {
    setForm((p) => ({
      ...p,
      permission_ids: p.permission_ids.includes(id)
        ? p.permission_ids.filter((x) => x !== id)
        : [...p.permission_ids, id],
    }));
  };

  return (
    <div>
      <div className="row-between" style={{ marginBottom: 16 }}>
        <h1 style={{ color: "#fff" }}>Roles & Permissions</h1>
        <button className="btn btn-blue" onClick={() => setShowCreate(true)}>+ Create Role</button>
      </div>

      {loading ? <LoadingBlock /> : error ? <ErrorState onRetry={reload} /> : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 12 }}>
          {data?.items.map((r: Role) => (
            <div key={r.id} style={{ background: "#161616", border: "1px solid #1f1f1f", borderRadius: 12, padding: 16 }}>
                <div className="row-between">
                  <h3 style={{ fontSize: 16 }}>{r.name}</h3>
                  {r.is_system && <span className="badge badge-blue">System</span>}
                </div>
                <p style={{ color: "#9ca3af", fontSize: 13, marginTop: 4 }}>{r.description || "Custom role"}</p>
                <div style={{ marginTop: 10, fontSize: 12, color: "#9ca3af" }}>
                  {r.permissions.length} permissions
                </div>
                <div style={{ marginTop: 10, display: "flex", flexWrap: "wrap", gap: 4 }}>
                  {r.permissions.slice(0, 6).map((p: Permission) => (
                    <span key={p.id} className="badge">{p.code}</span>
                  ))}
                  {r.permissions.length > 6 && <span className="badge">+{r.permissions.length - 6} more</span>}
                </div>
              </div>
            ))}
        </div>
      )}

      {showCreate && (
        <div className="modal-backdrop" onClick={() => setShowCreate(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ background: "#161616", color: "#fff", maxWidth: 700 }}>
            <h2 style={{ marginBottom: 16 }}>Create Role</h2>
            <form onSubmit={create}>
              <div className="field">
                <label>Name</label>
                <input className="input" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} style={{ background: "#0a0a0a", color: "#fff", borderColor: "#1f1f1f" }} />
              </div>
              <div className="field">
                <label>Slug</label>
                <input className="input" required value={form.slug} onChange={(e) => setForm({ ...form, slug: e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, "-") })} style={{ background: "#0a0a0a", color: "#fff", borderColor: "#1f1f1f" }} />
              </div>
              <div className="field">
                <label>Description</label>
                <input className="input" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} style={{ background: "#0a0a0a", color: "#fff", borderColor: "#1f1f1f" }} />
              </div>
              <div className="field">
                <label>Permissions</label>
                <div style={{ maxHeight: 280, overflowY: "auto", padding: 12, background: "#0a0a0a", borderRadius: 8, border: "1px solid #1f1f1f" }}>
                  {Object.entries(
                    (perms.data ?? []).reduce<Record<string, Permission[]>>((acc, p) => {
                      (acc[p.category] = acc[p.category] || []).push(p);
                      return acc;
                    }, {})
                  ).map(([cat, list]) => (
                    <div key={cat} style={{ marginBottom: 12 }}>
                      <div style={{ fontWeight: 700, fontSize: 12, color: "#9ca3af", textTransform: "uppercase", marginBottom: 6 }}>{cat}</div>
                      {list.map((p) => (
                        <label key={p.id} style={{ display: "flex", alignItems: "center", gap: 8, padding: "4px 0", cursor: "pointer" }}>
                          <input type="checkbox" checked={form.permission_ids.includes(p.id)} onChange={() => togglePerm(p.id)} />
                          <span className="text-sm">{p.name}</span>
                          <code style={{ fontSize: 11, color: "#9ca3af" }}>{p.code}</code>
                        </label>
                      ))}
                    </div>
                  ))}
                </div>
              </div>
              <div className="row" style={{ gap: 8, justifyContent: "flex-end" }}>
                <button type="button" className="btn btn-outline" onClick={() => setShowCreate(false)}>Cancel</button>
                <button type="submit" className="btn btn-blue" disabled={submitting}>{submitting ? "Creating..." : "Create"}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};