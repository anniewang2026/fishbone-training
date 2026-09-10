# -*- coding: utf-8 -*-
"""词级文字块检测 v2：连通域 + 行内邻近合并（垂直重叠且水平间隙小才合）。"""
import cv2, numpy as np, json

SRC = r"C:\Users\annie\.workbuddy\clipboard-images\clipboard-2026-09-10T06-14-17-795Z-ded04025.jpg"
img = cv2.imread(SRC); H, W = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
fg = ((gray < 150) | (hsv[:, :, 1] > 80)).astype(np.uint8)
fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
dens = cv2.blur(fg.astype(np.float32), (15, 15))
tz = cv2.morphologyEx((dens > 0.30).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 33), np.uint8))

n, lab, st, _ = cv2.connectedComponentsWithStats(fg, 8)
line_ids = set(i for i in range(1, n)
               if st[i][4] > 6000 and st[i][4] / max(st[i][2] * st[i][3], 1) < 0.30)

parts = []
def add(x, y, w, h, a):
    if a < 28 or h < 11 or h > 88 or w < 6 or w > 420:
        return
    if a / max(w * h, 1) > 0.90 and 12 < min(w, h) and max(w, h) < 26:
        return                                   # 方形实心 = 噪点/箭头
    parts.append([int(x), int(y), int(x + w), int(y + h)])

for i in range(1, n):
    if i in line_ids:
        continue
    x, y, w, h, a = st[i]; add(x, y, w, h, a)

big = np.isin(lab, list(line_ids)).astype(np.uint8)
resid = cv2.bitwise_and(big, tz)
nr, lr, sr, _ = cv2.connectedComponentsWithStats(resid, 8)
for i in range(1, nr):
    add(*sr[i])
print(f"原子块 {len(parts)} 个")

# 行内邻近合并
GAPX = 17
used = [False] * len(parts)
groups = []
order = sorted(range(len(parts)), key=lambda i: (parts[i][1], parts[i][0]))
for i in order:
    if used[i]:
        continue
    g = list(parts[i]); used[i] = True
    changed = True
    while changed:
        changed = False
        for j in order:
            if used[j]:
                continue
            q = parts[j]
            vo = min(g[3], q[3]) - max(g[1], q[1])
            if vo < 0.55 * min(g[3] - g[1], q[3] - q[1]):
                continue
            gap = max(g[0], q[0]) - min(g[2], q[2])
            if gap > GAPX:
                continue
            g = [min(g[0], q[0]), min(g[1], q[1]), max(g[2], q[2]), max(g[3], q[3])]
            used[j] = True
            changed = True
    groups.append(g)

boxes = [(x, y, x2 - x, y2 - y) for (x, y, x2, y2) in groups
         if (x2 - x) >= 18 and 11 <= (y2 - y) <= 88 and (x2 - x) <= 780]
boxes.sort(key=lambda b: (b[1] // 20, b[0]))
print(f"词级文字块 {len(boxes)} 个 | 宽中位 {np.median([b[2] for b in boxes]):.0f} 高中位 {np.median([b[3] for b in boxes]):.0f}")
json.dump(boxes, open("_tmp/wordboxes.json", "w"), ensure_ascii=False)

vb = img.copy()
for (x, y, w, h) in boxes:
    cv2.rectangle(vb, (x, y), (x + w, y + h), (0, 170, 0), 2)
cv2.imwrite("_tmp/w2_boxes.png", vb)
print("saved")
