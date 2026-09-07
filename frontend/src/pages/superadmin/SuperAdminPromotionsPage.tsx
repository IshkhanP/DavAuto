import React, { useState } from "react";
import { superAdminService } from "@/services";
import { useAsync } from "@/hooks/useAsync";
import { ErrorState, LoadingBlock } from "@/components/States";
import { formatCurrency } from "@/utils/format";
import toast from "react-hot-toast";

export const SuperAdminPromotionsPage: React.FC = () => {
  const { data, loading, error, reload } = useAsync(() => superAdminService.promotionPackages(), []);
  const [show, setShow] = useState(false);
  const [form, setForm] = useState({
    name: "", slug: "", promotion_type: "FEATURED", description: "",
    price: 0, currency: "USD", duration_days: 14, max_active_per_user: 10, display_order: 0,
  });
  const [saving, setSaving] = useState(false);

  const create = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      await superAdminService.createPromotionPackage(form);
      toast.success("Package created");
      setShow(false);
      reload();
    } catch {
      toast.error("Could not create");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <div className="row-between" style={{ marginBottom: 16 }}>
        <h1 style={{ color: "#fff" }}>Promotion Packages</h1>
        <button className="btn btn-blue" onClick={() => setShow(true)}>+ New Package</button>
      </div>
      {loading ? <LoadingBlock /> : error ? <ErrorState onRetry={reload} /> : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 12 }}>
          {data?.map((p: any) => (
            <div key={p.id} style={{ background: "#161616", border: "1px solid #1f1f1f", borderRadius: 12, padding: 16 }}>
              <div className="row-between">
                <h3 style={{ fontSize: 16 }}>{p.name}</h3>
                <span className="badge badge-blue">{p.promotion_type}</span>
              </div>
              <p style={{ color: "#9ca3af", fontSize: 13, marginTop: 4 }}>{p.description || "—"}</p>
              <div style={{ marginTop: 12, fontSize: 24, fontWeight: 800, color: "#fff" }}>{formatCurrency(p.price, p.currency)}</div>
              <p style={{ color: "#9ca3af", fontSize: 12, marginTop: 4 }}>{p.duration_days} days</p>
            </div>
          ))}
        </div>
      )}

      {show && (
        <div className="modal-backdrop" onClick={() => setShow(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ background: "#161616", color: "#fff" }}>
            <h2 style={{ marginBottom: 16 }}>New Package</h2>
            <form onSubmit={create}>
              <div className="field"><label>Name</label><input className="input" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} style={{ background: "#0a0a0a", color: "#fff", borderColor: "#1f1f1f" }} /></div>
              <div className="field"><label>Slug</label><input className="input" required value={form.slug} onChange={(e) => setForm({ ...form, slug: e.target.value.toLowerCase() })} style={{ background: "#0a0a0a", color: "#fff", borderColor: "#1f1f1f" }} /></div>
              <div className="field">
                <label>Type</label>
                <select className="select" value={form.promotion_type} onChange={(e) => setForm({ ...form, promotion_type: e.target.value })} style={{ background: "#0a0a0a", color: "#fff", borderColor: "#1f1f1f" }}>
                  <option value="FEATURED">Featured</option>
                  <option value="TOP_LISTING">Top Listing</option>
                  <option value="HOMEPAGE">Homepage</option>
                  <option value="HIGHLIGHTED">Highlighted</option>
                  <option value="DEALER_PROMOTION">Dealer Promotion</option>
                </select>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                <div className="field"><label>Price</label><input className="input" type="number" value={form.price} onChange={(e) => setForm({ ...form, price: Number(e.target.value) })} style={{ background: "#0a0a0a", color: "#fff", borderColor: "#1f1f1f" }} /></div>
                <div className="field"><label>Duration (days)</label><input className="input" type="number" value={form.duration_days} onChange={(e) => setForm({ ...form, duration_days: Number(e.target.value) })} style={{ background: "#0a0a0a", color: "#fff", borderColor: "#1f1f1f" }} /></div>
              </div>
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