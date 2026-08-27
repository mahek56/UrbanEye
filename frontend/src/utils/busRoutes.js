/**
 * busRoutes.js — Hard-coded bus route waypoints for Hyderabad.
 *
 * Each route is an array of [lat, lon] pairs tracing approximate
 * real corridors. These are demo-only — for animation purposes.
 */

export const BUS_ROUTES = [
  {
    bus_id: "TSRTC-14A",
    color: "#8C6A3A",
    waypoints: [
      [17.3850, 78.4867], // Hyderabad Central
      [17.3950, 78.4750],
      [17.4050, 78.4640],
      [17.4156, 78.4512], // Banjara Hills
      [17.4239, 78.4738], // Jubilee Hills
      [17.4350, 78.4850],
    ],
  },
  {
    bus_id: "TSRTC-219",
    color: "#8C6A3A",
    waypoints: [
      [17.4401, 78.4983], // Secunderabad
      [17.4300, 78.4900],
      [17.4200, 78.4820],
      [17.4100, 78.4750],
      [17.3950, 78.4620],
      [17.3850, 78.4600],
    ],
  },
  {
    bus_id: "TSRTC-5C",
    color: "#8C6A3A",
    waypoints: [
      [17.4500, 78.3750], // Hitech City
      [17.4430, 78.3900],
      [17.4350, 78.4100],
      [17.4280, 78.4300],
      [17.4200, 78.4500],
      [17.4156, 78.4512],
    ],
  },
  {
    bus_id: "TSRTC-88",
    color: "#8C6A3A",
    waypoints: [
      [17.3850, 78.4867],
      [17.3780, 78.4800],
      [17.3720, 78.4750],
      [17.3680, 78.4680],
      [17.3620, 78.4600],
      [17.3580, 78.4530],
    ],
  },
  {
    bus_id: "TSRTC-66X",
    color: "#8C6A3A",
    waypoints: [
      [17.4239, 78.4738],
      [17.4180, 78.4800],
      [17.4120, 78.4870],
      [17.4060, 78.4940],
      [17.4000, 78.5000],
      [17.3950, 78.5060],
    ],
  },
];
