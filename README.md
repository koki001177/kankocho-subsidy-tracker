# 観光庁 補助金事業 自動更新トラッカー

観光庁の公募ページを毎日自動で取得し、差分があれば一覧HTMLを更新するシステム。

## 仕組み

```
[GitHub Actions 毎朝9:00 JST]
        ↓
[scraper.py] 観光庁公募ページをスクレイピング
        ↓
[subsidy_data.json] と比較し差分検出
        ↓
[generate_html.py] index.html を再生成
        ↓
[git commit & push] 自動コミット
        ↓
[GitHub Pages] 公開URLでブラウザから閲覧
```

## セットアップ手順

### 1. GitHubリポジトリ作成

1. GitHubで新しいリポジトリを作成（例: `kankocho-subsidy-tracker`）
2. プライベートでもパブリックでもOK（パブリックなら無料無制限）

### 2. ローカルにファイル配置

このフォルダ全体（`scraper.py`, `generate_html.py`, `.github/`, `README.md`）をリポジトリにコミットしてpush。

```bash
cd kankocho-tracker
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<your-user>/kankocho-subsidy-tracker.git
git push -u origin main
```

### 3. GitHub Pages を有効化

1. リポジトリの **Settings → Pages**
2. **Source** を `GitHub Actions` に設定

### 4. 初回実行

リポジトリの **Actions** タブ → `Daily Subsidy Update` → **Run workflow** で手動実行。
完了後、`index.html` と `subsidy_data.json` が自動コミットされ、GitHub PagesのURLで閲覧可能になる。

### 5. 自動実行

以降は毎朝 9:00 JST に自動実行される。差分があれば自動でHTML更新＆コミット。

## ローカルでの動作確認

```bash
python3 scraper.py        # スクレイピング → JSON更新
python3 generate_html.py  # HTML生成
open index.html           # ブラウザで確認（macOS）
```

## ファイル構成

| ファイル | 役割 |
|---------|------|
| `scraper.py` | 観光庁公募ページのスクレイピング・差分検出 |
| `generate_html.py` | JSONからHTMLを生成 |
| `subsidy_data.json` | 補助金マスタデータ（自動更新） |
| `index.html` | 公開用HTML（自動更新） |
| `update_log.txt` | 更新履歴ログ（自動追記） |
| `.github/workflows/daily-update.yml` | GitHub Actions定義 |

## 静的データの追加・編集

公募ページに載らない予算額・補助率・概要などは `scraper.py` 内の `ENRICHMENT` 辞書で補完している。新事業の詳細を追加したい場合はここを編集。

```python
ENRICHMENT = {
    "事業名のキーワード": {
        "budget_year": "令和8年度",
        "budget_amount": "100億円",
        "rate": "上限2億円(2/3)",
        "target": "自治体・DMO等",
        "summary": "事業概要のテキスト",
        "note": "備考",
        "highlight": True,  # 注目バッジ
        "is_new": True,     # 新規バッジ
    },
}
```

## 通知連携（オプション）

LINE Notify、Slack、メール通知などを追加したい場合は `.github/workflows/daily-update.yml` の `steps.scrape.outputs.has_diff` を判定して通知ステップを追加可能。

例: 差分があった場合のみLINE通知:

```yaml
- name: Notify on diff
  if: steps.scrape.outputs.has_diff == 'true'
  run: |
    curl -X POST -H "Authorization: Bearer ${{ secrets.LINE_TOKEN }}" \
      -F "message=観光庁補助金に更新がありました（新規:${{ steps.scrape.outputs.added_count }}件）" \
      https://notify-api.line.me/api/notify
```

## トラブルシューティング

### スクレイピングが0件になる
観光庁ページのHTML構造が変わった可能性。`KoboParser`クラスを調整。

### GitHub Actionsが動かない
- リポジトリ Settings → Actions → General で「Allow all actions」を有効に
- `permissions: contents: write` が設定されているか確認

### GitHub Pagesにアクセスできない
- Settings → Pages で Source が `GitHub Actions` になっているか
- 初回デプロイには数分かかる

## ライセンス

個人利用・社内利用想定。観光庁公募ページの利用規約に従うこと。
