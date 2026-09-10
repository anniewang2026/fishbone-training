# -*- coding: utf-8 -*-
"""生成 draw.io 空白鱼骨图骨架模板 + 预览 PNG

几何规格（标准鱼骨图）：
  主骨/中骨/小骨 —— 水平线（互相平行）
  大骨 —— 与主骨成 60°（tan60 = 1.732）
  中骨挂在大骨上、向左水平延伸（层级的走向本身就是语法）
"""
import math
from xml.sax.saxutils import escape
from PIL import Image, ImageDraw, ImageFont

OUT_DRAWIO = "fishbone-skeleton.drawio"
OUT_PREVIEW = "骨架模板-预览.png"

W, H = 1700, 1120
SPINE_Y = 550
SPINE_X0, SPINE_X1 = 120, 1290
HEAD_X, HEAD_Y, HEAD_W, HEAD_H = 1300, 480, 244, 140

TAN60 = math.tan(math.radians(60))
BONE_H = 320                      # 大骨竖直高度
BONE_DX = BONE_H / TAN60          # 水平投影 ≈ 184.7 -> 与主骨 60°
MID_LEN = 220                     # 中骨（水平）长度
TS = (0.30, 0.50, 0.70, 0.90)     # 中骨在大骨上的位置（自 主骨端 -> 顶点）

# name, 主骨附着点 x, side(-1 上 / +1 下)
BONES = [("材料", 620, -1), ("设备", 1080, -1),
         ("人", 540, +1), ("方法", 1000, +1)]

# ---------------- draw.io 样式 ----------------
ST_SPINE = "endArrow=classic;html=1;strokeWidth=3;edgeStyle=none;strokeColor=#3f5061;endSize=9;"
ST_BONE = "endArrow=none;html=1;strokeWidth=2;edgeStyle=none;strokeColor=#2f6fb5;"
ST_MID = "endArrow=classic;html=1;strokeWidth=1.4;edgeStyle=none;strokeColor=#8aa2b8;endSize=6;"
ST_SMALL = "endArrow=classic;html=1;strokeWidth=1.2;edgeStyle=none;strokeColor=#b0bfcd;endSize=5;"
ST_COLL = "endArrow=none;html=1;strokeWidth=1.2;edgeStyle=none;strokeColor=#b0bfcd;"
ST_HEAD = ("rounded=1;arcSize=16;whiteSpace=wrap;html=1;fillColor=#dbe9f8;strokeColor=#2f6fb5;"
           "strokeWidth=2;fontSize=24;fontStyle=1;fontColor=#1e3a5f;")
ST_TAG = ("rounded=1;arcSize=28;whiteSpace=wrap;html=1;fillColor=#eaf2fb;strokeColor=#2f6fb5;"
          "fontSize=17;fontStyle=1;fontColor=#1e3a5f;")

cells, _n = [], [100]


def nid(p="c"):
    _n[0] += 1
    return f"{p}{_n[0]}"


def edge(x1, y1, x2, y2, style):
    cells.append(
        f'<mxCell id="{nid("e")}" value="" style="{style}" edge="1" parent="1">'
        f'<mxGeometry relative="1" as="geometry">'
        f'<mxPoint x="{x1:.1f}" y="{y1:.1f}" as="sourcePoint"/>'
        f'<mxPoint x="{x2:.1f}" y="{y2:.1f}" as="targetPoint"/>'
        f'</mxGeometry></mxCell>')


def rect(x, y, w, h, style, label=""):
    cells.append(
        f'<mxCell id="{nid("r")}" value="{escape(label)}" style="{style}" vertex="1" parent="1">'
        f'<mxGeometry x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" as="geometry"/>'
        f'</mxCell>')


def note(x, y, w, h, text, fs=14):
    st = ("text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=top;"
          f"fontSize={fs};fontColor=#40566b;whiteSpace=wrap;")
    cells.append(
        f'<mxCell id="{nid("t")}" value="{escape(text)}" style="{st}" vertex="1" parent="1">'
        f'<mxGeometry x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" as="geometry"/>'
        f'</mxCell>')


# ---------------- 骨架 ----------------
geoms = {"spine": (SPINE_X0, SPINE_Y, SPINE_X1, SPINE_Y), "bones": [], "mids": [], "smalls": [], "coll": []}

edge(SPINE_X0, SPINE_Y, SPINE_X1, SPINE_Y, ST_SPINE)
rect(HEAD_X, HEAD_Y, HEAD_W, HEAD_H, ST_HEAD, "问题　（双击改）")

for name, fx, side in BONES:
    tx, ty = fx - BONE_DX, SPINE_Y + side * BONE_H
    edge(fx, SPINE_Y, tx, ty, ST_BONE)
    geoms["bones"].append((fx, SPINE_Y, tx, ty))

    # 类别标签贴在骨梢外侧
    lx = tx - 55
    ly = ty - 74 if side < 0 else ty + 6
    rect(lx, ly, 110, 40, ST_TAG, name)

    for t in TS:
        ax = fx - BONE_DX * t
        ay = SPINE_Y + side * BONE_H * t
        edge(ax - MID_LEN, ay, ax, ay, ST_MID)     # 中骨：向左水平，箭头指向大骨
        geoms["mids"].append((ax - MID_LEN, ay, ax, ay))

# 小骨示范：挂在「材料」大骨第 1 根中骨的末端下方
mx, my = 620 - BONE_DX * TS[0], SPINE_Y - BONE_H * TS[0]      # (564.6, 454)
cx = mx - 70
edge(cx, my, cx, my + 58, ST_COLL)
geoms["coll"].append((cx, my, cx, my + 58))
for dy in (29, 58):
    edge(cx - 108, my + dy, cx, my + dy, ST_SMALL)
    geoms["smalls"].append((cx - 108, my + dy, cx, my + dy))

# ---------------- 第二页：使用说明 ----------------
GUIDE = "".join(
    f'<mxCell id="g{i}" value="{escape(t)}" style="text;html=1;strokeColor=none;fillColor=none;'
    f'align=left;verticalAlign=top;fontSize={fs};fontColor=#2c3e50;whiteSpace=wrap;" '
    f'vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>'
    for i, (t, x, y, w, h, fs) in enumerate([
        ("用这张骨架，5 分钟画完鱼骨图", 40, 30, 760, 40, 24),
        ("【1】改文字：双击任何一个词，直接打自己的内容。大骨已填「材料 / 设备 / 人 / 方法」，改成你要的分类。", 40, 90, 780, 30, 15),
        ("【2】加中骨（水平线）：点中任意一根中骨 → Ctrl+C → Ctrl+V → 拖到新位置。", 40, 130, 780, 30, 15),
        ("【3】加小骨：小骨和中骨一样是水平线。复制一根中骨，缩短，再用一根竖线接到中骨上（见左上角示范）。", 40, 170, 780, 50, 15),
        ("【4】加一根大骨：连大骨在内的整体复制。拖端点时若线拐成直角，选中线 → 右侧「样式」→ Line 改成 Straight(直线)。", 40, 220, 780, 50, 15),
        ("【5】配色：右侧「样式」里改线条颜色和粗细，把重点要因加粗或标红。", 40, 270, 780, 30, 15),
        ("【6】画完导出：文件 → 导出为 → SVG，交给 AI 就能做成逐笔生长的动画。", 40, 310, 780, 30, 15),
        ("几何规格：主骨 / 中骨 / 小骨 全部水平（互相平行），只有大骨是 60° 斜线。这是标准鱼骨图的画法。", 40, 370, 780, 30, 14),
    ]))
guide_cells = [GUIDE]

# ---------------- 组装 mxfile ----------------
model = ('<mxGraphModel dx="1600" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" '
         'connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1700" pageHeight="1120" '
         'math="0" shadow="0"><root><mxCell id="0"/><mxCell id="1" parent="0"/>'
         + "".join(cells) + "</root></mxGraphModel>")

gmodel = ('<mxGraphModel dx="1000" dy="700" grid="1" gridSize="10" page="1" pageScale="1" '
          'pageWidth="880" pageHeight="440" math="0" shadow="0"><root><mxCell id="0"/>'
          '<mxCell id="1" parent="0"/>' + "".join(guide_cells) + "</root></mxGraphModel>")

xml = ('<mxfile host="app.diagrams.net" agent="WorkBuddy" version="24.7.17" type="device">'
       f'<diagram id="skel" name="鱼骨图骨架">{model}</diagram>'
       f'<diagram id="guide" name="使用说明">{gmodel}</diagram>'
       '</mxfile>')

with open(OUT_DRAWIO, "w", encoding="utf-8") as f:
    f.write(xml)

# ---------------- 预览渲染 ----------------
S = 0.52
iw, ih = int(W * S), int(H * S)
im = Image.new("RGB", (iw, ih), "#ffffff")
d = ImageDraw.Draw(im)
FP = "C:/Windows/Fonts/msyh.ttc"


def font(sz):
    try:
        return ImageFont.truetype(FP, int(sz * S))
    except Exception:
        return ImageFont.load_default()


def line(x1, y1, x2, y2, color, wd, arrow=False):
    d.line([x1 * S, y1 * S, x2 * S, y2 * S], fill=color, width=max(1, int(wd * S)))
    if arrow:
        ang = math.atan2(y2 - y1, x2 - x1)
        L, sp = 11 * S, 0.42
        p = [(x2 * S, y2 * S),
             (x2 * S - L * math.cos(ang - sp), y2 * S - L * math.sin(ang - sp)),
             (x2 * S - L * math.cos(ang + sp), y2 * S - L * math.sin(ang + sp))]
        d.polygon(p, fill=color)


line(SPINE_X0, SPINE_Y, SPINE_X1, SPINE_Y, "#3f5061", 3, True)
d.rounded_rectangle([HEAD_X * S, HEAD_Y * S, (HEAD_X + HEAD_W) * S, (HEAD_Y + HEAD_H) * S],
                    radius=16, fill="#dbe9f8", outline="#2f6fb5", width=2)
d.text(((HEAD_X + HEAD_W / 2) * S, (HEAD_Y + HEAD_H / 2) * S), "问题", fill="#1e3a5f",
       font=font(26), anchor="mm")

for name, fx, side in BONES:
    tx, ty = fx - BONE_DX, SPINE_Y + side * BONE_H
    line(fx, SPINE_Y, tx, ty, "#2f6fb5", 2)
    lx, ly = tx - 55, (ty - 74 if side < 0 else ty + 6)
    d.rounded_rectangle([lx * S, ly * S, (lx + 110) * S, (ly + 40) * S], radius=12,
                        fill="#eaf2fb", outline="#2f6fb5", width=2)
    d.text(((lx + 55) * S, (ly + 20) * S), name, fill="#1e3a5f", font=font(17), anchor="mm")
    for t in TS:
        ax, ay = fx - BONE_DX * t, SPINE_Y + side * BONE_H * t
        line(ax - MID_LEN, ay, ax, ay, "#8aa2b8", 1.4, True)

mx, my = 620 - BONE_DX * TS[0], SPINE_Y - BONE_H * TS[0]
cx = mx - 70
line(cx, my, cx, my + 58, "#b0bfcd", 1.2)
for dy in (29, 58):
    line(cx - 108, my + dy, cx, my + dy, "#b0bfcd", 1.2, True)

d.text((30, ih - 34), "主骨 / 中骨 / 小骨 全部水平 ｜ 大骨 60° ｜ 中骨挂在大骨上向左延伸", font=font(15))
im.save(OUT_PREVIEW)

print(f"drawio: {OUT_DRAWIO}  ({len(xml)} 字符)")
print(f"预览:   {OUT_PREVIEW}  {im.size}")
print(f"图元: 大骨{len(geoms['bones'])} 中骨{len(geoms['mids'])} 小骨{len(geoms['smalls'])} "
      f"收集线{len(geoms['coll'])} 主骨1 鱼头1")
print(f"画布: {W}x{H}")
