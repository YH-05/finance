# Implementation Plan: NotebookLM MCP Server Improvements

## Context

PRレビュー（`docs/pr-review/pr-review-20260217.yaml`）で特定された改善点を実装します。現在のコードベースは高品質（総合79点）ですが、以下の3つの領域で改善の余地があります：

### 問題点

1. **DRY違反** (~1,280行の重複コード)
   - ページライフサイクルボイラープレート: 8サービス × 30行 = ~240行
   - MCPツールエラーハンドリング: 27関数 × 30-40行 = ~540-1,080行
   - サービスメソッドエラーハンドリング: 25メソッド × 20行 = ~500行

2. **パフォーマンス** (3-5倍改善可能)
   - BatchService逐次処理: 5ソースで75-150秒 → 並列化で15-30秒へ
   - wait_for_element逐次待機: 最悪30秒 → 並列化で2-5秒へ
   - _wait_for_source_processing固定待機: 3秒 → 動的検出で0.5-5秒へ

3. **セキュリティ** (6件のMEDIUM以上の指摘)
   - HIGH: セッションファイルパーミッション（SEC-006）
   - MEDIUM: テキスト/URL/ファイルパス入力バリデーション不足（SEC-002, 003, 004）
   - MEDIUM: Playwrightバージョン未固定（SEC-005）
   - その他: テスト再現性、型ヒント

### 改善の目標

- **保守性**: 1,280行削減、DRYの徹底
- **パフォーマンス**: バッチ処理3-5倍高速化
- **セキュリティ**: 全MEDIUM以上の指摘を解決
- **API互換性**: 既存のpublicメソッドは変更しない

---

## Implementation Plan

### Phase 1: Foundation - Reusable Infrastructure

**Goal**: エラーハンドリングとページ管理の共通基盤を作成

#### 1.1 Create Decorator Module

**New File**: `src/notebooklm/decorators.py` (~150 lines)

実装内容:
- `@handle_browser_operation(error_class)`: サービスメソッド用デコレータ
  - ValueError/NotebookLMErrorはpass-through
  - 汎用Exceptionを指定のerror_classでラップ
  - ロギング自動化（開始、完了、エラー）
  - contextの自動抽出（notebook_id等）

- `@mcp_tool_handler(tool_name)`: MCPツール用デコレータ
  - ctx.report_progress() の自動呼び出し（0%, 100%）
  - ValueError/NotebookLMError/Exceptionの標準的なハンドリング
  - エラー辞書の一貫したフォーマット
  - 詳細ロギング

**Key Implementation Pattern**:
```python
def handle_browser_operation(
    error_class: type[NotebookLMError] = NotebookLMError,
):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except (ValueError, NotebookLMError):
                raise  # Pass through validation and already-wrapped errors
            except Exception as e:
                # Extract context and wrap in error_class
                context = {"operation": func.__name__, "error": str(e), ...}
                logger.error(f"{func.__name__} failed", **context)
                raise error_class(f"Failed: {e}", context=context) from e
        return wrapper
    return decorator
```

#### 1.2 Add Page Context Manager

**Modify**: `src/notebooklm/browser/manager.py` (+15 lines)

```python
@asynccontextmanager
async def managed_page(self) -> AsyncIterator[Any]:
    """Context manager for automatic page lifecycle.

    Creates page → yields → ensures close in finally.
    """
    page = await self.new_page()
    try:
        yield page
    finally:
        await page.close()
```

#### 1.3 Tests for Phase 1

**New File**: `tests/notebooklm/unit/test_decorators.py` (~100 lines)

- `test_handle_browser_operation_passes_through_ValueError`
- `test_handle_browser_operation_wraps_generic_Exception`
- `test_mcp_tool_handler_reports_progress`
- `test_mcp_tool_handler_handles_NotebookLMError`

**Files Changed**:
- `src/notebooklm/decorators.py` (NEW): +150
- `src/notebooklm/browser/manager.py` (MODIFY): +15
- `tests/notebooklm/unit/test_decorators.py` (NEW): +100

**Checkpoint**: 全テスト成功、デコレータが正しく動作することを確認

---

### Phase 2: DRY Refactoring - Apply Decorators

**Goal**: 既存コードにデコレータとコンテキストマネージャを適用（-1,528行）

#### 2.1 Refactor Service Methods (8 files)

**Pattern Transformation**:

Before (30 lines):
```python
async def add_text_source(self, notebook_id: str, text: str) -> SourceInfo:
    if not notebook_id.strip():
        raise ValueError("notebook_id must not be empty")

    page = await self._browser_manager.new_page()
    try:
        await navigate_to_notebook(page, notebook_id)
        # ... 操作 ...
        return SourceInfo(...)
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        raise SourceAddError(f"Failed: {e}", context={...}) from e
    finally:
        await page.close()
```

After (8 lines):
```python
@handle_browser_operation(error_class=SourceAddError)
async def add_text_source(self, notebook_id: str, text: str) -> SourceInfo:
    if not notebook_id.strip():
        raise ValueError("notebook_id must not be empty")

    async with self._browser_manager.managed_page() as page:
        await navigate_to_notebook(page, notebook_id)
        # ... 操作 ...
        return SourceInfo(...)
```

**Files to Modify**:
1. `src/notebooklm/services/audio.py` (1 method): -22 lines
2. `src/notebooklm/services/studio.py` (4 methods): -88 lines
3. `src/notebooklm/services/note.py` (5 methods): -110 lines
4. `src/notebooklm/services/notebook.py` (3 methods): -66 lines
5. `src/notebooklm/services/chat.py` (2 methods): -44 lines
6. `src/notebooklm/services/source.py` (9 methods): -198 lines
7. `src/notebooklm/services/batch.py` (次のPhaseで並列化と同時に実施)

Total: -528 lines

各ファイルに `from notebooklm.decorators import handle_browser_operation` を追加。

#### 2.2 Refactor MCP Tools (7 files)

**Pattern Transformation**:

Before (50 lines):
```python
async def notebooklm_generate_audio_overview(
    notebook_id: str,
    ctx: Context,
    customize_prompt: str | None = None,
) -> dict[str, Any]:
    logger.info("MCP tool called: notebooklm_generate_audio_overview", ...)
    try:
        await ctx.report_progress(0.0, 1.0)
        browser_manager = ctx.lifespan_context["browser_manager"]
        service = AudioService(browser_manager)
        result = await service.generate_audio_overview(...)
        await ctx.report_progress(1.0, 1.0)
        return result.model_dump()
    except ValueError as e:
        logger.error(...); return {"error": str(e), ...}
    except NotebookLMError as e:
        logger.error(...); return {"error": str(e), ...}
```

After (10 lines):
```python
@mcp_tool_handler("notebooklm_generate_audio_overview")
async def notebooklm_generate_audio_overview(
    notebook_id: str,
    ctx: Context,
    customize_prompt: str | None = None,
) -> dict[str, Any]:
    browser_manager = ctx.lifespan_context["browser_manager"]
    service = AudioService(browser_manager)
    result = await service.generate_audio_overview(notebook_id, customize_prompt)
    return result.model_dump()
```

**Files to Modify**:
1. `src/notebooklm/mcp/tools/audio_tools.py` (1 function): -40 lines
2. `src/notebooklm/mcp/tools/batch_tools.py` (3 functions): -120 lines
3. `src/notebooklm/mcp/tools/chat_tools.py` (2 functions): -80 lines
4. `src/notebooklm/mcp/tools/note_tools.py` (5 functions): -200 lines
5. `src/notebooklm/mcp/tools/notebook_tools.py` (3 functions): -120 lines
6. `src/notebooklm/mcp/tools/source_tools.py` (9 functions): -360 lines
7. `src/notebooklm/mcp/tools/studio_tools.py` (4 functions): -160 lines

Total: -1,080 lines

各ファイルに `from notebooklm.decorators import mcp_tool_handler` を追加。

#### 2.3 Tests for Phase 2

**No new tests needed** - 既存のサービステストとMCPツールテストがすべて成功すればOK。

デコレータはロギングとエラーラッピングのみ追加するため、既存のテストは変更なしで動作するはず。

**Files Changed** (Phase 2 Total):
- 8 service files (MODIFY): -528 lines, +24 lines (imports)
- 7 MCP tool files (MODIFY): -1,080 lines, +56 lines (imports)

**Net**: -1,528 lines

**Checkpoint**: 全既存テスト成功、コードカバレッジ維持（80%以上）

---

### Phase 3: Performance Optimization

**Goal**: バッチ処理並列化とセレクタ待機の高速化（3-5倍改善）

#### 3.1 Parallelize BatchService

**Modify**: `src/notebooklm/services/batch.py` (~80 lines changed)

**変更内容**:

1. **Semaphoreの追加**（並行数制御）:
```python
class BatchService:
    def __init__(
        self,
        source_service: SourceService,
        chat_service: ChatService,
        studio_service: StudioService | None = None,
        max_concurrent: int = 5,  # NEW
    ) -> None:
        self._semaphore = asyncio.Semaphore(max_concurrent)
```

2. **batch_add_sources の並列化**:
```python
async def batch_add_sources(self, notebook_id: str, sources: list[dict]) -> BatchResult:
    async def add_single_source(idx: int, source_def: dict) -> dict:
        async with self._semaphore:
            # 各ソースを追加（並列実行）
            if source_type == "text":
                return await self._source_service.add_text_source(...)
            # ...

    results = await asyncio.gather(
        *[add_single_source(idx, src) for idx, src in enumerate(sources)],
        return_exceptions=False,
    )
    # 成功/失敗をカウント
```

3. **batch_chat の並列化**（同様のパターン）

**Performance Impact**:
- `batch_add_sources` (5 sources): 75-150s → 15-30s (5x)
- `batch_chat` (10 questions): 600s → 250-350s (1.7x)

#### 3.2 Parallelize wait_for_element

**Modify**: `src/notebooklm/browser/helpers.py` (~30 lines changed)

**変更内容**:

```python
async def wait_for_element(
    page: Any,
    selectors: list[str],
    *,
    timeout_ms: int = DEFAULT_ELEMENT_TIMEOUT_MS,
) -> Any:
    """Wait for element using parallel selector matching."""

    async def try_selector(selector: str) -> tuple[str, Any | None]:
        try:
            element = page.locator(selector)
            await element.wait_for(state="visible", timeout=timeout_ms)
            return (selector, element)
        except Exception:
            return (selector, None)

    # 全セレクタを並列で試行
    results = await asyncio.gather(
        *[try_selector(sel) for sel in selectors],
        return_exceptions=True,
    )

    # 最初の成功を返す
    for selector, element in results:
        if element is not None:
            return element

    raise ElementNotFoundError(...)
```

**Performance Impact**:
- 3 selectors, worst case: 30s → 2-5s (5-15x)

#### 3.3 Improve _wait_for_source_processing

**Modify**: `src/notebooklm/services/source.py` (~30 lines changed)

**変更内容**:

```python
async def _wait_for_source_processing(self, page: Any) -> None:
    """Wait for source processing via UI state polling."""
    from notebooklm.browser.helpers import poll_until

    async def is_processing_complete() -> bool:
        # プログレスバーセレクタをチェック
        for selector in ['div[role="progressbar"]', '.progress-indicator']:
            element = page.locator(selector)
            if await element.count() > 0:
                return False  # Still processing
        return True  # Complete

    await poll_until(
        check_fn=is_processing_complete,
        timeout_seconds=30.0,
        interval_seconds=0.5,
        operation_name="source_processing",
    )
```

**Performance Impact**:
- Fixed 3s → 0.5-5s dynamic (typically faster, more reliable)

#### 3.4 Tests for Phase 3

**New**: `tests/notebooklm/unit/test_batch_performance.py`
- `test_batch_add_sources_並列実行を確認`（asyncio.gatherのモック）
- `test_wait_for_element_並列実行で高速化`

**Integration**: 実際のパフォーマンス測定
- `test_batch_add_sources_completes_within_30s`
- `test_batch_chat_completes_within_350s`

**Files Changed**:
- `src/notebooklm/services/batch.py` (MODIFY): ~80 lines
- `src/notebooklm/browser/helpers.py` (MODIFY): ~30 lines
- `src/notebooklm/services/source.py` (MODIFY): ~30 lines
- `tests/notebooklm/unit/test_batch_performance.py` (NEW): +50 lines

**Checkpoint**: パフォーマンステスト成功、3-5倍の改善を確認

---

### Phase 4: Security Hardening

**Goal**: 全MEDIUM以上のセキュリティ指摘を解決

#### 4.1 Session File Permissions (SEC-006 HIGH)

**Modify**: `src/notebooklm/browser/manager.py` (+10 lines)

```python
async def save_session(self, path: str | None = None) -> None:
    """Save session with secure permissions (0600)."""
    session_path = path or self.session_file
    await self._browser_context.storage_state(path=session_path)

    # SEC-006: Restrict to owner-only read/write
    import os
    import stat
    os.chmod(session_path, stat.S_IRUSR | stat.S_IWUSR)  # 0600

    logger.info("Session saved", session_file=session_path, permissions="0600")
```

**Test**:
```python
def test_save_session_creates_file_with_0600_permissions():
    # session保存後、パーミッションが0600であることを確認
```

#### 4.2 Input Validation Layer (SEC-002, 003, 004 MEDIUM)

**New File**: `src/notebooklm/validation.py` (~200 lines)

実装内容:
- `validate_text_input(text, max_length=1_000_000)`: XSS対策
  - スクリプトタグ検出（正規表現）
  - 長さ制限（メモリ枯渇防止）
  - NUL文字チェック

- `validate_url_input(url, allowed_schemes=["http", "https"])`: SSRF対策
  - スキーム検証（file://, javascript://等を拒否）
  - プライベートIP検出（127.0.0.1, 10.x.x.x, 192.168.x.x等）
  - URL長制限（2048文字）

- `validate_file_path(file_path, allowed_directories=None)`: パストラバーサル対策
  - Path.resolve()でシンボリックリンク解決
  - allowed_directoriesとの相対パスチェック
  - ファイル存在確認
  - シンボリックリンク検出・拒否（オプション）

**Apply Validation**: `src/notebooklm/services/source.py` (+15 lines)

```python
from notebooklm.validation import validate_text_input, validate_url_input, validate_file_path

@handle_browser_operation(error_class=SourceAddError)
async def add_text_source(self, notebook_id: str, text: str, ...) -> SourceInfo:
    validate_text_input(text)  # SEC-002
    async with self._browser_manager.managed_page() as page:
        # ... 既存ロジック ...

@handle_browser_operation(error_class=SourceAddError)
async def add_url_source(self, notebook_id: str, url: str) -> SourceInfo:
    validate_url_input(url)  # SEC-003
    # ...

@handle_browser_operation(error_class=SourceAddError)
async def add_file_source(self, notebook_id: str, file_path: str) -> SourceInfo:
    validated_path = validate_file_path(file_path)  # SEC-004
    # ...
```

**Tests**: `tests/notebooklm/unit/test_validation.py` (~100 lines)
- `test_validate_text_input_異常系_スクリプトタグでValueError`
- `test_validate_url_input_異常系_プライベートIPでValueError`
- `test_validate_file_path_異常系_パストラバーサルでValueError`

#### 4.3 Fix Playwright Version Range (SEC-005 MEDIUM)

**Modify**: `pyproject.toml` (1 line)

Before: `playwright>=1.49.0`
After: `playwright>=1.49.0,<2.0.0`

#### 4.4 Fix conftest.py datetime (TEST-001 HIGH)

**Modify**: `tests/conftest.py` (+10 lines)

```python
import pytest
from datetime import datetime, timezone

@pytest.fixture
def fixed_datetime():
    """Fixed datetime for reproducible tests."""
    return datetime(2026, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
```

テストで `datetime.now()` を使用している箇所を `fixed_datetime` フィクスチャに置き換え。

#### 4.5 Files Changed (Phase 4 Total)

- `src/notebooklm/validation.py` (NEW): +200
- `src/notebooklm/browser/manager.py` (MODIFY): +10
- `src/notebooklm/services/source.py` (MODIFY): +15
- `pyproject.toml` (MODIFY): 1 line
- `tests/conftest.py` (MODIFY): +10
- `tests/notebooklm/unit/test_validation.py` (NEW): +100

**Checkpoint**: 全セキュリティテスト成功、Banditスキャンクリーン

---

## Critical Files to Modify

### New Files (3)
1. `src/notebooklm/decorators.py` (+150 lines)
   - DRY改善の中核となるデコレータ

2. `src/notebooklm/validation.py` (+200 lines)
   - セキュリティ強化の入力バリデーション層

3. `tests/notebooklm/unit/test_decorators.py` (+100 lines)
   - デコレータの単体テスト

### High-Priority Modifications (5)
1. `src/notebooklm/browser/manager.py` (+25 lines total)
   - managed_page() コンテキストマネージャ (Phase 1)
   - save_session() chmod (Phase 4)

2. `src/notebooklm/services/batch.py` (~80 lines changed)
   - 並列化（5x speedup）

3. `src/notebooklm/browser/helpers.py` (~30 lines changed)
   - セレクタ並列待機（5-15x speedup）

4. `src/notebooklm/services/source.py` (~45 lines changed)
   - _wait_for_source_processing改善 (Phase 3)
   - 入力バリデーション適用 (Phase 4)

5. `pyproject.toml` (1 line)
   - Playwrightバージョン固定

### Service Files (6) - Phase 2 Refactoring
Apply `@handle_browser_operation` and `managed_page()`:
1. `src/notebooklm/services/audio.py` (-22 lines)
2. `src/notebooklm/services/studio.py` (-88 lines)
3. `src/notebooklm/services/note.py` (-110 lines)
4. `src/notebooklm/services/notebook.py` (-66 lines)
5. `src/notebooklm/services/chat.py` (-44 lines)
6. (batch.py は Phase 3 で並列化と同時に実施)

### MCP Tool Files (7) - Phase 2 Refactoring
Apply `@mcp_tool_handler`:
1. `src/notebooklm/mcp/tools/audio_tools.py` (-40 lines)
2. `src/notebooklm/mcp/tools/batch_tools.py` (-120 lines)
3. `src/notebooklm/mcp/tools/chat_tools.py` (-80 lines)
4. `src/notebooklm/mcp/tools/note_tools.py` (-200 lines)
5. `src/notebooklm/mcp/tools/notebook_tools.py` (-120 lines)
6. `src/notebooklm/mcp/tools/source_tools.py` (-360 lines)
7. `src/notebooklm/mcp/tools/studio_tools.py` (-160 lines)

---

## Verification Strategy

### Phase 1 Verification (Foundation)
```bash
# 1. デコレータテスト成功
uv run pytest tests/notebooklm/unit/test_decorators.py -v

# 2. managed_page() 動作確認
uv run pytest tests/notebooklm/integration/ -k "page" -v
```

### Phase 2 Verification (DRY Refactoring)
```bash
# 1. 全既存テスト成功
uv run pytest tests/notebooklm/ -v

# 2. カバレッジ維持（80%以上）
uv run pytest tests/notebooklm/ --cov=src/notebooklm --cov-report=term-missing

# 3. コード行数確認
find src/notebooklm/services -name "*.py" | xargs wc -l
find src/notebooklm/mcp/tools -name "*.py" | xargs wc -l
# → ~1,280行削減を確認
```

### Phase 3 Verification (Performance)
```bash
# 1. パフォーマンステスト成功
uv run pytest tests/notebooklm/unit/test_batch_performance.py -v

# 2. 実際のパフォーマンス測定（統合テスト）
uv run pytest tests/notebooklm/integration/ -k "batch" -v --durations=10

# 3. 並列実行確認（モック検証）
# asyncio.gather が呼ばれることを確認
```

**Expected Results**:
- `batch_add_sources` (5 sources): < 30s
- `batch_chat` (10 questions): < 350s
- `wait_for_element` (3 selectors): < 5s

### Phase 4 Verification (Security)
```bash
# 1. セキュリティテスト成功
uv run pytest tests/notebooklm/unit/test_validation.py -v

# 2. セッションファイルパーミッション確認
ls -la .notebooklm-session.json
# → -rw------- (0600) を確認

# 3. Banditスキャン
bandit -r src/notebooklm -ll
# → 0 high/medium issues を確認

# 4. 全テストスイート成功
uv run pytest tests/notebooklm/ -v
```

### Final Integration Test
```bash
# 全品質チェック成功
make check-all

# エンドツーエンド動作確認
# 1. セッション作成・保存
# 2. バッチソース追加（5個）
# 3. バッチチャット（10個）
# 4. Studio生成
# → すべて正常動作し、パフォーマンス改善を確認
```

---

## Expected Outcomes

### Code Quality Metrics
| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Total Lines | ~22,545 | ~21,558 | -987 lines (-4.4%) |
| Duplicated Code | ~1,280 lines | 0 | -1,280 lines |
| Test Coverage | 80% | 80%+ | Maintained |

### Performance Metrics
| Operation | Before | After | Improvement |
|-----------|--------|-------|-------------|
| batch_add_sources (5) | 75-150s | 15-30s | 5x faster |
| batch_chat (10) | 600s | 250-350s | 1.7x faster |
| wait_for_element (3) | 30s (worst) | 2-5s | 5-15x faster |

### Security Metrics
| Finding | Severity | Status |
|---------|----------|--------|
| SEC-001 (diskcache) | HIGH | Documented (out of scope) |
| SEC-002 (text XSS) | MEDIUM | ✅ Fixed |
| SEC-003 (URL SSRF) | MEDIUM | ✅ Fixed |
| SEC-004 (path traversal) | MEDIUM | ✅ Fixed |
| SEC-005 (playwright version) | MEDIUM | ✅ Fixed |
| SEC-006 (session chmod) | MEDIUM | ✅ Fixed |
| TEST-001 (datetime) | HIGH | ✅ Fixed |

---

## Risk Mitigation

### Risk 1: NotebookLM API Rate Limiting
**Mitigation**: Semaphore (max_concurrent=5) で並行数制御。レート制限エラー検出時は exponential backoff を実装。

### Risk 2: Session chmod on Windows
**Mitigation**: プラットフォーム検出。Windows では警告ログのみ。macOS/Linux では 0600 を強制。

### Risk 3: Validation Blocks Legitimate Inputs
**Mitigation**: 保守的なバリデーションルール（1MB制限、プライベートIP拒否等）。ログで拒否理由を明確化。

### Risk 4: Parallel Selectors Increase CPU
**Mitigation**: 2-5個のセレクタに限定（典型的なユースケース）。5-15倍の速度向上のため許容可能なトレードオフ。

---

## Implementation Sequence

### Week 1: Foundation & DRY
- **Day 1-2**: Phase 1 (デコレータ、コンテキストマネージャ、テスト)
- **Day 3-5**: Phase 2 (サービス・MCPツールのリファクタリング)
- **Checkpoint**: 全テスト成功、~1,280行削減

### Week 2: Performance & Security
- **Day 6-7**: Phase 3 (並列化、パフォーマンス改善)
- **Day 8-9**: Phase 4 (セキュリティ強化)
- **Day 10**: 統合テスト、ドキュメント更新
- **Final Checkpoint**: 全改善完了、品質・パフォーマンス・セキュリティ目標達成

---

## API Compatibility

**No Breaking Changes**:
- 全サービスクラスのpublicメソッドシグネチャは不変
- MCPツールの外部インターフェースは不変
- 戻り値の型は変更なし

**Internal Changes Only**:
- デコレータは透過的（既存の動作にロギングとエラーラッピングを追加）
- コンテキストマネージャは内部実装の置き換え
- バリデーションは新規追加（既存の動作を強化）

既存のMCPクライアントやPythonコードは**変更なし**で動作します。
