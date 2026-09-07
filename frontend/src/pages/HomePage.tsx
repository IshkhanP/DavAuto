import React from "react";
import { Link } from "react-router-dom";
import { CarCard, CarCardGridSkeleton } from "@/components/CarCard";
import { HeroSearch } from "@/components/HeroSearch";
import { ErrorState } from "@/components/States";
import { carsService, catalogService, dealersService } from "@/services";
import { useAsync } from "@/hooks/useAsync";
import type { CarCard as CarCardData, Category, Dealer, Make } from "@/types";

export const HomePage: React.FC = () => {
  const featured = useAsync(() => carsService.featured(8), []);
  const latest = useAsync(() => carsService.latest(12), []);
  const makes = useAsync(() => catalogService.makes(), []);
  const categories = useAsync(() => catalogService.categories(), []);
  const dealers = useAsync(() => dealersService.list(), []);

  return (
    <div>
      {/* Hero */}
      <section style={{
        background: "linear-gradient(180deg, #0a0a0a 0%, #111 100%)",
        color: "#fff", padding: "4.5rem 0 3rem",
        position: "relative", overflow: "hidden",
      }}>
        <div style={{
          position: "absolute", inset: 0, opacity: 0.1,
          backgroundImage: "radial-gradient(circle at 30% 50%, rgba(37,99,235,0.4), transparent 60%)",
        }} />
        <div className="container" style={{ position: "relative" }}>
          <h1 style={{ fontSize: "clamp(2rem, 4.5vw, 3.5rem)", maxWidth: 720 }}>
            Find Your Next <span style={{ color: "#2563eb" }}>Car</span>
          </h1>
          <p style={{ marginTop: 12, color: "#cbd5e1", maxWidth: 540, fontSize: 17 }}>
            Browse thousands of vehicles from trusted sellers and dealers. Premium selection, transparent pricing.
          </p>
          <div style={{ marginTop: 28 }}>
            <HeroSearch />
          </div>
        </div>
      </section>

      {/* Featured */}
      <section className="section">
        <div className="container">
          <div className="section-title">
            <h2>Featured Cars</h2>
            <Link to="/cars" className="btn btn-ghost btn-sm">View all →</Link>
          </div>
          {featured.loading ? (
            <CarCardGridSkeleton count={4} />
          ) : featured.error ? (
            <ErrorState message={featured.error} onRetry={featured.reload} />
          ) : (
            <div className="grid-cars">
              {(featured.data ?? []).map((c) => <CarCard key={c.id} car={c} />)}
            </div>
          )}
        </div>
      </section>

      {/* Popular Makes */}
      <section className="section" style={{ background: "var(--color-bg-soft)" }}>
        <div className="container">
          <div className="section-title">
            <h2>Popular Makes</h2>
            <Link to="/cars" className="btn btn-ghost btn-sm">All makes →</Link>
          </div>
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(120px, 1fr))",
            gap: 10,
          }}>
            {(makes.data ?? []).slice(0, 15).map((m: Make) => (
              <Link key={m.id} to={`/cars?make_id=${m.id}`} className="card" style={{
                padding: "1.25rem 0.5rem", textAlign: "center", borderRadius: 10,
                display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700,
              }}>
                {m.name}
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Popular Categories */}
      <section className="section">
        <div className="container">
          <div className="section-title">
            <h2>Browse by Category</h2>
          </div>
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))",
            gap: 12,
          }}>
            {(categories.data ?? []).map((c: Category) => (
              <Link key={c.id} to={`/cars?body_type=${c.slug.toUpperCase()}`} className="card" style={{
                padding: "1.5rem 1rem", textAlign: "center", borderRadius: 12,
              }}>
                <div style={{
                  width: 48, height: 48, margin: "0 auto 12px",
                  background: "var(--color-light-gray)", borderRadius: "50%",
                  display: "flex", alignItems: "center", justifyContent: "center",
                }}>
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 17h14l-1.5-6h-11z"/><circle cx="7.5" cy="17.5" r="1.5"/><circle cx="16.5" cy="17.5" r="1.5"/></svg>
                </div>
                <div style={{ fontWeight: 700 }}>{c.name}</div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Latest Cars */}
      <section className="section" style={{ background: "var(--color-bg-soft)" }}>
        <div className="container">
          <div className="section-title">
            <h2>Latest Listings</h2>
            <Link to="/cars?sort=newest" className="btn btn-ghost btn-sm">See more →</Link>
          </div>
          {latest.loading ? (
            <CarCardGridSkeleton count={8} />
          ) : latest.error ? (
            <ErrorState message={latest.error} onRetry={latest.reload} />
          ) : (
            <div className="grid-cars">
              {(latest.data ?? []).map((c: CarCardData) => <CarCard key={c.id} car={c} />)}
            </div>
          )}
        </div>
      </section>

      {/* Dealers */}
      <section className="section">
        <div className="container">
          <div className="section-title">
            <h2>Featured Dealers</h2>
            <Link to="/dealers" className="btn btn-ghost btn-sm">All dealers →</Link>
          </div>
          <div style={{
            display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 14,
          }}>
            {(dealers.data ?? []).slice(0, 6).map((d: Dealer) => (
              <Link key={d.id} to={`/dealers/${d.id}`} className="card" style={{
                padding: 18, borderRadius: 12, display: "flex", flexDirection: "column", gap: 8,
              }}>
                <div className="row" style={{ gap: 12 }}>
                  <div style={{
                    width: 48, height: 48, background: "var(--color-black)", color: "#fff",
                    borderRadius: 10, display: "flex", alignItems: "center", justifyContent: "center",
                    fontWeight: 800, fontSize: 18,
                  }}>
                    {d.business_name?.[0]?.toUpperCase() ?? "D"}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 700 }}>{d.business_name}</div>
                    <div className="text-sm muted">{d.city}{d.country ? `, ${d.country}` : ""}</div>
                  </div>
                  {d.is_verified && <span className="badge badge-green">Verified</span>}
                </div>
                <p className="text-sm muted" style={{ marginTop: 4 }}>
                  {d.description?.slice(0, 100) || "Authorized dealer"}
                </p>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="section" style={{ background: "var(--color-bg-soft)" }}>
        <div className="container">
          <h2 style={{ textAlign: "center", marginBottom: 32 }}>How BlackSharkCars Works</h2>
          <div style={{
            display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 20,
          }}>
            {[
              { n: 1, t: "Search & Filter", d: "Find vehicles by make, model, price, year, location and many more filters." },
              { n: 2, t: "Contact Seller", d: "Reach out via in-app messaging or call directly. Always stay on platform for safety." },
              { n: 3, t: "Inspect & Test Drive", d: "Meet the seller, inspect the vehicle, and take it for a test drive." },
              { n: 4, t: "Drive Away", d: "Complete the transaction and drive away with confidence." },
            ].map((s) => (
              <div key={s.n} style={{ textAlign: "center", padding: "1rem" }}>
                <div style={{
                  width: 48, height: 48, margin: "0 auto 12px",
                  background: "var(--color-black)", color: "#fff", borderRadius: "50%",
                  display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 800,
                }}>
                  {s.n}
                </div>
                <h3 style={{ fontSize: 17, marginBottom: 6 }}>{s.t}</h3>
                <p className="text-sm muted">{s.d}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Why BlackSharkCars */}
      <section className="section" style={{ background: "#0a0a0a", color: "#fff" }}>
        <div className="container">
          <h2 style={{ textAlign: "center", marginBottom: 32 }}>Why BlackSharkCars</h2>
          <div style={{
            display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 20,
          }}>
            {[
              { t: "Verified Dealers", d: "We verify dealerships to keep listings trustworthy." },
              { t: "Secure Messaging", d: "Communicate safely without sharing your phone number." },
              { t: "Powerful Search", d: "Find exactly what you want with advanced filters." },
              { t: "Free to List", d: "Sellers can list vehicles at no cost, with optional promotions." },
            ].map((s) => (
              <div key={s.t} className="card" style={{
                background: "#161616", color: "#e5e7eb", border: "1px solid #1f1f1f",
                padding: 20, borderRadius: 12,
              }}>
                <h3 style={{ fontSize: 17, marginBottom: 6 }}>{s.t}</h3>
                <p className="text-sm" style={{ color: "#9ca3af" }}>{s.d}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
};