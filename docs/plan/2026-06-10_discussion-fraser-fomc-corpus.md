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
| act-2026-06-10-007 | 残り3種+redbookの一括ダウンロード実行（`download --types statement,minutes,beige_book,redbook`） | 高 |
| act-2026-06-10-008 | PoiT変換実装（Minutes公表日: 2005以降=会合+3週、1993-2004=次回会合+3日。release_date列追加） | 高 |
| act-2026-06-10-009 | 会見PRELIMINARY版16件の完全版をfederalreserve.govから補完 | 中 |
| act-2026-06-10-010 | fraser_test.ipynb整理 + ハードコードされたAPIキーのローテーション検討 | 中 |

## 次回の議論トピック

- 埋め込み分析パイプラインの設計（モデル選定、チャンク戦略、タカ派・ハト派指数の構築方法）
- 1993年以前への拡張（旧形式議事録: MoA/RoPA/MoD/歴史的Minutes、分類サブタイプは調査済み）
- federalreserve.govからのリアルタイム取得側（公表当日）との統合設計

## 参考情報

- FRASER API: レート制限30req/分（メタデータのみ）。テキスト本体はAPIキー不要・User-Agent必須
- FRASER API公式ドキュメント: https://fraser.stlouisfed.org/files/docs/fraser-api-user-documentation-v1.pdf
- 声明文の年次件数は制度史と一致: 1994-98年は政策変更時のみ、1999年5月から毎会合、2020年はCOVID臨時会合で12件
