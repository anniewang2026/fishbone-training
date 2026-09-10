# -*- coding: utf-8 -*-
"""直接用「前景 - 文字区」得到的线层矢量化，测精度。"""
import cv2, numpy as np

SRC = r"C:\Users\annie\.workbuddy\clipboard-images\clipboard-2026-09-10T06-14-17-795Z-ded04025.jpg"
img = cv2.imread(SRC); H, W = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
fg = ((gray < 150) | (hsv[:, :, 1] > 80)).astype(np.uint8)
fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))

dens = cv2.blur(fg.astype(np.float32), (15, 15))
tz = (dens > 0.30).astype(np.uint8)
tz = cv2.morphologyEx(tz, cv2.MORPH_CLOSE, np.ones((3, 33), np.uint8))
tz = cv2.morphologyEx(tz, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
lines = cv2.bitwise_and(fg, cv2.bitwise_not(tz))
lines = cv2.morphologyEx(lines, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
print("线层 px:", int(lines.sum()), " 占比 %.2f%%" % (lines.mean() * 100))

# 去掉孤立小噪点
nl, ll, sl, _ = cv2.connectedComponentsWithStats(lines, 8)
keep = np.zeros_like(lines)
kept = 0
for i in range(1, nl):
    x, y, w, h, a = sl[i]
    if a < 25:
        continue
    if a / (w * h) > 0.85 and max(w, h) < 22 and min(w, h) > 12:
        continue                       # 方形实心小块 = 残余汉字点
    keep[ll == i] = 1; kept += 1
print(f"保留连通块 {kept} 个 / {int(keep.sum())} px")

for eps in (0.6, 0.8, 1.0, 1.3):
    cnts, hier = cv2.findContours(keep, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    polys, tot = [], 0
    for c in cnts:
        if cv2.contourArea(c) < 3:
            continue
        ap = cv2.approxPolyDP(c, eps, True)
        polys.append(ap); tot += len(ap)
    chk = np.zeros_like(keep)
    cv2.fillPoly(chk, [p.reshape(-1, 1, 2) for p in polys], 1)
    err = int((chk != keep).sum())
    print(f"  eps={eps}: 轮廓{len(polys)} 点{tot} 误差 {err}px = {err/max(int(keep.sum()),1)*100:.2f}%")

ov = img.copy(); ov[keep > 0] = (0, 0, 255)
cv2.imwrite("_tmp/t2_overlay.png", cv2.addWeighted(img, 0.5, ov, 0.5, 0))
cv2.imwrite("_tmp/t2_lines.png", keep * 255)
print("saved")
