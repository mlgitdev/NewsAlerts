/* Shared helpers + event hub. Python pushes events via App.on(event, payload). */
(function () {
  const handlers = {};
  const _api = {
    get_state: () => fetch("/api/state").then((r) => r.json()),
    poll_events: (after_id) => fetch(`/api/events?after=${encodeURIComponent(after_id || 0)}`).then((r) => r.json()),
    save_config: (cfg) => fetch("/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(cfg),
    }).then((r) => r.json()),
    send_telegram_test: (creds) => fetch("/api/test_telegram", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(creds || {}),
    }).then((r) => r.json()),
    test_alpaca: (creds) => fetch("/api/test_alpaca", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(creds || {}),
    }).then((r) => r.json()),
    get_watchlists: () => fetch("/api/tv_watchlists").then((r) => r.json()),
    select_watchlist: (list_id, title) => fetch("/api/tv_watchlist/select", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ list_id, title }),
    }).then((r) => r.json()),
    add_to_watchlist: (list_id, symbol) => fetch("/api/tv_watchlist/add", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ list_id, symbol }),
    }).then((r) => r.json()),
    set_focused: (focused) => fetch("/api/set_focused", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ focused }),
    }).then((r) => r.json()).catch(() => {}),
    get_news: (ticker, force) => fetch(`/api/news?ticker=${encodeURIComponent(ticker)}&force=${force ? "1" : "0"}`).then((r) => r.json()),
    get_story: (id) => fetch(`/api/story?id=${encodeURIComponent(id)}`).then((r) => r.json()),
    get_quote: (ticker) => fetch(`/api/quote?ticker=${encodeURIComponent(ticker)}`).then((r) => r.json()),
    play_sound: (path) => fetch("/api/play_sound", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path }),
    }).then((r) => r.json()),
    set_volume: (volume) => fetch("/api/set_volume", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ volume }),
    }).then((r) => r.json()),
    play_alert: (kind) => fetch("/api/play_alert", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ kind }),
    }).then((r) => r.json()),
    open_url: (url) => fetch("/api/open_url", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    }).then((r) => r.json()),
    open_chart: (ticker) => fetch("/api/open_chart", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ticker }),
    }).then((r) => r.json()),
    pop_tape: () => fetch("/api/pop_tape", { method: "POST" }).then((r) => r.json()),
    refresh: () => fetch("/api/refresh", { method: "POST" }).then((r) => r.json()).catch(() => {}),
    select_symbol: (ticker) => fetch("/api/select_symbol", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ticker }),
    }).then((r) => r.json()),
    set_on_top: (on) => fetch("/api/set_on_top", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ on }),
    }).then((r) => r.json()),
    clear_tape: () => fetch("/api/clear_tape", { method: "POST" }).then((r) => r.json()),
  };

  const App = {
    config: null,
    sounds: [],
    on(event, payload) {
      if (event === "config") {
        if (App._saveT || Date.now() - App._lastSave < 1500) return;
        App.config = payload;
      }
      (handlers[event] || []).forEach((fn) => {
        try { fn(payload); } catch (e) { console.error(event, e); }
      });
    },
    sub(event, fn) { (handlers[event] = handlers[event] || []).push(fn); },
    api() { return _api; },
    ready: Promise.resolve(),
    _saveT: null,
    _lastSave: 0,
    saveConfig(immediate) {
      clearTimeout(App._saveT);
      const go = () => { App._saveT = null; App._lastSave = Date.now(); App.api().save_config(App.config); };
      if (immediate) go(); else App._saveT = setTimeout(go, 250);
    },
  };
  window.App = App;

  const U = {
    $: (s, el = document) => el.querySelector(s),
    $$: (s, el = document) => Array.from(el.querySelectorAll(s)),
    el(tag, attrs = {}, ...kids) {
      const e = document.createElement(tag);
      for (const [k, v] of Object.entries(attrs)) {
        if (k === "class") e.className = v;
        else if (k === "html") e.innerHTML = v;
        else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
        else if (v !== undefined && v !== null && v !== false) e.setAttribute(k, v);
      }
      kids.flat().forEach((k) => k != null && e.append(k.nodeType ? k : document.createTextNode(k)));
      return e;
    },
    esc: (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])),
    big(v, dp = 2) {
      if (v == null || isNaN(v)) return "—";
      const a = Math.abs(v);
      if (a >= 1e12) return (v / 1e12).toFixed(dp) + "T";
      if (a >= 1e9) return (v / 1e9).toFixed(dp) + "B";
      if (a >= 1e6) return (v / 1e6).toFixed(dp) + "M";
      if (a >= 1e3) return (v / 1e3).toFixed(dp) + "K";
      return (+v).toFixed(a < 10 && v % 1 ? dp : 0);
    },
    price(v) {
      if (v == null || isNaN(v)) return "—";
      return v < 1 ? v.toFixed(4) : v.toFixed(2);
    },
    pct(v, sign = true) {
      if (v == null || isNaN(v)) return "—";
      return (sign && v > 0 ? "+" : "") + v.toFixed(2) + "%";
    },
    dec(v, dp = 2) { return v == null || isNaN(v) ? "—" : (+v).toFixed(dp); },
    cls(v) { return v == null ? "" : v > 0 ? "up" : v < 0 ? "down" : ""; },
    parseNum(s) {
      if (s == null) return null;
      s = String(s).trim().replace(/[,$%\s]/g, "").toUpperCase();
      if (!s) return null;
      const m = s.match(/^(-?\d*\.?\d+)([KMBT]?)$/);
      if (!m) return null;
      return +m[1] * ({ "": 1, K: 1e3, M: 1e6, B: 1e9, T: 1e12 }[m[2]]);
    },
    fmtInput(v) { return v == null ? "" : U.big(v, v >= 1e3 && v % 1e3 ? 2 : 0).replace(/\.00(?=[KMBT])/, ""); },
    timeET(ts, secs = true) {
      if (!ts) return "—";
      return new Date(ts * 1000).toLocaleTimeString("en-US", {
        timeZone: "America/New_York", hour: "numeric", minute: "2-digit", second: secs ? "2-digit" : undefined,
      }).toLowerCase();
    },
    timeTape(ts) {
      if (!ts) return "—";
      const d = new Date(ts * 1000);
      const now = new Date();
      const optDate = { timeZone: "America/New_York", year: "numeric", month: "numeric", day: "numeric" };
      const dStr = d.toLocaleDateString("en-US", optDate);
      const nowStr = now.toLocaleDateString("en-US", optDate);
      if (dStr === nowStr) {
        return d.toLocaleTimeString("en-US", {
          timeZone: "America/New_York", hour: "numeric", minute: "2-digit", second: "2-digit",
        }).toLowerCase();
      }
      const datePart = d.toLocaleDateString("en-US", { timeZone: "America/New_York", month: "short", day: "numeric" });
      const timePart = d.toLocaleTimeString("en-US", { timeZone: "America/New_York", hour: "numeric", minute: "2-digit" }).toLowerCase();
      return `${datePart} ${timePart}`;
    },
    fullDateET(ts) {
      if (!ts) return "";
      return new Date(ts * 1000).toLocaleString("en-US", {
        timeZone: "America/New_York",
        weekday: "short",
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
        second: "2-digit",
      }) + ` ET (${U.ago(ts)})`;
    },
    ago(ts) {
      const s = Math.max(0, Date.now() / 1000 - ts);
      if (s < 60) return Math.floor(s) + "s ago";
      if (s < 3600) return Math.floor(s / 60) + "m ago";
      if (s < 86400) return Math.floor(s / 3600) + "h " + Math.floor((s % 3600) / 60) + "m ago";
      return Math.floor(s / 86400) + "d ago";
    },
    logo(logoid, symbol) {
      const box = U.el("span", { class: "logo" });
      if (logoid) {
        const img = U.el("img", { src: `https://s3-symbol-logo.tradingview.com/${logoid}.svg`, loading: "lazy" });
        img.onerror = () => { box.textContent = (symbol || "?")[0]; };
        box.append(img);
      } else box.textContent = (symbol || "?")[0];
      return box;
    },
    closePops() { U.$$(".pop").forEach((p) => p.remove()); },
    pop(anchor, content, opts = {}) {
      U.closePops();
      const p = U.el("div", { class: "pop" });
      p.append(content);
      document.body.append(p);
      const r = anchor.getBoundingClientRect();
      let x = opts.right ? r.right - p.offsetWidth : r.left;
      let y = r.bottom + 6;
      if (y + p.offsetHeight > innerHeight - 8) y = Math.max(8, r.top - p.offsetHeight - 6);
      x = Math.min(Math.max(8, x), innerWidth - p.offsetWidth - 8);
      p.style.left = x + "px"; p.style.top = y + "px";
      setTimeout(() => {
        const close = (e) => {
          if (!p.contains(e.target)) { p.remove(); document.removeEventListener("mousedown", close); opts.onClose && opts.onClose(); }
        };
        document.addEventListener("mousedown", close);
      });
      return p;
    },
    toast(kind, title, sub, onclick, ms = 8000) {
      let host = U.$(".toasts");
      if (!host) { host = U.el("div", { class: "toasts" }); document.body.append(host); }
      const t = U.el("div", { class: "toast " + kind },
        U.el("div", {}, U.el("div", { class: "t-title" }, title), sub ? U.el("div", { class: "t-sub" }, sub) : null));
      t.onclick = () => { onclick && onclick(); t.remove(); };
      host.append(t);
      while (host.children.length > 5) host.firstChild.remove();
      setTimeout(() => t.remove(), ms);
    },
    icons: {
      bell: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg>',
      bellOff: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8.7 3A6 6 0 0 1 18 8a21.3 21.3 0 0 0 .6 5"/><path d="M17 17H3s3-2 3-9a4.67 4.67 0 0 1 .3-1.7"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/><path d="m2 2 20 20"/></svg>',
      volHigh: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>',
      volLow: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>',
      volMute: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><line x1="23" y1="9" x2="17" y2="15"/><line x1="17" y1="9" x2="23" y2="15"/></svg>',
      gear: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>',
      list: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/></svg>',
      pause: '<svg viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="5" width="4" height="14" rx="1"/><rect x="14" y="5" width="4" height="14" rx="1"/></svg>',
      play: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M7 5v14l11-7z"/></svg>',
      popout: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 3h6v6M10 14 21 3M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/></svg>',
      refresh: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-2.64-6.36L21 8"/><path d="M21 3v5h-5"/></svg>',
      chart: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m7 15 4-4 3 3 5-6"/></svg>',
      filter: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 3H2l8 9.46V19l4 2v-8.54z"/></svg>',
      bolt: '<svg viewBox="0 0 24 24" fill="#fff"><path d="M13 2 3 14h9l-1 8 10-12h-9z"/></svg>',
    },
  };
  window.U = U;

  document.addEventListener("click", (e) => {
    const a = e.target.closest("a[href]");
    if (a && /^https?:/.test(a.getAttribute("href"))) {
      e.preventDefault();
      App.api().open_url(a.getAttribute("href"));
    }
  });

  let _isFocused = true;
  window.addEventListener("focus", () => {
    if (!_isFocused) {
      _isFocused = true;
      App.api().set_focused(true);
    }
  });
  window.addEventListener("blur", () => {
    if (_isFocused) {
      _isFocused = false;
      App.api().set_focused(false);
    }
  });
})();
