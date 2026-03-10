import { useEffect, useMemo, useState } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from "react-leaflet";
import L from "leaflet";

const API_BASE = import.meta.env.VITE_API_BASE_URL;

function FitBounds({ fires }) {
  const map = useMap();

  useEffect(() => {
    if (fires.length === 0) return;
    const bounds = L.latLngBounds(fires.map((f) => [f.lat, f.lon]));
    map.fitBounds(bounds, { padding: [50, 50] });
  }, [fires, map]);

  return null;
}

function getRiskColor(risk) {
  if (risk >= 220) return "red";
  if (risk >= 170) return "orange";
  return "yellow";
}

export default function App() {
  const [fires, setFires] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [confidence, setConfidence] = useState("all");

  const center = useMemo(() => {
  if (fires.length === 0) return [33.88, -117.88];
  return [Number(fires[0].lat), Number(fires[0].lon)];
}, [fires]);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        setErr("");

        const query =
          confidence !== "all" ? `?confidence=${encodeURIComponent(confidence)}` : "";

        const res = await fetch(`${API_BASE}/fires${query}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        const data = await res.json();
        setFires(data.slice(0, 1000));
      } catch (e) {
        setErr(String(e));
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [confidence]);

  const summary = useMemo(() => {
    const counts = { high: 0, medium: 0, low: 0, other: 0 };

    for (const fire of fires) {
      const c = String(fire.confidence || "").toLowerCase();
      if (c === "high") counts.high += 1;
      else if (c === "medium" || c === "nominal") counts.medium += 1;
      else if (c === "low") counts.low += 1;
      else counts.other += 1;
    }

    return counts;
  }, [fires]);
      
  return (
    <div style={{ height: "100vh", display: "flex", flexDirection: "column" }}>
      <header style={{ padding: "10px 14px", borderBottom: "1px solid #222" }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
          <div>
            <h2 style={{ margin: 0 }}>AI Wildfire Tracker</h2>
            <div style={{ opacity: 0.8, marginTop: 4 }}>
              {loading ? "Loading..." : `${fires.length} points`}
            </div>
            {!loading && (
              <div style={{ fontSize: 13, marginTop: 4 }}>
                High: {summary.high} | Medium: {summary.medium} | Low: {summary.low}
              </div>
            )}
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <label htmlFor="confidence-filter">Confidence:</label>
            <select
              id="confidence-filter"
              value={confidence}
              onChange={(e) => setConfidence(e.target.value)}
            >
              <option value="all">All</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
        </div>

        {err && (
          <div style={{ marginTop: 6, color: "salmon" }}>
            Error: {err} — check VITE_API_BASE_URL and that your API is running.
          </div>
        )}
      </header>

      <div style={{ position: "relative", flex: 1 }}>
        <div
          style={{
            position: "absolute",
            zIndex: 1000,
            right: 12,
            top: 12,
            background: "white",
            padding: "10px 12px",
            borderRadius: 8,
            boxShadow: "0 2px 8px rgba(0,0,0,0.2)",
            fontSize: 13,
            lineHeight: 1.5,
          }}
        >
          <div style={{ fontWeight: "bold", marginBottom: 6 }}>Risk Legend</div>
          <div>🔴 High risk (220+)</div>
          <div>🟠 Medium risk (170–219)</div>
          <div>🟡 Lower risk (&lt;170)</div>
        </div>

        <MapContainer center={center} zoom={5} style={{ height: "100%", width: "100%" }}>
          <FitBounds fires={fires} />
          <TileLayer
            attribution="&copy; OpenStreetMap contributors"
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {fires.map((f, idx) => {
            const frp = Number(f.frp ?? 0);
            const risk = Number(f.risk ?? 0);
            const radius = Math.min(12, 3 + frp / 10);
            const color = getRiskColor(risk);

            return (
              <CircleMarker
                key={idx}
                center={[f.lat, f.lon]}
                radius={radius}
                pathOptions={{ color }}
              >
                <Popup>
                  <div style={{ fontSize: 13 }}>
                    <div><b>Lat/Lon:</b> {f.lat}, {f.lon}</div>
                    <div><b>Brightness:</b> {f.brightness}</div>
                    <div><b>FRP:</b> {f.frp}</div>
                    <div><b>Confidence:</b> {f.confidence}</div>
                    <div><b>Risk:</b> {f.risk}</div>
                  </div>
                </Popup>
              </CircleMarker>
            );
          })}
        </MapContainer>
      </div>
    </div>
  );
}