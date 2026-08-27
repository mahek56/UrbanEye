/**
 * incidents.js — Data access layer for UrbanEye incidents.
 *
 * Currently returns hardcoded mock data matching the GET /incidents contract.
 *
 * ─── SWAP POINT ────────────────────────────────────────────────────────────
 * When the backend is ready, replace the body of fetchIncidents() with:
 *
 *   const res = await fetch('http://localhost:8000/incidents');
 *   if (!res.ok) throw new Error('Failed to fetch incidents');
 *   return res.json();
 *
 * Everything else in the app calls only this function — nothing else changes.
 * ───────────────────────────────────────────────────────────────────────────
 */

const MOCK_INCIDENTS = [
  {
    incident_id: "HYD-0091",
    lat: 17.4239,
    lon: 78.4738,
    type: "pothole",
    severity: 9.4,
    corroboration_count: 5,
    first_seen: "2026-08-26T08:12:00Z",
    last_seen: "2026-08-27T14:47:00Z",
  },
  {
    incident_id: "HYD-0073",
    lat: 17.4156,
    lon: 78.4512,
    type: "road_damage",
    severity: 7.1,
    corroboration_count: 3,
    first_seen: "2026-08-25T17:30:00Z",
    last_seen: "2026-08-27T11:20:00Z",
  },
  {
    incident_id: "HYD-0058",
    lat: 17.4401,
    lon: 78.4983,
    type: "obstruction",
    severity: 5.5,
    corroboration_count: 2,
    first_seen: "2026-08-27T06:05:00Z",
    last_seen: "2026-08-27T09:55:00Z",
  },
  {
    incident_id: "HYD-0044",
    lat: 17.3950,
    lon: 78.4620,
    type: "congestion",
    severity: 3.8,
    corroboration_count: 4,
    first_seen: "2026-08-26T21:45:00Z",
    last_seen: "2026-08-27T07:30:00Z",
  },
  {
    incident_id: "HYD-0031",
    lat: 17.4500,
    lon: 78.3750,
    type: "pothole",
    severity: 2.1,
    corroboration_count: 1,
    first_seen: "2026-08-27T13:00:00Z",
    last_seen: "2026-08-27T13:15:00Z",
  },
];

/**
 * Fetch all active incidents.
 * @returns {Promise<Array>} Array of incident objects per API_Contract.md
 */
export async function fetchIncidents() {
  // Simulate a brief network latency for realistic UX
  await new Promise((resolve) => setTimeout(resolve, 400));
  return MOCK_INCIDENTS;
}
