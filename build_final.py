# -*- coding: utf-8 -*-
"""
1:1 复刻原图（最终）—— 四层
  L0 底色 : 标签高亮底 + 鱼头灰框
  L1 线条 : 前景 - 文字像素  →  整体矢量化（原样保留每根线/箭头/短刺）
  L2 文字 : 原图检测位置 + 内容重排
"""
import cv2, numpy as np, json, os, math

SRC = r"C:\Users\annie\.workbuddy\clipboard-images\clipboard-2026-09-10T06-14-17-795Z-ded04025.jpg"
img = cv2.imread(SRC); H, W = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
fg = ((gray < 150) | (hsv[:, :, 1] > 80)).astype(np.uint8)
fgc = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
K3 = np.ones((3, 3), np.uint8); K5 = np.ones((5, 5), np.uint8)

# ============ 文字像素掩码 ============
n, lab, st, _ = cv2.connectedComponentsWithStats(fgc, 8)
line_ids = [i for i in range(1, n)
            if st[i][4] > 6000 and st[i][4] / max(st[i][2] * st[i][3], 1) < 0.30]
textmask = np.zeros_like(fg)
for i in range(1, n):
    if i in line_ids or st[i][4] < 40:
        continue
    x, y, w, h, a = st[i]
    if not (8 <= h <= 150 and w <= 900):
        continue
    if max(w, h) / max(min(w, h), 1) > 4.2 and min(w, h) <= 13:   # 细长 -> 是线
        continue
    if a / max(w * h, 1) < 0.30 and max(w, h) > 42:
        continue
    if max(w, h) > 150 and h <= 14:
        continue
    textmask[lab == i] = 1
free_px = int(textmask.sum())

big = np.isin(lab, line_ids).astype(np.uint8)
hb = cv2.morphologyEx(big, cv2.MORPH_OPEN, np.ones((1, 41), np.uint8))
vb = cv2.morphologyEx(big, cv2.MORPH_OPEN, np.ones((41, 1), np.uint8))
rawb = cv2.HoughLinesP(big * 255, 1, np.pi / 360, 40, minLineLength=70, maxLineGap=18)
db = np.zeros_like(big)
if rawb is not None:
    for s in np.asarray(rawb).reshape(-1, 4):
        x1, y1, x2, y2 = (int(v) for v in s)
        ang = abs(math.degrees(math.atan2(y2 - y1, x2 - x1))) % 180
        if 20 < ang < 160:
            cv2.line(db, (x1, y1), (x2, y2), 1, 13)
lines_in_big = cv2.bitwise_or(cv2.bitwise_or(hb, vb), db)
tib = cv2.bitwise_and(big, cv2.bitwise_not(cv2.dilate(lines_in_big, K5)))
tib = cv2.morphologyEx(tib, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
nt, lt, sbt, _ = cv2.connectedComponentsWithStats(tib, 8)
for i in range(1, nt):
    x, y, w, h, a = sbt[i]
    if a < 30:
        continue
    if a / max(w * h, 1) < 0.30 and max(w, h) > 42:
        continue
    if max(w, h) / max(min(w, h), 1) > 4.5 and min(w, h) <= 13:
        continue
    textmask[lt == i] = 1
print(f"文字像素 {int(textmask.sum())}（独立 {free_px}）")

# ============ L0 底色 ============
blur = cv2.medianBlur(img, 9)
hsvb = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)
g2 = cv2.cvtColor(blur, cv2.COLOR_BGR2GRAY).astype(np.int16)
hl = (((g2 < 240) | (hsvb[:, :, 1] > 30))).astype(np.uint8)
hl = cv2.bitwise_and(hl, cv2.bitwise_not(cv2.dilate(fg, np.ones((7, 7), np.uint8))))
hl = cv2.morphologyEx(hl, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
hl = cv2.morphologyEx(hl, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
nh, lh, sh, _ = cv2.connectedComponentsWithStats(hl, 8)
BG = []
for i in range(1, nh):
    x, y, w, h, a = sh[i]
    if a < 900 or w < 22 or h < 16 or a / (w * h) < 0.35:
        continue
    m = (lh == i)
    b, g, r = (int(np.median(blur[:, :, k][m])) for k in range(3))
    BG.append((int(x), int(y), int(w), int(h), r, g, b))
BG.sort(key=lambda t: -t[2] * t[3])
print(f"底色块 {len(BG)} 个")

# ============ L1 线条 ============
fl = cv2.bitwise_and(fg, cv2.bitwise_not(cv2.dilate(textmask, K3)))
fl = cv2.morphologyEx(fl, cv2.MORPH_CLOSE, K3)
fl = cv2.morphologyEx(fl, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
nl, ll, sl, _ = cv2.connectedComponentsWithStats(fl, 8)
keep = np.zeros_like(fl)
for i in range(1, nl):
    if sl[i][4] >= 22:
        keep[ll == i] = 1
print("线层像素", int(keep.sum()))
cnts, _ = cv2.findContours(keep, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
d_line, npts = [], 0
for c in cnts:
    if cv2.contourArea(c) < 6:
        continue
    ap = cv2.approxPolyDP(c, 0.9, True).reshape(-1, 2)
    if len(ap) < 3:
        continue
    npts += len(ap)
    d_line.append("M" + "L".join(f"{x},{y}" for x, y in ap) + "Z")
print(f"轮廓 {len(d_line)} 段 / {npts} 点")

# ============ L2 文字 ============
boxes = json.load(open("_tmp/wordboxes.json"))
from labels import LABELS

def color_of(x, y, w, h):
    m = fg[y:y + h, x:x + w] > 0
    if m.sum() < 6:
        return "#1a1a1a"
    hs = hsv[y:y + h, x:x + w]
    hh = np.median(hs[:, :, 0][m]); ss = np.median(hs[:, :, 1][m])
    if ss < 60:
        return "#1a1a1a"
    if hh < 12 or hh > 145:
        return "#e0356e"
    if 95 < hh < 135:
        return "#1b4fa0"
    return "#1a1a1a"

texts = []
for i, (x, y, w, h) in enumerate(boxes):
    t = LABELS.get(i, "").strip()
    if not t:
        continue
    nch = len([c for c in t if c not in " ·／/"])
    fs = min(h * 1.32, (w / max(nch, 1)) * 1.12, 34.0)
    texts.append((x, y, w, h, t, color_of(x, y, w, h), max(9.0, fs)))
texts.append((1478, 330, 108, 92, "成型不良", "#3a3a3a", 88.0))

FONT = "'Microsoft YaHei','Source Han Sans SC','PingFang SC','Noto Sans CJK SC',sans-serif"
o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="{FONT}">',
     f'<rect width="{W}" height="{H}" fill="#ffffff"/>']
# L0 鱼头框（手工补全）
o.append('<rect x="1572" y="288" width="108" height="292" rx="14" fill="#d9d9d9" stroke="#8a8a8a" stroke-width="2.5"/>')
for (x, y, w, h, r, g, b) in BG:
    o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="rgb({r},{g},{b})" fill-opacity="0.92"/>')
# L1
o.append(f'<path d="{" ".join(d_line)}" fill="#1c1c1c" fill-rule="evenodd"/>')
# L2
for (x, y, w, h, t, c, fs) in texts:
    if t == "成型不良":
        for k, ch in enumerate(t):
            o.append(f'<text x="{x + 18}" y="{y + 92 * (k + 1)}" font-size="86" fill="{c}">{ch}</text>')
    else:
        o.append(f'<text x="{x}" y="{y + h}" font-size="{fs:.1f}" fill="{c}">{t}</text>')
o.append('</svg>')
open("复刻-原图.svg", "w", encoding="utf-8").write("\n".join(o))
print(f"SVG {os.path.getsize('复刻-原图.svg')/1024:.0f} KB  文字 {len(texts)} 条")

# ============ 预览 ============
from PIL import Image, ImageDraw, ImageFont
pim = Image.new("RGB", (W, H), (255, 255, 255))
d = ImageDraw.Draw(pim)
d.rounded_rectangle([1572, 288, 1572 + 108, 288 + 292], radius=14, fill=(217, 217, 217), outline=(138, 138, 138), width=3)
for (x, y, w, h, r, g, b) in BG:
    d.rounded_rectangle([x, y, x + w, y + h], radius=10, fill=(r, g, b))
rz = np.zeros((H, W, 3), np.uint8); rz[keep > 0] = (30, 30, 30)
mk = Image.fromarray(cv2.cvtColor(rz, cv2.COLOR_BGR2RGB)).convert("L").point(lambda v: 255 if v > 20 else 0)
pim.paste((30, 30, 30), (0, 0), mk)
CMAP = {"#1a1a1a": (26, 26, 26), "#e0356e": (224, 53, 110), "#1b4fa0": (27, 79, 160), "#3a3a3a": (58, 58, 58)}
for (x, y, w, h, t, c, fs) in texts:
    f = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", max(8, int(round(fs))))
    if t == "成型不良":
        for k, ch in enumerate(t):
            d.text((x + 18, y + 92 * (k + 1)), ch, font=f, fill=CMAP[c], anchor="ls")
    else:
        d.text((x, y + h), t, font=f, fill=CMAP[c], anchor="ls")
pim.save("复刻-预览.png")
print("预览", pim.size)
