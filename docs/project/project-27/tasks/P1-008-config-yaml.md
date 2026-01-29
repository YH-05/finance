# P1-008: news-collection-config.yaml 作成

## 概要

ワークフロー設定ファイルを作成する。

## フェーズ

Phase 1: 基盤（モデル・設定・インターフェース）

## 依存タスク

- P1-007: config.py 設定ファイル読み込み機能実装

## 成果物

- `data/config/news-collection-config.yaml`（新規作成）

## 実装内容

project.md に記載の設定ファイル内容をそのまま作成する。

主要セクション：
- `version`: "1.0"
- `status_mapping`: カテゴリ → GitHub Status マッピング
- `github_status_ids`: Status 名 → ID マッピング
- `rss`: RSS設定
- `extraction`: 本文抽出設定
- `summarization`: 要約設定
- `github`: GitHub設定
- `filtering`: フィルタリング設定
- `output`: 出力設定

## 受け入れ条件

- [ ] project.md に記載の設定項目がすべて含まれている
- [ ] status_mapping, github_status_ids, rss, extraction, summarization, github, filtering, output セクションが存在
- [ ] `load_config()` で正常に読み込める
- [ ] YAML 構文が正しい

## 参照

- project.md: 設定ファイルセクション
