import React, { useState } from "react";
import { superAdminService } from "@/services";
import { useAsync } from "@/hooks/useAsync";
import { ErrorState, LoadingBlock } from "@/components/States";
import toast from "react-hot-toast";

export const SuperAdminLocationsPage: React.FC = () => {
  const { data, loading, error, reload } = useAsync(() => superAdminService.locations(), []);
  const [show, setShow] = useState(false);
  const [form, setForm] = useState({ country: "", city: "", display_name: "" });
  const [saving, setSaving] = useState(false);

  const create = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      await superAdminService.createLocation(form);
      toast.success("Location created");
      setShow(false);
      setForm({ country: "", city: "", display_name: "" });
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
        <h1 style={{ color: "#fff" }}>Locations</h1>
        <button className="btn btn-blue" onClick={() => setShow(true)}>+ New Location</button>
      </div>
      {loading ? <LoadingBlock /> : error ? <ErrorState onRetry={reload} /> : (
        <div style={{ background: "#161616", borderRadius: 12, overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", color: "#fff" }}>
            <thead><tr style={{ background: "#0f0f0f" }}><th style={th}>Display</th><th style={th}>City</th><th style={th}>Country</th><th style={th}>Region</th></tr></thead>
            <tbody>
              {data?.map((l: any) => (
                <tr key={l.id} style={{ borderTop: "1px solid #1f1f1f" }}>
                  <td style={td}>{l.display_name}</td>
                  <td style={td}>{l.city}</td>
                  <td style={td}>{l.country}</td>
                  <td style={td}>{l.region || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {show && (
        <div className="modal-backdrop" onClick={() => setShow(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ background: "#161616", color: "#fff" }}>
            <h2 style={{ marginBottom: 16 }}>New Location</h2>
            <form onSubmit={create}>
              <div className="field"><label>Country</label><input className="input" required value={form.country} onChange={(e) => setForm({ ...form, country: e.target.value })} style={{ background: "#0a0a0a", color: "#fff", borderColor: "#1f1f1f" }} /></div>
              <div className="field"><label>City</label><input className="input" required value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} style={{ background: "#0a0a0a", color: "#fff", borderColor: "#1f1f1f" }} /></div>
              <div className="field"><label>Display name</label><input className="input" required value={form.display_name} onChange={(e) => setForm({ ...form, display_name: e.target.value })} style={{ background: "#0a0a0a", color: "#fff", borderColor: "#1f1f1f" }} /></div>
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