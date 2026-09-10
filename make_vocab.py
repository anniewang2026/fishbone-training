# -*- coding: utf-8 -*-
"""把检测到的文字块裁成带编号的词汇表拼图，便于一次性读出全部内容。"""
import cv2, numpy as np, json

SRC = r"C:\Users\annie\.workbuddy\clipboard-images\clipboard-2026-09-10T06-14-17-795Z-ded04025.jpg"
img = cv2.imread(SRC)
boxes = json.load(open("_tmp/wordboxes.json"))
print("共", len(boxes), "块")

TH, PADX, COLS, PER = 38, 8, 3, 80
tiles = []
for k, (x, y, w, h) in enumerate(boxes):
    c = img[max(0, y - 2):y + h + 2, max(0, x - 3):x + w + 3].copy()
    s = TH / c.shape[0]
    c = cv2.resize(c, (max(1, int(c.shape[1] * s)), TH), interpolation=cv2.INTER_LANCZOS4)
    tiles.append(c)

for page in range((len(tiles) + PER - 1) // PER):
    chunk = tiles[page * PER:(page + 1) * PER]
    rows = (len(chunk) + COLS - 1) // COLS
    CW = 340
    canvas = np.full((rows * (TH + 16) + 10, COLS * CW + 10, 3), 255, np.uint8)
    for i, t in enumerate(chunk):
        r, c = i // COLS, i % COLS
        ox, oy = 10 + c * CW, 8 + r * (TH + 16)
        num = page * PER + i
        cv2.putText(canvas, f"{num:03d}", (ox, oy + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)
        tw = min(t.shape[1], CW - 70)
        t2 = t[:, :tw]
        canvas[oy + 2:oy + 2 + TH, ox + 62:ox + 62 + tw] = t2
        cv2.line(canvas, (ox - 2, oy), (ox - 2, oy + TH + 4), (200, 200, 200), 1)
    p = f"_tmp/vocab{page+1}.png"
    cv2.imwrite(p, canvas)
    print(p, canvas.shape)
