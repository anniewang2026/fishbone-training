# -*- coding: utf-8 -*-
"""把《注塑品质不良-要因拆解逻辑.md》渲染成可投影 / 可打印的 HTML 培训页

只支持本文件实际用到的 markdown 子集：标题 / 表格 / 引用 / 代码块 / 有序列表 / 分隔线 / 粗体 / 行内代码。
用法: python gen_reasoning_page.py
"""
import os
import re
import html

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = "注塑品质不良-要因拆解逻辑.md"
OUT = "要因拆解逻辑-培训页.html"


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    return s


def cells(r):
    return [c.strip() for c in r.strip().strip("|").split("|")]


def md2html(md):
    lines, out, i, n = md.split("\n"), [], 0, len(md.split("\n"))
    while i < n:
        raw = lines[i]
        s = raw.strip()
        if not s:
            i += 1
            continue
        if s == "---":
            out.append("<hr>")
            i += 1
            continue

        if s.startswith("```"):                                   # 代码块
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            out.append("<pre>" + html.escape("\n".join(buf)) + "</pre>")
            continue

        m = re.match(r"^(#{1,4})\s+(.*)$", s)                     # 标题
        if m:
            lv = len(m.group(1))
            out.append(f"<h{lv}>{inline(m.group(2))}</h{lv}>")
            i += 1
            continue

        if s.startswith(">"):                                     # 引用
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip())
                i += 1
            out.append("<blockquote>" + "<br>".join(inline(b) for b in buf) + "</blockquote>")
            continue

        if s.startswith("|"):                                     # 表格
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(lines[i].strip())
                i += 1
            head, body = cells(rows[0]), [cells(r) for r in rows[2:]]
            th = "".join(f"<th>{inline(c)}</th>" for c in head)
            tb = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>"
                         for r in body)
            out.append(f"<table><thead><tr>{th}</tr></thead><tbody>{tb}</tbody></table>")
            continue

        if re.match(r"^\d+\.\s+", s):                             # 有序列表
            items = []
            while i < n:
                t = lines[i].strip()
                if re.match(r"^\d+\.\s+", t):
                    items.append(re.sub(r"^\d+\.\s+", "", t))
                    i += 1
                elif t and lines[i][:1] in (" ", "\t") and items:
                    items[-1] += " " + t
                    i += 1
                else:
                    break
            out.append("<ol>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ol>")
            continue

        if len(s) > 1 and s.startswith("_") and s.endswith("_"):   # 末尾署名
            out.append(f'<p class="gen">{inline(s[1:-1])}</p>')
            i += 1
            continue

        out.append(f"<p>{inline(s)}</p>")
        i += 1
    return "\n".join(out)


TPL = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>注塑品质不良 · 要因拆解逻辑</title>
<style>
  :root{--ink:#1e3a5f;--sub:#5b7085;--line:#d6e2ee;--bg:#f4f8fc;--acc:#2f6fb5;--acc2:#3f8fd8;--warn:#c0392b}
  *{box-sizing:border-box}
  body{margin:0;padding:0 20px 72px;background:var(--bg);color:#243b53;
       font:15px/1.8 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
  .wrap{max-width:1000px;margin:0 auto}
  header{background:linear-gradient(135deg,#1e3a5f,#2f6fb5);color:#fff;border-radius:0 0 18px 18px;
         margin:0 -20px 26px;padding:30px 34px 26px}
  header h1{margin:0 0 8px;font-size:26px;letter-spacing:.5px}
  header p{margin:0;opacity:.92;font-size:14px}
  .flow{display:flex;flex-wrap:wrap;align-items:stretch;gap:10px;margin:0 0 26px}
  .fstep{flex:1 1 168px;background:#fff;border:1px solid var(--line);border-radius:12px;
         padding:12px 14px;box-shadow:0 1px 3px rgba(30,58,95,.06)}
  .fstep b{display:block;font-size:15px;color:var(--acc);margin-bottom:3px}
  .fstep span{font-size:12.5px;color:var(--sub);line-height:1.55}
  .far{align-self:center;color:var(--acc);font-size:19px;font-weight:700}
  .floop{flex:0 0 100%;text-align:center;color:var(--sub);font-size:13px;margin-top:-2px}
  .content{background:#fff;border:1px solid var(--line);border-radius:14px;padding:6px 30px 30px}
  h1,h2,h3{color:var(--ink);line-height:1.4}
  .content h2{font-size:20px;margin:32px 0 12px;padding-left:12px;border-left:5px solid var(--acc)}
  .content h3{font-size:16.5px;margin:26px 0 10px;color:#2c5686}
  .content h1{font-size:23px;margin:22px 0 10px}
  blockquote{margin:12px 0;padding:11px 16px;background:#eff6fd;border-left:4px solid var(--acc);
             border-radius:8px;color:#33475e;font-size:14px}
  table{width:100%;border-collapse:collapse;margin:12px 0 18px;font-size:13.5px;background:#fff}
  th,td{border:1px solid var(--line);padding:7px 11px;text-align:left;vertical-align:top}
  th{background:#eaf2fa;color:var(--ink);font-weight:600;white-space:nowrap}
  tbody tr:nth-child(even){background:#fbfdff}
  td:empty{background:#f7fafd}
  code{background:#eef4fb;color:#2c5686;padding:1px 6px;border-radius:4px;
       font:12.5px Consolas,"Courier New",monospace}
  pre{background:#1e3a5f;color:#dbe8f7;padding:16px 18px;border-radius:10px;overflow-x:auto;
      font:13px/1.65 Consolas,"Courier New",monospace;margin:12px 0 18px}
  hr{border:0;border-top:1px dashed var(--line);margin:30px 0}
  ol{padding-left:24px}
  li{margin:5px 0}
  .gen{color:var(--sub);font-size:12.5px;text-align:center;margin-top:26px}
  strong{color:#17324f}
  @media print{
    body{background:#fff;padding:0}
    header{background:#fff;color:var(--ink);border-bottom:2px solid var(--acc);border-radius:0}
    .flow{display:none}
    .content{border:0;padding:0}
    pre{background:#f4f8fc;color:#243b53;border:1px solid var(--line)}
    table{font-size:11.5px}
    .content h2{page-break-after:avoid}
    table,pre{page-break-inside:avoid}
  }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>注塑品质不良 · 要因拆解逻辑</h1>
    <p>一次要因 → 二次要因 → 三次要因 → 四次要因　｜　每一层都做同样四步</p>
  </header>

  <div class="flow">
    <div class="fstep"><b>① 定格</b><span>锁定上一级的<u>某一条</u>要因<br>一次只推一条</span></div>
    <div class="far">→</div>
    <div class="fstep"><b>② 建假说</b><span>「它在机制上怎么会导致问题？」<br>用 原理 · 原则 · 机制</span></div>
    <div class="far">→</div>
    <div class="fstep"><b>③ 筛选</b><span>可观测 · 可测量<br>可对策 · 不重复</span></div>
    <div class="far">→</div>
    <div class="fstep"><b>④ 定级</b><span>留下的成为下一级要因<br>回到 ①</span></div>
    <div class="floop">↺　同一套动作，往下重复做　↺</div>
  </div>

  <div class="content">
__BODY__
  </div>
</div>
</body>
</html>
"""


def main():
    with open(os.path.join(BASE, SRC), encoding="utf-8") as f:
        md = f.read()
    body = md2html(md)
    out = TPL.replace("__BODY__", body)
    p = os.path.join(BASE, OUT)
    with open(p, "w", encoding="utf-8") as f:
        f.write(out)

    # 自查：不应残留 markdown 标记
    import collections
    left = collections.Counter()
    for k in ("**", "|", "__", "```", "## "):
        if k in body:
            left[k] = body.count(k)
    print(f"OK -> {OUT}  {len(out)} 字符")
    print(f"  表格 {body.count('<table>')} 个 · 表格行 {body.count('<tr>')} 行 · "
          f"标题 {body.count('<h')} 个 · 代码块 {body.count('<pre>')} 个 · 引用 {body.count('<blockquote>')} 个")
    print("  残留 markdown 标记:", dict(left) or "无")
    return len(left)


if __name__ == "__main__":
    raise SystemExit(1 if main() else 0)
