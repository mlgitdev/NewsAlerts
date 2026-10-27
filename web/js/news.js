/* News pane: recent headlines (Benzinga highlighted) + BamSEC SEC filings. */
(function () {
  const RECENCY = [
    [1, "1h"],
    [2, "2h"],
    [4, "4h"],
    [8, "8h"],
    [12, "12h"],
    [24, "24h"],
    [72, "3d"],
    [168, "7d"],
  ];

  const News = {
    ticker: null,
    info: null,
    seen: new Set(),
    timer: null,
    open: new Set(),
    reqId: 0,
    bamsecData: null,
    bamsecLoading: false,
    bamsecActiveTab: "wire",
    bamsecFilter: "all",
    bamsecDrawerFilter: "all",
    bamsecSearchTerm: "",

    mount() {
      News.head = U.$("#news-head");
      News.tools = U.$("#news-tools");
      News.list = U.$("#news-list");
      News.symInput = U.$("#news-sym-input");
      News.symBtn = U.$("#news-sym-go");
      News.chips = U.$("#news-chips");

      // BamSEC elements
      News.subtabs = U.$("#news-subtabs");
      News.subtabWire = U.$("#subtab-wire");
      News.subtabBamsec = U.$("#subtab-bamsec");
      News.tabBadge = U.$("#bamsec-tab-badge");
      News.modeToggleBtn = U.$("#btn-bamsec-mode-toggle");
      News.drawer = U.$("#bamsec-drawer");
      News.fullView = U.$("#bamsec-full-view");

      if (News.symInput) {
        News.symInput.onkeydown = (e) => {
          if (e.key === "Enter") {
            e.preventDefault();
            News.submitCustomSymbol();
          }
        };
      }
      if (News.symBtn) {
        News.symBtn.onclick = () => News.submitCustomSymbol();
      }

      if (News.subtabWire) {
        News.subtabWire.onclick = () => News.switchSubtab("wire");
      }
      if (News.subtabBamsec) {
        News.subtabBamsec.onclick = () => News.switchSubtab("bamsec");
      }
      if (News.modeToggleBtn) {
        News.modeToggleBtn.onclick = () => News.toggleLayoutMode();
      }

      const bz = U.el("input", { type: "checkbox", id: "news-bz-only" });
      const rec = U.el("select", { id: "news-recency" }, RECENCY.map(([v, t]) => U.el("option", { value: v }, t)));
      News.count = U.el("span", { class: "muted", style: "margin-left:auto" });
      News.tools.append(
        U.el("label", { class: "check", style: "display:flex;gap:6px;align-items:center;cursor:pointer" }, bz, "Benzinga only"),
        U.el("span", { class: "muted" }, "· last"),
        rec,
        News.count
      );
      News.bz = bz;
      News.rec = rec;
      News.syncTools();
      bz.onchange = () => { App.config.news.benzinga_only = bz.checked; App.saveConfig(true); News.load(false); };
      rec.onchange = () => { App.config.news.recency_hours = +rec.value; App.saveConfig(true); News.load(false); };
      News.list.addEventListener("click", News.onClick);
      App.sub("select", (t) => { Screener.select(t); });
      App.sub("config", News.syncTools);
      News.renderChips();
      News.renderEmpty();
    },

    syncTools() {
      News.bz.checked = !!App.config.news.benzinga_only;
      const h = App.config.news.recency_hours;
      if (!RECENCY.some(([v]) => v === h)) {
        const lbl = h >= 24 && h % 24 === 0 ? `${h / 24}d` : `${h}h`;
        News.rec.append(U.el("option", { value: h }, lbl));
      }
      News.rec.value = h;
      News.renderChips();
      const cfg = App.config.news || {};
      if (News.modeToggleBtn) {
        News.modeToggleBtn.textContent = cfg.bamsec_mode === "tabs" ? "⊟ Drawer View" : "⊞ Tabs View";
      }
      News.renderBamsec();
    },

    async submitCustomSymbol() {
      if (!News.symInput) return;
      const raw = News.symInput.value.trim().toUpperCase();
      if (!raw) return;
      const sym = raw.split(":").pop().replace(/[^A-Z0-9.\-]/g, "");
      if (!sym) return;

      News.symInput.disabled = true;
      if (News.symBtn) { News.symBtn.disabled = true; News.symBtn.textContent = "…"; }

      try {
        const q = await App.api().get_quote(sym);
        if (!q || !q.ticker) {
          U.toast("alert", "⚠️ Symbol Not Found", `Symbol "${sym}" was not found on US exchanges (AMEX, NASDAQ, NYSE).`, null, 5000);
          return;
        }

        const list = App.config.news.custom_symbols || (App.config.news.custom_symbols = []);
        const cleanSym = q.symbol || sym;
        const idx = list.indexOf(cleanSym);
        if (idx >= 0) list.splice(idx, 1);
        list.unshift(cleanSym);
        if (list.length > 15) list.length = 15;
        App.saveConfig(true);
        News.renderChips();

        News.symInput.value = "";
        await News.select(q.ticker, q);
      } catch (err) {
        U.toast("alert", "⚠️ Lookup Failed", String(err), null, 4000);
      } finally {
        News.symInput.disabled = false;
        if (News.symBtn) { News.symBtn.disabled = false; News.symBtn.textContent = "Inspect"; }
        News.symInput.focus();
      }
    },

    renderChips() {
      if (!News.chips) return;
      const list = App.config.news.custom_symbols || [];
      if (!list.length) {
        News.chips.replaceChildren();
        return;
      }
      const activeSym = News.ticker ? News.ticker.split(":").pop().toUpperCase() : "";
      const chips = list.map((s) => {
        const chip = U.el("span", {
          class: "news-chip" + (s.toUpperCase() === activeSym ? " active" : ""),
          title: `Inspect ${s} catalyst wire`
        }, s);
        const del = U.el("span", {
          class: "news-chip-del",
          title: `Remove ${s} from custom watchlist`,
          onclick: (e) => {
            e.stopPropagation();
            const arr = App.config.news.custom_symbols || [];
            const i = arr.indexOf(s);
            if (i >= 0) arr.splice(i, 1);
            App.saveConfig(true);
            News.renderChips();
          }
        }, "×");
        chip.append(del);
        chip.onclick = () => News.selectCustomSymbol(s);
        return chip;
      });
      News.chips.replaceChildren(...chips);
    },

    async selectCustomSymbol(sym) {
      if (!sym) return;
      try {
        const q = await App.api().get_quote(sym);
        if (q && q.ticker) {
          News.select(q.ticker, q);
        } else {
          News.select(sym, null);
        }
      } catch (e) {
        News.select(sym, null);
      }
      News.renderChips();
    },

    renderEmpty() {
      News.head.replaceChildren(U.el("div", { class: "pane-title" }, "📰 News"));
      News.list.replaceChildren(
        U.el("div", { class: "news-empty-hero" },
          U.el("img", { src: "img/hero.jpg", class: "news-hero-img", alt: "NewsAlerts Hero" }),
          U.el("div", { class: "news-hero-caption" },
            U.el("div", { class: "news-hero-title" }, "Real-Time Momentum Intelligence"),
            U.el("div", { class: "news-hero-sub" }, "Click any symbol from the Screener or Tape, or enter a custom US symbol above to inspect live catalyst news and BamSEC filings.")
          )
        )
      );
      if (News.subtabs) News.subtabs.style.display = "none";
      if (News.drawer) News.drawer.style.display = "none";
      if (News.fullView) News.fullView.style.display = "none";
      News.renderChips();
    },

    async select(ticker, info) {
      if (News.ticker !== ticker) {
        News.seen = new Set();
        News.open = new Set();
        News.bamsecData = null;
        News.bamsecSearchTerm = "";
      }
      // Always return to wire news tab when selecting any ticker
      News.bamsecActiveTab = "wire";
      News.ticker = ticker;
      News.info = info || null;
      News.renderHead();
      News.renderChips();

      App.api().get_quote(ticker).then((q) => {
        if (q && News.ticker === ticker) {
          News.info = Object.assign({}, News.info, q);
          News.renderHead();
        }
      });

      News.list.replaceChildren(U.el("div", { class: "empty" }, "Loading news…"));
      await News.load(false, true);

      // Trigger BamSEC filing load
      News.bamsecActiveTab = "wire";
      const cfg = App.config.news || {};
      if (cfg.bamsec_enabled !== false) {
        News.loadBamsec(ticker, false);
      } else {
        News.bamsecData = null;
        News.renderBamsec();
      }

      clearInterval(News.timer);
      News.timer = setInterval(() => {
        News.load(true);
        const c = App.config.news || {};
        if (c.bamsec_enabled !== false) {
          News.loadBamsec(News.ticker, false);
        }
      }, Math.max(10, App.config.poll.news_sec) * 1000);
    },

    renderHead() {
      const i = News.info || {};
      const sym = i.symbol || (News.ticker ? News.ticker.split(":").pop() : "");
      if (!sym) return;

      const cfg = App.config.news || {};
      const bamsecEnabled = cfg.bamsec_enabled !== false;

      const refresh = U.el("button", { class: "icon-btn", id: "news-refresh", title: "Refresh", html: U.icons.refresh });
      const chart = U.el("button", { class: "icon-btn", id: "news-chart", title: "Open chart on TradingView", html: U.icons.chart });
      refresh.onclick = () => {
        News.load(true);
        if (bamsecEnabled) News.loadBamsec(News.ticker, true);
      };
      chart.onclick = () => App.api().open_chart(News.ticker);

      // Direct BamSEC external launch button (ONLY if BamSEC is enabled)
      let bamsecBtn = null;
      if (bamsecEnabled) {
        const bamsecUrl = (News.bamsecData && News.bamsecData.bamsec_url) ? News.bamsecData.bamsec_url : `https://www.bamsec.com/search?q=${sym}`;
        bamsecBtn = U.el("button", {
          class: "btn-bamsec-link",
          id: "news-bamsec-btn",
          title: `Open ${sym} filings directly on BamSEC in browser`,
          onclick: () => App.api().open_url(bamsecUrl)
        }, "📑 BamSEC ↗");
      }

      const b = i.borrow || { status: "na", label: "N/A" };
      const bTag = U.el("span", {
        class: "tag-borrow " + b.status,
        style: "margin-left:8px;vertical-align:middle;",
        title: `Borrow: ${b.label} (${b.status === "easy" ? "Easy to borrow" : b.status === "hard" ? "Hard to borrow" : b.status === "none" ? "No borrow available" : "N/A"})`
      }, b.label);

      // BamSEC filings badge in header (ONLY if BamSEC is enabled)
      let bamsecBadge = null;
      if (bamsecEnabled && News.bamsecData && News.bamsecData.total > 0) {
        bamsecBadge = U.el("span", {
          class: "tag-bamsec-count",
          title: `${News.bamsecData.total} SEC Filings found on BamSEC. Click to view.`,
          onclick: () => {
            if (cfg.bamsec_mode === "tabs") {
              News.switchSubtab("bamsec");
            } else {
              News.toggleDrawer(true);
            }
          }
        }, `📑 ${News.bamsecData.total} SEC`);
      }

      // Snapshot & Market Data from Alpaca
      const snap = i.snapshot || {};
      const details = i.details || {};
      const metaParts = [];
      if (i.desc) metaParts.push(i.desc);
      if (i.float) metaParts.push("Float " + U.big(i.float));
      if (snap.bid != null && snap.ask != null && (snap.bid > 0 || snap.ask > 0)) {
        metaParts.push(`B/A: $${snap.bid.toFixed(2)} × ${snap.bid_size || 0} / $${snap.ask.toFixed(2)} × ${snap.ask_size || 0}`);
      }
      if (snap.vwap != null && snap.vwap > 0) {
        metaParts.push(`VWAP: $${snap.vwap.toFixed(2)}`);
      }
      if (details.marginable) {
        metaParts.push("Marginable");
      }

      const addBtn = U.el("button", {
        class: "btn-wl-add",
        title: `Add ${sym} to active TradingView watchlist`,
        onclick: (e) => {
          e.stopPropagation();
          if (window.App && App.handleAddToWatchlist) {
            App.handleAddToWatchlist(addBtn, News.ticker || sym);
          }
        }
      }, "+");

      const bannedList = (window.App && App.config && App.config.banned_symbols) ? App.config.banned_symbols.map((x) => x.toUpperCase()) : [];
      const isBanned = bannedList.includes((sym || "").toUpperCase()) || bannedList.includes((News.ticker || "").split(":").pop().toUpperCase());
      const banBtn = U.el("button", {
        class: "btn-ban-sym" + (isBanned ? " is-banned" : ""),
        title: isBanned ? `Symbol ${sym} is banned (closing-only). Click to unban.` : `Ban ${sym} (IB Closing-Only / Restricted)`,
        onclick: (e) => {
          e.stopPropagation();
          if (window.App) {
            if (isBanned) App.unbanSymbol(News.ticker || sym);
            else App.banSymbol(News.ticker || sym);
            News.renderHead();
          }
        }
      }, "🚫");

      News.head.replaceChildren(
        U.el("div", { class: "news-head" }, U.logo(i.logoid, sym),
          U.el("div", {},
            U.el("div", { class: "name" }, sym, " ", addBtn, " ", banBtn,
              i.sp != null ? U.el("span", { class: "num", style: "font-weight:500;margin-left:6px" }, U.price(i.sp)) : null,
              i.sc != null ? U.el("span", { class: "num " + U.cls(i.sc), style: "font-weight:600;margin-left:6px;font-size:12.5px" }, U.pct(i.sc)) : null,
              bTag,
              bamsecBadge),
            U.el("div", { class: "sub", title: metaParts.join(" · ") }, metaParts.join(" · ")))),
        U.el("div", { class: "spacer" }), bamsecBtn, chart, refresh);
    },

    async load(force, first) {
      const t = News.ticker; if (!t) return;
      const id = ++News.reqId;
      const res = await App.api().get_news(t, !!force);
      if (id !== News.reqId || t !== News.ticker) return;
      const items = res.items || [];
      const fresh = items.filter((i) => !News.seen.has(i.id));
      const isFirst = first || News.seen.size === 0;
      items.forEach((i) => News.seen.add(i.id));
      if (!isFirst && fresh.length) {
        App.api().play_alert("news");
        U.toast("news", `📰 ${t.split(":").pop()} — new headline`, fresh[0].title, null, 6000);
      }
      News.render(items, isFirst ? new Set() : new Set(fresh.map((f) => f.id)), res.total);
    },

    async loadBamsec(ticker, force) {
      if (!ticker) return;
      const cfg = App.config.news || {};
      if (cfg.bamsec_enabled === false) {
        News.bamsecData = null;
        News.renderBamsec();
        News.renderHead();
        return;
      }
      News.bamsecLoading = true;
      try {
        const res = await App.api().get_bamsec(ticker, !!force);
        if (News.ticker === ticker) {
          News.bamsecData = res;
          if (News.tabBadge) News.tabBadge.textContent = res.total || 0;
          News.renderBamsec();
          News.renderHead();
        }
      } catch (err) {
        console.warn("BamSEC load failed:", err);
      } finally {
        News.bamsecLoading = false;
      }
    },

    onConfigChanged() {
      const cfg = App.config.news || {};
      if (cfg.bamsec_enabled === false) {
        News.bamsecData = null;
        News.bamsecActiveTab = "wire";
        News.renderBamsec();
        News.renderHead();
      } else {
        News.renderBamsec();
        News.renderHead();
        if (News.ticker && !News.bamsecData) {
          News.loadBamsec(News.ticker, false);
        }
      }
    },

    renderBamsec() {
      const cfg = App.config.news || {};
      if (cfg.bamsec_enabled === false) {
        if (News.subtabs) News.subtabs.style.display = "none";
        if (News.drawer) News.drawer.style.display = "none";
        if (News.fullView) News.fullView.style.display = "none";
        if (News.tools) News.tools.style.display = "";
        if (News.list) News.list.style.display = "";
        return;
      }

      const mode = cfg.bamsec_mode || "drawer";

      if (mode === "tabs") {
        if (News.drawer) News.drawer.style.display = "none";
        if (News.subtabs) News.subtabs.style.display = "";

        if (News.bamsecActiveTab === "bamsec") {
          if (News.subtabWire) News.subtabWire.classList.remove("active");
          if (News.subtabBamsec) News.subtabBamsec.classList.add("active");
          if (News.tools) News.tools.style.display = "none";
          if (News.list) News.list.style.display = "none";
          if (News.fullView) {
            News.fullView.style.display = "";
            News.renderBamsecFullView();
          }
        } else {
          if (News.subtabWire) News.subtabWire.classList.add("active");
          if (News.subtabBamsec) News.subtabBamsec.classList.remove("active");
          if (News.tools) News.tools.style.display = "";
          if (News.list) News.list.style.display = "";
          if (News.fullView) News.fullView.style.display = "none";
        }
      } else {
        // Drawer mode
        if (News.subtabs) News.subtabs.style.display = "none";
        if (News.fullView) News.fullView.style.display = "none";
        if (News.tools) News.tools.style.display = "";
        if (News.list) News.list.style.display = "";
        News.renderBamsecDrawer();
      }
    },

    renderBamsecDrawer() {
      if (!News.drawer) return;
      const cfg = App.config.news || {};
      if (cfg.bamsec_enabled === false || cfg.bamsec_mode === "tabs") {
        News.drawer.style.display = "none";
        return;
      }

      const data = News.bamsecData;
      if (!data || !data.ticker) {
        News.drawer.style.display = "none";
        return;
      }

      News.drawer.style.display = "";
      const total = data.total || 0;
      const isOpen = cfg.bamsec_drawer_open !== false;
      News.drawer.classList.toggle("collapsed", !isOpen);

      const all = data.all_filings || [];
      const newsCount = all.filter((f) => f.group === "news").length;
      const offeringCount = all.filter((f) => f.group === "offering").length;
      const ownCount = all.filter((f) => f.group === "ownership").length;
      const finCount = all.filter((f) => f.group === "financial").length;

      const arrow = U.el("span", { class: "bamsec-drawer-arrow" }, "▼");
      const title = U.el("span", { class: "bamsec-drawer-title" }, "⚡ BamSEC SEC Filings");
      const badge = U.el("span", { class: "bamsec-drawer-badge" }, `${total} Filings`);

      const summaryParts = [];
      if (newsCount) summaryParts.push(`News: ${newsCount}`);
      if (offeringCount) summaryParts.push(`Dilution: ${offeringCount}`);
      if (ownCount) summaryParts.push(`Insiders: ${ownCount}`);
      const summaryText = summaryParts.length ? `(${summaryParts.join(" · ")})` : "";
      const summaryEl = U.el("span", { class: "bamsec-drawer-summary" }, summaryText);

      const extBtn = U.el("button", {
        class: "bamsec-ext-btn",
        title: "Open full company filings page on BamSEC.com",
        onclick: (e) => {
          e.stopPropagation();
          App.api().open_url(data.bamsec_url || `https://www.bamsec.com/search?q=${data.ticker}`);
        }
      }, "BamSEC ↗");

      const modeBtn = U.el("button", {
        class: "btn-mode-toggle",
        title: "Switch layout to Sub-Tabs mode",
        onclick: (e) => {
          e.stopPropagation();
          News.toggleLayoutMode();
        }
      }, "⊞ Tabs");

      const head = U.el("div", { class: "bamsec-drawer-head" },
        arrow, title, badge, summaryEl,
        U.el("div", { class: "spacer" }),
        extBtn, modeBtn
      );
      head.onclick = () => News.toggleDrawer();

      // Drawer body with category pills & filings list
      const currentFilter = News.bamsecDrawerFilter || "all";
      const pillFilters = [
        ["all", `All (${total})`],
        ["news", `News 8-K/6-K (${newsCount})`],
        ["offering", `Offerings & Dilution (${offeringCount})`],
        ["ownership", `Ownership (${ownCount})`],
        ["financial", `Financials (${finCount})`],
      ];

      const pillsWrap = U.el("div", { class: "bamsec-pills" },
        pillFilters.map(([fVal, fLabel]) => {
          const p = U.el("button", {
            class: "bamsec-pill" + (currentFilter === fVal ? " active" : ""),
            onclick: (e) => {
              e.stopPropagation();
              News.bamsecDrawerFilter = fVal;
              News.renderBamsecDrawer();
            }
          }, fLabel);
          return p;
        })
      );

      const filteredFilings = currentFilter === "all" ? all : all.filter((f) => f.group === currentFilter);
      const rows = filteredFilings.map((f) => {
        const row = U.el("div", {
          class: "bamsec-filing-row",
          title: `[${f.form}] ${f.title} (${f.date}) — Click to open on BamSEC`,
          onclick: () => App.api().open_url(f.url)
        },
          U.el("span", { class: `tag-form ${f.group}` }, f.form),
          U.el("span", { class: "bamsec-filing-title" }, f.title),
          U.el("span", { class: "bamsec-filing-date" }, f.date),
          U.el("span", { class: "bamsec-filing-link" }, "↗")
        );
        return row;
      });

      const listWrap = U.el("div", { class: "bamsec-filing-list" },
        rows.length ? rows : U.el("div", { class: "muted", style: "padding:8px 4px;font-size:11.5px" }, "No filings in this category.")
      );

      const body = U.el("div", { class: "bamsec-drawer-body" }, pillsWrap, listWrap);
      News.drawer.replaceChildren(head, body);
    },

    renderBamsecFullView() {
      if (!News.fullView) return;
      const data = News.bamsecData;
      if (!data || !data.ticker) {
        News.fullView.replaceChildren(
          U.el("div", { class: "empty" },
            News.bamsecLoading ? "Loading BamSEC filings…" : "No BamSEC filings available for this symbol.")
        );
        return;
      }

      const total = data.total || 0;
      const all = data.all_filings || [];

      const searchInput = U.el("input", {
        type: "text",
        class: "bamsec-search-input",
        placeholder: "Filter filings (e.g. shelf, dividend)...",
        value: News.bamsecSearchTerm || ""
      });
      searchInput.oninput = () => {
        News.bamsecSearchTerm = searchInput.value.toLowerCase().trim();
        News.renderBamsecFullView();
      };

      const extBtn = U.el("button", {
        class: "btn-bamsec-link",
        onclick: () => App.api().open_url(data.bamsec_url || `https://www.bamsec.com/search?q=${data.ticker}`)
      }, "Open Company Page ↗");

      const fullHead = U.el("div", { class: "bamsec-full-head" },
        U.el("div", {},
          U.el("div", { class: "bamsec-full-company" }, data.company || data.ticker),
          U.el("div", { class: "muted", style: "font-size:11px;margin-top:2px;" }, `${total} official SEC filings indexed on BamSEC`)
        ),
        U.el("div", { style: "display:flex;align-items:center;gap:8px" }, searchInput, extBtn)
      );

      const newsCount = all.filter((f) => f.group === "news").length;
      const offeringCount = all.filter((f) => f.group === "offering").length;
      const ownCount = all.filter((f) => f.group === "ownership").length;
      const finCount = all.filter((f) => f.group === "financial").length;

      const currentFilter = News.bamsecFilter || "all";
      const pillFilters = [
        ["all", `All (${total})`],
        ["news", `News 8-K/6-K (${newsCount})`],
        ["offering", `Offerings & Dilution (${offeringCount})`],
        ["ownership", `Ownership (${ownCount})`],
        ["financial", `Financials (${finCount})`],
      ];

      const pillsWrap = U.el("div", { class: "bamsec-pills" },
        pillFilters.map(([fVal, fLabel]) => {
          const p = U.el("button", {
            class: "bamsec-pill" + (currentFilter === fVal ? " active" : ""),
            onclick: () => {
              News.bamsecFilter = fVal;
              News.renderBamsecFullView();
            }
          }, fLabel);
          return p;
        })
      );

      const term = News.bamsecSearchTerm || "";
      let matched = all;
      if (currentFilter !== "all") {
        matched = matched.filter((f) => f.group === currentFilter);
      }
      if (term) {
        matched = matched.filter((f) => (
          f.title.toLowerCase().includes(term) ||
          f.form.toLowerCase().includes(term) ||
          (f.category && f.category.toLowerCase().includes(term))
        ));
      }

      const sections = [];
      const cats = data.categories || {};
      const catNames = Object.keys(cats);

      if (catNames.length && currentFilter === "all" && !term) {
        for (const cName of catNames) {
          const cItems = cats[cName] || [];
          if (!cItems.length) continue;
          const cRows = cItems.map((f) => U.el("div", {
            class: "bamsec-filing-row",
            title: `[${f.form}] ${f.title} (${f.date}) — Click to view on BamSEC`,
            onclick: () => App.api().open_url(f.url)
          },
            U.el("span", { class: `tag-form ${f.group}` }, f.form),
            U.el("span", { class: "bamsec-filing-title" }, f.title),
            U.el("span", { class: "bamsec-filing-date" }, f.date),
            U.el("span", { class: "bamsec-filing-link" }, "↗")
          ));

          sections.push(U.el("div", { class: "bamsec-cat-section" },
            U.el("div", { class: "bamsec-cat-head" },
              U.el("span", {}, cName),
              U.el("span", { class: "muted num" }, `${cItems.length}`)
            ),
            U.el("div", {}, ...cRows)
          ));
        }
      } else {
        const rows = matched.map((f) => U.el("div", {
          class: "bamsec-filing-row",
          title: `[${f.form}] ${f.title} (${f.date}) — Click to view on BamSEC`,
          onclick: () => App.api().open_url(f.url)
        },
          U.el("span", { class: `tag-form ${f.group}` }, f.form),
          U.el("span", { class: "bamsec-filing-title" }, f.title),
          U.el("span", { class: "bamsec-filing-date" }, f.date),
          U.el("span", { class: "bamsec-filing-link" }, "↗")
        ));

        sections.push(U.el("div", { class: "bamsec-cat-section" },
          rows.length ? rows : U.el("div", { class: "muted", style: "padding:12px 4px;font-size:12px" }, "No matching filings found.")
        ));
      }

      News.fullView.replaceChildren(fullHead, pillsWrap, ...sections);
    },

    toggleDrawer(forceOpen) {
      const cfg = App.config.news || {};
      const willOpen = forceOpen != null ? forceOpen : !cfg.bamsec_drawer_open;
      cfg.bamsec_drawer_open = willOpen;
      App.saveConfig(true);
      if (News.drawer) {
        News.drawer.classList.toggle("collapsed", !willOpen);
      }
    },

    toggleLayoutMode() {
      const cfg = App.config.news || {};
      const newMode = (cfg.bamsec_mode === "tabs") ? "drawer" : "tabs";
      cfg.bamsec_mode = newMode;
      App.saveConfig(true);
      U.toast("info", "Layout Updated", `BamSEC view switched to ${newMode === "tabs" ? "Sub-Tabs" : "Collapsible Drawer"}.`);
      if (News.modeToggleBtn) {
        News.modeToggleBtn.textContent = newMode === "tabs" ? "⊟ Drawer View" : "⊞ Tabs View";
      }
      News.renderBamsec();
    },

    switchSubtab(tab) {
      News.bamsecActiveTab = tab;
      News.renderBamsec();
    },

    render(items, freshIds, total) {
      const h = App.config.news.recency_hours;
      const recLbl = h >= 24 && h % 24 === 0 ? `${h / 24}d` : `${h}h`;
      News.count.textContent = `${items.length} of ${total}`;
      if (!items.length) {
        News.list.replaceChildren(U.el("div", { class: "empty" }, U.el("div", { class: "big" }, "🌙"),
          `No ${App.config.news.benzinga_only ? "Benzinga " : ""}news in the last ${recLbl}.`));
        return;
      }
      const frag = document.createDocumentFragment();
      for (const it of items) {
        const hot = Date.now() / 1000 - it.published < 3600;
        const prov = it.provider === "benzinga" ? "benzinga" : (it.source || it.provider);
        const el = U.el("div", { class: "news-item" + (freshIds.has(it.id) ? " fresh" : "") + (News.open.has(it.id) ? " open" : ""), "data-id": it.id, "data-link": it.link },
          U.el("div", { class: "news-meta" },
            U.el("span", { class: "prov " + prov }, it.source || it.provider),
            U.el("span", { class: "num" }, U.timeET(it.published, false) + " ET"),
            U.el("span", { class: "age" + (hot ? " hot" : "") }, U.ago(it.published))),
          U.el("div", { class: "news-title" }, it.title),
          it.summary ? U.el("div", { class: "news-summary", style: "font-size:11.5px;color:var(--muted);margin-top:4px;line-height:1.4;" }, it.summary) : null);
        frag.append(el);
        if (News.open.has(it.id)) News.expand(el, it.id);
      }
      News.list.replaceChildren(frag);
    },

    onClick(e) {
      const act = e.target.closest("[data-act]");
      const item = e.target.closest(".news-item");
      if (!item) return;
      if (act) {
        e.stopPropagation();
        if (act.dataset.act === "open") App.api().open_url(item.dataset.link);
        return;
      }
      if (e.target.closest(".story")) return;
      const id = item.dataset.id;
      if (News.open.has(id)) { News.open.delete(id); item.classList.remove("open"); const s = U.$(".story-wrap", item); s && s.remove(); }
      else { News.open.add(id); item.classList.add("open"); News.expand(item, id); }
    },

    async expand(item, id) {
      const wrap = U.el("div", { class: "story-wrap" }, U.el("div", { class: "story muted" }, "Loading story…"));
      item.append(wrap);
      const s = await App.api().get_story(id);
      wrap.replaceChildren(
        U.el("div", { class: "story", html: (s && s.html) || "<i>No story text available — open the article.</i>" }),
        U.el("div", { class: "story-actions" }, U.el("button", { class: "btn sm", "data-act": "open" }, "Open article ↗")));
    },

    closeAllStories() {
      News.open.clear();
      if (News.list) {
        U.$$(".news-item.open", News.list).forEach((item) => {
          item.classList.remove("open");
          const s = item.querySelector(".story-wrap");
          if (s) s.remove();
        });
      }
    },

    openFirstStory() {
      if (!News.list) return false;
      const firstItem = News.list.querySelector(".news-item");
      if (firstItem) {
        firstItem.click();
        firstItem.scrollIntoView({ block: "nearest", behavior: "smooth" });
        return true;
      }
      return false;
    },
  };
  window.News = News;
})();
