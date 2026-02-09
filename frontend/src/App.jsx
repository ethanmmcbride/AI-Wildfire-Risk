import { useEffect, useMemo, useState } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";

const API_BASE = import.meta.env.VITE_API_BASE_URL;

export default function App() {
  const [fires, setFires] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  const center = useMemo(() => {
  if (!fires.length) return [33.88, -117.88];
  return [fires[0].lat, fires[0].lon];
}, [fires]);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        setErr("");

        const res = await fetch(`${API_BASE}/fires`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        setFires(data);
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
                  <TileLayer
                  attribution='&copy; OpenStreetMap contributors'
                  url="https://{s}.tile.openstreetmap.org/%7Bz%7D/%7Bx%7D/%7By%7D.png"
                  />

                    {fires.map((f, idx) => {
                      const frp = Number(f.frp ?? 0);
                      const radius = Math.min(12, 3 + frp / 10);

                      return (
                        <CircleMarker
                        key={idx}
                        center={[f.lat, f.lon]}
                        radius={radius}
                        pathOptions={{}}
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
                      
