/**
 * severity.js — Utility functions for mapping incident severity (0–10)
 * to visual properties: color, radius, opacity, and label.
 *
 * All functions accept a severity number in [0, 10].
 */

// Palette anchors (from design system)
const COLOR_LOW    = { r: 0xC9, g: 0x8B, b: 0x2A }; // --ochre
const COLOR_MID    = { r: 0xB5, g: 0x45, b: 0x1B }; // --rust
const COLOR_HIGH   = { r: 0x7A, g: 0x35, b: 0x20 }; // --sienna

function lerp(a, b, t) {
  return Math.round(a + (b - a) * t);
}

function toHex(r, g, b) {
  return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
}

/**
 * Returns a hex color interpolated through ochre → rust → sienna.
 */
export function getSeverityColor(severity) {
  const t = Math.max(0, Math.min(1, severity / 10));
  let r, g, b;
  if (t < 0.5) {
    const tt = t / 0.5;
    r = lerp(COLOR_LOW.r, COLOR_MID.r, tt);
    g = lerp(COLOR_LOW.g, COLOR_MID.g, tt);
    b = lerp(COLOR_LOW.b, COLOR_MID.b, tt);
  } else {
    const tt = (t - 0.5) / 0.5;
    r = lerp(COLOR_MID.r, COLOR_HIGH.r, tt);
    g = lerp(COLOR_MID.g, COLOR_HIGH.g, tt);
    b = lerp(COLOR_MID.b, COLOR_HIGH.b, tt);
  }
  return toHex(r, g, b);
}

/**
 * Returns the ink-blot circle radius in pixels.
 * Low severity → subtle dot; high severity → spreading stain.
 */
export function getSeverityRadius(severity) {
  const t = Math.max(0, Math.min(1, severity / 10));
  return 7 + t * 22; // range: 7px – 29px
}

/**
 * Returns fill opacity for the ink-blot.
 * Low severity → almost watermark; high severity → dense ink.
 */
export function getSeverityFillOpacity(severity) {
  const t = Math.max(0, Math.min(1, severity / 10));
  return 0.22 + t * 0.58; // range: 0.22 – 0.80
}

/**
 * Returns a human-readable severity label.
 */
export function getSeverityLabel(severity) {
  if (severity >= 8)   return 'CRITICAL';
  if (severity >= 6)   return 'HIGH';
  if (severity >= 4)   return 'MODERATE';
  if (severity >= 2)   return 'LOW';
  return 'TRACE';
}

/**
 * Returns a CSS class suffix for severity band styling.
 */
export function getSeverityBand(severity) {
  if (severity >= 8)   return 'critical';
  if (severity >= 6)   return 'high';
  if (severity >= 4)   return 'moderate';
  return 'low';
}
