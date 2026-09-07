// Format helpers used across the UI.
export function formatCurrency(value: number, currency = "USD"): string {
  try {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency,
      maximumFractionDigits: 0,
    }).format(value);
  } catch {
    return `${currency} ${value.toLocaleString()}`;
  }
}

export function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US").format(value);
}

export function formatMileage(km: number): string {
  return `${formatNumber(km)} km`;
}

export function formatDate(input?: string | Date | null): string {
  if (!input) return "";
  const d = typeof input === "string" ? new Date(input) : input;
  return d.toLocaleDateString("en-US", { day: "2-digit", month: "short", year: "numeric" });
}

export function formatDateTime(input?: string | Date | null): string {
  if (!input) return "";
  const d = typeof input === "string" ? new Date(input) : input;
  return d.toLocaleString("en-US", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

export function timeAgo(input?: string | Date | null): string {
  if (!input) return "";
  const d = typeof input === "string" ? new Date(input) : input;
  const diff = (Date.now() - d.getTime()) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)} min ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} h ago`;
  if (diff < 604800) return `${Math.floor(diff / 86400)} d ago`;
  return formatDate(d);
}

export function fuelLabel(s?: string | null): string {
  if (!s) return "";
  return s.replace(/_/g, " ").toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
}

export function statusLabel(s: string): string {
  return s.replace(/_/g, " ").toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
}