# 議論メモ: FRASER FOMCコーパス進捗 + 記者会見PDFソース変更

**日付**: 2026-06-11
**議論ID**: disc-2026-06-11-fraser-presconf-pdf
**Project**: quants-fraser-fomc-corpus
**参加**: ユーザー + AI
**前回メモ**: [2026-06-10_discussion-fraser-fomc-corpus.md](2026-06-10_discussion-fraser-fomc-corpus.md)

## 背景・コンテキスト

前回（2026-06-10）にFOMC 4種文書のインベントリ構築と記者会見92件のダウンロードまで完了していた。
今回はコンテキスト復元から開始し、残タスクの実行と記者会見ソースの方針変更を行った。

## 今回の実施内容

### 1. act-2026-06-10-007 完了: 全テキスト一括ダウンロード

- `fomc_corpus.py download --types statement,minutes,beige_book,redbook` を実行
- 全5種 1,103ユニークファイル取得完了（statement 246 / minutes 278 / press_conference 92 /
  beige_book 344 / redbook 143）。空ファイルゼロ
- inventory 1,106行との差分3行は欠落ではなく重複ファイル名（COVID臨時会合等で
  同一ファイルが複数会合itemに紐づく: `BeigeBook_20200304.txt`、`fomcminutes20191030.txt`、
  `fomcminutes20200315.txt`）

### 2. act-2026-06-10-008 完了: Point-in-Time変換（release_date列）

- `fomc_corpus.py` に `poit` サブコマンド（`add_release_dates`）を実装、inventory全1,106行に付与
- 変換ルール:
  - statement / press_conference / beige_book / redbook: `release_date = doc_date`（既に公表日）
  - minutes 2004-12-14会合以降: +21日（expedited release。境界は「2005以降」から史実に精緻化。
    第1号の2004-12-14会合分は2005-01-04公表 = ちょうど+21日）
  - minutes 1993〜2004-11: 次回会合の最終日+3日（旧方針、実遅延37〜51日）
  - 土日着地は翌月曜にロール（PoiT保守側）
- 検証: 実公表日4件と全一致（2005-01-04 / 2019-02-20 / 2019-11-20 / 2023-02-22）
- 既知の限界: COVID臨時会合等で実公表が数日ずれる例外あり（2020-03-15会合分:
  計算 2020-04-06 vs 実際 2020-04-08）。厳密なイベントスタディでは個別確認を推奨

### 3. 方針変更: 記者会見はFRB公式PDFを真とする（dec-2026-06-11-001）

act-2026-06-10-009（PRELIMINARY 16件の補完）の内容説明から議論が発展し、方針を変更:

- **変更前**: FRASERテキストを基本とし、直近のPRELIMINARY版16件のみfederalreserve.govで補完
- **変更後**: **全92会見をfederalreserve.gov公式PDFから取得し、PDFから直接抽出した
  テキストを真とする**。FRASERのpress_conferenceテキストは分析に使用しない
- 根拠: FRASER直近16件は冒頭発言のみ（語数<3000）で完全版反映は1年超遅れ。
  Q&A部分こそタカ派/ハト派分析の主要情報源。FRASER版は2015-12-16のような
  不完全ファイル（2,207語、PDFでは26ページ）も含まれていた

### 4. act-2026-06-11-001 完了: 全92会見PDFの一括ダウンロード

- URLパターン: `https://www.federalreserve.gov/mediacenter/files/FOMCpresconf{YYYYMMDD}.pdf`
  （2011-04-27初回・2020-03-03臨時電話会見・2026-04-29直近を含む5件で事前検証、全件200。
  `monetarypolicy/files/` 側は404）
- `fomc_corpus.py` に `download-presconf-pdf` サブコマンドを実装
  （`%PDF` マジックバイト検証・取得済みスキップ付き）
- 92/92件取得、failed 0、合計15MB（`data/pdfs/press_conference/`）
- ページ数検証で完全版（Q&A込み）を確認: 2026-04-29: 28p / 2024-05-01: 26p / 2015-12-16: 26p
  （冒頭発言のみなら4〜6ページ相当）。最小は2020-03-03の45KB（短い電話会見で正当）

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-06-11-001 | 議長記者会見は全92件をFRB公式PDFから取得し、PDF抽出テキストを真とする。FRASER版は分析に使用しない。テキスト抽出は別act | FRASER直近16件はPRELIMINARY版。dec-2026-06-10-009の「直近分のみ補完」を全件PDF方式に変更 |

## アクションアイテム（プロジェクト全体の最新状態）

| ID | 内容 | 優先度 | 状態 |
|----|------|--------|------|
| act-2026-06-10-007 | 全テキスト一括ダウンロード | 高 | ✅ completed（2026-06-11） |
| act-2026-06-10-008 | PoiT変換（release_date列） | 高 | ✅ completed（2026-06-11） |
| act-2026-06-10-009 | PRELIMINARY 16件補完 | 中 | ⛔ superseded（dec-2026-06-11-001） |
| act-2026-06-10-010 | fraser_test.ipynb整理 + APIキーローテーション検討 | 中 | pending |
| act-2026-06-11-001 | 全92会見PDFの一括ダウンロード | 高 | ✅ completed（2026-06-11） |
| act-2026-06-11-002 | 会見PDF 92件からのテキスト抽出実装（ライブラリ選定から。pypdf等は未インストール）。FRASER版テキストの扱い（退避/削除）も決定 | 高 | pending |

## 次回の議論トピック

- act-2026-06-11-002: PDFテキスト抽出の実装（抽出ライブラリ選定、話者ラベル・ページ番号等の整形方針）
- 成果物のgitコミット方針（PDF 92件・テキスト1,011件を含めるか、`.gitignore` 対象とするか）
- 埋め込み分析パイプラインの設計（モデル選定、チャンク戦略、タカ派・ハト派指数の構築方法）【前回持ち越し】
- 1993年以前への拡張（旧形式議事録: MoA/RoPA/MoD等）【前回持ち越し】
- federalreserve.govからのリアルタイム取得側（公表当日）との統合設計【前回持ち越し】

## 参考情報

- FRB会見PDF: APIキー不要、User-Agent付きで取得可。全92件が同一URLパターンで存在
- 成果物はすべて未コミット: `fomc_corpus.py`（poit / download-presconf-pdf 追加）、
  `fomc_inventory.csv`（release_date列追加）、`data/texts/` 1,011ファイル追加、
  `data/pdfs/press_conference/` 92ファイル（15MB）
