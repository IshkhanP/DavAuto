import React, { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { carsService, favoritesService, messagingService, reportsService } from "@/services";
import { useAsync } from "@/hooks/useAsync";
import { useAuth } from "@/context/AuthContext";
import { CarCard, CarCardGridSkeleton } from "@/components/CarCard";
import { ErrorState, LoadingBlock } from "@/components/States";
import { formatCurrency, formatMileage, fuelLabel, timeAgo } from "@/utils/format";
import toast from "react-hot-toast";
import type { CarDetail, CarCard as CarCardData, ContactMethod } from "@/types";

// NOTE: "CHAT" is the built-in messaging on the website itself
// (/dashboard/messages) — not a separate app — so it's labeled "Chat on
// site" rather than "In-app chat" to avoid implying a mobile app is needed.
const CONTACT_LABEL: Record<ContactMethod, string> = {
  PHONE: "Phone",
  WHATSAPP: "WhatsApp",
  VIBER: "Viber",
  TELEGRAM: "Telegram",
  CHAT: "Chat on site",
};

export const CarDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const navigate = useNavigate();

  const { data: car, loading, error, reload } = useAsync<CarDetail | null>(
    async () => (id ? await carsService.get(id) : null),
    [id]
  );

  const similar = useAsync<CarCardData[]>(
    async () => (id ? await carsService.similar(id, 6) : []),
    [id]
  );

  const [activeImage, setActiveImage] = useState(0);
  const [showGallery, setShowGallery] = useState(false);
  const [showContact, setShowContact] = useState(false);
  const [showReport, setShowReport] = useState(false);
  const [contactMessage, setContactMessage] = useState("");

  useEffect(() => {
    setActiveImage(0);
  }, [id]);

  if (loading) return <LoadingBlock height={400} />;
  if (error) return <ErrorState message={error} onRetry={reload} />;
  if (!car) return <ErrorState message="Car not found" />;

  const isOwner = user?.id === car.seller.id;

  const handleFavorite = async () => {
    if (!user) return navigate("/login");
    try {
      await favoritesService.add(car.id);
      toast.success("Added to favorites");
    } catch {
      toast.error("Could not favorite");
    }
  };

  const handleSendMessage = async () => {
    if (!user) return navigate("/login");
    try {
      const conv = await messagingService.createOrGet({
        car_id: car.id,
        recipient_id: car.seller.id,
        subject: `About: ${car.make_name} ${car.model_name}`,
        initial_message: contactMessage || "Hi, is this still available?",
      });
      toast.success("Message sent");
      setShowContact(false);
      navigate(`/dashboard/messages?c=${conv.id}`);
    } catch (e: any) {
      toast.error(e?.message || "Could not send message");
    }
  };

  const handleReport = async (reason: string, description: string) => {
    try {
      await reportsService.create({ car_id: car.id, reason, description });
      toast.success("Report submitted");
      setShowReport(false);
    } catch (e: any) {
      toast.error(e?.message || "Could not submit report");
    }
  };

  return (
    <div className="container" style={{ padding: "1.5rem 1.25rem" }}>
      <Helmet>
        <title>{`${car.make_name} ${car.model_name} ${car.year} — BlackSharkCars`}</title>
        <meta name="description" content={`${car.year} ${car.make_name} ${car.model_name} for ${formatCurrency(car.price, car.currency)}. ${car.description?.slice(0, 140) || ""}`} />
        <meta property="og:title" content={`${car.make_name} ${car.model_name} ${car.year}`} />
        <meta property="og:description" content={formatCurrency(car.price, car.currency)} />
        {car.images[0] && <meta property="og:image" content={car.images[0].url} />}
        <link rel="canonical" href={`${window.location.origin}/cars/${car.id}`} />
      </Helmet>

      <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 28 }} className="detail-grid">
        {/* Gallery */}
        <div>
          <div
            onClick={() => car.images.length > 0 && setShowGallery(true)}
            style={{
              aspectRatio: "4/3",
              background: "#1f1f1f", borderRadius: 12, overflow: "hidden",
              cursor: car.images.length ? "zoom-in" : "default",
            }}
          >
            {car.images.length > 0 ? (
              <img src={car.images[activeImage]?.url} alt="" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            ) : (
              <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", color: "#6b7280" }}>No image</div>
            )}
          </div>
          {car.images.length > 1 && (
            <div style={{
              display: "flex", gap: 8, marginTop: 12, overflowX: "auto",
            }}>
              {car.images.map((img, idx) => (
                <button
                  key={img.id}
                  onClick={() => setActiveImage(idx)}
                  style={{
                    width: 80, height: 60, borderRadius: 8, overflow: "hidden",
                    border: idx === activeImage ? "2px solid var(--color-blue)" : "2px solid transparent",
                    flexShrink: 0, padding: 0,
                  }}
                >
                  <img src={img.thumbnail_url || img.url} alt="" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                </button>
              ))}
            </div>
          )}

          {/* Specs */}
          <section style={{ marginTop: 28 }}>
            <h2 style={{ marginBottom: 12 }}>Specifications</h2>
            <div className="card" style={{ padding: 16, display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: 12 }}>
              <Spec label="Year" value={car.year.toString()} />
              <Spec label="Mileage" value={formatMileage(car.mileage)} />
              <Spec label="Fuel Type" value={fuelLabel(car.fuel_type)} />
              <Spec label="Transmission" value={fuelLabel(car.transmission)} />
              <Spec label="Body Type" value={fuelLabel(car.body_type)} />
              <Spec label="Drive Type" value={fuelLabel(car.drive_type)} />
              <Spec label="Engine" value={car.engine || "—"} />
              {car.engine_size && <Spec label="Engine Size" value={`${car.engine_size}L`} />}
              {car.horsepower && <Spec label="Horsepower" value={`${car.horsepower} HP`} />}
              <Spec label="Exterior Color" value={car.exterior_color || "—"} />
              <Spec label="Interior Color" value={car.interior_color || "—"} />
              {car.doors && <Spec label="Doors" value={car.doors.toString()} />}
              {car.seats && <Spec label="Seats" value={car.seats.toString()} />}
              <Spec label="Condition" value={fuelLabel(car.condition)} />
              {car.vin && <Spec label="VIN" value={car.vin} />}
            </div>
          </section>

          {/* Description */}
          {car.description && (
            <section style={{ marginTop: 28 }}>
              <h2 style={{ marginBottom: 12 }}>Description</h2>
              <div className="card" style={{ padding: 16 }}>
                <p style={{ whiteSpace: "pre-wrap" }}>{car.description}</p>
              </div>
            </section>
          )}

          {/* Features */}
          {car.features.length > 0 && (
            <section style={{ marginTop: 28 }}>
              <h2 style={{ marginBottom: 12 }}>Features</h2>
              <div className="card" style={{ padding: 16, display: "flex", flexWrap: "wrap", gap: 8 }}>
                {car.features.map((f) => (
                  <span key={f.id} className="badge">{f.name}{f.value ? `: ${f.value}` : ""}</span>
                ))}
              </div>
            </section>
          )}
        </div>

        {/* Sidebar */}
        <aside>
          <div className="card" style={{ padding: 20, position: "sticky", top: 80 }}>
            <div className="row" style={{ gap: 8, marginBottom: 6 }}>
              {car.is_featured && <span className="badge badge-amber">Featured</span>}
              {car.is_promoted && <span className="badge badge-blue">Promoted</span>}
              {car.status === "SOLD" && <span className="badge badge-red">Sold</span>}
            </div>
            <h1 style={{ fontSize: 24 }}>{car.make_name} {car.model_name}</h1>
            <p className="muted text-sm" style={{ marginTop: 4 }}>{car.year} · {car.location_display}</p>

            <div style={{ fontSize: 32, fontWeight: 800, marginTop: 16 }}>
              {formatCurrency(car.price, car.currency)}
              {car.is_negotiable && <span className="badge badge-green" style={{ marginLeft: 8, verticalAlign: "middle" }}>Negotiable</span>}
            </div>

            <div className="row" style={{ marginTop: 16, gap: 8 }}>
              <button onClick={handleFavorite} className="btn btn-outline btn-block" disabled={isOwner}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
                Save
              </button>
              {/* The "Message" button is only shown when CHAT isn't already
                  offered in the contact-methods list (avoids duplication with
                  the "Chat on site" button rendered inside the contact
                  section below). Both paths open the same on-site messaging
                  under /dashboard/messages. */}
              {!(car.contact_methods?.includes("CHAT")) && (
                <button onClick={() => setShowContact(true)} className="btn btn-blue btn-block" disabled={isOwner}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                  Message
                </button>
              )}
            </div>

            <button
              onClick={() => setShowReport(true)}
              className="btn btn-ghost btn-sm btn-block"
              style={{ marginTop: 8 }}
              disabled={isOwner}
            >
              Report listing
            </button>

            <hr style={{ border: 0, borderTop: "1px solid var(--color-border)", margin: "16px 0" }} />

            <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
              {car.seller.avatar_url ? (
                <img
                  src={car.seller.avatar_url}
                  alt={car.seller.full_name}
                  style={{ width: 44, height: 44, borderRadius: 10, objectFit: "cover" }}
                />
              ) : (
                <div style={{
                  width: 44, height: 44, background: "var(--color-black)", color: "#fff", borderRadius: 10,
                  display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 800,
                }}>
                  {car.seller.full_name?.[0]?.toUpperCase()}
                </div>
              )}
              <div>
                <div style={{ fontWeight: 700 }}>{car.seller.full_name}</div>
                <div className="text-sm muted">
                  {car.seller.seller_type === "DEALER" ? "Dealer" : "Private seller"}
                  {car.seller.city ? ` · ${car.seller.city}` : ""}
                </div>
              </div>
            </div>

            <div style={{ marginTop: 16, fontSize: 13, color: "var(--color-text-muted)" }}>
              <div className="row-between" style={{ padding: "4px 0" }}>
                <span>Views</span><span>{car.views_count}</span>
              </div>
              <div className="row-between" style={{ padding: "4px 0" }}>
                <span>Favorites</span><span>{car.favorites_count}</span>
              </div>
              <div className="row-between" style={{ padding: "4px 0" }}>
                <span>Listed</span><span>{timeAgo(car.published_at || car.created_at)}</span>
              </div>
            </div>
            {car.contact_methods && car.contact_methods.length > 0 && (
              <>
                <hr style={{ border: 0, borderTop: "1px solid #2a2a2a", margin: "12px 0" }} />
                <div className="text-sm" style={{ color: "#9ca3af", marginBottom: 4 }}>Contact</div>
                {car.phone_number && (
                  <div style={{ fontWeight: 700, fontSize: 18 }}>
                    {car.phone_country_code || ""} {car.phone_number}
                  </div>
                )}
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 8 }}>
                  {car.contact_methods.map((m) => (
                    <span key={m} className="badge badge-blue">{CONTACT_LABEL[m as ContactMethod] ?? m}</span>
                  ))}
                </div>
                <div style={{ display: "grid", gap: 6, marginTop: 10 }}>
                  {car.contact_methods.includes("PHONE") && car.phone_number && (
                    <a className="btn btn-outline" href={`tel:${car.phone_country_code ?? ""}${car.phone_number.replace(/\s/g, "")}`}>
                      📞 Call
                    </a>
                  )}
                  {car.contact_methods.includes("WHATSAPP") && car.phone_number && (
                    <a
                      className="btn btn-outline"
                      target="_blank"
                      rel="noreferrer"
                      href={`https://wa.me/${(car.phone_country_code ?? "").replace("+", "")}${car.phone_number.replace(/\D/g, "")}`}
                    >
                      💬 WhatsApp
                    </a>
                  )}
                  {car.contact_methods.includes("VIBER") && car.phone_number && (
                    <a
                      className="btn btn-outline"
                      target="_blank"
                      rel="noreferrer"
                      href={`viber://chat?number=%2B${(car.phone_country_code ?? "").replace("+", "")}${car.phone_number.replace(/\D/g, "")}`}
                    >
                      📱 Viber
                    </a>
                  )}
                  {car.contact_methods.includes("TELEGRAM") && car.phone_number && (
                    <a
                      className="btn btn-outline"
                      target="_blank"
                      rel="noreferrer"
                      href={`https://t.me/${(car.phone_country_code ?? "").replace("+", "")}${car.phone_number.replace(/\D/g, "")}`}
                    >
                      ✈️ Telegram
                    </a>
                  )}
                  {car.contact_methods.includes("CHAT") && (
                    <button className="btn btn-blue" onClick={() => setShowContact(true)} disabled={isOwner}>
                      💬 Chat on site
                    </button>
                  )}
                </div>
              </>
            )}
          </div>
        </aside>
      </div>

      {/* Similar */}
      <section style={{ marginTop: 40 }}>
        <h2 style={{ marginBottom: 16 }}>Similar Cars</h2>
        {similar.loading ? <CarCardGridSkeleton count={4} /> : (
          <div className="grid-cars">
            {(similar.data ?? []).map((c) => <CarCard key={c.id} car={c} />)}
          </div>
        )}
      </section>

      {/* Gallery modal */}
      {showGallery && (
        <div className="modal-backdrop" onClick={() => setShowGallery(false)}>
          <div onClick={(e) => e.stopPropagation()} style={{ maxWidth: 1100, width: "100%", maxHeight: "90vh" }}>
            <img src={car.images[activeImage]?.url} alt="" style={{ width: "100%", maxHeight: "85vh", objectFit: "contain" }} />
            <div className="row-between" style={{ marginTop: 8 }}>
              <button className="btn btn-outline btn-sm" onClick={() => setActiveImage((i) => Math.max(0, i - 1))}>‹ Prev</button>
              <span className="text-sm muted">{activeImage + 1} / {car.images.length}</span>
              <button className="btn btn-outline btn-sm" onClick={() => setActiveImage((i) => Math.min(car.images.length - 1, i + 1))}>Next ›</button>
            </div>
          </div>
        </div>
      )}

      {/* Contact modal */}
      {showContact && (
        <div className="modal-backdrop" onClick={() => setShowContact(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2 style={{ marginBottom: 8 }}>Chat on Site</h2>
            <p className="text-sm muted" style={{ marginBottom: 16 }}>
              Send a message about this vehicle using BlackSharkCars' built-in messaging —
              no separate app needed. You'll find the conversation under "Messages" in your dashboard.
            </p>
            <textarea
              className="textarea"
              rows={4}
              placeholder="Hi, is this still available?"
              value={contactMessage}
              onChange={(e) => setContactMessage(e.target.value)}
            />
            <div className="row" style={{ gap: 8, marginTop: 12, justifyContent: "flex-end" }}>
              <button className="btn btn-ghost" onClick={() => setShowContact(false)}>Cancel</button>
              <button className="btn btn-blue" onClick={handleSendMessage}>Send Message</button>
            </div>
          </div>
        </div>
      )}

      {/* Report modal */}
      {showReport && (
        <ReportModal carId={car.id} onClose={() => setShowReport(false)} onSubmit={handleReport} />
      )}

      <style>{`
        @media (max-width: 900px) {
          .detail-grid { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </div>
  );
};

const Spec: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div>
    <div className="text-sm muted" style={{ textTransform: "uppercase", letterSpacing: 0.4 }}>{label}</div>
    <div style={{ fontWeight: 600 }}>{value}</div>
  </div>
);

const ReportModal: React.FC<{ carId: string; onClose: () => void; onSubmit: (reason: string, description: string) => void }> = ({ onClose, onSubmit }) => {
  const [reason, setReason] = useState("SCAM");
  const [description, setDescription] = useState("");
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2 style={{ marginBottom: 8 }}>Report Listing</h2>
        <div className="field">
          <label>Reason</label>
          <select className="select" value={reason} onChange={(e) => setReason(e.target.value)}>
            <option value="SCAM">Scam</option>
            <option value="FAKE_LISTING">Fake listing</option>
            <option value="INCORRECT_INFO">Incorrect information</option>
            <option value="DUPLICATE">Duplicate listing</option>
            <option value="OFFENSIVE">Offensive content</option>
            <option value="SOLD_VEHICLE">Already sold</option>
            <option value="OTHER">Other</option>
          </select>
        </div>
        <div className="field">
          <label>Details (optional)</label>
          <textarea className="textarea" rows={3} value={description} onChange={(e) => setDescription(e.target.value)} />
        </div>
        <div className="row" style={{ gap: 8, marginTop: 12, justifyContent: "flex-end" }}>
          <button className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn btn-danger" onClick={() => onSubmit(reason, description)}>Submit Report</button>
        </div>
      </div>
    </div>
  );
};
