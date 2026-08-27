import React from 'react';
import LedgerRow from './LedgerRow';
import '../styles/Ledger.css';

export default function IncidentLedger({
  incidents,
  loading,
  selectedId,
  onSelectIncident,
}) {
  // Sort by severity descending (highest priority at top)
  const sorted = [...incidents].sort((a, b) => b.severity - a.severity);

  return (
    <aside className="ledger" aria-label="Incident ledger">
      {/* Header */}
      <div className="ledger__header">
        <div className="ledger__header-top">
          <h2 className="ledger__title">Incident Log</h2>
          <span className="ledger__count" aria-live="polite">
            {loading ? '…' : `${sorted.length} active`}
          </span>
        </div>
        <div className="ledger__subtitle">sorted by severity · Hyderabad</div>
      </div>

      {/* Column headers */}
      <div className="ledger__col-headers" aria-hidden="true">
        <span className="ledger__col-label">#</span>
        <span className="ledger__col-label">Type</span>
        <span className="ledger__col-label ledger__col-label--right">Sev.</span>
        <span className="ledger__col-label ledger__col-label--right">Last seen</span>
        <span className="ledger__col-label ledger__col-label--right">▲</span>
      </div>

      {/* List */}
      <div className="ledger__list" role="list">
        {loading ? (
          <div className="ledger__loading" role="status">
            <p className="ledger__loading-text">
              Fetching incidents<span className="ledger__loading-anim">...</span>
            </p>
          </div>
        ) : sorted.length === 0 ? (
          <div className="ledger__empty">
            <p className="ledger__empty-text">No active incidents</p>
          </div>
        ) : (
          sorted.map((incident, idx) => (
            <LedgerRow
              key={incident.incident_id}
              incident={incident}
              index={idx + 1}
              isSelected={selectedId === incident.incident_id}
              onClick={() => onSelectIncident(incident.incident_id)}
            />
          ))
        )}
      </div>

      {/* Footer */}
      <div className="ledger__footer">
        <p className="ledger__footer-text">
          ▲ = corroboration count · data via GET /incidents
        </p>
      </div>
    </aside>
  );
}
