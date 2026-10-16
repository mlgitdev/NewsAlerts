/* Screener: screen tabs, session selector, filter chips, results table. */
(function () {
  const SECTORS = ["Commercial Services", "Communications", "Consumer Durables", "Consumer Non-Durables",
    "Consumer Services", "Distribution Services", "Electronic Technology", "Energy Minerals", "Finance",
    "Health Services", "Health Technology", "Industrial Services", "Miscellaneous", "Non-Energy Minerals",
    "Process Industries", "Producer Manufacturing", "Retail Trade", "Technology Services", "Transportation",
    "Utilities"];

  const FIELDS = {
    price: { label: "price", sess: true, unit: "$", presets: [["1 to 20", 1, 20], ["1 to 10", 1, 10], ["2 to 20", 2, 20], ["< 5", null, 5], ["> 20", 20, null]] },
    chg: { label: "chg", sess: true, unit: "%", presets: [["> 5%", 5, null], ["> 10%", 10, null], ["> 20%", 20, null], ["> 50%", 50, null], ["< -10%", null, -10]] },
    vol: { label: "vol", sess: true, presets: [["> 50K", 5e4, null], ["> 100K", 1e5, null], ["> 500K", 5e5, null], ["> 1M", 1e6, null]] },
    chg_open: { label: "chg from open", sess: true, unit: "%", presets: [["> 0%", 0, null], ["> 5%", 5, null], ["> 10%", 10, null]] },
    gap: { label: "gap", sess: true, unit: "%", presets: [["> 5%", 5, null], ["> 10%", 10, null], ["> 20%", 20, null]] },
    float: { label: "Float", presets: [["300K to 25M", 3e5, 25e6], ["< 10M", null, 10e6], ["< 20M", null, 20e6], ["< 50M", null, 50e6]] },
    mcap: { label: "Mkt cap", presets: [["< 50M", null, 50e6], ["< 300M", null, 300e6], ["< 2B", null, 2e9], ["> 2B", 2e9, null]] },
    relvol: { label: "Rel vol", presets: [["> 1", 1, null], ["> 2", 2, null], ["> 5", 5, null], ["> 10", 10, null]] },
    relvol_t: { label: "Rel vol at time", presets: [["> 1", 1, null], ["> 2", 2, null], ["> 5", 5, null]] },
    sector: { label: "Sector", list: SECTORS },
    exchange: { label: "Exchange", list: ["NASDAQ", "NYSE", "AMEX"] },
  };
  const SESS_PREFIX = { pre: "Pre-mkt", post: "Post-mkt", regular: "" };

  const COLS = [
    { k: "symbol", label: "Symbol", l: 1 },
    { k: "desc", label: "Name", l: 1 },
    { k: "close", label: "Price", f: (r) => U.price(r.close) },
    { k: "change", label: "Chg %", f: (r) => U.pct(r.change), c: (r) => U.cls(r.change) },
    { k: "sp", label: "{S} price", sess: 1, f: (r) => U.price(r.sp) },
    { k: "sc", label: "{S} chg %", sess: 1, f: (r) => U.pct(r.sc), c: (r) => U.cls(r.sc) },
    { k: "float", label: "Float", f: (r) => U.big(r.float) },
    { k: "sv", label: "{S} vol", sess: 1, f: (r) => U.big(r.sv) },
    { k: "volume", label: "Vol", f: (r) => U.big(r.volume) },
    { k: "relvol_t", label: "Rel vol<br>at time", f: (r) => U.dec(r.relvol_t), c: (r) => (r.relvol_t >= 2 ? "up" : "") },
    { k: "relvol", label: "Rel vol", f: (r) => U.dec(r.relvol), c: (r) => (r.relvol >= 2 ? "up" : "") },
    { k: "mcap", label: "Mkt cap", f: (r) => U.big(r.mcap) },
    { k: "sector", label: "Sector", l: 1, f: (r) => r.sector || "—" },
    { k: "news_ts", label: "News", l: 1 },
    { k: "first_seen", label: "First seen", f: (r) => U.timeET(r.first_seen, false) },
  ];

  const Screener = {
    data: null, selected: null, flashed: new Set(), status: {},

    screen() { return App.config.screens.find((s) => s.id === App.config.active_screen) || App.config.screens[0]; },
    session(screen = Screener.screen()) {
      return screen.session === "auto" ? (Screener.status.auto_session || "regular") : screen.session;
    },

    mount() {
      Screener.tabs = U.$("#tabs");
      Screener.seg = U.$("#session-seg");
      Screener.chips = U.$("#filters");
      Screener.thead = U.$("#scr-head");
      Screener.tbody = U.$("#scr-body");
      Screener.title = U.$("#scr-title");
      Screener.seg.addEventListener("click", (e) => {
        const b = e.target.closest("button"); if (!b) return;
        Screener.screen().session = b.dataset.s; Screener.changed();
      });
      Screener.thead.addEventListener("click", (e) => {
        const th = e.target.closest("th"); if (!th) return;
        const s = Screener.screen(); const k = th.dataset.k;
        s.sort = { field: k, dir: s.sort && s.sort.field === k && s.sort.dir === "desc" ? "asc" : "desc" };
        Screener.renderTable(); App.saveConfig();
      });
      Screener.tbody.addEventListener("click", (e) => {
        const tr = e.target.closest("tr[data-t]"); if (!tr) return;
        Screener.select(tr.dataset.t);
      });
      Screener.tbody.addEventListener("dblclick", (e) => {
        const tr = e.target.closest("tr[data-t]"); if (tr) App.api().open_chart(tr.dataset.t);
      });
      App.sub("screener", (d) => { if (d.screen_id === App.config.active_screen) { Screener.data = d; Screener.renderTable(); } });
      App.sub("status", (s) => { const prev = Screener.status.auto_session; Screener.status = s; if (prev !== s.auto_session) Screener.renderBar(); });
      document.addEventListener("keydown", Screener.keys);
      Screener.renderBar();
    },

    keys(e) {
      if (/INPUT|SELECT|TEXTAREA/.test(document.activeElement.tagName)) return;
      if (e.key !== "ArrowDown" && e.key !== "ArrowUp") return;
      const rows = U.$$("tr[data-t]", Screener.tbody);
      if (!rows.length) return;
      let i = rows.findIndex((r) => r.dataset.t === Screener.selected);
      i = e.key === "ArrowDown" ? Math.min(rows.length - 1, i + 1) : Math.max(0, i - 1);
      Screener.select(rows[i].dataset.t);
      rows[i].scrollIntoView({ block: "nearest" });
      e.preventDefault();
    },

    changed() { Screener.data = null; Screener.renderBar(); Screener.renderTable(); App.saveConfig(true); },

    select(ticker) {
      Screener.selected = ticker;
      U.$$("tr.sel", Screener.tbody).forEach((r) => r.classList.remove("sel"));
      const tr = Screener.tbody.querySelector(`tr[data-t="${CSS.escape(ticker)}"]`);
      if (tr) tr.classList.add("sel");
      const row = Screener.data && Screener.data.rows.find((r) => r.ticker === ticker);
      News.select(ticker, row);
    },

    // ------------------------------------------------------------ top bar
    renderBar() { Screener.renderTabs(); Screener.renderSeg(); Screener.renderChips(); },

    renderTabs() {
      const t = Screener.tabs; t.replaceChildren();
      App.config.screens.forEach((s) => {
        const bell = U.el("span", { class: "bell" + (s.alert ? " on" : ""), title: s.alert ? "Alerts on (click to turn off)" : "Alerts off (click to turn on)" }, "🔔");
        bell.onclick = (e) => { e.stopPropagation(); s.alert = !s.alert; Screener.renderTabs(); App.saveConfig(true); };
        const name = U.el("span", {}, s.name);
        const cnt = U.el("span", { class: "count", id: "tab-count-" + s.id });
        const tab = U.el("div", { class: "tab" + (s.id === App.config.active_screen ? " active" : ""), id: "tab-" + s.id }, bell, name, cnt);
        tab.onclick = () => {
          if (App.config.active_screen === s.id) return;
          App.config.active_screen = s.id; Screener.changed();
        };
        tab.ondblclick = () => Screener.rename(s, name);
        tab.oncontextmenu = (e) => { e.preventDefault(); Screener.tabMenu(s, tab, name); };
        t.append(tab);
      });
      const add = U.el("div", { class: "tab", id: "tab-add", title: "New screen" }, "+");
      add.onclick = () => {
        const cur = Screener.screen();
        const s = JSON.parse(JSON.stringify(cur));
        s.id = "s" + Date.now(); s.name = cur.name + " copy";
        App.config.screens.push(s); App.config.active_screen = s.id; Screener.changed();
      };
      t.append(add);
    },

    rename(s, nameEl) {
      const inp = U.el("input", { type: "text", value: s.name });
      nameEl.replaceWith(inp); inp.focus(); inp.select();
      const done = () => { s.name = inp.value.trim() || s.name; Screener.renderTabs(); App.saveConfig(true); };
      inp.onblur = done;
      inp.onkeydown = (e) => { if (e.key === "Enter") inp.blur(); if (e.key === "Escape") { inp.value = s.name; inp.blur(); } };
    },

    tabMenu(s, tab, nameEl) {
      const m = U.el("div", {});
      const item = (txt, fn, cls) => U.el("div", { class: "menu-item " + (cls || ""), onclick: () => { U.closePops(); fn(); } }, txt);
      m.append(
        item("✏️  Rename", () => Screener.rename(s, U.$("span:nth-child(2)", U.$("#tab-" + s.id)))),
        item("⧉  Duplicate", () => {
          const c = JSON.parse(JSON.stringify(s)); c.id = "s" + Date.now(); c.name = s.name + " copy";
          App.config.screens.push(c); App.config.active_screen = c.id; Screener.changed();
        }),
        item(s.alert ? "🔕  Turn alerts off" : "🔔  Turn alerts on", () => { s.alert = !s.alert; Screener.renderTabs(); App.saveConfig(true); }),
      );
      if (App.config.screens.length > 1) m.append(U.el("div", { class: "sep" }), item("🗑  Delete", () => {
        App.config.screens = App.config.screens.filter((x) => x.id !== s.id);
        if (App.config.active_screen === s.id) App.config.active_screen = App.config.screens[0].id;
        Screener.changed();
      }, "danger"));
      U.pop(tab, m);
    },

    renderSeg() {
      const s = Screener.screen();
      const auto = Screener.status.auto_session;
      U.$$("button", Screener.seg).forEach((b) => {
        b.classList.toggle("active", b.dataset.s === (s.session || "auto"));
        if (b.dataset.s === "auto") b.innerHTML = `Auto${auto ? `<span class="auto-hint">${{ pre: "PRE", regular: "RTH", post: "POST" }[auto]}</span>` : ""}`;
      });
    },

    // ------------------------------------------------------------ filters
    chipText(f) {
      const d = FIELDS[f.field]; const sess = Screener.session();
      let label = d.label;
      if (d.sess) {
        const p = SESS_PREFIX[sess];
        label = p ? `${p} ${d.label}` : d.label[0].toUpperCase() + d.label.slice(1);
      }
      if (d.list) return f.values && f.values.length ? `${label}: ${f.values.length > 2 ? f.values.length + " selected" : f.values.join(", ")}` : label;
      const fmt = (v) => (d.unit === "%" ? v + "%" : d.unit === "$" ? v : U.fmtInput(v));
      if (f.min != null && f.max != null) return `${label}  ${fmt(f.min)} to ${fmt(f.max)}`;
      if (f.min != null) return `${label} > ${fmt(f.min)}`;
      if (f.max != null) return `${label} < ${fmt(f.max)}`;
      return label;
    },

    isSet(f) { return FIELDS[f.field].list ? !!(f.values && f.values.length) : f.min != null || f.max != null; },

    renderChips() {
      const box = Screener.chips; box.replaceChildren();
      const s = Screener.screen();
      s.filters.forEach((f, i) => {
        if (!FIELDS[f.field]) return;
        const x = U.el("span", { class: "x", title: "Remove filter" }, "✕");
        const chip = U.el("div", { class: "chip" + (Screener.isSet(f) ? " set" : ""), id: "chip-" + f.field }, U.el("span", {}, Screener.chipText(f)), x);
        x.onclick = (e) => { e.stopPropagation(); s.filters.splice(i, 1); Screener.changed(); };
        chip.onclick = () => Screener.editFilter(f, chip);
        box.append(chip);
      });
      const add = U.el("div", { class: "chip add", id: "chip-add" }, "+ Add filter");
      add.onclick = () => {
        const used = new Set(s.filters.map((f) => f.field));
        const m = U.el("div", {}, U.el("h4", {}, "Add filter"));
        Object.entries(FIELDS).filter(([k]) => !used.has(k)).forEach(([k, d]) => {
          const label = d.sess ? (SESS_PREFIX[Screener.session()] + " " + d.label).trim() : d.label;
          m.append(U.el("div", { class: "menu-item", onclick: () => {
            const f = d.list ? { field: k, values: [] } : { field: k, min: null, max: null };
            s.filters.push(f); U.closePops(); Screener.renderChips();
            Screener.editFilter(f, U.$("#chip-" + k));
          } }, label[0].toUpperCase() + label.slice(1)));
        });
        U.pop(add, m);
      };
      box.append(add);
    },

    editFilter(f, chip) {
      const d = FIELDS[f.field];
      const box = U.el("div", { style: "width:280px" }, U.el("h4", {}, Screener.chipText({ field: f.field })));
      if (d.list) {
        const vals = new Set(f.values || []);
        const list = U.el("div", { style: "max-height:320px;overflow:auto" });
        d.list.forEach((v) => {
          const c = U.el("input", { type: "checkbox" }); c.checked = vals.has(v);
          c.onchange = () => { c.checked ? vals.add(v) : vals.delete(v); f.values = [...vals]; Screener.changed(); };
          list.append(U.el("label", { class: "check" }, c, v));
        });
        box.append(list);
        U.pop(chip, box);
        return;
      }
      const unit = d.unit === "%" ? " (%)" : "";
      const mn = U.el("input", { type: "text", placeholder: "Min" + unit, value: d.unit ? (f.min ?? "") : U.fmtInput(f.min), style: "flex:1" });
      const mx = U.el("input", { type: "text", placeholder: "Max" + unit, value: d.unit ? (f.max ?? "") : U.fmtInput(f.max), style: "flex:1" });
      const apply = () => { f.min = U.parseNum(mn.value); f.max = U.parseNum(mx.value); U.closePops(); Screener.changed(); };
      const presets = U.el("div", { class: "presets" });
      (d.presets || []).forEach(([t, a, b]) => presets.append(U.el("button", { onclick: () => { f.min = a; f.max = b; U.closePops(); Screener.changed(); } }, t)));
      [mn, mx].forEach((i) => (i.onkeydown = (e) => { if (e.key === "Enter") apply(); }));
      box.append(presets,
        U.el("div", { class: "row" }, mn, U.el("span", { class: "muted" }, "to"), mx),
        U.el("div", { class: "muted", style: "font-size:11.5px;margin-bottom:10px" }, d.unit ? "Leave blank for no limit." : "Use K / M / B suffixes, e.g. 300K, 25M."),
        U.el("div", { class: "row", style: "justify-content:flex-end;margin:0" },
          U.el("button", { class: "btn sm", onclick: () => { f.min = f.max = null; U.closePops(); Screener.changed(); } }, "Clear"),
          U.el("button", { class: "btn sm primary", onclick: apply }, "Apply")));
      U.pop(chip, box);
      setTimeout(() => mn.focus(), 30);
    },

    // ------------------------------------------------------------ table
    cols() {
      const sess = Screener.data ? Screener.data.session : Screener.session();
      return COLS.filter((c) => !(c.sess && sess === "regular"))
        .map((c) => ({ ...c, label: c.label.replace("{S}", SESS_PREFIX[sess] || "") }));
    },

    sorted(rows) {
      const s = Screener.screen().sort || { field: "sc", dir: "desc" };
      let k = s.field;
      if (Screener.data && Screener.data.session === "regular") k = { sp: "close", sc: "change", sv: "volume" }[k] || k;
      const m = s.dir === "desc" ? -1 : 1;
      return rows.slice().sort((a, b) => {
        const x = a[k], y = b[k];
        if (x == null && y == null) return 0;
        if (x == null) return 1;
        if (y == null) return -1;
        return (typeof x === "string" ? x.localeCompare(y) : x - y) * m;
      });
    },

    renderTable() {
      const cols = Screener.cols();
      const s = Screener.screen();
      const sortK = s.sort && s.sort.field;
      Screener.thead.replaceChildren(U.el("tr", {}, cols.map((c) => U.el("th", {
        class: (c.l ? "l " : "") + (sortK === c.k ? "sorted" : ""), "data-k": c.k,
        html: c.label + (sortK === c.k ? `<span class="arr">${s.sort.dir === "desc" ? "↓" : "↑"}</span>` : ""),
      }))));
      const d = Screener.data;
      const sessName = { pre: "Pre-market", regular: "Regular hours", post: "Post-market" }[d ? d.session : Screener.session()];
      Screener.title.innerHTML = `${U.esc(s.name)} <span class="sub">· ${sessName}${d ? ` · ${d.rows.length} symbols` : ""}</span>`;
      const cnt = U.$("#tab-count-" + s.id); if (cnt) cnt.textContent = d ? d.rows.length : "";
      if (!d) { Screener.tbody.replaceChildren(U.el("tr", {}, U.el("td", { colspan: cols.length, class: "empty" }, U.el("div", { class: "big" }, "⏳"), "Loading screener…"))); return; }
      if (!d.rows.length) { Screener.tbody.replaceChildren(U.el("tr", {}, U.el("td", { colspan: cols.length, class: "empty" }, U.el("div", { class: "big" }, "🔍"), "No symbols match these filters right now. You'll hear the bell when one shows up."))); return; }
      const frag = document.createDocumentFragment();
      for (const r of Screener.sorted(d.rows)) {
        const tr = U.el("tr", { "data-t": r.ticker });
        if (r.ticker === Screener.selected) tr.classList.add("sel");
        if (r.is_new && !Screener.flashed.has(r.ticker + r.first_seen)) { tr.classList.add("new"); Screener.flashed.add(r.ticker + r.first_seen); }
        for (const c of cols) {
          const td = U.el("td", { class: c.l ? "l" : "" });
          if (c.k === "symbol") {
            const b = r.borrow || { status: "na", label: "N/A" };
            const bTag = U.el("span", {
              class: "tag-borrow " + b.status,
              title: `Borrow: ${b.label} (${b.status === "easy" ? "Easy to borrow" : b.status === "hard" ? "Hard to borrow" : b.status === "none" ? "No borrow available" : "N/A"})`
            }, b.label);
            td.append(U.el("div", { class: "sym" }, U.logo(r.logoid, r.symbol), U.el("span", { class: "tkr" }, r.symbol), bTag, r.is_new ? U.el("span", { class: "tag-new" }, "NEW") : null));
          } else if (c.k === "desc") {
            td.append(U.el("div", { class: "desc", title: r.desc }, r.desc));
          } else if (c.k === "news_ts") {
            if (r.news) td.append(U.el("span", { class: "news-flag" + (r.news_bz ? " bz" : ""), title: `${r.news} recent headline(s)` }, `📰 ${r.news} · ${U.ago(r.news_ts).replace(" ago", "")}`));
            else td.append(U.el("span", { class: "muted" }, "—"));
          } else {
            td.textContent = c.f(r);
            if (c.c) { const k = c.c(r); if (k) td.classList.add(k); }
          }
          tr.append(td);
        }
        frag.append(tr);
      }
      Screener.tbody.replaceChildren(frag);
    },
  };
  window.Screener = Screener;
})();
