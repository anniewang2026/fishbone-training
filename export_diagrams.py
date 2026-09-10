# -*- coding: utf-8 -*-
"""把 gen_fishbone.py 里已有的数据导出为专业绘图工具可直接打开的文件。

产出：
  1. 要因图-xmind.xmind     → XMind 打开后「结构」选「鱼骨图」，自动排版
  2. 要因图-drawio.drawio   → draw.io / diagrams.net 打开，几何位置与原图一致，文字可编辑

用法：
  python export_diagrams.py
"""
import io, json, math, os, sys, uuid, zipfile

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import gen_fishbone as G                                       # noqa: E402

TITLE_MAIN = "注塑件缺料（短射）要因分析图"
SUB = (f"标准鱼骨图 ｜ 大骨与主骨成 {G.BONE_DEG:.0f}° ｜ 中骨／小骨／小小骨 均为水平线（与主骨平行） ｜ "
       f"★=重点要因（待真因验证）")


# ============================================================ 1. XMind
def build_xmind(path):
    """XMind 2020+ (.xmind = zip: content.json + metadata.json + manifest.json)"""
    def topic(title, children=None):
        d = {"id": uuid.uuid4().hex, "class": "topic", "title": title}
        if children:
            d["children"] = {"attached": children}
        return d

    cats = []
    for cat in G.CATS:
        groups = []
        for gname, _gside, items in cat["groups"]:
            leaves = []
            for text, key, kids in items:
                label = ("★ " + text) if key else text
                leaves.append(topic(label, [topic(kt) for kt, _ in kids] or None))
            groups.append(topic(gname, leaves))
        cats.append(topic(cat["name"], groups))

    sheet_id = uuid.uuid4().hex
    root = topic("欠料（料不良）", cats)
    root["structureClass"] = "org.xmind.ui.fishbone.rightHeaded"   # 鱼头向右 = 追查原因

    content = [{
        "id": sheet_id,
        "class": "sheet",
        "title": "欠料（料不良）要因分析",
        "rootTopic": root,
        "topicPositioning": "fixed",
    }]
    metadata = {
        "creator": {"name": "WorkBuddy", "version": "1.0"},
        "activeSheetId": sheet_id,
    }
    manifest = {"file-entries": {"content.json": {}, "metadata.json": {}}}

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("content.json", json.dumps(content, ensure_ascii=False))
        z.writestr("metadata.json", json.dumps(metadata, ensure_ascii=False))
        z.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False))

    n = 1 + len(cats) + sum(len(c["groups"]) for c in G.CATS) \
        + sum(len(it) for c in G.CATS for _, _, it in c["groups"]) \
        + sum(len(k) for c in G.CATS for _, _, it in c["groups"] for _, _, k in it)
    return n


# ============================================================ 2. draw.io
FILLMAP = {"url(#gB)": "#0ea5e9", "url(#gT)": "#14b8a6", "url(#gI)": "#6366f1",
           "url(#gS)": "#475569", "url(#gHead)": "#2ab4c4", "url(#gKey)": "#3b82f6"}


def xesc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


def clean_color(c):
    return FILLMAP.get(c, c)


def build_drawio(path):
    prims, stats, size, diag = G.plan_all()
    dx, dy = diag["dx"], diag["dy"]
    W, H = size
    segs = list(diag["segs"])

    o = io.StringIO()
    o.write('<mxfile host="app.diagrams.net" agent="WorkBuddy" type="device">\n')
    o.write('<diagram id="fishbone" name="欠料要因分析">\n')
    o.write(f'<mxGraphModel dx="2000" dy="1200" grid="1" gridSize="20" guides="1" tooltips="1" '
            f'connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{W}" '
            f'pageHeight="{H}" math="0" shadow="0">\n<root>\n')
    o.write('<mxCell id="0" /><mxCell id="1" parent="0" />\n')
    o.write(f'<mxCell id="bg" value="" style="rounded=0;html=1;fillColor=#f8fbfd;'
            f'strokeColor=none;" vertex="1" parent="1"><mxGeometry x="0" y="0" '
            f'width="{W}" height="{H}" as="geometry"/></mxCell>\n')

    _seq = [0]

    def nid(pfx):
        _seq[0] += 1
        return f"{pfx}{_seq[0]}"

    def txt_cell(s, x, y, f, color, anchor="middle", bold=False, cid=""):
        cid = cid or nid("t")
        w = G.tw(s, f)
        if anchor == "middle":
            cx = x
        elif anchor == "start":
            cx = x + w / 2
        else:
            cx = x - w / 2
        cy = y - f * 0.35
        bx, by, bw, bh = cx - w / 2 - 4, cy - f * 0.8, w + 8, f * 1.6
        st = (f'text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;'
              f'fontSize={f};fontColor={color};' + ("fontStyle=1;" if bold else ""))
        o.write(f'<mxCell id="{cid}" value="{xesc(s)}" style="{st}" vertex="1" parent="1">'
                f'<mxGeometry x="{bx:.1f}" y="{by:.1f}" width="{bw:.1f}" height="{bh:.1f}" '
                f'as="geometry"/></mxCell>\n')

    li = 0
    for p in prims:
        if p[0] == "line":
            _, x1, y1, x2, y2, wdt, col, _cap = p
            owner = str(segs[li][4]) if li < len(segs) else ""
            li += 1
            arrow = "block" if owner.startswith(("SPINE", "BONE-", "LINE-")) else "none"
            fs = 1 if arrow == "block" else 0
            st = (f'edge;html=1;rounded=0;strokeColor={col};strokeWidth={wdt};'
                  f'startArrow=none;endArrow={arrow};endFill={fs};')
            o.write(f'<mxCell id="l{li}" style="{st}" edge="1" parent="1">'
                    f'<mxGeometry relative="1" as="geometry">'
                    f'<mxPoint x="{x1 + dx:.1f}" y="{y1 + dy:.1f}" as="sourcePoint"/>'
                    f'<mxPoint x="{x2 + dx:.1f}" y="{y2 + dy:.1f}" as="targetPoint"/>'
                    f'</mxGeometry></mxCell>\n')
        elif p[0] == "rect":
            _, x, y, w, h, rx, fill, stroke = p
            col = clean_color(fill)
            arc = max(0, min(50, int(rx / max(h, 1) * 100)))
            st = (f'rounded=1;arcSize={arc};html=1;fillColor={col};'
                  f'strokeColor={"none" if not stroke else stroke};whiteSpace=wrap;')
            o.write(f'<mxCell id="{nid("r")}" value="" style="{st}" '
                    f'vertex="1" parent="1"><mxGeometry x="{x + dx:.1f}" y="{y + dy:.1f}" '
                    f'width="{w:.1f}" height="{h:.1f}" as="geometry"/></mxCell>\n')
        elif p[0] == "text":
            _, x, y, s, f, c, anchor, weight = p
            txt_cell(s, x + dx, y + dy, f, c, anchor, weight == "bold")
        # poly 三角箭头 → 已由 edge 的 endArrow 表达，跳过

    # 标题
    txt_cell(TITLE_MAIN, 60, 54, 31, "#1e3a5f", "start", True, "tt1")
    txt_cell(SUB, 60, 88, 16, "#7b8ba1", "start", False, "tt2")

    o.write('</root>\n</mxGraphModel>\n</diagram>\n</mxfile>')
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(o.getvalue())
    return stats


if __name__ == "__main__":
    xm = os.path.join(BASE, "要因图-xmind.xmind")
    n = build_xmind(xm)
    print(f"[1/2] XMind   -> {os.path.basename(xm)}  ({os.path.getsize(xm)} bytes, {n} 个节点)")

    dw = os.path.join(BASE, "要因图-drawio.drawio")
    st = build_drawio(dw)
    print(f"[2/2] draw.io -> {os.path.basename(dw)}  ({os.path.getsize(dw)} bytes)")

    # 校验
    with zipfile.ZipFile(xm) as z:
        assert set(z.namelist()) == {"content.json", "metadata.json", "manifest.json"}, z.namelist()
        c = json.loads(z.read("content.json").decode("utf-8"))
        assert c[0]["rootTopic"]["structureClass"].endswith("fishbone.rightHeaded")
    import xml.etree.ElementTree as ET
    t = ET.parse(dw)
    cells = t.getroot().findall(".//mxCell")
    print(f"      xmind 校验通过 · drawio 校验通过（{len(cells)} 个图元）")
    print(f"      小骨 {st['items']} · 重点 {st['keys']} · 小小骨 {st['kids']}")
