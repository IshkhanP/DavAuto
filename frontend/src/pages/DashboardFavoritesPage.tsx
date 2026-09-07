import React, { useState } from "react";
import { favoritesService } from "@/services";
import { useAsync } from "@/hooks/useAsync";
import { CarCard, CarCardGridSkeleton } from "@/components/CarCard";
import { EmptyState, ErrorState } from "@/components/States";
import { Pagination } from "@/components/Pagination";
import type { CarCard as CarCardData, PaginatedResponse } from "@/types";

export const DashboardFavoritesPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const { data, loading, error, reload } = useAsync<PaginatedResponse<CarCardData>>(
    () => favoritesService.list(page, 12),
    [page]
  );

  if (loading) return <CarCardGridSkeleton count={6} />;
  if (error) return <ErrorState onRetry={reload} />;
  if (!data || data.items.length === 0)
    return <EmptyState title="No favorites yet" description="Tap the heart on any listing to save it here." />;

  return (
    <div>
      <h1 style={{ marginBottom: 8 }}>Favorites</h1>
      <p className="text-sm muted" style={{ marginBottom: 16 }}>{data.total} saved cars</p>
      <div className="grid-cars">
        {data.items.map((c) => (
          <CarCard key={c.id} car={c} onFavoriteChange={reload} />
        ))}
      </div>
      <Pagination page={data.page} totalPages={data.total_pages} onChange={setPage} />
    </div>
  );
};