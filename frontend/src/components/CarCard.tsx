import React, { useState } from "react";
import { Link } from "react-router-dom";
import type { CarCard as CarCardData } from "@/types";
import { favoritesService } from "@/services";
import { useAuth } from "@/context/AuthContext";
import { formatCurrency, formatMileage, fuelLabel } from "@/utils/format";
import toast from "react-hot-toast";

interface CarCardProps {
  car: CarCardData;
  /** Initial favorited state (typically passed in by the parent for list views). */
  initiallyFavorited?: boolean;
  onFavoriteChange?: (favorited: boolean) => void;
}

export const CarCard: React.FC<CarCardProps> = ({ car, initiallyFavorited = false, onFavoriteChange }) => {
  const { user } = useAuth();
  const [favorited, setFavorited] = useState(initiallyFavorited);

  const toggleFavorite = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!user) {
      toast.error("Please login to favorite cars");
      return;
    }
    try {
      const res = await favoritesService.toggle(car.id);
      setFavorited(res.favorited);
      onFavoriteChange?.(res.favorited);
      toast.success(res.favorited ? "Added to favorites" : "Removed from favorites");
    } catch {
      toast.error("Could not update favorite");
    }
  };

  return (
    <Link to={`/cars/${car.id}`} style={{ textDecoration: "none" }}>
      <article className="card" style={{
        background: "#fff", borderRadius: 12, overflow: "hidden",
        transition: "transform 200ms, box-shadow 200ms", cursor: "pointer",
        border: "1px solid var(--color-border)",
      }} onMouseEnter={(e) => { e.currentTarget.style.transform = "translateY(-2px)"; e.currentTarget.style.boxShadow = "var(--shadow-md)"; }}
         onMouseLeave={(e) => { e.currentTarget.style.transform = ""; e.currentTarget.style.boxShadow = ""; }}
      >
        <div style={{ position: "relative", aspectRatio: "4/3", background: "#1f1f1f" }}>
          {car.main_image ? (
            <img
              src={car.main_image}
              alt={`${car.make} ${car.model}`}
              loading="lazy"
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
          ) : (
            <div style={{
              width: "100%", height: "100%",
              display: "flex", alignItems: "center", justifyContent: "center",
              color: "#6b7280", fontSize: 14,
            }}>
              No image
            </div>
          )}

          {/* Badges */}
          <div style={{ position: "absolute", top: 10, left: 10, display: "flex", flexDirection: "column", gap: 4 }}>
            {car.is_featured && <span className="badge badge-amber">Featured</span>}
            {car.is_promoted && <span className="badge badge-blue">Promoted</span>}
          </div>

          {/* Favorite */}
          <button
            onClick={toggleFavorite}
            aria-label="Toggle favorite"
            style={{
              position: "absolute", top: 10, right: 10,
              width: 36, height: 36, borderRadius: "50%",
              background: "rgba(255, 255, 255, 0.92)", display: "flex",
              alignItems: "center", justifyContent: "center", border: "none",
              cursor: "pointer", boxShadow: "var(--shadow-sm)",
            }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill={favorited ? "#dc2626" : "none"} stroke={favorited ? "#dc2626" : "#111"} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
            </svg>
          </button>
        </div>

        <div style={{ padding: 16 }}>
          <h3 style={{ fontSize: 16, marginBottom: 4 }}>
            {car.make} {car.model}
          </h3>
          <p className="text-sm muted" style={{ marginBottom: 8 }}>
            {car.year} · {formatMileage(car.mileage)} · {fuelLabel(car.fuel_type)} · {fuelLabel(car.transmission)}
          </p>
          <div style={{ fontWeight: 800, fontSize: 20, marginBottom: 6 }}>
            {formatCurrency(car.price, car.currency)}
          </div>
          <div className="text-sm muted" style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
            {car.city ? `${car.city}${car.country ? `, ${car.country}` : ""}` : "Location not set"}
          </div>
        </div>
      </article>
    </Link>
  );
};

export const CarCardSkeleton: React.FC = () => (
  <div className="card" style={{ borderRadius: 12, overflow: "hidden", border: "1px solid var(--color-border)" }}>
    <div className="skeleton" style={{ aspectRatio: "4/3" }} />
    <div style={{ padding: 16 }}>
      <div className="skeleton" style={{ height: 16, width: "70%", marginBottom: 8 }} />
      <div className="skeleton" style={{ height: 12, width: "90%", marginBottom: 12 }} />
      <div className="skeleton" style={{ height: 20, width: "40%", marginBottom: 8 }} />
      <div className="skeleton" style={{ height: 12, width: "60%" }} />
    </div>
  </div>
);

export const CarCardGridSkeleton: React.FC<{ count?: number }> = ({ count = 8 }) => (
  <div className="grid-cars">
    {Array.from({ length: count }).map((_, i) => (
      <CarCardSkeleton key={i} />
    ))}
  </div>
);