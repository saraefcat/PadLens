/* Input History - event reducer. No dependencies, no network calls.
 * Input Overlay 5.1.x/SDL3 WebSocket event schema.
 */
(function (root, factory) {
  const api = factory();
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (root) root.InputHistoryCore = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  // SDL_GamepadButton values (SDL3), same numbering as Input Overlay v5.x.
  const BUTTONS = Object.freeze({
    0: 'A', 1: 'B', 2: 'X', 3: 'Y', 4: 'View', 5: 'Home',
    6: 'Menu', 7: 'L3', 8: 'R3', 9: 'LB', 10: 'RB',
    11: '↑', 12: '↓', 13: '←', 14: '→'
  });
  const TRIGGERS = Object.freeze({4: 'LT', 5: 'RT'});
  const TYPES = new Set(['controller_button_down', 'controller_button_up', 'controller_axis_motion',
    'controller_device_added', 'controller_device_removed']);

  // Only the controls rendered by this history are accepted. Input Overlay also
  // publishes keyboard/mouse events and additional SDL buttons; none are needed here.
  function normalizedEvent(data) {
    if (!data || typeof data !== 'object' || Array.isArray(data) || !TYPES.has(data.event_type)) return null;
    const device = data.device_index;
    if (!Number.isInteger(device) || device < 0 || device > 2147483647) return null;
    const stamp = data.time;
    const time = (typeof stamp === 'number' && Number.isFinite(stamp) && stamp > 0)
      ? stamp : null; // SDL nanoseconds; null means unknown, never invent a timestamp.
    if (data.event_type === 'controller_device_added' || data.event_type === 'controller_device_removed')
      return {type: data.event_type, code: null, value: null, time, device};
    const code = data.virtual_code;
    if (!Number.isInteger(code)) return null;
    if (data.event_type === 'controller_axis_motion') {
      if (!(code === 4 || code === 5) || typeof data.virtual_value !== 'number' ||
          !Number.isFinite(data.virtual_value) || data.virtual_value < -1.1 || data.virtual_value > 1.1)
        return null;
      return {type: data.event_type, code, value: data.virtual_value, time, device};
    }
    if (!Object.hasOwn(BUTTONS, code)) return null;
    return {type: data.event_type, code, value: null, time, device};
  }

  // Hard limit on a text frame BEFORE JSON.parse. Does not secure the upstream
  // WebSocket listener; it only bounds work by this browser source.
  function parseMessageFrame(raw, maxChars = 4096) {
    if (typeof raw !== 'string' || raw.length > maxChars) return null;
    try {
      const data = JSON.parse(raw);
      return normalizedEvent(data) ? data : null;
    } catch (_) { return null; }
  }

  class RateLimiter {
    constructor(limit = 2000, periodMs = 1000) {
      this.limit = limit; this.periodMs = periodMs;
      this.periodStart = null; this.count = 0;
    }
    accept(now) {
      if (!Number.isFinite(now)) return false;
      if (this.periodStart === null || now < this.periodStart || now - this.periodStart >= this.periodMs) {
        this.periodStart = now; this.count = 0;
      }
      if (this.count >= this.limit) return false;
      this.count += 1;
      return true;
    }
  }

  // The plugin may deliver a burst in reverse order. Hold a short burst and
  // sort by the SDL event timestamp, not WebSocket arrival order.
  class EventBuffer {
    constructor(holdbackMs = 90, maxPending = 512) {
      this.holdbackMs = holdbackMs;
      this.maxPending = maxPending;
      this.pending = [];
      this.serial = 0;
    }
    push(data, receivedAt) {
      if (this.pending.length >= this.maxPending) return false;
      this.pending.push({data, receivedAt, seq: this.serial++});
      return true;
    }
    drainDue(now) {
      if (!this.pending.length || now - this.pending[0].receivedAt < this.holdbackMs) return [];
      return reorder(this.pending.splice(0));
    }
    remainingDelay(now) {
      return this.pending.length ? Math.max(1, this.holdbackMs - (now - this.pending[0].receivedAt)) : null;
    }
    clear() { this.pending.length = 0; }
    get length() { return this.pending.length; }
  }

  class Reducer {
    constructor(options = {}) {
      this.maxItems = Math.max(1, Math.min(32, Number.isSafeInteger(options.maxItems) ? options.maxItems : 8));
      this.triggerOn = options.triggerOn ?? 0.22;
      this.triggerOff = options.triggerOff ?? 0.12;
      this.chordWindowNs = (options.chordWindowMs ?? 28) * 1000000;
      this.items = [];
      this.pressed = new Set();
      this.triggers = new Map();
      this.fixedDevice = Number.isInteger(options.deviceId) ? options.deviceId : null;
      this.selectedDevice = this.fixedDevice;
      this.nextId = 1;
      this.lastChord = null;
      this.lastStartTimeNs = null;
    }

    ingest(raw, receivedAt = Date.now()) {
      const e = normalizedEvent(raw);
      if (!e) return false;
      if (e.type === 'controller_device_added') return false;
      if (e.type === 'controller_device_removed') {
        if (this.selectedDevice === e.device) {
          this.pressed.clear(); this.triggers.clear(); this.selectedDevice = null;
          this.lastChord = null; this.lastStartTimeNs = null;
          this.selectedDevice = this.fixedDevice;
        }
        return false;
      }
      if (e.device === null) return false;
      if (this.selectedDevice === null) {
        // Ignore releases and idle stick/trigger noise from other devices.
        if (e.type === 'controller_button_down' ||
            (e.type === 'controller_axis_motion' && e.value >= this.triggerOn))
          this.selectedDevice = e.device;
        else return false;
      }
      if (e.device !== this.selectedDevice || e.code === null) return false;

      const t = e.time;  // SDL event timestamp (ns); missing timestamps do not yield fake intervals
      if (e.type === 'controller_button_down') {
        const label = BUTTONS[e.code];
        if (!label || this.pressed.has(e.code)) return false;
        this.pressed.add(e.code);
        // Group only near-simultaneous button DOWN events while the first is still held.
        const last = this.lastChord;
        if (last && t !== null && last.time !== null && this.pressed.has(last.code) && t - last.time >= 0 &&
            t - last.time <= this.chordWindowNs && !last.item.labels.includes(label)) {
          last.item.labels.push(label);
          // Keep each chord constituent's time in memory; UI remains one row.
          last.item.presses.push({label, timeNs:t});
          last.item.updatedAt = receivedAt;
          return true;
        }
        const item = this.add([label], receivedAt, 'button', t);
        this.lastChord = {time: t, code: e.code, item};
        return true;
      }
      if (e.type === 'controller_button_up') {
        this.pressed.delete(e.code);
        return false;
      }
      if (e.type === 'controller_axis_motion') {
        const label = TRIGGERS[e.code];
        if (!label || !Number.isFinite(e.value)) return false;
        const value = Math.min(1, Math.max(0, e.value));
        const active = this.triggers.get(e.code);
        if (!active && value >= this.triggerOn) {
          const item = this.add([label], receivedAt, 'trigger', t);
          item.peak = Math.round(value * 100);
          this.triggers.set(e.code, item);
          this.lastChord = null;
          return true;
        }
        if (active) {
          if (value <= this.triggerOff) {
            this.triggers.delete(e.code);
            return false;
          }
          if (Math.round(value * 100) >= active.peak + 4) {
            active.peak = Math.round(value * 100);
            return true;
          }
        }
      }
      return false;
    }

    add(labels, at, kind, timeNs) {
      const validTime = Number.isFinite(timeNs) && timeNs > 0 ? timeNs : null;
      let intervalMs = null;
      if (validTime !== null && this.lastStartTimeNs !== null) {
        const diffNs = validTime - this.lastStartTimeNs;
        // Long gaps are not meaningful RTA input intervals. Prevent malformed
        // timestamps from producing unwieldy onscreen numbers.
        if (Number.isFinite(diffNs) && diffNs >= 0 && diffNs <= 86_400_000_000_000)
          intervalMs = Math.round(diffNs / 1_000_000);
      }
      const item = {id: this.nextId++, labels, at, updatedAt: at, kind,
        startTimeNs: validTime, intervalMs,
        presses: labels.map(label => ({label, timeNs:validTime}))};
      this.lastStartTimeNs = validTime;
      this.items.unshift(item);
      if (this.items.length > this.maxItems) this.items.length = this.maxItems;
      return item;
    }

    clearItems() {
      // Clear the visible record without inventing a delta to a removed entry.
      // Keep the currently-held state to avoid manufacturing duplicate downs.
      this.items.length = 0;
      this.lastChord = null;
      this.lastStartTimeNs = null;
    }

    resetContinuity() {
      this.pressed.clear(); this.triggers.clear(); this.lastChord = null;
      this.lastStartTimeNs = null;
      this.selectedDevice = this.fixedDevice;
    }

    expire(now, ttlMs) {
      const old = this.items.length;
      this.items = this.items.filter(item => now - item.at < ttlMs);
      return old !== this.items.length;
    }
  }

  function reorder(events) {
    return [...events].sort((a, b) => {
      const ta = a.data.time, tb = b.data.time;
      const av = typeof ta === 'number' && Number.isFinite(ta) && ta > 0;
      const bv = typeof tb === 'number' && Number.isFinite(tb) && tb > 0;
      if (av && bv) return ta - tb || a.seq - b.seq;
      if (av !== bv) return av ? -1 : 1; // events with unknown time are last
      return a.seq - b.seq;
    });
  }

  // Pixels used for the visible panel, not the OBS browser source canvas.
  function normalizeWidth(value, fallback = 260) {
    const allowed = [240, 260, 300];
    return allowed.includes(Number(value)) ? Number(value) : fallback;
  }

  // Fit from newest events irrespective of display direction: never discard a
  // newer event just to show more old entries in bottom-newest mode.
  function recentItems(items, count, order = 'newest') {
    return viewItems(items.slice(0, Math.max(0, Math.floor(count))), order);
  }

  function viewItems(items, order = 'newest') {
    if (order !== 'newest' && order !== 'oldest') throw new TypeError('Invalid history order');
    return order === 'newest' ? [...items] : [...items].reverse();
  }

  // Calculate a displayed separator only when both adjacent history entries exist;
  // never attach the newer entry's interval to the wrong predecessor.
  function visibleInterval(newer, older) {
    if (!newer || !older || newer.id !== older.id + 1) return null;
    return Number.isInteger(newer.intervalMs) && newer.intervalMs >= 0 ? newer.intervalMs : null;
  }

  // UI-only sequence label. Internal item.id remains monotonic for timing and
  // adjacency checks; after display 999, restart at 01 (never emit 1000).
  function formatSequence(id) {
    if (!Number.isSafeInteger(id) || id < 1) throw new RangeError('Invalid history ID');
    const visible = ((id - 1) % 999) + 1;
    return String(visible).padStart(2, '0');
  }

  return {BUTTONS, TRIGGERS, normalizedEvent, parseMessageFrame, RateLimiter, EventBuffer,
    Reducer, reorder, viewItems, visibleInterval, normalizeWidth, recentItems, formatSequence};
});
