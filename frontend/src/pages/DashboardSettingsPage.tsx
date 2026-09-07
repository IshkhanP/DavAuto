import React, { useState } from "react";
import { authService } from "@/services";
import toast from "react-hot-toast";

export const DashboardSettingsPage: React.FC = () => {
  const [form, setForm] = useState({ current: "", next: "", confirm: "" });
  const [saving, setSaving] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (form.next !== form.confirm) {
      toast.error("Passwords do not match");
      return;
    }
    try {
      setSaving(true);
      await authService.changePassword(form.current, form.next);
      toast.success("Password updated");
      setForm({ current: "", next: "", confirm: "" });
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Could not update password");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ maxWidth: 560 }}>
      <h1 style={{ marginBottom: 16 }}>Settings</h1>

      <form className="card" style={{ padding: 20 }} onSubmit={submit}>
        <h2 style={{ fontSize: 18, marginBottom: 16 }}>Change Password</h2>
        <div className="field">
          <label>Current password</label>
          <input type="password" className="input" value={form.current} onChange={(e) => setForm({ ...form, current: e.target.value })} required />
        </div>
        <div className="field">
          <label>New password</label>
          <input type="password" className="input" value={form.next} onChange={(e) => setForm({ ...form, next: e.target.value })} required minLength={8} />
        </div>
        <div className="field">
          <label>Confirm new password</label>
          <input type="password" className="input" value={form.confirm} onChange={(e) => setForm({ ...form, confirm: e.target.value })} required />
        </div>
        <button className="btn btn-primary" disabled={saving}>{saving ? "Saving..." : "Update password"}</button>
      </form>
    </div>
  );
};