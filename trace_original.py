# -*- coding: utf-8 -*-
"""把线层矢量化成 SVG path，并校验重绘误差。"""
import cv2, numpy as np, json

SRC = r"C:\Users\annie\.workbuddy\clipboard-images\clipboard-2026-09-10T06-14-17-795Z-ded04025.jpg"
img = cv2.imread(SRC); H, W = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

fg = ((gray < 150) | (hsv[:, :, 1] > 80)).astype(np.uint8)
fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))

dens = cv2.blur(fg.astype(np.float32), (15, 15))
tz = (dens > 0.30).astype(np.uint8)
tz = cv2.morphologyEx(tz, cv2.MORPH_CLOSE, np.ones((3, 21), np.uint8))

n, lab, st, ce = cv2.connectedComponentsWithStats(fg, 8)
line_ids, text_from_cc = [], []
for i in range(1, n):
    x, y, ww, hh, a = st[i]
    fill = a / (ww * hh)
    if a > 6000 and fill < 0.30:
        line_ids.append(i)
    elif a >= 60 and 10 <= hh <= 90:
        text_from_cc.append((int(x), int(y), int(ww), int(hh)))

big = np.isin(lab, line_ids).astype(np.uint8)
print(f"线网络 {len(line_ids)} 个连通域 / {int(big.sum())} px")
resid = cv2.bitwise_and(big, tz)
resid = cv2.morphologyEx(resid, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
line_only = cv2.bitwise_and(big, cv2.bitwise_not(resid))
print(f"线层 {int(line_only.sum())} px（含粘连文字残块 {int(resid.sum())} px）")

# 粘连在线网络里的文字块
nr, lr, sr, _ = cv2.connectedComponentsWithStats(resid, 8)
for i in range(1, nr):
    x, y, ww, hh, a = sr[i]
    if a >= 60 and 10 <= hh <= 90:
        text_from_cc.append((int(x), int(y), int(ww), int(hh)))
text_from_cc.sort(key=lambda b: (b[1] // 20, b[0]))
json.dump(text_from_cc, open("_tmp/textboxes.json", "w"), ensure_ascii=False)
print(f"文字块合计 {len(text_from_cc)} 个")

# ---- 矢量化 ----
for eps in (1.0, 1.3, 1.6, 2.0):
    cnts, hier = cv2.findContours(line_only, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    polys, tot = [], 0
    for c in cnts:
        if cv2.contourArea(c) < 4:
            continue
        ap = cv2.approxPolyDP(c, eps, True)
        polys.append(ap); tot += len(ap)
    chk = np.zeros_like(line_only)
    cv2.fillPoly(chk, [p.reshape(-1, 1, 2) for p in polys], 1)
    err = int((chk != line_only).sum())
    print(f"  eps={eps}: 轮廓 {len(polys)} 点 {tot}  重绘误差 {err}px = {err/max(int(line_only.sum()),1)*100:.2f}%")

# 用 eps=1.3 落盘
cnts, hier = cv2.findContours(line_only, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
d_all = []
for c in cnts:
    if cv2.contourArea(c) < 4:
        continue
    ap = cv2.approxPolyDP(c, 1.3, True).reshape(-1, 2)
    d_all.append("M" + "L".join(f"{x},{y}" for x, y in ap) + "Z")
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
       f'<rect width="{W}" height="{H}" fill="#fff"/>'
       f'<path d="{" ".join(d_all)}" fill="#1a1a1a" fill-rule="evenodd"/></svg>')
open("_tmp/trace_lines.svg", "w", encoding="utf-8").write(svg)
print(f"SVG 落盘 {len(svg)/1024:.0f} KB")
cv2.imwrite("_tmp/f1_lineonly.png", line_only * 255)
cv2.imwrite("_tmp/f2_redraw.png", chk * 255)

ov = img.copy(); ov[line_only > 0] = (0, 0, 255)
cv2.imwrite("_tmp/f3_overlay.png", cv2.addWeighted(img, 0.5, ov, 0.5, 0))
# 文字块标注
vb = img.copy()
for (x, y, w, h) in text_from_cc:
    cv2.rectangle(vb, (x, y), (x + w, y + h), (0, 160, 0), 1)
cv2.imwrite("_tmp/f4_textboxes.png", vb)
print("saved")
