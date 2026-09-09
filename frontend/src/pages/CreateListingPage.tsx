import React, { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { catalogService, carsService, uploadsService } from "@/services";
import type { Category, Make, Model, Location, CarImage } from "@/types";
import { CONTACT_METHODS, ContactMethod } from "@/types";
import toast from "react-hot-toast";

/* ------------------------------------------------------------------ */
/*  Form shape & per-step validation rules                            */
/* ------------------------------------------------------------------ */

interface FormState {
  // Step 1 — Vehicle
  make_id: string;
  model_id: string;
  year: string;
  vin: string;
  // Step 2 — Specifications
  body_type: string;
  fuel_type: string;
  transmission: string;
  drive_type: string;
  mileage: string;
  engine: string;
  engine_size: string;
  horsepower: string;
  exterior_color: string;
  interior_color: string;
  doors: string;
  seats: string;
  condition: string;
  // Contact preferences (step 2)
  phone_country_code: string;
  phone_number: string;
  contact_methods: ContactMethod[];
  // Step 3 — Price & Location
  price: string;
  currency: string;
  category_id: string;
  location_id: string;
  // Step 4 — Photos
  // Step 5 — Description & features
  description: string;
  features: string;
  is_negotiable: boolean;
}

const EMPTY: FormState = {
  make_id: "", model_id: "", year: new Date().getFullYear().toString(), vin: "",
  body_type: "SEDAN", fuel_type: "PETROL", transmission: "AUTOMATIC", drive_type: "FWD",
  mileage: "0", engine: "", engine_size: "", horsepower: "",
  exterior_color: "", interior_color: "", doors: "4", seats: "5",
  condition: "USED",
  phone_country_code: "+1", phone_number: "", contact_methods: ["PHONE", "CHAT"],
  price: "", currency: "USD", category_id: "", location_id: "",
  description: "", features: "", is_negotiable: true,
};

const STEPS = [
  "Vehicle",
  "Specifications & Contact",
  "Price & Location",
  "Photos",
  "Description",
  "Preview",
] as const;

function validateStep(step: number, form: FormState): Record<string, string> {
  const errors: Record<string, string> = {};

  if (step === 0) {
    if (!form.make_id) errors.make_id = "Please choose a make";
    if (!form.model_id) errors.model_id = "Please choose a model";
    const yr = Number(form.year);
    if (!form.year || isNaN(yr) || yr < 1900 || yr > 2100) {
      errors.year = "Year must be between 1900 and 2100";
    }
  } else if (step === 1) {
    if (!form.fuel_type) errors.fuel_type = "Please choose a fuel type";
    if (!form.transmission) errors.transmission = "Please choose a transmission";
    if (form.mileage === "" || isNaN(Number(form.mileage)) || Number(form.mileage) < 0) {
      errors.mileage = "Mileage must be a non-negative number";
    }
    if (form.engine_size && isNaN(Number(form.engine_size))) {
      errors.engine_size = "Engine size must be a number";
    }
    if (form.horsepower && isNaN(Number(form.horsepower))) {
      errors.horsepower = "Horsepower must be a number";
    }
    const needsPhone = form.contact_methods.some((m) => m !== "CHAT");
    if (needsPhone) {
      if (!form.phone_country_code) errors.phone_country_code = "Country code is required";
      if (!form.phone_number) errors.phone_number = "Phone number is required";
      else if (!/^[\d\s\-+()]{4,20}$/.test(form.phone_number)) {
        errors.phone_number = "Phone number looks invalid";
      }
    }
    if (form.contact_methods.length === 0) {
      errors.contact_methods = "Please pick at least one contact method";
    }
  } else if (step === 2) {
    if (!form.price || isNaN(Number(form.price)) || Number(form.price) < 0) {
      errors.price = "Please enter a valid price";
    }
  } else if (step === 4) {
    if (form.features && form.features.length > 500) {
      errors.features = "Features list is too long";
    }
  }

  return errors;
}

const COUNTRY_CODES = ["+1", "+44", "+49", "+33", "+34", "+39", "+7", "+90", "+91", "+86", "+81", "+82", "+374", "+995", "+971"];

/* ------------------------------------------------------------------ */
/*  Reusable Field component with inline error highlighting          */
/* ------------------------------------------------------------------ */

interface FieldProps {
  label: string;
  required?: boolean;
  error?: string;
  children: React.ReactNode;
  hint?: string;
  id?: string;
}
const Field: React.FC<FieldProps> = ({ label, required, error, children, hint, id }) => (
  <label htmlFor={id} style={{ display: "flex", flexDirection: "column", gap: 6 }}>
    <span className="text-sm fw-6">
      {label}
      {required && <span style={{ color: "var(--color-red)", marginLeft: 4 }}>*</span>}
    </span>
    {children}
    {hint && !error && <span className="hint" style={{ color: "var(--color-text-muted)", fontSize: 12 }}>{hint}</span>}
    {error && (
      <span
        role="alert"
        className="error"
        style={{ color: "var(--color-red)", fontSize: 12, fontWeight: 600 }}
      >
        ⚠ {error}
      </span>
    )}
  </label>
);

/* ------------------------------------------------------------------ */
/*  The page                                                          */
/* ------------------------------------------------------------------ */

export const CreateListingPage: React.FC = () => {
  const navigate = useNavigate();
  const [form, setForm] = useState<FormState>(EMPTY);
  const [carId, setCarId] = useState<string | null>(null);
  const [images, setImages] = useState<CarImage[]>([]);
  const [uploading, setUploading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [savingDraft, setSavingDraft] = useState(false);
  // Per-step error map.  We only validate and surface errors for the section
  // the user clicks "Save section" on, so the rest of the form stays calm.
  const [errorsByStep, setErrorsByStep] = useState<Record<number, Record<string, string>>>({});
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [makes, setMakes] = useState<Make[]>([]);
  const [models, setModels] = useState<Model[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);

  useEffect(() => {
    catalogService.makes().then(setMakes).catch(() => {});
    catalogService.categories().then(setCategories).catch(() => {});
    catalogService.locations().then(setLocations).catch(() => {});
    const draft = localStorage.getItem("bsc_listing_draft");
    if (draft) {
      try {
        const parsed = JSON.parse(draft);
        setForm((p) => ({ ...p, ...parsed }));
      } catch {
        /* ignore corrupt drafts */
      }
    }
  }, []);

  useEffect(() => {
    localStorage.setItem("bsc_listing_draft", JSON.stringify(form));
  }, [form]);

  useEffect(() => {
    if (!form.make_id) {
      setModels([]);
      return;
    }
    catalogService.models(form.make_id).then(setModels).catch(() => setModels([]));
  }, [form.make_id]);

  const set = (patch: Partial<FormState>) => setForm((p) => ({ ...p, ...patch }));

  // Clear a field's error as soon as the user types / selects something.
  const clearError = (step: number, field: string) => {
    setErrorsByStep((prev) => {
      const stepErrors = prev[step];
      if (!stepErrors || !stepErrors[field]) return prev;
      const { [field]: _drop, ...rest } = stepErrors;
      return { ...prev, [step]: rest };
    });
  };

  // Creates the car record as soon as the minimum info (make/model/year) is
  // known. Price and mileage default to 0 if not filled in yet — this lets
  // photos get uploaded, and drafts get saved, before every field is done.
  const ensureCarId = async (): Promise<string> => {
    if (carId) return carId;
    if (!form.make_id || !form.model_id || !form.year) {
      throw new Error("Please choose a make, model, and year first");
    }
    const payload = {
      make_id: form.make_id,
      model_id: form.model_id,
      category_id: form.category_id || null,
      location_id: form.location_id || null,
      year: Number(form.year),
      price: Number(form.price || 0),
      currency: form.currency,
      mileage: Number(form.mileage || 0),
      vin: form.vin || null,
      body_type: form.body_type || null,
      fuel_type: form.fuel_type || null,
      transmission: form.transmission || null,
      drive_type: form.drive_type || null,
      engine: form.engine || null,
      engine_size: form.engine_size ? Number(form.engine_size) : null,
      horsepower: form.horsepower ? Number(form.horsepower) : null,
      exterior_color: form.exterior_color || null,
      interior_color: form.interior_color || null,
      doors: form.doors ? Number(form.doors) : null,
      seats: form.seats ? Number(form.seats) : null,
      description: form.description || null,
      condition: form.condition,
      is_negotiable: form.is_negotiable,
      features: form.features
        ? form.features.split(",").map((s) => ({ name: s.trim() })).filter((f) => f.name)
        : [],
      phone_country_code: form.phone_country_code || null,
      phone_number: form.phone_number || null,
      contact_methods: form.contact_methods.length ? form.contact_methods : null,
    };
    const car = await carsService.create(payload);
    setCarId(car.id);
    return car.id;
  };

  // Single "Save Draft" button (replaces the old per-section save buttons).
  // Creates the listing if it doesn't exist yet and marks it DRAFT so it's
  // safely parked in "My Listings" without needing every field filled in —
  // the seller can come back anytime and finish it before publishing.
  const saveDraft = async () => {
    if (!form.make_id || !form.model_id) {
      toast.error("Please choose a make and model first");
      return;
    }
    try {
      setSavingDraft(true);
      const id = await ensureCarId();
      await carsService.setStatus(id, "DRAFT");
      toast.success("Draft saved — continue anytime from My Listings");
    } catch (e: any) {
      toast.error(e?.message || e?.response?.data?.detail || "Could not save draft");
    } finally {
      setSavingDraft(false);
    }
  };

  const handleUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    try {
      setUploading(true);
      const id = await ensureCarId();
      for (const f of Array.from(files)) {
        try {
          const img = await uploadsService.uploadCarImage(id, f);
          setImages((prev) => [
            ...prev,
            { id: img.id, url: img.url, display_order: prev.length, is_main: prev.length === 0 },
          ]);
        } catch {
          toast.error(`Could not upload ${f.name}`);
        }
      }
      toast.success("Images uploaded");
    } catch (e: any) {
      toast.error(e?.message || "Could not save listing first");
    } finally {
      setUploading(false);
    }
  };

  const removeImage = async (imgId: string) => {
    try {
      await uploadsService.deleteCarImage(imgId);
      setImages((prev) => prev.filter((i) => i.id !== imgId));
    } catch {
      toast.error("Could not delete image");
    }
  };

  const setMain = async (imgId: string) => {
    if (!carId) return;
    try {
      await uploadsService.setMainImage(carId, imgId);
      setImages((prev) => prev.map((i) => ({ ...i, is_main: i.id === imgId })));
    } catch {
      toast.error("Could not set main image");
    }
  };

  // ---------- HTML5 drag-and-drop reorder ----------
  const [draggingId, setDraggingId] = useState<string | null>(null);
  const [dragOverId, setDragOverId] = useState<string | null>(null);

  const persistOrder = async (orderedIds: string[]) => {
    if (!carId) return;
    try {
      await uploadsService.reorderImages(carId, orderedIds);
    } catch {
      toast.error("Could not save new image order");
    }
  };

  const onDragStart = (id: string) => (e: React.DragEvent) => {
    setDraggingId(id);
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", id);
  };
  const onDragOver = (id: string) => (e: React.DragEvent) => {
    e.preventDefault();
    if (id !== dragOverId) setDragOverId(id);
  };
  const onDragLeave = () => setDragOverId(null);
  const onDrop = (toId: string) => (e: React.DragEvent) => {
    e.preventDefault();
    const fromId = draggingId || e.dataTransfer.getData("text/plain");
    if (!fromId || fromId === toId) {
      setDraggingId(null);
      setDragOverId(null);
      return;
    }
    // Reorder and persist atomically
    setImages((prev) => {
      const fromIdx = prev.findIndex((i) => i.id === fromId);
      const toIdx = prev.findIndex((i) => i.id === toId);
      if (fromIdx < 0 || toIdx < 0) return prev;
      const next = prev.slice();
      const [moved] = next.splice(fromIdx, 1);
      next.splice(toIdx, 0, moved);

      // Whichever photo ends up first is treated as the cover photo — keep
      // "is_main" in sync with position instead of requiring a separate
      // manual "Set main" click every time the order changes.
      const reordered = next.map((img, idx) => ({ ...img, is_main: idx === 0 }));
      const orderedIds = reordered.map((i) => i.id);
      persistOrder(orderedIds);

      if (prev[0]?.id !== reordered[0].id && carId) {
        uploadsService.setMainImage(carId, reordered[0].id).catch(() => {
          toast.error("Could not update main image");
        });
      }
      return reordered;
    });
    setDraggingId(null);
    setDragOverId(null);
  };

  const submit = async () => {
    // Validate every step before submitting.
    let all: Record<number, Record<string, string>> = {};
    for (let i = 0; i < STEPS.length; i++) {
      const e = validateStep(i, form);
      if (Object.keys(e).length) all[i] = e;
    }
    if (Object.keys(all).length) {
      setErrorsByStep(all);
      const firstStep = Object.keys(all).map(Number).sort()[0];
      toast.error(`Please fix the highlighted fields (starting at step ${firstStep + 1})`);
      // Smooth-scroll the user to the first section that has errors.
      document
        .getElementById(`section-${firstStep}`)
        ?.scrollIntoView({ behavior: "smooth", block: "start" });
      return;
    }
    try {
      setSubmitting(true);
      const id = await ensureCarId();
      await carsService.setStatus(id, "ACTIVE");
      toast.success("Listing submitted!");
      localStorage.removeItem("bsc_listing_draft");
      navigate(`/cars/${id}`);
    } catch (e: any) {
      toast.error(e?.message || "Could not submit listing");
    } finally {
      setSubmitting(false);
    }
  };

  const toggleContactMethod = (m: ContactMethod) => {
    setForm((p) => {
      const exists = p.contact_methods.includes(m);
      return {
        ...p,
        contact_methods: exists
          ? p.contact_methods.filter((x) => x !== m)
          : [...p.contact_methods, m],
      };
    });
    clearError(1, "contact_methods");
  };

  // Smooth scroll-to-section when the user clicks the stepper.
  const scrollTo = (i: number) => {
    document.getElementById(`section-${i}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <div style={{ maxWidth: 980, margin: "0 auto" }}>
      <div className="row-between" style={{ marginBottom: 8 }}>
        <h1>Create Listing</h1>
        <div className="row" style={{ gap: 8 }}>
          <button
            className="btn btn-outline btn-sm"
            onClick={saveDraft}
            disabled={savingDraft || submitting}
          >
            {savingDraft ? "Saving..." : "Save Draft"}
          </button>
          <button
            className="btn btn-ghost btn-sm"
            onClick={() => {
              if (confirm("Discard the draft and start over?")) {
                localStorage.removeItem("bsc_listing_draft");
                setForm(EMPTY);
                setCarId(null);
                setImages([]);
                setErrorsByStep({});
              }
            }}
          >
            Reset draft
          </button>
        </div>
      </div>
      <p className="muted text-sm" style={{ marginBottom: 24 }}>
        Fill in what you know, click <b>Save Draft</b> anytime to park it in "My Listings"
        and finish later, or fill every section and click <b>Submit listing</b> at the bottom to publish.
      </p>

      {/* Sticky stepper.  Click a step to jump straight to that section. */}
      <div
        style={{
          display: "flex", gap: 6, marginBottom: 16, overflowX: "auto",
          position: "sticky", top: 64, zIndex: 5, background: "var(--color-bg)",
          padding: "8px 0", borderBottom: "1px solid var(--color-border)",
        }}
      >
        {STEPS.map((label, i) => {
          const hasErrors = Object.keys(errorsByStep[i] ?? {}).length > 0;
          return (
            <button
              key={label}
              onClick={() => scrollTo(i)}
              className="btn btn-sm"
              style={{
                whiteSpace: "nowrap",
                background: hasErrors ? "rgba(220, 38, 38, 0.1)" : "var(--color-light-gray)",
                color: hasErrors ? "var(--color-red)" : "var(--color-text)",
                fontWeight: 600,
                border: hasErrors ? "1px solid var(--color-red)" : "1px solid transparent",
              }}
            >
              {hasErrors ? "⚠ " : ""}{i + 1}. {label}
            </button>
          );
        })}
      </div>

      {/* Section 1 — Vehicle */}
      <section id="section-0" className="card" style={{ padding: 24, marginBottom: 20 }}>
        <h2 style={{ fontSize: 20, marginBottom: 12 }}>1. Vehicle</h2>
        <p className="text-sm muted" style={{ marginBottom: 16 }}>
          Tell us the make and model of your car.
        </p>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }} className="grid-2">
          <Field label="Make" required error={errorsByStep[0]?.make_id}>
            <select
              id="input-make"
              className="select"
              value={form.make_id}
              onChange={(e) => {
                set({ make_id: e.target.value, model_id: "" });
                clearError(0, "make_id");
                clearError(0, "model_id");
              }}
              style={errorsByStep[0]?.make_id ? errorBorder : undefined}
            >
              <option value="">Select make</option>
              {makes.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
            </select>
          </Field>
          <Field label="Model" required error={errorsByStep[0]?.model_id}>
            <select
              id="input-model"
              className="select"
              value={form.model_id}
              onChange={(e) => {
                set({ model_id: e.target.value });
                clearError(0, "model_id");
              }}
              disabled={!form.make_id}
              style={errorsByStep[0]?.model_id ? errorBorder : undefined}
            >
              <option value="">Select model</option>
              {models.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
            </select>
          </Field>
          <Field label="Year" required error={errorsByStep[0]?.year} hint="Between 1900 and the current year.">
            <input
              id="input-year"
              className="input"
              type="number"
              min={1900}
              max={new Date().getFullYear() + 1}
              value={form.year}
              onChange={(e) => {
                set({ year: e.target.value });
                clearError(0, "year");
              }}
              style={errorsByStep[0]?.year ? errorBorder : undefined}
            />
          </Field>
          <Field label="VIN" hint="Vehicle Identification Number (optional)">
            <input
              id="input-vin"
              className="input"
              value={form.vin}
              onChange={(e) => set({ vin: e.target.value })}
              placeholder="e.g. 1HGCM82633A004352"
            />
          </Field>
        </div>
      </section>

      {/* Section 2 — Specifications & Contact preferences */}
      <section id="section-1" className="card" style={{ padding: 24, marginBottom: 20 }}>
        <h2 style={{ fontSize: 20, marginBottom: 12 }}>2. Specifications & Contact</h2>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }} className="grid-2">
          <Field label="Body type">
            <select className="select" value={form.body_type} onChange={(e) => set({ body_type: e.target.value })}>
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
          </Field>
          <Field label="Fuel type" required error={errorsByStep[1]?.fuel_type}>
            <select
              className="select"
              value={form.fuel_type}
              onChange={(e) => { set({ fuel_type: e.target.value }); clearError(1, "fuel_type"); }}
              style={errorsByStep[1]?.fuel_type ? errorBorder : undefined}
            >
              <option value="">Select</option>
              <option value="PETROL">Petrol</option>
              <option value="DIESEL">Diesel</option>
              <option value="HYBRID">Hybrid</option>
              <option value="PLUGIN_HYBRID">Plug-in Hybrid</option>
              <option value="ELECTRIC">Electric</option>
              <option value="LPG">LPG</option>
              <option value="CNG">CNG</option>
            </select>
          </Field>
          <Field label="Transmission" required error={errorsByStep[1]?.transmission}>
            <select
              className="select"
              value={form.transmission}
              onChange={(e) => { set({ transmission: e.target.value }); clearError(1, "transmission"); }}
              style={errorsByStep[1]?.transmission ? errorBorder : undefined}
            >
              <option value="">Select</option>
              <option value="AUTOMATIC">Automatic</option>
              <option value="MANUAL">Manual</option>
              <option value="SEMI_AUTOMATIC">Semi-Automatic</option>
              <option value="CVT">CVT</option>
            </select>
          </Field>
          <Field label="Drive type">
            <select className="select" value={form.drive_type} onChange={(e) => set({ drive_type: e.target.value })}>
              <option value="FWD">FWD (Front-Wheel Drive)</option>
              <option value="RWD">RWD (Rear-Wheel Drive)</option>
              <option value="AWD">AWD (All-Wheel Drive)</option>
              <option value="FOUR_WD">4WD (Four-Wheel Drive)</option>
            </select>
          </Field>
          <Field label="Mileage (km)" required error={errorsByStep[1]?.mileage}>
            <input
              className="input"
              type="number"
              min={0}
              value={form.mileage}
              onChange={(e) => { set({ mileage: e.target.value }); clearError(1, "mileage"); }}
              style={errorsByStep[1]?.mileage ? errorBorder : undefined}
            />
          </Field>
          <Field label="Engine">
            <input className="input" placeholder="e.g. 2.0L Turbo" value={form.engine} onChange={(e) => set({ engine: e.target.value })} />
          </Field>
          <Field label="Engine size (L)" error={errorsByStep[1]?.engine_size}>
            <input
              className="input"
              type="number"
              step="0.1"
              value={form.engine_size}
              onChange={(e) => { set({ engine_size: e.target.value }); clearError(1, "engine_size"); }}
              style={errorsByStep[1]?.engine_size ? errorBorder : undefined}
            />
          </Field>
          <Field label="Horsepower" error={errorsByStep[1]?.horsepower}>
            <input
              className="input"
              type="number"
              value={form.horsepower}
              onChange={(e) => { set({ horsepower: e.target.value }); clearError(1, "horsepower"); }}
              style={errorsByStep[1]?.horsepower ? errorBorder : undefined}
            />
          </Field>
          <Field label="Exterior color">
            <input className="input" value={form.exterior_color} onChange={(e) => set({ exterior_color: e.target.value })} />
          </Field>
          <Field label="Interior color">
            <input className="input" value={form.interior_color} onChange={(e) => set({ interior_color: e.target.value })} />
          </Field>
          <Field label="Doors">
            <input
              className="input"
              type="number"
              min={1}
              value={form.doors}
              onChange={(e) => set({ doors: e.target.value })}
            />
          </Field>
          <Field label="Seats">
            <input
              className="input"
              type="number"
              min={1}
              value={form.seats}
              onChange={(e) => set({ seats: e.target.value })}
            />
          </Field>
          <Field label="Condition" required>
            <select className="select" value={form.condition} onChange={(e) => set({ condition: e.target.value })}>
              <option value="NEW">New</option>
              <option value="USED">Used</option>
              <option value="CERTIFIED">Certified pre-owned</option>
            </select>
          </Field>
        </div>

        <h3 style={{ marginTop: 24, marginBottom: 8 }}>How can buyers reach you?</h3>
        <p className="text-sm muted" style={{ marginBottom: 12 }}>
          Choose the contact methods you prefer. Buyers will see only what you enable.
        </p>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }} className="grid-2">
          <Field label="Country code" error={errorsByStep[1]?.phone_country_code}>
            <select
              className="select"
              value={form.phone_country_code}
              onChange={(e) => { set({ phone_country_code: e.target.value }); clearError(1, "phone_country_code"); }}
              style={errorsByStep[1]?.phone_country_code ? errorBorder : undefined}
            >
              {COUNTRY_CODES.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </Field>
          <Field label="Phone number" error={errorsByStep[1]?.phone_number} hint="Digits only, e.g. 5551234567">
            <input
              className="input"
              type="tel"
              placeholder="5551234567"
              value={form.phone_number}
              onChange={(e) => { set({ phone_number: e.target.value }); clearError(1, "phone_number"); }}
              style={errorsByStep[1]?.phone_number ? errorBorder : undefined}
            />
          </Field>
        </div>
        <div style={{ marginTop: 12 }}>
          <span className="text-sm fw-6 muted" style={{ textTransform: "uppercase", letterSpacing: 0.4, fontSize: 12 }}>Contact methods *</span>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(170px, 1fr))", gap: 8, marginTop: 6 }}>
            {CONTACT_METHODS.map((m) => {
              const checked = form.contact_methods.includes(m);
              return (
                <label
                  key={m}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                    padding: "10px 12px",
                    border: "1px solid var(--color-border)",
                    borderRadius: 10,
                    background: checked ? "rgba(37, 99, 235, 0.06)" : "#fff",
                    cursor: "pointer",
                  }}
                >
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => toggleContactMethod(m)}
                  />
                  <span style={{ fontSize: 14, fontWeight: 600 }}>{labelFor(m)}</span>
                </label>
              );
            })}
          </div>
          {errorsByStep[1]?.contact_methods && (
            <span className="error" style={{ color: "var(--color-red)", fontSize: 12, marginTop: 4, display: "block" }}>
              ⚠ {errorsByStep[1]?.contact_methods}
            </span>
          )}
        </div>
      </section>

      {/* Section 3 — Price & Location */}
      <section id="section-2" className="card" style={{ padding: 24, marginBottom: 20 }}>
        <h2 style={{ fontSize: 20, marginBottom: 12 }}>3. Price & Location</h2>
        <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 12 }}>
          <Field label="Price" required error={errorsByStep[2]?.price}>
            <input
              className="input"
              type="number"
              min={0}
              value={form.price}
              onChange={(e) => { set({ price: e.target.value }); clearError(2, "price"); }}
              style={errorsByStep[2]?.price ? errorBorder : undefined}
            />
          </Field>
          <Field label="Currency">
            <select className="select" value={form.currency} onChange={(e) => set({ currency: e.target.value })}>
              <option value="USD">USD</option>
              <option value="EUR">EUR</option>
              <option value="AMD">AMD</option>
              <option value="RUB">RUB</option>
              <option value="GBP">GBP</option>
            </select>
          </Field>
        </div>
        <label style={{ display: "flex", alignItems: "center", gap: 8, margin: "12px 0" }}>
          <input
            type="checkbox"
            checked={form.is_negotiable}
            onChange={(e) => set({ is_negotiable: e.target.checked })}
          />
          <span className="text-sm">Price is negotiable</span>
        </label>
        <Field label="Category">
          <select className="select" value={form.category_id} onChange={(e) => set({ category_id: e.target.value })}>
            <option value="">Select category</option>
            {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </Field>
        <Field label="Location">
          <select className="select" value={form.location_id} onChange={(e) => set({ location_id: e.target.value })}>
            <option value="">Select location</option>
            {locations.map((l) => <option key={l.id} value={l.id}>{l.display_name}</option>)}
          </select>
        </Field>
      </section>

      {/* Section 4 — Photos */}
      <section id="section-3" className="card" style={{ padding: 24, marginBottom: 20 }}>
        <h2 style={{ fontSize: 20, marginBottom: 12 }}>4. Photos</h2>
        <p className="text-sm muted" style={{ marginBottom: 16 }}>
          Upload multiple images. The first image is set as the main photo — drag any
          photo into the first slot to make it the cover. JPG, PNG, WebP up to 15MB each.
        </p>
        <div
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => { e.preventDefault(); handleUpload(e.dataTransfer.files); }}
          onClick={() => fileInputRef.current?.click()}
          style={{
            border: "2px dashed var(--color-border)",
            borderRadius: 12,
            padding: 32,
            textAlign: "center",
            cursor: uploading ? "wait" : "pointer",
            background: "#fafafa",
            marginBottom: 16,
          }}
        >
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept="image/*"
            hidden
            onChange={(e) => handleUpload(e.target.files)}
          />
          {uploading ? (
            <p>Uploading images...</p>
          ) : (
            <>
              <p style={{ fontWeight: 600 }}>Drop images here</p>
              <p className="text-sm muted">or click to browse</p>
            </>
          )}
        </div>
        {images.length > 0 && (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))", gap: 10 }}>
            {images.map((img) => (
              <div
                key={img.id}
                draggable
                onDragStart={onDragStart(img.id)}
                onDragOver={onDragOver(img.id)}
                onDragLeave={onDragLeave}
                onDrop={onDrop(img.id)}
                style={{
                  position: "relative",
                  aspectRatio: "4/3",
                  borderRadius: 10,
                  overflow: "hidden",
                  cursor: draggingId === img.id ? "grabbing" : "grab",
                  border: dragOverId === img.id
                    ? "2px dashed var(--color-blue)"
                    : img.is_main
                      ? "2px solid var(--color-blue)"
                      : "1px solid var(--color-border)",
                  transform: draggingId === img.id ? "scale(0.96)" : "none",
                  transition: "transform 0.1s, border 0.1s",
                }}
              >
                <img src={img.url} alt="" style={{ width: "100%", height: "100%", objectFit: "cover", pointerEvents: "none" }} />
                {img.is_main && (
                  <span style={{ position: "absolute", top: 6, left: 6 }} className="badge badge-blue">Main</span>
                )}
                <span
                  title="Drag to reorder"
                  style={{
                    position: "absolute", top: 6, right: 6,
                    background: "rgba(0,0,0,0.55)", color: "#fff",
                    padding: "2px 6px", borderRadius: 4, fontSize: 10, fontWeight: 600,
                  }}
                >
                  {img.display_order + 1}
                </span>
                <div style={{ position: "absolute", bottom: 6, right: 6, display: "flex", gap: 4 }}>
                  {!img.is_main && (
                    <button
                      onClick={(e) => { e.stopPropagation(); setMain(img.id); }}
                      className="btn btn-sm"
                      style={{ background: "rgba(255,255,255,0.95)", color: "#111", padding: "2px 6px", fontSize: 11 }}
                    >
                      Set main
                    </button>
                  )}
                  <button
                    onClick={(e) => { e.stopPropagation(); removeImage(img.id); }}
                    className="btn btn-sm"
                    style={{ background: "rgba(220,38,38,0.95)", color: "#fff", padding: "2px 6px", fontSize: 11 }}
                  >
                    ×
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
        <p className="text-sm muted" style={{ marginTop: 8 }}>
          Drag the thumbnails to reorder — the first one automatically becomes the cover photo.
        </p>
      </section>

      {/* Section 5 — Description */}
      <section id="section-4" className="card" style={{ padding: 24, marginBottom: 20 }}>
        <h2 style={{ fontSize: 20, marginBottom: 12 }}>5. Description</h2>
        <Field label="Description" hint="Tell buyers about the condition, history, and any extras.">
          <textarea
            className="textarea"
            rows={6}
            placeholder="Describe your vehicle's condition, history, and any extras."
            value={form.description}
            onChange={(e) => set({ description: e.target.value })}
          />
        </Field>
        <Field label="Features (comma separated)" error={errorsByStep[4]?.features}>
          <input
            className="input"
            placeholder="Bluetooth, Sunroof, Heated Seats"
            value={form.features}
            onChange={(e) => { set({ features: e.target.value }); clearError(4, "features"); }}
            style={errorsByStep[4]?.features ? errorBorder : undefined}
          />
        </Field>
      </section>

      {/* Section 6 — Preview & Submit */}
      <section id="section-5" className="card" style={{ padding: 24, marginBottom: 20 }}>
        <h2 style={{ fontSize: 20, marginBottom: 12 }}>6. Preview</h2>
        <p className="text-sm muted" style={{ marginBottom: 16 }}>
          This is how your listing will look in the search results.
        </p>
        <div className="card" style={{ padding: 20 }}>
          <div className="row" style={{ gap: 12 }}>
            <div style={{ width: 160, height: 120, borderRadius: 8, background: "#1f1f1f", overflow: "hidden" }}>
              {images[0]?.url && <img src={images[0].url} alt="" style={{ width: "100%", height: "100%", objectFit: "cover" }} />}
            </div>
            <div style={{ flex: 1 }}>
              <h3>
                {makes.find((m) => m.id === form.make_id)?.name}{" "}
                {models.find((m) => m.id === form.model_id)?.name}
              </h3>
              <p className="text-sm muted">
                {form.year} · {form.mileage} km · {form.fuel_type} · {form.transmission}
              </p>
              <p style={{ fontSize: 24, fontWeight: 800, marginTop: 6 }}>
                {form.currency} {Number(form.price || 0).toLocaleString()}
              </p>
            </div>
          </div>
          {form.description && (
            <>
              <hr style={{ border: 0, borderTop: "1px solid var(--color-border)", margin: "16px 0" }} />
              <h4>Description</h4>
              <p style={{ whiteSpace: "pre-wrap" }}>{form.description}</p>
            </>
          )}
          {(form.phone_country_code || form.phone_number) && (
            <>
              <hr style={{ border: 0, borderTop: "1px solid var(--color-border)", margin: "16px 0" }} />
              <h4>Contact</h4>
              <p>
                {form.phone_country_code} {form.phone_number}
              </p>
              <p className="text-sm muted">Reach me via: {form.contact_methods.map(labelFor).join(", ")}</p>
            </>
          )}
        </div>
      </section>

      {/* Sticky submit footer */}
      <div
        style={{
          position: "sticky", bottom: 0, background: "var(--color-bg)",
          padding: "16px 0", borderTop: "1px solid var(--color-border)",
          zIndex: 5,
        }}
      >
        <div className="row-between" style={{ maxWidth: 980, margin: "0 auto" }}>
          <span className="text-sm muted">
            All sections filled? You're ready to publish.
          </span>
          <button
            className="btn btn-blue"
            onClick={submit}
            disabled={submitting}
            style={{ padding: "10px 20px" }}
          >
            {submitting ? "Submitting..." : "Submit listing"}
          </button>
        </div>
      </div>
    </div>
  );
};

const errorBorder: React.CSSProperties = {
  borderColor: "var(--color-red)",
  boxShadow: "0 0 0 1px var(--color-red)",
};

function labelFor(m: ContactMethod): string {
  switch (m) {
    case "PHONE": return "Phone call";
    case "WHATSAPP": return "WhatsApp";
    case "VIBER": return "Viber";
    case "TELEGRAM": return "Telegram";
    // Renamed from "In-app chat" — this is the built-in messaging on the
    // website itself (/dashboard/messages), not a separate mobile app.
    case "CHAT": return "Chat on site";
  }
}
