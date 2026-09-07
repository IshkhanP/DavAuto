import React, { useState } from "react";
import { useParams } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { dealersService } from "@/services";
import { useAsync } from "@/hooks/useAsync";
import { CarCard, CarCardGridSkeleton } from "@/components/CarCard";
import { EmptyState, ErrorState, LoadingBlock } from "@/components/States";
import { Pagination } from "@/components/Pagination";

export const DealerDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [page, setPage] = useState(1);

  const dealer = useAsync(async () => (id ? await dealersService.get(id) : null), [id]);
  const cars = useAsync(
    async () => (id ? await dealersService.cars(id, page, 12) : null),
    [id, page]
  );

  if (dealer.loading) return <LoadingBlock />;
  if (dealer.error) return <ErrorState onRetry={dealer.reload} />;
  if (!dealer.data) return <ErrorState message="Dealer not found" />;

  const d = dealer.data;

  return (
    <div className="container" style={{ padding: "2rem 1.25rem" }}>
      <Helmet><title>{d.business_name} — BlackSharkCars</title></Helmet>
      <div className="card" style={{ padding: 24, marginBottom: 24, display: "flex", flexDirection: "column", gap: 16 }}>
        <div className="row" style={{ gap: 16 }}>
          <div style={{
            width: 64, height: 64, background: "var(--color-black)", color: "#fff",
            borderRadius: 14, display: "flex", alignItems: "center", justifyContent: "center",
            fontWeight: 800, fontSize: 24,
          }}>
            {d.business_name?.[0]?.toUpperCase()}
          </div>
          <div style={{ flex: 1 }}>
            <div className="row" style={{ gap: 8 }}>
              <h1>{d.business_name}</h1>
              {d.is_verified && <span className="badge badge-green">Verified</span>}
            </div>
            <p className="text-sm muted">{[d.city, d.country].filter(Boolean).join(", ")}</p>
          </div>
        </div>
        {d.description && <p style={{ marginTop: 4 }}>{d.description}</p>}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 12 }}>
          {d.phone && <div><div className="text-sm muted">Phone</div>{d.phone}</div>}
          {d.email && <div><div className="text-sm muted">Email</div>{d.email}</div>}
          {d.website && <div><div className="text-sm muted">Website</div><a href={d.website} target="_blank" rel="noreferrer" style={{ color: "var(--color-blue)" }}>{d.website}</a></div>}
          {d.working_hours && <div><div className="text-sm muted">Working hours</div>{d.working_hours}</div>}
        </div>
      </div>

      <h2 style={{ marginBottom: 16 }}>Inventory</h2>
      {cars.loading ? <CarCardGridSkeleton count={6} /> :
        cars.error ? <ErrorState onRetry={cars.reload} /> :
          (cars.data?.items.length ?? 0) === 0 ? <EmptyState title="No cars yet" description="This dealer hasn't listed any cars." /> : (
            <>
              <div className="grid-cars">
                {cars.data!.items.map((c) => <CarCard key={c.id} car={c} />)}
              </div>
              <Pagination page={cars.data!.page} totalPages={cars.data!.total_pages} onChange={setPage} />
            </>
          )}
    </div>
  );
};