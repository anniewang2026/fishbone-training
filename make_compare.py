# -*- coding: utf-8 -*-
"""生成「原图 vs 1:1 复刻」叠图对比页（单文件，内联 SVG + base64 原图）。"""
import base64, os, re

svg = open("复刻-原图.svg", encoding="utf-8").read()
jpg = open("fishbone-source.jpg", "rb").read()
b64 = base64.b64encode(jpg).decode()

html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>原图 vs 1:1 复刻 · 叠图对比</title>
<style>
:root{--bg:#eef2f6;--card:#fff;--line:#c9d6e2;--txt:#2a3b4d;--sub:#6b7f93;--pri:#2f6fb5}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--txt);
     font-family:"Microsoft YaHei","PingFang SC",-apple-system,sans-serif}
.wrap{max-width:1500px;margin:0 auto;padding:20px 18px 60px}
h1{font-size:21px;margin:6px 0 6px}
p.lead{color:var(--sub);font-size:13.5px;line-height:1.75;margin:0 0 16px}
.bar{display:flex;align-items:center;gap:14px;flex-wrap:wrap;
     background:var(--card);border:1px solid var(--line);border-radius:12px;
     padding:12px 16px;margin-bottom:14px}
.bar label{font-size:13px;font-weight:600}
input[type=range]{flex:1;min-width:220px;accent-color:var(--pri)}
.val{font-variant-numeric:tabular-nums;font-weight:700;color:var(--pri);min-width:44px;text-align:right}
button{border:1px solid var(--line);background:#fff;border-radius:8px;
       padding:7px 13px;font-size:12.5px;cursor:pointer;color:var(--txt);font-family:inherit}
button:hover{border-color:var(--pri);color:var(--pri)}
.stage{position:relative;background:#fff;border:1px solid var(--line);
       border-radius:12px;overflow:auto;box-shadow:0 2px 14px rgba(40,70,110,.07)}
.inner{position:relative;width:100%;min-width:900px}
.inner svg{display:block;width:100%;height:auto}
.overlay{position:absolute;inset:0}
.overlay img{display:block;width:100%;height:100%;object-fit:fill}
.legend{display:flex;gap:18px;font-size:12.5px;color:var(--sub);margin-top:10px;flex-wrap:wrap}
.dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:5px}
</style>
</head>
<body>
<div class="wrap">
  <h1>原图 vs 1:1 复刻 · 叠图对比</h1>
  <p class="lead">
    拖动下面的滑块把<b>原图</b>叠在复刻图上：数值 0% = 只看复刻图（矢量、可任意放大、文字清晰）；
    100% = 只看你给的原图。中间任意位置都能直接看出两者是否严丝合缝 ——
    <b>线画在哪儿、箭头朝哪、小骨/小小骨挂在哪一级，完全按原图 1:1 提取，没有人工重排。</b>
  </p>
  <div class="bar">
    <label>原图透明度</label>
    <input id="op" type="range" min="0" max="100" value="0"/>
    <span class="val" id="ov">0%</span>
    <button data-v="0">只看复刻</button>
    <button data-v="50">对半叠</button>
    <button data-v="100">只看原图</button>
  </div>
  <div class="stage">
    <div class="inner" id="inner">
      __SVG__
      <div class="overlay" id="ovl" style="opacity:0">
        <img src="data:image/jpeg;base64,__B64__" alt="原图"/>
      </div>
    </div>
  </div>
  <div class="legend">
    <span><i class="dot" style="background:#1c1c1c"></i>原图线条 / 箭头（矢量描摹）</span>
    <span><i class="dot" style="background:#e0356e"></i>红字标注</span>
    <span><i class="dot" style="background:#1b4fa0"></i>蓝字标注</span>
    <span><i class="dot" style="background:#d9d9d9"></i>鱼头框 / 底色块</span>
  </div>
</div>
<script>
const op=document.getElementById('op'),ovl=document.getElementById('ovl'),ov=document.getElementById('ov');
function set(v){op.value=v;ovl.style.opacity=v/100;ov.textContent=v+'%';}
op.addEventListener('input',e=>set(+e.target.value));
document.querySelectorAll('button[data-v]').forEach(b=>b.onclick=()=>set(+b.dataset.v));
// 让原图与复刻严格同位：SVG 保持原始比例
const sv=document.querySelector('.inner svg');
const vb=sv.getAttribute('viewBox').split(/\\s+/).map(Number);
sv.setAttribute('style','display:block;width:100%;height:auto;aspect-ratio:'+vb[2]+'/'+vb[3]);
</script>
</body>
</html>"""

html = html.replace("__SVG__", svg).replace("__B64__", b64)
open("复刻对比.html", "w", encoding="utf-8").write(html)
print(f"复刻对比.html {os.path.getsize('复刻对比.html')/1024:.0f} KB")
