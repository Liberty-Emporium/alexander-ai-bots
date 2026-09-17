<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__ - Graph</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  html, body { margin: 0; height: 100%; background: #041027; color: #eaf2ff;
    font: 16px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; overflow: hidden; }
  #bar {
    position: fixed; inset: 0 0 auto 0; display: flex; align-items: center; gap: 12px;
    padding: 10px 14px; background: #061530ee; border-bottom: 1px solid #173464; z-index: 5;
  }
  #bar a.back {
    padding: 8px 14px; border: 1px solid #2b5390; border-radius: 10px; background: #0b1f42cc;
    color: #cfe6ff; text-decoration: none; font-weight: 700; font-size: 14px; white-space: nowrap;
  }
  #bar a.back:hover { background: #12305e; }
  #title { font-weight: 700; font-size: 15px; color: #ffd479; white-space: nowrap; }
  #search {
    margin-left: auto; padding: 8px 12px; border-radius: 10px; border: 1px solid #2b5390;
    background: #081c3c; color: #eaf2ff; font-size: 14px; width: 220px;
  }
  #count { font-size: 13px; color: #9fb6d9; white-space: nowrap; }
  canvas { position: fixed; inset: 0; display: block; cursor: grab; }
  canvas.dragging { cursor: grabbing; }
  #hint {
    position: fixed; left: 14px; bottom: 12px; font-size: 13px; color: #7d94b8; z-index: 5;
  }
  #tip {
    position: fixed; pointer-events: none; z-index: 6; padding: 6px 10px; border-radius: 9px;
    background: #0b1f42f2; border: 1px solid #2b5390; font-size: 14px; color: #eaf2ff;
    display: none; max-width: 320px;
  }
</style>
</head>
<body>
<div id="bar">
  <a class="back" href="__APP_URL__">&#8592; Back to __NAME__</a>
  <a class="back" href="__VAULT_URL__">Notes</a>
  <span id="title">Obsidian Graph</span>
  <input id="search" placeholder="Filter notes..." autocomplete="off">
  <span id="count"></span>
</div>
<canvas id="cv"></canvas>
<div id="hint">drag a dot &middot; scroll to zoom &middot; drag background to pan &middot; click a dot to open its note</div>
<div id="tip"></div>
<script>
const GRAPH = __GRAPH_JSON__;
const VAULT_URL = "__VAULT_URL__";

const canvas = document.getElementById('cv');
const ctx = canvas.getContext('2d');
const tip = document.getElementById('tip');
let W = 0, H = 0, DPR = Math.min(window.devicePixelRatio || 1, 2);

function resize() {
  W = window.innerWidth; H = window.innerHeight;
  canvas.width = W * DPR; canvas.height = H * DPR;
  canvas.style.width = W + 'px'; canvas.style.height = H + 'px';
  ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
}
window.addEventListener('resize', resize); resize();

// nodes and links
const nodes = GRAPH.nodes.map((n, i) => ({
  ...n, i,
  x: (Math.random() - 0.5) * Math.min(W, 900),
  y: (Math.random() - 0.5) * Math.min(H, 700),
  vx: 0, vy: 0,
}));
const byId = new Map(nodes.map(n => [n.id, n]));
const links = GRAPH.links
  .map(l => ({ s: byId.get(l.source), t: byId.get(l.target) }))
  .filter(l => l.s && l.t);
nodes.forEach(n => { n.deg = 0; });
links.forEach(l => { l.s.deg++; l.t.deg++; });

const view = { x: 0, y: 0, k: 1 };
let hover = null, dragNode = null, panning = false, last = null, filter = '';

function toWorld(px, py) { return { x: (px - W / 2) / view.k - view.x, y: (py - H / 2) / view.k - view.y }; }
function toScreen(x, y) { return { x: (x + view.x) * view.k + W / 2, y: (y + view.y) * view.k + H / 2 }; }

// ---- force simulation ----
function tick() {
  const k = 0.06;
  // repulsion
  for (let i = 0; i < nodes.length; i++) {
    const a = nodes[i];
    for (let j = i + 1; j < nodes.length; j++) {
      const b = nodes[j];
      let dx = b.x - a.x, dy = b.y - a.y;
      let d2 = dx * dx + dy * dy;
      if (d2 < 1) { dx = Math.random() - 0.5; dy = Math.random() - 0.5; d2 = 1; }
      const d = Math.sqrt(d2);
      const rep = 2600 / d2;
      const fx = (dx / d) * rep, fy = (dy / d) * rep;
      a.vx -= fx; a.vy -= fy; b.vx += fx; b.vy += fy;
    }
  }
  // springs
  for (const l of links) {
    const dx = l.t.x - l.s.x, dy = l.t.y - l.s.y;
    const d = Math.max(Math.sqrt(dx * dx + dy * dy), 1);
    const target = 110;
    const f = (d - target) * 0.02;
    const fx = (dx / d) * f, fy = (dy / d) * f;
    l.s.vx += fx; l.s.vy += fy; l.t.vx -= fx; l.t.vy -= fy;
  }
  // gravity to centre
  for (const n of nodes) {
    n.vx += -n.x * 0.004;
    n.vy += -n.y * 0.004;
    n.vx *= 0.85; n.vy *= 0.85;
    n.x += n.vx * k * 10;
    n.y += n.vy * k * 10;
  }
}

function radius(n) { return 5 + Math.min(n.deg, 12) * 1.7; }

function draw() {
  ctx.clearRect(0, 0, W, H);
  ctx.save();
  ctx.translate(W / 2, H / 2);
  ctx.scale(view.k, view.k);
  ctx.translate(view.x, view.y);

  // links
  for (const l of links) {
    const dim = filter && !match(l.s) && !match(l.t);
    ctx.strokeStyle = dim ? 'rgba(120,160,220,.08)' : 'rgba(150,190,255,.30)';
    ctx.lineWidth = 1 / view.k;
    ctx.beginPath();
    ctx.moveTo(l.s.x, l.s.y);
    ctx.lineTo(l.t.x, l.t.y);
    ctx.stroke();
  }

  // nodes
  for (const n of nodes) {
    const dim = filter && !match(n);
    const r = radius(n);
    const isHover = hover === n || (hover && links.some(l => (l.s === hover && l.t === n) || (l.t === hover && l.s === n)));
    ctx.beginPath();
    ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
    ctx.fillStyle = dim ? 'rgba(90,120,170,.25)' : (isHover ? '#ffd479' : n.color);
    ctx.fill();
    ctx.lineWidth = 1.2 / view.k;
    ctx.strokeStyle = 'rgba(10,26,52,.9)';
    ctx.stroke();

    if (!dim && (n.deg > 0 || hover === n || view.k > 1.1)) {
      ctx.font = `${13 / view.k}px system-ui, sans-serif`;
      ctx.fillStyle = hover === n ? '#ffd479' : 'rgba(226,238,255,.92)';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      ctx.fillText(n.label, n.x, n.y + r + 3 / view.k);
    }
  }
  ctx.restore();
}

function match(n) { return !filter || n.label.toLowerCase().includes(filter); }

function loop() { tick(); draw(); requestAnimationFrame(loop); }
loop();

// ---- interaction ----
function pick(px, py) {
  const w = toWorld(px, py);
  let best = null, bestD = Infinity;
  for (const n of nodes) {
    const dx = n.x - w.x, dy = n.y - w.y;
    const d2 = dx * dx + dy * dy;
    const r = radius(n) + 6 / view.k;
    if (d2 < r * r && d2 < bestD) { best = n; bestD = d2; }
  }
  return best;
}

canvas.addEventListener('wheel', (e) => {
  e.preventDefault();
  const before = toWorld(e.clientX, e.clientY);
  view.k *= e.deltaY < 0 ? 1.12 : 1 / 1.12;
  view.k = Math.max(0.25, Math.min(4, view.k));
  const after = toWorld(e.clientX, e.clientY);
  view.x += after.x - before.x;
  view.y += after.y - before.y;
}, { passive: false });

canvas.addEventListener('mousedown', (e) => {
  const n = pick(e.clientX, e.clientY);
  if (n) { dragNode = n; canvas.classList.add('dragging'); }
  else { panning = true; last = { x: e.clientX, y: e.clientY }; canvas.classList.add('dragging'); }
});

canvas.addEventListener('mousemove', (e) => {
  if (dragNode) {
    const w = toWorld(e.clientX, e.clientY);
    dragNode.x = w.x; dragNode.y = w.y; dragNode.vx = 0; dragNode.vy = 0;
    return;
  }
  if (panning && last) {
    view.x += (e.clientX - last.x) / view.k;
    view.y += (e.clientY - last.y) / view.k;
    last = { x: e.clientX, y: e.clientY };
    return;
  }
  const n = pick(e.clientX, e.clientY);
  if (n !== hover) hover = n;
  if (n) {
    tip.style.display = 'block';
    tip.textContent = n.label + '  (' + n.deg + (n.deg === 1 ? ' link' : ' links') + ')';
    const tw = tip.offsetWidth;
    tip.style.left = Math.min(e.clientX + 14, W - tw - 10) + 'px';
    tip.style.top = (e.clientY + 14) + 'px';
  } else {
    tip.style.display = 'none';
  }
});

window.addEventListener('mouseup', (e) => {
  if (dragNode) {
    const moved = Math.hypot(dragNode.x - toWorld(e.clientX, e.clientY).x, dragNode.y - toWorld(e.clientX, e.clientY).y);
    const n = dragNode;
    dragNode = null; canvas.classList.remove('dragging');
    if (moved < 2 && n.anchor) window.location.href = VAULT_URL + n.anchor;
    return;
  }
  panning = false; last = null; canvas.classList.remove('dragging');
});

document.getElementById('search').addEventListener('input', (e) => {
  filter = e.target.value.trim().toLowerCase();
});
document.getElementById('count').textContent = nodes.length + ' notes, ' + links.length + ' links';
</script>
</body>
</html>