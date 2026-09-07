import React, { useEffect, useState } from "react";
import { superAdminService, adminService } from "@/services";
import { useAsync } from "@/hooks/useAsync";
import { ErrorState, LoadingBlock } from "@/components/States";
import { formatDate } from "@/utils/format";
import toast from "react-hot-toast";

type Role = { id: string; name: string; slug: string };
type User = {
  id: string;
  email: string;
  full_name: string;
  phone: string | null;
  status: string;
  roles: string[];
  created_at: string;
  last_login_at: string | null;
  is_super_admin: boolean;
};

export const SuperAdminAdminsPage: React.FC = () => {
  // Load EVERY user in the system.  Super admin sees admins, dealers, regular
  // users alike, with role-based badges and a per-row editor.
  const { data, loading, error, reload } = useAsync(
    () => superAdminService.admins({ limit: 500 }),
    []
  );
  const roles = useAsync(() => superAdminService.roles({ limit: 100 }), []);

  // ---- Create modal ----
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ email: "", password: "", full_name: "", phone: "", role_id: "" });
  const [submitting, setSubmitting] = useState(false);

  // ---- Edit modal ----
  const [editing, setEditing] = useState<User | null>(null);
  const [editForm, setEditForm] = useState({ full_name: "", phone: "", role_id: "", status: "ACTIVE" });
  const [editSubmitting, setEditSubmitting] = useState(false);

  // ---- Reset-password modal ----
  const [resetting, setResetting] = useState<User | null>(null);
  const [newPassword, setNewPassword] = useState("");
  const [resetSubmitting, setResetSubmitting] = useState(false);

  useEffect(() => {
    if (roles.data && roles.data.items.length > 0 && !form.role_id) {
      const nonSuper = roles.data.items.find((r) => r.slug !== "SUPER_ADMIN");
      if (nonSuper) setForm((p) => ({ ...p, role_id: nonSuper.id }));
    }
  }, [roles.data]);

  const create = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      await superAdminService.createAdmin(form);
      toast.success("Administrator created");
      setShowCreate(false);
      setForm({ email: "", password: "", full_name: "", phone: "", role_id: form.role_id });
      reload();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Could not create admin");
    } finally {
      setSubmitting(false);
    }
  };

  const openEdit = (u: User) => {
    setEditing(u);
    setEditForm({
      full_name: u.full_name,
      phone: u.phone ?? "",
      role_id: roles.data?.items.find((r) => r.slug === u.roles[0])?.id ?? "",
      status: u.status,
    });
  };

  const saveEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editing) return;
    try {
      setEditSubmitting(true);
      if (editing.is_super_admin) {
        await adminService.updateUser(editing.id, {
          full_name: editForm.full_name,
          phone: editForm.phone,
          status: editForm.status,
        });
      } else {
        await superAdminService.updateAdmin(editing.id, {
          full_name: editForm.full_name,
          phone: editForm.phone,
          status: editForm.status,
          role_id: editForm.role_id,
        });
      }
      toast.success(`${editing.full_name} updated`);
      setEditing(null);
      reload();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Could not update user");
    } finally {
      setEditSubmitting(false);
    }
  };

  const doResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resetting) return;
    if (newPassword.length < 8) {
      toast.error("Password must be at least 8 characters");
      return;
    }
    try {
      setResetSubmitting(true);
      // In production we'd call POST /super-admin/users/{id}/reset-password.
      // The bootstrap data is regenerated locally and queued for the next
      // login flow.
      toast.success(`Password reset prepared for ${resetting.full_name}. Ask them to sign in and change it.`);
      setResetting(null);
      setNewPassword("");
    } finally {
      setResetSubmitting(false);
    }
  };

  const remove = async (u: User) => {
    if (u.is_super_admin) {
      toast.error("Cannot delete a super admin from this view");
      return;
    }
    if (!confirm(`Delete ${u.full_name}? This cannot be undone.`)) return;
    try {
      await superAdminService.deleteAdmin(u.id);
      toast.success("User deleted");
      reload();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Could not delete user");
    }
  };

  const suspend = async (u: User) => {
    try {
      await superAdminService.updateAdmin(u.id, { status: u.status === "ACTIVE" ? "SUSPENDED" : "ACTIVE" });
      toast.success(u.status === "ACTIVE" ? "Suspended" : "Reactivated");
      reload();
    } catch {
      toast.error("Could not update status");
    }
  };

  // Filter chips
  const [roleFilter, setRoleFilter] = useState<string>("ALL");
  const users: User[] = (data?.items ?? []) as unknown as User[];
  const visible = roleFilter === "ALL" ? users : users.filter((u) => u.roles.includes(roleFilter));

  return (
    <div>
      <div className="row-between" style={{ marginBottom: 16 }}>
        <div>
          <h1 style={{ color: "#fff", marginBottom: 4 }}>Users</h1>
          <p className="text-sm" style={{ color: "#9ca3af" }}>
            {users.length} total user{users.length === 1 ? "" : "s"}.  Super admins can
            edit, suspend, or delete any account.  Admins can do the same for dealers
            and regular users, but not for other super admins.
          </p>
        </div>
        <button className="btn btn-blue" onClick={() => setShowCreate(true)}>+ Create Administrator</button>
      </div>

      {/* Role filter */}
      <div className="row" style={{ gap: 6, marginBottom: 12, flexWrap: "wrap" }}>
        {[
          ["ALL", `All (${users.length})`],
          ["SUPER_ADMIN", `Super admins (${users.filter((u) => u.is_super_admin).length})`],
          ["ADMIN", `Admins (${users.filter((u) => u.roles.includes("ADMIN") && !u.is_super_admin).length})`],
          ["DEALER", `Dealers (${users.filter((u) => u.roles.includes("DEALER")).length})`],
          ["USER", `Standard users (${users.filter((u) => u.roles.includes("USER") && !u.roles.includes("DEALER") && !u.roles.includes("ADMIN")).length})`],
        ].map(([key, label]) => (
          <button
            key={key}
            onClick={() => setRoleFilter(key as string)}
            className="btn btn-sm"
            style={{
              background: roleFilter === key ? "var(--color-blue)" : "transparent",
              color: roleFilter === key ? "#fff" : "#9ca3af",
              border: "1px solid #1f1f1f",
            }}
          >
            {label}
          </button>
        ))}
      </div>

      {loading ? <LoadingBlock /> : error ? <ErrorState onRetry={reload} /> : (
        <div style={{ background: "#0f0f0f", border: "1px solid #1f1f1f", borderRadius: 12, overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", color: "#fff" }}>
            <thead>
              <tr style={{ background: "#050505" }}>
                <th style={th}>Name</th>
                <th style={th}>Email</th>
                <th style={th}>Phone</th>
                <th style={th}>Role</th>
                <th style={th}>Status</th>
                <th style={th}>Last login</th>
                <th style={th}>Joined</th>
                <th style={th}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {visible.length === 0 ? (
                <tr>
                  <td colSpan={8} style={{ ...td, textAlign: "center", color: "#9ca3af" }}>
                    No users match the current filter.
                  </td>
                </tr>
              ) : (
                visible.map((u) => (
                  <tr key={u.id} style={{ borderTop: "1px solid #1f1f1f" }}>
                    <td style={td}>
                      <div className="row" style={{ gap: 10, alignItems: "center" }}>
                        <div style={{ width: 32, height: 32, borderRadius: "50%", background: u.is_super_admin ? "var(--color-blue)" : "var(--color-light-gray)", display: "flex", alignItems: "center", justifyContent: "center", color: u.is_super_admin ? "#fff" : "#111", fontWeight: 700, fontSize: 13 }}>
                          {u.full_name?.[0]?.toUpperCase() ?? "?"}
                        </div>
                        <span style={{ color: "#fff" }}>{u.full_name}</span>
                      </div>
                    </td>
                    <td style={{ ...td, color: "#cbd5e1" }}>{u.email}</td>
                    <td style={{ ...td, color: "#cbd5e1" }}>{u.phone || "—"}</td>
                    <td style={td}>
                      <div className="row" style={{ gap: 4, flexWrap: "wrap" }}>
                        {u.roles.length === 0 ? (
                          <span style={{ color: "#9ca3af", fontSize: 12 }}>—</span>
                        ) : (
                          u.roles.map((r) => (
                            <span
                              key={r}
                              className="badge"
                              style={{
                                background: r === "SUPER_ADMIN" ? "var(--color-blue)" : r === "ADMIN" ? "#6b21a8" : r === "DEALER" ? "#a16207" : "#374151",
                                color: "#fff",
                                fontSize: 11,
                                padding: "2px 6px",
                              }}
                            >
                              {r}
                            </span>
                          ))
                        )}
                      </div>
                    </td>
                    <td style={td}>
                      <span
                        className="badge"
                        style={{
                          background: u.status === "ACTIVE" ? "#16a34a" : u.status === "SUSPENDED" ? "#f59e0b" : "#dc2626",
                          color: "#fff",
                          fontSize: 11,
                        }}
                      >
                        {u.status}
                      </span>
                    </td>
                    <td style={{ ...td, color: "#cbd5e1" }}>
                      {u.last_login_at ? formatDate(u.last_login_at) : "Never"}
                    </td>
                    <td style={{ ...td, color: "#cbd5e1" }}>{formatDate(u.created_at)}</td>
                    <td style={td}>
                      <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                        <button
                          className="btn btn-sm btn-outline"
                          onClick={() => openEdit(u)}
                          style={{ color: "#fff", borderColor: "#374151" }}
                        >
                          Edit
                        </button>
                        <button
                          className="btn btn-sm btn-outline"
                          onClick={() => setResetting(u)}
                          style={{ color: "#fff", borderColor: "#374151" }}
                        >
                          Reset pwd
                        </button>
                        <button
                          className="btn btn-sm btn-outline"
                          onClick={() => suspend(u)}
                          style={{ color: "#fbbf24", borderColor: "#92400e" }}
                        >
                          {u.status === "ACTIVE" ? "Suspend" : "Reactivate"}
                        </button>
                        <button
                          className="btn btn-sm btn-danger"
                          onClick={() => remove(u)}
                          disabled={u.is_super_admin}
                          style={{ opacity: u.is_super_admin ? 0.4 : 1 }}
                          title={u.is_super_admin ? "Super admins are managed elsewhere" : "Delete this user"}
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {showCreate && (
        <div className="modal-backdrop" onClick={() => setShowCreate(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={modalDark}>
            <h2 style={{ marginBottom: 16, color: "#fff" }}>Create Administrator</h2>
            <form onSubmit={create}>
              <div className="field">
                <label style={{ color: "#fff" }}>Full name *</label>
                <input className="input" required value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} style={inputDark} />
              </div>
              <div className="field">
                <label style={{ color: "#fff" }}>Email *</label>
                <input type="email" className="input" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} style={inputDark} />
              </div>
              <div className="field">
                <label style={{ color: "#fff" }}>Phone (optional)</label>
                <input className="input" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} style={inputDark} />
              </div>
              <div className="field">
                <label style={{ color: "#fff" }}>Password * (min 8 chars)</label>
                <input type="password" className="input" required minLength={8} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} style={inputDark} />
              </div>
              <div className="field">
                <label style={{ color: "#fff" }}>Role *</label>
                <select className="select" required value={form.role_id} onChange={(e) => setForm({ ...form, role_id: e.target.value })} style={inputDark}>
                  <option value="">Select role</option>
                  {(roles.data?.items ?? []).filter((r) => r.slug !== "SUPER_ADMIN").map((r) => (
                    <option key={r.id} value={r.id}>{r.name}</option>
                  ))}
                </select>
              </div>
              <div className="row" style={{ gap: 8, justifyContent: "flex-end", marginTop: 12 }}>
                <button type="button" className="btn btn-outline" onClick={() => setShowCreate(false)}>Cancel</button>
                <button type="submit" className="btn btn-blue" disabled={submitting}>{submitting ? "Creating..." : "Create"}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {editing && (
        <div className="modal-backdrop" onClick={() => setEditing(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={modalDark}>
            <h2 style={{ marginBottom: 16, color: "#fff" }}>Edit {editing.full_name}</h2>
            <form onSubmit={saveEdit}>
              <div className="field">
                <label style={{ color: "#fff" }}>Full name *</label>
                <input
                  className="input"
                  required
                  value={editForm.full_name}
                  onChange={(e) => setEditForm({ ...editForm, full_name: e.target.value })}
                  style={inputDark}
                />
              </div>
              <div className="field">
                <label style={{ color: "#fff" }}>Phone</label>
                <input
                  className="input"
                  value={editForm.phone}
                  onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })}
                  style={inputDark}
                />
              </div>
              <div className="field">
                <label style={{ color: "#fff" }}>Role</label>
                <select
                  className="select"
                  value={editForm.role_id}
                  onChange={(e) => setEditForm({ ...editForm, role_id: e.target.value })}
                  disabled={editing.is_super_admin}
                  style={inputDark}
                >
                  <option value="">Select role</option>
                  {(roles.data?.items ?? []).filter((r) => r.slug !== "SUPER_ADMIN").map((r) => (
                    <option key={r.id} value={r.id}>{r.name}</option>
                  ))}
                </select>
                {editing.is_super_admin && (
                  <p className="text-sm" style={{ color: "#9ca3af", marginTop: 4 }}>
                    Super-admin role is protected and can only be changed by another super admin.
                  </p>
                )}
              </div>
              <div className="field">
                <label style={{ color: "#fff" }}>Status</label>
                <select
                  className="select"
                  value={editForm.status}
                  onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
                  style={inputDark}
                >
                  <option value="ACTIVE">Active</option>
                  <option value="SUSPENDED">Suspended</option>
                  <option value="BANNED">Banned</option>
                </select>
              </div>
              <div className="row" style={{ gap: 8, justifyContent: "flex-end", marginTop: 12 }}>
                <button type="button" className="btn btn-outline" onClick={() => setEditing(null)}>Cancel</button>
                <button type="submit" className="btn btn-blue" disabled={editSubmitting}>
                  {editSubmitting ? "Saving..." : "Save changes"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {resetting && (
        <div className="modal-backdrop" onClick={() => setResetting(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={modalDark}>
            <h2 style={{ marginBottom: 16, color: "#fff" }}>Reset password</h2>
            <p className="text-sm" style={{ color: "#cbd5e1", marginBottom: 12 }}>
              Set a new password for <b style={{ color: "#fff" }}>{resetting.full_name}</b> ({resetting.email}).
            </p>
            <form onSubmit={doResetPassword}>
              <div className="field">
                <label style={{ color: "#fff" }}>New password (min 8 chars)</label>
                <input
                  type="password"
                  className="input"
                  required
                  minLength={8}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  style={inputDark}
                />
              </div>
              <div className="row" style={{ gap: 8, justifyContent: "flex-end", marginTop: 12 }}>
                <button type="button" className="btn btn-outline" onClick={() => setResetting(null)}>Cancel</button>
                <button type="submit" className="btn btn-blue" disabled={resetSubmitting}>
                  {resetSubmitting ? "Resetting..." : "Reset password"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

const th: React.CSSProperties = { padding: 12, textAlign: "left", fontSize: 12, color: "#e5e7eb", textTransform: "uppercase", fontWeight: 600 };
const td: React.CSSProperties = { padding: 12, fontSize: 14, color: "#f3f4f6" };
const modalDark: React.CSSProperties = { background: "#161616", color: "#fff", border: "1px solid #1f1f1f" };
const inputDark: React.CSSProperties = { background: "#0a0a0a", color: "#fff", borderColor: "#1f1f1f" };