import { useEffect, useMemo, useState } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import { useMap } from "react-leaflet";
import L from "leaflet";

const API_BASE = import.meta.env.VITE_API_BASE_URL;

function FitBounds({ fires }) {
  const map = useMap();

  useEffect(() => {
    if (fires.length === 0) return;

    const bounds = L.latLngBounds(
      fires.map(f => [f.lat, f.lon])
    );

    map.fitBounds(bounds, { padding: [50, 50] });
  }, [fires]);

  return null;
}

export default function App() {
  const [fires, setFires] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  const center = useMemo(() => {
  if (fires.length === 0) return [33.88, -117.88];
  return [Number(fires[0].lat), Number(fires[0].lon)];
}, [fires]);

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
                <MapContainer center={center} zoom={5} style={{ height: "100%", width: "100%" }}>
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
                      
