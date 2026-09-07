import React, { useRef, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { authService, uploadsService } from "@/services";
import toast from "react-hot-toast";

export const DashboardProfilePage: React.FC = () => {
  const { user, refreshUser } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [form, setForm] = useState({
    full_name: user?.full_name || "",
    phone: user?.phone || "",
    city: user?.city || "",
    country: user?.country || "",
  });
  const [saving, setSaving] = useState(false);
  const [uploadingAvatar, setUploadingAvatar] = useState(false);

  const set = (k: string, v: string) => setForm((p) => ({ ...p, [k]: v }));

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      await authService.updateMe(form);
      await refreshUser();
      toast.success("Profile updated");
    } catch {
      toast.error("Could not update");
    } finally {
      setSaving(false);
    }
  };

  const onPickAvatar = () => fileInputRef.current?.click();

  const onAvatarChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      setUploadingAvatar(true);
      await uploadsService.uploadAvatar(file);
      await refreshUser();
      toast.success("Profile picture updated");
    } catch {
      toast.error("Could not upload picture");
    } finally {
      setUploadingAvatar(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  return (
    <div style={{ maxWidth: 560 }}>
      <h1 style={{ marginBottom: 16 }}>Profile</h1>

      <div className="card" style={{ padding: 20, marginBottom: 16 }}>
        <div className="row" style={{ gap: 12, alignItems: "center" }}>
          {user?.avatar_url ? (
            <img
              src={user.avatar_url}
              alt={user.full_name}
              style={{ width: 72, height: 72, borderRadius: "50%", objectFit: "cover" }}
            />
          ) : (
            <div style={{
              width: 72, height: 72, background: "var(--color-black)", color: "#fff",
              borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center",
              fontWeight: 800, fontSize: 28,
            }}>
              {user?.full_name?.[0]?.toUpperCase()}
            </div>
          )}
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 700 }}>{user?.full_name}</div>
            <div className="text-sm muted">{user?.email}</div>
            <div className="text-sm muted" style={{ marginTop: 2 }}>
              Role{user?.roles?.length ? "s" : ""}: {(user?.roles ?? []).join(", ") || "USER"}
            </div>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            hidden
            onChange={onAvatarChange}
          />
          <button
            className="btn btn-outline btn-sm"
            type="button"
            onClick={onPickAvatar}
            disabled={uploadingAvatar}
          >
            {uploadingAvatar ? "Uploading..." : "Change picture"}
          </button>
        </div>
      </div>

      <form className="card" style={{ padding: 20 }} onSubmit={save}>
        <h3 style={{ fontSize: 16, marginBottom: 12 }}>Personal information</h3>
        <div className="field">
          <label>Full name</label>
          <input className="input" value={form.full_name} onChange={(e) => set("full_name", e.target.value)} />
        </div>
        <div className="field">
          <label>Phone</label>
          <input className="input" value={form.phone} onChange={(e) => set("phone", e.target.value)} />
        </div>
        <div className="field">
          <label>City</label>
          <input className="input" value={form.city} onChange={(e) => set("city", e.target.value)} />
        </div>
        <div className="field">
          <label>Country</label>
          <input className="input" value={form.country} onChange={(e) => set("country", e.target.value)} />
        </div>
        <button className="btn btn-primary" disabled={saving}>{saving ? "Saving..." : "Save changes"}</button>
      </form>
    </div>
  );
};