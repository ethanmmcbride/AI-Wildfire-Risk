import { useEffect, useMemo, useState } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import { useMap } from "react-leaflet";
import L from "leaflet";

const API_BASE = import.meta.env.VITE_API_BASE_URL;

const US_BOUNDS = L.latLngBounds([[24, -125], [50, -66]]);
const US_CENTER = [39.8283, -98.5795];

function FitBounds({ fires }) {
  const map = useMap();

  useEffect(() => {
    if (fires.length === 0) {
      map.setView(US_CENTER, 5);
      return;
    }

    const bounds = L.latLngBounds(
      fires
        .map(f => [Number(f.lat), Number(f.lon)])
        .filter(coord => Number.isFinite(coord[0]) && Number.isFinite(coord[1]))
    );

    if (!bounds.isValid()) {
      map.setView(US_CENTER, 5);
      return;
    }

    map.fitBounds(bounds, { padding: [50, 50], maxZoom: 8 });

    const center = map.getCenter();
    if (!US_BOUNDS.contains(center)) {
      map.setView(US_CENTER, Math.max(map.getZoom(), 4));
    }

    if (map.getZoom() < 4) {
      map.setZoom(4);
    }
  }, [fires, map]);

  return null;
}

export default function App() {
  const [fires, setFires] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  const center = useMemo(() => {
    return [39.8283, -98.5795]; // continental US center
  }, []);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        setErr("");

        const res = await fetch(`${API_BASE}/fires`);
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
  }, []);
      
  return (
      <div style={{ height: "100vh", display: "flex", flexDirection: "column" }}>
        <header style={{ padding: "10px 14px", borderBottom: "1px solid #222" }}>
          <div style={{ display: "flex", gap: 12, alignItems: "baseline"}}>
            <h2 style={{ margin: 0}}>AI Wildfire Tracker</h2>
            <span style={{opacity: 0.8}}>
              {loading ? "Loading..." : `${fires.length} points`}
              </span>
              </div>
                {err && (
                  <div style={{ marginTop: 6, color: "salmon" }}>
                    Error: {err} — check VITE_API_BASE_URL and that your API is running.
                  </div>
             )}
             </header>

              <div style={{ flex: 1 }}>
                <MapContainer
                  center={center}
                  zoom={5}
                  minZoom={4}
                  maxBounds={[[24, -125], [50, -66]]}
                  maxBoundsViscosity={0.8}
                  style={{ height: "100%", width: "100%" }}
                >
                  <FitBounds fires={fires} />
                  <TileLayer
                    attribution='&copy; OpenStreetMap contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  />

                    {fires.map((f, idx) => {
                      const frp = Number(f.frp ?? 0);
                      const radius = Math.min(12, 3 + frp / 10);
                      
                      const b = Number(f.brightness ?? 0);
                      const color = b > 350 ? "red" : b > 320 ? "orange" : "yellow";

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
                      
