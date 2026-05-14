#!/usr/bin/env python3
"""
subsidy_data.json から index.html を生成
"""

import json
from datetime import datetime
from html import escape
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "subsidy_data.json"
HTML_FILE = BASE_DIR / "index.html"

STATUS_LABEL = {
    "open": ("募集中", "status-open"),
    "closed": ("募集終了", "status-closed"),
    "result": ("採択結果", "status-result"),
    "unknown": ("情報", "status-prep"),
}

CSS = """
:root {
  --bg: #faf8f4; --paper: #ffffff; --ink: #1a1a1a; --ink-soft: #4a4a4a;
  --ink-mute: #888; --line: #e8e4dc; --line-dark: #d4cdbf;
  --accent: #8b3a3a; --gold: #a68b5b; --seal: #b8473d;
  --green: #4a6b3a; --green-bg: #eaf0e3;
  --amber: #b87b1c; --amber-bg: #f7ecd5;
  --gray-bg: #ececea; --blue: #2c5282; --blue-bg: #dbe5ee;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'Noto Sans JP', sans-serif; background: var(--bg);
  color: var(--ink); line-height: 1.7; font-size: 14px; min-height: 100vh;
}
body::before {
  content: ''; position: fixed; inset: 0;
  background-image:
    radial-gradient(circle at 20% 30%, rgba(166,139,91,0.04) 0%, transparent 50%),
    radial-gradient(circle at 80% 70%, rgba(139,58,58,0.03) 0%, transparent 50%);
  pointer-events: none; z-index: 0;
}
.container { position: relative; z-index: 1; max-width: 1400px; margin: 0 auto; padding: 60px 40px 80px; }
header { border-bottom: 1px solid var(--line-dark); padding-bottom: 40px; margin-bottom: 40px; }
.header-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 30px; }
.eyebrow {
  font-family: 'Cormorant Garamond', serif; font-style: italic;
  color: var(--gold); font-size: 15px; letter-spacing: 0.15em; margin-bottom: 8px;
}
h1 {
  font-family: 'Noto Serif JP', serif; font-size: 42px; font-weight: 700;
  letter-spacing: 0.04em; line-height: 1.2; margin-bottom: 12px;
}
.subtitle { font-family: 'Noto Serif JP', serif; color: var(--ink-soft); font-size: 16px; letter-spacing: 0.08em; }
.seal {
  width: 80px; height: 80px; border: 2px solid var(--seal); border-radius: 50%;
  display: flex; align-items: center; justify-content: center; color: var(--seal);
  font-family: 'Noto Serif JP', serif; font-size: 11px; font-weight: 700;
  letter-spacing: 0.1em; transform: rotate(-8deg); text-align: center;
  line-height: 1.3; flex-shrink: 0; margin-top: 8px;
}
.stats {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 0;
  border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); padding: 24px 0;
}
.stat { padding: 0 24px; border-right: 1px solid var(--line); }
.stat:last-child { border-right: none; }
.stat-label { font-size: 11px; letter-spacing: 0.15em; color: var(--ink-mute); text-transform: uppercase; margin-bottom: 6px; }
.stat-value { font-family: 'Noto Serif JP', serif; font-size: 28px; font-weight: 700; line-height: 1.1; }
.stat-sub { font-size: 12px; color: var(--accent); margin-top: 4px; }
.controls { display: flex; gap: 16px; align-items: center; margin: 36px 0 28px; flex-wrap: wrap; }
.search-box { flex: 1; min-width: 280px; position: relative; }
.search-box input {
  width: 100%; padding: 12px 16px 12px 42px; border: 1px solid var(--line-dark);
  background: var(--paper); font-family: 'Noto Sans JP', sans-serif;
  font-size: 14px; outline: none; transition: border-color 0.2s;
}
.search-box input:focus { border-color: var(--accent); }
.search-box::before {
  content: ''; position: absolute; left: 16px; top: 50%; transform: translateY(-50%);
  width: 16px; height: 16px; border: 1.5px solid var(--ink-mute); border-radius: 50%;
}
.search-box::after {
  content: ''; position: absolute; left: 28px; top: 26px;
  width: 8px; height: 1.5px; background: var(--ink-mute); transform: rotate(45deg);
}
.filter-group { display: flex; gap: 4px; border: 1px solid var(--line-dark); background: var(--paper); }
.filter-btn {
  padding: 10px 18px; border: none; background: transparent;
  font-family: 'Noto Sans JP', sans-serif; font-size: 13px;
  color: var(--ink-soft); cursor: pointer; transition: all 0.2s; letter-spacing: 0.05em;
}
.filter-btn:hover { color: var(--accent); }
.filter-btn.active { background: var(--ink); color: var(--paper); }
.count-display { font-family: 'Cormorant Garamond', serif; font-style: italic; color: var(--ink-mute); font-size: 15px; }
.table-wrap { background: var(--paper); border: 1px solid var(--line-dark); overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
thead { background: var(--ink); color: var(--paper); }
th {
  padding: 16px 14px; text-align: left; font-weight: 500; font-size: 11px;
  letter-spacing: 0.15em; text-transform: uppercase; white-space: nowrap;
  border-right: 1px solid rgba(255,255,255,0.1);
}
th:last-child { border-right: none; }
tbody tr { border-bottom: 1px solid var(--line); transition: background 0.15s; }
tbody tr:hover { background: rgba(166,139,91,0.06); }
tbody tr.hidden { display: none; }
tbody tr.row-new { background: linear-gradient(90deg, rgba(184,71,61,0.08), transparent); }
td { padding: 18px 14px; vertical-align: top; border-right: 1px solid var(--line); line-height: 1.6; }
td:last-child { border-right: none; }
.no-cell { font-family: 'Cormorant Garamond', serif; font-size: 18px; color: var(--gold); font-weight: 600; width: 40px; }
.project-name { font-weight: 500; font-size: 14px; min-width: 240px; max-width: 320px; }
.new-tag, .highlight-tag {
  display: inline-block; color: var(--paper); font-size: 9px; padding: 2px 6px;
  margin-left: 6px; letter-spacing: 0.1em; vertical-align: middle; font-weight: 700;
}
.new-tag { background: var(--seal); }
.highlight-tag { background: var(--gold); }
.budget-tag {
  display: inline-block; padding: 3px 8px; font-size: 11px;
  letter-spacing: 0.05em; border: 1px solid var(--line-dark);
  background: var(--bg); color: var(--ink-soft); white-space: nowrap;
}
.amount { font-family: 'Noto Serif JP', serif; font-weight: 700; color: var(--accent); font-size: 14px; white-space: nowrap; }
.rate { font-size: 12px; color: var(--ink-soft); white-space: nowrap; }
.target { font-size: 12px; color: var(--ink-soft); min-width: 140px; }
.summary { font-size: 12.5px; color: var(--ink-soft); line-height: 1.65; min-width: 260px; max-width: 360px; }
.deadline { font-family: 'Noto Serif JP', serif; font-size: 13px; white-space: nowrap; }
.status {
  display: inline-block; padding: 4px 10px; font-size: 11px;
  letter-spacing: 0.05em; white-space: nowrap; font-weight: 500;
}
.status-open { background: var(--green-bg); color: var(--green); border-left: 2px solid var(--green); }
.status-prep { background: var(--amber-bg); color: var(--amber); border-left: 2px solid var(--amber); }
.status-closed { background: var(--gray-bg); color: var(--ink-mute); border-left: 2px solid var(--ink-mute); }
.status-result { background: var(--blue-bg); color: var(--blue); border-left: 2px solid var(--blue); }
.url-link {
  color: var(--accent); text-decoration: none; font-size: 12px;
  border-bottom: 1px dotted var(--accent); padding-bottom: 1px; transition: all 0.2s;
}
.url-link:hover { color: var(--seal); border-bottom-style: solid; }
.note { font-size: 11.5px; color: var(--ink-mute); font-style: italic; min-width: 140px; }
footer {
  margin-top: 60px; padding-top: 30px; border-top: 1px solid var(--line-dark);
  display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 20px;
}
.footer-info { font-size: 12px; color: var(--ink-mute); line-height: 1.8; }
.footer-info strong { color: var(--ink-soft); font-weight: 500; }
.signature { font-family: 'Cormorant Garamond', serif; font-style: italic; color: var(--gold); font-size: 14px; letter-spacing: 0.08em; }
@media (max-width: 900px) {
  .container { padding: 30px 16px 50px; }
  h1 { font-size: 28px; }
  .stats { grid-template-columns: repeat(2, 1fr); }
  .stat { padding: 16px; border-bottom: 1px solid var(--line); }
  .stat:nth-child(odd) { border-right: 1px solid var(--line); }
  .stat:nth-child(3), .stat:nth-child(4) { border-bottom: none; }
  .seal { width: 60px; height: 60px; font-size: 9px; }
  .controls { flex-direction: column; align-items: stretch; }
}
@media print { body { background: white; } .controls, footer { display: none; } }
"""


def sort_key(e):
    """募集中→採択結果→募集終了の順で並べる。同ステータス内は公開日新しい順"""
    order = {"open": 0, "result": 1, "unknown": 2, "closed": 3}
    return (order.get(e["status"], 9), -_date_to_int(e.get("published", "")))


def _date_to_int(s):
    import re
    m = re.match(r"(\d{4})年(\d{1,2})月(\d{1,2})日", s)
    if not m:
        return 0
    return int(m.group(1)) * 10000 + int(m.group(2)) * 100 + int(m.group(3))


def render_row(idx, e):
    status_label, status_class = STATUS_LABEL.get(e["status"], STATUS_LABEL["unknown"])
    tags = ""
    if e.get("is_new"):
        tags += '<span class="new-tag">新規</span>'
    if e.get("highlight"):
        tags += '<span class="highlight-tag">注目</span>'

    row_class = ""
    # 直近30日以内に公開された募集中エントリは目立たせる
    if e["status"] == "open" and _is_recent(e.get("published", "")):
        row_class = "row-new"

    return f"""
<tr data-status="{e['status']}" class="{row_class}">
<td class="no-cell">{idx:02d}</td>
<td class="project-name">{escape(e['title'])}{tags}</td>
<td><span class="budget-tag">{escape(e.get('budget_year', '—') or '—')}</span></td>
<td class="amount">{escape(e.get('budget_amount', '—') or '—')}</td>
<td class="rate">{e.get('rate', '—') or '—'}</td>
<td class="target">{e.get('target', '—') or '—'}</td>
<td class="summary">{escape(e.get('summary', ''))}</td>
<td class="deadline">{escape(e.get('deadline', '—') or '—')}</td>
<td><span class="status {status_class}">{status_label}</span></td>
<td class="note">{e.get('note', '')}<br><a class="url-link" href="{escape(e['url'])}" target="_blank">公募ページ →</a></td>
</tr>"""


def _is_recent(date_str, days=30):
    import re
    m = re.match(r"(\d{4})年(\d{1,2})月(\d{1,2})日", date_str)
    if not m:
        return False
    try:
        d = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        return (datetime.now() - d).days <= days
    except Exception:
        return False


def main():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    entries = sorted(data["entries"], key=sort_key)
    total = len(entries)
    open_count = sum(1 for e in entries if e["status"] == "open")

    rows_html = "\n".join(render_row(i + 1, e) for i, e in enumerate(entries))
    last_updated = data.get("last_updated", "")
    if last_updated:
        try:
            last_updated_disp = datetime.fromisoformat(last_updated).strftime("%Y.%m.%d %H:%M")
        except ValueError:
            last_updated_disp = last_updated
    else:
        last_updated_disp = "—"

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>観光庁 補助金事業一覧 | 令和8年度</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@400;500;700&family=Noto+Sans+JP:wght@300;400;500;700&family=Cormorant+Garamond:wght@400;500;600&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<div class="container">
  <header>
    <div class="header-top">
      <div class="title-block">
        <div class="eyebrow">Japan Tourism Agency — Subsidy Programs</div>
        <h1>観光庁 補助金事業一覧</h1>
        <div class="subtitle">令和8年度（2026年度）— 自動更新トラッカー</div>
      </div>
      <div class="seal">観光<br>令和八<br>年度</div>
    </div>
    <div class="stats">
      <div class="stat">
        <div class="stat-label">Total Budget</div>
        <div class="stat-value">1,383億円</div>
        <div class="stat-sub">前年比 2.4倍</div>
      </div>
      <div class="stat">
        <div class="stat-label">Listed Programs</div>
        <div class="stat-value">{total}事業</div>
        <div class="stat-sub">本リスト掲載数</div>
      </div>
      <div class="stat">
        <div class="stat-label">Currently Open</div>
        <div class="stat-value">{open_count}事業</div>
        <div class="stat-sub">募集中</div>
      </div>
      <div class="stat">
        <div class="stat-label">Last Updated</div>
        <div class="stat-value" style="font-size:18px;">{last_updated_disp}</div>
        <div class="stat-sub">自動取得</div>
      </div>
    </div>
  </header>

  <div class="controls">
    <div class="search-box">
      <input type="text" id="search" placeholder="事業名・キーワードで検索（例：DX、オーバーツーリズム、宿泊）">
    </div>
    <div class="filter-group">
      <button class="filter-btn active" data-filter="all">すべて</button>
      <button class="filter-btn" data-filter="open">募集中</button>
      <button class="filter-btn" data-filter="result">採択結果</button>
      <button class="filter-btn" data-filter="closed">募集終了</button>
    </div>
    <span class="count-display"><span id="visible-count">{total}</span> / {total} 事業</span>
  </div>

  <div class="table-wrap">
    <table id="subsidy-table">
      <thead>
        <tr>
          <th>No.</th><th>事業名</th><th>予算区分</th><th>予算額</th>
          <th>補助率・上限</th><th>対象事業者</th><th>事業概要</th>
          <th>公募締切</th><th>ステータス</th><th>備考・リンク</th>
        </tr>
      </thead>
      <tbody>{rows_html}
      </tbody>
    </table>
  </div>

  <footer>
    <div class="footer-info">
      <strong>情報源</strong>　観光庁 公募情報ページ（<a href="https://www.mlit.go.jp/kankocho/kobo_2026_00003.html" class="url-link" target="_blank">mlit.go.jp/kankocho</a>）<br>
      <strong>更新方式</strong>　GitHub Actionsによる毎日自動取得　│　<strong>最終更新</strong>　{last_updated_disp}
    </div>
    <div class="signature">— Tourism Policy Tracker —</div>
  </footer>
</div>

<script>
const search = document.getElementById('search');
const filterBtns = document.querySelectorAll('.filter-btn');
const rows = document.querySelectorAll('#subsidy-table tbody tr');
const visibleCount = document.getElementById('visible-count');
let currentFilter = 'all', currentSearch = '';
function applyFilters() {{
  let count = 0;
  rows.forEach(row => {{
    const status = row.dataset.status;
    const text = row.textContent.toLowerCase();
    const matchStatus = currentFilter === 'all' || currentFilter === status;
    const matchSearch = currentSearch === '' || text.includes(currentSearch);
    if (matchStatus && matchSearch) {{ row.classList.remove('hidden'); count++; }}
    else {{ row.classList.add('hidden'); }}
  }});
  visibleCount.textContent = count;
}}
search.addEventListener('input', e => {{ currentSearch = e.target.value.toLowerCase(); applyFilters(); }});
filterBtns.forEach(btn => {{
  btn.addEventListener('click', () => {{
    filterBtns.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentFilter = btn.dataset.filter;
    applyFilters();
  }});
}});
</script>
</body>
</html>"""

    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Generated {HTML_FILE} ({total} entries)")


if __name__ == "__main__":
    main()
