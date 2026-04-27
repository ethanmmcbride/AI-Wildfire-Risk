import { CONFIDENCE_OPTIONS, REGION_OPTIONS } from "./fireUtils";

export default function FiltersPanel({
  region,
  onRegionChange,
  confidenceFilter,
  onConfidenceChange,
  minBrightness,
  onMinBrightnessChange,
  minFrp,
  onMinFrpChange,
  showHeatmap,
  onHeatmapToggle,
  showClusters,
  onClustersToggle,
}) {
  return (
    <section className="controls-panel">
      <h3>Filters</h3>
      <label>
        Region
        <select
          data-testid="region-filter"
          value={region}
          onChange={(e) => onRegionChange(e.target.value)}
        >
          {REGION_OPTIONS.map((r) => (
            <option key={r.value} value={r.value}>
              {r.label}
            </option>
          ))}
        </select>
      </label>
      <label>
        Confidence
        <select
          data-testid="confidence-filter"
          value={confidenceFilter}
          onChange={(e) => onConfidenceChange(e.target.value)}
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
          onChange={(e) => onMinBrightnessChange(e.target.value)}
        />
      </label>
      <label>
        Min FRP
        <input
          data-testid="frp-filter"
          type="number"
          value={minFrp}
          onChange={(e) => onMinFrpChange(e.target.value)}
        />
      </label>

      <h3>Map Layers</h3>
      <label htmlFor="heatmap-toggle" className="checkbox-row">
        <input
          id="heatmap-toggle"
          data-testid="heatmap-toggle"
          type="checkbox"
          checked={showHeatmap}
          onChange={(e) => onHeatmapToggle(e.target.checked)}
        />
        Risk heatmap
      </label>
      <small>Heatmap weighted by AI risk score (blue → orange → red).</small>
      <label htmlFor="cluster-toggle" className="checkbox-row" style={{ marginTop: 8 }}>
        <input
          id="cluster-toggle"
          data-testid="cluster-toggle"
          type="checkbox"
          checked={showClusters}
          onChange={(e) => onClustersToggle(e.target.checked)}
        />
        Marker clustering
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
  );
}
