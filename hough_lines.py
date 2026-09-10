# -*- coding: utf-8 -*-
"""用 HoughLinesP 提取原图全部直线段（大骨/主骨/中骨/小骨/箭头），聚类合并后输出。"""
import cv2, numpy as np, json, math

SRC = r"C:\Users\annie\.workbuddy\clipboard-images\clipboard-2026-09-10T06-14-17-795Z-ded04025.jpg"
img = cv2.imread(SRC); H, W = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
fg = ((gray < 150) | (hsv[:, :, 1] > 80)).astype(np.uint8)
fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
print("前景", int(fg.sum()))

raw = cv2.HoughLinesP(fg * 255, 1, np.pi / 360, threshold=42,
                      minLineLength=48, maxLineGap=9)
print("Hough 原始段:", 0 if raw is None else len(raw))
segs = [tuple(int(v) for v in s) for s in np.asarray(raw).reshape(-1, 4)]

# --- 聚类合并：同方向、法向距离近、且投影区间重叠/相邻 ---
def norm(s):
    x1, y1, x2, y2 = s
    if (x1, y1) > (x2, y2):
        x1, y1, x2, y2 = x2, y2, x1, y1
    ang = math.degrees(math.atan2(y2 - y1, x2 - x1)) % 180
    if ang > 90:
        ang -= 180
    L = math.hypot(x2 - x1, y2 - y1)
    return x1, y1, x2, y2, ang, L

segs = [norm(s) for s in segs]
segs.sort(key=lambda s: -s[5])
merged = []
for s in segs:
    x1, y1, x2, y2, ang, L = s
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    placed = False
    for m in merged:
        if abs(m["ang"] - ang) > 6:
            continue
        # 中点到 m 所在直线的距离
        dx, dy = m["ux"], m["uy"]
        d = abs((cx - m["cx"]) * -dy + (cy - m["cy"]) * dx)
        if d > 7:
            continue
        # 投影重叠检查
        p1 = (x1 - m["cx"]) * dx + (y1 - m["cy"]) * dy
        p2 = (x2 - m["cx"]) * dx + (y2 - m["cy"]) * dy
        lo, hi = min(p1, p2), max(p1, p2)
        if hi < -L or lo > m["half"] + 30:
            continue
        # 合并
        m["lo"] = min(m["lo"], lo); m["hi"] = max(m["hi"], hi)
        m["cx"] = m["cx"] + (lo + hi) / 2 * dx
        m["cy"] = m["cy"] + (lo + hi) / 2 * dy
        m["half"] = (m["hi"] - m["lo"]) / 2
        placed = True
        break
    if not placed:
        a = math.radians(ang)
        merged.append(dict(ang=ang, ux=math.cos(a), uy=math.sin(a),
                           cx=cx, cy=cy, lo=-L / 2, hi=L / 2, half=L / 2))

final = []
for m in merged:
    p1 = (m["cx"] + m["lo"] * m["ux"], m["cy"] + m["lo"] * m["uy"])
    p2 = (m["cx"] + m["hi"] * m["ux"], m["cy"] + m["hi"] * m["uy"])
    L = m["hi"] - m["lo"]
    if L < 42:
        continue
    final.append((round(p1[0]), round(p1[1]), round(p2[0]), round(p2[1]),
                  round(m["ang"], 1), round(L)))
final.sort(key=lambda s: -s[5])
print(f"合并后线段 {len(final)} 条（L>=42）")
hist = {}
for s in final:
    a = s[4]
    key = "水平" if abs(a) < 8 else ("垂直" if abs(abs(a) - 90) < 8 else f"{int(a//15)*15}~{int(a//15)*15+15}°")
    hist[key] = hist.get(key, 0) + 1
print("角度分布:", dict(sorted(hist.items(), key=lambda kv: -kv[1])))
print("最长 15 条:")
for s in final[:15]:
    print(f"   ({s[0]:>5},{s[1]:>5}) -> ({s[2]:>5},{s[3]:>5})  角{s[4]:>7}  长{s[5]:>5}")

json.dump(final, open("_tmp/segments.json", "w"))

# 渲染对比
vis = np.full((H, W, 3), 255, np.uint8)
for (x1, y1, x2, y2, a, L) in final:
    cv2.line(vis, (x1, y1), (x2, y2), (0, 0, 0), 4, cv2.LINE_AA)
cv2.imwrite("_tmp/h1_redraw.png", vis)
ov = img.copy()
for (x1, y1, x2, y2, a, L) in final:
    cv2.line(ov, (x1, y1), (x2, y2), (0, 0, 255), 2, cv2.LINE_AA)
cv2.imwrite("_tmp/h2_overlay.png", ov)
print("saved")
