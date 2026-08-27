/**
 * incidentPopup.js — Generates a ledger-styled HTML string for Leaflet popups.
 *
 * Leaflet popups require HTML strings, not JSX. This keeps the styling
 * consistent with the overall design system via inline styles.
 */

import { getSeverityLabel, getSeverityColor } from '../utils/severity';

function formatDate(isoString) {
  const d = new Date(isoString);
  const date = d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
  const time = d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: false });
  return `${date} · ${time}`;
}

const TYPE_LABELS = {
  pothole:     'POTHOLE',
  road_damage: 'ROAD DAMAGE',
  congestion:  'CONGESTION',
  obstruction: 'OBSTRUCTION',
};

export function buildIncidentPopupHTML(incident) {
  const { incident_id, type, severity, corroboration_count, first_seen, last_seen } = incident;
  const severityLabel = getSeverityLabel(severity);
  const accentColor = getSeverityColor(severity);
  const typeLabel = TYPE_LABELS[type] || type.toUpperCase();

  return `
    <div style="
      font-family: 'JetBrains Mono', 'Courier New', monospace;
      background: #EDE8DC;
      border: 1.5px solid #C8BFB0;
      border-top: 3px solid ${accentColor};
      padding: 0;
      min-width: 240px;
      max-width: 280px;
      box-shadow: 2px 3px 12px rgba(44,36,22,0.13);
    ">
      <!-- Header -->
      <div style="
        padding: 10px 14px 8px;
        border-bottom: 1px solid #C8BFB0;
        display: flex;
        justify-content: space-between;
        align-items: baseline;
      ">
        <span style="
          font-family: 'Zilla Slab', Georgia, serif;
          font-size: 13px;
          font-weight: 700;
          color: #2C2416;
          letter-spacing: 0.02em;
        ">${typeLabel}</span>
        <span style="
          font-size: 10px;
          color: #6B5E4A;
          letter-spacing: 0.08em;
        ">${incident_id}</span>
      </div>

      <!-- Severity row -->
      <div style="
        padding: 8px 14px;
        border-bottom: 1px solid #C8BFB0;
        display: flex;
        justify-content: space-between;
        align-items: center;
      ">
        <span style="font-size: 10px; color: #6B5E4A; letter-spacing: 0.1em;">SEVERITY</span>
        <span style="
          font-size: 13px;
          font-weight: 700;
          color: ${accentColor};
          letter-spacing: 0.05em;
        ">${severity.toFixed(1)} <span style="font-size:9px; font-weight:400; color:#6B5E4A;">${severityLabel}</span></span>
      </div>

      <!-- Corroboration -->
      <div style="
        padding: 8px 14px;
        border-bottom: 1px solid #C8BFB0;
        display: flex;
        justify-content: space-between;
      ">
        <span style="font-size: 10px; color: #6B5E4A; letter-spacing: 0.1em;">CONFIRMED BY</span>
        <span style="font-size: 12px; color: #2C2416; font-weight: 600;">
          ${corroboration_count} ${corroboration_count === 1 ? 'bus' : 'buses'}
        </span>
      </div>

      <!-- Timestamps -->
      <div style="padding: 8px 14px 10px;">
        <div style="
          font-size: 9.5px;
          color: #6B5E4A;
          letter-spacing: 0.08em;
          margin-bottom: 4px;
        ">FIRST SEEN</div>
        <div style="font-size: 11px; color: #2C2416; margin-bottom: 8px;">${formatDate(first_seen)}</div>
        <div style="
          font-size: 9.5px;
          color: #6B5E4A;
          letter-spacing: 0.08em;
          margin-bottom: 4px;
        ">LAST SEEN</div>
        <div style="font-size: 11px; color: #2C2416;">${formatDate(last_seen)}</div>
      </div>
    </div>
  `;
}
