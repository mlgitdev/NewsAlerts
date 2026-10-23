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
    App.version = state.version || "";
    App.semver = state.semver || null;
    App.app_dir = state.app_dir || "";
    App.secrets_file = state.secrets_file || "";
    App.has_keys_toml = !!state.has_keys_toml;

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
    initWatchlistControl();
    initFilterBannedControl();
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
      if (App.reloadWatchlists) App.reloadWatchlists();
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
    updateFilterBannedButton();
    if (c.alerts?.volume !== undefined) {
      renderVolume(c.alerts.volume);
    }
    Settings.applyUi();
  }

  function updateFilterBannedButton() {
    const btn = U.$("#btn-filter-banned");
    const txt = U.$("#filter-banned-text");
    if (!btn || !txt) return;
    const active = !!(App.config && App.config.filter_banned);
    const count = (App.config && App.config.banned_symbols) ? App.config.banned_symbols.length : 0;
    btn.classList.toggle("banned-on", active);
    btn.classList.toggle("active", active);
    txt.textContent = active ? `Banned: ON (${count})` : `Banned: OFF`;
    btn.title = active
      ? `IB Closing-Only Filter ACTIVE (${count} symbol(s) hidden). Click to show all.`
      : `IB Closing-Only Filter OFF. Click to hide ${count} banned / closing-only symbol(s).`;
  }

  App.updateFilterBannedButton = updateFilterBannedButton;

  function initFilterBannedControl() {
    const btn = U.$("#btn-filter-banned");
    if (btn) {
      btn.onclick = async () => {
        const current = !!(App.config && App.config.filter_banned);
        const next = !current;
        App.config.filter_banned = next;
        updateFilterBannedButton();
        await App.api().toggle_filter_banned(next);
        U.toast(
          next ? "info" : "muted",
          `Closing-Only Filter ${next ? "ON" : "OFF"}`,
          next
            ? `Hiding ${App.config.banned_symbols?.length || 0} banned symbols from Screener & Tape.`
            : `Showing all symbols on Screener & Tape.`
        );
        Screener.renderTable();
        Tape.renderAll();
      };
    }
    updateFilterBannedButton();
  }

  App.banSymbol = async function (symbol) {
    const sym = String(symbol || "").split(":").pop().trim().toUpperCase();
    if (!sym) return;
    App.config.banned_symbols = App.config.banned_symbols || [];
    if (!App.config.banned_symbols.includes(sym)) {
      App.config.banned_symbols.push(sym);
      await App.api().ban_symbol(sym);
      U.toast(
        "warn",
        `🚫 Symbol Banned: ${sym}`,
        App.config.filter_banned
          ? `${sym} added to banned list and hidden from Screener & Tape.`
          : `${sym} added to banned list. Turn ON the topbar 🚫 Banned filter to hide it.`,
        null,
        3500
      );
      updateFilterBannedButton();
      Screener.renderTable();
      Tape.renderAll();
      if (window.News && News.renderHead) News.renderHead();
    } else {
      U.toast("info", `${sym} already in banned list`, `Symbol is already cataloged in Closing-Only list.`);
    }
  };

  App.unbanSymbol = async function (symbol) {
    const sym = String(symbol || "").split(":").pop().trim().toUpperCase();
    if (!sym) return;
    App.config.banned_symbols = App.config.banned_symbols || [];
    const idx = App.config.banned_symbols.indexOf(sym);
    if (idx !== -1) {
      App.config.banned_symbols.splice(idx, 1);
      await App.api().unban_symbol(sym);
      U.toast("info", `Unbanned: ${sym}`, `${sym} removed from banned list.`);
      updateFilterBannedButton();
      Screener.renderTable();
      Tape.renderAll();
      if (window.News && News.renderHead) News.renderHead();
    }
  };


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

      const hk = App.config?.hotkeys || {};
      const matchKey = (action, defaultKey) => {
        const configured = (hk[action] !== undefined && hk[action] !== "") ? hk[action] : defaultKey;
        if (!configured) return false;
        const normKey = e.key === " " ? "Space" : e.key;
        const normCfg = configured === " " ? "Space" : configured;
        return normKey.toLowerCase() === normCfg.toLowerCase();
      };

      // ESCAPE key / configured close_modal: always allow Esc to close modal/drawer/story or unfocus active input
      if (matchKey("close_modal", "Escape") || e.key === "Escape") {
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

      // 1 – 5: Switch screener tab presets
      for (let i = 1; i <= 5; i++) {
        if (matchKey(`preset_${i}`, String(i))) {
          const idx = i - 1;
          if (App.config?.screens && App.config.screens[idx]) {
            e.preventDefault();
            Screener.switchTab(App.config.screens[idx].id);
          }
          return;
        }
      }

      // Master Mute
      if (matchKey("mute", "m")) {
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

      // Pop-Out Tape
      if (matchKey("popout_tape", "t")) {
        e.preventDefault();
        App.api().pop_tape();
        U.toast("info", "⚡ Pop-Out Tape", "Opening detached floating tape window", null, 2500);
        return;
      }

      // Space / configured pause_tape: Pause / Resume tape stream
      if (matchKey("pause_tape", "Space") || e.key === " ") {
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

      // Open / Toggle Settings Modal
      if (matchKey("settings", "s")) {
        e.preventDefault();
        if (window.Settings && Settings.isOpen && Settings.isOpen()) {
          Settings.close();
        } else if (window.Settings && Settings.open) {
          Settings.open();
        }
        return;
      }

      // Force Refresh
      if (matchKey("refresh", "r")) {
        e.preventDefault();
        if (App.api().refresh) App.api().refresh();
        if (window.News && News.ticker) {
          News.load(true);
        }
        U.toast("info", "🔄 Force Refresh", "Re-scanning screener and refreshing news headlines", null, 2500);
        return;
      }

      // Focus / expand first catalyst story
      if (matchKey("focus_story", "Enter") || e.key === "Enter") {
        if (window.News && News.openFirstStory && News.openFirstStory()) {
          e.preventDefault();
        }
        return;
      }
    });
  }

  async function initWatchlistControl() {
    const select = U.$("#watchlist-select");
    const syncBtn = U.$("#btn-watchlist-sync");
    const badge = U.$("#watchlist-status-badge");
    if (!select) return;

    async function loadWatchlists(silent = false) {
      if (syncBtn && !silent) syncBtn.classList.add("rotating");
      try {
        const res = await App.api().get_watchlists();
        if (select) {
          const currentVal = select.value || (res && res.active_id) || "";
          select.replaceChildren();
          const wls = res.watchlists || [];
          if (!wls.length) {
            select.append(U.el("option", { value: "" }, "No watchlists found"));
          } else {
            let matched = false;
            wls.forEach((w) => {
              const opt = U.el("option", { value: w.id }, `${w.title} (${w.count || 0})`);
              if (w.id === currentVal) {
                opt.selected = true;
                matched = true;
              }
              select.append(opt);
            });
            if (matched) {
              select.value = currentVal;
            } else if (res.active_id) {
              select.value = res.active_id;
            } else if (wls[0]) {
              select.value = wls[0].id;
            }
          }
        }
        if (badge) {
          if (res.connected) {
            badge.textContent = "TV Cloud";
            badge.className = "watchlist-status-badge";
            badge.title = "Synchronized with TradingView Cloud Watchlists";
            badge.onclick = null;
          } else {
            badge.textContent = "Local";
            badge.className = "watchlist-status-badge local";
            badge.title = "TradingView session not active — using local watchlist (Click for Settings)";
            badge.onclick = () => Settings.open("tv");
          }
        }
      } catch (e) {
        if (badge) {
          badge.textContent = "Offline";
          badge.className = "watchlist-status-badge local";
        }
      } finally {
        if (syncBtn && !silent) syncBtn.classList.remove("rotating");
      }
    }

    App.reloadWatchlists = loadWatchlists;

    select.onchange = async () => {
      const selectedId = select.value;
      const selectedTitle = select.options[select.selectedIndex]?.text?.replace(/\s*\(\d+\)$/, "") || "";
      if (!App.config) App.config = {};
      if (!App.config.watchlist) App.config.watchlist = {};
      App.config.watchlist.active_id = selectedId;
      App.config.watchlist.active_title = selectedTitle;
      try {
        await App.api().select_watchlist(selectedId, selectedTitle);
      } catch (e) {}
    };

    if (syncBtn) {
      syncBtn.onclick = () => {
        loadWatchlists(false);
        U.toast("info", "🔄 Watchlists Synced", "Refreshed TradingView custom watchlists", null, 2000);
      };
    }

    // Auto-refresh watchlist synchronization every 5 minutes (300,000 ms)
    if (App._wlInterval) clearInterval(App._wlInterval);
    App._wlInterval = setInterval(() => {
      loadWatchlists(true);
    }, 5 * 60 * 1000);

    await loadWatchlists(false);
  }

  async function handleAddToWatchlist(btn, symbol) {
    if (!symbol || !btn) return;
    if (btn.classList.contains("adding") || btn.classList.contains("flicker-green") || btn.classList.contains("flicker-red")) {
      return;
    }
    const select = U.$("#watchlist-select");
    const activeId = select ? select.value : (App.config?.watchlist?.active_id || "");
    const origText = btn.textContent;
    btn.classList.add("adding");

    try {
      const res = await App.api().add_to_watchlist(activeId, symbol);
      btn.classList.remove("adding");

      if (res && res.ok) {
        // Success or already exists: silent green flickering for 3 seconds
        btn.classList.add("flicker-green");
        btn.textContent = "✓";
        if (select && select.options[select.selectedIndex] && !res.already_exists) {
          const opt = select.options[select.selectedIndex];
          const m = opt.textContent.match(/^(.*?)\s*\((\d+)\)$/);
          if (m) {
            opt.textContent = `${m[1]} (${parseInt(m[2], 10) + 1})`;
          }
        }
        setTimeout(() => {
          btn.classList.remove("flicker-green");
          btn.textContent = origText;
        }, 3000);
      } else {
        // Failure: red flickering for 3 seconds + alert popup toast
        btn.classList.add("flicker-red");
        btn.textContent = "✕";
        setTimeout(() => {
          btn.classList.remove("flicker-red");
          btn.textContent = origText;
        }, 3000);
        U.toast(
          "err",
          "⚠️ Failed to Add to Watchlist",
          res?.message || res?.error || "Could not add symbol to TradingView watchlist. Please check session cookies.",
          null,
          5000
        );
      }
    } catch (err) {
      btn.classList.remove("adding");
      btn.classList.add("flicker-red");
      btn.textContent = "✕";
      setTimeout(() => {
        btn.classList.remove("flicker-red");
        btn.textContent = origText;
      }, 3000);
      U.toast(
        "err",
        "⚠️ Failed to Add to Watchlist",
        String(err.message || err),
        null,
        5000
      );
    }
  }

  App.handleAddToWatchlist = handleAddToWatchlist;

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
