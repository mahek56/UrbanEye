import React, { useState, useEffect } from 'react';
import '../styles/MapView.css';

function formatClock(date) {
  return date.toLocaleTimeString('en-IN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  });
}

function formatDate(date) {
  return date.toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

export default function StatusBar({ incidentCount }) {
  const [now, setNow] = useState(new Date());

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <header className="statusbar" role="banner">
      {/* Left — Wordmark */}
      <div className="statusbar__wordmark">
        <span className="statusbar__title">UrbanEye</span>
        <span className="statusbar__subtitle">{"// FIELD LEDGER"}</span>
      </div>

      {/* Right — Status indicators */}
      <div className="statusbar__right">
        <div className="statusbar__stat">
          <span className="statusbar__stat-label">Active incidents</span>
          <span className="statusbar__stat-value">{incidentCount ?? '—'}</span>
        </div>

        <div className="statusbar__divider" aria-hidden="true" />

        <div className="statusbar__stat">
          <span className="statusbar__stat-label">Updated</span>
          <span className="statusbar__stat-value">
            {formatDate(now)} · {formatClock(now)}
          </span>
        </div>

        <div className="statusbar__divider" aria-hidden="true" />

        <div
          className="statusbar__live-dot"
          title="Live feed active"
          aria-label="Live feed active"
        />
      </div>
    </header>
  );
}
