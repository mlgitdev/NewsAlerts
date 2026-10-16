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
    U.$("#btn-mute").onclick = toggleMute;
    U.$("#btn-alerts").onclick = toggleDrawer;
    U.$("#btn-settings").onclick = () => Settings.open();

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

  function toggleMute() {
    App.config.alerts.mute = !App.config.alerts.mute;
    updateMuteBtn();
    App.saveConfig(true);
  }

  function updateMuteBtn() {
    const btn = U.$("#btn-mute");
    const m = App.config.alerts.mute;
    btn.innerHTML = m ? U.icons.bellOff : U.icons.bell;
    btn.classList.toggle("active", m);
    btn.title = m ? "Muted (click to unmute)" : "Sound on (click to mute)";
  }

  function onConfig(c) {
    App.config = c;
    updateMuteBtn();
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

  window.addEventListener("DOMContentLoaded", init);
})();
