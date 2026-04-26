import { useEffect, useMemo, useState } from "react";
import "leaflet.markercluster/dist/MarkerCluster.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";
import "./index.css";

import StatsBar from "./components/StatsBar";
import FiltersPanel from "./components/FiltersPanel";
import MapView from "./components/MapView";
import EventsList from "./components/EventsList";
import {
  normalizeConfidence,
  getRiskScore,
  getSeverity,
  getConfidenceRank,
  buildFireId,
} from "./components/fireUtils";

const API_BASE = import.meta.env.VITE_API_BASE_URL;

export default function App() {
  const [fires, setFires] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [confidenceFilter, setConfidenceFilter] = useState("all");
  const [region, setRegion] = useState("ca");
  const [minBrightness, setMinBrightness] = useState("0");
  const [minFrp, setMinFrp] = useState("0");
  const [sortKey, setSortKey] = useState("brightness");
  const [sortDir, setSortDir] = useState("desc");
  const [selectedEventId, setSelectedEventId] = useState(null);
  const [showHeatmap, setShowHeatmap] = useState(true);
  const [showClusters, setShowClusters] = useState(true);

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

  const isStale = useMemo(() => {
    if (preparedFires.length === 0) return false;
    const dates = preparedFires
      .map((f) => f.acq_date)
      .filter(Boolean)
      .map((d) => new Date(d));
    const mostRecent = new Date(Math.max(...dates));
    const daysDiff = (Date.now() - mostRecent) / (1000 * 60 * 60 * 24);
    return daysDiff > 7;
  }, [preparedFires]);

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

  useEffect(() => {
    const controller = new AbortController();

    async function load() {
      try {
        setLoading(true);
        setErr("");

        const apiBase = `${API_BASE || "/api"}`.replace(/\/$/, "");
        const url = new URL(`${apiBase}/fires`, window.location.origin);
        if (region && region !== "us") url.searchParams.set("region", region);
        const res = await fetch(url.toString(), { signal: controller.signal });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (controller.signal.aborted) return;
        setFires(data.slice(0, 1000));
      } catch (e) {
        if (controller.signal.aborted) return;
        setErr(String(e));
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }
    load();

    return () => {
      controller.abort();
    };
  }, [region]);

  return (
    <div className="ui-shell">
      <header className="app-header">
        <div className="header-title-row">
          <h2>AI Wildfire Tracker</h2>
          <span>
            {loading ? "Loading..." : `${filteredFires.length} points (of ${preparedFires.length} total)`}
          </span>
        </div>
        {!loading && preparedFires.length > 0 && <StatsBar fires={preparedFires} />}
      </header>
      {isStale && (
        <div data-testid="stale-data-banner" className="stale-banner">
          Stale data — fire records are more than 7 days old.
        </div>
      )}

      <div className="main-layout">
        <FiltersPanel
          region={region}
          onRegionChange={setRegion}
          confidenceFilter={confidenceFilter}
          onConfidenceChange={setConfidenceFilter}
          minBrightness={minBrightness}
          onMinBrightnessChange={setMinBrightness}
          minFrp={minFrp}
          onMinFrpChange={setMinFrp}
          showHeatmap={showHeatmap}
          onHeatmapToggle={setShowHeatmap}
          showClusters={showClusters}
          onClustersToggle={setShowClusters}
        />

        <MapView
          fires={preparedFires}
          filteredFires={filteredFires}
          sortedFires={sortedFires}
          selectedFire={selectedFire}
          selectedEventId={selectedEventId}
          onSelectEvent={setSelectedEventId}
          showHeatmap={showHeatmap}
          showClusters={showClusters}
          loading={loading}
          err={err}
        />

        <EventsList
          sortedFires={sortedFires}
          selectedEventId={selectedEventId}
          onSelectEvent={setSelectedEventId}
          sortKey={sortKey}
          onSortKeyChange={setSortKey}
          sortDir={sortDir}
          onSortDirToggle={() => setSortDir((current) => (current === "asc" ? "desc" : "asc"))}
        />
      </div>
    </div>
  );
}
