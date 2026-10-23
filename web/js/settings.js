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
          App.app_dir = st.app_dir;
          App.secrets_file = st.secrets_file;
          App.has_keys_toml = st.has_keys_toml;
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
        if (App.updateFilterBannedButton) App.updateFilterBannedButton();
        Screener.renderBar(); Screener.renderTable(); Tape.renderAll(); News.syncTools();
        if (window.News && News.renderHead) News.renderHead();
      };
      U.$("#settings-cancel").onclick = () => Settings.close();
      U.$("#settings-close").onclick = () => Settings.close();
    },

    close() {
      const bg = U.$("#settings");
      if (bg) bg.classList.remove("show");
    },

    isOpen() {
      const bg = U.$("#settings");
      return !!(bg && bg.classList.contains("show"));
    },

    _currentOnTop: null,

    applyUi() {
      const ui = App.config.ui;
      document.documentElement.style.setProperty("--fs", (ui.font_size || 13) + "px");
      document.documentElement.style.setProperty("--row-h", Math.round((ui.font_size || 13) * 2.3) + "px");
      document.body.classList.toggle("bright", !!ui.tape_bright);
      const onTop = !!ui.always_on_top;
      if (Settings._currentOnTop !== onTop) {
        Settings._currentOnTop = onTop;
        App.api().set_on_top(onTop);
      }
    },

    // -- helpers
    field(label, input, help) {
      const items = [U.el("label", {}, label), input];
      if (help) items.push(U.el("div", { class: "help" }, help));
      return items;
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
              const res = await App.api().send_telegram_test({
                bot_token: a.telegram_bot_token || "",
                chat_id: a.telegram_chat_id || "",
              });
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
        ...Settings.field("History retention (days)", Settings.num(t, "retention_days"), "Keeps tape alerts saved on disk for off-hours and weekend review (default: 4 days)."));

      const stratSection = U.el("div", { class: "strat-section", style: "margin-top:16px;" });

      const renderStrategies = () => {
        const stratHead = U.el("div", { style: "display:flex;align-items:center;justify-content:space-between;margin:0 0 10px;" },
          U.el("h3", { style: "margin:0;font-size:12px;text-transform:uppercase;letter-spacing:.6px;color:var(--text-2);" }, `Strategies (${t.strategies.length})`),
          U.el("div", { style: "display:flex;gap:8px;align-items:center;" },
            U.el("button", {
              class: "btn sm primary",
              onclick: () => {
                const newName = "Custom Strategy " + (t.strategies.length + 1);
                const s = {
                  name: newName,
                  family: "custom",
                  trigger: "hod",
                  float_min: null,
                  float_max: null,
                  relvol_min: null,
                  relvol_max: null,
                  price_min: null,
                  price_max: null,
                  hi52_ratio_min: null,
                  up_pct: null,
                  window_min: null,
                };
                t.strategies.push(s);
                if (!t.enabled.includes(s.name)) t.enabled.push(s.name);
                renderStrategies();
              }
            }, "+ Add Strategy"),
            U.el("button", {
              class: "btn sm",
              title: "Export strategies to JSON file",
              onclick: () => Settings.exportStrategies(t.strategies, t.enabled)
            }, "💾 Export"),
            U.el("button", {
              class: "btn sm",
              title: "Import strategies from JSON file",
              onclick: () => {
                Settings.readJsonFile((err, data, filename) => {
                  if (err) {
                    U.toast("alert", "⚠️ Import Failed", "Invalid JSON file: " + err.message);
                    return;
                  }
                  const res = Settings.importStrategiesData(t, data);
                  if (res.ok) {
                    renderStrategies();
                    U.toast("alert", "✓ Strategies Imported", `Successfully imported ${res.count} strategies from ${filename}.`);
                  } else {
                    U.toast("alert", "⚠️ Import Failed", res.error);
                  }
                });
              }
            }, "📂 Import")
          )
        );

        const tbl = U.el("table", { class: "strat" });
        tbl.append(U.el("tr", {},
          U.el("th", {}, "Name"),
          U.el("th", {}, "Trigger"),
          U.el("th", {}, "Family"),
          STRAT_COLS.map(([, h]) => U.el("th", {}, h)),
          U.el("th", { style: "width:36px;text-align:center;" }, "")
        ));

        t.strategies.forEach((s) => {
          const name = U.el("input", { type: "text", value: s.name });
          name.onchange = () => {
            const old = s.name; s.name = name.value.trim() || old;
            t.enabled = t.enabled.map((n) => (n === old ? s.name : n));
          };
          const trig = U.el("select", {}, [["hod", "New HOD"], ["52w", "52w breakout"], ["squeeze", "Up X% in N min"]].map(([v, l]) => U.el("option", { value: v }, l)));
          trig.value = s.trigger || "hod";
          trig.onchange = () => (s.trigger = trig.value);

          const fam = U.el("select", {}, [["low", "Low Float"], ["medium", "Med Float"], ["large", "Large Cap"], ["squeeze", "Squeeze"], ["custom", "Custom"]].map(([v, l]) => U.el("option", { value: v }, l)));
          fam.value = s.family || "custom";
          fam.onchange = () => (s.family = fam.value);

          const delBtn = U.el("button", {
            class: "icon-btn strat-del-btn",
            title: `Delete strategy "${s.name}"`,
            style: "color:var(--muted);width:26px;height:26px;border-radius:4px;display:grid;place-items:center;",
            onclick: () => {
              const idx = t.strategies.indexOf(s);
              if (idx >= 0) {
                t.deleted_strategies = t.deleted_strategies || [];
                if (!t.deleted_strategies.includes(s.name)) t.deleted_strategies.push(s.name);
                t.strategies.splice(idx, 1);
                t.enabled = t.enabled.filter((n) => n !== s.name);
                renderStrategies();
              }
            }
          }, "🗑️");

          tbl.append(U.el("tr", {},
            U.el("td", { class: "name" }, name),
            U.el("td", {}, trig),
            U.el("td", {}, fam),
            STRAT_COLS.map(([k]) => U.el("td", {}, Settings.num(s, k, { big: k.startsWith("float") }))),
            U.el("td", { style: "text-align:center;" }, delBtn)
          ));
        });

        const help = U.el("div", { class: "help muted", style: "margin-top:10px;font-size:12px" },
          "HOD strategies fire when a matching stock prints a new session high. Floats accept K/M suffixes. Blank = no limit. Deleting or importing updates the running tape immediately upon saving.");

        stratSection.replaceChildren(stratHead, tbl, help);
      };

      renderStrategies();
      wrap.append(g, stratSection);
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
      const sourceDesc = App.has_keys_toml ? `external keys.toml (${App.secrets_file})` : "saved in config.json";
      const alpacaBanner = App.alpaca_active
        ? U.el("div", {
            style: "grid-column:1/-1;padding:9px 13px;background:rgba(74,222,128,0.12);border:1px solid rgba(74,222,128,0.3);border-radius:6px;color:#4ade80;font-size:12px;font-weight:500;display:flex;align-items:center;gap:8px;",
          }, `✓ Live Alpaca API Active · Loaded from ${sourceDesc} (${App.alpaca_key_masked})`)
        : null;

      const keyHelp = App.alpaca_active
        ? `Active (${sourceDesc}). Enter new keys here to update config.json.`
        : "Free at alpaca.markets (API Keys section). Stored in config.json.";

      if (alpacaBanner) g.append(alpacaBanner);
      g.append(
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
              const res = await App.api().test_alpaca({
                key_id: b.alpaca_key_id || "",
                secret_key: b.alpaca_secret_key || "",
              });
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

    tab_banned(c) {
      c.banned_symbols = c.banned_symbols || [];
      const wrap = U.el("div", { class: "banned-pane" });

      const header = U.el("div", {},
        U.el("h3", { style: "margin:0 0 6px;font-size:14px;color:var(--text);" }, "🚫 Banned & Closing-Only Stocks (IB / Broker Filter)"),
        U.el("p", { class: "muted", style: "margin:0;font-size:12px;line-height:1.4;" },
          "Exclude stocks in 'closing-only' status (or un-tradeable penny stocks like YMAT) from both the Screener table and the Tape stream. Audio chimes and Telegram alerts are also automatically suppressed for banned tickers.")
      );

      // Active toggle switch
      const toggleWrap = U.el("div", { style: "display:flex;align-items:center;gap:10px;padding:8px 12px;background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.25);border-radius:6px;" });
      const toggleCb = U.el("input", { type: "checkbox", id: "cfg-filter-banned", style: "cursor:pointer;width:16px;height:16px;" });
      toggleCb.checked = !!c.filter_banned;
      toggleCb.onchange = () => {
        c.filter_banned = toggleCb.checked;
      };
      const toggleLbl = U.el("label", { for: "cfg-filter-banned", style: "cursor:pointer;font-size:12.5px;font-weight:600;color:var(--text);" },
        "Enable Closing-Only Filter (Hide banned stocks on Screener & Tape)"
      );
      toggleWrap.append(toggleCb, toggleLbl);

      // Input row for adding symbols manually
      const addBar = U.el("div", { class: "banned-add-bar" });
      const input = U.el("input", {
        type: "text",
        class: "input banned-input",
        placeholder: "Enter symbol to ban (e.g. YMAT, GCT)...",
        maxlength: 10,
        spellcheck: "false",
        autocomplete: "off",
      });
      const addBtn = U.el("button", { class: "btn sm primary", style: "display:inline-flex;align-items:center;gap:4px;" }, "+ Add Symbol");

      const chipsWrap = U.el("div", { class: "banned-chips-wrap" });
      const countBadge = U.el("span", { class: "sub", style: "margin-left:8px;font-weight:normal;" });

      const renderChips = () => {
        chipsWrap.replaceChildren();
        const syms = c.banned_symbols || [];
        countBadge.textContent = `(${syms.length} symbol${syms.length === 1 ? "" : "s"})`;
        if (!syms.length) {
          chipsWrap.append(U.el("div", { class: "muted", style: "font-size:12px;padding:8px;" },
            "No symbols banned yet. Use the 🚫 icon in Screener or Tape rows, or add tickers above."));
          return;
        }
        syms.forEach((sym, idx) => {
          const chip = U.el("div", { class: "banned-chip" },
            U.el("span", {}, sym),
            U.el("button", {
              class: "banned-chip-remove",
              title: `Remove ${sym} from banned list`,
              onclick: () => {
                c.banned_symbols.splice(idx, 1);
                renderChips();
              }
            }, "✕")
          );
          chipsWrap.append(chip);
        });
      };

      const handleAdd = () => {
        const val = input.value.trim().toUpperCase().replace(/[^A-Z0-9.-]/g, "");
        if (!val) return;
        if (!c.banned_symbols.includes(val)) {
          c.banned_symbols.push(val);
          renderChips();
          input.value = "";
        } else {
          U.toast("info", `${val} already exists`, `Symbol is already in the banned list.`);
        }
        input.focus();
      };

      addBtn.onclick = handleAdd;
      input.onkeydown = (e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          handleAdd();
        }
      };

      addBar.append(input, addBtn);

      const listHeader = U.el("div", { style: "display:flex;align-items:center;justify-content:space-between;" },
        U.el("div", { style: "font-size:12.5px;font-weight:600;color:var(--text);" }, "Banned Tickers List", countBadge),
        U.el("button", {
          class: "btn sm",
          style: "font-size:11px;",
          onclick: () => {
            if (c.banned_symbols.length && confirm("Clear all banned symbols from the list?")) {
              c.banned_symbols = [];
              renderChips();
            }
          }
        }, "Clear All")
      );

      renderChips();

      wrap.append(header, toggleWrap, addBar, listHeader, chipsWrap);
      return wrap;
    },

    tab_hotkeys(c) {
      if (!c.hotkeys) {
        c.hotkeys = {};
      }
      const DEFAULTS = {
        mute: "m",
        popout_tape: "t",
        pause_tape: "Space",
        settings: "s",
        refresh: "r",
        close_modal: "Escape",
        focus_story: "Enter",
        preset_1: "1",
        preset_2: "2",
        preset_3: "3",
        preset_4: "4",
        preset_5: "5",
      };
      Object.keys(DEFAULTS).forEach((k) => {
        if (c.hotkeys[k] === undefined) c.hotkeys[k] = DEFAULTS[k];
      });

      const HOTKEY_ITEMS = [
        { key: "mute", label: "Master Mute / Pause Alerts", desc: "Instantly suppresses alert audio chimes and Telegram alerts." },
        { key: "popout_tape", label: "Pop-Out Tape Window", desc: "Launches the floating, detached running tape window." },
        { key: "pause_tape", label: "Pause / Resume Tape Stream", desc: "Holds incoming tape momentum alerts in buffer or resumes stream." },
        { key: "settings", label: "Open Settings Modal", desc: "Toggles this settings dialog for feeds, audio, and strategies." },
        { key: "refresh", label: "Force Refresh", desc: "Triggers an immediate screener re-scan and news headline fetch." },
        { key: "close_modal", label: "Dismiss Modals & Drawers", desc: "Closes open settings, drawer, or catalyst stories, or blurs active inputs." },
        { key: "focus_story", label: "Focus Latest Story", desc: "Expands the latest catalyst news story for the selected symbol." },
        { key: "preset_1", label: "Screener Preset 1", desc: "Switches to screener preset filter tab #1." },
        { key: "preset_2", label: "Screener Preset 2", desc: "Switches to screener preset filter tab #2." },
        { key: "preset_3", label: "Screener Preset 3", desc: "Switches to screener preset filter tab #3." },
        { key: "preset_4", label: "Screener Preset 4", desc: "Switches to screener preset filter tab #4." },
        { key: "preset_5", label: "Screener Preset 5", desc: "Switches to screener preset filter tab #5." },
      ];

      const wrap = U.el("div", { class: "hotkeys-pane" });

      const header = U.el("div", { class: "hotkeys-header" },
        U.el("div", { style: "display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;" },
          U.el("div", {},
            U.el("h3", { style: "margin:0 0 4px;font-size:14px;color:var(--text);font-weight:700;" }, "⚡ Keyboard Shortcuts & Hotkey Configuration"),
            U.el("div", { style: "font-size:12px;color:var(--muted);max-width:620px;line-height:1.4;" },
              "Customize keyboard shortcuts for rapid execution and seamless navigation. Click any shortcut input to record a new key, or customize key characters directly."
            )
          ),
          U.el("button", {
            class: "btn sm",
            id: "btn-reset-hotkeys",
            style: "white-space:nowrap;display:flex;align-items:center;gap:6px;",
            onclick: () => {
              Object.assign(c.hotkeys, DEFAULTS);
              U.toast("info", "Hotkeys Reset", "Restored institutional default keyboard shortcuts", null, 2500);
              const parent = wrap.parentElement;
              if (parent) {
                parent.replaceChildren(Settings.tab_hotkeys(c));
              }
            }
          }, "↺ Reset Defaults")
        )
      );

      const table = U.el("table", { class: "hotkeys-table" },
        U.el("thead", {},
          U.el("tr", {},
            U.el("th", { style: "width:34%;" }, "Action"),
            U.el("th", { style: "width:48%;" }, "Description"),
            U.el("th", { style: "width:18%;text-align:right;" }, "Shortcut Key")
          )
        )
      );

      const tbody = U.el("tbody");

      HOTKEY_ITEMS.forEach((item) => {
        const tr = U.el("tr", {});
        const tdName = U.el("td", { class: "hk-action" },
          U.el("strong", {}, item.label),
          U.el("span", { class: "hk-id-tag" }, item.key)
        );
        const tdDesc = U.el("td", { class: "hk-desc" }, item.desc);

        const currentVal = c.hotkeys[item.key] || DEFAULTS[item.key] || "";
        const keyBtn = U.el("input", {
          type: "text",
          class: "hotkey-key-input",
          value: currentVal,
          title: "Click to record a new keypress for this shortcut",
          readonly: true
        });

        keyBtn.onfocus = () => {
          keyBtn.classList.add("recording");
          keyBtn.value = "Press key...";
        };

        keyBtn.onblur = () => {
          keyBtn.classList.remove("recording");
          keyBtn.value = c.hotkeys[item.key] || DEFAULTS[item.key];
        };

        keyBtn.onkeydown = (e) => {
          e.preventDefault();
          e.stopPropagation();

          if (["Control", "Alt", "Shift", "Meta"].includes(e.key)) return;

          let captured = e.key;
          if (captured === " ") captured = "Space";
          else if (captured.length === 1) captured = captured.toUpperCase();

          c.hotkeys[item.key] = captured;
          keyBtn.value = captured;
          keyBtn.classList.remove("recording");
          keyBtn.blur();

          U.toast("info", "Shortcut Assigned", `${item.label} bound to [ ${captured} ]`, null, 2000);
        };

        const tdKey = U.el("td", { style: "text-align:right;" }, keyBtn);
        tr.append(tdName, tdDesc, tdKey);
        tbody.append(tr);
      });

      // Fixed row for Reserved Row Navigation (ArrowUp / ArrowDown)
      const trNav = U.el("tr", { class: "reserved-row" },
        U.el("td", { class: "hk-action" },
          U.el("strong", {}, "Screener Row Selection"),
          U.el("span", { class: "hk-id-tag" }, "navigation")
        ),
        U.el("td", { class: "hk-desc" }, "Move active selection up or down across momentum screener table rows."),
        U.el("td", { style: "text-align:right;" },
          U.el("span", { class: "hotkey-key-badge" }, "▲ / ▼")
        )
      );
      tbody.append(trNav);

      table.append(tbody);

      const notice = U.el("div", { class: "hotkeys-notice" },
        "💡 Note: Keyboard shortcuts are active throughout the application and floating windows. When typing inside text input fields or search boxes, shortcuts automatically yield to prevent accidental triggers."
      );

      wrap.append(header, table, notice);
      return wrap;
    },

    tab_backup(c) {
      const wrap = U.el("div", { class: "backup-pane" });

      const header = U.el("div", { style: "margin-bottom:16px;" },
        U.el("h3", { style: "margin:0 0 6px;font-size:14px;color:var(--text);" }, "Configuration Backup & Strategy Sync"),
        U.el("p", { class: "muted", style: "margin:0;font-size:12px;line-height:1.4;" },
          "Export your full terminal settings or specific trading strategies as portable JSON files. Easily restore backups across machines or share strategies with other traders.")
      );

      const cardsWrap = U.el("div", { class: "backup-cards-grid" });

      // Storage Directory Transparency & Explorer Access
      const storageCard = U.el("div", { class: "backup-card", style: "grid-column: 1 / -1; background: #131722; border-color: rgba(59,130,246,0.25);" },
        U.el("div", { class: "backup-card-head" },
          U.el("div", { class: "backup-card-title", style: "display:flex;align-items:center;gap:6px;" }, "📁 Central Application Directory (APP_DIR)"),
          U.el("div", { class: "backup-card-badge", style: "background:rgba(59,130,246,0.15);color:var(--accent);border-color:rgba(59,130,246,0.3);" },
            App.has_keys_toml ? "keys.toml Active" : "config.json Unified"
          )
        ),
        U.el("div", { class: "backup-card-desc", style: "display:flex;flex-direction:column;gap:6px;" },
          U.el("div", {}, "Active storage path where terminal settings, API keys, session cookies, and rolling tape history reside:"),
          U.el("code", { style: "font-family:var(--mono);background:var(--bg, #0d111a);padding:6px 10px;border-radius:4px;border:1px solid var(--border-2);color:var(--accent);font-size:12px;word-break:break-all;user-select:all;" }, App.app_dir || "%APPDATA%\\NewsAlerts"),
          U.el("div", { class: "muted", style: "font-size:11.5px;" },
            "Manifest: config.json (Settings/Credentials), tape_history.json (Tape Cache), app.log (Diagnostics), optional keys.toml (Secret Override)."
          )
        ),
        U.el("div", { class: "backup-card-actions", style: "margin-top:8px;" },
          U.el("button", {
            class: "btn sm",
            style: "display:inline-flex;align-items:center;gap:6px;",
            onclick: () => App.api().open_app_dir()
          }, "📂 Open App Data Folder in Explorer / Finder")
        )
      );

      // Card 1: Full Configuration Backup
      const fullCard = U.el("div", { class: "backup-card" },
        U.el("div", { class: "backup-card-head" },
          U.el("div", { class: "backup-card-title" }, "💾 Full Application Backup"),
          U.el("div", { class: "backup-card-badge" }, "Complete State")
        ),
        U.el("div", { class: "backup-card-desc" },
          "Exports all screeners, sound alert configs, tape universe thresholds, hotkeys, and strategies into a single restore file."),
        U.el("div", { class: "backup-card-actions" },
          U.el("button", {
            class: "btn sm primary",
            onclick: () => {
              const dt = new Date().toISOString().slice(0, 10);
              const payload = {
                app: "NewsAlerts",
                type: "full_backup",
                version: App.version || "2.7.0",
                exported_at: new Date().toISOString(),
                config: c,
              };
              Settings.exportJson(`newsalerts_backup_${dt}.json`, payload);
              U.toast("alert", "✓ Backup Exported", `Saved full configuration backup as newsalerts_backup_${dt}.json`);
            }
          }, "💾 Export Full Backup (.json)"),
          U.el("button", {
            class: "btn sm",
            onclick: () => {
              Settings.readJsonFile((err, data, filename) => {
                if (err) {
                  U.toast("alert", "⚠️ Import Failed", "Invalid JSON file: " + err.message);
                  return;
                }
                const cfg = data.config && typeof data.config === "object" ? data.config : data;
                if (!cfg || typeof cfg !== "object") {
                  U.toast("alert", "⚠️ Import Failed", "File does not contain valid NewsAlerts configuration.");
                  return;
                }
                // Update active working copy
                Object.assign(c, cfg);
                App.config = c;
                App.saveConfig(true);
                Settings.applyUi();
                Screener.renderBar();
                Screener.renderTable();
                Tape.renderAll();
                News.syncTools();
                U.toast("alert", "✓ Backup Restored", `Successfully imported configuration from ${filename}.`);
                // Re-render current tab
                const body = U.$("#settings-body");
                if (body) body.replaceChildren(Settings.tab_backup(c));
              });
            }
          }, "📂 Import Backup File")
        )
      );

      // Card 2: Strategies Import & Export
      const stratCard = U.el("div", { class: "backup-card" },
        U.el("div", { class: "backup-card-head" },
          U.el("div", { class: "backup-card-title" }, "⚡ Tape Strategies Only"),
          U.el("div", { class: "backup-card-badge" }, `${c.tape.strategies.length} Active`)
        ),
        U.el("div", { class: "backup-card-desc" },
          "Export your multi-strategy rules engine definitions (HOD, 52w breakouts, squeezes) to share with other traders or import custom setups."),
        U.el("div", { class: "backup-card-actions" },
          U.el("button", {
            class: "btn sm primary",
            onclick: () => Settings.exportStrategies(c.tape.strategies, c.tape.enabled)
          }, "💾 Export Strategies (.json)"),
          U.el("button", {
            class: "btn sm",
            onclick: () => {
              Settings.readJsonFile((err, data, filename) => {
                if (err) {
                  U.toast("alert", "⚠️ Import Failed", "Invalid JSON file: " + err.message);
                  return;
                }
                const res = Settings.importStrategiesData(c.tape, data);
                if (res.ok) {
                  App.config = c;
                  App.saveConfig(true);
                  Tape.renderAll();
                  U.toast("alert", "✓ Strategies Imported", `Imported ${res.count} strategies from ${filename}.`);
                  const body = U.$("#settings-body");
                  if (body) body.replaceChildren(Settings.tab_backup(c));
                } else {
                  U.toast("alert", "⚠️ Import Failed", res.error);
                }
              });
            }
          }, "📂 Import Strategies")
        )
      );

      // Card 3: Reset / Factory Defaults
      const resetCard = U.el("div", { class: "backup-card danger" },
        U.el("div", { class: "backup-card-head" },
          U.el("div", { class: "backup-card-title" }, "↺ Factory Reset"),
          U.el("div", { class: "backup-card-badge danger" }, "Destructive")
        ),
        U.el("div", { class: "backup-card-desc" },
          "Restore all screener presets, sound chimes, hotkeys, and strategies back to original factory defaults. Secret keys in keys.toml will be preserved."),
        U.el("div", { class: "backup-card-actions" },
          U.el("button", {
            class: "btn sm",
            style: "color:var(--down);border-color:rgba(246,70,93,0.4);",
            onclick: async () => {
              if (!confirm("Are you sure you want to reset all terminal settings and strategies back to factory defaults?")) return;
              try {
                const fresh = await App.api().reset_config();
                if (fresh) {
                  Object.assign(c, fresh);
                  App.config = fresh;
                  Settings.applyUi();
                  Screener.renderBar();
                  Screener.renderTable();
                  Tape.renderAll();
                  News.syncTools();
                  U.toast("alert", "↺ Factory Reset", "Terminal configuration successfully restored to factory defaults.");
                  const body = U.$("#settings-body");
                  if (body) body.replaceChildren(Settings.tab_backup(c));
                }
              } catch (e) {
                U.toast("alert", "⚠️ Reset Error", String(e));
              }
            }
          }, "↺ Restore Factory Defaults")
        )
      );

      cardsWrap.append(storageCard, fullCard, stratCard, resetCard);
      wrap.append(header, cardsWrap);
      return wrap;
    },

    exportJson(filename, data) {
      try {
        const str = JSON.stringify(data, null, 2);
        const blob = new Blob([str], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        setTimeout(() => {
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
        }, 500);
        return true;
      } catch (err) {
        U.toast("alert", "⚠️ Export Error", String(err));
        return false;
      }
    },

    exportStrategies(strategies, enabled) {
      const dt = new Date().toISOString().slice(0, 10);
      const payload = {
        app: "NewsAlerts",
        type: "strategies",
        version: App.version || "2.7.0",
        exported_at: new Date().toISOString(),
        strategies: strategies || [],
        enabled: enabled || [],
      };
      Settings.exportJson(`newsalerts_strategies_${dt}.json`, payload);
      U.toast("alert", "✓ Strategies Exported", `Saved ${strategies.length} strategies as newsalerts_strategies_${dt}.json`);
    },

    importStrategiesData(tapeCfg, data) {
      let incoming = null;
      if (Array.isArray(data)) {
        incoming = data;
      } else if (data && Array.isArray(data.strategies)) {
        incoming = data.strategies;
      } else {
        return { ok: false, error: "JSON does not contain a 'strategies' array." };
      }
      let count = 0;
      incoming.forEach((s) => {
        if (!s || typeof s !== "object" || !s.name) return;
        const existingIdx = tapeCfg.strategies.findIndex((x) => x.name === s.name);
        if (existingIdx >= 0) {
          tapeCfg.strategies[existingIdx] = s;
        } else {
          tapeCfg.strategies.push(s);
        }
        if (!tapeCfg.enabled.includes(s.name)) {
          tapeCfg.enabled.push(s.name);
        }
        count++;
      });
      return { ok: true, count };
    },

    readJsonFile(callback) {
      const fileInput = document.createElement("input");
      fileInput.type = "file";
      fileInput.accept = ".json,application/json";
      fileInput.style.display = "none";
      document.body.appendChild(fileInput);
      fileInput.onchange = (e) => {
        const file = e.target.files && e.target.files[0];
        if (!file) {
          document.body.removeChild(fileInput);
          return;
        }
        const reader = new FileReader();
        reader.onload = (event) => {
          try {
            const parsed = JSON.parse(event.target.result);
            callback(null, parsed, file.name);
          } catch (err) {
            callback(err, null, file.name);
          } finally {
            document.body.removeChild(fileInput);
          }
        };
        reader.onerror = (err) => {
          callback(err, null, file.name);
          document.body.removeChild(fileInput);
        };
        reader.readAsText(file);
      };
      fileInput.click();
    },

    tab_about(c) {
      const wrap = U.el("div", { class: "about-pane" });
      const ver = App.version || "";
      const sem = App.semver || { major: 0, minor: 0, patch: 0 };
      const hero = U.el("div", { class: "about-hero-wrap" },
        U.el("img", { src: "img/hero.jpg", class: "about-hero-img", alt: "NewsAlerts Hero Banner" }),
        U.el("div", { class: "about-hero-overlay" },
          U.el("div", { class: "about-title" }, "NewsAlerts — Momentum Intelligence"),
          U.el("div", { class: "about-ver" }, `v${ver} (SemVer 2.0.0)`)
        )
      );

      const linkGh = U.el("a", {
        href: "https://github.com/mlgitdev/NewsAlerts",
        target: "_blank",
        style: "color:var(--accent);text-decoration:none;font-weight:600;display:inline-flex;align-items:center;gap:6px;"
      }, "github.com/mlgitdev/NewsAlerts ↗");

      const linkWiki = U.el("a", {
        href: "https://github.com/mlgitdev/NewsAlerts/wiki",
        target: "_blank",
        style: "color:var(--accent);text-decoration:none;font-weight:600;display:inline-flex;align-items:center;gap:6px;"
      }, "Project Documentation Wiki ↗");

      const grid = U.el("div", { class: "form-grid", style: "margin-top:12px" });
      grid.append(
        U.el("h3", {}, "Project & Documentation"),
        ...Settings.field("GitHub Repository", linkGh, "Source code, release downloads, and issue tracker"),
        ...Settings.field("Documentation Wiki", linkWiki, "Terminal manual, rules engine, and strategy guides"),
        U.el("h3", {}, "System & Storage Transparency"),
        ...Settings.field("Semantic Version", U.el("span", { style: "color:var(--up);font-family:var(--mono);font-weight:700" }, `v${ver} [Major: ${sem.major}, Minor: ${sem.minor}, Patch: ${sem.patch}]`), "Strictly conforms to SemVer 2.0.0 (MAJOR.MINOR.PATCH)"),
        ...Settings.field("Platform Engine", U.el("span", { style: "color:var(--text);font-family:var(--mono);font-size:12px" }, "Python 3.10+ · Native pywebview · Cross-Platform Audio")),
        ...Settings.field("Central App Directory",
          U.el("div", { style: "display:flex;align-items:center;gap:8px;flex-wrap:wrap;" },
            U.el("code", { style: "font-family:var(--mono);background:#131722;padding:4px 8px;border-radius:4px;border:1px solid var(--border-2);color:var(--accent);word-break:break-all;font-size:11.5px;user-select:all;" }, App.app_dir || "%APPDATA%\\NewsAlerts"),
            U.el("button", {
              class: "btn sm",
              style: "display:inline-flex;align-items:center;gap:4px;white-space:nowrap;",
              onclick: () => App.api().open_app_dir()
            }, "📂 Open Folder")
          ),
          "Active resolved OS directory storing config.json, tape_history.json, app.log, and optional keys.toml"
        ),
        ...Settings.field("Credential Storage",
          U.el("div", { style: "display:flex;align-items:center;gap:8px;font-size:12px;" },
            U.el("span", { style: "color:" + (App.has_keys_toml ? "var(--up)" : "var(--accent)") + ";font-weight:600;" },
              App.has_keys_toml ? "Override: keys.toml" : "Unified: config.json"
            ),
            U.el("span", { class: "muted" },
              App.has_keys_toml ? `(${App.secrets_file})` : "(Managed via In-App Settings)"
            )
          ),
          "Credentials (TradingView cookies, Alpaca keys, Telegram tokens) are password-masked and saved atomically"
        ),
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
