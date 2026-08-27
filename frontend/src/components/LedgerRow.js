import React from 'react';
import { getSeverityColor, getSeverityLabel, getSeverityBand } from '../utils/severity';
import '../styles/Ledger.css';

const TYPE_DISPLAY = {
  pothole:     'Pothole',
  road_damage: 'Road Damage',
  congestion:  'Congestion',
  obstruction: 'Obstruction',
};

function formatTimeShort(isoString) {
  const d = new Date(isoString);
  // Show date if not today
  const today = new Date();
  const isToday =
    d.getDate() === today.getDate() &&
    d.getMonth() === today.getMonth() &&
    d.getFullYear() === today.getFullYear();

  const time = d.toLocaleTimeString('en-IN', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  });

  if (isToday) return time;

  const date = d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' });
  return `${date}\n${time}`;
}

export default function LedgerRow({ incident, index, isSelected, onClick }) {
  const { incident_id, type, severity, corroboration_count, last_seen } = incident;
  const color = getSeverityColor(severity);
  const label = getSeverityLabel(severity);
  const band  = getSeverityBand(severity);
  const typeDisplay = TYPE_DISPLAY[type] || type;
  const timeLines = formatTimeShort(last_seen).split('\n');

  return (
    <div
      className={`ledger-row${isSelected ? ' ledger-row--selected' : ''}`}
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onClick?.()}
      aria-pressed={isSelected}
      aria-label={`Incident ${incident_id}: ${typeDisplay}, severity ${severity}`}
    >
      {/* Severity accent bar on left edge */}
      <div
        className="ledger-row__dot"
        style={{ background: color }}
        aria-hidden="true"
      />

      {/* Column 1: Index */}
      <span className="ledger-row__index">{String(index).padStart(2, '0')}</span>

      {/* Column 2: Type + ID */}
      <div className="ledger-row__type-wrap">
        <span className="ledger-row__type">{typeDisplay}</span>
        <span className="ledger-row__id">{incident_id}</span>
      </div>

      {/* Column 3: Severity */}
      <div>
        <div className="ledger-row__sev" style={{ color }}>
          {severity.toFixed(1)}
        </div>
        <div className={`ledger-row__sev-band ledger-row__sev-band--${band}`}>
          {label}
        </div>
      </div>

      {/* Column 4: Last seen */}
      <div className="ledger-row__time">
        {timeLines.map((line, i) => (
          <div key={i}>{line}</div>
        ))}
      </div>

      {/* Column 5: Corroboration count */}
      <div className="ledger-row__corr">
        <span className="ledger-row__corr-icon">▲</span>
        {corroboration_count}
      </div>
    </div>
  );
}
