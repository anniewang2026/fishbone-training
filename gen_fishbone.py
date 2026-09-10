# -*- coding: utf-8 -*-
"""Generate beautified fishbone (Ishikawa) SVG + readable category cards, inject into index.src.html -> index.html"""
import re, io, sys

# ---------------- data (transcribed from original image, typos fixed) ----------------
CATS = [
    dict(name="材料", side="top", base_x=700, tip=(380, 190), col=(700, 520), limit=690, cls="b",
         groups=[
            ("性能", [("流动性差",0),("制剂添加过多",0),("未密封/氧化",0)]),
            ("材料干燥", [("干燥时间不足",0),("加料不及时",0),("设备异常",0),("定时器异常",0),("设定错误",0),("干燥温度偏低",1)]),
            ("混合材", [("未筛选",1),("粉尘多",0),("混入杂物",0),("不同材料",0),("粉碎机异常",1),("水口料",0),("刀片磨损",1)]),
            ("材质", [("吸水",0),("分解",0),("长时间外露",0),("搅拌时间短",0),("混合机异常",0),("混合比例异常",0)]),
         ]),
    dict(name="设备", side="top", base_x=1560, tip=(1330, 190), col=(1630, 560), limit=640, cls="t",
         groups=[
            ("成形机", [("螺杆磨损",1),("材质差",0),("时间长·磨损",0),("使用大吨位机器",0),("合模力大",0),("料筒磨损",1)]),
            ("模温机", [("循环水不足",0),("温度异常",0),("发热异常",0),("压力不足",0),("机水",0),("开关未开",0),("冷却系统异常",0)]),
            ("金型", [("设计不适",0),("进胶口小",0),("取数过多",0),("逸胶不平衡",0),("制品肉厚太薄",0),("配件不良",0),("尺寸不良",0),("破损",0),("堵塞",0),
                     ("清扫不及时",1),("槽深度不够",0),("位子不当",0),("温度低",0),("炭化物堵塞",0),("排气槽不良",1),("干燥剂过期失效",0),("设定错误",0),("温度异常",0),("温控失效",0),
                     ("过滤网未定期清扫",0),("过滤阀堵塞",0),("发热器不能正常发热",0)]),
            ("干燥机", [("温度异常",0),("温控失效",0),("不能正常发热",0),("发热器",0)]),
         ]),
    dict(name="人", side="bottom", base_x=700, tip=(380, 1250), col=(700, 520), limit=790, cls="i",
         groups=[
            ("作业者", [("作业手法错误",0),("工作马虎",0),("不良位置不明确",0),("品质观念不强",0)]),
            ("PQC", [("抽段数量不够",0),("未按标准作业",0)]),
            ("成型技术员", [("技术缺乏",0),("操作失误",0),("未对量产前部件进行确认",1),("未开启",0),("未废弃异常部件",1),("未按规定清扫排气槽",1)]),
            ("修模技术员", [("经验不足",0),("配件装错",0)]),
         ]),
    dict(name="方法", side="bottom", base_x=1560, tip=(1330, 1250), col=(1630, 560), limit=860, cls="s",
         groups=[
            ("金型维护", [("未按计划进行",0),("未按时进行",1),("方法错误",0),("定期保养",0),("项目不全·方法不正确",0),("日常保养",0),("保养位不全",0),("修理",0),("配件装错",0),("未按WGS作业",1)]),
            ("操作", [("开机生产部品未确认品质",0),("未按规定废弃数量",1),("未定期清洗",0),("料筒热流道清洗干净",0),("未清洗干净",0),("未废弃异常部品",1),("未确认",0),("未按下料槽",0),("异常处理",0)]),
            ("检查", [("出货检查",0),("未检查",0),("抽取数量不够",0),("未全数检查",0),("漏检",0),("外观全检",0)]),
            ("成形条件", [("温度·溶胶温度低",0),("温度·热胶位置温度低",0),("温度·金型温度低",1),("速度·计量快",0),("速度·射出速度快",1),
                        ("压力·背压力小",0),("压力·射出压力小",0),("压力·合模压力大",0),("压力·保压力小",1),
                        ("位置·计量位置小",0),("位置·射出位置小",0),("位置·保压切换位置大",1),("时间·射出时间短",1),("时间·保压时间不够",0)]),
         ]),
]

SPINE_Y = 720
BONE_DX = 320  # base_x - tip_x

# ---------------- helpers ----------------
def tw(s, font=14):
    w = 0
    for ch in s:
        w += font if ord(ch) > 0x2E00 else 8
    return w

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

TINT = {"b": ("#e0f2fe", "#0369a1"), "t": ("#ccfbf1", "#0f766e"),
        "i": ("#e0e7ff", "#4338ca"), "s": ("#e2e8f0", "#334155")}
GRAD = {"b": "gB", "t": "gT", "i": "gI", "s": "gS"}

def layout_blocks(cat):
    """Return list of blocks: dict(y, h, rows=[[chip,...]]) chip=dict(text,key,w)"""
    x0, bw = cat["col"]
    inner = bw - 24
    blocks = []
    for gname, items in cat["groups"]:
        chips = [dict(text=gname, key=-1, w=tw(gname) + 22)]
        for t, k in items:
            label = ("★" + t) if k else t
            chips.append(dict(text=label, key=k, w=tw(label) + (16 if k else 0) + 20))
        rows, cur, curw = [], [], 0
        for c in chips:
            if cur and curw + 8 + c["w"] > inner:
                rows.append(cur); cur, curw = [], 0
            cur.append(c); curw += (8 if curw else 0) + c["w"]
        if cur: rows.append(cur)
        h = len(rows) * 30 + 10
        blocks.append(dict(name=gname, rows=rows, h=h))
    total = sum(b["h"] for b in blocks) + (len(blocks) - 1) * 14
    if cat["side"] == "top":
        y = cat["limit"] - total
        if y < 40: print(f"[warn] {cat['name']} column overflows top: y={y}")
        for b in blocks: b["y"] = y; y += b["h"] + 14
    else:
        y = cat["limit"]
        for b in blocks: b["y"] = y; y += b["h"] + 14
        if y > 1460: print(f"[warn] {cat['name']} column overflows bottom: y={y}")
    return blocks

def bone_x_at(cat, yc):
    t = abs(yc - SPINE_Y) / 530.0
    t = min(max(t, 0), 1)
    return cat["base_x"] - BONE_DX * t

def build_svg():
    W, H = 2240, 1500
    o = io.StringIO()
    o.write(f'''<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="Microsoft YaHei,PingFang SC,sans-serif">
<defs>
 <linearGradient id="gB" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7dd3fc"/><stop offset="1" stop-color="#0ea5e9"/></linearGradient>
 <linearGradient id="gT" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5eead4"/><stop offset="1" stop-color="#14b8a6"/></linearGradient>
 <linearGradient id="gI" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#a5b4fc"/><stop offset="1" stop-color="#6366f1"/></linearGradient>
 <linearGradient id="gS" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#cbd5e1"/><stop offset="1" stop-color="#64748b"/></linearGradient>
 <linearGradient id="gHead" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#38bdf8"/><stop offset="1" stop-color="#14b8a6"/></linearGradient>
 <linearGradient id="gKey" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#93c5fd"/><stop offset="1" stop-color="#3b82f6"/></linearGradient>
 <filter id="ds" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="5" dy="5" stdDeviation="7" flood-color="#1e5a8c" flood-opacity="0.14"/></filter>
 <filter id="dss" x="-30%" y="-30%" width="160%" height="160%"><feDropShadow dx="3" dy="3" stdDeviation="4" flood-color="#1e5a8c" flood-opacity="0.12"/></filter>
</defs>
<rect x="0" y="0" width="{W}" height="{H}" fill="#f6fafd"/>
<text x="60" y="62" font-size="26" font-weight="bold" fill="#1e3a5f">欠料（料不良）要因分析图 · 美化版</text>
<text x="60" y="94" font-size="15" fill="#7b8ba1">冷色重排版 · 内容依据原图全量保留 · ★ = 重点要因（待真因验证）</text>
''')
    # spine + arrow + head
    o.write(f'<line x1="50" y1="{SPINE_Y}" x2="1662" y2="{SPINE_Y}" stroke="#475569" stroke-width="7" stroke-linecap="round"/>\n')
    o.write(f'<polygon points="1662,{SPINE_Y-22} 1662,{SPINE_Y+22} 1712,{SPINE_Y}" fill="#475569"/>\n')
    o.write(f'<rect x="1725" y="{SPINE_Y-67}" width="475" height="134" rx="38" fill="url(#gHead)" filter="url(#ds)"/>\n')
    o.write(f'<text x="1962" y="{SPINE_Y-8}" font-size="48" font-weight="bold" fill="#ffffff" text-anchor="middle">欠　料</text>\n')
    o.write(f'<text x="1962" y="{SPINE_Y+38}" font-size="21" fill="#ffffff" opacity="0.95" text-anchor="middle">（ 料 不 良 ）</text>\n')
    # bones + category chips
    for cat in CATS:
        tx, ty = cat["tip"]
        o.write(f'<line x1="{cat["base_x"]}" y1="{SPINE_Y}" x2="{tx}" y2="{ty}" stroke="#475569" stroke-width="5" stroke-linecap="round"/>\n')
        cy = ty - 92 if cat["side"] == "top" else ty + 30
        o.write(f'<rect x="{tx-80}" y="{cy}" width="160" height="56" rx="20" fill="url(#{GRAD[cat["cls"]]})" filter="url(#dss)"/>\n')
        o.write(f'<text x="{tx}" y="{cy+38}" font-size="25" font-weight="bold" fill="#ffffff" text-anchor="middle">{cat["name"]}</text>\n')
    # blocks
    for cat in CATS:
        x0, bw = cat["col"]
        blocks = layout_blocks(cat)
        for b in blocks:
            yc = b["y"] + b["h"] / 2
            xn = bone_x_at(cat, yc)
            o.write(f'<line x1="{xn:.0f}" y1="{yc:.0f}" x2="{x0}" y2="{yc:.0f}" stroke="#94a3b8" stroke-width="2.5"/>\n')
            o.write(f'<circle cx="{xn:.0f}" cy="{yc:.0f}" r="6" fill="#38bdf8" stroke="#ffffff" stroke-width="2"/>\n')
            o.write(f'<rect x="{x0}" y="{b["y"]}" width="{bw}" height="{b["h"]}" rx="18" fill="#ffffff" fill-opacity="0.95" stroke="#d7e3ee" filter="url(#dss)"/>\n')
            tint, tcol = TINT[cat["cls"]]
            r_y = b["y"] + 5
            for row in b["rows"]:
                cx = x0 + 12
                for c in row:
                    if c["key"] == -1:
                        o.write(f'<rect x="{cx}" y="{r_y}" width="{c["w"]}" height="26" rx="13" fill="{tint}"/>')
                        o.write(f'<text x="{cx + c["w"]/2:.0f}" y="{r_y + 17.5}" font-size="14" font-weight="bold" fill="{tcol}" text-anchor="middle">{esc(c["text"])}</text>')
                    elif c["key"] == 1:
                        o.write(f'<rect x="{cx}" y="{r_y}" width="{c["w"]}" height="26" rx="13" fill="url(#gKey)" filter="url(#dss)"/>')
                        o.write(f'<text x="{cx + c["w"]/2:.0f}" y="{r_y + 17.5}" font-size="14" font-weight="bold" fill="#ffffff" text-anchor="middle">{esc(c["text"])}</text>')
                    else:
                        o.write(f'<rect x="{cx}" y="{r_y}" width="{c["w"]}" height="26" rx="13" fill="#ffffff" stroke="#cbd5e1"/>')
                        o.write(f'<text x="{cx + c["w"]/2:.0f}" y="{r_y + 17.5}" font-size="14" fill="#475569" text-anchor="middle">{esc(c["text"])}</text>')
                    cx += c["w"] + 8
                r_y += 30
    # legend
    ly = 1462
    o.write(f'<rect x="60" y="{ly-18}" width="30" height="24" rx="12" fill="url(#gKey)"/><text x="75" y="{ly}" font-size="13" fill="#ffffff" text-anchor="middle" font-weight="bold">★</text>')
    o.write(f'<text x="100" y="{ly}" font-size="15" fill="#46586e">重点要因（待真因验证）</text>')
    o.write(f'<rect x="310" y="{ly-18}" width="30" height="24" rx="12" fill="#ffffff" stroke="#cbd5e1"/>')
    o.write(f'<text x="350" y="{ly}" font-size="15" fill="#46586e">一般可能原因</text>')
    o.write(f'<text x="490" y="{ly}" font-size="15" fill="#7b8ba1">大类：上=料·机　下=人·法（依据原图布局）</text>')
    o.write('</svg>')
    return o.getvalue()

def build_cards():
    o = io.StringIO()
    for cat in CATS:
        o.write(f'<div class="card"><div class="cat-head"><span class="cat-ico ci-{cat["cls"]}">{cat["name"]}</span>')
        keyn = sum(k for _, items in cat["groups"] for _, k in items)
        tot = sum(len(items) for _, items in cat["groups"])
        o.write(f'<span style="font-size:13px;color:#7b8ba1">{len(cat["groups"])}个中骨 · {tot}条小骨 · ★{keyn}条重点</span></div>')
        for gname, items in cat["groups"]:
            o.write(f'<div class="grp"><div class="gname">{esc(gname)}</div><div class="tags">')
            for t, k in items:
                cls = "tag-item key" if k else "tag-item"
                label = ("★" + t) if k else t
                o.write(f'<span class="{cls}">{esc(label)}</span>')
            o.write('</div></div>')
        o.write('</div>')
    return o.getvalue()

SRC = r"C:\Users\annie\WorkBuddy\2026-09-10-11-13-32\要因图培训\index.src.html"
DST = r"C:\Users\annie\WorkBuddy\2026-09-10-11-13-32\要因图培训\index.html"

with open(SRC, encoding="utf-8") as f:
    html = f.read()
html = html.replace("<!--FISHBONE_SVG-->", build_svg())
html = html.replace("<!--CATEGORY_CARDS-->", build_cards())
with open(DST, "w", encoding="utf-8") as f:
    f.write(html)
# stats
n_items = sum(len(items) for c in CATS for _, items in c["groups"])
n_key = sum(k for c in CATS for _, items in c["groups"] for _, k in items)
print(f"OK: index.html written, {len(html)} chars, {n_items} causes, {n_key} key items")
