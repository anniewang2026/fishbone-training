# -*- coding: utf-8 -*-
"""标准鱼骨图生成器 v2
结构：鱼头(右) → 脊骨 → 大骨(60度斜线) → 中骨(水平线) → 小骨(垂直短刺) → 小小骨(嵌套)
标准绘制法，不使用卡片式排版。
"""
import io, math

FONT = 16
TITLE_X, TITLE_Y = 60, 70

# ---------------- 数据：大骨 → 中骨 → 小骨(可带小小骨) ----------------
CATS = [
    dict(name="材料", side="top", cls="b", base_x=1600, groups=[
        ("性能", [("流动性差", 0, []), ("制剂添加过多", 0, []), ("未密封", 0, []), ("氧化", 0, [])]),
        ("材质", [("吸水", 0, []), ("分解", 0, [("长时间外露", 0)]), ("搅拌时间短", 0, []),
                 ("混合机异常", 0, []), ("混合比例异常", 0, [])]),
        ("材料干燥", [("干燥时间不足", 0, [("定时器异常", 0)]), ("加料不及时", 0, []), ("设备异常", 0, []),
                   ("设定错误", 0, []), ("干燥温度偏低", 1, [])]),
        ("混合材", [("粉尘多", 0, []), ("未筛选", 1, []), ("混入杂物", 0, []), ("不同材料", 0, []),
                  ("粉碎机异常", 1, []), ("水口料", 0, []), ("刀片筛网磨损", 1, [])]),
    ]),
    dict(name="设备", side="top", cls="t", base_x=2950, groups=[
        ("成形机", [("螺杆磨损", 1, []), ("材质差", 0, []), ("时间长磨损", 0, []),
                  ("使用大吨位机器", 0, []), ("合模力大", 0, []), ("料筒", 1, [])]),
        ("模温机", [("循环水不足", 0, []), ("温度异常", 0, []), ("发热异常", 0, []), ("压力不足", 0, []),
                  ("机水", 0, []), ("开关未开", 0, []), ("冷却系统异常", 0, [])]),
        ("金型", [("设计不适", 0, []), ("进胶口小", 0, []), ("取数过多", 0, []), ("逸胶不平衡", 0, []),
                ("制品肉厚太薄", 0, []), ("配件不良", 0, []), ("尺寸不良", 0, []), ("破损", 0, []), ("堵塞", 0, []),
                ("清扫不及时", 1, []), ("槽深度不够", 0, []), ("位子不当", 0, []), ("温度低", 0, []),
                ("炭化物堵塞", 0, []), ("排气槽不良", 1, []),
                ("干燥剂", 0, [("过期失效", 0), ("设定错误", 0)]),
                ("温度异常", 0, []), ("温控失效", 0, []), ("过滤网未定期清扫", 0, []),
                ("过滤网堵塞", 0, []), ("坏", 0, []), ("发热器", 0, [("不能正常发热", 0)])]),
        ("干燥机", [("热流道不顺", 0, []), ("温度异常", 0, []), ("温控失效", 0, []), ("发热器", 0, [])]),
    ]),
    dict(name="人", side="bottom", cls="i", base_x=1600, groups=[
        ("作业者", [("作业手法错误", 0, []), ("工作马虎", 0, []), ("不良位置不明确", 0, []), ("品质观念不强", 0, [])]),
        ("PQC", [("抽段数量不够", 1, []), ("未按标准作业", 0, [])]),
        ("成型技术员", [("技术缺乏", 0, []), ("操作失误", 0, []), ("未打开升水", 0, []),
                    ("未对量产前部品进行确认", 1, []), ("未废弃开不良品", 1, [])]),
        ("修模技术员", [("配件装错", 0, []), ("经验不足", 0, [])]),
    ]),
    dict(name="方法", side="bottom", cls="s", base_x=2950, groups=[
        ("金型维护", [("未按计划进行", 0, []), ("定期保养", 0, []), ("未按时进行", 1, []), ("方法错误", 0, []),
                   ("项目不全方法不正确", 0, []), ("日常保养", 0, []), ("保养位不全", 0, []),
                   ("配件装错", 0, []), ("修理", 0, []), ("未按WGS作业", 1, [])]),
        ("操作", [("开机生产部品未确认品质", 0, []), ("未按规定废弃数量", 1, []), ("未定期清洗", 0, []),
                ("料筒热流道清洗干净", 0, []), ("未清洗干净", 0, []), ("未废弃异常部品", 1, []),
                ("未确认", 0, []), ("未按下料槽", 0, []), ("异常处理", 0, [])]),
        ("检查", [("出货检查", 0, []), ("未检查", 0, []), ("抽取数量不够", 0, []),
                 ("未全数检查", 0, []), ("漏检", 0, []), ("外观全检", 0, [])]),
        ("成形条件", [("温度", 1, [("溶胶温度低", 0), ("热胶道温度低", 0), ("金型温度低", 0)]),
                   ("速度", 1, [("计量速度慢", 0), ("射出速度慢", 0)]),
                   ("时间", 1, [("射出时间短", 0), ("保压时间不够", 0)]),
                   ("压力", 1, [("背压力小", 0), ("射出压力小", 0), ("合模压力大", 0), ("保压力小", 0)]),
                   ("位置", 1, [("计量位置小", 0), ("保压切换位置大", 0)])]),
    ]),
]

SPINE_Y = 980
CANVAS_W, CANVAS_H = 3660, 1900
HEAD_W, HEAD_H = 330, 200
L_MAX = 900
L_HARD_MAX = 1250
BONE_CLEAR = 95     # 内容区距大骨斜线的让位距离
GAP_ROWS = 34
GAP_CHILD = 27
GRP_GAP = 26
ROW_STAGGER = 0    # 已改用纵向嵌套带，无需横向错位
TINT = {"b": ("#e0f2fe", "#0369a1"), "t": ("#ccfbf1", "#0f766e"),
        "i": ("#e0e7ff", "#4338ca"), "s": ("#e2e8f0", "#334155")}
GRAD = {"b": "gB", "t": "gT", "i": "gI", "s": "gS"}


def tw(s, font=FONT):
    w = 0.0
    for ch in s:
        w += font * (1.0 if ord(ch) > 0x2E00 else 0.56)
    return w


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def chip_w(text, key):
    label = ("★" + text) if key else text
    return tw(label) + 20


def layout_group(gname, items, L_max):
    """一个中骨组的排版：行分配、每根小骨刺高、组深度、水平线长度"""
    label_w = tw(gname) + 22
    # BONE_CLEAR：为大骨斜线让位（小骨文字位于中骨线上方，斜线在该高度会更靠左）
    avail = L_max - label_w - 30 - BONE_CLEAR
    slots = []
    for text, key, kids in items:
        w_self = chip_w(text, key)
        w_kid = max([tw(k[0]) + 18 for k in kids] or [0])
        # 有小小骨时，独占格宽度 = 自身 + 小小骨（小小骨在自己的格内向右展开）
        slot = (w_self + w_kid + 40 if kids else w_self) + 12
        slots.append(dict(text=text, key=key, kids=kids, slot=slot, own_w=w_self, kids_w=w_kid))
    rows, tmp = None, []
    for _max_rows in range(1, 6):
        tmp, cur, cw = [], [], 0.0
        for s in slots:
            if cur and cw + s["slot"] > avail:
                tmp.append(cur)
                cur, cw = [], 0.0
            cur.append(s)
            cw += s["slot"]
        if cur:
            tmp.append(cur)
        if len(tmp) <= _max_rows:
            rows = tmp
            break
    if rows is None:
        rows = tmp
    depth = 0
    for r, row in enumerate(rows):
        maxc = max(len(s["kids"]) for s in row)
        for s in row:
            s["tick"] = 20 + GAP_ROWS * r
        # 行高：小骨刺 + 父文字 + 小小骨嵌套带
        d = (20 + GAP_ROWS * r) + 54 + (GAP_CHILD * (maxc - 1) if maxc else 0)
        depth = max(depth, d)
    L = label_w + 30 + max(sum(s["slot"] for s in row) for row in rows) + BONE_CLEAR
    return dict(name=gname, label_w=label_w, L=min(L, L_max), depth=depth + 12, rows=rows)


def build():
    o = io.StringIO()
    o.write(f'''<svg viewBox="0 0 {CANVAS_W} {CANVAS_H}" xmlns="http://www.w3.org/2000/svg" font-family="Microsoft YaHei,PingFang SC,sans-serif" id="fishboneSvg">
<defs>
 <linearGradient id="gB" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7dd3fc"/><stop offset="1" stop-color="#0ea5e9"/></linearGradient>
 <linearGradient id="gT" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5eead4"/><stop offset="1" stop-color="#14b8a6"/></linearGradient>
 <linearGradient id="gI" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#a5b4fc"/><stop offset="1" stop-color="#6366f1"/></linearGradient>
 <linearGradient id="gS" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#94a3b8"/><stop offset="1" stop-color="#475569"/></linearGradient>
 <linearGradient id="gHead" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#38bdf8"/><stop offset="1" stop-color="#14b8a6"/></linearGradient>
 <linearGradient id="gKey" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#93c5fd"/><stop offset="1" stop-color="#3b82f6"/></linearGradient>
</defs>
<rect x="0" y="0" width="{CANVAS_W}" height="{CANVAS_H}" fill="#f8fbfd"/>
<text x="{TITLE_X}" y="{TITLE_Y}" font-size="30" font-weight="bold" fill="#1e3a5f">欠料（料不良）要因分析图</text>
<text x="{TITLE_X}" y="{TITLE_Y+34}" font-size="16" fill="#7b8ba1">标准鱼骨图 ｜ 大骨 → 中骨 → 小骨 → 小小骨 ｜ 蓝色高亮 ★ = 重点要因（待真因验证）</text>
''')
    stats = dict(items=0, keys=0)
    boxes, groups_all = [], []

    def place(cat, gs):
        sign = -1 if cat["side"] == "top" else 1
        need = sum(g["depth"] for g in gs) + GRP_GAP * (len(gs) - 1)
        dv = need / 0.78
        dx = dv / math.tan(math.radians(60))
        cursor = SPINE_Y + sign * (0.16 * dv)
        for g in reversed(gs):
            y_line = cursor
            cursor += sign * (g["depth"] + GRP_GAP)
            g["y_line"] = y_line
            g["x_attach"] = cat["base_x"] - dx * (abs(y_line - SPINE_Y) / dv)
            g["x_out"] = g["x_attach"] - g["L"]
        return dv, dx, cat["base_x"] - dx, SPINE_Y + sign * dv

    for cat in CATS:
        lcurs = [L_MAX] * len(cat["groups"])
        for _ in range(5):
            gs = [layout_group(n, it, lcurs[k]) for k, (n, it) in enumerate(cat["groups"])]
            place(cat, gs)
            newl = [min(L_HARD_MAX, max(520, g["x_attach"] - 60)) for g in gs]
            if all(abs(a - b) < 25 for a, b in zip(newl, lcurs)):
                lcurs = newl
                break
            lcurs = newl
        gs = [layout_group(n, it, lcurs[k]) for k, (n, it) in enumerate(cat["groups"])]
        tip_x, tip_y = place(cat, gs)[2:]
        for g in gs:
            boxes.append((cat["name"], g["name"], g["x_out"], g["x_attach"],
                          min(g["y_line"], g["y_line"] + (-1 if cat["side"] == "top" else 1) * g["depth"]),
                          max(g["y_line"], g["y_line"] + (-1 if cat["side"] == "top" else 1) * g["depth"])))
        groups_all.append((cat, gs, tip_x, tip_y))
    for nm, gn, x0, x1, y0, y1 in boxes:
        if x0 < 30:
            print(f"[warn] {nm}/{gn} 超出左边界 x0={x0:.0f}")
        if x1 > CANVAS_W - 30 or y0 < 130 or y1 > CANVAS_H - 60:
            print(f"[warn] {nm}/{gn} 超出画布 x1={x1:.0f} y=({y0:.0f},{y1:.0f})")
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            if a[0] == b[0]:
                continue
            if a[2] < b[3] and b[2] < a[3] and min(a[4], a[5]) < max(b[4], b[5]) and min(b[4], b[5]) < max(a[4], a[5]):
                print(f"[warn] 区域重叠 {a[0]}/{a[1]} × {b[0]}/{b[1]}")
    head_x = CANVAS_W - HEAD_W - 45
    o.write(f'<line x1="40" y1="{SPINE_Y}" x2="{head_x-8}" y2="{SPINE_Y}" stroke="#475569" stroke-width="8" stroke-linecap="round"/>\n')
    o.write(f'<polygon points="{head_x-8},{SPINE_Y-24} {head_x-8},{SPINE_Y+24} {head_x+22},{SPINE_Y}" fill="#475569"/>\n')
    o.write(f'<rect x="{head_x+24}" y="{SPINE_Y-HEAD_H//2}" width="{HEAD_W}" height="{HEAD_H}" rx="40" fill="url(#gHead)"/>\n')
    o.write(f'<text x="{head_x+24+HEAD_W//2}" y="{SPINE_Y+4}" font-size="52" font-weight="bold" fill="#ffffff" text-anchor="middle">欠　料</text>\n')
    o.write(f'<text x="{head_x+24+HEAD_W//2}" y="{SPINE_Y+52}" font-size="22" fill="#ffffff" opacity="0.95" text-anchor="middle">（ 料 不 良 ）</text>\n')
    for cat, gs, tip_x, tip_y in groups_all:
        sign = -1 if cat["side"] == "top" else 1
        o.write(f'<line x1="{cat["base_x"]}" y1="{SPINE_Y}" x2="{tip_x:.0f}" y2="{tip_y:.0f}" stroke="#475569" stroke-width="6" stroke-linecap="round"/>\n')
        ly = tip_y + sign * 64
        o.write(f'<rect x="{tip_x-92:.0f}" y="{ly-30:.0f}" width="184" height="60" rx="22" fill="url(#{GRAD[cat["cls"]]})"/>\n')
        o.write(f'<text x="{tip_x:.0f}" y="{ly+11:.0f}" font-size="30" font-weight="bold" fill="#ffffff" text-anchor="middle">{cat["name"]}</text>\n')
        tint, tcol = TINT[cat["cls"]]
        for g in gs:
            y_line, x_att, x_out = g["y_line"], g["x_attach"], g["x_out"]
            o.write(f'<line x1="{x_out:.0f}" y1="{y_line:.0f}" x2="{x_att:.0f}" y2="{y_line:.0f}" stroke="#64748b" stroke-width="3.5"/>\n')
            o.write(f'<circle cx="{x_att:.0f}" cy="{y_line:.0f}" r="6" fill="#38bdf8"/>\n')
            o.write(f'<rect x="{x_out:.0f}" y="{y_line-19:.0f}" width="{g["label_w"]:.0f}" height="38" rx="16" fill="{tint}" stroke="{tcol}" stroke-opacity="0.35"/>\n')
            o.write(f'<text x="{x_out+g["label_w"]/2:.0f}" y="{y_line+7:.0f}" font-size="19" font-weight="bold" fill="{tcol}" text-anchor="middle">{esc(g["name"])}</text>\n')
            cx = x_out + g["label_w"] + 30
            for r, row in enumerate(g["rows"]):
                cx = x_out + g["label_w"] + 30
                for s in row:
                    tick = s["tick"]
                    tx = cx + s["own_w"] / 2 + 6          # 小骨刺位置
                    nkid = len(s["kids"])
                    tick_all = tick + (34 + GAP_CHILD * (nkid - 1) if nkid else 0)
                    o.write(f'<line x1="{tx:.0f}" y1="{y_line:.0f}" x2="{tx:.0f}" y2="{y_line+sign*tick_all:.0f}" stroke="#94a3b8" stroke-width="2"/>\n')
                    label = ("★" + s["text"]) if s["key"] else s["text"]
                    w = s["own_w"]
                    if sign < 0:
                        ty = y_line - tick - 8
                        if s["key"]:
                            o.write(f'<rect x="{tx-w/2:.0f}" y="{ty-19:.0f}" width="{w:.0f}" height="27" rx="13" fill="url(#gKey)"/>\n')
                            o.write(f'<text x="{tx:.0f}" y="{ty+2:.0f}" font-size="{FONT}" font-weight="bold" fill="#ffffff" text-anchor="middle">{esc(label)}</text>\n')
                        else:
                            o.write(f'<text x="{tx:.0f}" y="{ty:.0f}" font-size="{FONT}" fill="#334155" text-anchor="middle">{esc(label)}</text>\n')
                        for i, (kt, _k) in enumerate(s["kids"]):
                            cy = y_line - (tick + 34 + GAP_CHILD * i)
                            kw = tw(kt) + 18
                            o.write(f'<line x1="{tx:.0f}" y1="{cy:.0f}" x2="{tx+kw:.0f}" y2="{cy:.0f}" stroke="#94a3b8" stroke-width="1.6"/>\n')
                            o.write(f'<text x="{tx+12:.0f}" y="{cy-7:.0f}" font-size="{FONT-2}" fill="#475569" text-anchor="start">{esc(kt)}</text>\n')
                    else:
                        ty = y_line + tick + 20
                        if s["key"]:
                            o.write(f'<rect x="{tx-w/2:.0f}" y="{ty-20:.0f}" width="{w:.0f}" height="27" rx="13" fill="url(#gKey)"/>\n')
                            o.write(f'<text x="{tx:.0f}" y="{ty+1:.0f}" font-size="{FONT}" font-weight="bold" fill="#ffffff" text-anchor="middle">{esc(label)}</text>\n')
                        else:
                            o.write(f'<text x="{tx:.0f}" y="{ty:.0f}" font-size="{FONT}" fill="#334155" text-anchor="middle">{esc(label)}</text>\n')
                        for i, (kt, _k) in enumerate(s["kids"]):
                            cy = y_line + (tick + 34 + GAP_CHILD * i)
                            kw = tw(kt) + 18
                            o.write(f'<line x1="{tx:.0f}" y1="{cy:.0f}" x2="{tx+kw:.0f}" y2="{cy:.0f}" stroke="#94a3b8" stroke-width="1.6"/>\n')
                            o.write(f'<text x="{tx+12:.0f}" y="{cy+17:.0f}" font-size="{FONT-2}" fill="#475569" text-anchor="start">{esc(kt)}</text>\n')
                    cx += s["slot"]
                    stats["items"] += 1
                    stats["keys"] += s["key"]
    ly = CANVAS_H - 42
    o.write(f'<rect x="60" y="{ly-19}" width="34" height="27" rx="13" fill="url(#gKey)"/><text x="77" y="{ly+2}" font-size="15" font-weight="bold" fill="#ffffff" text-anchor="middle">★</text>\n')
    o.write(f'<text x="106" y="{ly+2}" font-size="16" fill="#46586e">重点要因（待真因验证）</text>\n')
    o.write(f'<text x="430" y="{ly+2}" font-size="16" fill="#7b8ba1">绘制法：鱼头 → 脊骨 → 大骨(60°) → 中骨(水平) → 小骨(短刺) → 小小骨(嵌套)</text>\n')
    o.write(f'<text x="{CANVAS_W-580}" y="{ly+2}" font-size="16" fill="#7b8ba1">4 大骨 · 16 中骨 · {stats["items"]} 小骨 · ★{stats["keys"]} 重点要因</text>\n')
    o.write('</svg>')
    return o.getvalue(), stats


def cards():
    o = io.StringIO()
    for cat in CATS:
        n_items = sum(len(it) for _, it in cat["groups"])
        n_key = sum(k for _, it in cat["groups"] for _, k, _ in it)
        o.write(f'<div class="card"><div class="cat-head"><span class="cat-ico ci-{cat["cls"]}">{cat["name"]}</span>'
                f'<span style="font-size:13px;color:#7b8ba1">{len(cat["groups"])}中骨 · {n_items}小骨 · ★{n_key}重点</span></div>')
        for gname, items in cat["groups"]:
            o.write(f'<div class="grp"><div class="gname">{esc(gname)}</div><div class="tags">')
            for text, key, kids in items:
                cls = "tag-item key" if key else "tag-item"
                o.write(f'<span class="{cls}">{esc(("★" + text) if key else text)}</span>')
                for kt, _k in kids:
                    o.write(f'<span class="tag-kid">↳ {esc(kt)}</span>')
            o.write('</div></div>')
        o.write('</div>')
    return o.getvalue()


SVG, STATS = build()
SRC = r"C:\Users\annie\WorkBuddy\2026-09-10-11-13-32\要因图培训\index.src.html"
DST = r"C:\Users\annie\WorkBuddy\2026-09-10-11-13-32\要因图培训\index.html"
with open(SRC, encoding="utf-8") as f:
    html = f.read()
html = html.replace("<!--FISHBONE_SVG-->", SVG)
html = html.replace("<!--CATEGORY_CARDS-->", cards())
with open(DST, "w", encoding="utf-8") as f:
    f.write(html)
with open(r"C:\Users\annie\WorkBuddy\2026-09-10-11-13-32\要因图培训\fishbone.svg", "w", encoding="utf-8") as f:
    f.write(SVG)
print(f"OK: {STATS['items']} 小骨, {STATS['keys']} 重点要因, svg {len(SVG)} chars")
