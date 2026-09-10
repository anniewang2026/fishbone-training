# -*- coding: utf-8 -*-
"""补充：高亮底色块 + 鱼头灰框，作为最底层。"""
import cv2, numpy as np

SRC = r"C:\Users\annie\.workbuddy\clipboard-images\clipboard-2026-09-10T06-14-17-795Z-ded04025.jpg"
img = cv2.imread(SRC); H, W = img.shape[:2]
blur = cv2.medianBlur(img, 9)
hsvb = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)
g2 = cv2.cvtColor(blur, cv2.COLOR_BGR2GRAY).astype(np.int16)
s2 = hsvb[:, :, 1].astype(np.int16)

# 非白区域（含浅色高亮 + 灰框）
hl = ((g2 < 240) | (s2 > 30)).astype(np.uint8)
# 去掉线和文字本体
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
fg = ((gray < 150) | (hsv[:, :, 1] > 80)).astype(np.uint8)
hl = cv2.bitwise_and(hl, cv2.bitwise_not(cv2.dilate(fg, np.ones((7, 7), np.uint8))))
hl = cv2.morphologyEx(hl, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
hl = cv2.morphologyEx(hl, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
nh, lh, sh, _ = cv2.connectedComponentsWithStats(hl, 8)
blocks = []
for i in range(1, nh):
    x, y, w, h, a = sh[i]
    if a < 900 or w < 22 or h < 16:
        continue
    if a / (w * h) < 0.35:
        continue
    m = (lh == i)
    b, g, r = (float(np.median(blur[:, :, k][m])) for k in range(3))
    kind = "grey" if (max(b, g, r) - min(b, g, r)) < 22 else "tint"
    blocks.append((x, y, w, h, int(r), int(g), int(b), kind, a))
blocks.sort(key=lambda t: -t[8])
print(f"高亮/底色块 {len(blocks)} 个")
for t in blocks[:8]:
    print(f"   ({t[0]:>5},{t[1]:>5}) {t[2]:>4}x{t[3]:<4} rgb({t[4]},{t[5]},{t[6]}) {t[7]} {t[8]}px")

import json
json.dump([[int(v) for v in t[:7]] + [t[7]] for t in blocks], open("_tmp/bgblocks.json", "w"))

vis = img.copy()
for (x, y, w, h, r, g, b, kind, a) in blocks:
    cv2.rectangle(vis, (x, y), (x + w, y + h), (0, 200, 0), 2)
cv2.imwrite("_tmp/bg_blocks.png", vis)
print("saved")
