import React, { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { CarCard, CarCardGridSkeleton } from "@/components/CarCard";
import { FilterSidebar, FilterValues } from "@/components/FilterSidebar";
import { Pagination } from "@/components/Pagination";
import { EmptyState, ErrorState } from "@/components/States";
import { carsService } from "@/services";
import { useAsync } from "@/hooks/useAsync";
import type { CarCard as CarCardData, PaginatedResponse, SearchFilters } from "@/types";

const SORT_OPTIONS = [
  { value: "newest", label: "Newest" },
  { value: "price_asc", label: "Price: low → high" },
  { value: "price_desc", label: "Price: high → low" },
  { value: "mileage_asc", label: "Mileage: low → high" },
  { value: "year_desc", label: "Year: newest" },
  { value: "views_desc", label: "Most viewed" },
];

export const SearchPage: React.FC = () => {
  const [params, setParams] = useSearchParams();
  const [showMobileFilters, setShowMobileFilters] = useState(false);

  const initial: SearchFilters = {
    make_id: params.get("make_id") ?? undefined,
    model_id: params.get("model_id") ?? undefined,
    category_id: params.get("category_id") ?? undefined,
    body_type: params.get("body_type") ?? undefined,
    fuel_type: params.get("fuel_type") ?? undefined,
    transmission: params.get("transmission") ?? undefined,
    drive_type: params.get("drive_type") ?? undefined,
    condition: params.get("condition") ?? undefined,
    country: params.get("country") ?? undefined,
    city: params.get("city") ?? undefined,
    min_price: params.get("min_price") ? Number(params.get("min_price")) : undefined,
    max_price: params.get("max_price") ? Number(params.get("max_price")) : undefined,
    min_year: params.get("min_year") ? Number(params.get("min_year")) : undefined,
    max_year: params.get("max_year") ? Number(params.get("max_year")) : undefined,
    min_mileage: params.get("min_mileage") ? Number(params.get("min_mileage")) : undefined,
    max_mileage: params.get("max_mileage") ? Number(params.get("max_mileage")) : undefined,
    color: params.get("color") ?? undefined,
    seller_type: params.get("seller_type") ?? undefined,
    q: params.get("q") ?? undefined,
    sort: params.get("sort") ?? "newest",
    page: params.get("page") ? Number(params.get("page")) : 1,
    limit: 24,
  };

  const [filters, setFilters] = useState<SearchFilters>(initial);

  // Sync URL when filters change
  useEffect(() => {
    const p = new URLSearchParams();
    Object.entries(filters).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "" && v !== 1 && v !== 24) p.set(k, String(v));
      else if (k === "page" && v && v !== 1) p.set(k, String(v));
      else if (k === "sort" && v && v !== "newest") p.set(k, String(v));
    });
    setParams(p, { replace: true });
  }, [filters]);

  const { data, loading, error, reload } = useAsync<PaginatedResponse<CarCardData>>(
    () => carsService.search(filters),
    [JSON.stringify(filters)]
  );

  return (
    <div className="container" style={{ padding: "1.5rem 1.25rem" }}>
      <div className="row-between" style={{ marginBottom: 16 }}>
        <h1 style={{ fontSize: 24 }}>Browse Cars</h1>
        <div className="row" style={{ gap: 8 }}>
          <select
            className="select"
            style={{ width: "auto" }}
            value={filters.sort || "newest"}
            onChange={(e) => setFilters({ ...filters, sort: e.target.value, page: 1 })}
          >
            {SORT_OPTIONS.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
          </select>
          <button className="btn btn-outline show-mobile" onClick={() => setShowMobileFilters(true)}>
            Filters
          </button>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "280px 1fr", gap: 24 }} className="search-layout">
        <div className="hide-mobile">
          <FilterSidebar
            values={filters as FilterValues}
            onChange={(v) => setFilters({ ...filters, ...v, page: 1 })}
          />
        </div>

        <div>
          {loading ? (
            <CarCardGridSkeleton count={8} />
          ) : error ? (
            <ErrorState message={error} onRetry={reload} />
          ) : (data?.items?.length ?? 0) === 0 ? (
            <EmptyState
              title="No cars found"
              description="Try adjusting your filters or removing some to see more listings."
              action={{ label: "Reset filters", onClick: () => setFilters({ page: 1, limit: 24, sort: "newest" }) }}
            />
          ) : (
            <>
              <p className="text-sm muted" style={{ marginBottom: 12 }}>
                {data?.total?.toLocaleString()} results
              </p>
              <div className="grid-cars">
                {data!.items.map((c) => <CarCard key={c.id} car={c} />)}
              </div>
              <Pagination page={data!.page} totalPages={data!.total_pages} onChange={(p) => setFilters({ ...filters, page: p })} />
            </>
          )}
        </div>
      </div>

      {showMobileFilters && (
        <FilterSidebar
          isMobile
          values={filters as FilterValues}
          onChange={(v) => setFilters({ ...filters, ...v, page: 1 })}
          onClose={() => setShowMobileFilters(false)}
        />
      )}

      <style>{`
        @media (max-width: 900px) {
          .search-layout { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </div>
  );
};