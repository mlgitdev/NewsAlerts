/* Settings modal: TradingView login, polling, sounds, news, tape strategies. */
(function () {
  const STRAT_COLS = [["float_min", "Float ≥"], ["float_max", "Float <"], ["relvol_min", "RelVol ≥"], ["relvol_max", "RelVol <"],
    ["price_min", "Price ≥"], ["price_max", "Price <"], ["hi52_ratio_min", "52wH/Px ≥"], ["up_pct", "Up %"], ["window_min", "In min"]];

  const Settings = {
    open(initialTab = "general") {
      const c = JSON.parse(JSON.stringify(App.config));
      Settings.c = c;
      App.api().get_state().then((st) => {
        if (st) {
          App.alpaca_active = st.alpaca_active;
          App.alpaca_key_masked = st.alpaca_key_masked;
        }
      });
      const bg = U.$("#settings");
      const body = U.$("#settings-body");
      const tabs = U.$$("#settings-tabs button");
      const show = (name) => {
        tabs.forEach((b) => b.classList.toggle("active", b.dataset.tab === name));
        body.replaceChildren(Settings["tab_" + name](c));
      };
      tabs.forEach((b) => (b.onclick = () => show(b.dataset.tab)));
      show(initialTab || "general");
      bg.classList.add("show");
      U.$("#settings-save").onclick = () => {
        App.config = c; App.saveConfig(true); Settings.applyUi(); bg.classList.remove("show");
        Screener.renderBar(); Screener.renderTable(); Tape.renderAll(); News.syncTools();
      };
      U.$("#settings-cancel").onclick = () => bg.classList.remove("show");
      U.$("#settings-close").onclick = () => bg.classList.remove("show");
    },

    applyUi() {
      const ui = App.config.ui;
      document.documentElement.style.setProperty("--fs", (ui.font_size || 13) + "px");
      document.documentElement.style.setProperty("--row-h", Math.round((ui.font_size || 13) * 2.3) + "px");
      document.body.classList.toggle("bright", !!ui.tape_bright);
      App.api().set_on_top(!!ui.always_on_top);
    },

    // -- helpers
    field(label, input, help) {
      return [U.el("label", {}, label), input, help ? U.el("div", { class: "help" }, help) : null];
    },
    num(obj, key, opts = {}) {
      const i = U.el("input", { type: "text", class: "numin", value: opts.big ? U.fmtInput(obj[key]) : (obj[key] ?? "") });
      i.oninput = () => { obj[key] = U.parseNum(i.value); };
      return i;
    },
    check(obj, key, label) {
      const i = U.el("input", { type: "checkbox" }); i.checked = !!obj[key];
      i.onchange = () => (obj[key] = i.checked);
      return U.el("label", { style: "display:flex;gap:8px;align-items:center;cursor:pointer" }, i, label || "");
    },
    text(obj, key, type = "text", ph = "") {
      const i = U.el("input", { type, value: obj[key] || "", placeholder: ph, style: "width:100%" });
      i.oninput = () => (obj[key] = i.value.trim());
      return i;
    },
    sound(obj, key) {
      const sel = U.el("select", {}, U.el("option", { value: "" }, "(none)"),
        App.sounds.map((s) => U.el("option", { value: s.path }, s.name)));
      sel.value = obj[key] || "";
      sel.onchange = () => (obj[key] = sel.value);
      const test = U.el("button", { class: "btn sm", onclick: () => App.api().play_sound(sel.value) }, "▶ Test");
      return U.el("div", { class: "sound-row" }, sel, test);
    },

    // -- tabs
    tab_general(c) {
      const g = U.el("div", { class: "form-grid" });
      g.append(U.el("h3", {}, "TradingView login (real-time data)"),
        ...Settings.field("sessionid", Settings.text(c.tv, "sessionid", "password", "paste cookie value"),
          "tradingview.com → F12 → Application → Cookies → copy 'sessionid'. Without it data is ~15 min delayed."),
        ...Settings.field("sessionid_sign", Settings.text(c.tv, "sessionid_sign", "password", "optional")),
        U.el("h3", {}, "Polling"),
        ...Settings.field("Screener refresh (sec)", Settings.num(c.poll, "screener_sec")),
        ...Settings.field("Tape refresh (sec)", Settings.num(c.poll, "tape_sec")),
        ...Settings.field("News refresh (sec)", Settings.num(c.poll, "news_sec")),
        U.el("h3", {}, "Window"),
        ...Settings.field("Always on top", Settings.check(c.ui, "always_on_top")),
        ...Settings.field("Font size (px)", Settings.num(c.ui, "font_size")),
        ...Settings.field("Bright tape colors", Settings.check(c.ui, "tape_bright", "Warrior-style solid row colors")));
      return g;
    },

    tab_alerts(c) {
      const a = c.alerts;
      const g = U.el("div", { class: "form-grid" });
      g.append(U.el("h3", {}, "New symbol in screener (the bell)"),
        ...Settings.field("Sound", Settings.sound(a, "sound_new_symbol")),
        ...Settings.field("Volume (%)", Settings.num(a, "volume"), "Alert chime volume (0% to 100%)."),
        ...Settings.field("Re-entry window (min)", Settings.num(a, "reentry_min"),
          "A symbol that drops out and comes back within this window will not ring again."),
        ...Settings.field("Pause alerts (mute & stop sending)", Settings.check(a, "mute"),
          "When active, sound chimes are muted and Telegram notifications are suppressed."),
        ...Settings.field("Quiet while app focused", Settings.check(a, "quiet_when_focused")),
        U.el("h3", {}, "News"),
        ...Settings.field("Play news sound", Settings.check(a, "news_sound_enabled", "New symbol has fresh news / new headline for selected symbol")),
        ...Settings.field("News sound", Settings.sound(a, "sound_news")),
        U.el("h3", {}, "Tape"),
        ...Settings.field("Play tape sound", Settings.check(a, "tape_sound_enabled", "Fires on every enabled-strategy event (noisy)")),
        ...Settings.field("Tape sound", Settings.sound(a, "sound_tape")),
        U.el("h3", {}, "Telegram Bot Push Alerts"),
        ...Settings.field("Enable Telegram Alerts", Settings.check(a, "telegram_enabled", "Master toggle for Telegram notifications")),
        ...Settings.field("Tape Momentum Alerts", Settings.check(a, "telegram_tape_enabled", "Send push alert when a momentum symbol pops up on the tape (e.g. HOD / Squeeze breakout)")),
        ...Settings.field("Tape Alert Cooldown (sec)", Settings.num(a, "telegram_tape_cooldown_sec"), "Minimum seconds between alerts for the same symbol to prevent spam (default: 60s)"),
        ...Settings.field("Bot Token", Settings.text(a, "telegram_bot_token", "password", "Optional (from @BotFather)"), "Leave blank to read from AppData\\NewsAlerts\\keys.toml or local keys.toml"),
        ...Settings.field("Chat ID", Settings.text(a, "telegram_chat_id", "text", "Optional chat ID (e.g. 526065926)"), "Leave blank to read from keys.toml"),
        ...Settings.field("Test Bot Connection", U.el("button", {
          class: "btn sm primary",
          style: "width:180px",
          onclick: async (e) => {
            const btn = e.target;
            btn.disabled = true;
            btn.textContent = "Sending…";
            try {
              const res = await App.api().send_telegram_test();
              if (res.ok) {
                U.toast("alert", "✈️ Telegram Sent", res.message);
                btn.textContent = "✓ Sent!";
              } else {
                U.toast("alert", "⚠️ Telegram Failed", res.message);
                btn.textContent = "Failed";
              }
            } catch (err) {
              U.toast("alert", "⚠️ Error", String(err));
              btn.textContent = "Error";
            }
            setTimeout(() => { btn.disabled = false; btn.textContent = "✈️ Send Test Message"; }, 2500);
          }
        }, "✈️ Send Test Message"), "Sends a test message using configured credentials or keys.toml"));
      return g;
    },

    tab_news(c) {
      const g = U.el("div", { class: "form-grid" });
      g.append(U.el("h3", {}, "News filter"),
        ...Settings.field("Recency (hours)", Settings.num(c.news, "recency_hours"), "Only show headlines newer than this."),
        ...Settings.field("Benzinga only", Settings.check(c.news, "benzinga_only")),
        U.el("div", { class: "help", style: "grid-column:1/-1;margin:0" },
          "Source: TradingView news feed (includes Benzinga, Dow Jones, Reuters, press releases)."));
      return g;
    },

    tab_tape(c) {
      const t = c.tape;
      const wrap = U.el("div", {});
      const g = U.el("div", { class: "form-grid" });
      g.append(U.el("h3", {}, "Tape universe (stocks watched for events)"),
        ...Settings.field("Price min / max", U.el("div", { class: "sound-row" }, Settings.num(t.universe, "price_min"), Settings.num(t.universe, "price_max"))),
        ...Settings.field("Min session chg %", Settings.num(t.universe, "chg_min")),
        ...Settings.field("Min session volume", Settings.num(t.universe, "vol_min", { big: 1 })),
        ...Settings.field("Max symbols", Settings.num(t.universe, "limit")),
        ...Settings.field("Cooldown per symbol/strategy (sec)", Settings.num(t, "cooldown_sec")),
        ...Settings.field("History retention (days)", Settings.num(t, "retention_days"), "Keeps tape alerts saved on disk for off-hours and weekend review (default: 4 days)."),
        U.el("h3", {}, "Strategies"));
      const tbl = U.el("table", { class: "strat" });
      tbl.append(U.el("tr", {}, U.el("th", {}, "Name"), U.el("th", {}, "Trigger"), STRAT_COLS.map(([, h]) => U.el("th", {}, h))));
      t.strategies.forEach((s) => {
        const name = U.el("input", { type: "text", value: s.name });
        name.onchange = () => {
          const old = s.name; s.name = name.value.trim() || old;
          t.enabled = t.enabled.map((n) => (n === old ? s.name : n));
        };
        const trig = U.el("select", {}, [["hod", "New HOD"], ["52w", "52w breakout"], ["squeeze", "Up X% in N min"]].map(([v, l]) => U.el("option", { value: v }, l)));
        trig.value = s.trigger || "hod";
        trig.onchange = () => (s.trigger = trig.value);
        tbl.append(U.el("tr", {}, U.el("td", { class: "name" }, name), U.el("td", {}, trig),
          STRAT_COLS.map(([k]) => U.el("td", {}, Settings.num(s, k, { big: k.startsWith("float") })))));
      });
      wrap.append(g, tbl, U.el("div", { class: "help muted", style: "margin-top:10px;font-size:12px" },
        "HOD strategies fire when a matching stock prints a new session high. Floats accept K/M suffixes. Blank = no limit."));
      return wrap;
    },

    tab_borrow(c) {
      const b = c.borrow || (c.borrow = { alpaca_key_id: "", alpaca_secret_key: "", mode: "auto" });
      const g = U.el("div", { class: "form-grid" });
      const modeSel = U.el("select", {},
        U.el("option", { value: "auto" }, "Auto (Alpaca if keys set, else Float heuristic)"),
        U.el("option", { value: "alpaca" }, "Alpaca API (Live broker locates)"),
        U.el("option", { value: "heuristic" }, "Float-based Heuristic only"));
      modeSel.value = b.mode || "auto";
      modeSel.onchange = () => (b.mode = modeSel.value);
      const alpacaBanner = App.alpaca_active
        ? U.el("div", {
            style: "grid-column:1/-1;padding:9px 13px;background:rgba(74,222,128,0.12);border:1px solid rgba(74,222,128,0.3);border-radius:6px;color:#4ade80;font-size:12px;font-weight:500;display:flex;align-items:center;gap:8px;",
          }, `✓ Live Alpaca API Active · Auto-loaded from secrets/keys.toml (${App.alpaca_key_masked})`)
        : null;

      const keyHelp = App.alpaca_active
        ? "Auto-loaded from secrets/keys.toml. Leave blank to keep using keys.toml, or enter here to override."
        : "Free at alpaca.markets (API Keys section)";

      g.append(
        alpacaBanner,
        U.el("h3", {}, "Borrow Indicator Colors (Per Spec)"),
        U.el("div", { style: "grid-column:1/-1;display:flex;gap:14px;align-items:center;padding:6px 0;" },
          U.el("span", { class: "tag-borrow easy" }, "ETB (Red: Easy)"),
          U.el("span", { class: "tag-borrow hard" }, "HTB (Yellow: Hard)"),
          U.el("span", { class: "tag-borrow none" }, "NO BORROW (Green: None)"),
          U.el("span", { class: "tag-borrow na" }, "N/A (Orange: No Data)")
        ),
        U.el("h3", {}, "Resolution Mode"),
        ...Settings.field("Borrow source", modeSel, "How shortability is determined for each ticker"),
        U.el("h3", {}, "Alpaca API Keys (Optional Override)"),
        ...Settings.field("Alpaca Key ID", Settings.text(b, "alpaca_key_id", "text", App.alpaca_key_masked || "PK..."), keyHelp),
        ...Settings.field("Alpaca Secret Key", Settings.text(b, "alpaca_secret_key", "password", App.alpaca_active ? "••••••••••••" : "Secret..."), keyHelp),
        ...Settings.field("Test Alpaca Connection", U.el("button", {
          class: "btn sm primary",
          style: "width:210px",
          onclick: async (e) => {
            const btn = e.target;
            btn.disabled = true;
            btn.textContent = "Testing…";
            try {
              const res = await App.api().test_alpaca();
              if (res.ok) {
                U.toast("alert", "🦙 Alpaca Connected", res.message);
                btn.textContent = "✓ Connected!";
              } else {
                U.toast("alert", "⚠️ Alpaca Failed", res.message);
                btn.textContent = "Failed";
              }
            } catch (err) {
              U.toast("alert", "⚠️ Error", String(err));
              btn.textContent = "Error";
            }
            setTimeout(() => { btn.disabled = false; btn.textContent = "▶ Test Alpaca Connection"; }, 2500);
          }
        }, "▶ Test Alpaca Connection"), "Verifies account status and buying power with Alpaca API")
      );
      return g;
    },

    tab_about(c) {
      const wrap = U.el("div", { class: "about-pane" });
      const hero = U.el("div", { class: "about-hero-wrap" },
        U.el("img", { src: "img/hero.jpg", class: "about-hero-img", alt: "NewsAlerts Hero Banner" }),
        U.el("div", { class: "about-hero-overlay" },
          U.el("div", { class: "about-title" }, "NewsAlerts — Momentum Intelligence"),
          U.el("div", { class: "about-ver" }, "v2.4 Portable Edition")
        )
      );

      const grid = U.el("div", { class: "form-grid", style: "margin-top:12px" });
      grid.append(
        U.el("h3", {}, "System & Architecture"),
        ...Settings.field("Platform Engine", U.el("span", { style: "color:var(--text);font-family:var(--mono);font-size:12px" }, "Python 3.11 · Edge WebView2 · WinMM Per-Process Audio")),
        ...Settings.field("Data Storage", U.el("span", { style: "color:var(--text);font-family:var(--mono);font-size:12px" }, "%APPDATA%\\NewsAlerts\\ (Config & 4-Day Tape)")),
        ...Settings.field("TradingView Feeds", U.el("span", { style: "color:var(--up);font-weight:600" }, c.tv?.sessionid ? "Connected (Real-Time)" : "Unauthenticated (15m Delay)")),
        ...Settings.field("Borrow Locates", U.el("span", { style: "color:var(--text)" }, "Alpaca API + Live TradingView Feeds")),
        ...Settings.field("Push Notifications", U.el("span", { style: "color:var(--text)" }, "Telegram Asynchronous Queue Worker"))
      );

      wrap.append(hero, grid);
      return wrap;
    },
  };
  window.Settings = Settings;
})();
