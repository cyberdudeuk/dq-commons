/* Commons diagrams: plain-English, accessible SVG diagrams with no dependencies.
 * - DQD.constellation: a two-axis map in the style of a Morgan Map (automation against criticality to trust),
 *   with linked elements forming a "constellation".
 * - DQD.flow: a left-to-right flow with optional swimlanes, in the spirit of Mermaid flowcharts.
 * - DQD.columns: grouped boxes with relationship lines (for entity relationships and lineage).
 * Every diagram: focusable elements with names, shapes as well as colours, a details panel, a list view for
 * screen readers and small screens, theme colours from CSS variables, and no motion if reduced motion is set.
 */
(function () {
  var NS = "http://www.w3.org/2000/svg", D = {};
  var esc = function (s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]; }); };
  function el(tag, attrs, parent) {
    var e = document.createElementNS(NS, tag);
    Object.keys(attrs || {}).forEach(function (k) { e.setAttribute(k, attrs[k]); });
    if (parent) parent.appendChild(e);
    return e;
  }
  function wrap(text, max) {
    var words = String(text).split(/\s+/), lines = [], cur = "";
    words.forEach(function (w) { if ((cur + " " + w).trim().length > max && cur) { lines.push(cur); cur = w; } else cur = (cur + " " + w).trim(); });
    if (cur) lines.push(cur);
    if (lines.length > 3) { lines = lines.slice(0, 3); lines[2] = lines[2].replace(/.{0,2}$/, "…"); }
    return lines;
  }
  function label(g, x, y, text, max, cls, anchor) {
    var t = el("text", {x: x, y: y, "class": cls || "dqd-lbl", "text-anchor": anchor || "middle"}, g);
    wrap(text, max).forEach(function (line, i) { var s = el("tspan", {x: x, dy: i ? "1.15em" : "0"}, t); s.textContent = line; });
    return t;
  }
  // Shapes say what kind of thing a node is, so colour is never the only cue.
  function shape(g, kind, x, y, r) {
    if (kind === "diamond") return el("path", {d: "M" + x + " " + (y - r) + " L" + (x + r) + " " + y + " L" + x + " " + (y + r) + " L" + (x - r) + " " + y + " Z", "class": "dqd-shape"}, g);
    if (kind === "square") return el("rect", {x: x - r * .85, y: y - r * .85, width: r * 1.7, height: r * 1.7, rx: 4, "class": "dqd-shape"}, g);
    if (kind === "hex") { var p = []; for (var i = 0; i < 6; i++) { var a = Math.PI / 3 * i; p.push((x + r * Math.cos(a)).toFixed(1) + " " + (y + r * Math.sin(a)).toFixed(1)); } return el("path", {d: "M" + p.join(" L") + " Z", "class": "dqd-shape"}, g); }
    return el("circle", {cx: x, cy: y, r: r, "class": "dqd-shape"}, g);
  }
  function curve(a, b, bend) {
    var mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2, dx = b[0] - a[0], dy = b[1] - a[1];
    var cx = mx - dy * (bend || 0.15), cy = my + dx * (bend || 0.15);
    return "M" + a[0].toFixed(1) + " " + a[1].toFixed(1) + " Q" + cx.toFixed(1) + " " + cy.toFixed(1) + " " + b[0].toFixed(1) + " " + b[1].toFixed(1);
  }
  function defs(svg, id) {
    var d = el("defs", {}, svg), m = el("marker", {id: id, viewBox: "0 0 10 10", refX: "9", refY: "5", markerWidth: "7", markerHeight: "7", orient: "auto-start-reverse"}, d);
    el("path", {d: "M0 0 L10 5 L0 10 z", "class": "dqd-arrow"}, m);
  }
  // Shared behaviour: select a node, highlight its links, fill the panel, keep the list in step.
  function interact(root, svg, nodes, links, panel, onSelect) {
    var byId = {}; nodes.forEach(function (n) { byId[n.id] = n; });
    function select(id) {
      svg.classList.toggle("dqd-focus", !!id);
      svg.querySelectorAll(".dqd-node").forEach(function (g) {
        var on = g.dataset.id === id, near = links.some(function (l) { return (l.from === id && l.to === g.dataset.id) || (l.to === id && l.from === g.dataset.id); });
        g.classList.toggle("on", on); g.classList.toggle("near", near); g.setAttribute("aria-pressed", on ? "true" : "false");
      });
      svg.querySelectorAll(".dqd-link").forEach(function (p) { p.classList.toggle("on", p.dataset.from === id || p.dataset.to === id); });
      if (!panel) return;
      if (!id) { panel.innerHTML = panel.dataset.empty || ""; return; }
      var n = byId[id], out = links.filter(function (l) { return l.from === id; }), inn = links.filter(function (l) { return l.to === id; });
      var li = function (l, other) { return "<li>" + (l.label ? esc(l.label) + ": " : "") + '<button type="button" class="dqd-jump" data-go="' + esc(other) + '">' + esc(byId[other] ? byId[other].label : other) + "</button></li>"; };
      panel.innerHTML = "<h3>" + esc(n.label) + "</h3>" + (n.tag ? '<p class="small"><b>' + esc(n.tag) + "</b></p>" : "") + (n.desc ? "<p>" + n.desc + "</p>" : "") +
        (inn.length ? '<p class="small"><b>Comes from</b></p><ul class="small">' + inn.map(function (l) { return li(l, l.from); }).join("") + "</ul>" : "") +
        (out.length ? '<p class="small"><b>Leads to</b></p><ul class="small">' + out.map(function (l) { return li(l, l.to); }).join("") + "</ul>" : "") +
        (n.href ? '<p><a class="btn ghost" href="' + esc(n.href) + '">' + esc(n.hrefText || "Open") + "</a></p>" : "");
      if (onSelect) onSelect(n);
    }
    root.addEventListener("click", function (e) {
      var j = e.target.closest(".dqd-jump"); if (j) { select(j.dataset.go); var t = svg.querySelector('.dqd-node[data-id="' + j.dataset.go + '"]'); if (t) t.focus(); return; }
      var g = e.target.closest(".dqd-node"); if (g) select(g.classList.contains("on") ? null : g.dataset.id);
    });
    root.addEventListener("keydown", function (e) {
      var g = e.target.closest && e.target.closest(".dqd-node"); if (!g) { if (e.key === "Escape") select(null); return; }
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); select(g.classList.contains("on") ? null : g.dataset.id); }
      if (e.key === "Escape") select(null);
    });
    if (panel) panel.innerHTML = panel.dataset.empty || "";
    return select;
  }
  function nodeGroup(svg, n, name) {
    var g = el("g", {"class": "dqd-node k-" + (n.cls || n.kind || "x"), tabindex: "0", role: "button", "data-id": n.id, "aria-pressed": "false", "aria-label": name}, svg);
    return g;
  }
  function listView(host, nodes, links, heading) {
    if (!host) return;
    var by = {}; nodes.forEach(function (n) { by[n.id] = n; });
    host.innerHTML = (heading ? "<p class=\"small\">" + esc(heading) + "</p>" : "") + "<ul class=\"dqd-list\">" + nodes.map(function (n) {
      var out = links.filter(function (l) { return l.from === n.id; }).map(function (l) { return (l.label ? esc(l.label) + " → " : "→ ") + esc(by[l.to] ? by[l.to].label : l.to); });
      return "<li><b>" + (n.href ? '<a href="' + esc(n.href) + '">' + esc(n.label) + "</a>" : esc(n.label)) + "</b>" + (n.tag ? " <span class=\"small muted\">(" + esc(n.tag) + ")</span>" : "") + (out.length ? "<br><span class=\"small\">" + out.join("; ") + "</span>" : "") + "</li>";
    }).join("") + "</ul>";
  }

  /* Constellation: opts {xAxis:[low, high, title], yAxis:[low, high, title], quadrants:[tl, tr, bl, br],
     nodes:[{id,label,x(0-1),y(0-1),kind:'circle'|'square'|'diamond'|'hex',cls,tag,desc,href}], links:[{from,to,label}],
     panel: element, list: element } */
  D.constellation = function (host, o) {
    host.innerHTML = "";
    var W = 1000, H = 640, L = 90, R = 30, T = 30, B = 80, pw = W - L - R, ph = H - T - B;
    var svg = el("svg", {viewBox: "0 0 " + W + " " + H, "class": "dqd dqd-const", role: "group", "aria-label": o.title || "Map"}, host);
    defs(svg, "ah-" + (host.id || "c"));
    var X = function (v) { return L + v * pw; }, Y = function (v) { return T + (1 - v) * ph; };
    [[0, .5, 0, .5], [.5, 1, 0, .5], [0, .5, .5, 1], [.5, 1, .5, 1]].forEach(function (q, i) {
      el("rect", {x: X(q[0]), y: Y(q[3]), width: (q[1] - q[0]) * pw, height: (q[3] - q[2]) * ph, "class": "dqd-quad q" + i}, svg);
    });
    (o.quadrants || []).forEach(function (t, i) {
      var qx = i % 2 ? X(.75) : X(.25), qy = i < 2 ? Y(.97) : Y(.04);
      label(svg, qx, qy, t, 44, "dqd-quadlbl");
    });
    el("line", {x1: X(0), y1: Y(0), x2: X(1), y2: Y(0), "class": "dqd-axis"}, svg);
    el("line", {x1: X(0), y1: Y(0), x2: X(0), y2: Y(1), "class": "dqd-axis"}, svg);
    label(svg, X(0), Y(0) + 26, o.xAxis[0], 30, "dqd-ax", "start");
    label(svg, X(1), Y(0) + 26, o.xAxis[1], 30, "dqd-ax", "end");
    label(svg, X(.5), Y(0) + 56, o.xAxis[2], 60, "dqd-axt");
    var yt = el("text", {x: 26, y: Y(.5), "class": "dqd-axt", transform: "rotate(-90 26 " + Y(.5) + ")", "text-anchor": "middle"}, svg); yt.textContent = o.yAxis[2];
    var yl = el("text", {x: 52, y: Y(0), "class": "dqd-ax", transform: "rotate(-90 52 " + Y(0) + ")", "text-anchor": "start"}, svg); yl.textContent = o.yAxis[0];
    var yh = el("text", {x: 52, y: Y(1), "class": "dqd-ax", transform: "rotate(-90 52 " + Y(1) + ")", "text-anchor": "end"}, svg); yh.textContent = o.yAxis[1];
    var pos = {}; o.nodes.forEach(function (n) { pos[n.id] = [X(n.x), Y(n.y)]; });
    // Keep points and their labels apart: nudge any pair closer than the label box, within the plot.
    var ids = o.nodes.map(function (n) { return n.id; }), MX = 120, MY = 58;
    for (var it = 0; it < 80; it++) {
      var moved = false;
      for (var i = 0; i < ids.length; i++) for (var j = i + 1; j < ids.length; j++) {
        var a = pos[ids[i]], b = pos[ids[j]], dx = b[0] - a[0], dy = b[1] - a[1];
        if (Math.abs(dx) < MX && Math.abs(dy) < MY) {
          var px = (MX - Math.abs(dx)) / 2 + .5, py = (MY - Math.abs(dy)) / 2 + .5, sx = dx >= 0 ? 1 : -1, sy = dy >= 0 ? 1 : -1;
          if (px / MX < py / MY) { a[0] -= sx * px * .5; b[0] += sx * px * .5; } else { a[1] -= sy * py * .5; b[1] += sy * py * .5; }
          moved = true;
        }
      }
      ids.forEach(function (id) { var p = pos[id]; p[0] = Math.min(X(1) - 40, Math.max(X(0) + 40, p[0])); p[1] = Math.min(Y(0) - 40, Math.max(Y(1) + 26, p[1])); });
      if (!moved) break;
    }
    var lg = el("g", {"class": "dqd-links"}, svg);
    o.links.forEach(function (l) {
      if (!pos[l.from] || !pos[l.to]) return;
      el("path", {d: curve(pos[l.from], pos[l.to], .12), "class": "dqd-link", "data-from": l.from, "data-to": l.to, "marker-end": "url(#ah-" + (host.id || "c") + ")"}, lg);
    });
    o.nodes.forEach(function (n) {
      var g = nodeGroup(svg, n, n.label + (n.tag ? ", " + n.tag : "")), p = pos[n.id];
      el("rect", {x: p[0] - 70, y: p[1] - 18, width: 140, height: 72, "class": "dqd-hit"}, g);
      shape(g, n.kind, p[0], p[1], 14);
      label(g, p[0], p[1] + 30, n.short || n.label, 22, "dqd-lbl");
    });
    listView(o.list, o.nodes, o.links, o.listHeading);
    return interact(host, svg, o.nodes, o.links, o.panel, o.onSelect);
  };

  /* Flow: opts {lanes:[names] (optional), nodes:[{id,label,kind,lane,tag,desc,href}], links:[{from,to,label}]} */
  D.flow = function (host, o) {
    host.innerHTML = "";
    var nodes = o.nodes, links = o.links, byId = {}, layer = {}, order = [];
    nodes.forEach(function (n) { byId[n.id] = n; });
    // Layer = longest path from a start, ignoring links that go backwards (loops).
    var seen = {}, stack = {};
    function visit(id) { if (seen[id]) return; seen[id] = stack[id] = true; links.forEach(function (l) { if (l.from === id && !stack[l.to]) visit(l.to); else if (l.from === id) l.back = true; }); stack[id] = false; order.unshift(id); }
    nodes.forEach(function (n) { visit(n.id); });
    order.forEach(function (id) { layer[id] = layer[id] || 0; links.forEach(function (l) { if (l.from === id && !l.back) layer[l.to] = Math.max(layer[l.to] || 0, layer[id] + 1); }); });
    var lanes = o.lanes && o.lanes.length ? o.lanes : [""], laneOf = function (n) { var i = lanes.indexOf(n.lane); return i < 0 ? 0 : i; };
    var cols = 0; nodes.forEach(function (n) { cols = Math.max(cols, layer[n.id] + 1); });
    // Nodes sharing a lane and layer are stacked.
    var slot = {}, used = {};
    nodes.forEach(function (n) { var k = laneOf(n) + ":" + layer[n.id]; slot[n.id] = used[k] = (used[k] === undefined ? 0 : used[k] + 1); });
    var perLane = lanes.map(function (_, i) { var m = 0; Object.keys(used).forEach(function (k) { if (+k.split(":")[0] === i) m = Math.max(m, used[k] + 1); }); return Math.max(m, 1); });
    var LW = lanes[0] ? 140 : 20, CW = 172, RH = 100, W = LW + cols * CW + 20, top = [], y = 10;
    perLane.forEach(function (m) { top.push(y); y += m * RH; });
    var H = y + 10, svg = el("svg", {viewBox: "0 0 " + W + " " + H, width: W, "class": "dqd dqd-flow", role: "group", "aria-label": o.title || "Flow"}, host);
    defs(svg, "fa-" + (host.id || "f"));
    lanes.forEach(function (ln, i) {
      el("rect", {x: 0, y: top[i], width: W, height: perLane[i] * RH, "class": "dqd-lane l" + (i % 2)}, svg);
      if (ln) label(svg, 12, top[i] + 24, ln, 16, "dqd-lanelbl", "start");
    });
    var pos = {}; nodes.forEach(function (n) { pos[n.id] = [LW + layer[n.id] * CW + CW / 2, top[laneOf(n)] + slot[n.id] * RH + RH / 2 - 8]; });
    var lg = el("g", {"class": "dqd-links"}, svg);
    links.forEach(function (l) {
      var a = pos[l.from], b = pos[l.to]; if (!a || !b) return;
      var d = l.back ? "M" + a[0] + " " + (a[1] + 22) + " C" + a[0] + " " + (H - 4) + " " + b[0] + " " + (H - 4) + " " + b[0] + " " + (b[1] + 22)
        : "M" + (a[0] + 62) + " " + a[1] + " C" + (a[0] + 95) + " " + a[1] + " " + (b[0] - 95) + " " + b[1] + " " + (b[0] - 64) + " " + b[1];
      el("path", {d: d, "class": "dqd-link" + (l.back ? " back" : ""), "data-from": l.from, "data-to": l.to, "marker-end": "url(#fa-" + (host.id || "f") + ")"}, lg);
      if (l.label) { var t = el("text", {x: (a[0] + b[0]) / 2 + 10, y: (a[1] + b[1]) / 2 - 6, "class": "dqd-elbl", "text-anchor": "middle"}, lg); t.textContent = l.label; }
    });
    nodes.forEach(function (n) {
      var g = nodeGroup(svg, n, n.label + (n.tag ? ", " + n.tag : "")), p = pos[n.id];
      if (n.kind === "diamond") shape(g, "diamond", p[0], p[1], 34);
      else if (n.kind === "circle") el("rect", {x: p[0] - 60, y: p[1] - 26, width: 120, height: 52, rx: 26, "class": "dqd-shape"}, g);
      else el("rect", {x: p[0] - 62, y: p[1] - 30, width: 124, height: 60, rx: n.kind === "square" ? 4 : 12, "class": "dqd-shape"}, g);
      label(g, p[0], p[1] - (wrap(n.label, n.kind === "diamond" ? 12 : 18).length - 1) * 7 + 4, n.label, n.kind === "diamond" ? 12 : 18, "dqd-lbl");
    });
    listView(o.list, nodes, links, o.listHeading);
    return interact(host, svg, nodes, links, o.panel, o.onSelect);
  };

  /* Columns: grouped boxes with relationship lines. opts {groups:[names], nodes:[{id,label,group,tag,desc,href}], links:[{from,to,label}]} */
  D.columns = function (host, o) {
    host.innerHTML = "";
    var groups = o.groups, CW = 210, BH = 46, GAP = 12, TOP = 44, cols = {};
    groups.forEach(function (g) { cols[g] = []; });
    o.nodes.forEach(function (n) { (cols[n.group] || (cols[n.group] = [])).push(n); });
    var maxRows = 0; groups.forEach(function (g) { maxRows = Math.max(maxRows, cols[g].length); });
    var W = groups.length * CW + 20, H = TOP + maxRows * (BH + GAP) + 20;
    var svg = el("svg", {viewBox: "0 0 " + W + " " + H, width: W, "class": "dqd dqd-cols", role: "group", "aria-label": o.title || "Relationships"}, host);
    defs(svg, "ca-" + (host.id || "k"));
    var pos = {};
    groups.forEach(function (g, i) {
      var x = 10 + i * CW;
      el("rect", {x: x + 6, y: 6, width: CW - 12, height: H - 12, rx: 12, "class": "dqd-colbg c" + (i % 6)}, svg);
      label(svg, x + CW / 2, 30, g, 24, "dqd-colttl");
      cols[g].forEach(function (n, j) { pos[n.id] = [x + CW / 2, TOP + j * (BH + GAP) + BH / 2]; });
    });
    var lg = el("g", {"class": "dqd-links"}, svg);
    o.links.forEach(function (l) {
      var a = pos[l.from], b = pos[l.to]; if (!a || !b) return;
      var sx = a[0] < b[0] ? a[0] + 90 : a[0] - 90, ex = a[0] < b[0] ? b[0] - 92 : b[0] + 92;
      if (a[0] === b[0]) { sx = a[0] + 90; ex = b[0] + 92; }
      var bend = a[0] === b[0] ? 60 : 40;
      el("path", {d: "M" + sx + " " + a[1] + " C" + (sx + (sx > a[0] ? bend : -bend)) + " " + a[1] + " " + (ex + (ex > b[0] ? bend : -bend)) + " " + b[1] + " " + ex + " " + b[1],
        "class": "dqd-link", "data-from": l.from, "data-to": l.to, "marker-end": "url(#ca-" + (host.id || "k") + ")"}, lg);
    });
    o.nodes.forEach(function (n) {
      var g = nodeGroup(svg, n, n.label + (n.tag ? ", " + n.tag : "")), p = pos[n.id];
      el("rect", {x: p[0] - 90, y: p[1] - BH / 2, width: 180, height: BH, rx: 10, "class": "dqd-shape"}, g);
      label(g, p[0], p[1] + 5, n.label, 24, "dqd-lbl");
    });
    listView(o.list, o.nodes, o.links, o.listHeading);
    return interact(host, svg, o.nodes, o.links, o.panel, o.onSelect);
  };
  window.DQD = D;
})();
