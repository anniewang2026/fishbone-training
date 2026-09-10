# -*- coding: utf-8 -*-
"""鱼骨图「绘制过程」动画演示页生成器

复用 gen_fishbone.py 的几何数据（每根骨都带步骤号），输出一个可全屏投影的教学演示页：
  · 主骨 → 大骨(60°) → 中骨 → 小骨 → 小小骨，一步一步生长出来
  · 镜头自动跟随当前正在画的部分（可关）
  · 播放/暂停、上下一步、重播、倍速、按大骨跳转

用法: python gen_demo.py
"""
import os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import gen_fishbone as G                                       # noqa: E402

# ---- 案例名（改这里换鱼头） ----
G.HEAD_TEXT = "成型不良"
G.HEAD_SUB = ""

OUT = os.path.join(BASE, "鱼骨图绘制演示.html")


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def build():
    prims, stats, size, diag = G.plan_all()
    W, H = size
    dx, dy = diag["dx"], diag["dy"]
    steps = diag["steps"]
    total = diag["total_steps"]                                # 实际 21

    # ---------- 步骤说明 ----------
    labels = {0: "① 先画主骨（脊骨）：一条水平线，右端是鱼头「成型不良」",
              total: "✅ 完成：4 根大骨 · 16 根中骨 · 103 条小骨 · 18 条小小骨；粉红★=重点要因（待真因验证）"}
    jumps = {0: "主骨"}
    n = 1
    for cat in G.CATS:
        labels[n] = f"画「{cat['name']}」大骨：与主骨成 {G.BONE_DEG:.0f}° 的斜线"
        jumps[n] = cat["name"]
        n += 1
        for gname, gside, items in cat["groups"]:
            labels[n] = (f"{cat['name']} · 中骨「{gname}」"
                         f"（挂在斜线{'外侧' if gside == 'L' else '内侧'}）"
                         f"→ 逐条挂上 {len(items)} 条小骨")
            n += 1
    for k in range(total + 1):
        labels.setdefault(k, "")

    # ---------- 每个步骤的包围盒（用于镜头跟随） ----------
    box = {}
    for p, s in zip(prims, steps):
        if p[0] == "line":
            x1, y1, x2, y2 = p[1], p[2], p[3], p[4]
            b = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
        elif p[0] == "poly":
            xs = [q[0] for q in p[1]]; ys = [q[1] for q in p[1]]
            b = (min(xs), min(ys), max(xs), max(ys))
        elif p[0] == "rect":
            b = (p[1], p[2], p[1] + p[3], p[2] + p[4])
        else:
            _, x, y, txt, f, _c, anchor, _w = p
            tw = G.tw(txt, f)
            x0 = x - (tw / 2 if anchor == "middle" else (0 if anchor == "start" else tw))
            b = (x0, y - f, x0 + tw, y + f * 0.4)
        b = (b[0] + dx, b[1] + dy, b[2] + dx, b[3] + dy)
        if s in box:
            o = box[s]
            box[s] = (min(o[0], b[0]), min(o[1], b[1]), max(o[2], b[2]), max(o[3], b[3]))
        else:
            box[s] = b

    PADB = 70
    boxes = []
    for k in range(total + 1):
        if k == total or k not in box:
            boxes.append([0, 0, W, H])
            continue
        b = box[k]
        x0 = max(0, b[0] - PADB); y0 = max(0, b[1] - PADB)
        x1 = min(W, b[2] + PADB); y1 = min(H, b[3] + PADB)
        boxes.append([round(x0), round(y0), round(x1 - x0), round(y1 - y0)])

    # ---------- 组装 SVG ----------
    o = []
    o.append(f'<svg id="fig" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" '
             f'font-family="Microsoft YaHei,PingFang SC,sans-serif" preserveAspectRatio="xMidYMid meet">')
    o.append('<defs>'
             '<linearGradient id="gB" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7dd3fc"/><stop offset="1" stop-color="#0ea5e9"/></linearGradient>'
             '<linearGradient id="gT" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5eead4"/><stop offset="1" stop-color="#14b8a6"/></linearGradient>'
             '<linearGradient id="gI" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#a5b4fc"/><stop offset="1" stop-color="#6366f1"/></linearGradient>'
             '<linearGradient id="gS" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#94a3b8"/><stop offset="1" stop-color="#475569"/></linearGradient>'
             '<linearGradient id="gHead" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#38bdf8"/><stop offset="1" stop-color="#14b8a6"/></linearGradient>'
             '<linearGradient id="gKey" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fb7185"/><stop offset="1" stop-color="#e11d48"/></linearGradient>'
             '</defs>')
    o.append(f'<rect id="bg" x="0" y="0" width="{W}" height="{H}" fill="#f8fbfd"/>')
    o.append(f'<g transform="translate({dx:.0f},{dy:.0f})">')
    o.append(f'<text class="static" x="{G.PAD}" y="{-dy + 54:.0f}" font-size="34" font-weight="bold" '
             f'fill="#1e3a5f">成型不良　要因分析图</text>')
    o.append(f'<text class="static" x="{G.PAD}" y="{-dy + 92:.0f}" font-size="17" fill="#7b8ba1">'
             f'绘制演示 ｜ 大骨与脊骨成 {G.BONE_DEG:.0f}° ｜ 大骨 → 中骨(水平线，与主骨平行) → 小骨(短刺) → 小小骨 ｜ '
             f'★=重点要因</text>')

    idx_in_step = {}
    for p, s in zip(prims, steps):
        i = idx_in_step.get(s, 0)
        idx_in_step[s] = i + 1
        attrs = f'class="{{cls}}" data-step="{s}" data-i="{i}"'
        if p[0] == "line":
            _, x1, y1, x2, y2, w, c, cap = p
            o.append(f'<line {attrs.format(cls="ln")} x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" '
                     f'stroke="{c}" stroke-width="{w}" stroke-linecap="{cap}"/>')
        elif p[0] == "poly":
            pts = " ".join(f"{q[0]:.0f},{q[1]:.0f}" for q in p[1])
            o.append(f'<polygon {attrs.format(cls="ar")} points="{pts}" fill="{p[2]}"/>')
        elif p[0] == "rect":
            _, x, y, w, h, rx, fill, stroke = p
            st = f' stroke="#fff" stroke-opacity=".65"' if stroke else ""
            o.append(f'<rect {attrs.format(cls="ch")} x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" '
                     f'height="{h:.0f}" rx="{rx}" fill="{fill}"{st}/>')
        else:
            _, x, y, txt, f, c, anchor, weight = p
            o.append(f'<text {attrs.format(cls="tx")} x="{x:.0f}" y="{y:.0f}" font-size="{f}" '
                     f'fill="{c}" text-anchor="{anchor}" font-weight="{weight}">{esc(txt)}</text>')
    o.append('</g></svg>')
    svg = "\n".join(o)

    # ---------- 页面 ----------
    html = TEMPLATE.replace("__SVG__", svg) \
                   .replace("__BOXES__", str(boxes)) \
                   .replace("__LABELS__", str([labels[k] for k in range(total + 1)])) \
                   .replace("__TOTAL__", str(total)) \
                   .replace("__W__", str(W)).replace("__H__", str(H)) \
                   .replace("__JUMPS__", str([[k, v] for k, v in sorted(jumps.items())])) \
                   .replace("__RAWIMG__", "fishbone-source.jpg") \
                   .replace("__STATS__", f"{stats['items']} 条小骨 · {stats['keys']} 条重点 · {stats['kids']} 条小小骨")
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(html)
    return OUT, total, stats, size


TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>鱼骨图绘制演示 · 成型不良要因分析</title>
<style>
  :root{
    --ink:#1e3a5f; --ink2:#4a5c72; --muted:#7b8ba1; --line:#dbe6ef;
    --bg:#eef4f9; --panel:#ffffff; --accent:#0ea5e9; --accent2:#14b8a6;
    --shadow:0 8px 26px -14px rgba(30,58,95,.35), 0 2px 6px -2px rgba(30,58,95,.10);
  }
  *{box-sizing:border-box}
  html,body{margin:0;height:100%}
  body{
    background:radial-gradient(1200px 700px at 15% -10%, #e6f4fb 0%, transparent 60%),
               radial-gradient(1000px 620px at 100% 110%, #e9f8f4 0%, transparent 58%), var(--bg);
    color:var(--ink); font-family:"Microsoft YaHei","PingFang SC",system-ui,sans-serif;
    display:flex; flex-direction:column; height:100vh; overflow:hidden;
    -webkit-font-smoothing:antialiased;
  }

  /* ---------- 顶栏 ---------- */
  header{
    flex:0 0 auto; padding:14px 22px 12px; display:flex; align-items:center; gap:16px;
    background:rgba(255,255,255,.86); backdrop-filter:blur(10px);
    border-bottom:1px solid var(--line); box-shadow:0 2px 10px -8px rgba(30,58,95,.4);
  }
  .brand{display:flex;align-items:center;gap:11px;flex:0 0 auto}
  .brand .dot{width:12px;height:12px;border-radius:4px;background:linear-gradient(135deg,var(--accent),var(--accent2));box-shadow:0 0 0 4px rgba(14,165,233,.14)}
  .brand b{font-size:17px;letter-spacing:.3px}
  .brand small{color:var(--muted);font-size:12.5px;display:block;margin-top:1px}
  .cap{
    flex:1 1 auto; min-width:0; display:flex; align-items:center; gap:12px;
    background:#f3f8fc; border:1px solid #e3edf5; border-radius:14px;
    padding:9px 16px; overflow:hidden;
  }
  .cap .num{
    flex:0 0 auto; font-size:12px; font-weight:700; color:#fff; background:linear-gradient(135deg,var(--accent),var(--accent2));
    border-radius:9px; padding:4px 9px; letter-spacing:.5px;
  }
  .cap .txt{font-size:16.5px; font-weight:600; color:#24476e; white-space:nowrap; overflow:hidden; text-overflow:ellipsis}
  #rawimg{
    flex:0 0 auto; text-decoration:none; font-size:13px; color:var(--ink2);
    border:1px solid var(--line); background:#fff; border-radius:11px; padding:8px 13px; font-weight:600;
    box-shadow:var(--shadow); transition:.18s;
  }
  #rawimg:hover{border-color:#bcd6e8; transform:translateY(-1px)}

  /* ---------- 画布 ---------- */
  #stage{flex:1 1 auto; position:relative; min-height:0; padding:14px 18px 6px}
  #figwrap{
    position:absolute; inset:14px 18px 6px; border-radius:20px; background:#f8fbfd;
    border:1px solid #e4eef6; box-shadow:inset 0 1px 0 #fff, 0 14px 34px -24px rgba(30,58,95,.5);
    overflow:hidden;
  }
  #fig{width:100%;height:100%;display:block}
  #start{
    position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center;
    gap:16px; background:rgba(248,251,253,.92); backdrop-filter:blur(2px); z-index:5; transition:opacity .35s;
  }
  #start h2{margin:0;font-size:26px;letter-spacing:1px}
  #start p{margin:0;color:var(--muted);font-size:14.5px}
  #start.gone{opacity:0;pointer-events:none}
  .gobtn{
    border:none; cursor:pointer; font-family:inherit; font-weight:700; font-size:16px; color:#fff;
    background:linear-gradient(135deg,var(--accent),var(--accent2));
    border-radius:14px; padding:13px 34px; box-shadow:0 12px 26px -12px rgba(14,165,233,.85); transition:.18s;
  }
  .gobtn:hover{transform:translateY(-2px); box-shadow:0 16px 30px -12px rgba(14,165,233,.95)}

  /* ---------- 底栏 ---------- */
  footer{
    flex:0 0 auto; padding:10px 22px 14px; background:rgba(255,255,255,.86); backdrop-filter:blur(10px);
    border-top:1px solid var(--line); display:flex; flex-direction:column; gap:9px;
  }
  .row{display:flex; align-items:center; gap:10px; flex-wrap:wrap}
  button.ctl{
    font-family:inherit; cursor:pointer; border:1px solid var(--line); background:#fff; color:#24476e;
    border-radius:11px; padding:8px 13px; font-size:13.5px; font-weight:600; box-shadow:var(--shadow); transition:.16s;
  }
  button.ctl:hover{border-color:#bcd6e8; transform:translateY(-1px)}
  button.ctl:disabled{opacity:.38; cursor:not-allowed; transform:none}
  button.ctl.main{background:linear-gradient(135deg,var(--accent),var(--accent2)); color:#fff; border-color:transparent; padding:9px 22px}
  .chip{
    font-family:inherit; cursor:pointer; border:1px dashed #c6dbea; background:#f7fbfe; color:#3f6a92;
    border-radius:20px; padding:6px 14px; font-size:13px; font-weight:600; transition:.16s;
  }
  .chip:hover{background:#eaf5fc; border-color:#9fc9e2}
  .chip.now{background:linear-gradient(135deg,#e0f2fe,#ccfbf1); border-style:solid; border-color:#8fd0ea; color:#155e75}
  .sep{width:1px;height:22px;background:var(--line);margin:0 3px}
  .lab{font-size:12.5px;color:var(--muted);font-weight:600}
  select.ctl{padding:8px 10px; border-radius:11px; border:1px solid var(--line); background:#fff;
             font-family:inherit; font-size:13.5px; color:#24476e; font-weight:600; box-shadow:var(--shadow); cursor:pointer}
  .switch{display:flex;align-items:center;gap:7px;font-size:13px;color:var(--ink2);font-weight:600;cursor:pointer;user-select:none}
  .switch input{width:16px;height:16px;accent-color:#0ea5e9;cursor:pointer}
  #bar{flex:1 1 240px; height:7px; border-radius:6px; background:#e5eef5; overflow:hidden; min-width:160px}
  #bar i{display:block; height:100%; width:0; border-radius:6px; background:linear-gradient(90deg,var(--accent),var(--accent2)); transition:width .4s cubic-bezier(.4,0,.2,1)}
  .stat{font-size:12.5px;color:var(--muted)}

  /* ---------- 图元动画 ---------- */
  #fig .ln,#fig .ar,#fig .ch,#fig .tx{transition:opacity .42s ease, transform .42s cubic-bezier(.34,1.3,.5,1), stroke-dashoffset .62s cubic-bezier(.4,0,.2,1)}
  #fig .ar,#fig .ch{transform-box:fill-box; transform-origin:center; opacity:0; transform:scale(.55)}
  #fig .tx{opacity:0; transform:translateY(7px)}
  #fig .ln{opacity:0}
  #fig .ln.on{opacity:1; stroke-dashoffset:0 !important}
  #fig .ar.on,#fig .ch.on{opacity:1; transform:scale(1)}
  #fig .tx.on{opacity:1; transform:translateY(0)}
  #fig .ch.on.key{animation:pop .5s cubic-bezier(.34,1.4,.5,1)}
  @keyframes pop{0%{transform:scale(.55)}60%{transform:scale(1.1)}100%{transform:scale(1)}}
  #fig.finish .ch.key{animation:glow 1.5s ease-in-out infinite alternate}
  @keyframes glow{from{filter:drop-shadow(0 0 0 rgba(225,29,72,0))}to{filter:drop-shadow(0 0 10px rgba(225,29,72,.75))}}
  #fig .static{opacity:1}
</style>
</head>
<body>
<header>
  <div class="brand"><span class="dot"></span><div><b>鱼骨图绘制演示</b><small>成型不良要因分析 · __STATS__</small></div></div>
  <div class="cap"><span class="num" id="capnum">STEP 0</span><span class="txt" id="captxt">点右下角「开始演示」</span></div>
  <a id="rawimg" href="__RAWIMG__" target="_blank" rel="noopener">🖼 原图对照</a>
</header>

<div id="stage">
  <div id="figwrap">
    __SVG__
    <div id="start">
      <h2>鱼骨图是怎么一步步画出来的</h2>
      <p>主骨 → 大骨（60°）→ 中骨（与主骨平行）→ 小骨 → 小小骨，共 __TOTAL__ 步</p>
      <button class="gobtn" id="biggo">▶ 开始演示</button>
    </div>
  </div>
</div>

<footer>
  <div class="row" id="jumprow"></div>
  <div class="row">
    <button class="ctl main" id="play">▶ 播放</button>
    <button class="ctl" id="prev">⏮ 上一步</button>
    <button class="ctl" id="next">⏭ 下一步</button>
    <button class="ctl" id="reset">↺ 重播</button>
    <span class="sep"></span>
    <span class="lab">速度</span>
    <select class="ctl" id="speed">
      <option value="0.5">0.5×</option>
      <option value="1" selected>1×</option>
      <option value="1.6">1.6×</option>
      <option value="2.4">2.4×</option>
    </select>
    <label class="switch"><input type="checkbox" id="follow" checked>镜头跟随</label>
    <span class="sep"></span>
    <div id="bar"><i></i></div>
    <span class="stat" id="stepnum">0 / __TOTAL__</span>
  </div>
</footer>

<script>
const BOXES = __BOXES__;
const LABELS = __LABELS__;
const TOTAL = __TOTAL__;
const JUMPS = __JUMPS__;
const W = __W__, H = __H__;

const svg = document.getElementById('fig');
const els = [...svg.querySelectorAll('[data-step]')];
const byStep = {};
els.forEach(el => { const s = +el.dataset.step; (byStep[s] ||= []).push(el); });

// 线段：设成「一笔画」效果
const LENS = new Map();
els.forEach(el => {
  if (el.tagName === 'line') {
    let L = 100;
    try { L = el.getTotalLength(); } catch (e) {}
    LENS.set(el, L);
    el.style.strokeDasharray = L;
    el.style.strokeDashoffset = L;
  }
});

const STEP_MS = 1150, BONE_MS = 950, SPINE_MS = 1300, END_MS = 1700;
let cur = -1, playing = false, timer = null, speed = 1, follow = true;

function durOf(k){ return (k === 0 ? SPINE_MS : k === TOTAL ? END_MS : (LABELS[k].startsWith('画「') ? BONE_MS : STEP_MS)) / speed; }

function show(el, on, delay){
  el.style.transitionDelay = (on ? delay : 0) + 'ms';
  if (on) {
    if (el.tagName === 'line') el.style.strokeDashoffset = 0;
    el.classList.add('on');
  } else {
    if (el.tagName === 'line') { const L = LENS.get(el) || 100; el.style.strokeDashoffset = L; }
    el.classList.remove('on');
  }
}

function render(k, animate){
  for (let s = 0; s <= TOTAL; s++){
    const list = byStep[s] || [];
    const on = s <= k;
    const stagger = (animate && s === k) ? 55 : 0;
    const instant = (s < k);
    list.forEach((el, i) => show(el, on, instant ? 0 : i * stagger));
  }
  svg.classList.toggle('finish', k >= TOTAL);
  document.getElementById('captxt').textContent = LABELS[k] || '';
  document.getElementById('capnum').textContent = k >= TOTAL ? 'DONE' : 'STEP ' + k;
  document.getElementById('stepnum').textContent = k + ' / ' + TOTAL;
  document.querySelector('#bar i').style.width = (k / TOTAL * 100) + '%';
  document.querySelectorAll('.chip').forEach(c => {
    const s = +c.dataset.step;
    const nx = JUMPS.find(j => j[0] > s);
    c.classList.toggle('now', k >= s && (!nx || k < nx[0]));
  });
  document.getElementById('prev').disabled = k <= 0;
  document.getElementById('next').disabled = k >= TOTAL;
  if (follow) focus(k, animate);
}

// ---- 镜头跟随 ----
let box = [0,0,W,H], anim = null;
function focus(k, animate){
  const b = BOXES[k] || [0,0,W,H];
  // 保持宽高比，避免拉伸
  const ar = W / H, bar = b[2] / b[3];
  let x=b[0], y=b[1], w=b[2], h=b[3];
  if (bar > ar) { const nh = w / ar; y -= (nh - h) / 2; h = nh; }
  else { const nw = h * ar; x -= (nw - w) / 2; w = nw; }
  const target = [x, y, w, h];
  if (!animate) { box = target; svg.setAttribute('viewBox', box.join(' ')); return; }
  if (anim) cancelAnimationFrame(anim);
  const from = box.slice(), t0 = performance.now(), D = 620;
  (function step(t){
    const p = Math.min(1, (t - t0) / D), e = p < .5 ? 2*p*p : 1 - Math.pow(-2*p+2,2)/2;
    box = from.map((v, i) => v + (target[i] - v) * e);
    svg.setAttribute('viewBox', box.join(' '));
    if (p < 1) anim = requestAnimationFrame(step);
  })(t0);
}

// ---- 控制 ----
function goto(k, animate = true){ cur = Math.max(0, Math.min(TOTAL, k)); render(cur, animate); }
function stop(){ playing = false; clearTimeout(timer); document.getElementById('play').textContent = '▶ 播放'; }
function tick(){
  if (cur >= TOTAL) { stop(); return; }
  goto(cur + 1, true);
  timer = setTimeout(tick, durOf(cur));
}
function play(){
  if (playing) { stop(); return; }
  if (cur >= TOTAL) goto(0, false);
  playing = true; document.getElementById('play').textContent = '⏸ 暂停';
  document.getElementById('start').classList.add('gone');
  timer = setTimeout(tick, 260);
}

document.getElementById('play').onclick = play;
document.getElementById('biggo').onclick = play;
document.getElementById('next').onclick = () => { stop(); goto(cur + 1); };
document.getElementById('prev').onclick = () => { stop(); goto(cur - 1); };
document.getElementById('reset').onclick = () => { stop(); goto(0, false); };
document.getElementById('speed').onchange = e => speed = +e.target.value;
document.getElementById('follow').onchange = e => { follow = e.target.checked; if (follow) focus(cur, true); };
window.addEventListener('keydown', e => {
  if (e.key === ' ' || e.key === 'ArrowRight') { e.preventDefault(); stop(); goto(cur + 1); }
  if (e.key === 'ArrowLeft') { stop(); goto(cur - 1); }
  if (e.key === 'Enter') play();
});

// 跳转按钮
const jr = document.getElementById('jumprow');
jr.insertAdjacentHTML('beforeend', '<span class="lab">跳到：</span>');
JUMPS.forEach(([k, name]) => {
  const b = document.createElement('button');
  b.className = 'chip'; b.dataset.step = k; b.textContent = name;
  b.onclick = () => { stop(); goto(k); };
  jr.appendChild(b);
});

// 支持用 #step=8 直接跳到第 8 步（便于截图/分享某个阶段）
const m = /step=(\d+)/.exec(location.hash);
const init = m ? Math.max(0, Math.min(TOTAL, +m[1])) : 0;
if (init > 0) document.getElementById('start').classList.add('gone');
goto(init, false);
</script>
</body>
</html>
"""


if __name__ == "__main__":
    path, total, stats, size = build()
    print(f"OK -> {os.path.basename(path)}  ({os.path.getsize(path)} bytes)")
    print(f"   步骤 {total + 1} 步（0..{total}） · 画布 {size[0]}x{size[1]}")
    print(f"   {stats['items']} 小骨 · {stats['keys']} 重点 · {stats['kids']} 小小骨")
