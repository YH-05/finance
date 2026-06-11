# 議論メモ: FRASER FOMC 4種文書コーパス構築

**日付**: 2026-06-10
**議論ID**: disc-2026-06-10-fraser-fomc-corpus
**Project**: quants-fraser-fomc-corpus
**参加**: ユーザー + AI

## 背景・コンテキスト

FRASERからテキストデータをダウンロードしてクオンツ分析（ベクトル埋め込み等）に活用する構想。
FRASERで取得可能なデータの調査から始め、FOMC 4種文書（声明文・Minutes・議長記者会見・Beige Book）の
ヒストリカル一括取得の実装まで完了した。

## 議論のサマリー

1. **FRASERデータ調査**: API公式ドキュメント（v1.0.0）と実APIで全体像を確認。
   主要コレクション: FOMC会合文書(title 677)、FRB要人講演(3762)、FRB Bulletin(62)、
   Commercial and Financial Chronicle(1339、1865年〜)、Economic Report of the President(45)等。
2. **Transcripts vs Minutes**: Transcriptsは5年ラグのためリアルタイム分析はMinutesで代用が標準。
   会合Transcripts（非公開審議の逐語録）と議長記者会見トランスクリプト（公開イベント）は別物。
3. **カテゴリ指定APIの不在**: 全5,151 title走査で確認。Beige Book等の独立シリーズはなく、
   全てtitle 677の会合item内のファイル。ファイル単位の種別メタデータもなし→ファイル名規約分類が必須。
4. **命名規約の全数調査**: 全1,038 item・7,338ファイルを調査し103パターンを特定。
   4種の命名変遷を導出し、年次カウントが制度史と完全一致することで検証（誤分類ゼロ）。

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-06-10-008 | FOMC 4種テキストはFRASER title 677からファイル名規約分類で一括取得 | カテゴリ指定API不在を全title走査で確認。Beige Bookは5世代の命名変遷 |
| dec-2026-06-10-009 | リアルタイム分析はMinutes+声明文で代用、Transcriptsはヒストリカル検証用。直近の会見完全版はfederalreserve.govで補完 | FRASERの直近会見はPRELIMINARY版（冒頭発言のみ、92件中16件） |
| dec-2026-06-10-010 | fomc_corpus.py + fomc_inventory.csv（1,106ファイル）を成果物として作成 | statement 246 / minutes 280 / press_conference 92 / beige_book 345 / redbook 143 |

## 成果物

| ファイル | 内容 |
|---------|------|
| `notebook/FRASER/fomc_corpus.py` | 分類器（正規表現・検証済み）+ インベントリ構築 + 一括ダウンローダ |
| `notebook/FRASER/data/fomc_inventory.csv` | 1,106ファイルの全量カタログ（doc_type・doc_date・text/pdf URL） |
| `notebook/FRASER/data/texts/press_conference/` | 記者会見92件ダウンロード済み（動作実証） |

### 命名規約（調査結果）

| doc_type | 期間 | パターン変遷 |
|----------|------|-------------|
| statement | 1994〜 | `YYYYMMDDstatement` → `monetaryYYYYMMDDa1` (2019〜) |
| minutes | 1993〜 | `YYYYMMDDmin` → `fomcminutesYYYYMMDD` (2007〜) |
| press_conference | 2011〜 | `FOMCpresconfYYYYMMDD` (+`_final`/`-final`/`_f`) |
| beige_book | 1983〜 | `fomc*beige*` → `*beigebook` → `*beige` → `fullreport*` → `BeigeBook_*` |
| redbook | 1970-83 | `fomc{会合日}redbook{公表日}`（Beige Book前身） |

## アクションアイテム

| ID | 内容 | 優先度 |
|----|------|--------|
| act-2026-06-10-007 | ~~残り3種+redbookの一括ダウンロード実行~~ ✅ **完了（2026-06-11）** | 高 |
| act-2026-06-10-008 | ~~PoiT変換実装（release_date列追加）~~ ✅ **完了（2026-06-11）** | 高 |
| act-2026-06-10-009 | ~~会見PRELIMINARY版16件の補完~~ ⛔ **superseded（2026-06-11、dec-2026-06-11-001で全件PDF方式に変更）** | 中 |
| act-2026-06-10-010 | fraser_test.ipynb整理 + ハードコードされたAPIキーのローテーション検討 | 中 |
| act-2026-06-11-001 | 全92会見の完全版PDFをfederalreserve.govから一括ダウンロード（`download-presconf-pdf`） | 高 |
| act-2026-06-11-002 | 会見PDF 92件からのテキスト抽出実装（ライブラリ選定含む）。FRASER版テキストの扱いも決定 | 高 |

## 進捗追記（2026-06-11）

> 詳細は [2026-06-11_discussion-fraser-presconf-pdf.md](2026-06-11_discussion-fraser-presconf-pdf.md) を参照。

act-2026-06-10-007 完了。`fomc_corpus.py download --types statement,minutes,beige_book,redbook` を実行し、
全5種 1,103ユニークファイルの取得が完了（statement 246 / minutes 278 / press_conference 92 / beige_book 344 / redbook 143）。
インベントリ1,106行との差分3行は欠落ではなく重複ファイル名（COVID臨時会合等で同一ファイルが複数会合itemに紐づく:
`BeigeBook_20200304.txt`、`fomcminutes20191030.txt`、`fomcminutes20200315.txt`）。空ファイルゼロを確認。

act-2026-06-10-008 完了。`fomc_corpus.py` に `poit` サブコマンド（`add_release_dates`）を実装し、
inventory 全1,106行に release_date 列を付与。変換ルール:

- statement / press_conference / beige_book / redbook: `release_date = doc_date`（既に公表日）
- minutes（会合最終日→公表日に変換）:
  - 会合 2004-12-14 以降: +21日（expedited release。境界はメモの「2005以降」から史実に精緻化:
    FRBの迅速公表は2004-12-14会合分が第1号、2005-01-04公表=ちょうど+21日）
  - 1993〜2004-11: 次回会合の会合最終日 +3日（旧方針、遅延37〜51日）
  - 土日着地は翌月曜にロール（PoiT保守側）

検証: 実公表日4件と全一致（2004-12-14会合→2005-01-04、2019-01-30→2019-02-20、
2019-10-30→2019-11-20、2023-02-01→2023-02-22）。minutes以外の release_date ≠ doc_date はゼロ。
既知の限界: COVID臨時会合等で実公表が数日ずれる例外あり（2020-03-15会合分は計算2020-04-06 vs 実際2020-04-08）。
厳密なイベントスタディでは実公表日の個別確認を推奨（docstringに明記済み）。

**方針変更（dec-2026-06-11-001）**: 議長記者会見トランスクリプトは、PRELIMINARY 16件の補完
（act-2026-06-10-009、superseded）ではなく、**全92件を federalreserve.gov 公式PDFから取得し、
PDFから直接抽出したテキストを真とする**方式に変更。FRASERのpress_conferenceテキストは分析に使用しない。

- URLパターン: `https://www.federalreserve.gov/mediacenter/files/FOMCpresconf{YYYYMMDD}.pdf`
  （2011-04-27初回・2020-03-03臨時電話会見・2026-04-29直近を含む5件で存在確認済み。
  `monetarypolicy/files/` 側は404）
- `fomc_corpus.py` に `download-presconf-pdf` サブコマンドを追加（保存先 `data/pdfs/press_conference/`、
  `%PDF` マジックバイト検証付き、取得済みスキップ）
- テキスト抽出は別工程（act-2026-06-11-002）

act-2026-06-11-001 完了。全92会見のPDFを取得（合計15MB、failed 0、全件 `%PDF` 検証OK）。
ページ数スポットチェック（2026-04-29: 28p / 2024-05-01: 26p / 2015-12-16: 26p）で
Q&A込み完全版であることを確認。FRASER版が2,207語しかなかった2015-12-16会見（リフトオフ）も
PDFは26ページの完全版だった。最小ファイルは2020-03-03（45KB、COVID緊急利下げ時の短い電話会見で正当）。

## 次回の議論トピック

- 埋め込み分析パイプラインの設計（モデル選定、チャンク戦略、タカ派・ハト派指数の構築方法）
- 1993年以前への拡張（旧形式議事録: MoA/RoPA/MoD/歴史的Minutes、分類サブタイプは調査済み）
- federalreserve.govからのリアルタイム取得側（公表当日）との統合設計

## 参考情報

- FRASER API: レート制限30req/分（メタデータのみ）。テキスト本体はAPIキー不要・User-Agent必須
- FRASER API公式ドキュメント: https://fraser.stlouisfed.org/files/docs/fraser-api-user-documentation-v1.pdf
- 声明文の年次件数は制度史と一致: 1994-98年は政策変更時のみ、1999年5月から毎会合、2020年はCOVID臨時会合で12件
