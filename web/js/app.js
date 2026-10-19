/* Main application coordinator: boots modules, wires splitters, status bar, and alert drawer. */
(function () {
  const alertsLog = [];
  let unreadAlerts = 0;

  async function init() {
    await App.ready;
    const state = await App.api().get_state();
    App.config = state.config;
    App.sounds = state.sounds;
    App.alpaca_active = state.alpaca_active;
    App.alpaca_key_masked = state.alpaca_key_masked;
    App.version = state.version || "2.4.4";
    App.semver = state.semver || { major: 2, minor: 4, patch: 4 };

    renderVersionBadges(App.version);
    Settings.applyUi();

    // Mount core panels
    Screener.mount();
    News.mount();
    Tape.mount(U.$("#tape-host"), { popout: false });

    // Load initial cached data
    if (state.screener && state.screener.rows) {
      Screener.data = state.screener;
      Screener.renderTable();
    }
    if (state.tape) {
      Tape.load(state.tape);
    }
    if (state.status) {
      updateStatus(state.status);
      updateTvStatus(state.status);
    } else if (state.tv_connected !== undefined) {
      updateTvStatus(state);
    }
    const tvBadge = U.$("#tv-status-badge");
    if (tvBadge) {
      tvBadge.onclick = () => Settings.open("tv");
    }
    setTapePopped(state.tape_popped);

    // Topbar wiring
    initVolumeControl();
    U.$("#btn-mute").onclick = toggleMute;
    U.$("#btn-alerts").onclick = toggleDrawer;
    U.$("#btn-settings").onclick = () => Settings.open();
    const brand = U.$("#btn-brand-about") || U.$(".brand");
    if (brand) {
      const openAbout = () => Settings.open("about");
      brand.onclick = openAbout;
      brand.onkeydown = (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          openAbout();
        }
      };
    }

    // Keyboard Shortcuts & Hotkeys Coordinator
    initHotkeys();

    // Event subscriptions from Python
    App.sub("status", (st) => {
      updateStatus(st);
      updateTvStatus(st);
    });
    App.sub("tv_auth", (auth) => {
      updateTvStatus({
        tv_connected: auth.connected,
        tv_username: auth.username,
        tv_pro_plan: auth.pro_plan,
        tv_error: auth.error,
      });
    });
    App.sub("new_symbols", onNewSymbols);
    App.sub("tape_popped", setTapePopped);
    App.sub("config", onConfig);

    initSplitters();

    lastEventId = state.last_event_id || 0;
    startEventPolling();
  }

  let lastEventId = 0;
  async function startEventPolling() {
    while (true) {
      try {
        const events = await App.api().poll_events(lastEventId);
        if (events && events.length) {
          for (const ev of events) {
            if (ev.id > lastEventId) lastEventId = ev.id;
            App.on(ev.event, ev.payload);
          }
        }
      } catch (e) {
        await new Promise((r) => setTimeout(r, 1000));
      }
      await new Promise((r) => setTimeout(r, 350));
    }
  }

  function updateTvStatus(st) {
    const badge = U.$("#tv-status-badge");
    const txt = U.$("#tv-status-text");
    if (!badge || !txt) return;
    const connected = !!st.tv_connected;
    badge.className = "pill tv-status-pill " + (connected ? "connected" : "disconnected");
    if (connected) {
      txt.textContent = "TradingView — Connected";
      const u = st.tv_username ? ` as ${st.tv_username}` : "";
      const p = st.tv_pro_plan ? ` (${st.tv_pro_plan})` : "";
      badge.title = `TradingView: Connected${u}${p} · Real-time streaming active (click for settings)`;
    } else {
      txt.textContent = "TradingView — Disconnected";
      const err = st.tv_error ? `: ${st.tv_error}` : " (cookies invalid or expired)";
      badge.title = `TradingView: Disconnected${err} · Click to update session cookies in Settings`;
    }
  }

  function updateStatus(st) {
    Screener.status = st;
    const dot = U.$("#status-dot");
    const txt = U.$("#status-text");
    if (!st.ok) {
      dot.className = "dot err";
      txt.textContent = st.error || "Disconnected";
      return;
    }
    dot.className = "dot ok";
    const rt = st.realtime ? "RT" : "15m";
    const sess = (st.market || "open").toUpperCase();
    txt.textContent = `${rt} · ${sess} · ${st.et || ""}`;
  }

  let _lastNonZeroVol = 80;
  let _volDebounceTimer = null;

  function renderVolume(vol) {
    vol = Math.max(0, Math.min(100, Math.round(vol)));
    const clipRect = U.$("#vol-clip-rect");
    const label = U.$("#vol-label");
    const btn = U.$("#btn-vol");
    if (clipRect) {
      clipRect.setAttribute("width", ((vol / 100) * 64).toFixed(1));
    }
    if (label) {
      label.textContent = `${vol}%`;
    }
    if (btn) {
      if (vol === 0) {
        btn.innerHTML = U.icons.volMute;
        btn.title = "Volume: 0% (Muted) — Click to restore";
      } else if (vol <= 50) {
        btn.innerHTML = U.icons.volLow;
        btn.title = `Volume: ${vol}% — Click to mute`;
      } else {
        btn.innerHTML = U.icons.volHigh;
        btn.title = `Volume: ${vol}% — Click to mute`;
      }
    }
  }

  function setVolume(vol, save = false) {
    vol = Math.max(0, Math.min(100, Math.round(vol)));
    if (!App.config) App.config = {};
    if (!App.config.alerts) App.config.alerts = {};
    if (vol > 0) _lastNonZeroVol = vol;
    App.config.alerts.volume = vol;
    renderVolume(vol);

    clearTimeout(_volDebounceTimer);
    if (save) {
      App.api().set_volume(vol).catch(() => {});
      App.saveConfig(true);
    } else {
      _volDebounceTimer = setTimeout(() => {
        App.api().set_volume(vol).catch(() => {});
      }, 40);
    }
  }

  function initVolumeControl() {
    const track = U.$("#vol-bar-track");
    const btnVol = U.$("#btn-vol");
    const initialVol = App.config?.alerts?.volume !== undefined ? App.config.alerts.volume : 80;
    if (initialVol > 0) _lastNonZeroVol = initialVol;
    renderVolume(initialVol);

    if (btnVol) {
      btnVol.onclick = () => {
        const cur = App.config?.alerts?.volume !== undefined ? App.config.alerts.volume : 80;
        if (cur > 0) {
          _lastNonZeroVol = cur;
          setVolume(0, true);
        } else {
          setVolume(_lastNonZeroVol || 80, true);
        }
      };
    }

    if (track) {
      function getVolFromEvent(e) {
        const r = track.getBoundingClientRect();
        const x = Math.max(0, Math.min(r.width, e.clientX - r.left));
        return Math.round((x / r.width) * 100);
      }

      track.onmousedown = (e) => {
        e.preventDefault();
        const vol = getVolFromEvent(e);
        setVolume(vol, false);

        const onMove = (moveEv) => {
          setVolume(getVolFromEvent(moveEv), false);
        };
        const onUp = (upEv) => {
          window.removeEventListener("mousemove", onMove);
          window.removeEventListener("mouseup", onUp);
          setVolume(getVolFromEvent(upEv), true);
        };
        window.addEventListener("mousemove", onMove);
        window.addEventListener("mouseup", onUp);
      };
    }
  }

  function toggleMute() {
    App.config.alerts.mute = !App.config.alerts.mute;
    updateMuteBtn();
    App.saveConfig(true);
  }

  function updateMuteBtn() {
    const btn = U.$("#btn-mute");
    if (!btn) return;
    const isPaused = !!App.config?.alerts?.mute;
    btn.innerHTML = isPaused ? U.icons.bellOff : U.icons.bell;
    btn.classList.toggle("paused", isPaused);
    btn.classList.toggle("active", isPaused);
    btn.title = isPaused
      ? "Alerts PAUSED (Sound & Telegram suppressed) — Click to resume"
      : "Alerts ACTIVE (Sound & Telegram enabled) — Click to pause";
  }

  function onConfig(c) {
    App.config = c;
    updateMuteBtn();
    if (c.alerts?.volume !== undefined) {
      renderVolume(c.alerts.volume);
    }
    Settings.applyUi();
  }

  function onNewSymbols(p) {
    const syms = p.symbols || [];
    if (!syms.length) return;
    const sNames = syms.map((s) => s.symbol).join(", ");
    unreadAlerts += syms.length;
    document.title = `(${unreadAlerts}) NewsAlerts — Momentum Screener`;
    U.$("#alerts-badge").textContent = unreadAlerts || "";

    syms.forEach((s) => {
      alertsLog.unshift({ ts: p.ts || Date.now() / 1000, screen: p.screen_name, symbol: s });
    });
    while (alertsLog.length > 200) alertsLog.pop();

    U.toast(
      "alert",
      `🔔 ${p.screen_name}: ${sNames}`,
      `${syms.length} new symbol(s) popped up`,
      () => {
        Screener.select(syms[0].ticker);
      },
      9000
    );
    renderDrawer();
  }

  function toggleDrawer() {
    const d = U.$("#alerts-drawer");
    const show = !d.classList.contains("show");
    d.classList.toggle("show", show);
    if (show) {
      unreadAlerts = 0;
      document.title = "NewsAlerts — Momentum Screener";
      U.$("#alerts-badge").textContent = "";
      renderDrawer();
    }
  }

  function renderDrawer() {
    const list = U.$("#drawer-list");
    list.replaceChildren();
    if (!alertsLog.length) {
      list.append(U.el("div", { class: "empty", style: "padding:20px" }, "No symbol alerts recorded yet."));
      return;
    }
    alertsLog.forEach((item) => {
      const s = item.symbol;
      const b = s.borrow || { status: "na", label: "N/A" };
      const el = U.el(
        "div",
        { class: "d-item" },
        U.el("span", { class: "d-time" }, U.timeET(item.ts)),
        U.logo(s.logoid, s.symbol),
        U.el("strong", {}, s.symbol),
        U.el("span", { class: "tag-borrow " + b.status }, b.label),
        U.el("span", { class: "num " + U.cls(s.sc), style: "margin-left:auto" }, U.pct(s.sc)),
        U.el("span", { class: "muted", style: "font-size:11px" }, item.screen)
      );
      el.onclick = () => {
        Screener.select(s.ticker);
        U.$("#alerts-drawer").classList.remove("show");
      };
      list.append(el);
    });
  }

  function setTapePopped(popped) {
    const main = U.$("#main-grid");
    if (!main) return;
    main.classList.toggle("tape-hidden", !!popped);
  }

  function initSplitters() {
    const sv = U.$("#split-v");
    const sh = U.$("#split-h");
    const root = document.documentElement;

    // Restore saved sizes
    if (App.config.ui.news_width) root.style.setProperty("--news-w", App.config.ui.news_width + "px");
    if (App.config.ui.tape_height) root.style.setProperty("--tape-h", App.config.ui.tape_height + "px");

    // Vertical splitter (Screener vs News)
    sv.addEventListener("mousedown", (e) => {
      e.preventDefault();
      const startX = e.clientX;
      const startW = parseInt(getComputedStyle(root).getPropertyValue("--news-w")) || 420;
      const onMove = (ev) => {
        const nw = Math.max(280, Math.min(800, startW - (ev.clientX - startX)));
        root.style.setProperty("--news-w", nw + "px");
        App.config.ui.news_width = nw;
      };
      const onUp = () => {
        window.removeEventListener("mousemove", onMove);
        window.removeEventListener("mouseup", onUp);
        App.saveConfig();
      };
      window.addEventListener("mousemove", onMove);
      window.addEventListener("mouseup", onUp);
    });

    // Horizontal splitter (Upper vs Tape)
    sh.addEventListener("mousedown", (e) => {
      e.preventDefault();
      const startY = e.clientY;
      const startH = parseInt(getComputedStyle(root).getPropertyValue("--tape-h")) || 300;
      const onMove = (ev) => {
        const nh = Math.max(140, Math.min(window.innerHeight - 200, startH - (ev.clientY - startY)));
        root.style.setProperty("--tape-h", nh + "px");
        App.config.ui.tape_height = nh;
      };
      const onUp = () => {
        window.removeEventListener("mousemove", onMove);
        window.removeEventListener("mouseup", onUp);
        App.saveConfig();
      };
      window.addEventListener("mousemove", onMove);
      window.addEventListener("mouseup", onUp);
    });
  }

  function initHotkeys() {
    document.addEventListener("keydown", (e) => {
      // Do not intercept if modifier keys like Ctrl / Alt / Meta are held
      if (e.ctrlKey || e.altKey || e.metaKey) return;

      const tag = document.activeElement ? document.activeElement.tagName : "";
      const isEditable = /INPUT|SELECT|TEXTAREA/.test(tag) || (document.activeElement && document.activeElement.isContentEditable);

      // ESCAPE key: always allow Esc to close modal/drawer/story or unfocus active input
      if (e.key === "Escape") {
        if (isEditable) {
          document.activeElement.blur();
          e.preventDefault();
          return;
        }
        let handled = false;
        if (window.Settings && Settings.isOpen && Settings.isOpen()) {
          Settings.close();
          handled = true;
        }
        const drawer = U.$("#alerts-drawer");
        if (drawer && drawer.classList.contains("show")) {
          drawer.classList.remove("show");
          handled = true;
        }
        if (window.News && News.closeAllStories && News.open && News.open.size > 0) {
          News.closeAllStories();
          handled = true;
        }
        if (handled) e.preventDefault();
        return;
      }

      // If user is actively typing in an input/select/textarea, ignore terminal hotkeys
      if (isEditable) return;

      const k = e.key;

      // 1 – 5: Switch screener tab presets
      if (k >= "1" && k <= "5") {
        const idx = parseInt(k, 10) - 1;
        if (App.config?.screens && App.config.screens[idx]) {
          e.preventDefault();
          Screener.switchTab(App.config.screens[idx].id);
        }
        return;
      }

      // M / m: Master Mute
      if (k === "m" || k === "M") {
        e.preventDefault();
        toggleMute();
        const isMuted = !!App.config?.alerts?.mute;
        U.toast(
          "info",
          isMuted ? "🔔 Alerts Muted" : "🔔 Alerts Active",
          isMuted ? "Audio chimes & Telegram alerts paused" : "Audio chimes & Telegram alerts active",
          null,
          2500
        );
        return;
      }

      // T / t: Pop-Out Tape
      if (k === "t" || k === "T") {
        e.preventDefault();
        App.api().pop_tape();
        U.toast("info", "⚡ Pop-Out Tape", "Opening detached floating tape window", null, 2500);
        return;
      }

      // Space: Pause / Resume tape stream
      if (k === " ") {
        e.preventDefault();
        Tape.setPaused(!Tape.paused);
        U.toast(
          "info",
          Tape.paused ? "⏸ Tape Stream Paused" : "▶ Tape Stream Resumed",
          Tape.paused ? "Incoming tape momentum events held in buffer" : "Tape momentum stream running",
          null,
          2500
        );
        return;
      }

      // S / s: Open / Toggle Settings Modal
      if (k === "s" || k === "S") {
        e.preventDefault();
        if (window.Settings && Settings.isOpen && Settings.isOpen()) {
          Settings.close();
        } else if (window.Settings && Settings.open) {
          Settings.open();
        }
        return;
      }

      // R / r: Force Refresh
      if (k === "r" || k === "R") {
        e.preventDefault();
        if (App.api().refresh) App.api().refresh();
        if (window.News && News.ticker) {
          News.load(true);
        }
        U.toast("info", "🔄 Force Refresh", "Re-scanning screener and refreshing news headlines", null, 2500);
        return;
      }

      // Enter: Focus / expand first catalyst story
      if (k === "Enter") {
        if (window.News && News.openFirstStory && News.openFirstStory()) {
          e.preventDefault();
        }
        return;
      }
    });
  }

  function renderVersionBadges(ver) {
    const formatted = ver.startsWith("v") ? ver : `v${ver}`;
    const cornerEl = U.$("#corner-version-text");
    if (cornerEl) cornerEl.textContent = formatted;
    const brandEl = U.$("#brand-version");
    if (brandEl) brandEl.textContent = formatted;
    const cornerBadge = U.$("#corner-version-badge");
    if (cornerBadge) {
      cornerBadge.onclick = () => Settings.open("about");
      cornerBadge.title = `NewsAlerts ${formatted} (SemVer 2.0.0) — Click for Details`;
    }
    const brand = U.$("#btn-brand-about") || U.$(".brand");
    if (brand) {
      brand.title = `NewsAlerts ${formatted} (SemVer 2.0.0) — Click to view About & System Info`;
    }
  }

  window.addEventListener("DOMContentLoaded", init);
})();
