import L from "leaflet";

export const US_BOUNDS = L.latLngBounds([[24, -125], [50, -66]]);
export const US_CENTER = [39.8283, -98.5795];

export const CONFIDENCE_OPTIONS = ["all", "high", "nominal", "low"];

export const REGION_OPTIONS = [
  { value: "us", label: "All US" },
  { value: "ca", label: "California" },
  { value: "fl", label: "Florida" },
  { value: "ga", label: "Georgia" },
  { value: "tx", label: "Texas" },
  { value: "or", label: "Oregon" },
  { value: "wa", label: "Washington" },
  { value: "az", label: "Arizona" },
  { value: "co", label: "Colorado" },
];

export function normalizeConfidence(confidence) {
  const normalized = String(confidence ?? "").trim().toLowerCase();
  if (["h", "high"].includes(normalized)) return "high";
  if (["l", "low"].includes(normalized)) return "low";
  if (["n", "nominal", "medium", "med"].includes(normalized)) return "nominal";
  return normalized || "unknown";
}

export function getRiskScore(fire) {
  if (fire.risk !== undefined && fire.risk !== null && !Number.isNaN(Number(fire.risk))) {
    return Number(fire.risk);
  }
  const b = Number(fire.brightness ?? 0);
  const f = Number(fire.frp ?? 0);
  return Number(Math.min((b * 0.6 + f * 0.4) / 350, 1.0).toFixed(4));
}

export function getSeverity(fire) {
  const b = Number(fire.brightness ?? 0);
  const f = Number(fire.frp ?? 0);
  if (b >= 350 || f >= 50) return "critical";
  if (b >= 320 || f >= 20) return "warning";
  return "monitor";
}

export function getMarkerColor(fire) {
  const b = Number(fire.brightness ?? 0);
  if (b >= 350) return "#d7263d";
  if (b >= 320) return "#f08c00";
  return "#ffd43b";
}

export function getMarkerRadius(fire) {
  const frp = Number(fire.frp ?? 0);
  return Math.min(12, 3 + frp / 10);
}

export function getConfidenceRank(confidence) {
  const normalized = String(confidence ?? "").toLowerCase();
  if (normalized === "high") return 3;
  if (normalized === "nominal" || normalized === "medium") return 2;
  if (normalized === "low") return 1;
  return 0;
}

export function buildFireId(fire, index) {
  return [
    fire.lat ?? fire.latitude ?? "na",
    fire.lon ?? fire.longitude ?? "na",
    fire.acq_date ?? "na",
    fire.acq_time ?? "na",
    fire.brightness ?? "na",
    fire.frp ?? "na",
    index,
  ].join("|");
}
