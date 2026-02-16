# /ca-eval — 競争優位性評価

KYの投資判断軸に基づいて、アナリストレポートの競争優位性を評価するワークフローを実行します。

## 使用方法

```
/ca-eval TICKER
/ca-eval ORLY
/ca-eval CHD --report path/to/report.md
```

## パラメータ

| パラメータ | 必須 | デフォルト | 説明 |
|-----------|------|-----------|------|
| ticker | Yes | - | 評価対象のティッカーシンボル（例: ORLY, COST, CHD） |
| --report | No | analyst/raw/ 配下を自動検索 | アナリストレポートのパス |

## スキル

$SKILL:ca-eval
