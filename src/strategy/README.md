# strategy

投資戦略の構築・バックテスト・評価パッケージ

## 概要

このパッケージは投資戦略の設計、バックテスト、パフォーマンス評価機能を提供します。

**現在のバージョン:** 0.1.0

## ディレクトリ構成

```
strategy/
├── __init__.py           # 公開 API 定義（__version__含む）
├── py.typed              # PEP 561 マーカー
├── types.py              # 型定義
├── core/                 # コアビジネスロジック
│   └── __init__.py
└── utils/                # ユーティリティ関数
    ├── __init__.py
    └── logging_config.py # 構造化ロギング設定
```

## 実装状況

| モジュール                | 状態        | 備考                                |
| ------------------------- | ----------- | ----------------------------------- |
| `types.py`                | ✅ 実装済み | 基本型定義                          |
| `utils/logging_config.py` | ✅ 実装済み | 構造化ロギング                      |
| `core/`                   | ⏳ 未実装   | `/issue` → `feature-implementer` で実装 |

## 公開 API

```python
from strategy import get_logger
```

## 拡張ガイド

1. **コアモジュール追加**: `/issue` → `feature-implementer` で TDD 実装
2. **ユーティリティ追加**: `/issue` → `feature-implementer` で TDD 実装
3. **型定義追加**: `types.py` に追加

## 関連ドキュメント

- `template/src/template_package/README.md` - テンプレート実装の詳細
- `docs/development-guidelines.md` - 開発ガイドライン
