#!/usr/bin/env python3
"""
観光庁公募ページのスクレイピング
- https://www.mlit.go.jp/kankocho/kobo_2026_00003.html を取得
- 各エントリ（公開日、ステータス、事業名、対象、締切、リンク）を抽出
- subsidy_data.json と比較し、差分を検出
- 差分があれば JSON を更新し、ログを出力
"""

import json
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from html.parser import HTMLParser

BASE_DIR = Path(__file__).resolve().parent
KOBO_URL = "https://www.mlit.go.jp/kankocho/kobo_2026_00003.html"
KOBO_BASE = "https://www.mlit.go.jp"
DATA_FILE = BASE_DIR / "subsidy_data.json"
LOG_FILE = BASE_DIR / "update_log.txt"
USER_AGENT = "Mozilla/5.0 (kankocho-subsidy-tracker)"


# ===== 静的補完情報 =====
# 公募ページに載らない予算額・補助率・備考を補う辞書
# 事業名の部分一致でマージされる
ENRICHMENT = {
    "オーバーツーリズムの未然防止・抑制をはじめとする観光地の面的受入環境整備促進事業": {
        "budget_year": "令和8年度",
        "budget_amount": "100億円",
        "rate": "上限2億円(2/3)、5,000万円(1/2)",
        "target": "自治体・DMO・観光事業者等",
        "summary": "中長期視点での地域一体オーバーツーリズム対策。混雑可視化、予約システム整備、観光客と住民の動線分離など。",
        "note": "前年比8.3倍 / 事前着手届出4/17 12:00まで",
        "highlight": True,
    },
    "観光地・観光産業における省力化投資補助事業": {
        "budget_year": "R7補正",
        "budget_amount": "—",
        "rate": "前年から上限倍増",
        "target": "宿泊業",
        "summary": "自動チェックイン機、配膳ロボット、PMS導入等の省力化投資。本格的な人手不足対応投資が可能に。",
        "note": "人手不足対応",
    },
    "地方誘客促進に向けたインバウンド安全・安心対策推進事業": {
        "budget_year": "R7補正",
        "budget_amount": "8.8億円",
        "rate": "—",
        "target": "自治体・DMO・観光事業者等",
        "summary": "インバウンド受入地域における安全・安心対策の推進。多言語対応の災害情報・医療案内、保険整備等。",
    },
    "全国の観光地・観光産業における観光DX推進事業": {
        "budget_year": "令和8年度",
        "target": "宿泊業・観光事業者等",
        "summary": "キャッシュレス決済端末、観光アプリ、デジタルチケット、PMS、AIチャットボット等のデジタルツール導入支援。",
        "note": "予約・顧客管理一元化、多言語対応",
    },
    "地域資源を活用した観光まちづくり推進事業": {
        "budget_year": "令和8年度",
        "summary": "歴史的資源（古民家等）、食、自然、文化資源の施設整備支援。地方分散促進、観光客と住民の動線分離。",
    },
    "宿泊施設サステナビリティ強化支援事業": {
        "budget_year": "令和8年度",
        "target": "宿泊業（旅館業法許可必須）",
        "summary": "省エネ型空調、太陽光発電、蓄電設備、温室効果ガス排出量計測システム等。ESG投資・環境意識への対応。",
    },
    "ユニバーサルツーリズム促進事業": {
        "budget_year": "令和8年度",
        "budget_amount": "40億円",
        "rate": "1/2、上限1,500万円",
        "summary": "観光施設・宿泊施設のバリアフリー化に必要な施設整備、設備導入支援。",
    },
    "観光需要分散のための地域観光資源のコンテンツ化促進事業": {
        "budget_year": "R7補正",
        "budget_amount": "49億円",
        "summary": "観光客の地方分散・地域消費額拡大。R7「地域魅力向上事業」「プレミアムインバウンドツアー集中支援事業」の後継。",
        "note": "オーバーツーリズム解消目的",
    },
    "デジタルノマド誘客に向けたモデル実証事業": {
        "budget_year": "令和8年度",
        "summary": "ワーケーション環境整備、長期滞在型サービス開発。デジタルノマド誘客モデル事業。",
        "note": "新規事業",
        "is_new": True,
    },
    "文化資源を活用した全国各地のインバウンド創出・拡大": {
        "budget_year": "令和8年度",
        "budget_amount": "224億円",
        "summary": "文化庁・観光庁連携事業。文化財・伝統文化のインバウンド向け活用、海外展開強化。",
        "note": "前年度比大幅増 / 文化庁連携",
        "highlight": True,
    },
    "国立公園等のインバウンドに向けた環境整備": {
        "budget_year": "令和8年度",
        "budget_amount": "178億円",
        "summary": "国立公園・国民公園・世界自然遺産の受入環境整備、魅力向上。",
        "note": "前年比約3倍",
    },
    "DMO総合支援事業": {
        "budget_year": "令和8年度",
        "summary": "DMO体制整備、万博レガシー活用事業。",
    },
    "能登半島地震からの復興に向けた観光再生支援事業": {
        "budget_year": "令和8年度",
        "summary": "能登半島地震被災地の観光再生支援。",
    },
    "MICE": {
        "budget_year": "令和8年度",
        "summary": "地域のMICE誘致力強化支援。",
    },
}


# ===== HTTP取得 =====
def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


# ===== HTMLパーサー：観光庁公募ページから各エントリを抽出 =====
class KoboParser(HTMLParser):
    """
    観光庁公募ページの構造:
      <a href="/kankocho/kobo08_00057.html">
        2026年2月26日 募集中 :   令和８年度「○○事業」の公募開始
        その他観光関係者 自治体・DMO ...
        【締切日】2026年5月29日
      </a>
    """
    def __init__(self):
        super().__init__()
        self.entries = []
        self.in_link = False
        self.current_href = ""
        self.buffer = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            attrs_d = dict(attrs)
            href = attrs_d.get("href", "")
            # 公募詳細ページへのリンクのみ拾う
            if "/kankocho/" in href and ("kobo" in href or "topics" in href):
                self.in_link = True
                self.current_href = href
                self.buffer = []

    def handle_endtag(self, tag):
        if tag == "a" and self.in_link:
            text = " ".join(self.buffer).strip()
            text = re.sub(r"\s+", " ", text)
            if text:
                self._add_entry(text, self.current_href)
            self.in_link = False
            self.buffer = []

    def handle_data(self, data):
        if self.in_link:
            self.buffer.append(data)

    def _add_entry(self, text, href):
        # "2026年2月26日 募集中 : 令和８年度「...」の公募開始 ..." のような構造から抽出
        m = re.match(
            r"(\d{4}年\d{1,2}月\d{1,2}日)\s*"
            r"(募集中|募集終了|採択結果|募集結果)?\s*"
            r"[:：]?\s*(.+)", text
        )
        if not m:
            return

        pub_date = m.group(1)
        status_raw = m.group(2) or ""
        rest = m.group(3)

        # 締切抽出
        deadline_m = re.search(r"【締切日】\s*(\d{4}年\d{1,2}月\d{1,2}日)", rest)
        deadline = deadline_m.group(1) if deadline_m else ""

        # 締切表記を本文から除去
        title_part = re.sub(r"【締切日】[^】]*\d{4}年\d{1,2}月\d{1,2}日", "", rest).strip()

        # カテゴリタグ抽出（その他観光関係者・宿泊業・旅行業 等）
        category_tags = []
        for tag in ["その他観光関係者", "交通", "宿泊業", "旅行業",
                    "自治体・DMO", "観光施設", "一般の方"]:
            if tag in title_part:
                category_tags.append(tag)
                title_part = title_part.replace(tag, "")
        title = re.sub(r"\s+", " ", title_part).strip()

        # ステータスを正規化
        status = self._normalize_status(status_raw)

        full_url = KOBO_BASE + href if href.startswith("/") else href

        self.entries.append({
            "id": href.rstrip("/").split("/")[-1].replace(".html", ""),
            "published": pub_date,
            "status_raw": status_raw,
            "status": status,
            "title": title,
            "categories": category_tags,
            "deadline": deadline,
            "url": full_url,
        })

    @staticmethod
    def _normalize_status(s):
        mapping = {
            "募集中": "open",
            "募集終了": "closed",
            "採択結果": "result",
            "募集結果": "result",
        }
        return mapping.get(s, "unknown")


def parse_kobo_page(html):
    p = KoboParser()
    p.feed(html)
    # 重複除去（同じID）
    seen = set()
    unique = []
    for e in p.entries:
        if e["id"] in seen:
            continue
        seen.add(e["id"])
        unique.append(e)
    return unique


# ===== Enrichment（静的データのマージ） =====
def enrich(entries):
    for e in entries:
        e.setdefault("budget_year", "")
        e.setdefault("budget_amount", "—")
        e.setdefault("rate", "—")
        e.setdefault("target", "—")
        e.setdefault("summary", e["title"])
        e.setdefault("note", "")
        e.setdefault("highlight", False)
        e.setdefault("is_new", False)

        for keyword, data in ENRICHMENT.items():
            if keyword in e["title"]:
                for k, v in data.items():
                    if not e.get(k) or e[k] in ("", "—"):
                        e[k] = v
                break
    return entries


# ===== 差分検出 =====
def diff_entries(old_list, new_list):
    """新規追加・ステータス変更・削除を検出"""
    old_map = {e["id"]: e for e in old_list}
    new_map = {e["id"]: e for e in new_list}

    added = [new_map[i] for i in new_map if i not in old_map]
    removed = [old_map[i] for i in old_map if i not in new_map]
    changed = []
    for i in new_map:
        if i in old_map:
            o, n = old_map[i], new_map[i]
            diffs = {}
            for key in ["status", "deadline", "title"]:
                if o.get(key) != n.get(key):
                    diffs[key] = (o.get(key), n.get(key))
            if diffs:
                changed.append({"id": i, "title": n["title"], "diffs": diffs})

    return added, removed, changed


# ===== ログ出力 =====
def write_log(added, removed, changed):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [f"\n===== {now} ====="]

    if not (added or removed or changed):
        lines.append("差分なし")
    else:
        if added:
            lines.append(f"【新規追加】{len(added)}件")
            for e in added:
                lines.append(f"  + [{e['status']}] {e['title']} (締切: {e['deadline'] or '—'})")
        if changed:
            lines.append(f"【変更】{len(changed)}件")
            for c in changed:
                lines.append(f"  ~ {c['title']}")
                for k, (o, n) in c["diffs"].items():
                    lines.append(f"      {k}: {o} → {n}")
        if removed:
            lines.append(f"【削除】{len(removed)}件")
            for e in removed:
                lines.append(f"  - {e['title']}")

    log_text = "\n".join(lines)
    print(log_text)

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_text + "\n")


# ===== メイン =====
def main():
    print(f"[{datetime.now()}] Fetching {KOBO_URL}")
    try:
        html = fetch(KOBO_URL)
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        print(f"ERROR: fetch failed: {e}", file=sys.stderr)
        sys.exit(1)

    entries = parse_kobo_page(html)
    entries = enrich(entries)
    print(f"Parsed {len(entries)} entries")

    # 既存データ読み込み
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            old_data = json.load(f)
        old_entries = old_data.get("entries", [])
    else:
        old_entries = []

    # 差分検出
    added, removed, changed = diff_entries(old_entries, entries)
    has_diff = bool(added or removed or changed)

    write_log(added, removed, changed)

    # JSON保存（常に保存 = 初回や追加情報の更新に対応）
    data = {
        "last_updated": datetime.now().isoformat(timespec="seconds"),
        "source_url": KOBO_URL,
        "entries": entries,
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # GitHub Actions 用：差分の有無を環境変数で出力
    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"has_diff={'true' if has_diff else 'false'}\n")
            f.write(f"added_count={len(added)}\n")
            f.write(f"changed_count={len(changed)}\n")
            f.write(f"removed_count={len(removed)}\n")

    sys.exit(0)


if __name__ == "__main__":
    import os
    main()
