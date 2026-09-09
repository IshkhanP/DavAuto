// A minimal, fast path to create a listing without opening the full
// multi-section CreateListingPage wizard. Captures just enough to get a
// draft/active row into "My Listings" — photos, specs, description, and
// contact preferences can all be filled in afterwards from the edit page.
import React, { useEffect, useState } from "react";
import { catalogService, carsService } from "@/services";
import type { Make, Model } from "@/types";
import toast from "react-hot-toast";

interface QuickAddListingModalProps {
  onClose: () => void;
  onCreated: (carId: string) => void;
}

const CURRENCIES = ["USD", "EUR", "AMD", "RUB", "GBP"];

export const QuickAddListingModal: React.FC<QuickAddListingModalProps> = ({ onClose, onCreated }) => {
  const [makes, setMakes] = useState<Make[]>([]);
  const [models, setModels] = useState<Model[]>([]);
  const [form, setForm] = useState({
    make_id: "",
    model_id: "",
    year: new Date().getFullYear().toString(),
    price: "",
    currency: "USD",
    mileage: "0",
    condition: "USED",
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    catalogService.makes().then(setMakes).catch(() => {});
  }, []);

  useEffect(() => {
    if (!form.make_id) {
      setModels([]);
      return;
    }
    catalogService.models(form.make_id).then(setModels).catch(() => setModels([]));
  }, [form.make_id]);

  const set = (patch: Partial<typeof form>) => setForm((p) => ({ ...p, ...patch }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.make_id || !form.model_id || !form.year) {
      toast.error("Please choose a make, model, and year");
      return;
    }
    try {
      setSubmitting(true);
      const car = await carsService.create({
        make_id: form.make_id,
        model_id: form.model_id,
        year: Number(form.year),
        price: Number(form.price || 0),
        currency: form.currency,
        mileage: Number(form.mileage || 0),
        condition: form.condition,
      });
      toast.success("Listing created — add photos and details anytime");
      onCreated(car.id);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Could not create listing");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2 style={{ marginBottom: 4 }}>Quick Add Listing</h2>
        <p className="text-sm muted" style={{ marginBottom: 16 }}>
          Get a listing started in seconds — no need to open the full form. You can
          add photos, specs, and a description anytime from "My Listings".
        </p>
        <form onSubmit={submit}>
          <div className="field">
            <label>Make</label>
            <select
              className="select"
              required
              value={form.make_id}
              onChange={(e) => set({ make_id: e.target.value, model_id: "" })}
            >
              <option value="">Select make</option>
              {makes.map((m) => (
                <option key={m.id} value={m.id}>{m.name}</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Model</label>
            <select
              className="select"
              required
              disabled={!form.make_id}
              value={form.model_id}
              onChange={(e) => set({ model_id: e.target.value })}
            >
              <option value="">Select model</option>
              {models.map((m) => (
                <option key={m.id} value={m.id}>{m.name}</option>
              ))}
            </select>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <div className="field">
              <label>Year</label>
              <input
                className="input"
                type="number"
                required
                min={1900}
                max={new Date().getFullYear() + 1}
                value={form.year}
                onChange={(e) => set({ year: e.target.value })}
              />
            </div>
            <div className="field">
              <label>Mileage (km)</label>
              <input
                className="input"
                type="number"
                min={0}
                value={form.mileage}
                onChange={(e) => set({ mileage: e.target.value })}
              />
            </div>
            <div className="field">
              <label>Price</label>
              <input
                className="input"
                type="number"
                min={0}
                value={form.price}
                onChange={(e) => set({ price: e.target.value })}
              />
            </div>
            <div className="field">
              <label>Currency</label>
              <select className="select" value={form.currency} onChange={(e) => set({ currency: e.target.value })}>
                {CURRENCIES.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
          </div>
          <div className="field">
            <label>Condition</label>
            <select className="select" value={form.condition} onChange={(e) => set({ condition: e.target.value })}>
              <option value="NEW">New</option>
              <option value="USED">Used</option>
              <option value="CERTIFIED">Certified pre-owned</option>
            </select>
          </div>
          <div className="row" style={{ gap: 8, justifyContent: "flex-end", marginTop: 12 }}>
            <button type="button" className="btn btn-ghost" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-blue" disabled={submitting}>
              {submitting ? "Creating..." : "Create Listing"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
