import React, { useEffect, useState } from "react";
import { catalogService } from "@/services";
import type { Category, Make, Model } from "@/types";

export interface FilterValues {
  make_id?: string;
  model_id?: string;
  category_id?: string;
  body_type?: string;
  fuel_type?: string;
  transmission?: string;
  drive_type?: string;
  condition?: string;
  country?: string;
  min_price?: number;
  max_price?: number;
  min_year?: number;
  max_year?: number;
  min_mileage?: number;
  max_mileage?: number;
  color?: string;
  seller_type?: string;
  sort?: string;
}

interface FilterSidebarProps {
  values: FilterValues;
  onChange: (v: FilterValues) => void;
  onClose?: () => void;
  isMobile?: boolean;
}

export const FilterSidebar: React.FC<FilterSidebarProps> = ({ values, onChange, onClose, isMobile }) => {
  const [makes, setMakes] = useState<Make[]>([]);
  const [models, setModels] = useState<Model[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [countries, setCountries] = useState<string[]>([]);

  useEffect(() => {
    catalogService.makes().then(setMakes).catch(() => {});
    catalogService.categories().then(setCategories).catch(() => {});
    catalogService.countries().then(setCountries).catch(() => setCountries([]));
  }, []);

  useEffect(() => {
    if (!values.make_id) {
      setModels([]);
      return;
    }
    catalogService.models(values.make_id).then(setModels).catch(() => setModels([]));
  }, [values.make_id]);

  const set = (patch: Partial<FilterValues>) => onChange({ ...values, ...patch });

  const reset = () => onChange({});

  const content = (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      <div className="row-between">
        <h3 style={{ fontSize: 18 }}>Filters</h3>
        {isMobile && (
          <button className="btn btn-ghost btn-sm" onClick={onClose}>Close</button>
        )}
      </div>

      <Group title="Make & Model">
        <select className="select" value={values.make_id || ""} onChange={(e) => set({ make_id: e.target.value, model_id: undefined })}>
          <option value="">Any make</option>
          {makes.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
        </select>
        <select className="select" value={values.model_id || ""} onChange={(e) => set({ model_id: e.target.value })} disabled={!values.make_id}>
          <option value="">Any model</option>
          {models.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
        </select>
      </Group>

      <Group title="Price (USD)">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
          <input className="input" type="number" placeholder="Min" value={values.min_price ?? ""} onChange={(e) => set({ min_price: e.target.value ? Number(e.target.value) : undefined })} />
          <input className="input" type="number" placeholder="Max" value={values.max_price ?? ""} onChange={(e) => set({ max_price: e.target.value ? Number(e.target.value) : undefined })} />
        </div>
      </Group>

      <Group title="Year">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
          <input className="input" type="number" placeholder="From" value={values.min_year ?? ""} onChange={(e) => set({ min_year: e.target.value ? Number(e.target.value) : undefined })} />
          <input className="input" type="number" placeholder="To" value={values.max_year ?? ""} onChange={(e) => set({ max_year: e.target.value ? Number(e.target.value) : undefined })} />
        </div>
      </Group>

      <Group title="Mileage (km)">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
          <input className="input" type="number" placeholder="Min" value={values.min_mileage ?? ""} onChange={(e) => set({ min_mileage: e.target.value ? Number(e.target.value) : undefined })} />
          <input className="input" type="number" placeholder="Max" value={values.max_mileage ?? ""} onChange={(e) => set({ max_mileage: e.target.value ? Number(e.target.value) : undefined })} />
        </div>
      </Group>

      <Group title="Body type">
        <select className="select" value={values.body_type || ""} onChange={(e) => set({ body_type: e.target.value || undefined })}>
          <option value="">Any</option>
          <option value="SEDAN">Sedan</option>
          <option value="SUV">SUV</option>
          <option value="COUPE">Coupe</option>
          <option value="HATCHBACK">Hatchback</option>
          <option value="WAGON">Wagon</option>
          <option value="PICKUP">Pickup</option>
          <option value="VAN">Van</option>
          <option value="MOTORCYCLE">Motorcycle</option>
          <option value="TRUCK">Truck</option>
          <option value="ELECTRIC">Electric</option>
          <option value="CONVERTIBLE">Convertible</option>
          <option value="CROSSOVER">Crossover</option>
        </select>
      </Group>

      <Group title="Fuel">
        <select className="select" value={values.fuel_type || ""} onChange={(e) => set({ fuel_type: e.target.value || undefined })}>
          <option value="">Any</option>
          <option value="PETROL">Petrol</option>
          <option value="DIESEL">Diesel</option>
          <option value="HYBRID">Hybrid</option>
          <option value="PLUGIN_HYBRID">Plug-in Hybrid</option>
          <option value="ELECTRIC">Electric</option>
          <option value="LPG">LPG</option>
          <option value="CNG">CNG</option>
        </select>
      </Group>

      <Group title="Transmission">
        <select className="select" value={values.transmission || ""} onChange={(e) => set({ transmission: e.target.value || undefined })}>
          <option value="">Any</option>
          <option value="AUTOMATIC">Automatic</option>
          <option value="MANUAL">Manual</option>
          <option value="SEMI_AUTOMATIC">Semi-Automatic</option>
          <option value="CVT">CVT</option>
        </select>
      </Group>

      <Group title="Drive">
        <select className="select" value={values.drive_type || ""} onChange={(e) => set({ drive_type: e.target.value || undefined })}>
          <option value="">Any</option>
          <option value="FWD">FWD</option>
          <option value="RWD">RWD</option>
          <option value="AWD">AWD</option>
          <option value="FOUR_WD">4WD</option>
        </select>
      </Group>

      <Group title="Condition">
        <select className="select" value={values.condition || ""} onChange={(e) => set({ condition: e.target.value || undefined })}>
          <option value="">Any</option>
          <option value="NEW">New</option>
          <option value="USED">Used</option>
          <option value="CERTIFIED">Certified</option>
        </select>
      </Group>

      <Group title="Color">
        <input className="input" placeholder="e.g. Black" value={values.color || ""} onChange={(e) => set({ color: e.target.value || undefined })} />
      </Group>

      <Group title="Location">
        <select className="select" value={values.country || ""} onChange={(e) => set({ country: e.target.value || undefined })}>
          <option value="">Any country</option>
          {countries.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
      </Group>

      <Group title="Seller type">
        <select className="select" value={values.seller_type || ""} onChange={(e) => set({ seller_type: e.target.value || undefined })}>
          <option value="">All</option>
          <option value="USER">Private</option>
          <option value="DEALER">Dealer</option>
        </select>
      </Group>

      <button className="btn btn-outline btn-block" onClick={reset}>Reset filters</button>
    </div>
  );

  if (!isMobile) {
    return (
      <aside style={{
        background: "#fff", border: "1px solid var(--color-border)",
        borderRadius: 14, padding: 18, position: "sticky", top: 80,
      }}>
        {content}
      </aside>
    );
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div onClick={(e) => e.stopPropagation()} style={{
        background: "#fff", borderRadius: 14, padding: 18,
        width: "100%", maxWidth: 420, maxHeight: "90vh", overflowY: "auto",
      }}>
        {content}
      </div>
    </div>
  );
};

const Group: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
  <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
    <span className="text-sm fw-6 muted" style={{ textTransform: "uppercase", letterSpacing: 0.5 }}>{title}</span>
    {children}
  </div>
);