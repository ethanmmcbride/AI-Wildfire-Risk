import { useEffect, useMemo, useState } from "react";
import { CircleMarker, MapContainer, Popup, TileLayer, useMap } from "react-leaflet";
import L from "leaflet";
import "./index.css";

const API_BASE = import.meta.env.VITE_API_BASE_URL;
const US_BOUNDS = L.latLngBounds([[24, -125], [50, -66]]);
const US_CENTER = [39.8283, -98.5795];
const CONFIDENCE_OPTIONS = ["all", "high", "nominal", "low"];

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

function isStaleFireData(events, staleDays = 2) {
  if (!events || events.length === 0) return false;

  const newestDate = events
    .map((event) => {
      const time = String(event.acq_time ?? "0000").padStart(4, "0");
      return new Date(`${event.acq_date}T${time.slice(0, 2)}:${time.slice(2, 4)}:00`);
    })
    .filter((date) => !Number.isNaN(date.getTime()))
    .sort((a, b) => b - a)[0];

  if (!newestDate) return false;

  const ageMs = Date.now() - newestDate.getTime();
  const staleMs = staleDays * 24 * 60 * 60 * 1000;

  return ageMs > staleMs;
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

export default function App() {
  const [fires, setFires] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [confidenceFilter, setConfidenceFilter] = useState("all");
  const [californiaOnly, setCaliforniaOnly] = useState(true);
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

  const showStaleBanner = isStaleFireData(preparedFires);

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
        if (californiaOnly) url.searchParams.set("region", "ca");
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
  }, [californiaOnly]);

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

      {showStaleBanner && !loading && !err && (
        <div className="stale-data-banner" data-testid="stale-data-banner">
          Wildfire data may be stale. Latest fire record is older than 2 days.
        </div>
      )}

      <div className="main-layout">
        <section className="controls-panel">
          <h3>Filters</h3>
          <div>
            <span>Region</span>
            <label htmlFor="ca-toggle" className="checkbox-row" data-testid="ca-toggle-label">
              <input
                id="ca-toggle"
                data-testid="ca-toggle"
                type="checkbox"
                checked={californiaOnly}
                onChange={(e) => setCaliforniaOnly(e.target.checked)}
              />
              California only
            </label>
            <small>Data shown is US-only; toggle narrows to California.</small>
          </div>
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
