/* News pane: recent headlines (Benzinga highlighted) for the selected symbol. */
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
    ticker: null, info: null, seen: new Set(), timer: null, open: new Set(), reqId: 0,

    mount() {
      News.head = U.$("#news-head");
      News.tools = U.$("#news-tools");
      News.list = U.$("#news-list");
      News.symInput = U.$("#news-sym-input");
      News.symBtn = U.$("#news-sym-go");
      News.chips = U.$("#news-chips");

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

      const bz = U.el("input", { type: "checkbox", id: "news-bz-only" });
      const rec = U.el("select", { id: "news-recency" }, RECENCY.map(([v, t]) => U.el("option", { value: v }, t)));
      News.count = U.el("span", { class: "muted", style: "margin-left:auto" });
      News.tools.append(U.el("label", { class: "check", style: "display:flex;gap:6px;align-items:center;cursor:pointer" }, bz, "Benzinga only"),
        U.el("span", { class: "muted" }, "· last"), rec, News.count);
      News.bz = bz; News.rec = rec;
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

        // Add to custom symbols list
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
            U.el("div", { class: "news-hero-sub" }, "Click any symbol from the Screener or Tape, or enter a custom US symbol above to inspect live catalyst news.")
          )
        )
      );
      News.renderChips();
    },

    async select(ticker, info) {
      if (News.ticker !== ticker) { News.seen = new Set(); News.open = new Set(); }
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
      clearInterval(News.timer);
      News.timer = setInterval(() => News.load(true), Math.max(10, App.config.poll.news_sec) * 1000);
    },

    renderHead() {
      const i = News.info || {};
      const sym = i.symbol || News.ticker.split(":").pop();
      const refresh = U.el("button", { class: "icon-btn", id: "news-refresh", title: "Refresh", html: U.icons.refresh });
      const chart = U.el("button", { class: "icon-btn", id: "news-chart", title: "Open chart on TradingView", html: U.icons.chart });
      refresh.onclick = () => News.load(true);
      chart.onclick = () => App.api().open_chart(News.ticker);
      const b = i.borrow || { status: "na", label: "N/A" };
      const bTag = U.el("span", {
        class: "tag-borrow " + b.status,
        style: "margin-left:8px;vertical-align:middle;",
        title: `Borrow: ${b.label} (${b.status === "easy" ? "Easy to borrow" : b.status === "hard" ? "Hard to borrow" : b.status === "none" ? "No borrow available" : "N/A"})`
      }, b.label);

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

      News.head.replaceChildren(
        U.el("div", { class: "news-head" }, U.logo(i.logoid, sym),
          U.el("div", {},
            U.el("div", { class: "name" }, sym, " ", addBtn,
              i.sp != null ? U.el("span", { class: "num", style: "font-weight:500;margin-left:6px" }, U.price(i.sp)) : null,
              i.sc != null ? U.el("span", { class: "num " + U.cls(i.sc), style: "font-weight:600;margin-left:6px;font-size:12.5px" }, U.pct(i.sc)) : null,
              bTag),
            U.el("div", { class: "sub", title: metaParts.join(" · ") }, metaParts.join(" · ")))),
        U.el("div", { class: "spacer" }), chart, refresh);
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
