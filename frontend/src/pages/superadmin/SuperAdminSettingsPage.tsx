import React, { useState } from "react";
import { superAdminService } from "@/services";
import { useAsync } from "@/hooks/useAsync";
import { ErrorState, LoadingBlock } from "@/components/States";
import toast from "react-hot-toast";

export const SuperAdminSettingsPage: React.FC = () => {
  const { data, loading, error, reload } = useAsync(() => superAdminService.settings(), []);

  const update = async (key: string, value: string) => {
    try {
      await superAdminService.updateSetting(key, { value });
      toast.success("Setting updated");
      reload();
    } catch {
      toast.error("Could not update setting");
    }
  };

  return (
    <div>
      <h1 style={{ color: "#fff", marginBottom: 16 }}>Site Settings</h1>
      {loading ? <LoadingBlock /> : error ? <ErrorState onRetry={reload} /> : (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {data?.map((s: any) => (
            <SettingRow key={s.key} setting={s} onSave={(v) => update(s.key, v)} />
          ))}
        </div>
      )}
    </div>
  );
};

const SettingRow: React.FC<{ setting: any; onSave: (v: string) => void }> = ({ setting, onSave }) => {
  const [value, setValue] = useState(setting.value || "");
  return (
    <div style={{ background: "#161616", border: "1px solid #1f1f1f", borderRadius: 12, padding: 16, display: "flex", alignItems: "center", gap: 12 }}>
      <div style={{ flex: 1 }}>
        <div style={{ fontWeight: 700, color: "#fff" }}>{setting.key}</div>
        <div style={{ color: "#9ca3af", fontSize: 13 }}>{setting.description}</div>
      </div>
      <input
        className="input"
        style={{ background: "#0a0a0a", color: "#fff", borderColor: "#1f1f1f", maxWidth: 280 }}
        value={value}
        onChange={(e) => setValue(e.target.value)}
      />
      <button className="btn btn-blue btn-sm" onClick={() => onSave(value)}>Save</button>
    </div>
  );
};