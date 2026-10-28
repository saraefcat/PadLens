/* v0.8: bounded input handling, resilient ordering, and device selection. */
(() => {
  'use strict';
  const D = window.ControllerHistoryDefaults;
  if (!D || !window.InputHistoryCore) {
    document.querySelector('#status').textContent = '構成ファイル読込エラー';
    document.querySelector('#status').className = 'error';
    return;
  }
  const CONFIG = Object.freeze({
    WS_URL: D.WS_URL,
    DEVICE_ID: D.DEVICE_ID,
    MAX_ITEMS: D.MAX_ITEMS,
    LIFETIME_MS: D.LIFETIME_MS,
    CHORD_WINDOW_MS: 28,
    REORDER_DELAY_MS: 90,
    MAX_MESSAGE_CHARS: 4096,
    MAX_PENDING_EVENTS: 512,
    MAX_EVENTS_PER_SECOND: 2000,
    TRIGGER_ON: .22,
    TRIGGER_OFF: .12,
    DEMO: new URLSearchParams(location.search).get('demo') === '1'
  });
  const {Reducer, normalizedEvent, parseMessageFrame, RateLimiter, EventBuffer,
    recentItems, visibleInterval, normalizeWidth, formatSequence} = window.InputHistoryCore;
  const history = new Reducer({maxItems:CONFIG.MAX_ITEMS, chordWindowMs:CONFIG.CHORD_WINDOW_MS,
    deviceId:CONFIG.DEVICE_ID, triggerOn:CONFIG.TRIGGER_ON, triggerOff:CONFIG.TRIGGER_OFF});
  const list = document.querySelector('#items');
  const panelRoot = document.querySelector('main');
  const indicator = document.querySelector('#status');
  const mode = document.querySelector('#mode');
  const btn = document.querySelector('#settings-btn');
  const panel = document.querySelector('#settings-panel');
  const orderButtons = [...document.querySelectorAll('.order-choice')];
  const widthButtons = [...document.querySelectorAll('.width-choice')];
  const checkbox = document.querySelector('#interval-checkbox');
  const expireCheckbox = document.querySelector('#expire-checkbox');
  const headerCheckbox = document.querySelector('#header-checkbox');
  const settingsConnection = document.querySelector('#settings-connection');
  const clearButton = document.querySelector('#clear-history-btn');
  // Keep the old internal key readable once, to carry across existing v0.8 settings.
  // This is a storage migration identifier, not a product name or UI label.
  const SETTINGS_KEY = 'controller_input_history_settings';
  const LEGACY_SETTINGS_KEY = 'wolverine_input_history_v02_settings';

  function readSettings() {
    const defaults = {
      order: D.INPUT_ORDER === 'oldest' ? 'oldest' : 'newest',
      width: normalizeWidth(D.HISTORY_WIDTH),
      showInterval: D.SHOW_INPUT_INTERVAL === true,
      autoExpire: D.AUTO_EXPIRE !== false,
      showHeader: D.SHOW_HEADER !== false
    };
    try {
      const current = localStorage.getItem(SETTINGS_KEY);
      const legacy = current === null ? localStorage.getItem(LEGACY_SETTINGS_KEY) : null;
      const saved = JSON.parse(current ?? legacy ?? 'null');
      if (legacy !== null && saved && typeof saved === 'object' && !Array.isArray(saved)) {
        localStorage.setItem(SETTINGS_KEY, JSON.stringify(saved));
        // Do not remove legacy settings: users must be able to roll back to v0.8.
      }
      if (saved && typeof saved === 'object') {
        if (saved.order === 'newest' || saved.order === 'oldest') defaults.order = saved.order;
        if ([240, 260, 300].includes(saved.width)) defaults.width = saved.width;
        if (typeof saved.showInterval === 'boolean') defaults.showInterval = saved.showInterval;
        if (typeof saved.autoExpire === 'boolean') defaults.autoExpire = saved.autoExpire;
        if (typeof saved.showHeader === 'boolean') defaults.showHeader = saved.showHeader;
      }
    } catch (_) { /* local file storage may be unavailable in some CEF profiles */ }
    // Demo-only URL overrides are convenient for deterministic preview images.
    if (CONFIG.DEMO) {
      const params = new URLSearchParams(location.search);
      if (['newest','oldest'].includes(params.get('order'))) defaults.order = params.get('order');
      if (['on','off'].includes(params.get('timing'))) defaults.showInterval = params.get('timing') === 'on';
      if (['on','off'].includes(params.get('expire'))) defaults.autoExpire = params.get('expire') === 'on';
      if (['on','off'].includes(params.get('header'))) defaults.showHeader = params.get('header') === 'on';
      if (['240', '260', '300'].includes(params.get('width'))) defaults.width = Number(params.get('width'));
    }
    return defaults;
  }
  const settings = readSettings();
  function updateOptions() {
    orderButtons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.order === settings.order)));
    widthButtons.forEach(button => button.setAttribute('aria-pressed', String(Number(button.dataset.width) === settings.width)));
    applyViewportWidth();
    checkbox.checked = settings.showInterval;
    expireCheckbox.checked = settings.autoExpire;
    headerCheckbox.checked = settings.showHeader;
    panelRoot.classList.toggle('header-hidden', !settings.showHeader);
    mode.textContent = settings.showInterval ? 'Δt' : '';
    render();
  }
  function applyViewportWidth() {
    // OBS may use a narrower browser canvas than the configured preset.
    // Clamp only in that case: never allow the source itself to crop the UI.
    panelRoot.style.width = `${Math.min(settings.width, window.innerWidth)}px`;
  }
  function saveSettings() {
    try { localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings)); }
    catch (_) { /* edit user_config.js for reliable persistence when disabled */ }
    updateOptions();
  }
  function setPanelOpen(open) {
    panel.classList.toggle('open', open);
    panelRoot.classList.toggle('settings-open', open);
    btn.setAttribute('aria-expanded', String(open));
    btn.setAttribute('aria-label', open ? '入力履歴設定を閉じる' : '入力履歴設定を開く');
  }
  btn.addEventListener('click', () => setPanelOpen(!panel.classList.contains('open')));
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && panel.classList.contains('open')) {
      setPanelOpen(false);
      btn.focus();
    }
  });
  orderButtons.forEach(button => button.addEventListener('click', () => {
    settings.order = button.dataset.order;
    saveSettings();
  }));
  widthButtons.forEach(button => button.addEventListener('click', () => {
    settings.width = normalizeWidth(button.dataset.width);
    saveSettings();
  }));
  checkbox.addEventListener('change', () => { settings.showInterval = checkbox.checked; saveSettings(); });
  headerCheckbox.addEventListener('change', () => { settings.showHeader = headerCheckbox.checked; saveSettings(); });
  expireCheckbox.addEventListener('change', () => {
    settings.autoExpire = expireCheckbox.checked;
    if (settings.autoExpire) history.expire(Date.now(), CONFIG.LIFETIME_MS);
    saveSettings();
  });
  clearButton.addEventListener('click', () => { history.clearItems(); render(); });

  function setConnectionStatus(text, connected) {
    indicator.textContent = ({'切断・再接続中':'再接続','接続待機':'待機','接続済':'接続','接続エラー':'エラー'})[text] || text;
    indicator.classList.toggle('error', !connected);
    settingsConnection.textContent = '接続状態：' + indicator.textContent;
  }
  let socket = null;
  let retryTimer = null;
  let retryMs = 1000;
  let queueTimer = null;
  let lastCommittedNs = null;
  let limitedPeriod = false;
  const rateLimiter = new RateLimiter(CONFIG.MAX_EVENTS_PER_SECOND);
  const buffer = new EventBuffer(CONFIG.REORDER_DELAY_MS, CONFIG.MAX_PENDING_EVENTS);
  const counters = {oversize:0, malformed:0, overflow:0, rateLimited:0, late:0};
  // Expose only numerical diagnostics; never store gamepad/keyboard payloads.
  window.ControllerInputHistoryDiagnostics = () => Object.freeze({...counters, queued:buffer.length});

  function resetInputContinuity() {
    history.resetContinuity();
    lastCommittedNs = null;
  }
  function onQueueOverload() {
    // A missing DOWN/UP event could otherwise leave a button stuck as pressed.
    resetInputContinuity();
    buffer.clear();
    if (queueTimer !== null) { clearTimeout(queueTimer); queueTimer = null; }
  }
  function scheduleFlush() {
    if (queueTimer !== null) return;
    const delay = buffer.remainingDelay(Date.now());
    if (delay !== null) queueTimer = setTimeout(flushQueue, delay);
  }
  function flushQueue() {
    queueTimer = null;
    const batch = buffer.drainDue(Date.now());
    let changed = false;
    for (const item of batch) {
      const e = normalizedEvent(item.data);
      if (!e) continue;
      // Other connected gamepads must not influence chronology or selection.
      if (history.selectedDevice !== null && e.device !== history.selectedDevice) continue;
      if (e.time !== null && lastCommittedNs !== null && e.time < lastCommittedNs) {
        // This is an event that arrived too late even for the holdback window.
        // Reset held states and time continuity instead of producing false Δt.
        counters.late += 1;
        resetInputContinuity();
        // A stale press is not a trustworthy new historical event.
        if (e.type === 'controller_button_down' || e.type === 'controller_axis_motion') continue;
      }
      const oldSelection = history.selectedDevice;
      changed = history.ingest(item.data, item.receivedAt) || changed;
      if (e.type === 'controller_device_removed' && oldSelection === e.device) {
        lastCommittedNs = null;
      } else if (e.time !== null && (history.selectedDevice === e.device || oldSelection === e.device)) {
        lastCommittedNs = Math.max(lastCommittedNs ?? e.time, e.time);
      }
    }
    if (changed) render();
    scheduleFlush();
  }
  function receive(data) {
    const now = Date.now();
    if (!rateLimiter.accept(now)) {
      counters.rateLimited += 1;
      if (!limitedPeriod) { limitedPeriod = true; onQueueOverload(); }
      return;
    }
    limitedPeriod = false;
    if (!buffer.push(data, now)) {
      counters.overflow += 1;
      onQueueOverload();
      return;
    }
    scheduleFlush();
  }
  function appendInterval(ms, arrow) {
    const line = document.createElement('div');
    line.className = 'interval';
    const mark = document.createElement('span');
    mark.className = 'arrow'; mark.textContent = arrow;
    const value = document.createElement('span');
    if (ms === null) {
      value.className = 'muted';
      value.textContent = 'Δt 不明';
    } else {
      value.textContent = `+${ms} ms`;
    }
    line.append(mark, value);
    return line;
  }
  function renderRow(item, now, isLatest) {
    const row = document.createElement('div');
    row.className = 'event';
    if (isLatest) row.classList.add('latest');
    if (settings.autoExpire && now - item.at >= CONFIG.LIFETIME_MS * .75) row.classList.add('aging');
    const seq = document.createElement('span');
    seq.className = 'seq'; seq.textContent = formatSequence(item.id);
    row.append(seq);
    const keys = document.createElement('div');
    keys.className = 'keys';
    item.labels.forEach((label, index) => {
      // Keep the + and the following key together when an input wraps.
      const token = document.createElement('span');
      token.className = 'key-token';
      if (index) {
        const plus = document.createElement('span');
        plus.className = 'plus'; plus.textContent = '+'; token.append(plus);
      }
      const chip = document.createElement('span');
      chip.className = 'chip';
      chip.textContent = ['↑','↓','←','→'].includes(label) ? `D${label}` : label;
      token.append(chip);
      keys.append(token);
    });
    if (item.kind === 'trigger' && Number.isInteger(item.peak)) {
      const peak = document.createElement('span');
      peak.className = 'peak'; peak.textContent = `${item.peak}% peak`; keys.append(peak);
    }
    row.append(keys);
    return row;
  }
  function drawRows(count, now) {
    const rows = recentItems(history.items, count, settings.order);
    const fragment = document.createDocumentFragment();
    rows.forEach((entry,index) => {
      if (settings.showInterval && settings.order === 'oldest' && index > 0) {
        fragment.append(appendInterval(visibleInterval(entry, rows[index-1]), '↓'));
      }
      fragment.append(renderRow(entry, now, entry === history.items[0]));
      if (settings.showInterval && settings.order === 'newest' && index < rows.length - 1) {
        fragment.append(appendInterval(visibleInterval(entry, rows[index+1]), '↑'));
      }
    });
    list.replaceChildren(fragment);
  }
  function render() {
    const now = Date.now();
    // Render and synchronously prune the oldest entries until *all visible*
    // rows fit inside the OBS browser source viewport, with no scroll or crop.
    const bottomLimit = Math.min(document.documentElement.clientHeight, window.innerHeight) - 7;
    let count = history.items.length;
    do {
      drawRows(count, now);
      if (list.getBoundingClientRect().bottom <= bottomLimit || count === 0) break;
      count -= 1;
    } while (true);
  }
  window.addEventListener('resize', () => { applyViewportWidth(); render(); });
  function scheduleReconnect() {
    setConnectionStatus('切断・再接続中', false);
    resetInputContinuity();
    buffer.clear();
    if (queueTimer !== null) { clearTimeout(queueTimer); queueTimer = null; }
    if (retryTimer !== null) return;
    retryTimer = setTimeout(() => {
      retryTimer = null;
      connect();
    }, retryMs);
    retryMs = Math.min(retryMs * 2, 10000);
  }
  function connect() {
    if (CONFIG.DEMO) return;
    setConnectionStatus('接続待機', false);
    try { socket = new WebSocket(CONFIG.WS_URL); }
    catch (_) { scheduleReconnect(); return; }
    socket.addEventListener('open', () => { retryMs = 1000; setConnectionStatus('接続済', true); });
    socket.addEventListener('message', event => {
      if (typeof event.data !== 'string' || event.data.length > CONFIG.MAX_MESSAGE_CHARS) {
        counters.oversize += 1;
        return;
      }
      const data = parseMessageFrame(event.data, CONFIG.MAX_MESSAGE_CHARS);
      if (data) receive(data);
      else counters.malformed += 1;
    });
    socket.addEventListener('close', scheduleReconnect);
    socket.addEventListener('error', () => {setConnectionStatus('接続エラー', false);});
  }
  setInterval(() => {
    const now = Date.now();
    if (!settings.autoExpire) return;
    if (history.expire(now, CONFIG.LIFETIME_MS)) render();
    else if (history.items.some(item => now - item.at >= CONFIG.LIFETIME_MS * .75)) render();
  }, 250);
  updateOptions();
  if (CONFIG.DEMO) {
    setConnectionStatus('DEMO', true);
    const base = 10_000_000_000;
    const e = (event_type,virtual_code,offsetMs,virtual_value=1)=>({
      event_type,virtual_code,time:base+offsetMs*1_000_000,virtual_value,device_index:0});
    const samples = [
      e('controller_button_down',0,0),e('controller_button_up',0,120),
      e('controller_button_down',1,74),e('controller_button_up',1,140),
      e('controller_button_down',13,151),e('controller_button_up',13,170),
      e('controller_button_down',9,162),e('controller_button_up',9,210),
      e('controller_button_down',0,338),e('controller_button_up',0,395),
      e('controller_axis_motion',4,520,.24),e('controller_axis_motion',4,540,.68)
    ];
    samples.forEach(data => receive(data));
  } else connect();
})();
