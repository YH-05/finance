# エビデンスベース開発

## 禁止語と推奨語

| 禁止 | 推奨 |
|------|------|
| best, optimal | measured X, documented Y |
| faster, slower | reduces X%, increases Y ms |
| always, never | typically, in most cases |
| perfect, ideal | meets requirement X |

## 証拠要件

### 性能

```
"measured Xms" | "reduces X%"
```

例:
- "measured 150ms response time"
- "reduces memory usage by 30%"

### 品質

```
"coverage X%" | "complexity Y"
```

例:
- "coverage 85%"
- "cyclomatic complexity reduced from 15 to 8"

### セキュリティ

```
"scan detected X"
```

例:
- "Bandit scan detected 0 high severity issues"
- "OWASP ZAP found no critical vulnerabilities"

## 主張と根拠の対応

```python
# 主張する場合は必ず根拠を示す

# 性能改善
"処理時間を改善" → "処理時間を 500ms から 150ms に短縮（70% 改善）"

# 品質向上
"テストを追加" → "カバレッジを 60% から 85% に向上"

# セキュリティ
"脆弱性を修正" → "SQLインジェクション脆弱性（CWE-89）を修正"
```

## 測定可能な基準

### コードカバレッジ目標

| テスト種別 | 目標 |
|-----------|------|
| ユニットテスト | 80%以上 |
| 統合テスト | 60%以上 |
| E2Eテスト | 主要フロー100% |

### パフォーマンス基準

| 項目 | 基準 |
|------|------|
| API応答時間 | 95パーセンタイル < 200ms |
| ページ読み込み | First Contentful Paint < 1.5s |
| メモリ使用量 | 増加率 < 10%/hour（リーク検出） |

## レビューでの使用

### 悪い例

```markdown
このコードはダメです。
パフォーマンスが悪いです。
```

### 良い例

```markdown
この実装だと O(n²) の時間計算量になります。
dict を使うと O(n) に改善できます:

```python
task_map = {t.id: t for t in tasks}
result = [task_map.get(id) for id in ids]
```

計測結果: 1000件のデータで 500ms → 5ms に改善
```

## コミットメッセージでの使用

```
perf(api): レスポンス時間を70%短縮

変更前: 平均500ms
変更後: 平均150ms

- N+1クエリを解消（50件のDBクエリ → 2件）
- インメモリキャッシュを導入

Measured with: Apache Bench (100 concurrent requests)
```
