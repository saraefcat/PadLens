/* Default settings. These survive file moves and OBS browser cache resets.
 * For live changes use OBS's browser source -> Interact -> hover over the top-right corner.
 * Two direct buttons (no native dropdown) choose newest/top or newest/bottom.
 * History width 240/260/300px uses direct buttons; source canvas 300x510px.
 * Header can be hidden without losing the hover-revealed settings button.
 * localStorage changes, if available, take precedence over this file.
 */
window.ControllerHistoryDefaults = Object.freeze({
  HISTORY_WIDTH: 260,          // 240 / 260 / 300 (default: 260)
  INPUT_ORDER: 'newest',        // 'newest' (top) or 'oldest' (bottom)
  SHOW_INPUT_INTERVAL: false, // show delta between the START of consecutive history rows
  SHOW_HEADER: true,           // true: show title/status; false: hide header + its spacing
  AUTO_EXPIRE: true,          // true: clear older entries after LIFETIME_MS; false: keep up to MAX_ITEMS
  MAX_ITEMS: 8,
  LIFETIME_MS: 9000,
  DEVICE_ID: null,             // null: first input-producing gamepad
  WS_URL: 'ws://127.0.0.1:16899/'
});
