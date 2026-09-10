# -*- coding: utf-8 -*-
"""生成「mermaid在线打开.html」—— 一键跳到 mermaid.live（代码已预填）+ 可复制文本框"""
import os
import sys
import html
import zlib
import base64
import json

BASE = os.path.dirname(os.path.abspath(__file__))
LIVE = "https://mermaid.live/edit#pako:"


def enc(code):
    payload = json.dumps({"code": code, "mermaid": "{\"theme\":\"default\"}",
                          "autoSync": True, "updateDiagram": True})
    return base64.urlsafe_b64encode(zlib.compress(payload.encode("utf-8"), 9)).decode().rstrip("=")


def read(name):
    with open(os.path.join(BASE, name), encoding="utf-8") as f:
        return f.read()


TPL = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mermaid 鱼骨图 · 一键打开</title>
<style>
  :root{--ink:#1e3a5f;--sub:#5b7085;--line:#d6e2ee;--bg:#f4f8fc;--acc:#2f6fb5}
  *{box-sizing:border-box}
  body{margin:0;padding:32px 20px 60px;background:var(--bg);color:var(--ink);
       font:15px/1.75 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
  .wrap{max-width:920px;margin:0 auto}
  h1{font-size:24px;margin:0 0 6px}
  .lead{color:var(--sub);margin:0 0 28px}
  .card{background:#fff;border:1px solid var(--line);border-radius:14px;padding:20px 22px;margin-bottom:20px}
  .card h2{font-size:17px;margin:0 0 4px;display:flex;align-items:baseline;gap:10px;flex-wrap:wrap}
  .card h2 em{font-style:normal;font-size:13px;font-weight:400;color:var(--sub)}
  .btn{display:inline-block;margin:12px 0 14px;padding:11px 22px;border-radius:9px;
       background:linear-gradient(135deg,#2f6fb5,#3f8fd8);color:#fff;text-decoration:none;font-weight:600}
  .btn:hover{filter:brightness(1.07)}
  textarea{width:100%;height:200px;padding:12px 14px;border:1px solid var(--line);border-radius:9px;
           font:13px/1.6 Consolas,"Courier New",monospace;resize:vertical;background:#fbfdff;color:#243b53}
  .tail{height:340px}
  .tip{background:#fff;border:1px solid var(--line);border-left:4px solid var(--acc);
       border-radius:10px;padding:16px 20px;color:#33475e}
  .tip b{color:var(--ink)}
  .tip ol{margin:8px 0 0;padding-left:22px}
  .tip code{background:#eef4fb;padding:1px 6px;border-radius:4px;font-size:13px}
</style>
</head>
<body>
<div class="wrap">
  <h1>注塑件缺料（短射） · 鱼骨图 Mermaid 版</h1>
  <p class="lead">点按钮 → 浏览器打开 mermaid.live，代码已经填好，右边立刻就是鱼骨图。改文字，图会实时跟着变。</p>

  <div class="card">
    <h2>① 总览版 <em>22 行 · 结构清晰 · 讲课时用这个</em></h2>
    <a class="btn" href="__LINK_OVER__" target="_blank" rel="noopener">在 mermaid.live 打开 →</a>
    <textarea readonly spellcheck="false">__CODE_OVER__</textarea>
  </div>

  <div class="card">
    <h2>② 完整版 <em>142 行 · 102 条小骨 + 18 条小小骨全在 · 图会比较挤</em></h2>
    <a class="btn" href="__LINK_FULL__" target="_blank" rel="noopener">在 mermaid.live 打开 →</a>
    <textarea readonly spellcheck="false" class="tail">__CODE_FULL__</textarea>
  </div>

  <div class="tip">
    <b>如果按钮打不开，用复制的办法（一定行）：</b>
    <ol>
      <li>浏览器打开 <code>mermaid.live</code></li>
      <li>点左边代码框 → <code>Ctrl+A</code> 全选 → <code>Delete</code> 删掉里面的示例</li>
      <li>回到本页，在对应文本框里点一下 → <code>Ctrl+A</code> → <code>Ctrl+C</code></li>
      <li>粘到 mermaid.live 的代码框（<code>Ctrl+V</code>），右边立刻出图</li>
    </ol>
    <p style="margin:10px 0 0"><b>导出图片：</b>mermaid.live 左上角 <code>Actions</code> → <code>Download PNG</code> 或 <code>Download SVG</code>。</p>
  </div>
</div>
</body>
</html>
"""


def main():
    over = read("鱼骨图-mermaid-总览版.txt")
    full = read("鱼骨图-mermaid-完整版.txt")
    out = (TPL.replace("__LINK_OVER__", LIVE + enc(over))
              .replace("__LINK_FULL__", LIVE + enc(full))
              .replace("__CODE_OVER__", html.escape(over))
              .replace("__CODE_FULL__", html.escape(full)))
    p = os.path.join(BASE, "mermaid在线打开.html")
    with open(p, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"OK -> {p}  {len(out)} 字符")


if __name__ == "__main__":
    main()
