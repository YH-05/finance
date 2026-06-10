# 議論メモ: Reuters mode B（本文取得）実現可否・代替手段の調査

**日付**: 2026-06-10
**議論ID**: disc-2026-06-10-reuters-mode-b-investigation
**プロジェクト**: Project:quants-library
**先行**: disc-2026-06-10-reuters-news-scraper（FOLLOWS）
**参加**: ユーザー + AI

## 背景・コンテキスト

mode A（メタデータ収集）を main にマージ済み。次フェーズの mode B（記事本文取得）の実装に着手したが、本文ページは DataDome で保護されており実現可否の検証が必要だった。

## 議論のサマリー

1. **DataDome 通過検証（全滅）**: vanilla Playwright を headless/headful × bundled-chromium/実Chrome の4構成で試行 → すべて記事ページ 401。さらに stealth-lite（webdriver 隠蔽・homepage seed）、patchright（DataDome 特化 stealth Playwright）でも**ホームページ含め 401**（`captcha-delivery.com` 誘導）。調査時に MCP ブラウザが通過したのはフレッシュなウォームアップ状態だったためと推定。
2. **無料代替の調査**: archive.today=429（厳格レート制限）、r.jina.ai=451（Reuters 明示ブロック）、GDELT=メタデータのみ本文なし。**Wayback Machine が最有力**（アーカイブ済み HTML に Fusion/JSON-LD 本文が残る）だが、本日の大量アクセス（mode A 86ページ + 多数 PoC）で **archive.org も 429（IP rate-limit）** となり、クールダウン180s + 300/600/1200s バックオフでも解消せず本文取得可否を未検証。
3. **方針決定**: Wayback を後日（別セッション・IP クールダウン後）低速で再検証し、本文が取れれば mode B = Wayback 経由で TDD 実装。非リアルタイム・カバレッジ部分的の制約付き。確実性・リアルタイム性重視なら有料（LSEG MRN / Reuters Connect / commercial unblocker）が現実解。

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-06-10-005 | **mode B（無料 Playwright 本文取得）は DataDome により実現不可能**（vanilla×4 + stealth + patchright すべて 401） | MCP 通過はフレッシュ状態の偶然と推定 |
| dec-2026-06-10-006 | 無料代替も全滅: archive.today=429 / jina=451(Reuters明示ブロック) / GDELT=本文なし / Wayback=本日 IP rate-limit で未検証 | mode A 86ページ + 多数 PoC で IP が複数サービスで制限 |
| dec-2026-06-10-007 | **方針=Wayback を後日低速で再検証→可なら mode B=Wayback 経由 TDD 実装**（非リアルタイム・部分カバレッジ）。確実/リアルタイム重視なら有料 API/unblocker | ユーザー選択 |

## アクションアイテム

| ID | 内容 | 優先度 | 状態 |
|----|------|--------|------|
| act-2026-06-10-004 | [次回セッション・IP クールダウン後] `.tmp/reuters_wayback_verify.py` を低速実行し、Wayback スナップショットの本文残存・カバレッジ・lag を確認 | 中 | pending |
| act-2026-06-10-005 | 検証 OK なら mode B = Wayback 経由本文取得を TDD 実装（fetch_via_wayback / extract_fusion_json / parse_article を純関数化） | 中 | pending |
| act-2026-06-10-006 | feature/reuters-mode-b ブランチの扱い決定（コミットなし。削除して後日切り直す or 保持） | 低 | pending |

## 次回の議論トピック

- Wayback 再検証の結果に基づく mode B 実装可否の最終判断
- 本文ベース分析の必要性とコスト（無料 Wayback の制約 vs 有料 API の確実性）
- IP rate-limit を避けるための収集ペーシング・プロキシ方針

## 参考情報

- DataDome 通過検証 PoC: `.tmp/reuters_mode_b_poc.py`, `.tmp/reuters_mode_b_poc2.py`
- 代替手段調査: `.tmp/reuters_alt_sources.py`
- Wayback 低速検証（再実行用）: `.tmp/reuters_wayback_verify.py`
- mode A 実装: main（PR #3971 / a5da158）
- 関連メモリ: `feedback_ci_lint_reproduction`
