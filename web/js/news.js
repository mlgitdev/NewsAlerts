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
    },

    renderEmpty() {
      News.head.replaceChildren(U.el("div", { class: "pane-title" }, "📰 News"));
      News.list.replaceChildren(U.el("div", { class: "empty" }, U.el("div", { class: "big" }, "📰"), "Click a symbol to see its latest news."));
    },

    async select(ticker, info) {
      if (News.ticker !== ticker) { News.seen = new Set(); News.open = new Set(); }
      News.ticker = ticker;
      News.info = info || null;
      News.renderHead();
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

      News.head.replaceChildren(
        U.el("div", { class: "news-head" }, U.logo(i.logoid, sym),
          U.el("div", {},
            U.el("div", { class: "name" }, sym, " ",
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
  };
  window.News = News;
})();
