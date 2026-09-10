# -*- coding: utf-8 -*-
"""标准鱼骨图生成器 v6 —— 小骨 / 小小骨一律「水平线」（与中骨平行）

绘图规格：
  · 主骨（脊骨）水平，鱼头在右
  · 大骨与主骨成 60°
  · 中骨：水平线，与主骨平行；同一大骨的中骨由内向外左右交错分布
  · 小骨：水平短线，与所属中骨平行；文字写在线的上方；线一端经收集线接到中骨
  · 小小骨：水平短线，与所属中骨平行；从父小骨线末端向外延伸，并向中骨侧缩进一行

坐标原点取脊骨，最后整体平移进画布。
"""
import io, math

# ---------------- 参数（可调） ----------------
BONE_DEG = 60.0                  # 大骨与脊骨夹角（标准 60°）
TAN = math.tan(math.radians(BONE_DEG))
FONT, FONT_KID, FONT_G, FONT_CAT = 15, 13, 17, 30

ROW_PITCH = 28                   # 小骨行距
TOP_OFF = 34                     # 第一行小骨线距中骨线的距离
COL_GAP = 22                     # 同半区相邻列的净距
ROW_MAX = 2                      # 每列最多占用的「行单位」（小骨 1 + 每个小小骨 1）
DIAG_CLR = 34                    # 内容与大骨斜线之间的净距
LINE_L = 18                      # 小骨横线在文字两端的出头长度
LINE_LK = 13                     # 小小骨横线出头长度
KID_OFF = 7                      # 小小骨横线起点相对父小骨线末端的偏移
LINE_GAP = 24                    # 相邻中骨线最小净距
LABEL_PAD = 18                   # 中骨名与内容间距
START_V = 84                     # 最内侧中骨线距脊骨距离
TAIL = 52                        # 大骨超出最外中骨长度
GAP = 100                        # 左右两类内容之间的最小净距
PAD = 44                         # 画布留白

# 鱼头文字（改这两行即可换案例名；HEAD_SUB 留空则鱼头变矮）
HEAD_TEXT = "注塑件缺料"
HEAD_SUB = "（短 射）"
HEAD_W, HEAD_H = 356, 212

# ---------------- 数据 ----------------
# groups 自「脊骨侧」向「外侧」排列；side: L=向外侧延展 / R=向鱼头侧延展
CATS = [
    dict(name="材料", side="top", cls="b", groups=[
        ("材料干燥", "L", [("干燥时间不足", 0, [("定时器异常", 0)]), ("加料不及时", 0, []),
                        ("设备异常", 0, []), ("设定错误", 0, []), ("干燥温度偏低", 1, [])]),
        ("混合材", "R", [("粉尘多", 0, []), ("混入杂物", 0, []), ("未筛选", 1, []), ("不同材料", 0, []),
                       ("粉碎机异常", 1, []), ("水口长", 0, []), ("刀片筛网磨损", 1, [])]),
        ("性能", "L", [("流动性差", 0, []), ("制剂添加过多", 0, []), ("未密封", 0, []), ("氧化", 0, [])]),
        ("材质", "R", [("吸水", 0, [("长时间外露", 0)]), ("分解", 0, []), ("搅拌时间短", 0, []),
                      ("混合机异常", 0, []), ("混合比例异常", 0, [])]),
    ]),
    dict(name="设备", side="top", cls="t", groups=[
        ("干燥机", "R", [("干燥剂", 0, [("过期失效", 0), ("设定错误", 0)]), ("温度异常", 0, []),
                       ("温控失效", 0, []), ("过滤网未定期清扫", 0, []), ("过滤网堵塞", 0, []),
                       ("坏", 0, []), ("发热器", 0, [("不能正常发热", 0)])]),
        ("模温机", "L", [("循环水不足", 0, []), ("温度异常", 0, []), ("发热异常", 0, []),
                       ("压力不足", 0, []), ("机水", 0, []), ("开关未开", 0, []), ("冷却系统异常", 0, [])]),
        ("模具空腔", "R", [("设计不适", 0, []), ("取数过多", 0, []), ("配件不良", 0, []), ("尺寸不良", 0, []),
                        ("破损", 0, []), ("进胶口小", 0, []), ("进胶不平衡", 0, []), ("部品肉厚太薄", 0, []),
                        ("堵塞", 0, []), ("清扫不及时", 1, []), ("槽深度不够", 0, []), ("位子不当", 0, []),
                        ("温度低", 0, []), ("炭化物堵塞", 0, []), ("排气槽不良", 1, []), ("热流道不顺", 0, [])]),
        ("成形机", "L", [("螺杆磨损", 1, []), ("材质差", 0, []), ("时间长磨损", 0, []),
                       ("使用大吨位机器", 0, []), ("合模力大", 0, []), ("料筒", 1, []),
                       ("温控器坏", 0, [])]),
    ]),
    dict(name="人", side="bottom", cls="i", groups=[
        ("作业者", "L", [("作业手法错误", 0, []), ("工作马虎", 0, []),
                       ("不良位置不明确", 0, []), ("品质观念不强", 0, [])]),
        ("成型技术员", "R", [("技术缺乏", 0, []), ("操作失误", 0, []), ("未打开升水", 0, []),
                          ("未废弃开机不良品", 1, []), ("未对量产前部品进行确认", 1, []),
                          ("未按照规定清扫排气槽", 1, [])]),
        ("PQC", "L", [("未按标准作业", 0, []), ("抽取数量不够", 0, [])]),
        ("修模技术员", "R", [("配件装错", 0, []), ("经验不足", 0, [])]),
    ]),
    dict(name="方法", side="bottom", cls="s", groups=[
        ("检查", "R", [("出货检查", 0, []), ("未检查", 0, []), ("抽取数量不够", 0, []),
                      ("未全数检查", 0, []), ("漏检", 0, []), ("外观全检", 0, [])]),
        ("模具维护", "L", [("未按计划进行", 0, []), ("未按时进行", 1, []), ("定期保养", 0, []),
                        ("方法错误", 0, []), ("日常保养", 0, []), ("项目不全方法不正确", 0, []),
                        ("保养位子不全", 0, []), ("配件装错", 0, []), ("修理", 0, []),
                        ("未按WGS作业", 1, [])]),
        ("成形条件", "R", [("温度", 1, [("溶胶温度低", 0), ("热胶道温度低", 0), ("模温低", 0)]),
                        ("速度", 1, [("计量速度慢", 0), ("射出速度慢", 0)]),
                        ("时间", 1, [("射出时间短", 0), ("保压时间不够", 0)]),
                        ("压力", 1, [("背压力小", 0), ("射出压力小", 0), ("合模压力大", 0), ("保压力小", 0)]),
                        ("位置", 1, [("计量位置小", 0), ("保压切换位置大", 0)])]),
        ("操作", "L", [("开机生产部品未确认品质", 0, []), ("未按规定废弃数量", 1, []),
                      ("未定期清洗", 0, []), ("料筒热流道清洗", 0, []), ("未清洗干净", 0, []),
                      ("未废弃异常部品", 1, []), ("未确认", 0, []), ("未按下料槽", 0, []),
                      ("异常处理", 0, [])]),
    ]),
]

TINT = {"b": ("#e0f2fe", "#0369a1"), "t": ("#ccfbf1", "#0f766e"),
        "i": ("#e0e7ff", "#4338ca"), "s": ("#e2e8f0", "#334155")}
GRAD = {"b": "gB", "t": "gT", "i": "gI", "s": "gS"}


def tw(s, f=FONT):
    return sum(f * (1.0 if ord(ch) > 0x2E00 else 0.52) for ch in s)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def make_cells(items):
    """每个小骨 = 一条水平线 + 文字；小小骨 = 从父线末端向外延伸的水平线"""
    out = []
    for text, key, kids in items:
        label = ("★" + text) if key else text
        seg = tw(label, FONT) + LINE_L * 2                    # 小骨横线长度
        ks = [(k[0], tw(k[0], FONT_KID) + LINE_LK * 2) for k in kids]
        kw = max([w for _, w in ks] or [0])
        units = 1 + len(ks)                                   # 占用的行单位
        slot = seg + (KID_OFF + kw if ks else 0)              # 该小骨独占的横向宽度
        out.append(dict(text=text, key=key, label=label, kids=ks,
                        seg=seg, kw=kw, units=units, slot=slot))
    return out


def pack_half(cells):
    """一侧的小骨按「列」堆叠：先定列数使各列尽量等高，再逐列向下排"""
    if not cells:
        return [], 0
    total = sum(c["units"] for c in cells)
    ncol = max(1, math.ceil(total / ROW_MAX))
    cap = math.ceil(total / ncol)                     # 每列行单位上限（均衡）
    groups, cur, used = [], [], 0
    for c in cells:
        if cur and used + c["units"] > cap:
            groups.append(cur)
            cur, used = [], 0
        cur.append(c)
        used += c["units"]
    if cur:
        groups.append(cur)
    cols = []
    for g in groups:
        rows, pos = 0, []
        for c in g:
            pos.append(rows)
            rows += c["units"]
        cols.append(dict(cells=g, pos=pos, w=max(c["slot"] for c in g), rows=rows))
    return cols, max(c["rows"] for c in cols)


def layout_block(gname, items, side):
    label_w = tw(gname, FONT_G) + 24
    cells = make_cells(items)
    na = (len(cells) + 1) // 2
    up, up_r = pack_half(cells[:na])
    dn, dn_r = pack_half(cells[na:])
    ncol = max(len(up), len(dn))
    colw, colx, x = [], [], 0.0
    for i in range(ncol):
        a = up[i]["w"] if i < len(up) else 0.0
        b = dn[i]["w"] if i < len(dn) else 0.0
        w = max(a, b)
        colw.append(w)
        colx.append(x)
        x += w + COL_GAP
    items_w = (x - COL_GAP if colw else 0.0) + 14
    up_d = TOP_OFF + (up_r - 1) * ROW_PITCH + 22 if up_r else 0.0
    dn_d = TOP_OFF + (dn_r - 1) * ROW_PITCH + 12 if dn_r else 0.0
    # L 侧：向外半区被大骨斜线穿过 → 内容内侧让位
    # R 侧：向内半区被大骨斜线穿过 → 内容内侧让位
    if side == "L":
        head, tail_pad = 0.0, up_d / TAN + DIAG_CLR
    else:
        head, tail_pad = dn_d / TAN + DIAG_CLR, 0.0
    w = head + items_w + LABEL_PAD + label_w + tail_pad
    return dict(name=gname, side=side, label_w=label_w, head=head, tail_pad=tail_pad,
                up=up, dn=dn, up_r=up_r, dn_r=dn_r, up_d=up_d, dn_d=dn_d,
                colx=colx, colw=colw, items_w=items_w, w=w)


def plan_cat(cat, bx):
    blocks = []
    for gname, gside, items in cat["groups"]:
        blocks.append(layout_block(gname, items, gside))
    v = max(START_V, blocks[0]["dn_d"] + 46)
    for b in blocks:
        b["v"] = v
        v += b["up_d"] + b["dn_d"] + LINE_GAP
    return blocks, v - LINE_GAP + TAIL


def measure(cat):
    bs, V = plan_cat(cat, 0.0)
    xs = []
    for b in bs:
        xa = -b["v"] / TAN
        xf = xa - b["w"] if b["side"] == "L" else xa + b["w"]
        xs += [min(xa, xf), max(xa, xf)]
    return bs, V, min(xs), max(xs)


def plan_all():
    ref = {c["name"]: measure(c) for c in CATS}
    lefts, rights = ["材料", "人"], ["设备", "方法"]
    off_r = 0.0
    for lc in lefts:
        for rc in rights:
            off_r = max(off_r, (ref[lc][3] + GAP) - ref[rc][2])
    bx = {c["name"]: (0.0 if c["name"] in lefts else off_r) for c in CATS}

    prims, texts, segs, steps = [], [], [], []
    stats = dict(items=0, keys=0, kids=0)
    diag = dict(cats=[])
    detail = []
    owner = [None]
    st = [0]                                        # 当前绘制步骤（给动画演示用）

    def line(x1, y1, x2, y2, w, c, cap="round"):
        prims.append(("line", x1, y1, x2, y2, w, c, cap))
        steps.append(st[0])
        segs.append((x1, y1, x2, y2, owner[0]))

    def tri(pts, fill):
        prims.append(("poly", pts, fill))
        steps.append(st[0])

    def text(x, y, s, f, c, anchor="middle", weight="normal"):
        prims.append(("text", x, y, s, f, c, anchor, weight))
        steps.append(st[0])
        w = tw(s, f)
        x0 = x - (w / 2 if anchor == "middle" else (0 if anchor == "start" else w))
        texts.append((x0 - 3, y - f, x0 + w + 3, y + f * 0.35, s, owner[0]))

    def rect(x, y, w, h, rx, fill, stroke=None):
        prims.append(("rect", x, y, w, h, rx, fill, stroke))
        steps.append(st[0])

    nstep = 1                                       # 0 号步骤留给「主骨+鱼头」
    for cat in CATS:
        bs, V = plan_cat(cat, bx[cat["name"]])
        sign = -1 if cat["side"] == "top" else 1
        b0 = bx[cat["name"]]
        tip = (b0 - V / TAN, sign * V)
        bone_step = nstep                            # 一根大骨 = 一个步骤
        nstep += 1
        for b in bs:
            b["y"] = sign * b["v"]
            b["xa"] = b0 - b["v"] / TAN
            b["xf"] = b["xa"] - b["w"] if b["side"] == "L" else b["xa"] + b["w"]
            b["_step"] = nstep                       # 一根中骨 + 它的小骨 = 一个步骤
            nstep += 1
        detail.append((cat, bs, tip, sign, V, bone_step))
        stats["items"] += sum(len(it) for _, _, it in cat["groups"])
        stats["keys"] += sum(k for _, _, it in cat["groups"] for _, k, _ in it)
        stats["kids"] += sum(len(kd) for _, _, it in cat["groups"] for _, _, kd in it)
        diag["cats"].append(f'{cat["name"]}: 骨高{V:.0f} 骨长{V/math.sin(math.radians(BONE_DEG)):.0f}')
        for b in bs:
            diag["cats"].append(f'    {b["name"]:<6}{b["side"]} v={b["v"]:>4.0f} 宽={b["w"]:>4.0f} '
                                f'上{b["up_d"]:>4.0f}/下{b["dn_d"]:>4.0f}')
    total_steps = nstep                              # 最后一步 = 收尾（高亮★）

    for cat, bs, tip, sign, V, bone_step in detail:
        b0 = bx[cat["name"]]
        tint, tcol = TINT[cat["cls"]]
        gid = GRAD[cat["cls"]]
        st[0] = bone_step
        owner[0] = "BONE-" + cat["name"]
        line(b0, 0, tip[0], tip[1], 7, "#3f5061")
        ux, uy = (b0 - tip[0]) / V, (0 - tip[1]) / V
        ax, ay = b0 - ux * 48, -uy * 48
        px, py = -uy, ux
        tri([(b0, 0), (ax + px * 14, ay + py * 14), (ax - px * 14, ay - py * 14)], "#3f5061")
        lx, ly = tip[0] - ux * 68, tip[1] - uy * 68
        rect(lx - 76, ly - 33, 152, 66, 22, f"url(#{gid})")
        text(lx, ly + 11, cat["name"], FONT_CAT, "#ffffff", weight="bold")

        for b in bs:
            y, xa, xf, side = b["y"], b["xa"], b["xf"], b["side"]
            st[0] = b["_step"]
            # ---- 中骨：水平线（与主骨平行）+ 外端名称色片 ----
            owner[0] = "LINE-" + cat["name"] + "/" + b["name"]
            line(xf, y, xa, y, 3.4, "#64748b", cap="butt")
            ad = 15 if side == "L" else -15
            tri([(xa, y), (xa - ad, y - 8), (xa - ad, y + 8)], "#64748b")
            if side == "L":
                rect(xf, y - 21, b["label_w"], 42, 18, tint, tcol)
                text(xf + b["label_w"] / 2, y + 7, b["name"], FONT_G, tcol, weight="bold")
                x_in, dirn = xa - b["tail_pad"], -1.0
            else:
                rect(xf - b["label_w"], y - 21, b["label_w"], 42, 18, tint, tcol)
                text(xf - b["label_w"] / 2, y + 7, b["name"], FONT_G, tcol, weight="bold")
                x_in, dirn = xa + b["head"], 1.0
            # ---- 小骨 / 小小骨（一律水平线，与中骨平行）----
            for cols, sgn2 in ((b["up"], 1.0), (b["dn"], -1.0)):
                away = sign * sgn2                     # 行号增大方向的屏幕 y 系数
                for i, col in enumerate(cols):
                    x_col = x_in + dirn * b["colx"][i]
                    deep = TOP_OFF + (col["rows"] - 1) * ROW_PITCH
                    owner[0] = "COL-" + cat["name"] + "/" + b["name"] + "#" + str(i)
                    line(x_col, y, x_col, y + away * deep, 1.8, "#cbd5e1", cap="butt")
                    for c, r in zip(col["cells"], col["pos"]):
                        yl = y + away * (TOP_OFF + r * ROW_PITCH)
                        x_seg = x_col + dirn * c["seg"]
                        owner[0] = f'{cat["name"]}/{b["name"]}#{i}-{r}'
                        if c["key"]:
                            line(x_col, yl, x_seg, yl, 3.2, "#e11d48", cap="butt")
                        else:
                            line(x_col, yl, x_seg, yl, 2.2, "#94a3b8", cap="butt")
                        text(x_col + dirn * 8, yl - 5, c["label"], FONT,
                             "#be123c" if c["key"] else "#2f4256",
                             anchor="start" if dirn > 0 else "end",
                             weight="bold" if c["key"] else "normal")
                        if c["kids"]:
                            x_j = x_col + dirn * (c["seg"] + KID_OFF)
                            ky_last = y + away * (TOP_OFF + (r + len(c["kids"])) * ROW_PITCH)
                            line(x_j, yl, x_j, ky_last, 1.4, "#cbd5e1", cap="butt")
                            for j, (kt, kw) in enumerate(c["kids"]):
                                ky = y + away * (TOP_OFF + (r + j + 1) * ROW_PITCH)
                                line(x_j, ky, x_j + dirn * kw, ky, 1.6, "#94a3b8", cap="butt")
                                text(x_j + dirn * 7, ky - 4, kt, FONT_KID, "#4a5c72",
                                     anchor="start" if dirn > 0 else "end")

    xs, ys = [], []
    for p in prims:
        if p[0] == "line":
            xs += [p[1], p[3]]; ys += [p[2], p[4]]
        elif p[0] == "poly":
            xs += [q[0] for q in p[1]]; ys += [q[1] for q in p[1]]
        elif p[0] == "rect":
            xs += [p[1], p[1] + p[3]]; ys += [p[2], p[2] + p[4]]
    for t in texts:
        xs += [t[0], t[2]]; ys += [t[1], t[3]]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)

    st[0] = 0                                       # 步骤 0：主骨 + 鱼头
    owner[0] = "SPINE"
    line(minx + 16, 0, maxx + 74, 0, 9, "#3f5061")
    tri([(maxx + 120, 0), (maxx + 74, -27), (maxx + 74, 27)], "#3f5061")
    hx = maxx + 120
    if HEAD_SUB:
        rect(hx + 26, -HEAD_H / 2, HEAD_W, HEAD_H, 46, "url(#gHead)")
        text(hx + 26 + HEAD_W / 2, 6, HEAD_TEXT, 46, "#ffffff", weight="bold")
        text(hx + 26 + HEAD_W / 2, 56, HEAD_SUB, 22, "#ffffff")
    else:
        rect(hx + 26, -66, HEAD_W, 132, 40, "url(#gHead)")
        text(hx + 26 + HEAD_W / 2, 18, HEAD_TEXT, 46, "#ffffff", weight="bold")

    full_minx, full_maxx = minx, hx + 26 + HEAD_W + 26
    dx, dy = PAD - full_minx, PAD - miny + 96
    W = int(math.ceil(full_maxx - full_minx + PAD * 2))
    H = int(math.ceil(maxy - miny + PAD * 2 + 96))
    diag["dx"], diag["dy"] = dx, dy
    diag["texts"], diag["segs"] = texts, segs
    diag["steps"] = steps
    diag["total_steps"] = total_steps
    return prims, stats, (W, H), diag


def check():
    """碰撞自查：文字互压 / 线段穿透他人文字 / 大骨穿透文字"""
    prims, stats, size, diag = plan_all()
    texts, segs, bad = diag["texts"], diag["segs"], []
    for i in range(len(texts)):
        a = texts[i]
        for j in range(i + 1, len(texts)):
            b = texts[j]
            if a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]:
                bad.append(f'文字互压: 「{a[4]}」 × 「{b[4]}」')

    def hit(t, x1, y1, x2, y2):
        """任意线段是否与文字框相交（Liang-Barsky 裁剪）"""
        bx0, by0, bx1, by1 = t[0], t[1], t[2], t[3]
        dx, dy = x2 - x1, y2 - y1
        t0, t1 = 0.0, 1.0
        for p, q in ((-dx, x1 - bx0), (dx, bx1 - x1),
                     (-dy, y1 - by0), (dy, by1 - y1)):
            if abs(p) < 1e-9:
                if q < 0:
                    return False
                continue
            r = q / p
            if p < 0:
                if r > t1:
                    return False
                t0 = max(t0, r)
            else:
                if r < t0:
                    return False
                t1 = min(t1, r)
        return t0 < t1

    for (x1, y1, x2, y2, own) in segs:
        for t in texts:
            if own is not None and t[5] == own:
                continue
            if t[5] is None:
                continue
            if hit(t, x1, y1, x2, y2):
                kind = "大骨" if str(own).startswith(("BONE-", "SPINE")) else "线段"
                bad.append(f'{kind}穿透:「{t[4]}」 (owner={own})')
    print(f"自查: {len(texts)} 文字块 / {len(segs)} 线段 → 问题 {len(bad)} 处")
    for s in bad[:40]:
        print("   -", s)
    return bad


def build_svg():
    prims, stats, size, diag = plan_all()
    W, H = size
    o = io.StringIO()
    o.write(f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" '
            f'font-family="Microsoft YaHei,PingFang SC,sans-serif" id="fishboneSvg">\n<defs>\n'
            '<linearGradient id="gB" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7dd3fc"/><stop offset="1" stop-color="#0ea5e9"/></linearGradient>\n'
            '<linearGradient id="gT" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5eead4"/><stop offset="1" stop-color="#14b8a6"/></linearGradient>\n'
            '<linearGradient id="gI" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#a5b4fc"/><stop offset="1" stop-color="#6366f1"/></linearGradient>\n'
            '<linearGradient id="gS" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#94a3b8"/><stop offset="1" stop-color="#475569"/></linearGradient>\n'
            '<linearGradient id="gHead" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#38bdf8"/><stop offset="1" stop-color="#14b8a6"/></linearGradient>\n'
            '<linearGradient id="gKey" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#93c5fd"/><stop offset="1" stop-color="#3b82f6"/></linearGradient>\n'
            '</defs>\n')
    o.write(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#f8fbfd"/>\n')
    dx, dy = diag["dx"], diag["dy"]
    o.write(f'<g transform="translate({dx:.0f},{dy:.0f})">\n')
    o.write(f'<text x="{PAD}" y="{-dy + 54:.0f}" font-size="31" font-weight="bold" fill="#1e3a5f">'
            f'{esc(HEAD_TEXT)}{esc(HEAD_SUB)} 要因分析图</text>\n')
    o.write(f'<text x="{PAD}" y="{-dy + 88:.0f}" font-size="16" fill="#7b8ba1">'
            f'标准鱼骨图 ｜ 大骨与主骨成 {BONE_DEG:.0f}° ｜ 中骨／小骨／小小骨 均为水平线（与主骨平行） ｜ '
            f'★=重点要因（待真因验证）</text>\n')
    for p in prims:
        if p[0] == "line":
            _, x1, y1, x2, y2, w, c, cap = p
            o.write(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" '
                    f'stroke="{c}" stroke-width="{w}" stroke-linecap="{cap}"/>\n')
        elif p[0] == "poly":
            pts = " ".join(f"{q[0]:.0f},{q[1]:.0f}" for q in p[1])
            o.write(f'<polygon points="{pts}" fill="{p[2]}"/>\n')
        elif p[0] == "rect":
            _, x, y, w, h, rx, fill, stroke = p
            st = f' stroke="{stroke}" stroke-opacity="0.4"' if stroke else ""
            o.write(f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" rx="{rx}" '
                    f'fill="{fill}"{st}/>\n')
        else:
            _, x, y, s, f, c, anchor, weight = p
            o.write(f'<text x="{x:.0f}" y="{y:.0f}" font-size="{f}" fill="{c}" text-anchor="{anchor}" '
                    f'font-weight="{weight}">{esc(s)}</text>\n')
    o.write('</g>\n</svg>')
    return o.getvalue(), stats, size, diag


def cards():
    """页面下半部分的「同一份内容·放大可读版」分类卡片"""
    o = io.StringIO()
    for cat in CATS:
        n_items = sum(len(it) for _, _, it in cat["groups"])
        n_key = sum(k for _, _, it in cat["groups"] for _, k, _ in it)
        o.write(f'<div class="card"><div class="cat-head">'
                f'<span class="cat-ico ci-{cat["cls"]}">{cat["name"]}</span>'
                f'<span style="font-size:13px;color:#7b8ba1">{len(cat["groups"])} 中骨 · '
                f'{n_items} 小骨 · ★{n_key} 重点</span></div>')
        for gname, gside, items in cat["groups"]:
            o.write(f'<div class="grp"><div class="gname">{esc(gname)}'
                    f'<span style="font-weight:400;color:#8ba0b6;font-size:12.5px">'
                    f'　（挂在斜线{"外侧" if gside == "L" else "内侧"}）</span></div><div class="tags">')
            for text, key, kids in items:
                cls = "tag-item key" if key else "tag-item"
                o.write(f'<span class="{cls}">{esc(("★" + text) if key else text)}</span>')
                for kt, _k in kids:
                    o.write(f'<span class="tag-kid">↳ {esc(kt)}</span>')
            o.write('</div></div>')
        o.write('</div>')
    return o.getvalue()


BASE = r"C:\Users\annie\WorkBuddy\2026-09-10-11-13-32\要因图培训"


def emit():
    """生成 SVG + 注入培训页面 index.html"""
    svg, stats, size, diag = build_svg()
    with open(BASE + r"\fishbone.svg", "w", encoding="utf-8") as f:
        f.write(svg)
    html = open(BASE + r"\index.src.html", encoding="utf-8").read()
    html = html.replace("<!--FISHBONE_SVG-->", svg)
    html = html.replace("<!--CATEGORY_CARDS-->", cards())
    with open(BASE + r"\index.html", "w", encoding="utf-8") as f:
        f.write(html)
    return svg, stats, size, diag


if __name__ == "__main__":
    SVG, STATS, SIZE, DIAG = emit()
    print(f"OK: {STATS['items']} 小骨, {STATS['keys']} 重点, {STATS['kids']} 小小骨, 画布 {SIZE}")
    for s in DIAG["cats"]:
        print("   ", s)
    check()
