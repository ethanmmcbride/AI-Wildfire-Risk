export default function EventsList({
  sortedFires,
  selectedEventId,
  onSelectEvent,
  sortKey,
  onSortKeyChange,
  sortDir,
  onSortDirToggle,
}) {
  return (
    <aside className="events-panel">
      <h3>Events</h3>
      <div className="sort-controls">
        <label>
          Sort by
          <select data-testid="sort-key" value={sortKey} onChange={(e) => onSortKeyChange(e.target.value)}>
            <option value="brightness">Brightness</option>
            <option value="frp">FRP</option>
            <option value="confidence">Confidence</option>
            <option value="risk">Risk</option>
          </select>
        </label>
        <button
          type="button"
          data-testid="sort-dir"
          onClick={onSortDirToggle}
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
              onClick={() => onSelectEvent(fire.id)}
            >
              <div className="event-row-top">
                <span className={`severity-pill ${fire.severity}`}>{fire.severity}</span>
                <span>{fire.confidence}</span>
              </div>
              <div>Lat/Lon: {fire.lat.toFixed(2)}, {fire.lon.toFixed(2)}</div>
              <div>
                Brightness: {fire.brightness} | FRP: {fire.frp}
              </div>
              <div>Risk (AI): {fire.risk.toFixed(4)}</div>
            </button>
          </li>
        ))}
      </ul>
    </aside>
  );
}
