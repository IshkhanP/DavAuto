import React from "react";

interface EmptyStateProps {
  title: string;
  description?: string;
  action?: { label: string; onClick: () => void };
  icon?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ title, description, action, icon }) => (
  <div style={{
    background: "#fff",
    border: "1px dashed var(--color-border)",
    borderRadius: 14,
    padding: "3rem 1.5rem",
    textAlign: "center",
  }}>
    <div style={{
      width: 60, height: 60, margin: "0 auto 1rem",
      background: "var(--color-light-gray)", borderRadius: "50%",
      display: "flex", alignItems: "center", justifyContent: "center",
      color: "var(--color-text-muted)",
    }}>
      {icon ?? (
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
      )}
    </div>
    <h3 style={{ fontSize: 18, marginBottom: 6 }}>{title}</h3>
    {description && <p className="text-sm muted" style={{ maxWidth: 380, margin: "0 auto" }}>{description}</p>}
    {action && (
      <button onClick={action.onClick} className="btn btn-primary" style={{ marginTop: 16 }}>
        {action.label}
      </button>
    )}
  </div>
);

interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
}
export const ErrorState: React.FC<ErrorStateProps> = ({ message = "Something went wrong", onRetry }) => (
  <div style={{
    background: "#fff", border: "1px solid var(--color-border)", borderRadius: 14,
    padding: "2.5rem 1.5rem", textAlign: "center",
  }}>
    <div style={{
      width: 56, height: 56, margin: "0 auto 1rem",
      background: "rgba(220, 38, 38, 0.1)", borderRadius: "50%",
      display: "flex", alignItems: "center", justifyContent: "center", color: "var(--color-red)",
    }}>
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
    </div>
    <h3 style={{ fontSize: 17, marginBottom: 6 }}>Something went wrong</h3>
    <p className="text-sm muted" style={{ maxWidth: 360, margin: "0 auto" }}>{message}</p>
    {onRetry && (
      <button onClick={onRetry} className="btn btn-outline" style={{ marginTop: 16 }}>Try again</button>
    )}
  </div>
);

export const LoadingBlock: React.FC<{ height?: number }> = ({ height = 200 }) => (
  <div className="skeleton" style={{ height, borderRadius: 12 }} />
);