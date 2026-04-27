export default function StatsBar({ fires, modelLoaded }) {
  if (!fires || fires.length === 0) return null;

  const critical = fires.filter((f) => f.severity === "critical").length;
  const warning = fires.filter((f) => f.severity === "warning").length;
  const monitor = fires.filter((f) => f.severity === "monitor").length;
  const maxRisk = Math.max(...fires.map((f) => f.risk));
  const latestDate = [...new Set(fires.map((f) => f.acq_date))].sort().pop() ?? "N/A";

  return (
    <div className="stats-bar">
      <div className="stat-item">
        <span className="stat-value stat-critical">{critical}</span>
        <span className="stat-label">Critical</span>
      </div>
      <div className="stat-item">
        <span className="stat-value stat-warning">{warning}</span>
        <span className="stat-label">Warning</span>
      </div>
      <div className="stat-item">
        <span className="stat-value stat-monitor">{monitor}</span>
        <span className="stat-label">Monitor</span>
      </div>
      <div className="stat-divider" />
      <div className="stat-item">
        <span className="stat-value">{maxRisk.toFixed(4)}</span>
        <span className="stat-label">Max Risk</span>
      </div>
      <div className="stat-item">
        <span className="stat-value">{latestDate}</span>
        <span className="stat-label">Latest Data</span>
      </div>
      <div className="stat-divider" />
      <div className="stat-item">
        <span
          className={`stat-value ${modelLoaded ? "stat-model-active" : "stat-model-fallback"}`}
          data-testid="model-status"
        >
          {modelLoaded === null ? "..." : modelLoaded ? "AI Model" : "Fallback"}
        </span>
        <span className="stat-label">Risk Source</span>
      </div>
    </div>
  );
}
