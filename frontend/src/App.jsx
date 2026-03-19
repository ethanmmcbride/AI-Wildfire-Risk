import { useEffect, useMemo, useState } from "react";
import { CircleMarker, MapContainer, Popup, TileLayer, useMap } from "react-leaflet";
import L from "leaflet";
import "./index.css";

const API_BASE = import.meta.env.VITE_API_BASE_URL;
const US_BOUNDS = L.latLngBounds([[24, -125], [50, -66]]);
const US_CENTER = [39, -100];
const CONFIDENCE_OPTIONS = ["all", "high", "nominal", "low"];
const STATE_OPTIONS = [
  { value: "all", label: "All states" },
  { value: "al", label: "Alabama" },
  { value: "ak", label: "Alaska" },
  { value: "ar", label: "Arkansas" },
  { value: "az", label: "Arizona" },
  { value: "co", label: "Colorado" },
  { value: "ct", label: "Connecticut" },
  { value: "de", label: "Delaware" },
  { value: "fl", label: "Florida" },
  { value: "ga", label: "Georgia" },
  { value: "hi", label: "Hawaii" },
  { value: "id", label: "Idaho" },
  { value: "il", label: "Illinois" },
  { value: "in", label: "Indiana" },
  { value: "ia", label: "Iowa" },
  { value: "ks", label: "Kansas" },
  { value: "ky", label: "Kentucky" },
  { value: "la", label: "Louisiana" },
  { value: "me", label: "Maine" },
  { value: "md", label: "Maryland" },
  { value: "ma", label: "Massachusetts" },
  { value: "mi", label: "Michigan" },
  { value: "mn", label: "Minnesota" },
  { value: "ms", label: "Mississippi" },
  { value: "mo", label: "Missouri" },
  { value: "mt", label: "Montana" },
  { value: "ne", label: "Nebraska" },
  { value: "nv", label: "Nevada" },
  { value: "nh", label: "New Hampshire" },
  { value: "nj", label: "New Jersey" },
  { value: "nm", label: "New Mexico" },
  { value: "ny", label: "New York" },
  { value: "nc", label: "North Carolina" },
  { value: "nd", label: "North Dakota" },
  { value: "oh", label: "Ohio" },
  { value: "ok", label: "Oklahoma" },
  { value: "or", label: "Oregon" },
  { value: "pa", label: "Pennsylvania" },
  { value: "ri", label: "Rhode Island" },
  { value: "sc", label: "South Carolina" },
  { value: "sd", label: "South Dakota" },
  { value: "tn", label: "Tennessee" },
  { value: "tx", label: "Texas" },
  { value: "ut", label: "Utah" },
  { value: "vt", label: "Vermont" },
  { value: "va", label: "Virginia" },
  { value: "wa", label: "Washington" },
  { value: "wv", label: "West Virginia" },
  { value: "wi", label: "Wisconsin" },
  { value: "wy", label: "Wyoming" },
];

const STATE_BOUNDS = {
  al: L.latLngBounds([[30.1, -88.5], [35.0, -84.8]]),
  ak: L.latLngBounds([[51.0, -179.0], [71.5, -129.9]]),
  ar: L.latLngBounds([[33.0, -94.6], [36.5, -89.6]]),
  az: L.latLngBounds([[31.3, -114.8], [37.0, -109.0]]),
  co: L.latLngBounds([[37.0, -109.1], [41.0, -102.0]]),
  ct: L.latLngBounds([[40.9, -73.7], [42.0, -71.8]]),
  de: L.latLngBounds([[38.4, -75.8], [39.8, -75.0]]),
  fl: L.latLngBounds([[24.5, -87.7], [31.0, -80.0]]),
  ga: L.latLngBounds([[30.3, -85.6], [35.0, -80.8]]),
  hi: L.latLngBounds([[18.8, -160.5], [22.5, -154.8]]),
  id: L.latLngBounds([[42.0, -117.2], [49.0, -111.0]]),
  il: L.latLngBounds([[36.9, -91.5], [42.5, -87.0]]),
  in: L.latLngBounds([[37.8, -88.1], [41.8, -84.8]]),
  ia: L.latLngBounds([[40.4, -96.6], [43.5, -90.1]]),
  ks: L.latLngBounds([[36.9, -102.1], [40.0, -94.6]]),
  ky: L.latLngBounds([[36.5, -89.6], [39.2, -81.9]]),
  la: L.latLngBounds([[29.0, -94.0], [33.0, -88.8]]),
  me: L.latLngBounds([[43.0, -71.1], [47.5, -66.9]]),
  md: L.latLngBounds([[37.9, -79.5], [39.7, -75.0]]),
  ma: L.latLngBounds([[41.2, -73.5], [42.9, -69.9]]),
  mi: L.latLngBounds([[41.7, -90.4], [48.3, -82.4]]),
  mn: L.latLngBounds([[43.5, -96.5], [49.4, -89.5]]),
  ms: L.latLngBounds([[30.2, -91.7], [35.0, -88.0]]),
  mo: L.latLngBounds([[35.9, -95.8], [40.6, -89.1]]),
  mt: L.latLngBounds([[44.4, -116.0], [49.0, -104.0]]),
  ne: L.latLngBounds([[40.0, -104.1], [43.0, -95.3]]),
  nv: L.latLngBounds([[35.0, -120.0], [42.0, -114.0]]),
  nh: L.latLngBounds([[42.7, -72.6], [45.3, -70.7]]),
  nj: L.latLngBounds([[38.9, -75.6], [41.4, -73.9]]),
  nm: L.latLngBounds([[31.3, -109.1], [37.0, -103.0]]),
  ny: L.latLngBounds([[40.5, -79.8], [45.0, -71.8]]),
  nc: L.latLngBounds([[33.8, -84.3], [36.6, -75.5]]),
  nd: L.latLngBounds([[45.9, -104.0], [49.0, -96.5]]),
  oh: L.latLngBounds([[38.4, -84.8], [41.9, -80.5]]),
  ok: L.latLngBounds([[33.6, -103.0], [37.0, -94.4]]),
  or: L.latLngBounds([[42.0, -124.8], [46.3, -116.5]]),
  pa: L.latLngBounds([[39.7, -80.5], [42.5, -74.7]]),
  ri: L.latLngBounds([[41.1, -71.9], [42.0, -71.1]]),
  sc: L.latLngBounds([[32.0, -83.4], [35.2, -78.4]]),
  sd: L.latLngBounds([[42.4, -104.1], [45.9, -96.4]]),
  tn: L.latLngBounds([[34.9, -90.3], [36.7, -81.7]]),
  tx: L.latLngBounds([[25.8, -106.6], [36.5, -93.5]]),
  ut: L.latLngBounds([[37.0, -114.1], [42.0, -109.0]]),
  vt: L.latLngBounds([[42.7, -73.4], [45.0, -71.4]]),
  va: L.latLngBounds([[36.5, -83.7], [39.5, -75.2]]),
  wa: L.latLngBounds([[45.5, -124.8], [49.0, -116.9]]),
  wv: L.latLngBounds([[37.2, -82.6], [40.6, -77.7]]),
  wi: L.latLngBounds([[42.5, -92.9], [47.3, -86.2]]),
  wy: L.latLngBounds([[40.9, -111.1], [45.0, -104.0]]),
};

function normalizeConfidence(confidence) {
  const normalized = String(confidence ?? "").trim().toLowerCase();
  if (["h", "high"].includes(normalized)) return "high";
  if (["l", "low"].includes(normalized)) return "low";
  if (["n", "nominal", "medium", "med"].includes(normalized)) return "nominal";
  return normalized || "unknown";
}

function getRiskScore(fire) {
  if (fire.risk !== undefined && fire.risk !== null && !Number.isNaN(Number(fire.risk))) {
    return Number(fire.risk);
  }
  const b = Number(fire.brightness ?? 0);
  const f = Number(fire.frp ?? 0);
  return Number(((b * 0.6) + (f * 0.4)).toFixed(2));
}

function getSeverity(fire) {
  const b = Number(fire.brightness ?? 0);
  const f = Number(fire.frp ?? 0);
  if (b >= 350 || f >= 50) return "critical";
  if (b >= 320 || f >= 20) return "warning";
  return "monitor";
}

function getMarkerColor(fire) {
  const b = Number(fire.brightness ?? 0);
  if (b >= 350) return "#d7263d";
  if (b >= 320) return "#f08c00";
  return "#ffd43b";
}

function getMarkerRadius(fire) {
  const frp = Number(fire.frp ?? 0);
  return Math.min(12, 3 + frp / 10);
}

function getConfidenceRank(confidence) {
  const normalized = String(confidence ?? "").toLowerCase();
  if (normalized === "high") return 3;
  if (normalized === "nominal" || normalized === "medium") return 2;
  if (normalized === "low") return 1;
  return 0;
}

function buildFireId(fire, index) {
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

function FitBounds({ fires, selectedState }) {
  const map = useMap();

  useEffect(() => {
    if (selectedState === "all") {
      map.setView(US_CENTER, 5);
      return;
    }
    if (selectedState && STATE_BOUNDS[selectedState]) {
      map.fitBounds(STATE_BOUNDS[selectedState], { padding: [50, 50] });
      return;
    }

    if (fires.length === 0) {
      map.setView(US_CENTER, 5);
      return;
    }
    if (fires.length === 1) {
      map.setView([fires[0].lat, fires[0].lon], 7, { animate: true });
      return;
    }

    const bounds = L.latLngBounds(
      fires
        .map((f) => [Number(f.lat), Number(f.lon)])
        .filter((coord) => Number.isFinite(coord[0]) && Number.isFinite(coord[1]))
    );

    if (typeof bounds.isValid === "function" && !bounds.isValid()) {
      map.setView(US_CENTER, 5);
      return;
    }

    map.fitBounds(bounds, { padding: [50, 50], maxZoom: 7 });
    if (typeof map.getZoom === "function" && typeof map.setZoom === "function" && map.getZoom() < 4) {
      map.setZoom(4);
    }
  }, [fires, selectedState, map]);

  return null;
}

function FocusOnSelectedFire({ fire }) {
  const map = useMap();

  useEffect(() => {
    if (!fire) return;
    map.setView([fire.lat, fire.lon], 8, { animate: true });
  }, [fire, map]);

  return null;
}

export default function App() {
  const [fires, setFires] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [confidenceFilter, setConfidenceFilter] = useState("all");
  const [selectedState, setSelectedState] = useState("all");
  const [minBrightness, setMinBrightness] = useState("0");
  const [minFrp, setMinFrp] = useState("0");
  const [sortKey, setSortKey] = useState("brightness");
  const [sortDir, setSortDir] = useState("desc");
  const [selectedEventId, setSelectedEventId] = useState(null);

  const parsedMinBrightness = useMemo(() => {
    const parsed = Number(minBrightness);
    return Number.isFinite(parsed) ? parsed : 0;
  }, [minBrightness]);

  const parsedMinFrp = useMemo(() => {
    const parsed = Number(minFrp);
    return Number.isFinite(parsed) ? parsed : 0;
  }, [minFrp]);

  const preparedFires = useMemo(
    () =>
      fires.map((f, idx) => ({
        ...f,
        lat: Number(f.lat),
        lon: Number(f.lon),
        brightness: Number(f.brightness ?? 0),
        frp: Number(f.frp ?? 0),
        confidence: normalizeConfidence(f.confidence),
        risk: getRiskScore(f),
        severity: getSeverity(f),
        id: buildFireId(f, idx),
      })),
    [fires]
  );

  const filteredFires = useMemo(
    () =>
      preparedFires.filter((f) => {
        const confidencePass = confidenceFilter === "all" || f.confidence === confidenceFilter;
        const brightnessPass = f.brightness >= parsedMinBrightness;
        const frpPass = f.frp >= parsedMinFrp;
        return confidencePass && brightnessPass && frpPass;
      }),
    [preparedFires, confidenceFilter, parsedMinBrightness, parsedMinFrp]
  );

  const sortedFires = useMemo(() => {
    const sorted = [...filteredFires];
    sorted.sort((a, b) => {
      let cmp = 0;
      if (sortKey === "confidence") cmp = getConfidenceRank(a.confidence) - getConfidenceRank(b.confidence);
      else cmp = Number(a[sortKey] ?? 0) - Number(b[sortKey] ?? 0);
      return sortDir === "asc" ? cmp : -cmp;
    });
    return sorted;
  }, [filteredFires, sortKey, sortDir]);

  const selectedFire = useMemo(
    () => sortedFires.find((f) => f.id === selectedEventId) ?? null,
    [sortedFires, selectedEventId]
  );

  useEffect(() => {
    if (selectedEventId && !filteredFires.some((f) => f.id === selectedEventId)) {
      setSelectedEventId(null);
    }
  }, [filteredFires, selectedEventId]);

  const center = useMemo(() => US_CENTER, []);

  useEffect(() => {
    const controller = new AbortController();

    async function load() {
      try {
        setLoading(true);
        setErr("");

        const apiBase = `${API_BASE || "/api"}`.replace(/\/$/, "");
        const url = new URL(`${apiBase}/fires`, window.location.origin);
        if (selectedState && selectedState !== "all") url.searchParams.set("region", selectedState);
        const res = await fetch(url.toString(), { signal: controller.signal });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (controller.signal.aborted) return;
        setFires(data.slice(0, 1000));
      } catch (e) {
        if (controller.signal.aborted) return;
        setErr(String(e));
      } finally {
        if (controller.signal.aborted) return;
        setLoading(false);
      }
    }
    load();

    return () => {
      controller.abort();
    };
  }, [selectedState]);

  return (
    <div className="ui-shell">
      <header className="app-header">
        <div className="header-title-row">
          <h2>AI Wildfire Tracker</h2>
          <span>
            {loading ? "Loading..." : `${filteredFires.length} points (of ${preparedFires.length} total)`}
          </span>
        </div>
        {err && (
          <div className="error-banner">
            Error: {err} — check VITE_API_BASE_URL and that your API is running.
          </div>
        )}
      </header>

      <div className="main-layout">
        <section className="controls-panel">
          <h3>Filters</h3>
          <label>
            State
            <select
              data-testid="state-select"
              value={selectedState}
              onChange={(e) => setSelectedState(e.target.value)}
            >
              {STATE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <small>Data shown is US-only; choose a state or show all states.</small>
          <label>
            Confidence
            <select
              data-testid="confidence-filter"
              value={confidenceFilter}
              onChange={(e) => setConfidenceFilter(e.target.value)}
            >
              {CONFIDENCE_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
          <label>
            Min brightness
            <input
              data-testid="brightness-filter"
              type="number"
              value={minBrightness}
              onChange={(e) => setMinBrightness(e.target.value)}
            />
          </label>
          <label>
            Min FRP
            <input
              data-testid="frp-filter"
              type="number"
              value={minFrp}
              onChange={(e) => setMinFrp(e.target.value)}
            />
          </label>

          <h3>Legend</h3>
          <ul className="legend" data-testid="legend">
            <li>
              <span className="legend-dot critical" /> Brightness {">="} 350: Critical
            </li>
            <li>
              <span className="legend-dot warning" /> Brightness 320-349: Warning
            </li>
            <li>
              <span className="legend-dot monitor" /> Brightness {"<"} 320: Monitor
            </li>
            <li>Marker radius scales with FRP (higher FRP = larger marker)</li>
          </ul>
        </section>

        <section className="map-panel">
          {filteredFires.length === 0 && !loading && <div className="overlay-note">No events match filters.</div>}
          <MapContainer
            center={center}
            zoom={5}
            minZoom={4}
            maxBounds={[[18, -179], [72, -66]]}
            maxBoundsViscosity={0.8}
            className="map-container"
          >
            <FitBounds fires={filteredFires} selectedState={selectedState} />
            <FocusOnSelectedFire fire={selectedFire} />
            <TileLayer
              attribution="&copy; OpenStreetMap contributors"
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            {sortedFires.map((fire) => {
              const selected = fire.id === selectedEventId;
              return (
                <CircleMarker
                  key={fire.id}
                  center={[fire.lat, fire.lon]}
                  radius={getMarkerRadius(fire)}
                  pathOptions={{
                    color: getMarkerColor(fire),
                    fillColor: getMarkerColor(fire),
                    fillOpacity: 0.75,
                    weight: selected ? 3 : 1,
                  }}
                  eventHandlers={{ click: () => setSelectedEventId(fire.id) }}
                >
                  <Popup>
                    <div className="popup-content">
                      <div>
                        <b>Severity:</b> {fire.severity}
                      </div>
                      <div>
                        <b>Risk:</b> {fire.risk.toFixed(2)}
                      </div>
                      <div>
                        <b>Lat/Lon:</b> {fire.lat.toFixed(3)}, {fire.lon.toFixed(3)}
                      </div>
                      <div>
                        <b>Brightness:</b> {fire.brightness}
                      </div>
                      <div>
                        <b>FRP:</b> {fire.frp}
                      </div>
                      <div>
                        <b>Confidence:</b> {fire.confidence}
                      </div>
                      <div>
                        <b>Time:</b> {fire.acq_date ?? "N/A"} {fire.acq_time ?? ""}
                      </div>
                    </div>
                  </Popup>
                </CircleMarker>
              );
            })}
          </MapContainer>
        </section>

        <aside className="events-panel">
          <h3>Events</h3>
          <div className="sort-controls">
            <label>
              Sort by
              <select data-testid="sort-key" value={sortKey} onChange={(e) => setSortKey(e.target.value)}>
                <option value="brightness">Brightness</option>
                <option value="frp">FRP</option>
                <option value="confidence">Confidence</option>
                <option value="risk">Risk</option>
              </select>
            </label>
            <button
              type="button"
              data-testid="sort-dir"
              onClick={() => setSortDir((current) => (current === "asc" ? "desc" : "asc"))}
            >
              {sortDir === "asc" ? "Ascending" : "Descending"}
            </button>
          </div>

          <div className="events-count" data-testid="events-count">
            {sortedFires.length} events
          </div>
          <ul className="events-list">
            {sortedFires.map((fire) => (
              <li key={fire.id}>
                <button
                  type="button"
                  className={`event-row ${selectedEventId === fire.id ? "selected" : ""}`}
                  data-testid="event-row"
                  onClick={() => setSelectedEventId(fire.id)}
                >
                  <div className="event-row-top">
                    <span className={`severity-pill ${fire.severity}`}>{fire.severity}</span>
                    <span>{fire.confidence}</span>
                  </div>
                  <div>Lat/Lon: {fire.lat.toFixed(2)}, {fire.lon.toFixed(2)}</div>
                  <div>
                    Brightness: {fire.brightness} | FRP: {fire.frp}
                  </div>
                  <div>Risk: {fire.risk.toFixed(2)}</div>
                </button>
              </li>
            ))}
          </ul>
        </aside>
      </div>
    </div>
  );
}
