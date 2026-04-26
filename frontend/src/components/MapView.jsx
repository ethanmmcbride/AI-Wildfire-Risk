import { useEffect, useRef } from "react";
import { CircleMarker, MapContainer, Popup, TileLayer, useMap } from "react-leaflet";
import MarkerClusterGroup from "react-leaflet-markercluster";
import L from "leaflet";
import "leaflet.heat";
import { US_BOUNDS, US_CENTER, getMarkerColor, getMarkerRadius } from "./fireUtils";

function HeatmapLayer({ fires }) {
  const map = useMap();
  const heatRef = useRef(null);

  useEffect(() => {
    if (heatRef.current) {
      map.removeLayer(heatRef.current);
      heatRef.current = null;
    }

    const maxRisk = Math.max(...fires.map((f) => f.risk), 1);
    const points = fires
      .filter((f) => f.risk > 0)
      .map((f) => [f.lat, f.lon, f.risk / maxRisk]);
    if (points.length === 0) return;

    heatRef.current = L.heatLayer(points, {
      radius: 25,
      blur: 20,
      max: 0.6,
      minOpacity: 0.15,
      maxZoom: 9,
      gradient: { 0.2: "#2b83ba", 0.4: "#abdda4", 0.6: "#ffffbf", 0.8: "#fdae61", 1.0: "#d7191c" },
    }).addTo(map);

    return () => {
      if (heatRef.current) {
        map.removeLayer(heatRef.current);
        heatRef.current = null;
      }
    };
  }, [fires, map]);

  return null;
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

function FireMarkers({ fires, selectedEventId, onSelectEvent }) {
  return fires.map((fire) => {
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
        eventHandlers={{ click: () => onSelectEvent(fire.id) }}
      >
        <Popup>
          <div className="popup-content">
            <div><b>Severity:</b> {fire.severity}</div>
            <div><b>Risk Score (AI):</b> {fire.risk.toFixed(4)}</div>
            <div><b>Lat/Lon:</b> {fire.lat.toFixed(3)}, {fire.lon.toFixed(3)}</div>
            <div><b>Brightness:</b> {fire.brightness}</div>
            <div><b>FRP:</b> {fire.frp}</div>
            <div><b>Confidence:</b> {fire.confidence}</div>
            <div><b>Time:</b> {fire.acq_date ?? "N/A"} {fire.acq_time ?? ""}</div>
          </div>
        </Popup>
      </CircleMarker>
    );
  });
}

export default function MapView({
  fires,
  filteredFires,
  sortedFires,
  selectedFire,
  selectedEventId,
  onSelectEvent,
  showHeatmap,
  showClusters,
  loading,
  err,
}) {
  const center = filteredFires.length > 0
    ? [filteredFires[0].lat, filteredFires[0].lon]
    : US_CENTER;

  if (err) {
    return (
      <section className="map-panel">
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%", backgroundColor: "#1e293b", color: "#f87171", padding: "40px", textAlign: "center", borderRadius: "8px" }}>
          <h2 style={{ fontSize: "24px", marginBottom: "10px" }}>AI Tracking System Offline</h2>
          <p style={{ color: "#cbd5e1", marginBottom: "20px" }}>
            We are currently unable to connect to the wildfire database. Please ensure the backend API is actively running.
          </p>
          <p style={{ fontSize: "12px", color: "#64748b" }}>Developer Details: {err}</p>
        </div>
      </section>
    );
  }

  return (
    <section className="map-panel">
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
        {showHeatmap && <HeatmapLayer fires={filteredFires} />}
        {showClusters ? (
          <MarkerClusterGroup
            chunkedLoading
            maxClusterRadius={40}
            spiderfyOnMaxZoom
            showCoverageOnHover={false}
            iconCreateFunction={(cluster) => {
              const count = cluster.getChildCount();
              let size = "small";
              if (count >= 100) size = "large";
              else if (count >= 10) size = "medium";
              return L.divIcon({
                html: `<span>${count}</span>`,
                className: `marker-cluster marker-cluster-${size}`,
                iconSize: L.point(40, 40),
              });
            }}
          >
            <FireMarkers fires={sortedFires} selectedEventId={selectedEventId} onSelectEvent={onSelectEvent} />
          </MarkerClusterGroup>
        ) : (
          <FireMarkers fires={sortedFires} selectedEventId={selectedEventId} onSelectEvent={onSelectEvent} />
        )}
      </MapContainer>
    </section>
  );
}
