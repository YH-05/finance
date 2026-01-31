# P10-003: item_id空チェック追加

## 概要

`gh project item-add` の戻り値（item_id）が空の場合、フィールド設定をスキップしてエラーを回避する。

## 背景

2026-01-31のログで154件の「Publication failed」が発生。原因は `gh project item-edit --id ''` で空のitem_idが渡されていること。

```
gh project item-edit --id '' --field-id PVTSSF_...
→ non-zero exit status 1
```

## 変更内容

### 変更ファイル

| ファイル | 変更内容 |
|----------|----------|
| `src/news/publisher.py` | item_id空チェックとログ出力 |

### 実装詳細

```python
# src/news/publisher.py

async def _add_issue_to_project(
    self,
    issue_number: int,
    article: SummarizedArticle,
) -> None:
    """Issue を Project に追加し、フィールドを設定。"""
    # 1. Issue を Project に追加
    issue_url = f"https://github.com/{self._repo}/issues/{issue_number}"
    owner = self._repo.split("/")[0]

    add_result = subprocess.run(
        [
            "gh", "project", "item-add",
            str(self._project_number),
            "--owner", owner,
            "--url", issue_url,
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    item_id = add_result.stdout.strip()

    # item_id が空の場合はフィールド設定をスキップ
    if not item_id:
        logger.warning(
            "Empty item_id from project item-add, skipping field updates",
            issue_number=issue_number,
            issue_url=issue_url,
            stderr=add_result.stderr,
        )
        return

    logger.debug(
        "Added issue to project",
        issue_number=issue_number,
        project_number=self._project_number,
        item_id=item_id,
    )

    # 2. Status フィールドを設定
    # ... 既存コード
```

## 受け入れ条件

- [ ] item_idが空の場合、フィールド設定がスキップされる
- [ ] 警告ログが出力される（issue_number, stderr含む）
- [ ] 例外が発生しない（graceful degradation）
- [ ] 単体テストが通る

## テストケース

```python
def test_empty_item_id_skips_field_update(publisher, mocker):
    """item_idが空の場合、フィールド設定をスキップする。"""
    mocker.patch(
        "subprocess.run",
        return_value=Mock(stdout="", stderr="Already exists", returncode=0),
    )

    # 例外なしで完了
    await publisher._add_issue_to_project(123, article)

    # item-editは呼ばれない
    assert subprocess.run.call_count == 1  # item-addのみ
```

## 依存関係

- 依存先: P10-002
- ブロック: P10-004

## 見積もり

- 作業時間: 15分
- 複雑度: 低
