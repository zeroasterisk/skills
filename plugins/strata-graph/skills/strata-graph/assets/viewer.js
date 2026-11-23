/* Strata Graph Interactive Viewer (Zero-Dependency Vanilla JS + SVG/DOM)
   Architectural heritage: Inspired by Adam Gospodarczyk's (@overment) limen picture (MIT).
   Independent multi-domain implementation adding:
   - Multi-dataset Hub tabs (strata-hub/1 & strata-graph/1)
   - Hierarchy vs Expanded Spine mode + OUTSIDE ghost lifting
   - Sugiyama + weighted PAV isotonic regression + 4.5px multi-lane colored bundles
   - Explicit outer return arcs (↺) for backtracks & cycles (no silent cycle erasure)
   - Blind-alley spur styling & filtering
   - 1-Hop / 2-Hop ego networks + Shift+Click Path Finder (A <-> B)
   - Temporal Trace / ATIF Trajectory Scrubber + Multi-Run Comparison
   - Smooth zoom & drag-to-pan + Dark/Light theme toggle */

(function () {
  "use strict";

  const SVG_NS = "http://www.w3.org/2000/svg";
  const FALLBACK_COLORS_DARK = ["#60a5fa", "#2dd4bf", "#a78bfa", "#fbbf24", "#4ade80", "#f87171", "#e879f9", "#22d3ee"];
  const FALLBACK_COLORS_LIGHT = ["#2563eb", "#0f766e", "#7c3aed", "#b45309", "#15803d", "#dc2626", "#c026d3", "#0891b2"];
  const TRACE_PALETTE = ["#60a5fa", "#34d399", "#f472b6", "#fbbf24", "#a78bfa", "#22d3ee"];

  const GEO = {
    cardW: 218,
    cardH: 94,
    ghostW: 204,
    ghostH: 64,
    sliceW: 204,
    sliceH: 68,
    dummyW: 12,
    colGap: 40,
    dummyGap: 14,
    rowGap: 68,
    bandGap: 56,
    padX: 36,
    padY: 28,
    laneGap: 4.5,
    portInset: 18,
    returnMargin: 38,
    returnLaneStep: 18
  };

  /* ------------------------------------------------------------- DOM utils */
  function h(tag, cls, text) {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text !== undefined && text !== null) node.textContent = String(text);
    return node;
  }

  // Data values (status, role, level, tier) become CSS class names, and classList.add
  // throws on whitespace, so reduce them to a safe token.
  function cssToken(value) {
    return String(value).toLowerCase().replace(/[^a-z0-9_-]+/g, "-").replace(/^-+|-+$/g, "");
  }

  function svgEl(tag, attrs, cls) {
    const node = document.createElementNS(SVG_NS, tag);
    if (cls) node.setAttribute("class", cls);
    if (attrs) {
      for (const [k, v] of Object.entries(attrs)) {
        if (v !== undefined && v !== null) node.setAttribute(k, String(v));
      }
    }
    return node;
  }

  function safeUrl(raw) {
    if (!raw || typeof raw !== "string") return null;
    try {
      const u = new URL(raw, window.location.href);
      if (u.protocol === "http:" || u.protocol === "https:") return u.href;
    } catch (_) {
      return null;
    }
    return null;
  }

  /* --------------------------------------------------------- Parse payload */
  const dataEl = document.getElementById("strata-data");
  if (!dataEl) return;
  let rawPayload;
  try {
    rawPayload = JSON.parse(dataEl.textContent || "{}");
  } catch (err) {
    document.body.textContent = "Failed to parse embedded Strata Graph JSON: " + String(err);
    return;
  }

  const hub = rawPayload.schema === "strata-hub/1"
    ? rawPayload
    : { schema: "strata-hub/1", title: rawPayload.title || "Strata Graph", datasets: [rawPayload] };

  const datasets = (hub.datasets || []).map(prepareDataset);
  if (!datasets.length) return;

  /* ----------------------------------------------------------------- State */
  const st = {
    dsIdx: 0,
    focusId: datasets[0].rootId,
    expandAll: false,
    hopDepth: 1,
    zoom: null, // null = auto-fit (capped at 1.0)
    scale: 1, // effective scale from the last applyScale, the start for zoom steps
    theme: document.documentElement.getAttribute("data-theme") || "dark",
    hiddenRels: new Set(),
    hideBlindAlleys: false,
    showAllSlices: false,
    selectedId: null,
    selectedBundleKey: null,
    compareTargetId: null,
    hoverId: null,
    hoverBundleKey: null,
    activeTraceIdx: datasets[0].traces.length ? 0 : -1,
    activeStepIdx: 0,
    playTimer: null,
    currentLayout: null
  };

  /* ----------------------------------------------------------- DOM handles */
  const dom = {
    hubBar: document.getElementById("hub-bar"),
    crumbs: document.getElementById("crumbs"),
    modeToggle: document.getElementById("mode-toggle"),
    hopToggle: document.getElementById("hop-toggle"),
    zoomOut: document.getElementById("zoom-out"),
    zoomFit: document.getElementById("zoom-fit"),
    zoomIn: document.getElementById("zoom-in"),
    searchInput: document.getElementById("search-input"),
    searchResults: document.getElementById("search-results"),
    diagToggle: document.getElementById("diag-toggle"),
    themeToggle: document.getElementById("theme-toggle"),
    panelToggle: document.getElementById("panel-toggle"),
    main: document.getElementById("main"),
    levelHead: document.getElementById("level-head"),
    legend: document.getElementById("legend"),
    traceBar: document.getElementById("trace-bar"),
    pathBanner: document.getElementById("path-banner"),
    viewport: document.getElementById("viewport"),
    sizer: document.getElementById("sizer"),
    canvas: document.getElementById("canvas"),
    edges: document.getElementById("edges"),
    blocks: document.getElementById("blocks"),
    panel: document.getElementById("panel"),
    panelBody: document.getElementById("panel-body"),
    drawer: document.getElementById("drawer"),
    tip: document.getElementById("tip")
  };

  /* --------------------------------------------------- Dataset preparation */
  // Keep only plain objects from a list that came from untrusted JSON.
  function objectsOf(list) {
    return (Array.isArray(list) ? list : []).filter((x) => x && typeof x === "object" && !Array.isArray(x));
  }

  function prepareDataset(raw) {
    const nodes = objectsOf(raw.nodes).map((n) => ({ ...n }));
    const byId = new Map();
    for (const n of nodes) {
      n.title = String(n.title ?? n.id);
      n.kids = [];
      n.sources = Array.isArray(n.sources) ? n.sources : [];
      n.tags = Array.isArray(n.tags) ? n.tags : [];
      n.metrics = n.metrics || {};
      byId.set(n.id, n);
    }

    let rootId = raw.rootId && byId.has(raw.rootId) ? raw.rootId : null;
    if (!rootId) {
      const syntheticRoot = {
        id: "__root__",
        title: raw.title || "Graph",
        kind: "system",
        status: "ready",
        parent: null,
        summary: raw.subtitle || "",
        kids: [],
        sources: [],
        tags: [],
        metrics: {}
      };
      nodes.unshift(syntheticRoot);
      byId.set(syntheticRoot.id, syntheticRoot);
      rootId = syntheticRoot.id;
      for (const n of nodes) {
        if (n.id !== rootId && (!n.parent || !byId.has(n.parent))) n.parent = rootId;
      }
    }

    // Build parent tree safely (break any accidental cycle)
    for (const n of nodes) {
      if (n.id === rootId) {
        n.parent = null;
        continue;
      }
      if (!n.parent || !byId.has(n.parent) || n.parent === n.id) {
        n.parent = rootId;
      }
    }
    for (const n of nodes) {
      if (n.id === rootId) continue;
      const seen = new Set([n.id]);
      let cur = n;
      while (cur.parent) {
        if (seen.has(cur.parent)) {
          cur.parent = rootId;
          break;
        }
        seen.add(cur.parent);
        cur = byId.get(cur.parent);
      }
      const p = byId.get(n.parent);
      if (p) p.kids.push(n);
    }

    // Sort kids deterministically
    function countDesc(u) {
      let total = 0;
      for (const k of u.kids) total += 1 + countDesc(k);
      u.descCount = total;
      return total;
    }
    countDesc(byId.get(rootId));

    const edges = objectsOf(raw.edges).filter(
      (e) => byId.has(e.from) && byId.has(e.to) && e.from !== e.to
    );

    // Degree statistics
    const inDeg = new Map();
    const outDeg = new Map();
    for (const e of edges) {
      outDeg.set(e.from, (outDeg.get(e.from) || 0) + 1);
      inDeg.set(e.to, (inDeg.get(e.to) || 0) + 1);
    }
    for (const n of nodes) {
      n.inDeg = inDeg.get(n.id) || 0;
      n.outDeg = outDeg.get(n.id) || 0;
    }

    // Relation palette
    const relMeta = new Map();
    const rawRels = raw.relations || {};
    let fallbackIdx = 0;
    const allRelIds = new Set(Object.keys(rawRels));
    for (const e of edges) allRelIds.add(e.relation || "relates-to");
    for (const rid of allRelIds) {
      const cfg = rawRels[rid] || {};
      const fi = fallbackIdx % FALLBACK_COLORS_DARK.length;
      fallbackIdx++;
      relMeta.set(rid, {
        id: rid,
        label: cfg.label || rid,
        darkColor: cfg.darkColor || cfg.color || FALLBACK_COLORS_DARK[fi],
        lightColor: cfg.lightColor || cfg.color || FALLBACK_COLORS_LIGHT[fi],
        dash: cfg.dash || "none",
        category: cfg.category || "structural"
      });
    }

    const overlays = objectsOf(raw.overlays).map((ov, i) => ({
      id: ov.id || `slice-${i}`,
      title: String(ov.title || ov.id || `slice-${i}`),
      kind: ov.kind || "slice",
      summary: ov.summary || "",
      url: ov.url || null,
      touches: (Array.isArray(ov.touches) ? ov.touches : []).filter((tid) => byId.has(tid))
    })).filter((ov) => ov.touches.length > 0);

    const traces = objectsOf(raw.traces).map((tr, idx) => ({
      id: tr.id || `trace-${idx}`,
      title: tr.title || `Trace ${idx + 1}`,
      color: tr.color || TRACE_PALETTE[idx % TRACE_PALETTE.length],
      agent: tr.agent || "",
      model: tr.model || "",
      totalTokens: tr.totalTokens || 0,
      blindAlleyCount: tr.blindAlleyCount || 0,
      summary: tr.summary || "",
      steps: objectsOf(tr.steps).filter((s) => byId.has(s.nodeId))
    })).filter((tr) => tr.steps.length > 0);

    const diagnostics = Array.isArray(raw.diagnostics) ? raw.diagnostics : [];

    return {
      id: raw.id || "default",
      title: raw.title || "Strata Graph",
      subtitle: raw.subtitle || "",
      domain: typeof raw.domain === "string" && raw.domain ? raw.domain : "system",
      generatedAt: raw.generatedAt || "",
      sourceLabel: raw.sourceLabel || "",
      levelLabel: typeof raw.levelLabel === "string" ? raw.levelLabel : "",
      axisNotes: Array.isArray(raw.axisNotes) ? raw.axisNotes.filter((n) => n && typeof n === "object") : [],
      rootId,
      nodes,
      byId,
      edges,
      relMeta,
      overlays,
      traces,
      diagnostics
    };
  }

  // Synthetic boxes (slices, outside ghosts) live in the same map as real node ids, so
  // their keys start with "~", which node ids from the compilers never do.
  function sliceBoxId(overlayId) {
    return `~slice:${overlayId}`;
  }

  // Any change of the selected block also drops a picked wire bundle and a path target,
  // because the inspector and highlighting check selectedBundleKey first.
  function setSelection(id) {
    st.selectedId = id;
    st.selectedBundleKey = null;
    st.compareTargetId = null;
  }

  function curDs() {
    return datasets[st.dsIdx];
  }

  function relColor(ds, relId) {
    const m = ds.relMeta.get(relId);
    if (!m) return st.theme === "dark" ? "#94a3b8" : "#475569";
    return st.theme === "dark" ? m.darkColor : m.lightColor;
  }

  function ancestorChain(ds, id) {
    const out = [];
    let cur = ds.byId.get(id);
    const guard = new Set();
    while (cur && !guard.has(cur.id)) {
      guard.add(cur.id);
      out.unshift(cur);
      cur = cur.parent ? ds.byId.get(cur.parent) : null;
    }
    return out;
  }

  function isDescendantOf(ds, nodeId, ancId) {
    let cur = ds.byId.get(nodeId);
    const guard = new Set();
    while (cur && cur.parent && !guard.has(cur.id)) {
      if (cur.parent === ancId) return true;
      guard.add(cur.id);
      cur = ds.byId.get(cur.parent);
    }
    return false;
  }

  /* ------------------------------------------ Level projection & lifting */
  function buildLevelModel(ds) {
    const focus = ds.byId.get(st.focusId) || ds.byId.get(ds.rootId);
    const spineMap = new Map();
    const groupFrames = new Map(); // parentId -> title when expandAll is true
    const MAX_LEAVES = 110;
    let hiddenLeaves = 0;

    if (!st.expandAll) {
      for (const child of focus.kids) {
        if (st.hideBlindAlleys && (child.status === "blind-alley" || child.status === "error")) continue;
        spineMap.set(child.id, {
          id: child.id,
          node: child,
          zone: "spine",
          groupId: null
        });
      }
    } else {
      // Collect leaf descendants (or 2nd-level blocks) inside focus, at most 110
      const leaves = [];
      function walk(u, topGroup) {
        if (!u.kids.length) {
          leaves.push({ node: u, group: topGroup });
          return;
        }
        for (const k of u.kids) {
          walk(k, topGroup || (u.id !== focus.id ? u : k.kids.length ? k : null));
        }
      }
      walk(focus, null);
      const capped = leaves.slice(0, MAX_LEAVES);
      hiddenLeaves = leaves.length - capped.length;
      for (const item of capped) {
        if (st.hideBlindAlleys && (item.node.status === "blind-alley" || item.node.status === "error")) continue;
        const gid = item.group && item.group.id !== item.node.id ? item.group.id : null;
        if (gid) groupFrames.set(gid, item.group.title);
        spineMap.set(item.node.id, {
          id: item.node.id,
          node: item.node,
          zone: "spine",
          groupId: gid
        });
      }
    }

    // Map any dataset nodeId to its visible spine block or OUTSIDE representative
    function resolveInside(nodeId) {
      if (spineMap.has(nodeId)) return nodeId;
      let cur = ds.byId.get(nodeId);
      while (cur && cur.parent) {
        if (spineMap.has(cur.parent)) return cur.parent;
        cur = ds.byId.get(cur.parent);
      }
      return null;
    }

    function resolveOutside(nodeId) {
      // Lift outside node to top-level child of root (or sibling of focus) so ghosts stay compact
      const chain = ancestorChain(ds, focus.id).map((x) => x.id);
      const focusAncSet = new Set(chain);
      let cur = ds.byId.get(nodeId);
      let best = cur;
      while (cur && cur.parent) {
        if (focusAncSet.has(cur.parent)) {
          best = cur;
          break;
        }
        cur = ds.byId.get(cur.parent);
      }
      return best ? best.id : nodeId;
    }

    const topGhosts = new Map();
    const botGhosts = new Map();
    const rawPairEdges = new Map(); // key "u->v" or "back:u->v" -> bundle

    function ensureGhost(map, targetNodeId, zone) {
      const gid = `~${zone}:${targetNodeId}`;
      if (!map.has(gid)) {
        const base = ds.byId.get(targetNodeId);
        map.set(gid, {
          id: gid,
          realId: targetNodeId,
          node: base,
          zone,
          isGhost: true
        });
      }
      return gid;
    }

    // Count all relations at this level (even hidden ones, for legend toggles)
    const relCounts = new Map();

    for (const e of ds.edges) {
      if (st.hideBlindAlleys) {
        const nu = ds.byId.get(e.from);
        const nv = ds.byId.get(e.to);
        if ((nu && (nu.status === "blind-alley" || nu.status === "error")) ||
            (nv && (nv.status === "blind-alley" || nv.status === "error"))) {
          continue;
        }
      }

      const inU = resolveInside(e.from);
      const inV = resolveInside(e.to);
      if (!inU && !inV) continue;
      if (inU && inV && inU === inV) continue;

      let uId = inU;
      let vId = inV;
      if (!uId) {
        const outId = resolveOutside(e.from);
        uId = ensureGhost(topGhosts, outId, "top");
      }
      if (!vId) {
        const outId = resolveOutside(e.to);
        vId = ensureGhost(botGhosts, outId, "bot");
      }

      const rel = e.relation || "relates-to";
      relCounts.set(rel, (relCounts.get(rel) || 0) + 1);
      if (st.hiddenRels.has(rel)) continue;

      const isExplicitBack = e.flowRole === "backtrack" || e.flowRole === "loop";
      const key = `${isExplicitBack ? "back:" : ""}${uId}->${vId}`;
      if (!rawPairEdges.has(key)) {
        rawPairEdges.set(key, {
          key,
          u: uId,
          v: vId,
          isBacktrack: isExplicitBack,
          edges: [],
          byRel: new Map()
        });
      }
      const b = rawPairEdges.get(key);
      b.edges.push(e);
      if (!b.byRel.has(rel)) b.byRel.set(rel, []);
      b.byRel.get(rel).push(e);
    }

    // Overlays / Cross-cutting web slices active at this level
    const activeSlices = [];
    for (const ov of ds.overlays) {
      const touchedVis = new Set();
      for (const tid of ov.touches) {
        const visId = resolveInside(tid);
        if (visId) touchedVis.add(visId);
      }
      if (touchedVis.size >= 1) {
        activeSlices.push({
          id: sliceBoxId(ov.id),
          overlay: ov,
          zone: "slice",
          isSlice: true,
          touchedSpineIds: Array.from(touchedVis)
        });
      }
    }
    activeSlices.sort((a, b) => b.touchedSpineIds.length - a.touchedSpineIds.length);
    const visibleSlices = activeSlices.slice(0, 18);

    const bundlesList = Array.from(rawPairEdges.values());
    const liftedIn = new Map();
    const liftedOut = new Map();
    for (const b of bundlesList) {
      liftedOut.set(b.u, (liftedOut.get(b.u) || 0) + b.edges.length);
      liftedIn.set(b.v, (liftedIn.get(b.v) || 0) + b.edges.length);
    }

    return {
      focus,
      spineMap,
      topGhosts,
      botGhosts,
      bundles: bundlesList,
      liftedIn,
      liftedOut,
      slices: visibleSlices,
      hiddenLeaves,
      relCounts,
      groupFrames,
      resolveInside
    };
  }

  /* ------------------------------------ Sugiyama + PAV Isotonic Layout */
  function pav(items) {
    // Pool Adjacent Violators with minimum center-to-center spacing
    if (!items.length) return [];
    const blocks = items.map((it, idx) => ({
      start: idx,
      end: idx,
      weight: it.weight,
      sumDesired: it.desired * it.weight,
      items: [it],
      offsets: [0]
    }));

    function blockPos(blk) {
      return blk.sumDesired / blk.weight;
    }

    const stack = [];
    for (const blk of blocks) {
      stack.push(blk);
      while (stack.length >= 2) {
        const right = stack[stack.length - 1];
        const left = stack[stack.length - 2];
        const leftLastOff = left.offsets[left.offsets.length - 1];
        const leftLastItem = left.items[left.items.length - 1];
        const rightFirstItem = right.items[0];
        const minGap = (leftLastItem.w + rightFirstItem.w) / 2 +
          (leftLastItem.isDummy || rightFirstItem.isDummy ? GEO.dummyGap : GEO.colGap);
        const leftRightEdge = blockPos(left) + leftLastOff + minGap;
        const rightLeftEdge = blockPos(right);
        if (leftRightEdge <= rightLeftEdge + 0.01) break;

        // Merge left & right into one contiguous block
        stack.pop();
        const shift = leftLastOff + minGap;
        for (let i = 0; i < right.items.length; i++) {
          const off = shift + right.offsets[i];
          left.items.push(right.items[i]);
          left.offsets.push(off);
          left.weight += right.items[i].weight;
          left.sumDesired += (right.items[i].desired - off) * right.items[i].weight;
        }
      }
    }

    const centers = [];
    for (const blk of stack) {
      const base = blockPos(blk);
      for (let i = 0; i < blk.items.length; i++) {
        centers.push({ item: blk.items[i], cx: base + blk.offsets[i] });
      }
    }
    return centers;
  }

  function computeLayout(ds, level, viewportW) {
    const spineItems = Array.from(level.spineMap.values());
    const topItems = Array.from(level.topGhosts.values());
    const botItems = Array.from(level.botGhosts.values());

    if (!spineItems.length) {
      return { width: 600, height: 260, boxes: new Map(), forwardRoutes: [], backRoutes: [], sliceRoutes: [], bandY: null, frames: [] };
    }

    const spineIds = new Set(spineItems.map((x) => x.id));
    // Separate forward spine bundles from explicit backtracks, then run DFS cycle
    // detection so residual cycles also route as return arcs.
    const forwardCandidates = [];
    const backBundles = [];

    for (const b of level.bundles) {
      if (b.isBacktrack) {
        backBundles.push(b);
      } else {
        forwardCandidates.push(b);
      }
    }

    // Order spine nodes so entrypoints (inDeg 0 / high out-in delta) come first for DFS
    const adj = new Map();
    const inCount = new Map();
    const outCount = new Map();
    for (const s of spineItems) {
      adj.set(s.id, []);
      inCount.set(s.id, 0);
      outCount.set(s.id, 0);
    }
    for (const b of forwardCandidates) {
      if (spineIds.has(b.u) && spineIds.has(b.v)) {
        adj.get(b.u).push(b);
        outCount.set(b.u, (outCount.get(b.u) || 0) + b.edges.length);
        inCount.set(b.v, (inCount.get(b.v) || 0) + b.edges.length);
      }
    }

    const orderedRoots = [...spineItems].sort((a, b) => {
      const aEntry = inCount.get(a.id) === 0 ? 0 : 1;
      const bEntry = inCount.get(b.id) === 0 ? 0 : 1;
      if (aEntry !== bEntry) return aEntry - bEntry;
      const dA = (outCount.get(a.id) || 0) - (inCount.get(a.id) || 0);
      const dB = (outCount.get(b.id) || 0) - (inCount.get(b.id) || 0);
      if (dA !== dB) return dB - dA;
      return a.node.title.localeCompare(b.node.title);
    });

    const color = new Map(); // 0 unvisited, 1 active stack, 2 done
    const cyclicKeys = new Set();

    // Break direct mutual 2-cycles deterministically in favor of heavier bundle weight
    const pairBundleMap = new Map();
    for (const b of forwardCandidates) {
      if (spineIds.has(b.u) && spineIds.has(b.v)) {
        pairBundleMap.set(`${b.u}->${b.v}`, b);
      }
    }
    for (const b of forwardCandidates) {
      if (!spineIds.has(b.u) || !spineIds.has(b.v)) continue;
      const rev = pairBundleMap.get(`${b.v}->${b.u}`);
      if (!rev || cyclicKeys.has(b.key) || cyclicKeys.has(rev.key)) continue;
      const nu = level.spineMap.get(b.u)?.node;
      const nv = level.spineMap.get(b.v)?.node;
      const tu = Number.isFinite(nu?.tier) ? nu.tier : null;
      const tv = Number.isFinite(nv?.tier) ? nv.tier : null;
      if (tu !== null && tv !== null && tu !== tv) {
        cyclicKeys.add(tu > tv ? b.key : rev.key);
        continue;
      }
      const ou = Number.isFinite(nu?.order) ? nu.order : null;
      const ov = Number.isFinite(nv?.order) ? nv.order : null;
      if (tu !== null && tv !== null && tu === tv && ou !== null && ov !== null && ou !== ov) {
        cyclicKeys.add(ou > ov ? b.key : rev.key);
        continue;
      }
      const netU = (outCount.get(b.u) || 0) - (inCount.get(b.u) || 0);
      const netV = (outCount.get(b.v) || 0) - (inCount.get(b.v) || 0);
      if (b.edges.length < rev.edges.length || (b.edges.length === rev.edges.length && netU < netV)) {
        cyclicKeys.add(b.key);
      } else {
        cyclicKeys.add(rev.key);
      }
    }

    function dfs(uid) {
      color.set(uid, 1);
      const outs = (adj.get(uid) || []).filter((b) => !cyclicKeys.has(b.key));
      outs.sort((a, b) => b.edges.length - a.edges.length);
      for (const b of outs) {
        const stv = color.get(b.v) || 0;
        if (stv === 1) {
          cyclicKeys.add(b.key);
        } else if (stv === 0) {
          dfs(b.v);
        }
      }
      color.set(uid, 2);
    }
    for (const r of orderedRoots) {
      if (!color.get(r.id)) dfs(r.id);
    }

    const dagBundles = [];
    for (const b of forwardCandidates) {
      if (cyclicKeys.has(b.key)) {
        b.isLoop = true;
        backBundles.push(b);
      } else {
        dagBundles.push(b);
      }
    }

    // Topological longest-path rank assignment on spine DAG.
    // On dense prose container overviews without explicit tiers/stack domain,
    // prevent weak single-link cross-references from stretching sections vertically.
    const allContainers = !st.expandAll && spineItems.length >= 5 && spineItems.every((s) => s.node.kids && s.node.kids.length > 0);
    const hasExplicitTiers = spineItems.some((s) => Number.isFinite(s.node.tier));
    const isStackLayout = hasExplicitTiers || ds.domain === "system-stack";
    const spineDagBundles = dagBundles.filter((b) => spineIds.has(b.u) && spineIds.has(b.v));
    let rankBundles = spineDagBundles;
    if (!isStackLayout && allContainers && spineDagBundles.length >= spineItems.length) {
      const weights = spineDagBundles.map((b) => b.edges.length).sort((a, b) => a - b);
      const minStrong = Math.max(2, weights[Math.floor(weights.length * 0.45)] || 2);
      const strong = spineDagBundles.filter((b) => b.edges.length >= minStrong || inCount.get(b.u) === 0);
      if (strong.length > 0) rankBundles = strong;
    }

    const dagOut = new Map();
    const dagInDeg = new Map();
    for (const s of spineItems) {
      dagOut.set(s.id, []);
      dagInDeg.set(s.id, 0);
    }
    for (const b of rankBundles) {
      dagOut.get(b.u).push(b.v);
      dagInDeg.set(b.v, (dagInDeg.get(b.v) || 0) + 1);
    }

    const baseRank = new Map();
    if (hasExplicitTiers) {
      const maxDefinedTier = Math.max(0, ...spineItems.filter((s) => Number.isFinite(s.node.tier)).map((s) => s.node.tier));
      for (const s of spineItems) {
        baseRank.set(s.id, Number.isFinite(s.node.tier) ? s.node.tier : maxDefinedTier);
      }
    } else {
      const queue = [];
      for (const r of orderedRoots) {
        if (dagInDeg.get(r.id) === 0) {
          baseRank.set(r.id, 0);
          queue.push(r.id);
        }
      }
      const rankCap = isStackLayout ? 24 : (allContainers ? 2 : 999);
      while (queue.length) {
        const u = queue.shift();
        const ru = baseRank.get(u) || 0;
        for (const v of dagOut.get(u) || []) {
          baseRank.set(v, Math.min(rankCap, Math.max(baseRank.get(v) || 0, ru + 1)));
          dagInDeg.set(v, dagInDeg.get(v) - 1);
          if (dagInDeg.get(v) === 0) queue.push(v);
        }
      }
      for (const s of spineItems) {
        if (!baseRank.has(s.id)) baseRank.set(s.id, 0);
      }
    }

    // Wrap wide ranks into several rows to fit the viewport width
    const maxPerRow = Math.max(3, Math.min(7, Math.floor((Math.max(viewportW, 880) - 120) / (GEO.cardW + GEO.colGap))));
    const maxBase = Math.max(0, ...Array.from(baseRank.values()));
    const rowOf = new Map();
    let curRowIdx = 0;

    if (topItems.length > 0) {
      for (let i = 0; i < topItems.length; i++) {
        rowOf.set(topItems[i].id, Math.floor(i / maxPerRow));
      }
      curRowIdx = Math.floor((topItems.length - 1) / maxPerRow) + 1;
    }

    for (let r = 0; r <= maxBase; r++) {
      const bucket = orderedRoots.filter((s) => baseRank.get(s.id) === r);
      if (!bucket.length) continue;
      // Preserve explicit left-to-right node.order when provided, else groupId + degree
      bucket.sort((a, b) => {
        const oa = Number.isFinite(a.node.order) ? a.node.order : Infinity;
        const ob = Number.isFinite(b.node.order) ? b.node.order : Infinity;
        if (oa !== ob) return oa - ob;
        if (a.groupId !== b.groupId) return String(a.groupId || "").localeCompare(String(b.groupId || ""));
        const degA = (level.liftedIn.get(a.id) || a.node.inDeg) + (level.liftedOut.get(a.id) || a.node.outDeg);
        const degB = (level.liftedIn.get(b.id) || b.node.inDeg) + (level.liftedOut.get(b.id) || b.node.outDeg);
        return degB - degA;
      });
      for (let i = 0; i < bucket.length; i++) {
        rowOf.set(bucket[i].id, curRowIdx + Math.floor(i / maxPerRow));
      }
      curRowIdx += Math.floor((bucket.length - 1) / maxPerRow) + 1;
    }

    // Ensure strict downward rank on rank-enforcing bundles unless explicit tiers are locked
    let changed = !hasExplicitTiers;
    let passGuard = 0;
    const maxAllowedSpineRow = isStackLayout ? 60 : (allContainers ? (topItems.length > 0 ? 4 : 2) : 60);
    while (changed && passGuard < 20) {
      changed = false;
      passGuard++;
      for (const b of rankBundles) {
        if (spineIds.has(b.u) && spineIds.has(b.v)) {
          const ru = rowOf.get(b.u);
          const rv = rowOf.get(b.v);
          if (rv <= ru && ru + 1 <= maxAllowedSpineRow) {
            rowOf.set(b.v, ru + 1);
            changed = true;
          }
        }
      }
    }

    const maxSpineRow = Math.max(curRowIdx - 1, ...Array.from(rowOf.values()));
    let totalRows = maxSpineRow + 1;
    if (botItems.length > 0) {
      for (let i = 0; i < botItems.length; i++) {
        rowOf.set(botItems[i].id, totalRows + Math.floor(i / maxPerRow));
      }
      totalRows += Math.floor((botItems.length - 1) / maxPerRow) + 1;
    }

    // Build rows array with real items + dummy channel waypoints for multi-row spans
    const rows = Array.from({ length: totalRows }, () => []);
    const allReal = [...topItems, ...spineItems, ...botItems];
    const itemById = new Map();

    for (const it of allReal) {
      const r = rowOf.get(it.id);
      const w = it.isGhost ? GEO.ghostW : GEO.cardW;
      const hgt = it.isGhost ? GEO.ghostH : GEO.cardH;
      const entry = {
        id: it.id,
        ref: it,
        row: r,
        w,
        h: hgt,
        isDummy: false,
        weight: 1.0,
        upNbrs: [],
        dnNbrs: [],
        cx: 0,
        y: 0
      };
      rows[r].push(entry);
      itemById.set(it.id, entry);
    }

    // Decompose dagBundles across rows using dummy waypoints, or keep clean left->right same-row forward arrows
    const realFrac = new Map();
    for (const row of rows) {
      row.forEach((it, idx) => realFrac.set(it.id, (idx + 0.5) / Math.max(1, row.length)));
    }
    let dummySeq = 0;
    const bundleChain = new Map(); // bundle.key -> [entry0, dummy1..., entryK]
    const horizBundles = [];
    for (const b of dagBundles) {
      const eu = itemById.get(b.u);
      const ev = itemById.get(b.v);
      if (!eu || !ev) continue;
      const euCol = rows[eu.row].indexOf(eu);
      const evCol = rows[ev.row].indexOf(ev);
      if (ev.row === eu.row && evCol > euCol && !b.isBacktrack) {
        horizBundles.push(b);
        continue;
      }
      if (ev.row <= eu.row) {
        // Backward or same-row loop: route as an outer return arc
        b.isLoop = true;
        backBundles.push(b);
        continue;
      }
      const chain = [eu];
      const laneSpanW = Math.max(GEO.dummyW, b.byRel.size * GEO.laneGap + 8);
      const uFrac = realFrac.get(eu.id) ?? 0.5;
      const vFrac = realFrac.get(ev.id) ?? 0.5;
      for (let r = eu.row + 1; r < ev.row; r++) {
        let tFrac = uFrac + ((r - eu.row) / (ev.row - eu.row)) * (vFrac - uFrac);
        if (uFrac <= 0.3 && vFrac <= 0.3) tFrac = Math.max(0.02, tFrac - 0.06);
        else if (uFrac >= 0.7 && vFrac >= 0.7) tFrac = Math.min(0.98, tFrac + 0.06);
        const d = {
          id: `~d${dummySeq++}`,
          ref: null,
          row: r,
          w: laneSpanW,
          h: GEO.cardH,
          isDummy: true,
          targetFrac: tFrac,
          weight: 2.5,
          upNbrs: [],
          dnNbrs: [],
          cx: 0,
          y: 0
        };
        rows[r].push(d);
        itemById.set(d.id, d);
        chain.push(d);
      }
      chain.push(ev);
      for (let i = 0; i < chain.length - 1; i++) {
        chain[i].dnNbrs.push(chain[i + 1]);
        chain[i + 1].upNbrs.push(chain[i]);
      }
      bundleChain.set(b.key, chain);
    }

    // Slot multi-row dummy channels proportionally so left/center skip wires avoid a right-margin curtain
    for (const row of rows) {
      row.sort((a, b) => {
        const ka = a.isDummy ? (a.targetFrac ?? 0.5) : (realFrac.get(a.id) ?? 0.5);
        const kb = b.isDummy ? (b.targetFrac ?? 0.5) : (realFrac.get(b.id) ?? 0.5);
        return ka - kb;
      });
    }

    // Initial X positions centered around 0
    for (const row of rows) {
      let x = 0;
      for (let i = 0; i < row.length; i++) {
        if (i > 0) {
          const prev = row[i - 1];
          const gap = prev.isDummy || row[i].isDummy ? GEO.dummyGap : GEO.colGap;
          x += prev.w / 2 + gap + row[i].w / 2;
        }
        row[i].cx = x;
      }
      const mid = x / 2;
      for (const it of row) it.cx -= mid;
    }

    // 16-pass bidirectional barycenter ordering + PAV X-coordinate refinement
    for (let iter = 0; iter < 16; iter++) {
      const down = iter % 2 === 0;
      const start = down ? 1 : rows.length - 2;
      const end = down ? rows.length : -1;
      const step = down ? 1 : -1;

      for (let r = start; r !== end; r += step) {
        const row = rows[r];
        if (!row.length) continue;
        const hasLockedOrder = row.some((it) => !it.isDummy && it.ref && it.ref.node && Number.isFinite(it.ref.node.order));
        if (hasLockedOrder) continue;
        for (const it of row) {
          const nbrs = down ? it.upNbrs : it.dnNbrs;
          const allNbrs = it.upNbrs.length && it.dnNbrs.length && iter >= 6
            ? [...it.upNbrs, ...it.dnNbrs]
            : nbrs.length ? nbrs : (down ? it.dnNbrs : it.upNbrs);
          if (allNbrs.length) {
            it.desired = allNbrs.reduce((acc, n) => acc + n.cx, 0) / allNbrs.length;
          } else {
            it.desired = it.cx;
          }
        }
        row.sort((a, b) => a.desired - b.desired);
        const placed = pav(row);
        for (let i = 0; i < placed.length; i++) {
          row[i] = placed[i].item;
          row[i].cx = placed[i].cx;
        }
      }
    }

    // Vertical Y coordinates per row
    let curY = GEO.padY;
    const rowY = [];
    const rowH = [];
    for (let r = 0; r < rows.length; r++) {
      const row = rows[r];
      const maxH = row.reduce((m, it) => Math.max(m, it.isDummy ? 44 : it.h), 52);
      rowY.push(curY);
      rowH.push(maxH);
      for (const it of row) {
        it.y = curY + (it.isDummy ? 0 : (maxH - it.h) / 2);
        if (it.isDummy) it.h = maxH;
      }
      curY += maxH + GEO.rowGap;
    }

    // Normalize X so minimum left edge starts at GEO.padX
    let minLeft = Infinity;
    let maxRight = -Infinity;
    for (const row of rows) {
      for (const it of row) {
        if (it.isDummy) continue;
        minLeft = Math.min(minLeft, it.cx - it.w / 2);
        maxRight = Math.max(maxRight, it.cx + it.w / 2);
      }
    }
    if (!Number.isFinite(minLeft)) {
      minLeft = 0;
      maxRight = 600;
    }

    const leftRailCount = backBundles.filter((b) => {
      if (!b.isBacktrack) return false;
      const bv = itemById.get(b.v);
      if (!bv) return false;
      return rows[bv.row].some((it) => !it.isDummy && it.cx > bv.cx + 10);
    }).length;
    const leftGutter = leftRailCount > 0 ? GEO.returnMargin + leftRailCount * GEO.returnLaneStep + 20 : 0;
    const shiftX = GEO.padX + leftGutter - minLeft;
    for (const row of rows) {
      for (const it of row) it.cx += shiftX;
    }
    const minLeftX = minLeft + shiftX;
    maxRight += shiftX;

    const boxes = new Map();
    for (const row of rows) {
      for (const it of row) {
        if (it.isDummy) continue;
        boxes.set(it.id, {
          id: it.id,
          ref: it.ref,
          x: it.cx - it.w / 2,
          y: it.y,
          cx: it.cx,
          w: it.w,
          h: it.h,
          row: it.row
        });
      }
    }

    // Cross-cutting slices go in a separate band below the spine
    let bandY = null;
    if (level.slices.length > 0) {
      bandY = curY - GEO.rowGap + GEO.bandGap;
      const spineSpanW = Math.max(maxRight - GEO.padX, 680);
      const cols = Math.max(2, Math.min(5, Math.floor((spineSpanW + GEO.colGap) / (GEO.sliceW + 14))));
      let sliceBottom = bandY + 30;
      for (let i = 0; i < level.slices.length; i++) {
        const sl = level.slices[i];
        const col = i % cols;
        const r = Math.floor(i / cols);
        const sx = GEO.padX + col * (GEO.sliceW + 14);
        const sy = bandY + 30 + r * (GEO.sliceH + 12);
        boxes.set(sl.id, {
          id: sl.id,
          ref: sl,
          x: sx,
          y: sy,
          cx: sx + GEO.sliceW / 2,
          w: GEO.sliceW,
          h: GEO.sliceH,
          row: rows.length + r
        });
        maxRight = Math.max(maxRight, sx + GEO.sliceW);
        sliceBottom = Math.max(sliceBottom, sy + GEO.sliceH);
      }
      curY = sliceBottom + GEO.padY;
    } else {
      curY = curY - GEO.rowGap + GEO.padY;
    }

    // Assign bottom exit ports & top entry ports for forward bundles
    const outSlots = new Map();
    const inSlots = new Map();
    const activeDagBundles = dagBundles.filter((b) => bundleChain.has(b.key));

    for (const b of activeDagBundles) {
      const chain = bundleChain.get(b.key);
      const u = chain[0];
      const next = chain[1];
      const prev = chain[chain.length - 2];
      const v = chain[chain.length - 1];
      if (!outSlots.has(u.id)) outSlots.set(u.id, []);
      if (!inSlots.has(v.id)) inSlots.set(v.id, []);
      outSlots.get(u.id).push({ b, targetX: next.cx });
      inSlots.get(v.id).push({ b, sourceX: prev.cx });
    }

    const outPortX = new Map();
    const inPortX = new Map();
    for (const [uid, list] of outSlots.entries()) {
      list.sort((a, b) => a.targetX - b.targetX);
      const bx = boxes.get(uid);
      const usable = Math.max(24, bx.w - GEO.portInset * 2);
      for (let i = 0; i < list.length; i++) {
        const px = list.length === 1
          ? bx.cx
          : bx.x + GEO.portInset + (usable * i) / (list.length - 1);
        outPortX.set(list[i].b.key, px);
      }
    }
    for (const [vid, list] of inSlots.entries()) {
      list.sort((a, b) => a.sourceX - b.sourceX);
      const bx = boxes.get(vid);
      const usable = Math.max(24, bx.w - GEO.portInset * 2);
      for (let i = 0; i < list.length; i++) {
        const px = list.length === 1
          ? bx.cx
          : bx.x + GEO.portInset + (usable * i) / (list.length - 1);
        inPortX.set(list[i].b.key, px);
      }
    }

    // Build SVG paths for forward multi-lane bundles
    const forwardPairKeys = new Set(activeDagBundles.map((b) => `${b.u}->${b.v}`));
    const forwardRoutes = [];

    for (const b of activeDagBundles) {
      const chain = bundleChain.get(b.key);
      const bu = boxes.get(b.u);
      const bv = boxes.get(b.v);
      const relKeys = Array.from(b.byRel.keys());
      const nLanes = relKeys.length;
      const baseStartX = outPortX.get(b.key) ?? bu.cx;
      const baseEndX = inPortX.get(b.key) ?? bv.cx;

      const lanes = [];
      for (let li = 0; li < nLanes; li++) {
        const offset = (li - (nLanes - 1) / 2) * GEO.laneGap;
        const pts = [];
        pts.push({ x: baseStartX + offset, y: bu.y + bu.h });
        for (let ci = 1; ci < chain.length - 1; ci++) {
          const dm = chain[ci];
          pts.push({ x: dm.cx + offset, y: dm.y });
          pts.push({ x: dm.cx + offset, y: dm.y + dm.h });
        }
        pts.push({ x: baseEndX + offset, y: bv.y });

        // Construct smooth vertical-tangent cubic Bezier with straight channel segments
        let d = `M ${pts[0].x.toFixed(1)} ${pts[0].y.toFixed(1)}`;
        let idx = 0;
        while (idx < pts.length - 1) {
          const p = pts[idx];
          const q = pts[idx + 1];
          if (idx % 2 === 0) {
            const my = (p.y + q.y) / 2;
            d += ` C ${p.x.toFixed(1)} ${my.toFixed(1)}, ${q.x.toFixed(1)} ${my.toFixed(1)}, ${q.x.toFixed(1)} ${q.y.toFixed(1)}`;
          } else {
            d += ` L ${q.x.toFixed(1)} ${q.y.toFixed(1)}`;
          }
          idx++;
        }
        const endPt = pts[pts.length - 1];
        lanes.push({
          rel: relKeys[li],
          d,
          arrowX: endPt.x,
          arrowY: endPt.y,
          arrowDir: "down"
        });
      }

      const reverseExists = forwardPairKeys.has(`${b.v}->${b.u}`);
      const isQuietBypass =
        level.focus.id === ds.rootId &&
        !st.expandAll &&
        bu.ref?.node?.quietBypass === true &&
        bv.row - bu.row > 1;
      forwardRoutes.push({
        bundle: b,
        lanes,
        isQuietBypass,
        badgeT: reverseExists ? 0.36 : 0.5
      });
    }

    // Horizontal left-to-right routes for forward pairs in the same row
    for (const b of horizBundles) {
      const bu = boxes.get(b.u);
      const bv = boxes.get(b.v);
      if (!bu || !bv) continue;
      const relKeys = Array.from(b.byRel.keys());
      const nLanes = relKeys.length;
      const lanes = [];
      const yMid = bu.y + bu.h / 2;
      for (let li = 0; li < nLanes; li++) {
        const offset = (li - (nLanes - 1) / 2) * GEO.laneGap;
        const x1 = bu.x + bu.w;
        const x2 = bv.x;
        const y = yMid + offset;
        lanes.push({
          rel: relKeys[li],
          d: `M ${x1.toFixed(1)} ${y.toFixed(1)} L ${x2.toFixed(1)} ${y.toFixed(1)}`,
          arrowX: x2,
          arrowY: y,
          arrowDir: "right"
        });
      }
      forwardRoutes.push({
        bundle: b,
        lanes,
        isQuietBypass: false,
        badgeT: 0.5
      });
    }

    // Build outer left/right return arcs for explicit backtracks & loops (↺)
    const backRoutes = [];
    let rightChannelMax = maxRight;
    backBundles.sort((a, b) => {
      const ya = boxes.get(a.u)?.y || 0;
      const yb = boxes.get(b.u)?.y || 0;
      return ya - yb;
    });

    let leftSlot = 0;
    let rightSlot = 0;
    const rowHasSiblingRight = (bBox) =>
      Array.from(boxes.values()).some((o) =>
        !o.ref?.isSlice && Math.abs(o.y - bBox.y) < 30 && o.x > bBox.x + bBox.w - 4
      );
    for (let i = 0; i < backBundles.length; i++) {
      const b = backBundles[i];
      const bu = boxes.get(b.u);
      const bv = boxes.get(b.v);
      if (!bu || !bv) continue;

      const useLeftRail = b.isBacktrack && rowHasSiblingRight(bv);
      const firstRel = Array.from(b.byRel.keys())[0] || "backtracks-to";
      if (useLeftRail) {
        const railX = minLeftX - GEO.returnMargin - (leftSlot++) * GEO.returnLaneStep;
        const x1 = bu.x;
        const y1 = bu.y + bu.h * 0.62;
        const x2 = bv.x;
        const y2 = bv.y + bv.h * 0.38;
        const c1x = Math.min(x1 - 36, railX);
        const c2x = Math.min(x2 - 36, railX);
        const d = `M ${x1.toFixed(1)} ${y1.toFixed(1)} C ${c1x.toFixed(1)} ${y1.toFixed(1)}, ${c2x.toFixed(1)} ${y2.toFixed(1)}, ${x2.toFixed(1)} ${y2.toFixed(1)}`;
        backRoutes.push({
          bundle: b,
          rel: firstRel,
          d,
          arrowX: x2,
          arrowY: y2,
          arrowDir: "right",
          railX,
          midY: (y1 + y2) / 2
        });
      } else {
        const railX = maxRight + GEO.returnMargin + (rightSlot++) * GEO.returnLaneStep;
        rightChannelMax = Math.max(rightChannelMax, railX + 34);

        const x1 = bu.x + bu.w;
        const y1 = bu.y + bu.h * 0.62;
        const x2 = bv.x + bv.w;
        const y2 = bv.y + bv.h * 0.38;
        const c1x = Math.max(x1 + 36, railX);
        const c2x = Math.max(x2 + 36, railX);
        const d = `M ${x1.toFixed(1)} ${y1.toFixed(1)} C ${c1x.toFixed(1)} ${y1.toFixed(1)}, ${c2x.toFixed(1)} ${y2.toFixed(1)}, ${x2.toFixed(1)} ${y2.toFixed(1)}`;
        backRoutes.push({
          bundle: b,
          rel: firstRel,
          d,
          arrowX: x2,
          arrowY: y2,
          arrowDir: "left",
          railX,
          midY: (y1 + y2) / 2
        });
      }
    }

    // Build Cross-Cutting Slice curves
    const sliceRoutes = [];
    for (const sl of level.slices) {
      const sb = boxes.get(sl.id);
      if (!sb) continue;
      for (const tid of sl.touchedSpineIds) {
        const tb = boxes.get(tid);
        if (!tb) continue;
        const x1 = sb.cx;
        const y1 = sb.y;
        const x2 = tb.cx;
        const y2 = tb.y + tb.h;
        const my = y1 - Math.max(36, (y1 - y2) * 0.42);
        const d = `M ${x1.toFixed(1)} ${y1.toFixed(1)} C ${x1.toFixed(1)} ${my.toFixed(1)}, ${x2.toFixed(1)} ${(y2 + 34).toFixed(1)}, ${x2.toFixed(1)} ${y2.toFixed(1)}`;
        sliceRoutes.push({
          key: `slicewire:${sl.id}->${tid}`,
          sliceId: sl.id,
          targetId: tid,
          d
        });
      }
    }

    // Group frames when Expanded mode is active
    const frames = [];
    if (st.expandAll && level.groupFrames.size > 0) {
      for (const [gid, title] of level.groupFrames.entries()) {
        let fx1 = Infinity, fy1 = Infinity, fx2 = -Infinity, fy2 = -Infinity;
        let count = 0;
        for (const s of spineItems) {
          if (s.groupId !== gid) continue;
          const b = boxes.get(s.id);
          if (!b) continue;
          count++;
          fx1 = Math.min(fx1, b.x - 10);
          fy1 = Math.min(fy1, b.y - 22);
          fx2 = Math.max(fx2, b.x + b.w + 10);
          fy2 = Math.max(fy2, b.y + b.h + 8);
        }
        if (count >= 2) {
          frames.push({ id: gid, title, x: fx1, y: fy1, w: fx2 - fx1, h: fy2 - fy1 });
        }
      }
    }

    const totalW = Math.max(rightChannelMax + GEO.padX, 720);
    const totalH = Math.max(curY, 340);

    return {
      width: totalW,
      height: totalH,
      boxes,
      forwardRoutes,
      backRoutes,
      sliceRoutes,
      bandY,
      frames
    };
  }

  /* ------------------------------------------ Path Finder & Ego Subgraph */
  function computeHighlightSets(ds, level, lay) {
    const litNodes = new Set();
    const litBundles = new Set();

    // Path Finder Mode: Selected A <-> Compare B
    if (st.selectedId && st.compareTargetId && lay.boxes.has(st.selectedId) && lay.boxes.has(st.compareTargetId)) {
      const a = st.selectedId;
      const b = st.compareTargetId;
      litNodes.add(a);
      litNodes.add(b);

      // Build undirected + directed adjacency over visible bundles
      const allRoutes = [
        ...lay.forwardRoutes.map((r) => r.bundle),
        ...lay.backRoutes.map((r) => r.bundle)
      ];
      const nbrs = new Map();
      for (const bun of allRoutes) {
        if (!nbrs.has(bun.u)) nbrs.set(bun.u, []);
        if (!nbrs.has(bun.v)) nbrs.set(bun.v, []);
        nbrs.get(bun.u).push({ to: bun.v, key: bun.key });
        nbrs.get(bun.v).push({ to: bun.u, key: bun.key });
      }

      // Bounded simple paths up to length 4 + shortest BFS path
      const foundPaths = [];
      const queue = [[{ node: a, viaKey: null }]];
      let shortestLen = Infinity;
      while (queue.length && foundPaths.length < 16) {
        const path = queue.shift();
        const last = path[path.length - 1].node;
        if (path.length - 1 > Math.min(4, shortestLen + 1)) continue;
        if (last === b && path.length > 1) {
          shortestLen = Math.min(shortestLen, path.length - 1);
          foundPaths.push(path);
          continue;
        }
        for (const edge of nbrs.get(last) || []) {
          if (path.some((p) => p.node === edge.to)) continue;
          queue.push([...path, { node: edge.to, viaKey: edge.key }]);
        }
      }

      for (const p of foundPaths) {
        for (const step of p) {
          litNodes.add(step.node);
          if (step.viaKey) litBundles.add(step.viaKey);
        }
      }

      // Shared cross-cutting slices touching BOTH A and B
      const sharedSlices = [];
      for (const sl of level.slices) {
        if (sl.touchedSpineIds.includes(a) && sl.touchedSpineIds.includes(b)) {
          sharedSlices.push(sl);
          litNodes.add(sl.id);
          litBundles.add(`slicewire:${sl.id}->${a}`);
          litBundles.add(`slicewire:${sl.id}->${b}`);
        }
      }

      return {
        active: true,
        litNodes,
        litBundles,
        pathStats: {
          pathCount: foundPaths.length,
          shortestHops: Number.isFinite(shortestLen) ? shortestLen : null,
          sharedSlices
        }
      };
    }

    // Bundle Focus
    const activeBundleKey = st.hoverBundleKey || st.selectedBundleKey;
    if (activeBundleKey) {
      litBundles.add(activeBundleKey);
      const allRoutes = [...lay.forwardRoutes.map((r) => r.bundle), ...lay.backRoutes.map((r) => r.bundle)];
      const hit = allRoutes.find((x) => x.key === activeBundleKey);
      if (hit) {
        litNodes.add(hit.u);
        litNodes.add(hit.v);
      }
      return { active: true, litNodes, litBundles, pathStats: null };
    }

    // Node or Slice Ego Network (1-Hop or 2-Hop)
    const focusTarget = st.hoverId || st.selectedId;
    if (focusTarget && lay.boxes.has(focusTarget)) {
      litNodes.add(focusTarget);
      if (lay.boxes.get(focusTarget).ref.isSlice) {
        for (const sr of lay.sliceRoutes) {
          if (sr.sliceId === focusTarget) {
            litBundles.add(sr.key);
            litNodes.add(sr.targetId);
          }
        }
      } else {
        const allRoutes = [...lay.forwardRoutes.map((r) => r.bundle), ...lay.backRoutes.map((r) => r.bundle)];
        let frontier = new Set([focusTarget]);
        for (let hop = 0; hop < st.hopDepth; hop++) {
          const nextFrontier = new Set();
          for (const bun of allRoutes) {
            if (frontier.has(bun.u) || frontier.has(bun.v)) {
              litBundles.add(bun.key);
              if (!litNodes.has(bun.u)) {
                litNodes.add(bun.u);
                nextFrontier.add(bun.u);
              }
              if (!litNodes.has(bun.v)) {
                litNodes.add(bun.v);
                nextFrontier.add(bun.v);
              }
            }
          }
          frontier = nextFrontier;
        }
        // Also light slices touching the focused block
        for (const sr of lay.sliceRoutes) {
          if (sr.targetId === focusTarget) {
            litBundles.add(sr.key);
            litNodes.add(sr.sliceId);
          }
        }
      }
      return { active: true, litNodes, litBundles, pathStats: null };
    }

    return { active: false, litNodes, litBundles, pathStats: null };
  }

  /* ------------------------------------------------------------- Rendering */
  function renderHubTabs() {
    dom.hubBar.replaceChildren();
    if (datasets.length <= 1) {
      dom.hubBar.hidden = true;
      return;
    }
    dom.hubBar.hidden = false;
    dom.hubBar.appendChild(h("span", "hub-brand", "Strata Explorer"));

    datasets.forEach((ds, idx) => {
      const btn = h("button", "hub-tab");
      btn.type = "button";
      btn.setAttribute("role", "tab");
      btn.setAttribute("aria-selected", idx === st.dsIdx ? "true" : "false");
      btn.appendChild(h("span", null, ds.title));
      btn.appendChild(h("span", "hub-pill", `${ds.nodes.length - 1}n · ${ds.edges.length}e`));
      btn.addEventListener("click", () => {
        if (st.dsIdx === idx) return;
        stopPlayback();
        st.dsIdx = idx;
        st.focusId = datasets[idx].rootId;
        st.expandAll = false;
        st.zoom = null;
        st.hiddenRels.clear();
        st.selectedId = null;
        st.selectedBundleKey = null;
        st.compareTargetId = null;
        st.activeTraceIdx = datasets[idx].traces.length ? 0 : -1;
        st.activeStepIdx = 0;
        renderAll();
      });
      dom.hubBar.appendChild(btn);
    });
  }

  function renderTopBar(ds, level) {
    dom.crumbs.replaceChildren();
    const chain = ancestorChain(ds, level.focus.id);
    if (chain.length > 1) {
      const up = h("button", "up-btn", "↑ Up");
      up.type = "button";
      up.title = "Go up one hierarchy level (Esc)";
      up.addEventListener("click", () => {
        st.focusId = chain[chain.length - 2].id;
        setSelection(null);
        st.zoom = null;
        renderAll();
      });
      dom.crumbs.appendChild(up);
    }

    chain.forEach((node, idx) => {
      if (idx > 0) dom.crumbs.appendChild(h("span", "sep", "/"));
      const isLast = idx === chain.length - 1;
      if (isLast) {
        dom.crumbs.appendChild(h("span", "crumb current", node.title));
      } else {
        const b = h("button", "crumb", node.title);
        b.type = "button";
        b.addEventListener("click", () => {
          st.focusId = node.id;
          setSelection(null);
          st.zoom = null;
          renderAll();
        });
        dom.crumbs.appendChild(b);
      }
    });

    dom.modeToggle.textContent = st.expandAll ? "Mode: Expanded" : "Mode: Hierarchy";
    dom.modeToggle.classList.toggle("active", st.expandAll);
    dom.hopToggle.textContent = `Hops: ${st.hopDepth}`;
    dom.hopToggle.classList.toggle("active", st.hopDepth === 2);
    dom.themeToggle.textContent = st.theme === "dark" ? "Theme: Dark" : "Theme: Light";

    // Diagnostics button
    dom.diagToggle.replaceChildren();
    dom.diagToggle.appendChild(h("span", null, "Diagnostics"));
    const badge = h("span", "dcount", String(ds.diagnostics.length));
    const hasErr = ds.diagnostics.some((d) => d.level === "error");
    const hasWarn = ds.diagnostics.some((d) => d.level === "warn");
    if (hasErr) badge.classList.add("lv-error");
    else if (hasWarn) badge.classList.add("lv-warn");
    dom.diagToggle.appendChild(badge);
  }

  function renderLevelHead(ds, level) {
    dom.levelHead.replaceChildren();
    const row = h("div", "lh-row");
    const left = h("div", "lh-title-wrap");
    left.appendChild(h("span", "tag", level.focus.id === ds.rootId ? ds.domain : level.focus.kind));
    const title = h("h1", "lh-title", level.focus.title);
    title.id = "level-title";
    left.appendChild(title);
    row.appendChild(left);

    const ghostCount = level.topGhosts.size + level.botGhosts.size;
    const statsParts = [
      `${level.spineMap.size} spine blocks`,
      `${level.bundles.length} wire bundles`
    ];
    if (level.hiddenLeaves) statsParts.push(`+${level.hiddenLeaves} more blocks not shown`);
    if (ghostCount) statsParts.push(`${ghostCount} outside ghosts`);
    if (level.slices.length) {
      statsParts.push(
          `${level.slices.length} cross-cut ${level.slices.length === 1 ? "lens" : "lenses"}`);
    }
    if (ds.traces.length) statsParts.push(`${ds.traces.length} trace${ds.traces.length > 1 ? "s" : ""}`);
    row.appendChild(h("span", "lh-stats", statsParts.join(" · ")));
    dom.levelHead.appendChild(row);

    const sumText = level.focus.summary || ds.subtitle;
    if (sumText) dom.levelHead.appendChild(h("p", "lh-sum", sumText));
  }

  function renderLegend(ds, level) {
    dom.legend.replaceChildren();

    const relGroup = h("div", "lg-group");
    relGroup.appendChild(h("span", "lg-label", "Wires (edges)"));
    for (const [rid, meta] of ds.relMeta.entries()) {
      const cnt = level.relCounts.get(rid) || 0;
      if (cnt === 0 && ds.relMeta.size > 6) continue;
      const btn = h("button", "lg-item");
      btn.type = "button";
      const active = !st.hiddenRels.has(rid);
      btn.setAttribute("aria-pressed", active ? "true" : "false");

      const sw = svgEl("svg", { width: 20, height: 8, viewBox: "0 0 20 8" }, "swatch");
      const ln = svgEl("line", {
        x1: 1, y1: 4, x2: 19, y2: 4,
        stroke: st.theme === "dark" ? meta.darkColor : meta.lightColor,
        "stroke-width": 2.2,
        "stroke-dasharray": meta.dash
      });
      sw.appendChild(ln);
      btn.appendChild(sw);
      btn.appendChild(h("span", null, meta.label));
      btn.appendChild(h("span", "lg-count", String(cnt)));
      btn.addEventListener("click", () => {
        if (st.hiddenRels.has(rid)) st.hiddenRels.delete(rid);
        else st.hiddenRels.add(rid);
        renderAll();
      });
      relGroup.appendChild(btn);
    }
    dom.legend.appendChild(relGroup);

    // Cross-cutting & Blind-alley filters
    const filterGroup = h("div", "lg-group");
    if (level.slices.length > 0) {
      const sBtn = h("button", "lg-item lg-toggle");
      sBtn.type = "button";
      sBtn.setAttribute("aria-pressed", st.showAllSlices ? "true" : "false");
      sBtn.appendChild(h("span", null, `◆ Cross-Cut Lenses (${level.slices.length})`));
      sBtn.addEventListener("click", () => {
        st.showAllSlices = !st.showAllSlices;
        renderAll();
      });
      filterGroup.appendChild(sBtn);
    }

    const hasBlindNodes = ds.nodes.some((n) => n.status === "blind-alley" || n.status === "error");
    if (hasBlindNodes) {
      const bBtn = h("button", "lg-item lg-toggle");
      bBtn.type = "button";
      bBtn.setAttribute("aria-pressed", !st.hideBlindAlleys ? "true" : "false");
      bBtn.appendChild(h("span", null, st.hideBlindAlleys ? "✕ Blind Alleys Hidden" : "✕ Blind Alleys Shown"));
      bBtn.addEventListener("click", () => {
        st.hideBlindAlleys = !st.hideBlindAlleys;
        renderAll();
      });
      filterGroup.appendChild(bBtn);
    }
    if (filterGroup.childNodes.length) dom.legend.appendChild(filterGroup);

    dom.legend.appendChild(
      h("span", "lg-hint", "Click block to inspect · Double-click container to drill in · Shift+Click 2nd block to trace paths")
    );
  }

  function renderTraceBar(ds, level) {
    dom.traceBar.replaceChildren();
    if (!ds.traces.length) {
      dom.traceBar.hidden = true;
      return;
    }
    dom.traceBar.hidden = false;

    const topRow = h("div", "tb-top");
    topRow.appendChild(h("span", "tb-label", ds.domain.startsWith("atif") ? "ATIF Trajectories" : "Traces"));

    ds.traces.forEach((tr, idx) => {
      const pill = h("button", "trace-pill" + (st.activeTraceIdx === idx ? " active" : ""));
      pill.type = "button";
      const dot = h("span", "trace-dot");
      dot.style.background = tr.color;
      pill.appendChild(dot);
      pill.appendChild(h("span", null, tr.title));
      pill.addEventListener("click", () => {
        stopPlayback();
        st.activeTraceIdx = st.activeTraceIdx === idx ? -1 : idx;
        st.activeStepIdx = 0;
        renderAll();
      });
      topRow.appendChild(pill);
    });

    if (ds.traces.length > 1) {
      const cmpBtn = h("button", "trace-pill" + (st.activeTraceIdx === -2 ? " active" : ""));
      cmpBtn.type = "button";
      cmpBtn.appendChild(h("span", null, `⇄ Compare All (${ds.traces.length})`));
      cmpBtn.addEventListener("click", () => {
        stopPlayback();
        st.activeTraceIdx = st.activeTraceIdx === -2 ? 0 : -2;
        renderAll();
      });
      topRow.appendChild(cmpBtn);
    }
    dom.traceBar.appendChild(topRow);

    if (st.activeTraceIdx >= 0 && ds.traces[st.activeTraceIdx]) {
      const tr = ds.traces[st.activeTraceIdx];
      const clampedStep = Math.max(0, Math.min(st.activeStepIdx, tr.steps.length - 1));
      st.activeStepIdx = clampedStep;

      const ctrl = h("div", "tb-controls");
      const prevBtn = h("button", "tbtn icon-btn", "◀");
      prevBtn.type = "button";
      prevBtn.title = "Previous step ([)";
      prevBtn.addEventListener("click", () => stepTrace(-1));

      const playBtn = h("button", "tbtn", st.playTimer ? "⏸ Pause" : "▶ Play");
      playBtn.type = "button";
      playBtn.addEventListener("click", () => togglePlayback());

      const nextBtn = h("button", "tbtn icon-btn", "▶");
      nextBtn.type = "button";
      nextBtn.title = "Next step (])";
      nextBtn.addEventListener("click", () => stepTrace(1));

      ctrl.appendChild(prevBtn);
      ctrl.appendChild(playBtn);
      ctrl.appendChild(nextBtn);

      const track = h("div", "step-track");
      tr.steps.forEach((step, sIdx) => {
        const pip = h("button", `step-pip role-${step.role || "normal"}${sIdx === clampedStep ? " current" : ""}`);
        pip.type = "button";
        const marker = step.role === "blind-alley" || step.isError ? "✕" : step.role === "backtrack" ? "↺" : "";
        pip.textContent = `${sIdx + 1}${marker}`;
        pip.title = `Step ${sIdx + 1}: ${step.label}`;
        pip.addEventListener("click", () => {
          stopPlayback();
          st.activeStepIdx = sIdx;
          const visId = level.resolveInside(step.nodeId);
          if (visId) setSelection(visId);
          renderAll();
        });
        track.appendChild(pip);
      });
      ctrl.appendChild(track);

      const curStep = tr.steps[clampedStep];
      if (curStep) {
        ctrl.appendChild(h("span", "step-readout", `Step ${clampedStep + 1}/${tr.steps.length}: ${curStep.label}`));
      }
      dom.traceBar.appendChild(ctrl);
    }
  }

  function renderPathBanner(ds, level, hlInfo) {
    dom.pathBanner.replaceChildren();
    if (!st.selectedId || !st.compareTargetId || !hlInfo.pathStats) {
      dom.pathBanner.hidden = true;
      return;
    }
    dom.pathBanner.hidden = false;

    const boxA = st.currentLayout?.boxes.get(st.selectedId);
    const boxB = st.currentLayout?.boxes.get(st.compareTargetId);
    const nameA = boxA?.ref?.node?.title || st.selectedId;
    const nameB = boxB?.ref?.node?.title || st.compareTargetId;

    const ps = hlInfo.pathStats;
    const left = h("div");
    left.appendChild(h("strong", null, `Path Trace: ${nameA} ↔ ${nameB}`));
    const detail = ps.pathCount > 0
      ? ` · ${ps.pathCount} connecting path${ps.pathCount > 1 ? "s" : ""} (shortest: ${ps.shortestHops} hop${ps.shortestHops > 1 ? "s" : ""})`
      : " · No direct spine path within 4 hops";
    const sliceNote = ps.sharedSlices.length
      ? ` · ${ps.sharedSlices.length} shared web slice${ps.sharedSlices.length > 1 ? "s" : ""}`
      : "";
    left.appendChild(h("span", null, detail + sliceNote));
    dom.pathBanner.appendChild(left);

    const clearBtn = h("button", "tbtn", "Clear Path (Esc)");
    clearBtn.type = "button";
    clearBtn.addEventListener("click", () => {
      st.compareTargetId = null;
      renderAll();
    });
    dom.pathBanner.appendChild(clearBtn);
  }

  function arrowPolygon(x, y, dir, color) {
    let pts;
    if (dir === "left") {
      pts = `${x.toFixed(1)},${y.toFixed(1)} ${(x + 7.5).toFixed(1)},${(y - 4.2).toFixed(1)} ${(x + 7.5).toFixed(1)},${(y + 4.2).toFixed(1)}`;
    } else if (dir === "right") {
      pts = `${x.toFixed(1)},${y.toFixed(1)} ${(x - 7.5).toFixed(1)},${(y - 4.2).toFixed(1)} ${(x - 7.5).toFixed(1)},${(y + 4.2).toFixed(1)}`;
    } else {
      pts = `${x.toFixed(1)},${y.toFixed(1)} ${(x - 4.2).toFixed(1)},${(y - 7.5).toFixed(1)} ${(x + 4.2).toFixed(1)},${(y - 7.5).toFixed(1)}`;
    }
    return svgEl("polygon", { points: pts, fill: color }, "head");
  }

  function renderCanvas(ds, level, lay, hlInfo) {
    dom.edges.replaceChildren();
    dom.blocks.replaceChildren();

    if (!level.spineMap.size) {
      dom.blocks.appendChild(h("p", "empty", "No visible blocks at this focus level."));
      return;
    }

    dom.edges.setAttribute("width", String(lay.width));
    dom.edges.setAttribute("height", String(lay.height));
    dom.edges.setAttribute("viewBox", `0 0 ${lay.width} ${lay.height}`);

    dom.viewport.classList.toggle("hl-mode", hlInfo.active);
    dom.viewport.classList.toggle("show-slices", st.showAllSlices);

    // Optional group frames in Expanded mode
    for (const fr of lay.frames) {
      dom.edges.appendChild(svgEl("rect", { x: fr.x, y: fr.y, width: fr.w, height: fr.h, rx: 10 }, "frame"));
      const lbl = h("div", "frame-label", fr.title);
      lbl.style.left = `${fr.x + 8}px`;
      lbl.style.top = `${fr.y + 4}px`;
      dom.blocks.appendChild(lbl);
    }

    // Optional dataset-supplied notes drawn in the left margin beside a spine block
    if (level.focus.id === ds.rootId) {
      for (const note of ds.axisNotes || []) {
        const bx = lay.boxes.get(note.nodeId);
        if (!bx || bx.x < 220) continue;
        const el = h("div", "frame-label");
        el.style.left = "20px";
        el.style.top = `${bx.y + 4}px`;
        el.style.width = `${Math.max(180, bx.x - 36)}px`;
        el.style.whiteSpace = "normal";
        el.style.lineHeight = "1.35";
        el.textContent = String(note.text || "");
        dom.blocks.appendChild(el);
      }
    }

    // Cross-Cutting Lens Band Divider
    if (lay.bandY !== null) {
      const bl = h("div", "band-label");
      bl.style.left = `${GEO.padX}px`;
      bl.style.top = `${lay.bandY}px`;
      bl.style.width = `${Math.max(400, lay.width - GEO.padX * 2)}px`;
      bl.appendChild(h("span", null, "Cross-Cut Lenses & Shared Provenance "));
      bl.appendChild(h("span", "band-hint", "· hover or click a lens to trace shared concepts across the spine"));
      dom.blocks.appendChild(bl);
    }

    // 1. Cross-cutting slice threads (rendered beneath spine bundles)
    const sliceFrag = document.createDocumentFragment();
    for (const sr of lay.sliceRoutes) {
      const g = svgEl("g", { "data-bundle-key": sr.key }, "bundle slice-wire");
      if (hlInfo.litBundles.has(sr.key)) g.classList.add("hl");
      const ln = svgEl("path", {
        d: sr.d,
        stroke: st.theme === "dark" ? "#e879f9" : "#a21caf",
        "stroke-dasharray": "4 4",
        "stroke-opacity": "0.68"
      }, "line");
      g.appendChild(ln);
      sliceFrag.appendChild(g);
    }
    dom.edges.appendChild(sliceFrag);

    // 2. Forward multi-lane colored wire bundles
    const countLayer = document.createDocumentFragment();
    const placedCountPts = [];
    const pickCountPt = (pathEl, defaultT) => {
      const totalLen = pathEl.getTotalLength();
      const candidates = [defaultT, 0.36, 0.64, 0.24, 0.76, 0.16, 0.84];
      let bestPt = pathEl.getPointAtLength(totalLen * defaultT);
      let bestClear = -1;
      for (const t of candidates) {
        const clampedT = Math.min(0.92, Math.max(0.08, t));
        const pt = pathEl.getPointAtLength(totalLen * clampedT);
        let minDist = Infinity;
        for (const o of placedCountPts) {
          if (Math.abs(pt.x - o.x) < 30 && Math.abs(pt.y - o.y) < 20) {
            minDist = Math.min(minDist, Math.hypot(pt.x - o.x, pt.y - o.y));
          }
        }
        if (minDist === Infinity) {
          placedCountPts.push({ x: pt.x, y: pt.y });
          return pt;
        }
        if (minDist > bestClear) {
          bestClear = minDist;
          bestPt = pt;
        }
      }
      placedCountPts.push({ x: bestPt.x, y: bestPt.y });
      return bestPt;
    };
    for (const fr of lay.forwardRoutes) {
      const b = fr.bundle;
      const g = svgEl("g", { "data-bundle-key": b.key }, "bundle");
      if (fr.isQuietBypass) g.setAttribute("opacity", "0.42");
      if (hlInfo.litBundles.has(b.key)) {
        g.classList.add("hl");
        g.removeAttribute("opacity");
      }
      if (st.selectedBundleKey === b.key) {
        g.classList.add("picked");
        g.removeAttribute("opacity");
      }

      let midLanePath = null;
      fr.lanes.forEach((lane, idx) => {
        const col = relColor(ds, lane.rel);
        const meta = ds.relMeta.get(lane.rel);
        const p = svgEl("path", {
          d: lane.d,
          stroke: col,
          "stroke-dasharray": meta ? meta.dash : "none"
        }, "line");
        g.appendChild(p);
        g.appendChild(arrowPolygon(lane.arrowX, lane.arrowY, lane.arrowDir, col));
        if (idx === Math.floor(fr.lanes.length / 2)) midLanePath = p;

        const hit = svgEl("path", { d: lane.d }, "hit");
        bindBundleEvents(hit, b);
        g.appendChild(hit);
      });
      dom.edges.appendChild(g);

      if (b.edges.length >= 2 && midLanePath) {
        try {
          const pt = pickCountPt(midLanePath, fr.badgeT);
          const label = String(b.edges.length);
          const pw = Math.max(20, label.length * 7 + 10);
          const cg = svgEl("g", { transform: `translate(${pt.x.toFixed(1)},${pt.y.toFixed(1)})`, "data-bundle-key": b.key }, "count");
          if (hlInfo.litBundles.has(b.key)) cg.classList.add("hl");
          if (st.selectedBundleKey === b.key) cg.classList.add("picked");
          cg.appendChild(svgEl("rect", { x: -pw / 2, y: -9, width: pw, height: 18, rx: 9 }));
          const tx = svgEl("text", { x: 0, y: 3.5, "text-anchor": "middle" });
          tx.textContent = label;
          cg.appendChild(tx);
          bindBundleEvents(cg, b);
          countLayer.appendChild(cg);
        } catch (_) { /* ignore SVG measurement fallback */ }
      }
    }

    // 3. Explicit outer return arcs for Backtracks & Loops (↺)
    for (const br of lay.backRoutes) {
      const b = br.bundle;
      const col = b.isBacktrack
        ? (st.theme === "dark" ? "#fb923c" : "#c2410c")
        : relColor(ds, br.rel);
      const g = svgEl("g", { "data-bundle-key": b.key }, "bundle");
      if (hlInfo.litBundles.has(b.key)) g.classList.add("hl");
      if (st.selectedBundleKey === b.key) g.classList.add("picked");

      const p = svgEl("path", {
        d: br.d,
        stroke: col,
        "stroke-dasharray": "7 4"
      }, "line backtrack-arc");
      g.appendChild(p);
      g.appendChild(arrowPolygon(br.arrowX, br.arrowY, br.arrowDir, col));

      const hit = svgEl("path", { d: br.d }, "hit");
      bindBundleEvents(hit, b);
      g.appendChild(hit);
      dom.edges.appendChild(g);

      // Pill badge on the outer return arc ("↺" or "↺ N")
      try {
        const pt = pickCountPt(p, 0.5);
        const label = b.edges.length > 1 ? `↺ ${b.edges.length}` : "↺";
        const pw = Math.max(22, label.length * 6.5 + 10);
        const cg = svgEl("g", { transform: `translate(${pt.x.toFixed(1)},${pt.y.toFixed(1)})`, "data-bundle-key": b.key }, "count backtrack-pill");
        if (hlInfo.litBundles.has(b.key)) cg.classList.add("hl");
        cg.appendChild(svgEl("rect", { x: -pw / 2, y: -9, width: pw, height: 18, rx: 9 }));
        const tx = svgEl("text", { x: 0, y: 3.5, "text-anchor": "middle" });
        tx.textContent = label;
        cg.appendChild(tx);
        bindBundleEvents(cg, b);
        countLayer.appendChild(cg);
      } catch (_) { /* ignore */ }
    }
    dom.edges.appendChild(countLayer);

    // Compute Trace Visit Badges per visible block (cap at 4 + overflow '+N' on 1 row)
    const visitMap = new Map(); // boxId -> [{ text, color, cls }]
    const visitTotal = new Map();
    let currentTraceBoxId = null;

    if (st.activeTraceIdx >= 0 && ds.traces[st.activeTraceIdx]) {
      const tr = ds.traces[st.activeTraceIdx];
      tr.steps.forEach((step, idx) => {
        const visId = level.resolveInside(step.nodeId);
        if (!visId) return;
        visitTotal.set(visId, (visitTotal.get(visId) || 0) + 1);
        if (!visitMap.has(visId)) visitMap.set(visId, []);
        const arr = visitMap.get(visId);
        if (arr.length < 4) {
          const cls = step.role === "blind-alley" || step.isError
            ? "chip-blind"
            : step.role === "backtrack" ? "chip-backtrack" : "";
          arr.push({ text: `#${idx + 1}`, color: tr.color, cls });
        }
        if (idx === st.activeStepIdx) currentTraceBoxId = visId;
      });
      for (const [visId, arr] of visitMap.entries()) {
        const extra = (visitTotal.get(visId) || 0) - arr.length;
        if (extra > 0) arr.push({ text: `+${extra}`, color: tr.color, cls: "" });
      }
    } else if (st.activeTraceIdx === -2) {
      // Compare All Runs mode: attach run-colored indicator chips to visited nodes
      ds.traces.forEach((tr, rIdx) => {
        const touched = new Set();
        const failed = new Set();
        for (const step of tr.steps) {
          const visId = level.resolveInside(step.nodeId);
          if (visId) {
            touched.add(visId);
            if (step.isError || step.role === "blind-alley") failed.add(visId);
          }
        }
        for (const visId of touched) {
          if (!visitMap.has(visId)) visitMap.set(visId, []);
          visitMap.get(visId).push({
            text: `R${rIdx + 1}`,
            color: tr.color,
            cls: failed.has(visId) ? "chip-blind" : ""
          });
        }
      });
    }

    // 4. Render DOM Cards (Spine, Ghost OUTSIDE, and Cross-Cutting Slices)
    const blockFrag = document.createDocumentFragment();
    for (const [id, bx] of lay.boxes.entries()) {
      const ref = bx.ref;
      const card = h("div", "block");
      card.dataset.boxId = id;
      card.style.left = `${bx.x}px`;
      card.style.top = `${bx.y}px`;
      card.style.width = `${bx.w}px`;
      card.style.height = `${bx.h}px`;
      card.tabIndex = 0;

      if (hlInfo.litNodes.has(id)) card.classList.add("hl");
      if (st.selectedId === id) card.classList.add("selected");
      if (st.compareTargetId === id) card.classList.add("compare-target");
      if (currentTraceBoxId === id) card.classList.add("trace-current");

      if (ref.isSlice) {
        card.classList.add("slice-block");
        const head = h("div", "b-head");
        head.appendChild(h("span", "b-kind", ref.overlay.kind));
        const cnt = ref.touchedSpineIds.length;
        const unit = !st.expandAll && level.focus.id === ds.rootId
          ? (ds.levelLabel || (ds.domain === "okf-wiki" ? "section" : ds.domain === "process" ? "phase" : "layer"))
          : (!st.expandAll && level.focus.kids && level.focus.kids.some((k) => k.kids && k.kids.length))
            ? "group"
            : "item";
        head.appendChild(h("span", "badge", `${cnt} ${unit}${cnt === 1 ? "" : "s"}`));
        card.appendChild(head);
        card.appendChild(h("div", "b-title", ref.overlay.title));
      } else if (ref.isGhost) {
        card.classList.add("ghost");
        const head = h("div", "b-head");
        head.appendChild(h("span", "b-kind", ref.zone === "top" ? "↑ Outside Caller" : "↓ Outside Target"));
        card.appendChild(head);
        card.appendChild(h("div", "b-title", ref.node ? ref.node.title : ref.realId));
      } else {
        const node = ref.node;
        const hasKids = node.kids && node.kids.length > 0 && !st.expandAll;
        if (hasKids) card.classList.add("has-kids");
        if (node.status) card.classList.add(`st-${cssToken(node.status)}`);

        const head = h("div", "b-head");
        head.appendChild(h("span", "b-kind", node.kind || "node"));
        if (node.status && node.status !== "ready") {
          const statusLabel = node.status === "blind-alley" ? "✕ blind alley" : node.status;
          head.appendChild(h("span", `badge st-${cssToken(node.status)}`, statusLabel));
        } else if (node.trust && node.trust.tier === "human-reviewed") {
          head.appendChild(h("span", "badge st-verified", "verified"));
        }
        card.appendChild(head);

        card.appendChild(h("div", "b-title", node.title));

        const foot = h("div", "b-foot");
        const inCnt = hasKids ? (level.liftedIn.get(id) || 0) : node.inDeg;
        const outCnt = hasKids ? (level.liftedOut.get(id) || 0) : node.outDeg;
        const degText = `${inCnt} in · ${outCnt} out`;
        foot.appendChild(h("span", null, degText));
        if (hasKids) {
          const openBtn = h("button", "b-open", `${node.kids.length} parts →`);
          openBtn.type = "button";
          openBtn.addEventListener("click", (ev) => {
            ev.stopPropagation();
            drillInto(node.id);
          });
          foot.appendChild(openBtn);
        } else if (node.sources && node.sources.length > 0) {
          foot.appendChild(h("span", null, `${node.sources.length} src`));
        }
        card.appendChild(foot);
      }

      // Attach Trace Visit Chips if present
      const chips = visitMap.get(id);
      if (chips && chips.length) {
        const wrap = h("div", "visit-chips");
        for (const c of chips) {
          const chip = h("span", `visit-chip ${c.cls}`.trim(), c.text);
          if (!c.cls && c.color) chip.style.borderColor = c.color;
          wrap.appendChild(chip);
        }
        card.appendChild(wrap);
      }

      bindBlockEvents(card, id, ref);
      blockFrag.appendChild(card);
    }
    dom.blocks.appendChild(blockFrag);

    applyScale(lay);
  }

  function applyScale(lay) {
    const vw = Math.max(320, dom.viewport.clientWidth - 16);
    const vh = Math.max(240, dom.viewport.clientHeight - 16);
    let scale = st.zoom;
    if (scale === null) {
      const fitX = vw / lay.width;
      const fitY = vh / lay.height;
      scale = Math.max(0.42, Math.min(1.0, Math.min(fitX, fitY)));
    }
    st.scale = scale;
    dom.canvas.style.width = `${lay.width}px`;
    dom.canvas.style.height = `${lay.height}px`;
    dom.canvas.style.transform = `scale(${scale.toFixed(3)})`;
    dom.sizer.style.width = `${Math.ceil(lay.width * scale)}px`;
    dom.sizer.style.height = `${Math.ceil(lay.height * scale)}px`;
    dom.zoomFit.textContent = st.zoom === null ? `Fit (${Math.round(scale * 100)}%)` : `${Math.round(scale * 100)}%`;
  }

  /* ------------------------------------------------------ Inspector Panel */
  function renderInspector(ds, level, lay) {
    dom.panelBody.replaceChildren();

    // Case 1: Selected Wire Bundle
    if (st.selectedBundleKey) {
      const allRoutes = [...lay.forwardRoutes.map((r) => r.bundle), ...lay.backRoutes.map((r) => r.bundle)];
      const bun = allRoutes.find((b) => b.key === st.selectedBundleKey);
      if (bun) {
        const tags = h("div", "d-tags");
        tags.appendChild(h("span", "tag", bun.isBacktrack ? "↺ Backtrack Arc" : bun.isLoop ? "↺ Cycle Arc" : "Wire Bundle"));
        tags.appendChild(h("span", "badge", `${bun.edges.length} edge${bun.edges.length > 1 ? "s" : ""}`));
        dom.panelBody.appendChild(tags);

        const nameU = lay.boxes.get(bun.u)?.ref?.node?.title || bun.u;
        const nameV = lay.boxes.get(bun.v)?.ref?.node?.title || bun.v;
        dom.panelBody.appendChild(h("h2", "d-title", `${nameU} → ${nameV}`));
        dom.panelBody.appendChild(
          h("p", "d-sum", bun.isBacktrack
            ? "Explicit backtrack / retry return transition preserved without reversing causal reading order."
            : "Lifted connections bundled across hierarchy levels and grouped into parallel relation lanes.")
        );

        const sec = h("div", "d-sec");
        sec.appendChild(h("h3", null, `Underlying Links (${bun.edges.length})`));
        const ul = h("ul", "d-list");
        for (const e of bun.edges.slice(0, 45)) {
          const li = h("li", "d-conn");
          const top = h("div", "d-conn-top");
          const srcNode = ds.byId.get(e.from);
          const dstNode = ds.byId.get(e.to);
          const jump = h("button", "d-jump", `${srcNode ? srcNode.title : e.from} → ${dstNode ? dstNode.title : e.to}`);
          jump.type = "button";
          jump.addEventListener("click", () => jumpToNode(ds, e.to));
          top.appendChild(jump);
          const pill = h("span", "d-rel-pill", e.relation);
          pill.style.color = relColor(ds, e.relation);
          top.appendChild(pill);
          li.appendChild(top);
          const snip = e.contextSnippet || e.summary;
          if (snip) li.appendChild(h("p", "d-snippet", snip));
          ul.appendChild(li);
        }
        sec.appendChild(ul);
        dom.panelBody.appendChild(sec);
        return;
      }
    }

    // Case 2: Selected Cross-Cutting Slice
    const ov = st.selectedId ? ds.overlays.find((o) => sliceBoxId(o.id) === st.selectedId) : null;
    if (ov) {
      // Search can select a slice that the level model left out (it shows at most 18).
      const tags = h("div", "d-tags");
      tags.appendChild(h("span", "tag", `◆ ${ov.kind}`));
      tags.appendChild(h("span", "badge", `${ov.touches.length} total touches`));
      dom.panelBody.appendChild(tags);
      dom.panelBody.appendChild(h("h2", "d-title", ov.title));
      dom.panelBody.appendChild(h("p", "d-id", ov.id));
      if (ov.summary) dom.panelBody.appendChild(h("p", "d-sum", ov.summary));

      const href = safeUrl(ov.url);
      if (href) {
        const linkWrap = h("div", "d-actions");
        const a = h("a", "d-action", "Open Canonical Source ↗");
        a.href = href;
        a.target = "_blank";
        a.rel = "noopener noreferrer";
        linkWrap.appendChild(a);
        dom.panelBody.appendChild(linkWrap);
      }

      const sec = h("div", "d-sec");
      sec.appendChild(h("h3", null, `Touched Concepts / Blocks (${ov.touches.length})`));
      const ul = h("ul", "d-list");
      for (const tid of ov.touches) {
        const tn = ds.byId.get(tid);
        if (!tn) continue;
        const li = h("li", "d-conn");
        const jump = h("button", "d-jump", tn.title);
        jump.type = "button";
        jump.addEventListener("click", () => jumpToNode(ds, tid));
        li.appendChild(jump);
        if (tn.summary) li.appendChild(h("p", "d-snippet", tn.summary));
        ul.appendChild(li);
      }
      sec.appendChild(ul);
      dom.panelBody.appendChild(sec);
      return;
    }

    // Case 3: Selected Node (or Ghost, or Current Level Container fallback)
    let targetNode = level.focus;
    let isGhostSel = false;
    if (st.selectedId && lay.boxes.has(st.selectedId)) {
      const ref = lay.boxes.get(st.selectedId).ref;
      if (ref.isGhost) {
        targetNode = ref.node || ds.byId.get(ref.realId) || level.focus;
        isGhostSel = true;
      } else if (ref.node) {
        targetNode = ref.node;
      }
    }

    const tags = h("div", "d-tags");
    tags.appendChild(h("span", "tag", targetNode.kind || "block"));
    if (targetNode.status) {
      tags.appendChild(h("span", `badge st-${cssToken(targetNode.status)}`, targetNode.status));
    }
    if (targetNode.trust && targetNode.trust.tier) {
      tags.appendChild(h("span", `badge st-${targetNode.trust.tier === "human-reviewed" ? "verified" : "draft"}`, `OKF: ${targetNode.trust.tier}`));
    }
    if (isGhostSel) tags.appendChild(h("span", "badge", "Outside Current Focus"));
    dom.panelBody.appendChild(tags);

    dom.panelBody.appendChild(h("h2", "d-title", targetNode.title));
    dom.panelBody.appendChild(h("p", "d-id", targetNode.id));
    if (targetNode.summary) dom.panelBody.appendChild(h("p", "d-sum", targetNode.summary));
    if (targetNode.body) dom.panelBody.appendChild(h("div", "d-body", targetNode.body));

    // Action buttons
    const actions = h("div", "d-actions");
    if (targetNode.kids && targetNode.kids.length > 0 && targetNode.id !== level.focus.id) {
      const drillBtn = h("button", "d-action", `Open ${targetNode.kids.length} parts →`);
      drillBtn.type = "button";
      drillBtn.addEventListener("click", () => drillInto(targetNode.id));
      actions.appendChild(drillBtn);
    }
    if (isGhostSel && targetNode.id) {
      const jmp = h("button", "d-action", "Jump to Home Level →");
      jmp.type = "button";
      jmp.addEventListener("click", () => jumpToNode(ds, targetNode.id));
      actions.appendChild(jmp);
    }
    const extUrl = safeUrl(targetNode.url);
    if (extUrl) {
      const a = h("a", "d-action quiet", "Source Resource ↗");
      a.href = extUrl;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      actions.appendChild(a);
    }
    if (actions.childNodes.length) dom.panelBody.appendChild(actions);

    // Metrics grid (if present)
    const mEntries = Object.entries(targetNode.metrics || {}).filter(([, v]) => v !== null && v !== undefined && v !== "");
    if (mEntries.length > 0) {
      const grid = h("div", "d-meta-grid");
      for (const [k, v] of mEntries.slice(0, 6)) {
        const cell = h("div", "d-metric");
        cell.appendChild(h("div", "d-metric-k", k.replace(/_/g, " ")));
        cell.appendChild(h("div", "d-metric-v", String(v)));
        grid.appendChild(cell);
      }
      dom.panelBody.appendChild(grid);
    }

    // Active Trace Step Details visiting this node
    if (st.activeTraceIdx >= 0 && ds.traces[st.activeTraceIdx]) {
      const tr = ds.traces[st.activeTraceIdx];
      const matchingSteps = tr.steps.filter(
        (s) => s.nodeId === targetNode.id || isDescendantOf(ds, s.nodeId, targetNode.id)
      );
      if (matchingSteps.length > 0) {
        const tSec = h("div", "d-sec");
        tSec.appendChild(h("h3", null, `Trajectory Steps on Block (${matchingSteps.length})`));
        const ul = h("ul", "d-list");
        for (const s of matchingSteps.slice(0, 12)) {
          const li = h("li", "d-conn");
          const top = h("div", "d-conn-top");
          top.appendChild(h("strong", null, `Step ${s.stepIndex}: ${s.label}`));
          if (s.role && s.role !== "normal") {
            top.appendChild(h("span", `badge st-${cssToken(s.role)}`, s.role));
          }
          li.appendChild(top);
          if (s.thought) li.appendChild(h("p", "d-snippet", `Thought: ${s.thought}`));
          if (s.observation) li.appendChild(h("p", "d-snippet", `Result: ${s.observation}`));
          ul.appendChild(li);
        }
        tSec.appendChild(ul);
        dom.panelBody.appendChild(tSec);
      }
    }

    // Sources / Provenance list
    if (targetNode.sources && targetNode.sources.length > 0) {
      const sSec = h("div", "d-sec");
      sSec.appendChild(h("h3", null, `Provenance Sources (${targetNode.sources.length})`));
      const ul = h("ul", "d-list");
      for (const src of targetNode.sources.slice(0, 12)) {
        const li = h("li", "d-conn");
        const u = safeUrl(src.url);
        if (u) {
          const a = h("a", null, src.title || src.id || u);
          a.href = u;
          a.target = "_blank";
          a.rel = "noopener noreferrer";
          li.appendChild(a);
        } else {
          li.appendChild(h("span", null, src.title || src.id));
        }
        if (src.author) li.appendChild(h("p", "d-snippet", `Author: ${src.author}`));
        ul.appendChild(li);
      }
      sSec.appendChild(ul);
      dom.panelBody.appendChild(sSec);
    }

    // Outgoing & Incoming direct edges
    const outgoing = ds.edges.filter((e) => e.from === targetNode.id);
    const incoming = ds.edges.filter((e) => e.to === targetNode.id);

    if (outgoing.length > 0) {
      const oSec = h("div", "d-sec");
      oSec.appendChild(h("h3", null, `Outgoing Connections (${outgoing.length})`));
      const ul = h("ul", "d-list");
      for (const e of outgoing.slice(0, 25)) {
        const dst = ds.byId.get(e.to);
        const li = h("li", "d-conn");
        const top = h("div", "d-conn-top");
        const jmp = h("button", "d-jump", dst ? dst.title : e.to);
        jmp.type = "button";
        jmp.addEventListener("click", () => jumpToNode(ds, e.to));
        top.appendChild(jmp);
        const pill = h("span", "d-rel-pill", e.relation);
        pill.style.color = relColor(ds, e.relation);
        top.appendChild(pill);
        li.appendChild(top);
        if (e.contextSnippet || e.summary) li.appendChild(h("p", "d-snippet", e.contextSnippet || e.summary));
        ul.appendChild(li);
      }
      oSec.appendChild(ul);
      dom.panelBody.appendChild(oSec);
    }

    if (incoming.length > 0) {
      const iSec = h("div", "d-sec");
      iSec.appendChild(h("h3", null, `Incoming Connections (${incoming.length})`));
      const ul = h("ul", "d-list");
      for (const e of incoming.slice(0, 25)) {
        const src = ds.byId.get(e.from);
        const li = h("li", "d-conn");
        const top = h("div", "d-conn-top");
        const jmp = h("button", "d-jump", src ? src.title : e.from);
        jmp.type = "button";
        jmp.addEventListener("click", () => jumpToNode(ds, e.from));
        top.appendChild(jmp);
        const pill = h("span", "d-rel-pill", e.relation);
        pill.style.color = relColor(ds, e.relation);
        top.appendChild(pill);
        li.appendChild(top);
        if (e.contextSnippet || e.summary) li.appendChild(h("p", "d-snippet", e.contextSnippet || e.summary));
        ul.appendChild(li);
      }
      iSec.appendChild(ul);
      dom.panelBody.appendChild(iSec);
    }
  }

  function renderDiagnosticsDrawer(ds) {
    dom.drawer.replaceChildren();
    dom.drawer.appendChild(h("h3", null, `Compiler & Integrity Diagnostics (${ds.diagnostics.length})`));
    if (!ds.diagnostics.length) {
      dom.drawer.appendChild(h("p", "d-snippet", "No integrity errors or warnings. Node ids, parent references, edge endpoints, and trace steps were checked."));
      return;
    }
    for (const d of ds.diagnostics) {
      const row = h("div", "diag-row");
      row.appendChild(h("span", `diag-code lv-${cssToken(d.level || "info")}`, `[${(d.level || "info").toUpperCase()}] ${d.code || "CHECK"}`));
      row.appendChild(h("span", null, d.message));
      dom.drawer.appendChild(row);
    }
  }

  /* --------------------------------------------------- Interaction Events */
  function bindBlockEvents(el, boxId, ref) {
    el.addEventListener("mouseenter", (ev) => {
      st.hoverId = boxId;
      updateHoverHighlights();
      const summary = ref.isSlice
        ? ref.overlay.summary
        : ref.node ? ref.node.summary : "";
      if (summary) showTip(ev, summary);
    });
    el.addEventListener("mousemove", moveTip);
    el.addEventListener("mouseleave", () => {
      st.hoverId = null;
      hideTip();
      updateHoverHighlights();
    });
    el.addEventListener("click", (ev) => {
      ev.stopPropagation();
      const selectedIsSlice = curDs().overlays.some((o) => sliceBoxId(o.id) === st.selectedId);
      if (ev.shiftKey && st.selectedId && st.selectedId !== boxId && !selectedIsSlice && !ref.isSlice) {
        st.compareTargetId = boxId;
        st.selectedBundleKey = null;
        renderAll();
        return;
      }
      st.compareTargetId = null;
      st.selectedBundleKey = null;
      st.selectedId = st.selectedId === boxId ? null : boxId;
      renderAll();
    });
    el.addEventListener("dblclick", (ev) => {
      ev.stopPropagation();
      if (!ref.isSlice && !ref.isGhost && ref.node && ref.node.kids && ref.node.kids.length > 0) {
        drillInto(ref.node.id);
      } else if (ref.isGhost && ref.realId) {
        jumpToNode(curDs(), ref.realId);
      }
    });
  }

  function bindBundleEvents(el, bundle) {
    el.addEventListener("mouseenter", (ev) => {
      st.hoverBundleKey = bundle.key;
      updateHoverHighlights();
      const relSummary = Array.from(bundle.byRel.entries())
        .map(([r, arr]) => `${r} (${arr.length})`)
        .join(", ");
      showTip(ev, `${bundle.edges.length} link${bundle.edges.length > 1 ? "s" : ""}: ${relSummary}`);
    });
    el.addEventListener("mousemove", moveTip);
    el.addEventListener("mouseleave", () => {
      st.hoverBundleKey = null;
      hideTip();
      updateHoverHighlights();
    });
    el.addEventListener("click", (ev) => {
      ev.stopPropagation();
      st.selectedId = null;
      st.compareTargetId = null;
      st.selectedBundleKey = st.selectedBundleKey === bundle.key ? null : bundle.key;
      renderAll();
    });
  }

  function updateHoverHighlights() {
    if (!st.currentLayout) return;
    const ds = curDs();
    const level = st.currentLevel;
    const lay = st.currentLayout;
    const hlInfo = computeHighlightSets(ds, level, lay);
    dom.viewport.classList.toggle("hl-mode", hlInfo.active);
    for (const el of dom.blocks.querySelectorAll(".block[data-box-id]")) {
      el.classList.toggle("hl", hlInfo.litNodes.has(el.dataset.boxId));
    }
    for (const el of dom.edges.querySelectorAll("[data-bundle-key]")) {
      el.classList.toggle("hl", hlInfo.litBundles.has(el.getAttribute("data-bundle-key")));
    }
  }

  function drillInto(nodeId) {
    st.focusId = nodeId;
    st.expandAll = false;
    st.selectedId = null;
    st.compareTargetId = null;
    st.selectedBundleKey = null;
    st.zoom = null;
    renderAll();
  }

  function jumpToNode(ds, nodeId) {
    const target = ds.byId.get(nodeId);
    if (!target) return;
    if (target.parent && ds.byId.has(target.parent)) {
      st.focusId = target.parent;
    } else {
      st.focusId = ds.rootId;
    }
    st.expandAll = false;
    setSelection(target.id);
    renderAll();
  }

  /* --------------------------------------------------- Tooltip & Playback */
  function showTip(ev, text) {
    dom.tip.textContent = text;
    dom.tip.hidden = false;
    moveTip(ev);
  }
  function moveTip(ev) {
    if (dom.tip.hidden) return;
    const x = Math.min(window.innerWidth - 350, ev.clientX + 14);
    const y = Math.min(window.innerHeight - 80, ev.clientY + 14);
    dom.tip.style.left = `${Math.max(8, x)}px`;
    dom.tip.style.top = `${Math.max(8, y)}px`;
  }
  function hideTip() {
    dom.tip.hidden = true;
  }

  function stepTrace(delta) {
    const ds = curDs();
    if (st.activeTraceIdx < 0 || !ds.traces[st.activeTraceIdx]) return;
    const tr = ds.traces[st.activeTraceIdx];
    st.activeStepIdx = (st.activeStepIdx + delta + tr.steps.length) % tr.steps.length;
    const step = tr.steps[st.activeStepIdx];
    if (step && st.currentLevel) {
      const visId = st.currentLevel.resolveInside(step.nodeId);
      if (visId) setSelection(visId);
    }
    renderAll();
  }

  function stopPlayback() {
    if (st.playTimer) {
      clearInterval(st.playTimer);
      st.playTimer = null;
    }
  }

  function togglePlayback() {
    if (st.playTimer) {
      stopPlayback();
      renderAll();
      return;
    }
    st.playTimer = setInterval(() => stepTrace(1), 1050);
    renderAll();
  }

  /* ------------------------------------------------------- Global Controls */
  dom.modeToggle.addEventListener("click", () => {
    st.expandAll = !st.expandAll;
    setSelection(null);
    st.zoom = null;
    renderAll();
  });

  dom.hopToggle.addEventListener("click", () => {
    st.hopDepth = st.hopDepth === 1 ? 2 : 1;
    renderAll();
  });

  function stepZoom(delta) {
    const cur = st.zoom ?? st.scale;
    st.zoom = Math.min(2.2, Math.max(0.3, +(cur + delta).toFixed(2)));
    if (st.currentLayout) applyScale(st.currentLayout);
  }

  dom.zoomIn.addEventListener("click", () => stepZoom(0.15));
  dom.zoomOut.addEventListener("click", () => stepZoom(-0.15));

  dom.zoomFit.addEventListener("click", () => {
    st.zoom = null;
    if (st.currentLayout) applyScale(st.currentLayout);
  });

  dom.themeToggle.addEventListener("click", () => {
    st.theme = st.theme === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", st.theme);
    renderAll();
  });

  dom.panelToggle.addEventListener("click", () => {
    const closed = dom.main.classList.toggle("panel-closed");
    dom.panelToggle.setAttribute("aria-expanded", closed ? "false" : "true");
    if (st.currentLayout) applyScale(st.currentLayout);
  });

  function setDrawerOpen(open) {
    dom.drawer.hidden = !open;
    dom.diagToggle.setAttribute("aria-expanded", open ? "true" : "false");
  }

  function setSearchOpen(open) {
    dom.searchResults.hidden = !open;
    dom.searchInput.setAttribute("aria-expanded", open ? "true" : "false");
  }

  dom.diagToggle.addEventListener("click", () => {
    setDrawerOpen(dom.drawer.hidden);
  });

  // Viewport background click clears selection
  let suppressViewportClick = false;
  dom.viewport.addEventListener("click", () => {
    if (suppressViewportClick) {
      suppressViewportClick = false;
      return;
    }
    if (st.selectedId || st.selectedBundleKey || st.compareTargetId) {
      st.selectedId = null;
      st.selectedBundleKey = null;
      st.compareTargetId = null;
      renderAll();
    }
  });

  // Drag-to-pan & Ctrl/Cmd+Wheel zoom
  let panState = null;
  dom.viewport.addEventListener("mousedown", (ev) => {
    if (ev.target.closest(".block") || ev.target.closest(".count")) return;
    panState = {
      startX: ev.clientX,
      startY: ev.clientY,
      scrollLeft: dom.viewport.scrollLeft,
      scrollTop: dom.viewport.scrollTop,
      moved: false
    };
    dom.viewport.classList.add("panning");
  });
  window.addEventListener("mousemove", (ev) => {
    if (!panState) return;
    if (Math.hypot(ev.clientX - panState.startX, ev.clientY - panState.startY) > 4) panState.moved = true;
    dom.viewport.scrollLeft = panState.scrollLeft - (ev.clientX - panState.startX);
    dom.viewport.scrollTop = panState.scrollTop - (ev.clientY - panState.startY);
  });
  window.addEventListener("mouseup", () => {
    if (panState) {
      // The click that follows a drag must not clear the selection. The flag is
      // reset on the next task in case no click reaches the viewport.
      if (panState.moved) {
        suppressViewportClick = true;
        setTimeout(() => {
          suppressViewportClick = false;
        }, 0);
      }
      panState = null;
      dom.viewport.classList.remove("panning");
    }
  });

  dom.viewport.addEventListener("wheel", (ev) => {
    if (ev.ctrlKey || ev.metaKey) {
      ev.preventDefault();
      const cur = st.zoom ?? st.scale;
      const delta = ev.deltaY < 0 ? 0.1 : -0.1;
      st.zoom = Math.max(0.3, Math.min(2.2, +(cur + delta).toFixed(2)));
      if (st.currentLayout) applyScale(st.currentLayout);
    }
  }, { passive: false });

  // Live Instant Search
  dom.searchInput.addEventListener("input", () => {
    const q = dom.searchInput.value.trim().toLowerCase();
    dom.searchResults.replaceChildren();
    if (!q) {
      setSearchOpen(false);
      return;
    }
    const ds = curDs();
    const hits = [];
    for (const n of ds.nodes) {
      if (n.id === ds.rootId) continue;
      const hay = `${n.title} ${n.id} ${n.kind} ${n.summary || ""} ${(n.tags || []).join(" ")}`.toLowerCase();
      if (hay.includes(q)) hits.push({ type: "node", item: n });
      if (hits.length >= 18) break;
    }
    for (const ov of ds.overlays) {
      if (hits.length >= 24) break;
      const hay = `${ov.title} ${ov.id} ${ov.summary || ""}`.toLowerCase();
      if (hay.includes(q)) hits.push({ type: "slice", item: ov });
    }
    if (!hits.length) {
      const li = h("li", "r-item", "No matching blocks or slices.");
      dom.searchResults.appendChild(li);
      setSearchOpen(true);
      return;
    }
    for (const hit of hits) {
      const li = h("li", "r-item");
      const top = h("div", "r-top");
      top.appendChild(h("span", "tag", hit.type === "slice" ? `◆ ${hit.item.kind}` : hit.item.kind));
      top.appendChild(h("span", "r-title", hit.item.title));
      top.appendChild(h("span", "r-id", hit.item.id));
      li.appendChild(top);
      if (hit.item.summary) li.appendChild(h("div", "r-sum", hit.item.summary));
      li.addEventListener("click", () => {
        setSearchOpen(false);
        dom.searchInput.value = "";
        if (hit.type === "node") {
          jumpToNode(ds, hit.item.id);
        } else {
          st.focusId = ds.rootId;
          setSelection(sliceBoxId(hit.item.id));
          renderAll();
        }
      });
      dom.searchResults.appendChild(li);
    }
    setSearchOpen(true);
  });

  document.addEventListener("click", (ev) => {
    if (dom.searchResults.hidden) return;
    if (ev.target === dom.searchInput || dom.searchResults.contains(ev.target)) return;
    setSearchOpen(false);
  });

  // Keyboard shortcuts
  window.addEventListener("keydown", (ev) => {
    if (ev.key === "Escape" && !dom.searchResults.hidden) {
      setSearchOpen(false);
      if (ev.target === dom.searchInput) dom.searchInput.blur();
      return;
    }
    if (ev.target === dom.searchInput) return;
    if (ev.key === "/") {
      ev.preventDefault();
      dom.searchInput.focus();
    } else if (ev.key === "Escape") {
      if (!dom.drawer.hidden) {
        setDrawerOpen(false);
      } else if (st.compareTargetId) {
        st.compareTargetId = null;
        renderAll();
      } else if (st.selectedId || st.selectedBundleKey) {
        st.selectedId = null;
        st.selectedBundleKey = null;
        renderAll();
      } else {
        const ds = curDs();
        const chain = ancestorChain(ds, st.focusId);
        if (chain.length > 1) {
          st.focusId = chain[chain.length - 2].id;
          st.zoom = null;
          renderAll();
        }
      }
    } else if (ev.key === "[") {
      stepTrace(-1);
    } else if (ev.key === "]") {
      stepTrace(1);
    } else if (ev.key === "0") {
      st.zoom = null;
      if (st.currentLayout) applyScale(st.currentLayout);
    } else if (!ev.ctrlKey && !ev.metaKey && !ev.altKey) {
      if (ev.key === "+" || ev.key === "=") stepZoom(0.15);
      else if (ev.key === "-") stepZoom(-0.15);
    }
  });

  window.addEventListener("resize", () => {
    if (st.currentLayout && st.zoom === null) applyScale(st.currentLayout);
  });

  /* ---------------------------------------------------- Master Render Loop */
  function renderAll() {
    hideTip();
    st.hoverId = null;
    st.hoverBundleKey = null;
    const ds = curDs();
    const level = buildLevelModel(ds);
    const lay = computeLayout(ds, level, dom.viewport.clientWidth || 1100);
    st.currentLevel = level;
    st.currentLayout = lay;
    const hlInfo = computeHighlightSets(ds, level, lay);

    renderHubTabs();
    renderTopBar(ds, level);
    renderLevelHead(ds, level);
    renderLegend(ds, level);
    renderTraceBar(ds, level);
    renderPathBanner(ds, level, hlInfo);
    renderCanvas(ds, level, lay, hlInfo);
    renderInspector(ds, level, lay);
    renderDiagnosticsDrawer(ds);
  }

  renderAll();
})();
