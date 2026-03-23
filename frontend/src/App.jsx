import { useEffect, useMemo, useState } from "react";
import { CircleMarker, MapContainer, Popup, TileLayer, useMap } from "react-leaflet";
import L from "leaflet";
import "./index.css";

const API_BASE = import.meta.env.VITE_API_BASE_URL;
const US_BOUNDS = L.latLngBounds([[24, -125], [50, -66]]);
const US_CENTER = [39.8283, -98.5795];
const CONFIDENCE_OPTIONS = ["all", "high", "nominal", "low"];

const STATE_CODES = [
  "us",
  "al", "ak", "az", "ar", "ca", "co", "ct", "de", "fl", "ga",
  "hi", "id", "il", "in", "ia", "ks", "ky", "la", "me", "md",
  "ma", "mi", "mn", "ms", "mo", "mt", "ne", "nv", "nh", "nj",
  "nm", "ny", "nc", "nd", "oh", "ok", "or", "pa", "ri", "sc",
  "sd", "tn", "tx", "ut", "vt", "va", "wa", "wv", "wi", "wy",
];

const STATE_LABELS = {
  us: "US (All States)",
  al: "Alabama",
  ak: "Alaska",
  az: "Arizona",
  ar: "Arkansas",
  ca: "California",
  co: "Colorado",
  ct: "Connecticut",
  de: "Delaware",
  fl: "Florida",
  ga: "Georgia",
  hi: "Hawaii",
  id: "Idaho",
  il: "Illinois",
  in: "Indiana",
  ia: "Iowa",
  ks: "Kansas",
  ky: "Kentucky",
  la: "Louisiana",
  me: "Maine",
  md: "Maryland",
  ma: "Massachusetts",
  mi: "Michigan",
  mn: "Minnesota",
  ms: "Mississippi",
  mo: "Missouri",
  mt: "Montana",
  ne: "Nebraska",
  nv: "Nevada",
  nh: "New Hampshire",
  nj: "New Jersey",
  nm: "New Mexico",
  ny: "New York",
  nc: "North Carolina",
  nd: "North Dakota",
  oh: "Ohio",
  ok: "Oklahoma",
  or: "Oregon",
  pa: "Pennsylvania",
  ri: "Rhode Island",
  sc: "South Carolina",
  sd: "South Dakota",
  tn: "Tennessee",
  tx: "Texas",
  ut: "Utah",
  vt: "Vermont",
  va: "Virginia",
  wa: "Washington",
  wv: "West Virginia",
  wi: "Wisconsin",
  wy: "Wyoming",
};

const STATE_CENTERS = {
  us: { center: [39.8283, -98.5795], zoom: 4 },
  al: { center: [32.8, -86.8], zoom: 7 },
  ak: { center: [64.0, -153.0], zoom: 4 },
  az: { center: [34.2, -111.4], zoom: 7 },
  ar: { center: [34.7, -92.3], zoom: 7 },
  ca: { center: [37.0, -120.0], zoom: 6 },
  co: { center: [39.0, -105.5], zoom: 7 },
  ct: { center: [41.6, -72.7], zoom: 8 },
  de: { center: [39.0, -75.4], zoom: 8 },
  fl: { center: [27.6, -83.8], zoom: 7 },
  ga: { center: [32.8, -83.6], zoom: 7 },
  hi: { center: [20.8, -157.4], zoom: 7 },
  id: { center: [45.5, -114.0], zoom: 6 },
  il: { center: [40.0, -89.2], zoom: 7 },
  in: { center: [40.0, -86.0], zoom: 7 },
  ia: { center: [42.0, -93.1], zoom: 7 },
  ks: { center: [38.5, -98.0], zoom: 7 },
  ky: { center: [37.8, -85.7], zoom: 7 },
  la: { center: [31.0, -91.8], zoom: 7 },
  me: { center: [45.2, -69.0], zoom: 7 },
  md: { center: [38.8, -76.8], zoom: 8 },
  ma: { center: [42.2, -71.8], zoom: 8 },
  mi: { center: [45.0, -86.0], zoom: 6 },
  mn: { center: [45.7, -93.9], zoom: 7 },
  ms: { center: [32.7, -89.6], zoom: 7 },
  mo: { center: [38.5, -92.3], zoom: 7 },
  mt: { center: [47.0, -110.0], zoom: 6 },
  ne: { center: [41.5, -99.8], zoom: 7 },
  nv: { center: [38.8, -117.0], zoom: 6 },
  nh: { center: [43.5, -71.6], zoom: 8 },
  nj: { center: [40.2, -74.5], zoom: 8 },
  nm: { center: [34.5, -106.2], zoom: 7 },
  ny: { center: [42.7, -75.6], zoom: 7 },
  nc: { center: [35.6, -79.8], zoom: 7 },
  nd: { center: [47.0, -100.5], zoom: 7 },
  oh: { center: [40.4, -82.6], zoom: 7 },
  ok: { center: [35.6, -98.5], zoom: 7 },
  or: { center: [43.8, -120.5], zoom: 6 },
  pa: { center: [40.6, -77.2], zoom: 7 },
  ri: { center: [41.7, -71.5], zoom: 8 },
  sc: { center: [33.9, -81.0], zoom: 7 },
  sd: { center: [44.5, -100.0], zoom: 7 },
  tn: { center: [35.8, -86.0], zoom: 7 },
  tx: { center: [31.0, -99.9], zoom: 6 },
  ut: { center: [39.3, -111.9], zoom: 7 },
  vt: { center: [44.0, -72.6], zoom: 8 },
  va: { center: [37.8, -78.2], zoom: 7 },
  wa: { center: [47.7, -121.5], zoom: 6 },
  wv: { center: [38.9, -80.8], zoom: 7 },
  wi: { center: [44.5, -89.5], zoom: 7 },
  wy: { center: [43.0, -107.3], zoom: 6 },
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

function FitBounds({ fires }) {
  const map = useMap();

  useEffect(() => {
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
    if (typeof map.getCenter === "function" && typeof US_BOUNDS.contains === "function") {
      const center = map.getCenter();
      if (!US_BOUNDS.contains(center)) {
        const nextZoom = typeof map.getZoom === "function" ? Math.max(map.getZoom(), 4) : 5;
        map.setView(US_CENTER, nextZoom);
      }
    }
    if (typeof map.getZoom === "function" && typeof map.setZoom === "function" && map.getZoom() < 4) {
      map.setZoom(4);
    }
  }, [fires, map]);

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

function FocusOnSelectedState({ state }) {
  const map = useMap();

  useEffect(() => {
    if (!state || !STATE_CENTERS[state]) return;
    const stateConfig = STATE_CENTERS[state];
    map.setView(stateConfig.center, stateConfig.zoom, { animate: true });
  }, [state, map]);

  return null;
}

export default function App() {
  const [fires, setFires] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [confidenceFilter, setConfidenceFilter] = useState("all");
  const [selectedState, setSelectedState] = useState("ca");
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

  const center = useMemo(() => {
    if (filteredFires.length === 0) return US_CENTER;
    return [filteredFires[0].lat, filteredFires[0].lon];
  }, [filteredFires]);

  useEffect(() => {
    const controller = new AbortController();

    async function load() {
      try {
        setLoading(true);
        setErr("");

        const apiBase = `${API_BASE || "/api"}`.replace(/\/$/, "");
        const url = new URL(`${apiBase}/fires`, window.location.origin);
        url.searchParams.set("region", selectedState);
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

      </header>

      <div className="main-layout">
        <section className="controls-panel">
          <h3>Filters</h3>
          <label>
            Region
            <select
              data-testid="state-select"
              value={selectedState}
              onChange={(e) => setSelectedState(e.target.value)}
            >
              {STATE_CODES.map((code) => (
                <option key={code} value={code}>
                  {STATE_LABELS[code]}
                </option>
              ))}
            </select>
            <small>Select a state to filter fire data.</small>
          </label>
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
          {err ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', backgroundColor: '#1e293b', color: '#f87171', padding: '40px', textAlign: 'center', borderRadius: '8px' }}>
              <h2 style={{ fontSize: '24px', marginBottom: '10px' }}>⚠️ AI Tracking System Offline</h2>
              <p style={{ color: '#cbd5e1', marginBottom: '20px' }}>
                We are currently unable to connect to the wildfire database. Please ensure the backend API is actively running.
              </p>
              <p style={{ fontSize: '12px', color: '#64748b' }}>Developer Details: {err}</p>
            </div>
          ) : (
            <>
              {filteredFires.length === 0 && !loading && <div className="overlay-note">No events match filters.</div>}
              <MapContainer
                center={center}
                zoom={5}
                minZoom={4}
                maxBounds={[[24, -125], [50, -66]]}
                maxBoundsViscosity={0.8}
                className="map-container"
              >
                <FocusOnSelectedState state={selectedState} />
                <FitBounds fires={filteredFires} />
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
                          <div><b>Severity:</b> {fire.severity}</div>
                          <div><b>Risk:</b> {fire.risk.toFixed(2)}</div>
                          <div><b>Lat/Lon:</b> {fire.lat.toFixed(3)}, {fire.lon.toFixed(3)}</div>
                          <div><b>Brightness:</b> {fire.brightness}</div>
                          <div><b>FRP:</b> {fire.frp}</div>
                          <div><b>Confidence:</b> {fire.confidence}</div>
                          <div><b>Time:</b> {fire.acq_date ?? "N/A"} {fire.acq_time ?? ""}</div>
                        </div>
                      </Popup>
                    </CircleMarker>
                  );
                })}
              </MapContainer>
            </>
          )}
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
