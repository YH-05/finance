# news.sinks

ニュース記事の出力先モジュール。

## 概要

ニュース記事をさまざまな出力先に書き込む Sink クラスを提供します。JSON ファイル出力と GitHub Issue/Project 出力に対応。

**対応出力先:**

| Sink | 出力先 | 用途 |
|------|--------|------|
| `FileSink` | JSON ファイル | ローカルデータ保存 |
| `GitHubSink` | GitHub Issue + Project | Issue 管理・プロジェクト追跡 |

## クイックスタート

### JSON ファイル出力

```python
from pathlib import Path
from news.sinks import FileSink, WriteMode

# 上書きモード（デフォルト）
sink = FileSink(output_dir=Path("data/news"))
sink.write(articles)
# → data/news/news_YYYYMMDD.json

# 追記モード（既存ファイルに追加、重複除外）
sink = FileSink(
    output_dir=Path("data/news"),
    write_mode=WriteMode.APPEND,
)
sink.write(articles)
```

### GitHub Issue 出力

```python
from news.sinks import GitHubSink, GitHubSinkConfig

# 設定で初期化
config = GitHubSinkConfig(
    project_number=24,
    labels=["news", "finance"],
    dry_run=False,
)
sink = GitHubSink(config=config)

# 記事を Issue として作成
sink.write(articles)
```

### バッチ出力

```python
# 複数の FetchResult をまとめて出力
results = [result1, result2, result3]
sink.write_batch(results)
```

## API リファレンス

### FileSink

JSON ファイル出力 Sink。`SinkProtocol` を実装。

**コンストラクタ:**

```python
FileSink(
    output_dir: Path = Path("data/news"),
    write_mode: WriteMode = WriteMode.OVERWRITE,
)
```

| パラメータ | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| `output_dir` | `Path` | `data/news` | 出力ディレクトリ |
| `write_mode` | `WriteMode` | `OVERWRITE` | 書き込みモード |

**メソッド:**

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `write(articles, metadata)` | 記事を JSON ファイルに書き出し | `bool` |
| `write_batch(results)` | 複数結果を一括出力 | `bool` |

**プロパティ:**

| プロパティ | 型 | 説明 |
|-----------|-----|------|
| `sink_name` | `str` | `"json_file"` |
| `sink_type` | `SinkType` | `SinkType.FILE` |

### WriteMode

| 値 | 説明 |
|----|------|
| `OVERWRITE` | 既存ファイルを上書き |
| `APPEND` | 既存ファイルに追加（重複除外） |

### GitHubSink

GitHub Issue/Project 出力 Sink。`SinkProtocol` を実装。

**コンストラクタ:**

```python
GitHubSink(config: GitHubSinkConfig)
```

**メソッド:**

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `write(articles, metadata)` | 記事を GitHub Issue として作成 | `bool` |
| `write_batch(results)` | 複数結果を一括 Issue 作成 | `bool` |

### GitHubSinkConfig

| フィールド | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| `project_number` | `int` | — | GitHub Project 番号（必須） |
| `repository` | `str \| None` | None | リポジトリ（"owner/repo"） |
| `labels` | `list[str]` | `[]` | Issue ラベル |
| `dry_run` | `bool` | False | ドライランモード |

## モジュール構成

```
news/sinks/
├── __init__.py   # パッケージエクスポート
├── file.py       # FileSink, WriteMode
├── github.py     # GitHubSink, GitHubSinkConfig
└── README.md     # このファイル
```

## 依存ライブラリ

| ライブラリ | 用途 |
|-----------|------|
| pydantic | GitHubSinkConfig のバリデーション |
| gh CLI | GitHub Issue/Project 操作 |

## 関連モジュール

- [news.core](../core/README.md) - SinkProtocol, SinkType 定義
- [news.processors](../processors/README.md) - パイプライン連携
- [news.config](../config/README.md) - Sink 設定（FileSinkConfig, GitHubSinkConfig）
