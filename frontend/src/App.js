import React, { useState, useEffect, useCallback } from 'react';
import StatusBar from './components/StatusBar';
import MapView from './components/MapView';
import IncidentLedger from './components/IncidentLedger';
import { fetchIncidents } from './api/incidents';
import './styles/global.css';

const POLL_INTERVAL_MS = 30_000; // 30s — re-fetch interval when backend is live

export default function App() {
  const [incidents,   setIncidents]   = useState([]);
  const [loading,     setLoading]     = useState(true);
  const [selectedId,  setSelectedId]  = useState(null);

  // ── Load incidents ─────────────────────────────────────────
  const loadIncidents = useCallback(async () => {
    try {
      const data = await fetchIncidents();
      setIncidents(data);
    } catch (err) {
      console.error('[UrbanEye] Failed to fetch incidents:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadIncidents();
    const poll = setInterval(loadIncidents, POLL_INTERVAL_MS);
    return () => clearInterval(poll);
  }, [loadIncidents]);

  // ── Selection handler — togglable ─────────────────────────
  const handleSelectIncident = useCallback((id) => {
    setSelectedId((prev) => (prev === id ? null : id));
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Top bar */}
      <StatusBar incidentCount={loading ? null : incidents.length} />

      {/* Main content: map + sidebar */}
      <div style={{ display: 'flex', flex: 1, minHeight: 0 }}>
        <MapView
          incidents={incidents}
          selectedId={selectedId}
          onSelectIncident={handleSelectIncident}
        />
        <IncidentLedger
          incidents={incidents}
          loading={loading}
          selectedId={selectedId}
          onSelectIncident={handleSelectIncident}
        />
      </div>
    </div>
  );
}
