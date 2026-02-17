# `configuration/` を `utils_core/` に統合するリファクタリング計画

## 概要

`src/configuration/file_path.py` の環境変数管理機能を `src/utils_core/` に統合し、プロジェクト全体の設定管理を一元化します。

### 現状の問題点

1. **レガシーコードの残存**: `configuration/` ディレクトリ（3ファイル）はほぼ使用されていない
2. **重複実装**: ロギング機能が3箇所に重複
   - `configuration/log.py` (レガシー、debugpy/pandas 依存)
   - `news/utils/logging_config.py` (ローカル実装)
   - `utils_core/logging/config.py` (新しい実装、全体で使用中)
3. **未使用の環境変数**: 30個以上の環境変数定義があるが、実際に使用されているのは5個のみ
4. **直接的な環境変数アクセス**: `os.environ.get()` の直接呼び出しが散在

### 実際に使用されている環境変数

| 変数名 | 使用箇所 | 必須 |
|--------|---------|------|
| `FRED_API_KEY` | `market/fred/fetcher.py:100` | ✅ |
| `LOG_LEVEL` | `utils_core/logging/config.py:270` | ❌ (デフォルト: INFO) |
| `LOG_FORMAT` | `utils_core/logging/config.py:282` | ❌ (デフォルト: console) |
| `LOG_DIR` | `utils_core/logging/config.py:286` | ❌ |
| `PROJECT_ENV` | `utils_core/logging/config.py:325` | ❌ (デフォルト: development) |

## リファクタリング戦略

### アーキテクチャ選択: Option B

**`utils_core/settings.py` として新規モジュール作成**

**理由**:
- ロギング設定と環境変数管理は責務が異なる（単一責任原則）
- 将来的な拡張（pydantic-settings 導入など）が容易
- インポートパスが明確（`from utils_core.settings import get_setting`）

### 新規モジュール構成

```
src/utils_core/
├── __init__.py
├── types.py                    # 既存（LogLevel, LogFormat）
├── settings.py                 # 新規作成（環境変数管理）
└── logging/
    ├── __init__.py
    └── config.py               # 既存（structlog設定）→ 修正
```

## 段階的実装計画（6 Phase）

### Phase 1: 新規モジュール作成（影響: なし）

**作業内容**:
1. `src/utils_core/settings.py` を作成
   - 実際に使用されている5つの環境変数のみを実装
   - 遅延読み込み（lazy loading）を実装
   - 型安全なアクセス関数を提供

2. テストを作成
   - `tests/utils_core/unit/test_settings.py`
   - 環境変数の取得、デフォルト値、型変換、エラーケースをカバー

**成果物**:
- `src/utils_core/settings.py`
- `tests/utils_core/unit/test_settings.py`

**検証基準**:
- `make test-unit` が成功
- `make typecheck` が成功

### Phase 2: `utils_core/logging/config.py` のリファクタリング（影響: 小）

**作業内容**:
1. `utils_core/logging/config.py` を修正
   - `os.environ.get()` の直接呼び出しを削除
   - `settings.py` の関数を使用するように変更
   - 変更箇所: 270行目、282行目、286行目、287行目、325行目

2. 既存のロギングテストを実行して動作確認

**変更ファイル**:
- `src/utils_core/logging/config.py`

**検証基準**:
- 既存のロギングテストが全て成功
- `make check-all` が成功

### Phase 3: レガシーコードの非推奨化（影響: なし）

**作業内容**:
1. `configuration/__init__.py` を修正
   - import 時に Deprecation 警告を表示
   - 将来のバージョンで削除予定であることを明示

**変更ファイル**:
- `src/configuration/__init__.py`

**検証基準**:
- `configuration` をインポートすると警告が表示される
- 既存の動作は変わらない

### Phase 4: `configuration/log.py` の削除（影響: なし）

**作業内容**:
1. `configuration/log.py` を削除
   - 使用箇所は `configuration/log.py` 自身からのみなので安全に削除可能

**変更ファイル**:
- `src/configuration/log.py` (削除)

**検証基準**:
- `make check-all` が成功
- grep で `from configuration.log` が見つからない

### Phase 5: `news/utils/logging_config.py` の統合（影響: 中）

**作業内容**:
1. `news/utils/logging_config.py` と `utils_core/logging/config.py` を比較
2. 機能差分を分析
3. 必要に応じて `utils_core/logging/config.py` に機能をマージ
4. `news/utils/logging_config.py` を削除
5. `news/` パッケージ内のインポート文を更新

**変更ファイル**:
- `src/news/utils/logging_config.py` (削除)
- `src/news/` 配下のインポート文

**検証基準**:
- `news` パッケージのテストが全て成功
- `make check-all` が成功

### Phase 6: `configuration/` ディレクトリの完全削除（影響: なし）

**作業内容**:
1. `configuration/file_path.py` の削除
2. `configuration/__init__.py` の削除
3. `configuration/` ディレクトリの削除

**変更ファイル**:
- `src/configuration/` (ディレクトリごと削除)

**検証基準**:
- `make check-all` が成功
- grep で `from configuration` が見つからない

## 実装の優先順位

### 必須（Must）: Phase 1, 2
- 設定管理の一元化（最重要）
- 推定時間: 1.5時間

### 推奨（Should）: Phase 4, 5
- レガシーコードの削除（品質向上）
- 推定時間: 1.5時間

### オプション（Could）: Phase 3, 6
- Deprecation 警告、完全削除（将来的な整理）
- 推定時間: 30分

**総推定時間**: 約3.5時間

## Critical Files（重要ファイル）

### Phase 1, 2 で作成・修正するファイル

1. **`src/utils_core/settings.py`** [作成]
   - 環境変数管理の中核モジュール
   - 型安全なアクセス関数を提供

2. **`src/utils_core/logging/config.py`** [修正]
   - 270行目: `LOG_LEVEL` の取得
   - 282行目: `LOG_FORMAT` の取得
   - 286行目: `LOG_DIR` の取得
   - 287行目: `LOG_FILE_ENABLED` の取得
   - 325行目: `PROJECT_ENV` の取得

3. **`tests/utils_core/unit/test_settings.py`** [作成]
   - settings.py の包括的テスト

### Phase 4, 5 で削除するファイル

4. **`src/configuration/log.py`** [削除]
   - レガシーロギング実装

5. **`src/news/utils/logging_config.py`** [削除]
   - 重複実装の統合

### Phase 6 で削除するファイル

6. **`src/configuration/file_path.py`** [削除]
7. **`src/configuration/__init__.py`** [削除]

## リスク評価

| リスク | 影響度 | 確率 | 対策 |
|-------|--------|------|------|
| 既存コードの破壊 | 低 | 低 | 段階的移行、各Phase後にテスト実行 |
| 環境変数の読み込みタイミング変更 | 低 | 中 | 遅延読み込み（lazy loading）を実装 |
| テストの失敗 | 中 | 低 | Phase 1 で包括的なテスト作成 |
| `news/utils/logging_config.py` の統合時の機能差分 | 中 | 中 | 詳細な比較分析を実施 |

## 検証方法

### 各 Phase 終了後の検証

```bash
# 品質チェック
make check-all

# 単体テストのみ
make test-unit

# 型チェックのみ
make typecheck
```

### 最終検証（Phase 6 完了後）

```bash
# 全テスト実行
make test

# configuration パッケージの使用箇所がないことを確認
grep -r "from configuration" src/
grep -r "import configuration" src/

# 期待される結果: マッチなし
```

## 後方互換性

- **Phase 3**: Deprecation 警告を追加（v0.2.0）
- **Phase 6**: 完全削除（v1.0.0）

移行期間を設けることで、既存コードへの影響を最小化します。

## 将来的な拡張計画

### Pydantic Settings への移行（Optional）

将来的に設定管理をより堅牢にする場合、pydantic-settings への移行を検討できます。現在の `settings.py` の設計は、この移行を容易にするように設計されています。

### 設定のバリデーション強化

環境変数の値に対するより詳細なバリデーションを追加できます（例: ログレベルの有効性チェック）。

## まとめ

このリファクタリングにより：

1. **設定管理が一元化**され、`utils_core/settings.py` が唯一の環境変数アクセスポイントとなります
2. **レガシーコードが削除**され、コードベースが整理されます
3. **重複実装が解消**され、保守性が向上します
4. **型安全性が向上**し、環境変数の誤用を防げます

実装は **Phase 1 → Phase 2** を最優先とし、新しいアーキテクチャを確立してから、レガシーコードの削除を進めることを推奨します。
