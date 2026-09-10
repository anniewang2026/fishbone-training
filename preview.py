# -*- coding: utf-8 -*-
"""用 PIL 把 gen_fishbone 的图元渲染成 PNG 预览（不依赖浏览器/SVG 渲染器）

用途：验证布局是否正确、动画分段是否合理。
用法: python preview.py [最大步骤号]   # 只画 step<=N 的图元；省略则画全部
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import gen_fishbone as G                                       # noqa: E402

FONTS = {}
def font(sz):
    if sz not in FONTS:
        FONTS[sz] = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", int(round(sz)))
    return FONTS[sz]

GRAD = {"url(#gB)": "#0ea5e9", "url(#gT)": "#14b8a6", "url(#gI)": "#6366f1",
        "url(#gS)": "#475569", "url(#gHead)": "#2ab4c4", "url(#gKey)": "#e11d48"}


def render(step_max=None, scale=0.32, out="preview_full.png", head=None, head_sub=None):
    if head is not None:
        G.HEAD_TEXT, G.HEAD_SUB = head, head_sub
    prims, stats, size, diag = G.plan_all()
    W, H = size
    dx, dy = diag["dx"], diag["dy"]
    steps = diag["steps"]
    w, h = int(W * scale), int(H * scale)
    im = Image.new("RGB", (w, h), "#f8fbfd")
    d = ImageDraw.Draw(im)

    def S(v):
        return v * scale

    d.text((S(60), S(30)), f"{G.HEAD_TEXT}{G.HEAD_SUB}　要因分析图", fill="#1e3a5f", font=font(34 * scale))

    for p, s in zip(prims, steps):
        if step_max is not None and s > step_max:
            continue
        if p[0] == "line":
            _, x1, y1, x2, y2, wd, c, _cap = p
            d.line([S(x1 + dx), S(y1 + dy), S(x2 + dx), S(y2 + dy)], fill=c,
                   width=max(1, int(round(wd * scale))))
        elif p[0] == "poly":
            pts = [(S(q[0] + dx), S(q[1] + dy)) for q in p[1]]
            d.polygon(pts, fill=GRAD.get(p[2], p[2]))
        elif p[0] == "rect":
            _, x, y, rw, rh, rx, fill, stroke = p
            col = GRAD.get(fill, fill)
            box = [S(x + dx), S(y + dy), S(x + dx + rw), S(y + dy + rh)]
            try:
                d.rounded_rectangle(box, radius=S(rx), fill=col,
                                    outline="#ffffff" if stroke else None)
            except Exception:
                d.rectangle(box, fill=col)
        else:
            _, x, y, txt, f, c, anchor, weight = p
            try:
                anch = {"middle": "ms", "start": "ls", "end": "rs"}[anchor]
                d.text((S(x + dx), S(y + dy)), txt, fill=c, font=font(f * scale), anchor=anch)
            except Exception:
                pass
    im.save(os.path.join(BASE, out))
    return os.path.join(BASE, out), (w, h), stats


if __name__ == "__main__":
    args = sys.argv[1:]
    sm = int(args[0]) if args and args[0] != "-" else None
    p, wh, st = render(sm, out=("preview_full.png" if sm is None else f"preview_step{sm}.png"))
    print("OK", p, wh, st)
