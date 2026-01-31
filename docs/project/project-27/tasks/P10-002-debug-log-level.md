# P10-002: ファイルログをDEBUGレベルに変更

## 概要

ファイル出力のログレベルをDEBUGに変更し、詳細な障害分析を可能にする。コンソール出力はINFOを維持。

## 背景

現在はファイルもコンソールも同一レベル（INFO）で出力しているが、障害分析にはDEBUGレベルの詳細情報が必要。

## 変更内容

### 変更ファイル

| ファイル | 変更内容 |
|----------|----------|
| `src/news/scripts/finance_news_workflow.py` | ファイルログレベルをDEBUGに固定 |
| `src/news/utils/logging_config.py` | ファイルとコンソールの分離設定 |

### 実装詳細

```python
# src/news/scripts/finance_news_workflow.py

def setup_logging(
    *,
    verbose: bool = False,
    log_dir: Path | None = None,
) -> Path:
    """ログ設定を初期化。

    - コンソール: verbose=True→DEBUG, False→INFO
    - ファイル: 常にDEBUG（詳細な障害分析用）
    """
    console_level = "DEBUG" if verbose else "INFO"
    file_level = "DEBUG"  # 常にDEBUG

    _setup_logging(
        level=console_level,
        file_level=file_level,  # 新パラメータ
        format="console",
        log_file=log_file,
        include_timestamp=True,
        include_caller_info=True,
        force=True,
    )
```

### logging_config.py の変更

```python
def setup_logging(
    level: str = "INFO",
    file_level: str | None = None,  # 追加
    ...
) -> None:
    """
    Parameters
    ----------
    file_level : str | None
        ファイル出力のログレベル。Noneの場合はlevelと同じ。
    """
    file_level = file_level or level

    # ファイルハンドラ
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, file_level.upper()))
```

## 受け入れ条件

- [ ] ファイル出力がDEBUGレベルになる
- [ ] コンソール出力はデフォルトINFO（--verbose時はDEBUG）
- [ ] 既存のログ呼び出しが正常に動作する
- [ ] 単体テストが通る

## 依存関係

- 依存先: P10-001
- ブロック: P10-003, P10-005, P10-008, P10-010, P10-014

## 見積もり

- 作業時間: 20分
- 複雑度: 低
