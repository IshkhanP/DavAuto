import React, { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { carsService, uploadsService } from "@/services";
import { useAsync } from "@/hooks/useAsync";
import { ErrorState, LoadingBlock } from "@/components/States";
import toast from "react-hot-toast";
import type { CarDetail, CarImage } from "@/types";

export const EditListingPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: car, loading, error, reload } = useAsync<CarDetail | null>(
    async () => (id ? await carsService.get(id) : null),
    [id]
  );

  const [form, setForm] = useState<Record<string, any>>({});
  const [saving, setSubmitting] = useState(false);
  const [images, setImages] = useState<CarImage[]>([]);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Drag-and-drop state
  const [draggingId, setDraggingId] = useState<string | null>(null);
  const [dragOverId, setDragOverId] = useState<string | null>(null);

  useEffect(() => {
    if (car) {
      setForm({
        year: car.year,
        price: car.price,
        currency: car.currency,
        mileage: car.mileage,
        vin: car.vin ?? "",
        body_type: car.body_type,
        fuel_type: car.fuel_type,
        transmission: car.transmission,
        drive_type: car.drive_type,
        engine: car.engine,
        engine_size: car.engine_size,
        horsepower: car.horsepower,
        exterior_color: car.exterior_color,
        interior_color: car.interior_color,
        doors: car.doors,
        seats: car.seats,
        description: car.description,
        condition: car.condition,
      });
      // Initialize images from the car
      setImages(car.images || []);
    }
  }, [car]);

  if (loading) return <LoadingBlock />;
  if (error) return <ErrorState onRetry={reload} />;
  if (!car) return <ErrorState message="Listing not found" />;

  const set = (k: string, v: any) => setForm((p) => ({ ...p, [k]: v }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      const updated = await carsService.update(car.id, form);
      toast.success("Listing updated");
      navigate(`/cars/${updated.id}`);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Update failed");
    } finally {
      setSubmitting(false);
    }
  };

  // ---------- Image handling ----------
  const handleUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    try {
      setUploading(true);
      for (const f of Array.from(files)) {
        try {
          const img = await uploadsService.uploadCarImage(car.id, f);
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
      toast.error(e?.message || "Upload failed");
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
    try {
      await uploadsService.setMainImage(car.id, imgId);
      setImages((prev) => prev.map((i) => ({ ...i, is_main: i.id === imgId })));
    } catch {
      toast.error("Could not set main image");
    }
  };

  // ---------- Drag-and-drop reorder ----------
  const persistOrder = async (orderedIds: string[]) => {
    try {
      await uploadsService.reorderImages(car.id, orderedIds);
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
    setImages((prev) => {
      const fromIdx = prev.findIndex((i) => i.id === fromId);
      const toIdx = prev.findIndex((i) => i.id === toId);
      if (fromIdx < 0 || toIdx < 0) return prev;
      const next = prev.slice();
      const [moved] = next.splice(fromIdx, 1);
      next.splice(toIdx, 0, moved);

      // Whichever photo ends up first is treated as the cover photo — keep
      // "is_main" in sync with position so reordering doesn't leave a stale
      // main image that no longer matches what's shown first in the grid.
      const reordered = next.map((img, idx) => ({ ...img, is_main: idx === 0 }));
      const orderedIds = reordered.map((i) => i.id);
      persistOrder(orderedIds);

      if (prev[0]?.id !== reordered[0].id) {
        uploadsService.setMainImage(car.id, reordered[0].id).catch(() => {
          toast.error("Could not update main image");
        });
      }
      return reordered;
    });
    setDraggingId(null);
    setDragOverId(null);
  };

  return (
    <div style={{ maxWidth: 900, margin: "0 auto" }}>
      <h1 style={{ marginBottom: 8 }}>Edit Listing</h1>
      <p className="muted text-sm" style={{ marginBottom: 16 }}>{car.make_name} {car.model_name} · {car.year}</p>

      <form className="card" style={{ padding: 24, marginBottom: 20 }} onSubmit={submit}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <Field label="Year"><input className="input" type="number" value={form.year ?? ""} onChange={(e) => set("year", Number(e.target.value))} /></Field>
          <Field label="Price"><input className="input" type="number" value={form.price ?? ""} onChange={(e) => set("price", Number(e.target.value))} /></Field>
          <Field label="Currency">
            <select className="select" value={form.currency} onChange={(e) => set("currency", e.target.value)}>
              <option>USD</option><option>EUR</option><option>AMD</option><option>RUB</option><option>GBP</option>
            </select>
          </Field>
          <Field label="Mileage (km)"><input className="input" type="number" value={form.mileage ?? 0} onChange={(e) => set("mileage", Number(e.target.value))} /></Field>
          <Field label="VIN"><input className="input" value={form.vin ?? ""} onChange={(e) => set("vin", e.target.value)} /></Field>
          <Field label="Body type">
            <select className="select" value={form.body_type ?? ""} onChange={(e) => set("body_type", e.target.value)}>
              <option value="">—</option>
              <option>SEDAN</option><option>SUV</option><option>COUPE</option><option>HATCHBACK</option>
              <option>WAGON</option><option>PICKUP</option><option>VAN</option><option>CONVERTIBLE</option><option>CROSSOVER</option>
            </select>
          </Field>
          <Field label="Fuel type">
            <select className="select" value={form.fuel_type ?? ""} onChange={(e) => set("fuel_type", e.target.value)}>
              <option value="">—</option>
              <option>PETROL</option><option>DIESEL</option><option>HYBRID</option><option>PLUGIN_HYBRID</option><option>ELECTRIC</option>
            </select>
          </Field>
          <Field label="Transmission">
            <select className="select" value={form.transmission ?? ""} onChange={(e) => set("transmission", e.target.value)}>
              <option value="">—</option>
              <option>AUTOMATIC</option><option>MANUAL</option><option>SEMI_AUTOMATIC</option><option>CVT</option>
            </select>
          </Field>
          <Field label="Drive type">
            <select className="select" value={form.drive_type ?? ""} onChange={(e) => set("drive_type", e.target.value)}>
              <option value="">—</option>
              <option>FWD</option><option>RWD</option><option>AWD</option><option>FOUR_WD</option>
            </select>
          </Field>
          <Field label="Engine"><input className="input" value={form.engine ?? ""} onChange={(e) => set("engine", e.target.value)} /></Field>
          <Field label="Engine size (L)"><input className="input" type="number" step="0.1" value={form.engine_size ?? ""} onChange={(e) => set("engine_size", e.target.value)} /></Field>
          <Field label="Horsepower"><input className="input" type="number" value={form.horsepower ?? ""} onChange={(e) => set("horsepower", Number(e.target.value))} /></Field>
          <Field label="Exterior color"><input className="input" value={form.exterior_color ?? ""} onChange={(e) => set("exterior_color", e.target.value)} /></Field>
          <Field label="Interior color"><input className="input" value={form.interior_color ?? ""} onChange={(e) => set("interior_color", e.target.value)} /></Field>
          <Field label="Doors"><input className="input" type="number" value={form.doors ?? ""} onChange={(e) => set("doors", Number(e.target.value))} /></Field>
          <Field label="Seats"><input className="input" type="number" value={form.seats ?? ""} onChange={(e) => set("seats", Number(e.target.value))} /></Field>
        </div>
        <div className="field" style={{ marginTop: 16 }}>
          <label>Description</label>
          <textarea className="textarea" rows={4} value={form.description ?? ""} onChange={(e) => set("description", e.target.value)} />
        </div>
        <button className="btn btn-primary" disabled={saving} style={{ marginTop: 16 }}>{saving ? "Saving..." : "Save changes"}</button>
      </form>

      {/* Images Section */}
      <section className="card" style={{ padding: 24, marginBottom: 20 }}>
        <h2 style={{ fontSize: 20, marginBottom: 12 }}>Photos</h2>
        <p className="text-sm muted" style={{ marginBottom: 16 }}>
          Upload additional images, drag to reorder, or set a main photo. Whichever
          photo you drag into the first slot automatically becomes the cover photo.
          JPG, PNG, WebP up to 15MB each.
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
        {images.length === 0 && (
          <p className="text-sm muted" style={{ textAlign: "center", padding: "20px 0" }}>
            No images yet. Upload some above.
          </p>
        )}
        <p className="text-sm muted" style={{ marginTop: 8 }}>
          Drag the thumbnails to reorder — the first one is always the cover photo.
        </p>
      </section>
    </div>
  );
};

const Field: React.FC<{ label: string; children: React.ReactNode }> = ({ label, children }) => (
  <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
    <span className="text-sm fw-6">{label}</span>
    {children}
  </label>
);
