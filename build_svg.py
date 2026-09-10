# -*- coding: utf-8 -*-
"""
1:1 复刻原图 v4 —— 三层分工
  文字掩码 = 独立文字块 + (线条网络 - 长直线)
  L1 线段 : 在「去文字的前景」上 HoughLinesP + 合并 + 采样原图实际线宽
  L2 文字 : 检测 bbox + 内容重排
  L3 残留 : 前景 - 文字 - 线带 = 箭头/短刺，原样矢量化
"""
import cv2, numpy as np, json, os, math

SRC = r"C:\Users\annie\.workbuddy\clipboard-images\clipboard-2026-09-10T06-14-17-795Z-ded04025.jpg"
img = cv2.imread(SRC); H, W = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
fg = ((gray < 150) | (hsv[:, :, 1] > 80)).astype(np.uint8)
fgc = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
K5 = np.ones((5, 5), np.uint8); K3 = np.ones((3, 3), np.uint8)

# ================= 文字像素掩码 =================
n, lab, st, _ = cv2.connectedComponentsWithStats(fgc, 8)
line_ids = [i for i in range(1, n)
            if st[i][4] > 6000 and st[i][4] / max(st[i][2] * st[i][3], 1) < 0.30]
textmask = np.zeros_like(fg)
for i in range(1, n):
    if i in line_ids or st[i][4] < 40:
        continue
    x, y, w, h, a = st[i]
    if 8 <= h <= 150 and w <= 900:
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
    if sbt[i][4] >= 30:
        textmask[lt == i] = 1
print(f"文字像素 {free_px} + 线上粘连 {int(textmask.sum()) - free_px} = {int(textmask.sum())}")

# ================= L1 线段 =================
fl = cv2.bitwise_and(fg, cv2.bitwise_not(cv2.dilate(textmask, K3)))
raw = cv2.HoughLinesP(fl * 255, 1, np.pi / 720, 42, minLineLength=30, maxLineGap=12)
segs = [tuple(int(v) for v in s) for s in np.asarray(raw).reshape(-1, 4)]
print("Hough 原始", len(segs))

def dirv(x1, y1, x2, y2):
    a = math.radians(math.degrees(math.atan2(y2 - y1, x2 - x1)) % 180)
    if a > math.pi / 2:
        a -= math.pi
    return math.cos(a), math.sin(a)

segs = [(x1, y1, x2, y2, *dirv(x1, y1, x2, y2), math.hypot(x2 - x1, y2 - y1))
        for (x1, y1, x2, y2) in segs]
segs.sort(key=lambda s: -s[6])
COS8 = math.cos(math.radians(8))
merged = []
for (x1, y1, x2, y2, ux, uy, L) in segs:
    ax, ay = (x1 + x2) / 2, (y1 + y2) / 2
    hit = None
    for m in merged:
        if abs(m["ux"] * ux + m["uy"] * uy) < COS8:
            continue
        if abs((ax - m["ax"]) * -m["uy"] + (ay - m["ay"]) * m["ux"]) > 9:
            continue
        p1 = (x1 - m["ax"]) * m["ux"] + (y1 - m["ay"]) * m["uy"]
        p2 = (x2 - m["ax"]) * m["ux"] + (y2 - m["ay"]) * m["uy"]
        lo, hi = min(p1, p2), max(p1, p2)
        if hi < m["lo"] - 32 or lo > m["hi"] + 32:
            continue
        hit = (m, lo, hi); break
    if hit:
        m, lo, hi = hit
        m["lo"] = min(m["lo"], lo); m["hi"] = max(m["hi"], hi)
    else:
        merged.append(dict(ax=ax, ay=ay, ux=ux, uy=uy, lo=-L / 2, hi=L / 2))

LINES = []
for m in merged:
    L = m["hi"] - m["lo"]
    if L < 44:
        continue
    x1 = m["ax"] + m["lo"] * m["ux"]; y1 = m["ay"] + m["lo"] * m["uy"]
    x2 = m["ax"] + m["hi"] * m["ux"]; y2 = m["ay"] + m["hi"] * m["uy"]
    px, py = -m["uy"], m["ux"]
    ws = []
    for t in np.linspace(0.15, 0.85, 7):
        sx, sy = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
        c = 0
        for u in np.arange(-11, 11.01, 0.5):
            qx, qy = int(round(sx + px * u)), int(round(sy + py * u))
            if 0 <= qx < W and 0 <= qy < H and fl[qy, qx]:
                c += 1
        ws.append(c * 0.5)
    wd = float(np.median(ws)) if ws else 4.0
    if wd < 1.2:
        continue
    LINES.append((x1, y1, x2, y2, max(2.2, min(wd, 12.0)), L))
print(f"合并后线段 {len(LINES)} 条（线宽 {min(l[4] for l in LINES):.1f}~{max(l[4] for l in LINES):.1f}）")

# ================= L3 残留 =================
used = cv2.dilate(textmask, K5)
for (x1, y1, x2, y2, wd, L) in LINES:
    cv2.line(used, (int(x1), int(y1)), (int(x2), int(y2)), 1, max(3, int(wd) + 2))
resid = cv2.bitwise_and(fg, cv2.bitwise_not(used))
resid = cv2.morphologyEx(resid, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
nz, lz, sz, _ = cv2.connectedComponentsWithStats(resid, 8)
keepz = np.zeros_like(resid); na = 0
for i in range(1, nz):
    if sz[i][4] < 24 or sz[i][4] > 1500:
        continue
    keepz[lz == i] = 1; na += 1
print(f"残留块 {na} 个 / {int(keepz.sum())} px")
cz, _ = cv2.findContours(keepz, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
d_res = []
for c in cz:
    if cv2.contourArea(c) < 8:
        continue
    ap = cv2.approxPolyDP(c, 0.7, True).reshape(-1, 2)
    d_res.append("M" + "L".join(f"{x},{y}" for x, y in ap) + "Z")

# ================= L2 文字 =================
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
print(f"文字 {len(texts)} 条")

FONT = "'Microsoft YaHei','Source Han Sans SC','PingFang SC','Noto Sans CJK SC',sans-serif"
o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="{FONT}">',
     f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
     '<g stroke="#1c1c1c" stroke-linecap="round">']
for (x1, y1, x2, y2, wd, L) in LINES:
    o.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke-width="{wd:.1f}"/>')
o.append('</g>')
o.append(f'<path d="{" ".join(d_res)}" fill="#1c1c1c" fill-rule="evenodd"/>')
for (x, y, w, h, t, c, fs) in texts:
    if t == "成型不良":
        for k, ch in enumerate(t):
            o.append(f'<text x="{x + 20}" y="{y + 92 * (k + 1)}" font-size="88" fill="{c}">{ch}</text>')
    else:
        o.append(f'<text x="{x}" y="{y + h}" font-size="{fs:.1f}" fill="{c}">{t}</text>')
o.append('</svg>')
open("复刻-原图.svg", "w", encoding="utf-8").write("\n".join(o))
print(f"SVG {os.path.getsize('复刻-原图.svg')/1024:.0f} KB")

# ================= 预览 =================
from PIL import Image, ImageDraw, ImageFont
pim = Image.new("RGB", (W, H), (255, 255, 255))
d = ImageDraw.Draw(pim)
for (x1, y1, x2, y2, wd, L) in LINES:
    d.line([(x1, y1), (x2, y2)], fill=(28, 28, 28), width=max(1, int(round(wd))))
rz = np.zeros((H, W, 3), np.uint8); rz[keepz > 0] = (28, 28, 28)
mask = Image.fromarray(cv2.cvtColor(rz, cv2.COLOR_BGR2RGB)).convert("L").point(lambda v: 255 if v > 20 else 0)
pim.paste((28, 28, 28), (0, 0), mask)
CMAP = {"#1a1a1a": (26, 26, 26), "#e0356e": (224, 53, 110), "#1b4fa0": (27, 79, 160), "#3a3a3a": (58, 58, 58)}
for (x, y, w, h, t, c, fs) in texts:
    f = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", max(8, int(round(fs))))
    if t == "成型不良":
        for k, ch in enumerate(t):
            d.text((x + 20, y + 92 * (k + 1)), ch, font=f, fill=CMAP[c], anchor="ls")
    else:
        d.text((x, y + h), t, font=f, fill=CMAP[c], anchor="ls")
pim.save("复刻-预览.png")
cv2.imwrite("_tmp/g2_textmask.png", textmask * 255)
print("预览", pim.size)
