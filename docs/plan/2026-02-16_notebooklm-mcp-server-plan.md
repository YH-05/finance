# NotebookLM MCP サーバー 実装計画

## Context（背景）

Google NotebookLM を Claude Code から操作可能にする MCP (Model Context Protocol) サーバーを開発する。NotebookLM は AI を活用したリサーチ・ライティングツールであり、これを MCP 統合することで、Claude Code から直接ノートブック管理、データソース追加、Audio Overview 生成などが可能になる。

### プロジェクト目標

1. **Claude Code からの NotebookLM 操作を可能にする**
   - ノートブック作成・管理
   - データソース（ドキュメント、URL等）の追加・削除
   - Audio Overview（ポッドキャスト）の生成
   - ノート検索・分析

2. **2つの API アプローチを調査・比較する**
   - 公式 NotebookLM Enterprise API（2025年9月リリース、alpha版）
   - 非公式 notebooklm-py（コミュニティプロジェクト）

3. **実装可能性と制約を明確にする**
   - 各アプローチの技術的詳細
   - リスク・制約の評価
   - 推奨実装方針の決定

---

## 技術調査レポート

### 1. NotebookLM Enterprise API（公式）

#### 概要

- **リリース**: 2025年9月（alpha版）
- **提供元**: Google Cloud
- **位置付け**: Discovery Engine API の一部

#### 料金

| 項目 | 詳細 |
|------|------|
| **Enterprise ライセンス** | $9/ライセンス/月 |
| **年間契約** | 割引あり（詳細は要問合せ） |
| **無料トライアル** | 14日間（5000ライセンス） |
| **API 利用料金** | 公開情報なし（要問合せ） |

**参考**: [NotebookLM Pricing](https://www.elite.cloud/post/notebooklm-pricing-2025-free-plan-vs-paid-plan-which-one-actually-saves-you-time/)

#### 認証方式

| 方式 | 詳細 | 用途 |
|------|------|------|
| **Bearer Token** | `gcloud auth print-access-token` | API 呼び出し |
| **ユーザー認証** | `gcloud auth login` | Google Drive アクセス時 |
| **IAM ロール** | Cloud NotebookLM User | アクセス制御 |
| **Service Account** | 標準 GCP IAM（詳細未公開） | 自動化・本番環境 |

**参考**: [Create and manage notebooks (API)](https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebooks)

#### 機能と制約

| 項目 | 詳細 |
|------|------|
| **ドキュメントサイズ上限** | 200MB または 500,000語 |
| **Enterprise版の上限** | 標準版の5倍（音声、ノート、ソース） |
| **API ステータス** | alpha版（不安定な可能性） |
| **レート制限** | 公開情報なし |

**参考**: [NotebookLM Enterprise Overview](https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/overview)

#### 利用可能な API エンドポイント（alpha版時点）

**Notebook 管理:**
```
POST   /v1/notebooks          - ノートブック作成
GET    /v1/notebooks/{id}     - ノートブック取得
GET    /v1/notebooks          - ノートブック一覧
DELETE /v1/notebooks/{id}     - ノートブック削除
```

**Data Source 管理:**
```
POST   /v1/notebooks/{id}/sources    - ソース追加
GET    /v1/notebooks/{id}/sources    - ソース一覧
DELETE /v1/notebooks/{id}/sources/{sourceId} - ソース削除
```

**Audio Overview:**
```
POST   /v1/notebooks/{id}/audioOverview - Audio Overview 生成
```

**参考**: [Add and manage data sources](https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebooks-sources)

#### メリット

✅ **公式サポート**: Google による正式サポート
✅ **安定性**: API 仕様が安定（変更時は通知あり）
✅ **エンタープライズ機能**: VPC-SC、IAM、監査ログ
✅ **高い上限**: 標準版の5倍のリソース
✅ **TOS 準拠**: 利用規約違反のリスクなし

#### デメリット

❌ **alpha版**: 機能が限定的・不安定な可能性
❌ **コスト**: ライセンス料 + API 利用料（詳細不明）
❌ **GCP 必須**: Google Cloud プロジェクトが必要
❌ **セットアップ**: GCP の初期設定が必要
❌ **ドキュメント不足**: alpha版のため情報が限定的

---

### 2. notebooklm-py（非公式）

#### 概要

- **種類**: 非公式コミュニティプロジェクト
- **GitHub**: [teng-lin/notebooklm-py](https://github.com/teng-lin/notebooklm-py)
- **認証**: ブラウザクッキー（Google アカウント）
- **対象**: 消費者版 NotebookLM

**参考**: [NotebookLM-py: The CLI Tool](https://medium.com/@tentenco/notebooklm-py-the-cli-tool-that-unlocks-google-notebooklm-1de7106fd7ca)

#### 実装方式

```python
# ブラウザクッキーを使用した認証
from notebooklm import NotebookLM

client = NotebookLM()  # ブラウザのクッキーを自動取得
notebooks = client.list_notebooks()
```

#### リスク評価

| リスク | 詳細 | 深刻度 |
|--------|------|--------|
| **API 安定性** | Google が内部 API を変更する可能性（予告なし） | 🔴 高 |
| **TOS 違反** | 自動化アクセスは利用規約で禁止される可能性 | 🔴 高 |
| **アカウント停止** | 自動化ツール使用によるアカウントフラグ | 🟡 中 |
| **メンテナンス依存** | コミュニティプロジェクト、継続性不明 | 🟡 中 |
| **機能制限** | 内部 API の制約により一部機能が未実装 | 🟡 中 |

**参考**: [notebooklm-py Troubleshooting](https://github.com/teng-lin/notebooklm-py/blob/main/docs/troubleshooting.md)

#### メリット

✅ **無料**: ライセンス料不要
✅ **簡単**: GCP セットアップ不要
✅ **即座に利用可能**: 消費者版 NotebookLM で動作
✅ **プロトタイピング**: 迅速な検証が可能

#### デメリット

❌ **TOS 違反リスク**: 利用規約違反の可能性
❌ **不安定**: API 変更で突然動作しなくなる
❌ **非公式**: Google による保証なし
❌ **本番環境不適**: プロダクション利用は推奨されない
❌ **機能制限**: Enterprise 機能（IAM、監査ログ等）なし

---

### 3. 両者の比較分析

| 観点 | NotebookLM Enterprise API | notebooklm-py |
|------|--------------------------|---------------|
| **公式サポート** | ✅ Google 公式 | ❌ コミュニティプロジェクト |
| **安定性** | ✅ 安定（alpha版の制約あり） | ❌ 不安定（API変更で破損） |
| **TOS 準拠** | ✅ 準拠 | ❌ 違反リスク |
| **初期コスト** | ❌ GCP セットアップ必要 | ✅ セットアップ不要 |
| **ランニングコスト** | ❌ $9/月 + API料金 | ✅ 無料 |
| **認証方式** | Bearer Token / Service Account | ブラウザクッキー |
| **対象** | Enterprise 版のみ | 消費者版 |
| **機能** | ✅ フル機能 + Enterprise | ⚠️ 限定的 |
| **プロトタイピング** | ⚠️ セットアップ時間必要 | ✅ 即座に開始可能 |
| **本番環境** | ✅ 推奨 | ❌ 非推奨 |

---

## 推奨実装方針

### 戦略：段階的ハイブリッドアプローチ

両方の API を調査・実装し、段階的に移行する戦略を推奨します。

#### Phase 0: 調査・検証（本プラン）

1. 両方の技術の詳細調査 ✅
2. 実装可能性の評価 ✅
3. リスク分析 ✅
4. 実装計画の策定（本ドキュメント）

#### Phase 1: プロトタイピング（notebooklm-py）

**目的**: 迅速な検証と要件定義

**実装内容:**
- notebooklm-py を使用した MCP サーバーの試作
- 基本的なツール実装（ノートブック CRUD、ソース管理）
- 実際の使用感とワークフローの検証
- 要件の明確化

**期間**: 1-2週間

**成果物:**
- プロトタイプ MCP サーバー（`src/notebooklm_proto/mcp/server.py`）
- 要件定義書（`docs/notebooklm/requirements.md`）
- リスク評価レポート（`docs/notebooklm/risks.md`）

**リスク緩和策:**
- 専用 Google アカウントを作成（メインアカウントを使用しない）
- 内部プロジェクトのみで使用（外部公開しない）
- 明示的に「プロトタイプ」として位置付ける

#### Phase 2: 公式 API 移行準備

**目的**: Enterprise API への移行基盤を整備

**実装内容:**
1. **GCP セットアップ**
   - Google Cloud プロジェクト作成
   - Discovery Engine API 有効化
   - IAM 設定（Service Account 作成）
   - ライセンス取得（14日間トライアルから開始）

2. **認証実装**
   - gcloud CLI 認証（開発環境）
   - Service Account 認証（本番環境）
   - 環境変数での切り替え機能

3. **API クライアント実装**
   - `src/notebooklm/core/client.py`（Enterprise API 用）
   - Pydantic スキーマ定義
   - エラーハンドリング
   - レート制限対応

**期間**: 2-3週間

**成果物:**
- GCP プロジェクト（セットアップ済み）
- 認証モジュール（`src/notebooklm/core/auth.py`）
- API クライアント（`src/notebooklm/core/client.py`）
- セットアップガイド（`docs/notebooklm/setup-gcp.md`）

#### Phase 3: 本番実装（Enterprise API）

**目的**: 本番品質の MCP サーバーを実装

**実装内容:**
1. **MCP サーバー実装**（Phase 1 のツール）
   - ノートブック作成・取得・一覧・削除
   - データソース追加・削除・一覧
   - Audio Overview 生成

2. **MCP サーバー実装**（Phase 2-3 の拡張ツール）
   - ノート検索・フィルタリング
   - コンテンツ抽出・分析
   - バッチ処理機能

3. **品質保証**
   - ユニットテスト（全ツール 100% カバレッジ）
   - 統合テスト（実際の API 呼び出し）
   - エラーハンドリング検証
   - パフォーマンステスト

4. **ドキュメント**
   - README（使用方法）
   - API リファレンス
   - トラブルシューティングガイド

**期間**: 3-4週間

**成果物:**
- 本番 MCP サーバー（`src/notebooklm/mcp/server.py`）
- テストスイート（`tests/notebooklm/`）
- 完全なドキュメント（`src/notebooklm/README.md`）

---

## パッケージ構造設計

### ディレクトリレイアウト

```
src/notebooklm/
├── README.md                  # パッケージドキュメント
├── __init__.py                # 公開API定義
├── py.typed                   # 型チェックマーカー
├── types.py                   # 型定義（全モジュール共通）
├── errors.py                  # 例外クラス定義
├── config.py                  # 設定管理（環境変数連携）
│
├── core/                      # コアロジック
│   ├── __init__.py
│   ├── auth.py                # 認証（gcloud / Service Account）
│   ├── client.py              # NotebookLM API クライアント
│   └── rate_limiter.py        # レート制限管理
│
├── services/                  # サービス層（高レベルAPI）
│   ├── __init__.py
│   ├── notebook_manager.py   # ノートブック管理
│   ├── source_manager.py     # データソース管理
│   └── audio_generator.py    # Audio Overview 生成
│
├── mcp/                       # MCP統合
│   ├── __init__.py
│   └── server.py              # MCP サーバー（7-9ツール実装）
│
├── cache/                     # キャッシング層（オプション）
│   ├── __init__.py
│   └── manager.py             # キャッシュ管理
│
└── utils/
    ├── __init__.py
    ├── logging_config.py      # 構造化ロギング
    └── helpers.py             # ヘルパー関数

tests/notebooklm/
├── unit/                      # ユニットテスト
│   ├── test_auth.py
│   ├── test_client.py
│   ├── test_notebook_manager.py
│   └── mcp/
│       └── test_server.py
├── property/                  # プロパティテスト（オプション）
└── integration/               # 統合テスト
    └── test_api_integration.py

docs/notebooklm/
├── setup-gcp.md               # GCP セットアップガイド
├── requirements.md            # 要件定義書
├── risks.md                   # リスク評価
├── api-reference.md           # API リファレンス
└── troubleshooting.md         # トラブルシューティング

# プロトタイプ用（Phase 1のみ、Phase 2で削除）
src/notebooklm_proto/
├── __init__.py
└── mcp/
    └── server.py              # notebooklm-py ベースの試作
```

### 参照実装パターン

| 実装対象 | 参照元 |
|---------|--------|
| **MCP サーバー構造** | `src/rss/mcp/server.py` |
| **サービス層** | `src/rss/services/feed_manager.py` |
| **API クライアント** | `src/market/industry/api_clients/census.py` |
| **認証実装** | `src_sample/google_drive_utils.py` |
| **設定管理** | `src/edgar/config.py` |
| **エラーハンドリング** | `src/market/errors.py` |
| **ユニットテスト** | `tests/rss/unit/mcp/test_server.py` |

---

## MCP ツール設計

### Phase 1: 基本操作（MVP）

| ツール名 | 説明 | 優先度 |
|---------|------|--------|
| `notebooklm_create_notebook` | ノートブック作成 | 🔴 必須 |
| `notebooklm_get_notebook` | ノートブック取得 | 🔴 必須 |
| `notebooklm_list_notebooks` | ノートブック一覧 | 🔴 必須 |
| `notebooklm_delete_notebook` | ノートブック削除 | 🟡 推奨 |
| `notebooklm_add_source` | データソース追加 | 🔴 必須 |
| `notebooklm_remove_source` | データソース削除 | 🟡 推奨 |
| `notebooklm_list_sources` | データソース一覧 | 🔴 必須 |

**合計**: 7ツール（RSS MCP と同規模）

### Phase 2: Audio Overview 生成

| ツール名 | 説明 | 優先度 |
|---------|------|--------|
| `notebooklm_generate_audio` | Audio Overview 生成 | 🟢 Phase 2 |
| `notebooklm_get_audio_status` | 生成ステータス確認 | 🟢 Phase 2 |

**合計**: +2ツール

### Phase 3: 検索・分析機能

| ツール名 | 説明 | 優先度 |
|---------|------|--------|
| `notebooklm_search_notes` | ノート内検索 | 🔵 Phase 3 |
| `notebooklm_extract_content` | コンテンツ抽出 | 🔵 Phase 3 |
| `notebooklm_analyze_notebook` | ノート分析 | 🔵 Phase 3 |

**合計**: +3ツール
**総計**: 12ツール

---

## 認証実装設計

### 認証方式の選択

**開発環境**: gcloud CLI 認証
**本番環境**: Service Account 認証
**切り替え**: 環境変数 `NOTEBOOKLM_AUTH_MODE`

### 実装例

```python
# src/notebooklm/core/auth.py

from enum import Enum
from pathlib import Path
import os

class AuthMode(str, Enum):
    GCLOUD_CLI = "gcloud_cli"
    SERVICE_ACCOUNT = "service_account"

def get_auth_mode() -> AuthMode:
    """環境変数から認証モードを取得"""
    mode = os.getenv("NOTEBOOKLM_AUTH_MODE", "gcloud_cli")
    return AuthMode(mode)

def get_access_token() -> str:
    """認証モードに応じてアクセストークンを取得"""
    mode = get_auth_mode()

    if mode == AuthMode.GCLOUD_CLI:
        return _get_gcloud_token()
    elif mode == AuthMode.SERVICE_ACCOUNT:
        return _get_service_account_token()
    else:
        raise ValueError(f"Unknown auth mode: {mode}")

def _get_gcloud_token() -> str:
    """gcloud CLI からトークン取得"""
    import subprocess
    result = subprocess.run(
        ["gcloud", "auth", "print-access-token"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()

def _get_service_account_token() -> str:
    """Service Account からトークン取得"""
    from google.auth import default
    from google.auth.transport.requests import Request

    credentials, _ = default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    credentials.refresh(Request())
    return credentials.token
```

### 環境変数設計

```bash
# .env.example に追加

# NotebookLM 認証設定
NOTEBOOKLM_AUTH_MODE=gcloud_cli              # gcloud_cli | service_account
NOTEBOOKLM_PROJECT_ID=your-gcp-project-id    # GCP プロジェクト ID
NOTEBOOKLM_LOCATION=us-central1              # リージョン
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json  # Service Account キー
```

---

## リスク評価と緩和策

### 主要リスク

| リスク | 影響 | 確率 | 緩和策 |
|--------|------|------|--------|
| **alpha API の不安定性** | 🔴 高 | 🟡 中 | 公式ドキュメント監視、バージョン固定 |
| **API 仕様変更** | 🟡 中 | 🟡 中 | 抽象化層、アダプターパターン |
| **レート制限** | 🟡 中 | 🟡 中 | レート制限実装、キャッシング |
| **notebooklm-py の TOS 違反** | 🔴 高 | 🟡 中 | Phase 1 のみ使用、専用アカウント |
| **GCP セットアップの複雑さ** | 🟡 中 | 🟢 低 | セットアップガイド作成 |
| **コスト** | 🟡 中 | 🔴 高 | 14日間トライアル活用、使用量監視 |

### 緩和策の詳細

#### 1. alpha API の不安定性

**対策:**
- Google Cloud リリースノート監視
- エラーハンドリングを厳格に実装
- フォールバック機能（キャッシュ、リトライ）
- テストスイートによる早期検出

#### 2. notebooklm-py の TOS 違反リスク

**対策:**
- **Phase 1 のみ**で使用（プロトタイプ、検証目的）
- 専用 Google アカウント作成（メインアカウント隔離）
- 内部プロジェクトのみ（外部公開しない）
- Phase 2 で Enterprise API に完全移行

#### 3. コスト管理

**対策:**
- 14日間トライアルで検証
- GCP 予算アラート設定
- 使用量ログの監視
- キャッシング戦略（不要な API 呼び出し削減）

---

## 実装ロードマップ

### タイムライン（全体: 6-9週間）

```
Week 1-2:  Phase 1 - プロトタイピング（notebooklm-py）
Week 3-5:  Phase 2 - Enterprise API 移行準備
Week 6-9:  Phase 3 - 本番実装（Enterprise API）
Week 10+:  Phase 4 - 拡張機能（オプション）
```

### Phase 別の詳細タスク

#### Phase 0: 調査・検証 ✅ 完了

- [x] NotebookLM Enterprise API 調査
- [x] notebooklm-py 調査
- [x] 両者の比較分析
- [x] リスク評価
- [x] 実装計画策定（本ドキュメント）

#### Phase 1: プロトタイピング（1-2週間）

**Week 1:**
- [ ] プロトタイプパッケージ作成（`src/notebooklm_proto/`）
- [ ] notebooklm-py のインストール・動作確認
- [ ] 専用 Google アカウント作成
- [ ] 基本的な MCP ツール実装（3-4個）
  - [ ] `notebooklm_create_notebook`
  - [ ] `notebooklm_list_notebooks`
  - [ ] `notebooklm_add_source`

**Week 2:**
- [ ] 残りのツール実装（3-4個）
  - [ ] `notebooklm_get_notebook`
  - [ ] `notebooklm_delete_notebook`
  - [ ] `notebooklm_remove_source`
  - [ ] `notebooklm_list_sources`
- [ ] 実際の使用感検証
- [ ] 要件定義書作成（`docs/notebooklm/requirements.md`）
- [ ] リスク評価レポート作成（`docs/notebooklm/risks.md`）

**成果物:**
- プロトタイプ MCP サーバー
- 要件定義書
- リスク評価レポート

#### Phase 2: Enterprise API 移行準備（2-3週間）

**Week 3:**
- [ ] GCP プロジェクト作成
- [ ] Discovery Engine API 有効化
- [ ] IAM 設定（Service Account 作成）
- [ ] NotebookLM Enterprise ライセンス取得（14日間トライアル）
- [ ] セットアップガイド作成（`docs/notebooklm/setup-gcp.md`）

**Week 4:**
- [ ] 認証モジュール実装（`src/notebooklm/core/auth.py`）
  - [ ] gcloud CLI 認証
  - [ ] Service Account 認証
  - [ ] 環境変数での切り替え
- [ ] 認証ユニットテスト作成

**Week 5:**
- [ ] API クライアント実装（`src/notebooklm/core/client.py`）
  - [ ] REST API 基盤（httpx）
  - [ ] Pydantic スキーマ定義（`src/notebooklm/types.py`）
  - [ ] エラーハンドリング（`src/notebooklm/errors.py`）
  - [ ] レート制限対応（`src/notebooklm/core/rate_limiter.py`）
- [ ] API クライアントユニットテスト作成

**成果物:**
- GCP プロジェクト（セットアップ済み）
- 認証モジュール
- API クライアント
- セットアップガイド

#### Phase 3: 本番実装（3-4週間）

**Week 6:**
- [ ] サービス層実装
  - [ ] `src/notebooklm/services/notebook_manager.py`
  - [ ] `src/notebooklm/services/source_manager.py`
- [ ] サービス層ユニットテスト作成

**Week 7:**
- [ ] MCP サーバー実装（Phase 1 ツール）
  - [ ] `src/notebooklm/mcp/server.py`
  - [ ] 7ツールの実装
- [ ] MCP サーバーユニットテスト作成

**Week 8:**
- [ ] MCP サーバー実装（Phase 2 ツール）
  - [ ] Audio Overview 生成ツール（2個）
- [ ] 統合テスト作成（`tests/notebooklm/integration/`）
- [ ] エラーハンドリング検証

**Week 9:**
- [ ] ドキュメント作成
  - [ ] パッケージ README（`src/notebooklm/README.md`）
  - [ ] API リファレンス（`docs/notebooklm/api-reference.md`）
  - [ ] トラブルシューティングガイド（`docs/notebooklm/troubleshooting.md`）
- [ ] `.mcp.json.template` 更新
- [ ] `pyproject.toml` 更新（エントリーポイント追加）
- [ ] プロトタイプパッケージ削除（`src/notebooklm_proto/`）

**成果物:**
- 本番 MCP サーバー
- テストスイート（100% カバレッジ）
- 完全なドキュメント

#### Phase 4: 拡張機能（オプション）

**Week 10+:**
- [ ] Phase 3 ツール実装（検索・分析、3個）
- [ ] キャッシング機能実装（`src/notebooklm/cache/`）
- [ ] パフォーマンス最適化
- [ ] 追加ドキュメント

**成果物:**
- 拡張機能
- パフォーマンスレポート

---

## 重要なファイルパス

### 実装ファイル（優先度順）

#### 🔴 Phase 1（プロトタイプ）

1. `src/notebooklm_proto/mcp/server.py` - プロトタイプ MCP サーバー
2. `docs/notebooklm/requirements.md` - 要件定義書
3. `docs/notebooklm/risks.md` - リスク評価レポート

#### 🔴 Phase 2（認証・API クライアント）

4. `src/notebooklm/core/auth.py` - 認証モジュール
5. `src/notebooklm/core/client.py` - API クライアント
6. `src/notebooklm/types.py` - 型定義（Pydantic）
7. `src/notebooklm/errors.py` - 例外クラス
8. `src/notebooklm/core/rate_limiter.py` - レート制限
9. `docs/notebooklm/setup-gcp.md` - GCP セットアップガイド
10. `tests/notebooklm/unit/test_auth.py` - 認証テスト
11. `tests/notebooklm/unit/test_client.py` - API クライアントテスト

#### 🔴 Phase 3（本番 MCP サーバー）

12. `src/notebooklm/services/notebook_manager.py` - ノートブック管理サービス
13. `src/notebooklm/services/source_manager.py` - ソース管理サービス
14. `src/notebooklm/services/audio_generator.py` - Audio 生成サービス
15. `src/notebooklm/mcp/server.py` - 本番 MCP サーバー
16. `tests/notebooklm/unit/mcp/test_server.py` - MCP サーバーテスト
17. `tests/notebooklm/integration/test_api_integration.py` - 統合テスト
18. `src/notebooklm/README.md` - パッケージドキュメント
19. `docs/notebooklm/api-reference.md` - API リファレンス
20. `docs/notebooklm/troubleshooting.md` - トラブルシューティング

#### 🟡 設定ファイル

21. `pyproject.toml` - パッケージ設定（依存関係、エントリーポイント）
22. `.mcp.json.template` - MCP サーバー設定
23. `.env.example` - 環境変数テンプレート

### 参照ファイル（実装時に参照）

| 実装対象 | 参照ファイル |
|---------|-------------|
| MCP サーバー | `src/rss/mcp/server.py` |
| サービス層 | `src/rss/services/feed_manager.py` |
| API クライアント | `src/market/industry/api_clients/census.py` |
| Google 認証 | `src_sample/google_drive_utils.py` |
| 設定管理 | `src/edgar/config.py` |
| エラー定義 | `src/market/errors.py` |
| 型定義 | `src/rss/types.py` |
| ユニットテスト | `tests/rss/unit/mcp/test_server.py` |
| 統合テスト | `tests/rss/integration/test_mcp_integration.py` |

---

## 依存関係

### 新規追加パッケージ

```toml
# pyproject.toml に追加

[project.dependencies]
# 既存パッケージ...
"google-auth>=2.0.0",                    # Google Cloud 認証
"google-cloud-discoveryengine>=0.1.0",  # Discovery Engine API
"httpx>=0.28.1",                         # HTTP クライアント
"pydantic>=2.0.0",                       # データ検証
"structlog>=25.4.0",                     # ロギング（既存）

[project.optional-dependencies]
mcp = [
    "mcp>=1.0.0",                        # MCP フレームワーク（既存）
]

# Phase 1 のみ（プロトタイプ、Phase 2 で削除）
dev = [
    "notebooklm-py>=0.1.0",              # 非公式 API（検証用のみ）
]

[project.scripts]
notebooklm-mcp = "notebooklm.mcp.server:main"
```

### 既存パッケージとの関係

```
notebooklm/
├── 依存: utils_core (ロギング)
├── 依存: なし（独立パッケージ）
└── MCP: FastMCP フレームワーク
```

---

## 検証とテスト戦略

### テストカバレッジ目標

| テスト種別 | 目標カバレッジ | 内容 |
|-----------|---------------|------|
| ユニットテスト | 100% | 全モジュール・全関数 |
| 統合テスト | 主要フロー100% | 実際の API 呼び出し |
| プロパティテスト | オプション | Hypothesis（データ検証） |

### テスト構成

```
tests/notebooklm/
├── unit/
│   ├── test_auth.py              # 認証テスト
│   ├── test_client.py            # API クライアントテスト
│   ├── test_notebook_manager.py  # サービス層テスト
│   ├── test_source_manager.py
│   ├── test_audio_generator.py
│   └── mcp/
│       └── test_server.py        # MCP サーバーテスト
│
├── integration/
│   └── test_api_integration.py   # 実際の API 呼び出しテスト
│
└── conftest.py                   # 共通フィクスチャ
```

### モックとフィクスチャ

```python
# tests/notebooklm/conftest.py

import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_gcloud_token():
    """gcloud CLI トークンのモック"""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = "mock-access-token\n"
        yield mock_run

@pytest.fixture
def mock_api_client():
    """API クライアントのモック"""
    client = Mock()
    client.create_notebook.return_value = {"id": "notebook-123"}
    return client

@pytest.fixture
def sample_notebook_data():
    """サンプルノートブックデータ"""
    return {
        "id": "notebook-123",
        "title": "Test Notebook",
        "sources": [],
        "created_at": "2026-02-16T00:00:00Z",
    }
```

### 統合テストの注意点

**統合テストは実際の API を呼び出すため:**
- GCP プロジェクトが必要
- API 利用料金が発生する可能性
- レート制限に注意
- 環境変数 `RUN_INTEGRATION_TESTS=1` で制御

```python
# tests/notebooklm/integration/test_api_integration.py

import os
import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS") != "1",
    reason="Integration tests require RUN_INTEGRATION_TESTS=1"
)

def test_create_notebook_integration():
    """実際の API でノートブック作成をテスト"""
    # 実際の API 呼び出し
    ...
```

---

## まとめ

### 実装の核心

1. **段階的アプローチ**: notebooklm-py（プロトタイプ） → Enterprise API（本番）
2. **リスク管理**: 各フェーズでリスクを評価・緩和
3. **品質重視**: 100% テストカバレッジ、型安全性、エラーハンドリング
4. **柔軟性**: 両方の認証方式をサポート（gcloud CLI / Service Account）

### 成功の鍵

✅ **Phase 1 での迅速な検証** - notebooklm-py で要件を明確化
✅ **Phase 2 での確実な基盤** - 認証・API クライアントの堅牢な実装
✅ **Phase 3 での本番品質** - テスト・ドキュメント・エラーハンドリング
✅ **継続的な監視** - alpha API の変更を監視、柔軟に対応

### 最初の一歩

**推奨される開始タスク:**
1. 専用 Google アカウント作成（Phase 1 用）
2. `src/notebooklm_proto/` ディレクトリ作成
3. notebooklm-py のインストール・動作確認
4. 最初のツール実装（`notebooklm_create_notebook`）

---

## Sources

- [NotebookLM Pricing](https://www.elite.cloud/post/notebooklm-pricing-2025-free-plan-vs-paid-plan-which-one-actually-saves-you-time/)
- [Create and manage notebooks (API) | NotebookLM Enterprise](https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebooks)
- [Add and manage data sources](https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebooks-sources)
- [NotebookLM Enterprise Overview](https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/overview)
- [NotebookLM-py: The CLI Tool](https://medium.com/@tentenco/notebooklm-py-the-cli-tool-that-unlocks-google-notebooklm-1de7106fd7ca)
- [GitHub - teng-lin/notebooklm-py](https://github.com/teng-lin/notebooklm-py)
- [How to Access NotebookLM Via API?](https://discuss.ai.google.dev/t/how-to-access-notebooklm-via-api/5084)
- [NotebookLM Enterprise rate limits](https://support.google.com/notebooklm/answer/16269187?hl=en)
