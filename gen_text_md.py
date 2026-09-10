# -*- coding: utf-8 -*-
"""从 gen_fishbone.py 的数据源生成「文字版结构表」markdown（改数据后重跑即可保持同步）

用法: python gen_text_md.py
"""
import os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import gen_fishbone as G                                       # noqa: E402

OUT = os.path.join(BASE, "要因图-文字版结构.md")

HEAD_NAME = f"{G.HEAD_TEXT}（短射）"
SIDE_CN = {"L": "外侧", "R": "内侧"}
CAT_CN = {"材料": "材料", "设备": "设备", "人": "人", "方法": "方法"}


def cat_stat(cat):
    items = [it for _, _, its in cat["groups"] for it in its]
    kids = [k for _, _, its in cat["groups"] for it in its for k in it[2]]
    keys = [it for it in items if it[1]]
    return len(cat["groups"]), len(items), len(kids), len(keys)


def main():
    o = []
    A = o.append
    tot = dict(g=0, i=0, k=0, key=0)
    for c in G.CATS:
        a, b, d, e = cat_stat(c)
        tot["g"] += a; tot["i"] += b; tot["k"] += d; tot["key"] += e

    A(f"# {HEAD_NAME} 要因分析图 · 文字版结构表\n")
    A("> 用途：直接按此表用任意绘图工具（PPT / XMind / draw.io / Visio / AI 绘图）重绘。")
    A(f"> 数据来源：原图逐条数字化，共 **4 大骨 · {tot['g']} 中骨 · {tot['i']} 小骨 · {tot['k']} 小小骨**，"
      f"其中 **★{tot['key']} 条重点要因**（原图粉色标注，待真因验证）。\n")

    A("## 一、绘图规格（照这个画才是标准鱼骨图）\n")
    A("| 项目 | 规格 |")
    A("|---|---|")
    A(f"| 主骨（脊骨） | 水平直线，箭头指向右侧鱼头；鱼头写「{HEAD_NAME}」 |")
    A(f"| **大骨角度** | **与主骨夹角 {G.BONE_DEG:.0f}°** |")
    A("| 大骨数量 | 4 根：材料、设备在主骨**上方**；人、方法在主骨**下方** |")
    A("| 大骨方向 | 外端（骨尖）偏向**远离鱼头**一侧，即斜线自主骨向左上 / 左下张开 |")
    A("| 中骨 | **水平线，与主骨平行**；一端接在大骨斜线上，另一端（自由端）写中骨名 |")
    A("| 中骨分布 | **同一根大骨的中骨分列斜线两侧，由内向外左右交错**（本表「挂在斜线」列已标） |")
    A("| 小骨 | **水平短线，与所属中骨平行**；文字写在线上方；线的一端经竖向收集线接到中骨 |")
    A("| 小小骨 | **同样是水平短线，与所属中骨平行**；从父小骨线的末端向外延伸，并向中骨侧缩进一行 |")
    A(f"| 高亮 | ★ = 重点要因（待真因验证），共 {tot['key']} 条 |")
    A("| 画布比例 | 约 1.6 : 1（宽 : 高，横版，适合投影与报告） |")
    A("| 大骨间距 | 自中骨线起约 190 px 一根，四根依次向外 |")
    A("")
    A("> 一句话记法：**主骨横、大骨 60°、中骨/小骨/小小骨全部横平（与主骨平行）**。")
    A("> 只有大骨是斜的，其余全是横线——这就是鱼骨图「一眼看清层级」的关键。\n")

    A("## 二、结构总览\n")
    A("```")
    A("                    ┌─ 材料（上左）")
    A(f"   {HEAD_NAME} ◀── 主骨 ──┤")
    A("     （鱼头·右）      └─ 设备（上右）")
    A("")
    A("                    ┌─ 人  （下左）")
    A("        主骨 ───────┤")
    A("                    └─ 方法（下右）")
    A("")
    A("  层级：中骨（横线·注明名称）")
    A("          └─ 小骨（横线·文字在线上面）")
    A("                └─ 小小骨（横线·再向外伸一段）")
    A("```\n")

    A("## 三、各分类明细\n")
    for cat in G.CATS:
        gn, inum, knum, keyn = cat_stat(cat)
        pos = "主骨上方" if cat["side"] == "top" else "主骨下方"
        A(f"### {cat['name']}（{pos}）\n")
        A(f"{gn} 中骨 · {inum} 小骨 · {knum} 小小骨 · ★{keyn} 重点\n")
        A("| # | 中骨 | 挂在斜线 | 小骨（★=重点要因，↳ 后为小小骨） |")
        A("|---|---|---|---|")
        for i, (gname, gside, items) in enumerate(cat["groups"], 1):
            cells = []
            for text, key, kids in items:
                s = f"**★{text}**" if key else text
                if kids:
                    s += "（" + "；".join(k[0] for k in kids) + "）"
                cells.append(s)
            A(f"| {i} | **{gname}** | {SIDE_CN[gside]}（自主骨向外第 {i} 根） | {'、'.join(cells)} |")
        A("")

    A(f"## 四、重点要因（★）清单 —— 共 {tot['key']} 条\n")
    A("| # | 大骨 | 中骨 | 小骨 |")
    A("|---|---|---|---|")
    n = 0
    for cat in G.CATS:
        for gname, _gs, items in cat["groups"]:
            for text, key, _kids in items:
                if key:
                    n += 1
                    A(f"| {n} | {cat['name']} | {gname} | {text} |")
    A("")

    A("## 五、转写与订正说明\n")
    A("- 原图全部条目已逐条数字化，按「大骨 → 中骨 → 小骨 → 小小骨」重新归位。")
    A("- 已修正的疑似字迹误读：射出速度**慢**（非「快」）、计量速度**慢**、「刀片筛网磨损」、"
      "「未废弃开机不良品」、「未打开升水」、过滤**网**堵塞、发热器（不能正常发热）。")
    A("- 「抽取数量不够」原图写作「拔取」，已按行业用语订正。")
    A("- 「成形机」下原图有两条同名「时间长磨损」，**已去重保留一条**，故小骨总数为 "
      f"{tot['i']} 条（非 103）。")
    A("- 「金型」为日语借词，本版统一改为中文 **「模具空腔」/「模具维护」**；"
      "文中的「金型温度低」相应改为「模温低」。")
    A("- 小小骨放在中骨侧（朝向主骨）逐行缩进，与实际手绘习惯一致。")

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(o) + "\n")
    print(f"OK -> {OUT}  ({len(o)} 行)  4 大骨 · {tot['g']} 中骨 · {tot['i']} 小骨 · "
          f"{tot['k']} 小小骨 · ★{tot['key']}")


if __name__ == "__main__":
    main()
