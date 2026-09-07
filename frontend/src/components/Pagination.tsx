import React from "react";

interface PaginationProps {
  page: number;
  totalPages: number;
  onChange: (page: number) => void;
}

export const Pagination: React.FC<PaginationProps> = ({ page, totalPages, onChange }) => {
  if (totalPages <= 1) return null;

  const pages: number[] = [];
  for (let i = 1; i <= totalPages; i++) {
    if (i === 1 || i === totalPages || Math.abs(i - page) <= 2) pages.push(i);
    else if (pages[pages.length - 1] !== -1) pages.push(-1);
  }

  return (
    <nav className="pagination" aria-label="Pagination">
      <button className="btn btn-outline btn-sm" disabled={page <= 1} onClick={() => onChange(page - 1)}>
        ‹ Prev
      </button>
      {pages.map((p, idx) =>
        p === -1 ? (
          <span key={`gap-${idx}`} style={{ padding: "0 8px" }}>…</span>
        ) : (
          <button
            key={p}
            onClick={() => onChange(p)}
            className={`btn btn-sm ${p === page ? "btn-primary" : "btn-outline"}`}
            aria-current={p === page ? "page" : undefined}
          >
            {p}
          </button>
        )
      )}
      <button className="btn btn-outline btn-sm" disabled={page >= totalPages} onClick={() => onChange(page + 1)}>
        Next ›
      </button>
    </nav>
  );
};