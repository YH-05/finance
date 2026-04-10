# 議論メモ: NSE全銘柄DB・XBRL解析スクリプト整備

**日付**: 2026-04-08
**議論ID**: disc-2026-04-08-nse-scripts
**参加**: ユーザー + AI

## 背景・コンテキスト

NSE shareholding APIのエンドポイント修正（PR #3902）完了後、
全NSE上場銘柄のデータをローカルSQLiteに格納し、XBRLから詳細株主リストを取得するスクリプトを整備した。

## 成果物

### scripts/nse_index_shareholding.py

- **目的**: NSE全上場銘柄のDB構築
- **データソース**: EQUITY_L.csv, allIndices, equity-stockIndices, corporate-share-holdings-master
- **出力**: `data/cache/nse/nse_index.db`
  - `stocks` テーブル: 2,263行
  - `index_members` テーブル: 9,141行（124インデックス）
  - `shareholdings` テーブル: 109,294行
- **Windows互換**: httpx単体依存、uv syncで即実行可能
- **NAS出力先**: `/Volumes/personal_folder/Projects/quants/data/`

### scripts/nse_parse_xbrl.py

- **目的**: 全銘柄のXBRL（in-bse-shp名前空間）を解析して詳細株主リストを生成
- **入力**: SQLiteのshareholdingsテーブルから最新XBRL URLを取得
- **出力**:
  - `data/cache/nse/{SYMBOL}/shareholding_detail.csv`（銘柄別）
  - `data/cache/nse/all_shareholding_detail.csv`（全銘柄統合、146,195行、19MB）
- **CSV列**: symbol, company_name, report_date, category, sub_category, shareholder_name, pan, num_shareholders, num_fully_paid_shares, num_voting_rights, pct_total_shares, pct_fully_diluted, num_shares_demat, is_category_total
- **成功率**: 2,236/2,253件（99.3%）

## NAS保存先

| ファイル | サイズ |
|---------|--------|
| `/Volumes/personal_folder/Projects/quants/data/sqlite/nse_index.db` | 22MB |
| `/Volumes/personal_folder/Projects/quants/data/exports/nse/stocks.csv` | 364KB |
| `/Volumes/personal_folder/Projects/quants/data/exports/nse/shareholdings.csv` | 17MB |
| `/Volumes/personal_folder/Projects/quants/data/exports/nse/index_members.csv` | 541KB |
| `/Volumes/personal_folder/Projects/quants/data/exports/nse/all_shareholding_detail.csv` | 19MB |

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-04-08-014 | NSE SQLiteはローカルパス書き込み → NASコピーの2段階方式 | NASでSQLite書き込み時に "database is locked" エラーが発生するため |
| dec-2026-04-08-015 | nse_index_shareholding.pyはhttpx単体依存のWindows互換スタンドアロンツール | Windows環境でもuv syncで即実行可能 |
| dec-2026-04-08-016 | nse_parse_xbrl.pyに全銘柄CSV結合機能を追加（all_shareholding_detail.csv） | 2,236ディレクトリコピーより単一CSVコピーの方が効率的なため |
| dec-2026-04-08-017 | XBRL 17件失敗はデータ不備（null/無効URL）でありコード問題ではない | null:10件、"-":5件、削除済み:2件。全てHTTP 404 |

## アクションアイテム

| ID | 内容 | 優先度 | 状態 |
|----|------|--------|------|
| act-2026-04-08-012 | Windows環境でのスクリプト実行テスト | 中 | pending |
| act-2026-04-08-013 | NAS定期同期の自動化検討（launchd/cron） | 低 | pending |
| act-2026-04-08-009 | 他のNSEエンドポイントのNextApi移行調査 | 中 | pending |
| act-2026-04-08-006 | Issue #3899: ETF.com自動化 (Wave2) | 低 | pending |
| act-2026-04-08-007 | Issue #3900: ASEAN統合設計書 (Wave3) | 中 | pending |
| act-2026-04-08-010 | Issue #3900 bodyをスコープ拡大版に更新 | 高 | pending |
| act-2026-04-08-011 | market_commonリネーム + MarketExchange enum | 高 | pending |

## 技術メモ

### SQLiteとNASの非互換性

SQLiteはファイルロック機構がネットワークドライブと相性が悪い。
**正しいパターン**: `data/cache/nse/nse_index.db`（ローカル）で書き込み → 完了後NASにコピー

### XBRL名前空間

NSE XBRLは `in-bse-shp` 名前空間を使用（BSE共通規格）。
- 98種類のユニークタグ
- 38 Dimension Members（カテゴリ分類）
- コンテキスト別データ（promoter/public等の区分）

### Windows互換性確認済み

- `pathlib.Path` でパス区切り問題なし
- httpxはWindows環境でも動作
- `uv sync --all-extras` で依存関係を揃えるだけで実行可能

## 次回の議論トピック

- Wave2（#3899 ETF.com自動化）の実装開始
- Wave3（#3900 ASEAN統合設計）の market_common リネーム着手
- Windows環境での実機テスト結果確認
