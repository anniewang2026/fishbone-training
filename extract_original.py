# -*- coding: utf-8 -*-
"""
把原图分层剥离：色块层 / 线层（含箭头、边框）/ 文字层。
目的：拿到原图 1:1 的线条几何，作为重建底稿。
"""
import cv2, numpy as np, json, os, sys

SRC = os.environ.get("SRC") or r"C:\Users\annie\.workbuddy\clipboard-images\clipboard-2026-09-10T06-14-17-795Z-ded04025.jpg"
OUT = "_tmp"
os.makedirs(OUT, exist_ok=True)

img = cv2.imread(SRC)
H, W = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
sat = hsv[:, :, 1]

# ---------- 1) 前景：暗（黑线黑字）或 高饱和（红/蓝字） ----------
fg = ((gray < 150) | (sat > 80)).astype(np.uint8)
fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
print(f"[1] 前景占比 {fg.mean()*100:.1f}%")

# ---------- 2) 局部密度 -> 文字区掩码 ----------
dens = cv2.blur(fg.astype(np.float32), (15, 15))
tz = (dens > 0.30).astype(np.uint8)
tz = cv2.morphologyEx(tz, cv2.MORPH_CLOSE, np.ones((3, 33), np.uint8))   # 横向把字连成行
tz = cv2.morphologyEx(tz, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
print(f"[2] 文字区占比 {tz.mean()*100:.1f}%")

# ---------- 3) 线层 = 前景 - 文字区 ----------
lines = cv2.bitwise_and(fg, cv2.bitwise_not(tz))
lines = cv2.morphologyEx(lines, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
print(f"[3] 线层占比 {lines.mean()*100:.2f}%  ({lines.sum()} px)")

# ---------- 4) 文字块 bbox ----------
n, lab, st, ce = cv2.connectedComponentsWithStats(tz, 8, cv2.CV_32S)
boxes = []
for i in range(1, n):
    x, y, ww, hh, area = st[i]
    if area < 120 or hh < 12 or hh > 90 or ww > 700:
        continue
    boxes.append((int(x), int(y), int(ww), int(hh)))
boxes.sort(key=lambda b: (b[1] // 22, b[0]))
print(f"[4] 文字行块 {len(boxes)} 个（宽中位 {np.median([b[2] for b in boxes]):.0f} 高中位 {np.median([b[3] for b in boxes]):.0f}）")

# ---------- 5) 保存调试图 ----------
cv2.imwrite(f"{OUT}/e1_fg.png", fg * 255)
cv2.imwrite(f"{OUT}/e2_textzone.png", tz * 255)
cv2.imwrite(f"{OUT}/e3_lines.png", lines * 255)

ov = img.copy()
ov[lines > 0] = (0, 0, 255)                    # 线层 = 红
vis = cv2.addWeighted(img, 0.45, ov, 0.55, 0)
cv2.imwrite(f"{OUT}/e4_overlay.png", vis)

json.dump(boxes, open(f"{OUT}/textboxes.json", "w"), ensure_ascii=False)
print("[5] 调试图已存", OUT)
