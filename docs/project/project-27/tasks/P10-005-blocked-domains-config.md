# P10-005: config.yamlにblocked_domains追加

## 概要

ペイウォールやボット検出を行うドメインのブロックリストを設定ファイルに追加する。

## 背景

以下のドメインでHTTP 401/403エラーが発生:
- `seekingalpha.com` (403 Forbidden) - 14件
- `wsj.com` (401 Unauthorized) - ペイウォール
- `reuters.com` (401 Unauthorized) - ペイウォール

## 変更内容

### 変更ファイル

| ファイル | 変更内容 |
|----------|----------|
| `data/config/news-collection-config.yaml` | `blocked_domains` セクション追加 |

### 実装詳細

```yaml
# data/config/news-collection-config.yaml

# ===========================================
# ドメインフィルタリング
# ===========================================

# ブロックするドメイン（記事収集対象外）
blocked_domains:
  # ペイウォール（HTTP 401）
  - wsj.com
  - reuters.com
  - ft.com
  - bloomberg.com
  - barrons.com

  # ボット検出（HTTP 403）
  - seekingalpha.com

  # その他（抽出困難）
  - twitter.com
  - x.com

# ドメインフィルタリング設定
domain_filtering:
  enabled: true
  log_blocked: true  # ブロック時にログ出力
```

## 受け入れ条件

- [ ] `blocked_domains` リストがconfig.yamlに追加される
- [ ] YAMLの構文が正しい
- [ ] 既存の設定と競合しない
- [ ] ドキュメントに設定説明を追加

## 設定値の説明

| ドメイン | 理由 | エラーコード |
|----------|------|-------------|
| wsj.com | ペイウォール | HTTP 401 |
| reuters.com | ペイウォール | HTTP 401 |
| ft.com | ペイウォール | HTTP 401 |
| bloomberg.com | ペイウォール | HTTP 401 |
| barrons.com | ペイウォール | HTTP 401 |
| seekingalpha.com | ボット検出 | HTTP 403 |
| twitter.com | 動的コンテンツ | 抽出失敗 |
| x.com | 動的コンテンツ | 抽出失敗 |

## 依存関係

- 依存先: P10-002
- ブロック: P10-006

## 見積もり

- 作業時間: 10分
- 複雑度: 低
