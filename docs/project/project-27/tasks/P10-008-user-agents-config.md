# P10-008: config.yamlにuser_agents追加

## 概要

User-Agentローテーション用の設定を追加する。

## 背景

一部サイトはボット検出でUser-Agentをチェックしている。複数のUser-Agentをローテーションすることで検出を回避する。

## 変更内容

### 変更ファイル

| ファイル | 変更内容 |
|----------|----------|
| `data/config/news-collection-config.yaml` | `user_agents` セクション追加 |

### 実装詳細

```yaml
# data/config/news-collection-config.yaml

# ===========================================
# 本文抽出設定
# ===========================================

extraction:
  concurrency: 5
  timeout_seconds: 30
  min_body_length: 200
  max_retries: 3

  # User-Agent ローテーション
  user_agent_rotation:
    enabled: true
    user_agents:
      - "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
      - "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
      - "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
      - "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15"
      - "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
```

## 受け入れ条件

- [ ] `user_agent_rotation` セクションが追加される
- [ ] 5種類以上のUser-Agentが設定される
- [ ] YAMLの構文が正しい
- [ ] 既存の `extraction` 設定と統合される

## User-Agent選定基準

- 最新のChrome/Firefox/Safariバージョン
- Windows/Mac/Linuxの各OS
- 実際のブラウザで使用されているもの

## 依存関係

- 依存先: P10-002
- ブロック: P10-009

## 見積もり

- 作業時間: 10分
- 複雑度: 低
