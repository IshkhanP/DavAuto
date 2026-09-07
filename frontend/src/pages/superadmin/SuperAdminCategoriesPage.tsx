import React, { useState } from "react";
import { superAdminService } from "@/services";
import { useAsync } from "@/hooks/useAsync";
import { ErrorState, LoadingBlock } from "@/components/States";
import toast from "react-hot-toast";

export const SuperAdminCategoriesPage: React.FC = () => {
  const { data, loading, error, reload } = useAsync(() => superAdminService.categories(), []);
  const [show, setShow] = useState(false);
  const [form, setForm] = useState({ name: "", slug: "", icon: "", display_order: 0 });
  const [saving, setSaving] = useState(false);

  const create = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      await superAdminService.createCategory(form);
      toast.success("Category created");
      setShow(false);
      setForm({ name: "", slug: "", icon: "", display_order: 0 });
      reload();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Could not create");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <div className="row-between" style={{ marginBottom: 16 }}>
        <h1 style={{ color: "#fff" }}>Categories</h1>
        <button className="btn btn-blue" onClick={() => setShow(true)}>+ New Category</button>
      </div>

      {loading ? <LoadingBlock /> : error ? <ErrorState onRetry={reload} /> : (
        <div style={{ background: "#161616", borderRadius: 12, overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", color: "#fff" }}>
            <thead><tr style={{ background: "#0f0f0f" }}><th style={th}>Name</th><th style={th}>Slug</th><th style={th}>Icon</th><th style={th}>Order</th><th style={th}>Status</th></tr></thead>
            <tbody>
              {data?.map((c: any) => (
                <tr key={c.id} style={{ borderTop: "1px solid #1f1f1f" }}>
                  <td style={td}>{c.name}</td>
                  <td style={td}>{c.slug}</td>
                  <td style={td}>{c.icon || "—"}</td>
                  <td style={td}>{c.display_order}</td>
                  <td style={td}>{c.is_active ? <span className="badge badge-green">Active</span> : <span className="badge">Inactive</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {show && (
        <div className="modal-backdrop" onClick={() => setShow(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ background: "#161616", color: "#fff" }}>
            <h2 style={{ marginBottom: 16 }}>New Category</h2>
            <form onSubmit={create}>
              <div className="field"><label>Name</label><input className="input" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} style={dark} /></div>
              <div className="field"><label>Slug</label><input className="input" required value={form.slug} onChange={(e) => setForm({ ...form, slug: e.target.value.toLowerCase() })} style={dark} /></div>
              <div className="field"><label>Icon</label><input className="input" value={form.icon} onChange={(e) => setForm({ ...form, icon: e.target.value })} style={dark} /></div>
              <div className="field"><label>Display order</label><input className="input" type="number" value={form.display_order} onChange={(e) => setForm({ ...form, display_order: Number(e.target.value) })} style={dark} /></div>
              <div className="row" style={{ gap: 8, justifyContent: "flex-end" }}>
                <button type="button" className="btn btn-outline" onClick={() => setShow(false)}>Cancel</button>
                <button type="submit" className="btn btn-blue" disabled={saving}>{saving ? "Saving..." : "Save"}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

const th: React.CSSProperties = { padding: 12, textAlign: "left", fontSize: 12, color: "#9ca3af", textTransform: "uppercase" };
const td: React.CSSProperties = { padding: 12, fontSize: 13, color: "#e5e7eb" };
const dark: React.CSSProperties = { background: "#0a0a0a", color: "#fff", borderColor: "#1f1f1f" };