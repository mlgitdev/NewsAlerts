/* Running tape (Warrior-style momentum events). Used in main window and pop-out window. */
(function () {
  const COLS = [
    ["Time", "l", (e) => U.timeTape(e.ts)],
    ["Symbol", "l", null],
    ["Price", "", (e) => U.price(e.price)],
    ["Volume", "", (e) => U.big(e.volume)],
    ["Float", "", (e) => U.big(e.float)],
    ["Rel Vol<br>(Daily)", "", (e) => U.dec(e.relvol)],
    ["Rel Vol<br>(5 min %)", "", (e) => U.dec(e.relvol5)],
    ["Chg %", "", (e) => U.pct(e.chg)],
    ["Gap %", "", (e) => U.pct(e.gap)],
    ["Pos in<br>52w Range", "", (e) => U.dec(e.pos52)],
    ["Range<br>Today", "", (e) => U.dec(e.range)],
    ["Strategy Name", "l", (e) => e.strategy],
  ];
  const MAX_DOM = 3000;

  const Tape = {
    events: [],
    pending: [],
    paused: false,
    root: null,

    mount(host, opts = {}) {
      Tape.opts = opts;
      const strBtn = U.el("button", { class: "btn sm", id: "tape-strategies-btn" });
      const pauseBtn = U.el("button", { class: "icon-btn", id: "tape-pause-btn", title: "Pause tape", html: U.icons.pause });
      const clearBtn = U.el("button", {
        class: "icon-btn",
        id: "tape-clear-btn",
        title: "Clear tape history from disk",
        html: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;vertical-align:-2px"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>'
      });
      const popBtn = opts.popout ? null : U.el("button", { class: "icon-btn", id: "tape-popout-btn", title: "Pop out tape", html: U.icons.popout });
      const count = U.el("span", { class: "sub" });
      const newBtn = U.el("button", { class: "new-events", id: "tape-new-events" }, "New Events ↑");
      const thead = U.el("tr", {}, COLS.map(([h, c]) => U.el("th", { class: c, html: h })));
      const tbody = U.el("tbody");
      const body = U.el("div", { class: "pane-body" },
        U.el("table", { class: "grid" }, U.el("thead", {}, thead), tbody));
      const pane = U.el("section", { class: "pane tape-pane", id: "tape-pane" },
        U.el("div", { class: "pane-head" },
          U.el("div", { class: "pane-title" }, "⚡ Small Cap — High of Day Momentum", count),
          U.el("div", { class: "spacer" }), strBtn, pauseBtn, clearBtn, popBtn),
        newBtn, body);
      host.append(pane);
      Object.assign(Tape, { root: pane, tbody, body, newBtn, pauseBtn, clearBtn, strBtn, count });

      strBtn.onclick = () => Tape.strategyMenu(strBtn);
      pauseBtn.onclick = () => Tape.setPaused(!Tape.paused);
      clearBtn.onclick = async () => {
        if (confirm("Clear all historical tape momentum alerts saved on disk?")) {
          await App.api().clear_tape();
          Tape.events = [];
          Tape.renderAll();
        }
      };
      if (popBtn) popBtn.onclick = () => App.api().pop_tape();
      newBtn.onclick = () => { Tape.setPaused(false); body.scrollTop = 0; Tape.updateNewBtn(); };
      body.addEventListener("scroll", () => { if (body.scrollTop < 5 && !Tape.paused) Tape.updateNewBtn(); });
      tbody.addEventListener("click", (e) => {
        const tr = e.target.closest("tr");
        if (tr && tr.dataset.t) App.api().select_symbol(tr.dataset.t);
      });
      tbody.addEventListener("dblclick", (e) => {
        const tr = e.target.closest("tr");
        if (tr && tr.dataset.t) App.api().open_chart(tr.dataset.t);
      });
      App.sub("tape", (evs) => Tape.add(evs));
      App.sub("tape_cleared", () => { Tape.events = []; Tape.renderAll(); });
      App.sub("config", () => Tape.renderAll());

      if (opts.popout) {
        document.addEventListener("keydown", (e) => {
          if (e.ctrlKey || e.altKey || e.metaKey) return;
          if (/INPUT|SELECT|TEXTAREA/.test(document.activeElement?.tagName) || document.activeElement?.isContentEditable) return;
          const hk = App.config?.hotkeys || {};
          const pauseKey = (hk.pause_tape || "Space").toLowerCase();
          const normKey = (e.key === " " ? "Space" : e.key).toLowerCase();
          if (normKey === pauseKey || e.key === " ") {
            e.preventDefault();
            Tape.setPaused(!Tape.paused);
          }
        });
      }
    },

    enabled() { return new Set(App.config.tape.enabled); },

    load(events) { Tape.events = events || []; Tape.renderAll(); },

    row(e, animate) {
      const tr = U.el("tr", { class: e.family + (animate ? " in" : ""), "data-t": e.ticker });
      COLS.forEach(([h, c, fn], i) => {
        const td = U.el("td", { class: c });
        if (i === 0) {
          td.textContent = U.timeTape(e.ts);
          td.title = U.fullDateET(e.ts);
        } else if (i === 1) {
          const b = e.borrow || { status: "na", label: "N/A" };
          const bTag = U.el("span", {
            class: "tag-borrow " + b.status,
            style: "margin-left:6px;",
            title: `Borrow: ${b.label} (${b.status === "easy" ? "Easy to borrow" : b.status === "hard" ? "Hard to borrow" : b.status === "none" ? "No borrow available" : "N/A"})`
          }, b.label);
          const addBtn = U.el("button", {
            class: "btn-wl-add",
            title: `Add ${e.symbol} to active TradingView watchlist`,
            onclick: (ev) => {
              ev.stopPropagation();
              if (window.App && App.handleAddToWatchlist) {
                App.handleAddToWatchlist(addBtn, e.ticker || e.symbol);
              }
            }
          }, "+");
          td.append(U.el("span", { class: "sym-link" }, e.symbol), addBtn, bTag);
        } else td.textContent = fn(e);
        if (i === 3) {
          td.classList.add("vol-cell");
          if (e.volume >= 1e6) { td.style.background = "#4b5568"; td.style.color = "#fff"; }
        }
        if (i === 4 && e.float != null && e.float < 20e6) td.classList.add("float-low");
        if (i === 7 || i === 8) td.className += " " + U.cls(e[i === 7 ? "chg" : "gap"]);
        tr.append(td);
      });
      return tr;
    },

    renderAll() {
      if (!Tape.tbody || !App.config) return;
      const en = Tape.enabled();
      const frag = document.createDocumentFragment();
      let n = 0;
      for (const e of Tape.events) {
        if (!en.has(e.strategy)) continue;
        frag.append(Tape.row(e, false));
        if (++n >= MAX_DOM) break;
      }
      Tape.tbody.replaceChildren(frag);
      if (!n) Tape.tbody.append(U.el("tr", {}, U.el("td", { colspan: COLS.length, class: "empty" },
        "Waiting for momentum events… (tape runs during pre, regular and post market)")));
      Tape.pending = [];
      Tape.updateStrBtn();
      Tape.updateNewBtn();
    },

    add(evs) {
      Tape.events = evs.concat(Tape.events).slice(0, 5000);
      const en = Tape.enabled();
      const vis = evs.filter((e) => en.has(e.strategy));
      if (!vis.length) return;
      if (Tape.paused) { Tape.pending = vis.concat(Tape.pending); Tape.updateNewBtn(); return; }
      Tape.insert(vis, true);
    },

    insert(vis, animate) {
      const empty = Tape.tbody.querySelector("td.empty");
      if (empty) empty.parentElement.remove();
      const body = Tape.body;
      const before = body.scrollHeight;
      const frag = document.createDocumentFragment();
      vis.forEach((e) => frag.append(Tape.row(e, animate && body.scrollTop < 5)));
      Tape.tbody.prepend(frag);
      while (Tape.tbody.children.length > MAX_DOM) Tape.tbody.lastChild.remove();
      if (body.scrollTop > 5) { body.scrollTop += body.scrollHeight - before; Tape.scrolledNew = true; }
      Tape.updateNewBtn();
    },

    setPaused(p) {
      Tape.paused = p;
      Tape.pauseBtn.innerHTML = p ? U.icons.play : U.icons.pause;
      Tape.pauseBtn.classList.toggle("active", p);
      Tape.pauseBtn.title = p ? "Resume tape" : "Pause tape";
      if (!p && Tape.pending.length) { const q = Tape.pending; Tape.pending = []; Tape.insert(q, false); }
      Tape.updateNewBtn();
    },

    updateNewBtn() {
      const n = Tape.pending.length;
      if (Tape.body.scrollTop < 5) Tape.scrolledNew = false;
      const show = n > 0 || Tape.scrolledNew;
      Tape.newBtn.classList.toggle("show", show);
      Tape.newBtn.textContent = n ? `New Events ↑ (${n})` : "New Events ↑";
      const en = Tape.enabled();
      const vis = Tape.events.filter((e) => en.has(e.strategy)).length;
      const days = App.config?.tape?.retention_days || 4;
      Tape.count.textContent = Tape.paused ? "· paused" : (vis ? `· ${vis} alerts (${days}d history)` : "");
    },

    updateStrBtn() {
      const all = App.config.tape.strategies.length;
      const on = App.config.tape.enabled.length;
      Tape.strBtn.innerHTML = `${U.icons.bell.replace("<svg", '<svg style="width:13px;height:13px;vertical-align:-2px;margin-right:5px"')}Strategies <span class="muted">${on}/${all}</span>`;
    },

    strategyMenu(anchor) {
      const cfg = App.config.tape;
      const box = U.el("div", { style: "min-width:360px" });
      const allOn = cfg.enabled.length === cfg.strategies.length;
      const all = U.el("input", { type: "checkbox" });
      all.checked = allOn;
      all.onchange = () => {
        cfg.enabled = all.checked ? cfg.strategies.map((s) => s.name) : [];
        U.$$("input[data-s]", box).forEach((c) => (c.checked = all.checked));
        Tape.renderAll(); App.saveConfig();
      };
      box.append(U.el("label", { class: "check" }, all, U.el("b", {}, "Select / Unselect All")), U.el("div", { class: "sep" }));
      const fam = { low: "var(--mint)", medium: "var(--sand)", squeeze: "var(--cyan)", large: "var(--accent-2)" };
      cfg.strategies.forEach((s) => {
        const c = U.el("input", { type: "checkbox", "data-s": s.name });
        c.checked = cfg.enabled.includes(s.name);
        c.onchange = () => {
          const set = new Set(cfg.enabled);
          c.checked ? set.add(s.name) : set.delete(s.name);
          cfg.enabled = cfg.strategies.map((x) => x.name).filter((n) => set.has(n));
          all.checked = cfg.enabled.length === cfg.strategies.length;
          Tape.renderAll(); App.saveConfig();
        };
        box.append(U.el("label", { class: "check" }, c,
          U.el("span", { style: `width:8px;height:8px;border-radius:2px;background:${fam[s.family] || "#888"}` }), s.name));
      });
      U.pop(anchor, box, { right: true });
    },
  };
  window.Tape = Tape;
})();
