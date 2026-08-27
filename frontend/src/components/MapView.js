import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import '../styles/MapView.css';

import { getSeverityColor, getSeverityRadius, getSeverityFillOpacity } from '../utils/severity';
import { buildIncidentPopupHTML } from './incidentPopup';
import { BUS_ROUTES } from '../utils/busRoutes';

// ── Hyderabad centre ───────────────────────────────────────────
const HYD_LAT  = 17.3850;
const HYD_LON  = 78.4867;
const ZOOM     = 13;

// ── Tile layer ─────────────────────────────────────────────────
// Stadia Toner-Lite: charcoal linework on white — warm-filtered via CSS.
// On localhost the free tier works without an API key.
// For production: append ?api_key=YOUR_KEY or configure via Stadia dashboard.
const TILE_URL =
  'https://tiles.stadiamaps.com/tiles/stamen_toner_lite/{z}/{x}/{y}{r}.png';
const TILE_ATTR =
  '&copy; <a href="https://stadiamaps.com/">Stadia Maps</a> ' +
  '&copy; <a href="https://stamen.com">Stamen Design</a> ' +
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>';

// ── Bus animation config ──────────────────────────────────────
const BUS_STEP_MS   = 1800;  // ms between waypoint steps
const BUS_ICON_SIZE = [32, 15];

function makeBusIcon(busId) {
  const short = busId.replace('TSRTC-', '');
  return L.divIcon({
    className: '',
    html: `<div class="bus-glyph" title="${busId}">${short}</div>`,
    iconSize:   BUS_ICON_SIZE,
    iconAnchor: [16, 7],
  });
}

// ── Helpers ────────────────────────────────────────────────────
function interpolatePath(waypoints, t) {
  // t in [0, 1] across the whole route
  const segments = waypoints.length - 1;
  const segT     = t * segments;
  const segIdx   = Math.min(Math.floor(segT), segments - 1);
  const localT   = segT - segIdx;
  const a = waypoints[segIdx];
  const b = waypoints[segIdx + 1];
  return [
    a[0] + (b[0] - a[0]) * localT,
    a[1] + (b[1] - a[1]) * localT,
  ];
}

// ──────────────────────────────────────────────────────────────
export default function MapView({ incidents, selectedId, onSelectIncident }) {
  const mapContainerRef = useRef(null);
  const mapRef          = useRef(null);
  const blotLayerRef    = useRef(null);   // L.layerGroup for incident blots
  const busMarkersRef   = useRef([]);
  const busTimersRef    = useRef([]);
  const coordsRef       = useRef(null);

  // ── Initialize map once ────────────────────────────────────
  useEffect(() => {
    if (mapRef.current) return; // already initialized

    const map = L.map(mapContainerRef.current, {
      center:          [HYD_LAT, HYD_LON],
      zoom:            ZOOM,
      zoomControl:     true,
      attributionControl: true,
    });

    // Tile layer with CSS warm filter applied via the container class
    L.tileLayer(TILE_URL, {
      attribution: TILE_ATTR,
      maxZoom:     19,
      // Apply warm sepia shift directly on the tile elements
      className:   'map-tiles-warm',
    }).addTo(map);

    // Inject tile filter style once
    const style = document.createElement('style');
    style.textContent = `
      .map-tiles-warm img {
        filter: sepia(0.28) brightness(1.04) contrast(0.95) saturate(0.85);
      }
    `;
    document.head.appendChild(style);

    // Incident blot layer group
    blotLayerRef.current = L.layerGroup().addTo(map);

    // Bus markers
    BUS_ROUTES.forEach((route) => {
      const marker = L.marker(route.waypoints[0], {
        icon:        makeBusIcon(route.bus_id),
        zIndexOffset: 1000,
      }).addTo(map);
      marker.bindTooltip(route.bus_id, {
        permanent: false,
        direction: 'top',
        className: 'bus-tooltip',
        offset:    [0, -10],
      });
      busMarkersRef.current.push({ marker, route });
    });

    // ── Animate buses along routes ────────────────────────────
    busMarkersRef.current.forEach(({ marker, route }, i) => {
      let step = 0;
      const totalSteps = (route.waypoints.length - 1) * 40; // 40 sub-steps per segment

      // Stagger start
      const timer = setTimeout(() => {
        const interval = setInterval(() => {
          step = (step + 1) % totalSteps;
          const t = step / totalSteps;
          const [lat, lon] = interpolatePath(route.waypoints, t);
          marker.setLatLng([lat, lon]);
        }, BUS_STEP_MS / 40);
        busTimersRef.current.push(interval);
      }, i * 600);

      busTimersRef.current.push(timer);
    });

    // ── Coordinates display ───────────────────────────────────
    map.on('mousemove', (e) => {
      if (coordsRef.current) {
        coordsRef.current.textContent =
          `${e.latlng.lat.toFixed(4)}°N  ${e.latlng.lng.toFixed(4)}°E`;
      }
    });

    mapRef.current = map;

    // Capture ref value for cleanup (avoids stale-ref ESLint warning)
    const timers = busTimersRef.current;
    return () => {
      timers.forEach(clearTimeout);
      timers.forEach(clearInterval);
      map.remove();
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Re-render blots when incidents change ──────────────────
  useEffect(() => {
    if (!mapRef.current || !blotLayerRef.current) return;
    blotLayerRef.current.clearLayers();

    incidents.forEach((incident) => {
      const { lat, lon, severity, incident_id } = incident;
      const color   = getSeverityColor(severity);
      const radius  = getSeverityRadius(severity);
      const opacity = getSeverityFillOpacity(severity);

      const blot = L.circleMarker([lat, lon], {
        radius,
        color,
        weight:       1.2,
        opacity:      Math.min(opacity + 0.15, 0.9),
        fillColor:    color,
        fillOpacity:  opacity,
        // No standard Leaflet pin — pure circle geometry
      });

      // Build popup
      const popupHTML = buildIncidentPopupHTML(incident);
      blot.bindPopup(popupHTML, {
        maxWidth:    300,
        minWidth:    240,
        autoPan:     true,
        closeButton: true,
        className:   'ledger-popup',
      });

      blot.on('click', () => {
        onSelectIncident(incident_id);
      });

      // Subtle hover pulse
      blot.on('mouseover', function () {
        this.setStyle({ weight: 2.5, opacity: 1 });
      });
      blot.on('mouseout', function () {
        this.setStyle({
          weight:  1.2,
          opacity: Math.min(opacity + 0.15, 0.9),
        });
      });

      blotLayerRef.current.addLayer(blot);

      // Store ref on blot for pan-to
      blot._incidentId = incident_id;
      blot._incidentData = incident;
    });
  }, [incidents, onSelectIncident]);

  // ── Pan to selected incident ───────────────────────────────
  useEffect(() => {
    if (!mapRef.current || !blotLayerRef.current || !selectedId) return;

    blotLayerRef.current.eachLayer((layer) => {
      if (layer._incidentId === selectedId) {
        mapRef.current.setView(layer.getLatLng(), Math.max(mapRef.current.getZoom(), 14), {
          animate: true,
          duration: 0.6,
        });
        layer.openPopup();
      }
    });
  }, [selectedId]);

  return (
    <div className="mapview-wrapper">
      <div
        id="urbaneye-map"
        className="mapview-container"
        ref={mapContainerRef}
        aria-label="Hyderabad road incident map"
      />
      {/* Coordinate readout */}
      <div className="mapview-coords" ref={coordsRef} aria-hidden="true">
        17.3850°N  78.4867°E
      </div>
    </div>
  );
}
