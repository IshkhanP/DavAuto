import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { catalogService } from "@/services";
import type { Make, Model } from "@/types";

export const HeroSearch: React.FC = () => {
  const navigate = useNavigate();
  const [makes, setMakes] = useState<Make[]>([]);
  const [models, setModels] = useState<Model[]>([]);
  const [makeId, setMakeId] = useState<string>("");
  const [modelId, setModelId] = useState<string>("");
  const [minPrice, setMinPrice] = useState<string>("");
  const [maxPrice, setMaxPrice] = useState<string>("");
  const [year, setYear] = useState<string>("");
  const [country, setCountry] = useState<string>("");

  useEffect(() => {
    catalogService.makes().then(setMakes).catch(() => {});
    catalogService.countries().then((c) => c.length && setCountry(c[0])).catch(() => {});
  }, []);

  useEffect(() => {
    if (!makeId) {
      setModels([]);
      setModelId("");
      return;
    }
    catalogService.models(makeId).then(setModels).catch(() => setModels([]));
    setModelId("");
  }, [makeId]);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const params = new URLSearchParams();
    if (makeId) params.set("make_id", makeId);
    if (modelId) params.set("model_id", modelId);
    if (minPrice) params.set("min_price", minPrice);
    if (maxPrice) params.set("max_price", maxPrice);
    if (year) params.set("min_year", year);
    if (country) params.set("country", country);
    navigate(`/cars?${params.toString()}`);
  };

  return (
    <form onSubmit={submit} style={{
      background: "#fff",
      borderRadius: 16,
      padding: "1.25rem",
      boxShadow: "var(--shadow-md)",
      border: "1px solid var(--color-border)",
    }}>
      <div style={{
        display: "grid",
        gridTemplateColumns: "1fr 1fr 1fr 1fr 1fr auto",
        gap: "0.75rem",
        alignItems: "end",
      }} className="hero-grid">
        <Field label="Make">
          <select className="select" value={makeId} onChange={(e) => setMakeId(e.target.value)}>
            <option value="">Any make</option>
            {makes.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
          </select>
        </Field>
        <Field label="Model">
          <select className="select" value={modelId} onChange={(e) => setModelId(e.target.value)} disabled={!makeId}>
            <option value="">Any model</option>
            {models.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
          </select>
        </Field>
        <Field label="Price">
          <div style={{ display: "flex", gap: 6 }}>
            <input className="input" placeholder="Min" type="number" value={minPrice} onChange={(e) => setMinPrice(e.target.value)} />
            <input className="input" placeholder="Max" type="number" value={maxPrice} onChange={(e) => setMaxPrice(e.target.value)} />
          </div>
        </Field>
        <Field label="Year">
          <input className="input" placeholder="From" type="number" value={year} onChange={(e) => setYear(e.target.value)} />
        </Field>
        <Field label="Location">
          <input className="input" placeholder="Country" value={country} onChange={(e) => setCountry(e.target.value)} />
        </Field>
        <button type="submit" className="btn btn-primary btn-lg" style={{ height: 44 }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          Search
        </button>
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 12 }}>
        <p className="text-sm muted">Use Advanced Search for more filters</p>
        <button type="button" onClick={() => navigate("/cars")} className="btn btn-ghost btn-sm">
          Advanced Search →
        </button>
      </div>

      <style>{`
        @media (max-width: 980px) {
          .hero-grid { grid-template-columns: 1fr 1fr !important; }
        }
        @media (max-width: 540px) {
          .hero-grid { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </form>
  );
};

const Field: React.FC<{ label: string; children: React.ReactNode }> = ({ label, children }) => (
  <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
    <span className="text-sm fw-6">{label}</span>
    {children}
  </label>
);