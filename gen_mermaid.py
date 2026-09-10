# -*- coding: utf-8 -*-
"""从 gen_fishbone.py 数据源生成 Mermaid ishikawa-beta 文本

Mermaid v11.12.3+ 起支持 ishikawa-beta：层级完全由缩进决定
  第 1 行  = 问题（鱼头）
  缩进 1 级 = 大骨
  缩进 2 级 = 中骨
  缩进 3 级 = 小骨
  缩进 4 级 = 小小骨

用法: python gen_mermaid.py
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import gen_fishbone as G                                       # noqa: E402

IND = "    "                                                   # 4 空格
HEAD = f"{G.HEAD_TEXT}（短射）"

# ---------------------------------------------------------------- 大骨排布
# 目标：像手绘原图那样，大骨分列脊骨上下两侧。
# Mermaid 的 ishikawa-beta 不支持直接指定「哪根朝上」，实测规律（2026-09-10，v11.12.3+）：
#   ① 按声明顺序 **交替** 分配：第 1、3、5…根朝上，第 2、4、6…根朝下；
#   ② 同一侧内「**越晚声明越靠左**」（越远离鱼头），即同侧从左到右 = 声明逆序。
# 所以要让某类落在指定侧与位置，要按「同侧逆序」再「上下交错」反推声明顺序。
# 下方表 = 每根大骨的 (类别名, 侧别, 同侧内从左到右次序)，0 = 最靠左（最远离鱼头）。
LAYOUT = [
    ("材料", "top", 0),      # 上排左
    ("设备", "top", 1),      # 上排右（靠近鱼头）
    ("人",   "bottom", 0),   # 下排左
    ("方法", "bottom", 1),   # 下排右（靠近鱼头）
]


def plan_order():
    """把 LAYOUT 反推成「应该按什么顺序写进 Mermaid 源码」"""
    top = sorted([x for x in LAYOUT if x[1] == "top"], key=lambda t: -t[2])
    bot = sorted([x for x in LAYOUT if x[1] == "bottom"], key=lambda t: -t[2])
    order = []
    for i in range(max(len(top), len(bot))):
        if i < len(top):
            order.append(top[i][0])
        if i < len(bot):
            order.append(bot[i][0])
    return order


def placement(order):
    """按实测规律，反推「这份声明顺序渲染出来会落在哪」—— 用于自查"""
    res = {}
    for side in ("top", "bottom"):
        # 声明序号 0,2,4… 朝上；1,3,5… 朝下；同侧从左到右 = 声明逆序
        mem = [n for i, n in enumerate(order)
               if ("top" if i % 2 == 0 else "bottom") == side][::-1]
        for k, n in enumerate(mem):
            res[n] = (side, k)
    return res


ORDER = plan_order()


def build(levels=4):
    """levels: 1=只要大骨 2=到大骨/中骨 3=到小骨 4=全量"""
    if levels < 1: levels = 1
    L = ["ishikawa-beta", IND + HEAD]
    by_name = {c["name"]: c for c in G.CATS}
    for name in ORDER:
        c = by_name.get(name)
        if c is None:
            raise SystemExit(f"LAYOUT 里的「{name}」不在数据源 CATS 中")
        L.append(IND + c["name"])
        if levels < 2:
            continue
        for gname, _gs, items in c["groups"]:
            L.append(IND * 2 + gname)
            if levels < 3:
                continue
            for text, _key, kids in items:
                L.append(IND * 3 + text)
                if levels < 4:
                    continue
                for k in kids:
                    L.append(IND * 4 + k[0])
    return "\n".join(L) + "\n"


def verify(txt):
    """校验：缩进为 4 的倍数、层级只增不跳、无空行、首行正确"""
    lines = [l for l in txt.split("\n") if l.strip()]
    bad = []
    if lines[0] != "ishikawa-beta":
        bad.append("首行不是 ishikawa-beta")
    prev = 0
    for i, l in enumerate(lines[1:], 1):
        sp = len(l) - len(l.lstrip(" "))
        if sp % 4:
            bad.append(f"第{i}行缩进{sp}不是4的倍数: {l.strip()[:20]}")
        lv = sp // 4
        if lv > prev + 1:
            bad.append(f"第{i}行层级从{prev}跳到{lv}")
        if lv < 1:
            bad.append(f"第{i}行层级为0: {l.strip()[:20]}")
        prev = lv
    return bad


def check_layout():
    """自查：反推的渲染位置是否与 LAYOUT 目标一致"""
    got = placement(ORDER)
    bad = []
    for name, side, idx in LAYOUT:
        if got.get(name) != (side, idx):
            bad.append(f"{name}: 目标({side},{idx}) 实际{got.get(name)}")
    return bad


def main():
    print("=== 大骨排布自查 ===")
    print("写进源码的声明顺序:", " → ".join(ORDER))
    got = placement(ORDER)
    for side, label in (("top", "上排(从左到右)"), ("bottom", "下排(从左到右)")):
        mem = sorted([n for n, v in got.items() if v[0] == side], key=lambda n: got[n][1])
        print(f"  {label}: {' | '.join(mem)}")
    bad_layout = check_layout()
    print("  排布自查:", "OK 与目标一致" if not bad_layout else f"❌ {bad_layout}")
    print()

    outs = []
    full = build(4)
    over = build(2)
    for name, txt, tag in [("鱼骨图-mermaid-完整版.txt", full, "全量 4 级"),
                           ("鱼骨图-mermaid-总览版.txt", over, "总览 2 级")]:
        bad = verify(txt) + bad_layout
        p = os.path.join(BASE, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(txt)
        n = len([l for l in txt.split("\n") if l.strip()])
        outs.append((name, n, len(txt), bad))
    for name, n, sz, bad in outs:
        flag = "OK" if not bad else f"异常 {bad[:2]}"
        print(f"{name:<28} {n:>4} 行  {sz:>6} 字符  {flag}")
    print()
    print("=== 总览版全文 ===")
    print(over)


if __name__ == "__main__":
    main()
