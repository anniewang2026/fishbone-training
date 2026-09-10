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


def build(levels=4):
    """levels: 1=只要大骨 2=到大骨/中骨 3=到小骨 4=全量"""
    if levels < 1: levels = 1
    L = ["ishikawa-beta", IND + HEAD]
    for c in G.CATS:
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


def main():
    outs = []
    full = build(4)
    over = build(2)
    for name, txt, tag in [("鱼骨图-mermaid-完整版.txt", full, "全量 4 级"),
                           ("鱼骨图-mermaid-总览版.txt", over, "总览 2 级")]:
        bad = verify(txt)
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
