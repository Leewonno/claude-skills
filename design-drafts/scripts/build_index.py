#!/usr/bin/env python3
"""시안 폴더의 drafts.json을 읽어 비교용 index.html을 만든다.

사용법: python3 build_index.py <시안 폴더>
"""
import html
import json
import sys
from pathlib import Path

TEMPLATE = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__ · 시안 비교</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/variable/pretendardvariable.css">
<style>
  :root {
    --bg: #18181b; --panel: #232327; --line: #34343a;
    --text: #f4f4f5; --muted: #a1a1aa; --accent: #ffffff;
  }
  * { box-sizing: border-box; margin: 0; }
  html, body { height: 100%; }
  body {
    display: flex; flex-direction: column; background: var(--bg); color: var(--text);
    font-family: "Pretendard Variable", Pretendard, -apple-system, system-ui, sans-serif;
    font-size: 14px;
  }
  header { padding: 14px 20px 0; background: var(--panel); border-bottom: 1px solid var(--line); }
  .top { display: flex; align-items: baseline; gap: 12px; }
  h1 { font-size: 15px; font-weight: 700; }
  .request { color: var(--muted); font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; }
  .tools { display: flex; gap: 6px; flex-shrink: 0; }
  .tools button, .tools a {
    font: inherit; font-size: 12px; color: var(--text); background: transparent;
    border: 1px solid var(--line); border-radius: 6px; padding: 4px 10px; cursor: pointer; text-decoration: none;
  }
  .tools button:hover, .tools a:hover { border-color: var(--muted); }
  nav { display: flex; gap: 2px; margin-top: 12px; overflow-x: auto; }
  nav button {
    font: inherit; color: var(--muted); background: none; border: 0; cursor: pointer;
    padding: 8px 14px 10px; border-bottom: 2px solid transparent; white-space: nowrap;
  }
  nav button b { color: var(--text); margin-right: 6px; }
  nav button[aria-selected="true"] { color: var(--text); border-bottom-color: var(--accent); }
  .summary { padding: 10px 20px; color: var(--muted); font-size: 13px; border-bottom: 1px solid var(--line); }
  .summary strong { color: var(--text); font-weight: 600; margin-right: 8px; }
  main { flex: 1; overflow: auto; position: relative; }
  .stage { transform-origin: top left; margin: 0 auto; }
  iframe { display: block; border: 0; background: #fff; }
</style>
</head>
<body>
<header>
  <div class="top">
    <h1>__TITLE__</h1>
    <span class="request">__REQUEST__</span>
    <div class="tools">
      <button id="fit" type="button">실제 크기</button>
      <a id="open" href="#" target="_blank" rel="noopener">새 탭에서 열기</a>
    </div>
  </div>
  <nav id="tabs" role="tablist"></nav>
</header>
<div class="summary" id="summary"></div>
<main id="main"><div class="stage" id="stage"><iframe id="frame" title="시안"></iframe></div></main>
<script>
const DATA = __DATA__;
const tabs = document.getElementById('tabs');
const frame = document.getElementById('frame');
const stage = document.getElementById('stage');
const main = document.getElementById('main');
const fitBtn = document.getElementById('fit');
let current = 0;
let fit = true;

DATA.drafts.forEach((d, i) => {
  const b = document.createElement('button');
  b.type = 'button';
  b.setAttribute('role', 'tab');
  b.innerHTML = '<b></b><span></span>';
  b.querySelector('b').textContent = d.id;
  b.querySelector('span').textContent = d.name;
  b.onclick = () => show(i);
  tabs.appendChild(b);
});

function widthOf(d) { return d.width || DATA.width || 1440; }

function layout() {
  const d = DATA.drafts[current];
  const w = widthOf(d);
  const avail = main.clientWidth;
  const s = fit ? Math.min(1, avail / w) : 1;
  frame.style.width = w + 'px';
  frame.style.height = (main.clientHeight / s) + 'px';
  stage.style.width = w + 'px';
  stage.style.transform = s < 1 ? 'scale(' + s + ')' : 'none';
  stage.style.margin = s < 1 ? '0' : '0 auto';
  fitBtn.textContent = fit ? '실제 크기' : '화면 맞춤';
}

function show(i) {
  current = (i + DATA.drafts.length) % DATA.drafts.length;
  const d = DATA.drafts[current];
  [...tabs.children].forEach((b, j) => b.setAttribute('aria-selected', j === current));
  frame.src = d.file;
  document.getElementById('open').href = d.file;
  const sum = document.getElementById('summary');
  sum.innerHTML = '<strong></strong><span></span>';
  sum.querySelector('strong').textContent = d.id + '. ' + d.name;
  sum.querySelector('span').textContent = (d.summary || '') + ' · ' + widthOf(d) + 'px';
  main.scrollTop = 0;
  layout();
}

fitBtn.onclick = () => { fit = !fit; layout(); };
window.addEventListener('resize', layout);
window.addEventListener('keydown', e => {
  if (e.key === 'ArrowRight') show(current + 1);
  else if (e.key === 'ArrowLeft') show(current - 1);
  else if (/^[1-9]$/.test(e.key) && +e.key <= DATA.drafts.length) show(+e.key - 1);
});
show(0);
</script>
</body>
</html>
"""


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("사용법: python3 build_index.py <시안 폴더>")
    folder = Path(sys.argv[1]).expanduser().resolve()
    data = json.loads((folder / "drafts.json").read_text(encoding="utf-8"))

    missing = [d["file"] for d in data["drafts"] if not (folder / d["file"]).exists()]
    if missing:
        sys.exit(f"시안 파일이 없습니다: {', '.join(missing)}")

    out = (
        TEMPLATE.replace("__TITLE__", html.escape(data.get("title", "시안")))
        .replace("__REQUEST__", html.escape(data.get("request", "")))
        .replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
    )
    index = folder / "index.html"
    index.write_text(out, encoding="utf-8")
    print(index)


if __name__ == "__main__":
    main()
