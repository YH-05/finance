# Reuters ニューススクレイピング設計書

- 作成日: 2026-06-10
- 最終更新: 2026-06-10（法務を非スコープ化 / RIC↔NASDAQ ティッカーを実証）
- 対象: `https://www.reuters.com/`
- 目的: クオンツ分析用にロイターのニュース記事（メタデータ + 関連ティッカー + 本文）を収集する
- ステータス: **設計のみ（未実装）**
- 調査ツール: site-investigator スキル（Playwright MCP）+ curl_cffi コールド PoC
- 関連成果物: `.tmp/site-reports/www.reuters.com/report.md` / `.tmp/site-investigation-reuters-2026-06-10.json` / PoC `.tmp/reuters_poc*.py`, `.tmp/reuters_ric_nasdaq.py`

---

## 0. エグゼクティブサマリ

| 項目 | 結論 |
|------|------|
| CMS | **Arc XP (Fusion / PageForge)** — 完全 SSR。記事 URL の単一 GET に全文 JSON 埋め込み。 |
| **bot 対策（実体）** | **DataDome**（記事HTML・内部API を 401 + `captcha-delivery.com` 誘導でブロック）。Akamai は CDN/perf のみ。 |
| **PoC 結果** | サイトマップ XML = curl_cffi コールドで **200**。記事HTML・/pf/api = chrome131 偽装+ヘッダ+Cookieシードでも **401**。 |
| 記事発見 | **ニュースサイトマップ**（コールド取得可、`<news:stock_tickers>` 付き） |
| 本文取得 | **Playwright（実ブラウザ）必須**。curl_cffi 単独は DataDome で不可。 |
| ティッカー | サイトマップ `<news:stock_tickers>`（RIC）→ **NASDAQ ティッカー = 米株 RIC のサフィックス除去（実証一致率 95.5%）** |
| 法務 | **本設計では非スコープ**（ユーザー方針）。robots/規約の判断は各自に委ねる。§1 に最小限のメモのみ。 |
| 収集方針 | **取得時は無フィルタで全件保存（raw レイヤー）。言語/section/subsection は列付与し、フィルタは分析時のみ適用**。 |
| 推奨方針 | **段階A: サイトマップ・メタデータ収集（コールド可・高速）** → 必要時 **段階B: Playwright で本文**。 |

---

## 1. 前提メモ（法務は非スコープ）

- 本設計はユーザー方針により **技術的実現性に集中**し、利用規約・robots.txt・著作権等のリーガル判断は扱わない（各自で判断）。
- 事実情報のみ記録: `robots.txt` は許可リスト方式で `User-agent: *` を `/plus/` 以外 Disallow、`/pf/api/` も Disallow。bot 対策は DataDome。これらは「技術上の制約」として §2 以降で扱う。

---

## 2. サイト構造（調査で確定した事実）

### 2.1 技術スタック・bot 対策
- `window.Fusion` グローバル（Arc XP）。`arcSite="reuters"`, `deployment="366"`。完全 SSR。
- **bot 対策の主壁は DataDome**。証拠: (a) ホームページが `datadome` Cookie をセット、(b) 記事/API の 401 レスポンス本文が `https://geo.captcha-delivery.com/interstitial/...` へ誘導。Akamai（go-mpulse）は perf 計測でブロック主体ではない。

### 2.2 PoC 実測結果（curl_cffi 0.15.0 impersonate=chrome131 / urllib）
| 対象 | 結果 |
|------|------|
| `news-sitemap-index` / サブ（コールド） | **200**（XML フィードは DataDome 通過） |
| 記事 HTML ×3（chrome131 + ブラウザヘッダ / ホーム Cookie シード後 / 素 urllib） | **すべて 401**（DataDome） |
| `/pf/api/...article-by-id-or-url-v1`（コールド） | **401**（本文に captcha-delivery.com） |
| 記事 HTML（Playwright 実ブラウザ） | **200**（完全 SSR・Fusion JSON 取得済） |

結論: **本文取得は Playwright が事実上必須。サイトマップ・メタデータはコールドで取得可能。**

### 2.3 記事 JSON スキーマ（`Fusion.globalContent.result`・Playwright 取得時）
`id`(Arc記事ID/重複排除キー), `canonical_url`, `type`("story"), `title`/`basic_headline`, `description`/`excerpt`/`summary`, `content_elements[]`(本文: `{type:"paragraph",content}` と `{type:"header"}`), `published_time`/`updated_time`(ISO 8601 UTC), `word_count`/`read_minutes`, `authors[]`(name/byline/topic_url/role), `taxonomy.primary_section.name`, `taxonomy.tags[].text`(Reuters トピックコード `RULES:IRAN` 等), `dateline`。

### 2.4 ニュースサイトマップ（記事発見の一次ソース・コールド取得可）
```
インデックス: https://www.reuters.com/arc/outboundfeeds/news-sitemap-index/?outputType=xml  （86サブ）
サブ:        https://www.reuters.com/arc/outboundfeeds/news-sitemap/?outputType=xml[&from={n}]  （各最大100・実測50前後）
```
各 `<url>`: `loc` / `lastmod` / `news:publication_date` / `news:title`(CDATA) / `news:keywords`(GUID/USN) / **`news:stock_tickers`（RIC、カンマ区切り）**。収録範囲は概ね**直近48時間**。ヒストリカルは全件 `sitemap-index` 巡回が必要。

---

## 3. スクレイピング・アーキテクチャ設計

`news_scraper` パッケージのパターン（ソース=1モジュール、`session.py`/`retry.py`/`types.Article` 再利用、CNBC のサイトマップ + Playwright 過去記事収集の前例）に揃え、**新規 `src/news_scraper/reuters.py`** として設計する。

### 3.0 ETL 方針（収集と分析の分離）
- **収集（save）= 無フィルタ全件**: news-sitemap で取得できる記事を**言語/カテゴリで絞らず全件 raw 保存**。各記事に `language`/`section`/`subsection`/`rics_*` をメタデータ列として付与。
- **分析（filter）= 分析時にのみ絞り込み**: 保存済みデータに対し言語/section/subsection/ticker/date でフィルタしてテキスト分析。
- 根拠（実測）: ある時刻のスナップショット 3,799件の言語分布は **es 2,602 / latam 588 / en 438 / pt 78 / fr 35 / de 35 / it 23**。収集時に `en` 限定していたら **88% を取りこぼす**。時間帯で言語構成が大きく変動するため、全件保存が必須。
- 保存先（本番）: `data/raw/news/reuters/{YYYY-MM-DD}/`（raw）。分析は raw をロードしてフィルタ。

### 3.1 収集モード（用途で二段階）
| モード | 取得物 | 手段 | 速度/コスト | クオンツ用途 |
|--------|--------|------|------------|--------------|
| **A: メタデータのみ（推奨初手）** | URL/見出し/公開時刻/**RIC→NASDAQ**/keywords | サイトマップ（curl_cffi コールド 200） | 高速・低負荷 | ティッカー別ヘッドラインフロー、イベント検知、カバレッジ量、見出しセンチメント |
| **B: 本文込み** | A + 本文/著者/タグ/word_count | Playwright（実ブラウザ） | 低速（DataDome） | 本文 NLP・センチメント・固有表現抽出 |

> 段階Aを既定とし、Bは `mode` フラグでオプトイン。B の Playwright 依存は遅延 import。

### 3.2 データフロー
```
[1] 発見(共通)   news-sitemap-index → 各サブ（curl_cffi, 2-3s間隔）
                 → SitemapEntry{loc,title,pub_date,lastmod,rics[],keywords}
                 → lastmod / pub_date で差分フィルタ（前回収集以降のみ）
                       │
        ┌── mode A ──┴── mode B ──┐
[2A] 正規化のみ        [2B] 本文取得（Playwright, 5-10s間隔, 並列1-2）
                          → 生HTML から Fusion.globalContent 抽出
                          → content_elements 結合（フォールバック JSON-LD→trafilatura）
                       │
[3] ティッカー変換  convert_rics()：米株RIC→NASDAQティッカー（§5）。Article へマップ
[4] 永続化         DataFrame → parquet（data/processed/news/reuters/）。重複排除キー = Arc id(B) / loc(A)
```

### 3.3 モジュール構成（`reuters.py`）
| 関数 | 役割 | モード |
|------|------|--------|
| `fetch_news_sitemap(session, since=None) -> list[SitemapEntry]` | インデックス→サブを辿り `since` 以降を返す | A/B |
| `parse_sitemap_xml(xml) -> list[SitemapEntry]` | `<url>` から loc/title/date/rics/keywords 抽出 | A/B |
| `convert_rics(rics) -> RicConversion` | RIC→NASDAQ ティッカー変換（§5）。米株/その他を分離 | A/B |
| `fetch_article_playwright(url) -> str` | 実ブラウザで記事 HTML 取得（DataDome 通過） | B |
| `extract_fusion_json(html) -> dict` | `Fusion.globalContent = {...};` をインライン抽出 | B |
| `parse_article(html) -> Article` | Fusion JSON→Article（フォールバック JSON-LD/trafilatura） | B |
| `collect_reuters_news(config, mode="metadata", since=None, limit=None) -> pd.DataFrame` | エントリポイント | A/B |

### 3.4 データモデル（既存 `types.Article` を利用）
- `ticker` には **NASDAQ ティッカー**（§5 変換後、複数は カンマ区切り）を格納。リポジトリ基準形式は NASDAQ 形式（`normalize_ticker(nasdaq_symbol, target)` の入力＝NASDAQ 形式、クラス株はドット `BRK.B`）。
- `metadata` に `rics_raw`（元 RIC 全件）, `rics_nonus`（指数/FX/先物/国際株などNASDAQ対象外）, `rics_unmatched`, `keywords`, `lastmod`、mode B では `+{updated_time,word_count,read_minutes,dateline,taxonomy_tags[]}` を保持。

| Article | mode A | mode B 追加 |
|---------|--------|-------------|
| `title` | `news:title` | `result.title` |
| `url` | `loc` | `canonical_url` |
| `published` | `news:publication_date` | `published_time` |
| `category` | URL 先頭セクション | `taxonomy.primary_section.name` |
| `source` | `"reuters"` | 同左 |
| `content` | `""` | `content_elements[]` 結合 |
| `ticker` | **`convert_rics(...)` の NASDAQ ティッカー** | 同左 |
| `article_id` | `loc` | Arc `id` |

---

## 4. レート制御・bot 回避設計
| 項目 | サイトマップ(A) | 記事本文(B) |
|------|-----------------|-------------|
| 手段 | curl_cffi `impersonate=chrome131`（`create_session`） | Playwright（実ブラウザ、headful 推奨） |
| 間隔 | 2–3 秒 + ジッタ | 5–10 秒 + ジッタ |
| 並列 | 1–2 | 1–2 |
| リトライ | `retry.py` 指数バックオフ（401/429/5xx で待機増） | 同左。401 連発時はコンテキスト再構築 |
| Cookie | セッション維持 | ブラウザコンテキスト維持（`datadome` 保持） |

**高速化オプション（B）**: Playwright で `datadome` Cookie を取得 → curl_cffi に注入して後続記事を高速取得。Cookie は fingerprint/IP に紐づき短命なため、最適化扱い（既定にしない）。

---

## 5. RIC → NASDAQ ティッカー変換（実証済み）

### 5.1 リポジトリの基準形式
- 基準は **NASDAQ 形式**。`normalize_ticker(nasdaq_symbol, target)`（`src/market/pipeline/ticker_normalizer.py`）は **常に NASDAQ 形式を入力**に取り、`yfinance`(`.`→`-`)/`alphavantage`(`.`前)/`sec_edgar`(恒等)/`nasdaq`(恒等) へ変換する。
- NASDAQ 形式のクラス株はドット表記（`BRK.B`, `GEF.B`）。
- → Reuters 収集は **RIC を NASDAQ 形式に変換**して `ticker` に入れれば、既存の `normalize_ticker` で他ソース形式へ展開できる。

### 5.2 実証結果（PoC: `reuters_ric_nasdaq.py`）
- サイトマップ10ページから **395 unique RIC**（825 mentions）収集。
- NASDAQ 公式ディレクトリ（`nasdaqlisted.txt`+`otherlisted.txt`、**13,319 シンボル**）と突合。
- **米株 RIC 89件 → 一致率 95.5%**:
  - 直接一致 **84**（root == NASDAQ ティッカー。例 `AAPL.O`→`AAPL`, `BA.N`→`BA`, `AVGO.O`→`AVGO`）
  - クラス株一致 **1**（`BFb.N`→`BF.B`。末尾小文字→ドット表記を実証）
  - 未一致 **4**（`SPCX.O`=SpaceX 上場前プレースホルダ, `MTSR.O`=最近のIPO/買収, `CDTX.O`, `EXAS.O`）＝タイミング/エッジケース。要個別確認。

### 5.3 変換ルール（`convert_rics` 設計）
| RIC パターン | 判定 | NASDAQ ティッカー |
|--------------|------|-------------------|
| `{root}.{O,OQ,N,A,P,K,PK,DG,PH}` | **米株** | **`root`（サフィックス除去）**。root が `^[A-Z0-9]+[a-z]$`（クラス株）なら末尾小文字 X → `{base}.{X}`（例 `BFb`→`BF.B`） |
| 先頭 `.`（`.SPX` `.IXIC` `.N225` `.AXJO` …） | 指数 | NASDAQ ティッカーではない → `metadata.rics_nonus` に退避 |
| 末尾 `=`（`EUR=` `JPY=` …） | FX | 同上（退避） |
| 末尾 `c{n}`/`cv{n}`（`CLc1` `LCOc1` …） | 先物 | 同上（退避） |
| `{root}.{T,AX,L,HK,SS,SZ,TO,PA,DE,MI,SA,BA,NS,BO,KS,…}` | 国際株 | NASDAQ 対象外 → `rics_nonus`（ADR で米上場の場合のみ別途 ADR ティッカーが必要） |
| `{root}.UL` | Reuters 非上場 | 破棄 |
| 未一致米株 | エッジ | `metadata.rics_unmatched` に保持 + ログ |

### 5.4 取引所サフィックス → 上場市場（メタデータ）
`.O`/`.OQ`=NASDAQ, `.N`=NYSE, `.A`=NYSE American, `.P`=NYSE Arca, `.K`=NYSE系, `.PK`=OTC/Pink。`ticker` には不要だが、`metadata.listing_exchange` として保持するとフィルタに有用。

### 5.5 実装方針
- **米株のみを `ticker`（NASDAQ 形式）に採用**。指数/FX/先物/国際株は `metadata.rics_nonus` に分離（NASDAQ ティッカー universe には乗らない）。
- NASDAQ ディレクトリ（`nasdaqlisted.txt`/`otherlisted.txt`）を任意で取り込み、変換後ティッカーの **実在検証**（universe フィルタ）に使える。未一致は破棄せず `rics_unmatched` に残してログ駆動で精査。
- 変換は純関数（I/O なし）として実装し、ディレクトリ照合はオプションのバリデーション層に分離。

---

## 6. 段階的実装計画

| Phase | 内容 | 完了条件 |
|-------|------|---------|
| 1 | サイトマップパーサ + `SitemapEntry` | `news-sitemap` から loc/title/date/rics 抽出の単体テスト green |
| 2 | `convert_rics`（§5、純関数） | 米株除去/クラス株/退避分類の単体テスト green（`AAPL.O`→`AAPL`, `BFb.N`→`BF.B`, `.SPX`→退避） |
| 3 | mode A 統合（メタデータ収集 + 差分 + parquet） | 差分収集・重複排除・保存が動作 |
| 4 | （任意）NASDAQ ディレクトリ照合バリデーション | 変換後ティッカーの実在率を計測 |
| 5 | mode B: Playwright 本文取得 + Fusion パーサ | 複数記事タイプで本文・メタ抽出 green、DataDome を低速で通過 |
| 6 | クオンツ連携 | RIC→NASDAQ カバレッジ計測、ティッカー別/トピックコード別集計の最小例 |

各 Phase は TDD（`test-writer`/`test-unit-writer`）で実装し `feature-implementer` に委譲。`make check-all` を各サイクルで通す。

---

## 7. リスク・検証項目
| リスク | 対応 |
|--------|------|
| **DataDome により本文ページが 401** | mode A（メタデータのみ）を既定に。本文は Playwright |
| Playwright headless が DataDome に検知 | headful/stealth を検証。検知時は間隔拡大・セッション分散 |
| `datadome` Cookie 注入の短命 | 既定にしない。最適化オプション扱い |
| `Fusion.globalContent` 形式変更 | JSON-LD / trafilatura の二重フォールバック |
| 米株 RIC 未一致（上場前/IPO直後/コーポレートアクション） | `rics_unmatched` 保持・ログ・ディレクトリ照合で検出（実証 4/89=4.5%） |
| クラス株・優先株・ワラントの RIC 表記揺れ | 末尾小文字→ドット規則 + ディレクトリ照合で吸収。優先/ワラントは個別対応 |
| 国際株/指数/FX/先物は NASDAQ 非対象 | `rics_nonus` に分離（universe 外として明示） |
| サイトマップ 48h 制限 | ヒストリカルは全件 sitemap-index を低速巡回（量大） |

---

## 9. mode A PoC 実測・カバレッジ分析（`reuters_mode_a_poc.py`）

### 9.1 言語フィルタ（実装済み）
- **`<news:language>` は信頼不可**: 多言語記事（`/es/`, `/pt/` 等）でも全件 `en` と誤タグ付け（実測 600/600 が `en`）。
- **言語判定は URL セクションプレフィックスで行う**: `/es/`(スペイン語), `/pt/`(ポルトガル語), `/fr/`, `/de/`, `/it/`, `/latam/` 等は多言語版。英語記事は `world`/`business`/`markets`/`legal`/`sports`/`commentary`/`fact-check` 等。
- `--lang en`（既定）で英語のみ抽出。実測: 12ページ 600件 → 英語 364件（非英語 236件を除外）。`NON_EN_SECTIONS` 集合で判定（生 `news:language` は `metadata.sitemap_lang_tag` に参考保持）。

### 9.2 ティッカー・カバレッジ（英語記事 364件）
- **NASDAQ ティッカーあり: 22.0%（80件）** / なし: 78.0%（284件）。
- ETF ティッカー（例 `EPU`=iShares MSCI Peru）も **NASDAQ ティッカーとして含める**（除外しない方針）。

### 9.3 NASDAQ 非紐付けニュースの傾向（284件の内訳）
| 分類 | 比率（非紐付け中） | 内容傾向 |
|------|-------------------|----------|
| **(a) stock_tickers タグ自体なし** | 75.4%（214件） | スポーツ（NHL/NBA/MLB/World Cup）、政治・地政学（Iran/Ukraine/Congress）、マクロ経済（雇用・インフレ統計）、fact-check/commentary。**個別企業に紐づかないニュース**。 |
| **(b) タグはあるが米株 RIC なし** | 24.6%（70件） | **米国外上場の国際企業**（日本 `8306.T`/`7974.T`、伊 `.MI`、英 `.L`、印 `.NS`、ASX 等）+ **マクロ/市場系**（指数 `.N225`、FX、商品先物 `CLc1`/`GCcv1`、経済指標 `=ECI`）。 |

- 非紐付けニュースの見出し頻出語: `world`/`cup`(World Cup)/`iran`/`oil`/`prices`/`inflation`/`india`/`ukraine`/`mexico` → スポーツ・地政学・マクロ・商品が主。
- 含意（クオンツ）: **NASDAQ ティッカー universe で拾えるのは英語記事の約22%**。残り78%は (a) 非企業ニュース、(b) 国際株・マクロ・商品。米株シグナルに絞るなら (a)(b) は対象外だが、**マクロ/商品/国際株シグナルを使うなら `metadata.rics_nonus`（指数/FX/先物/国際株 RIC）が別途活用可能**。

### 9.5 メタデータフィルタリング設計（カテゴリ指定収集）

**重要な構造的事実**: 発見フィード（news-sitemap / sitemap-index）は**フラット**で全カテゴリが時系列混在。**サーバ側でのカテゴリ絞り込みはできない**。カテゴリは URL パス `/{section}/{subsection}/{slug}/` に符号化されている。
- **topic-sitemap**（`/arc/outboundfeeds/topic-sitemap/?outputType=xml`）= **538 個のカテゴリ/トピック URL**（`/business/aerospace-defense/`, `/technology/ai-and-us/`, `/world/us/alabama/` 等）。これは**カテゴリの正規辞書**（各カテゴリの記事フィードではなくランディング URL 一覧）。フィルタ値の妥当性検証・列挙に使える。

→ 発見フィードはフラットなので、**収集は無フィルタ全件保存**し、**フィルタは保存データに対する分析時処理**として実装する（§3.0）。フィルタ軸:

| 軸 | ソース（保存列） | フィルタ適用 | 実装 |
|----|--------|-------------|------|
| **言語** | `language`（URL セクション先頭。`news:language` は誤タグで不可） | **分析時** | `filter_df` / `--lang`（実装済み） |
| **カテゴリ（section）** | `section`（URL 第1セグメント `business`） | **分析時** include/exclude | `--sections` / `--exclude-sections`（実装済み） |
| **カテゴリ（subsection）** | `subsection`（URL 第1-2 `business/energy`） | **分析時**（粒度細） | `--sections business/energy`（実装済み） |
| **ティッカー** | `ticker` / `metadata.rics_nasdaq` | 分析時 | DataFrame フィルタ |
| **日付** | `published` / `metadata.lastmod` | 分析時（収集時は増分制御のみ） | `--since`（収集範囲）/ 分析時は列で絞る |
| トピックコード（`RULES:*`） | 記事JSON `taxonomy.tags` | 記事取得後 | mode B のみ |
| カテゴリ指定の**収集**（サーバ側） | Arc collection API / セクションページ | Playwright 必須（DataDome） | mode B（深掘り/ヒストリカル時） |

- 収集（`collect`）は言語/カテゴリでフィルタせず全件保存。分析（`filter_df`）が保存済みの `language`/`section`/`subsection` 列で絞り込む（`--sections` は両粒度を OR マッチ）。
- **実測効果（分析時フィルタ）**: 金融系（`business,markets,technology`）に絞ると **ティッカー付与率 22.0% → 33.3%**、`sports,podcasts` 除外で 27.4%。**カテゴリフィルタはクオンツ用途のS/N比を直接改善**する。
- 設計上の使い分け: **日次インクリメンタル収集 = フラット news-sitemap を全件保存（mode A、安価）**。**特定カテゴリのヒストリカル深掘り = セクションページ/collection API（mode B、Playwright）**。

### 9.4 PoC 実行結果サマリ
| 項目 | 値 |
|------|-----|
| 全件保存（86ページ・無フィルタ） | **3,799件**（直近約48h、curl_cffi コールド 200、parquet 941KB） |
| 言語分布 | es 2,602 / latam 588 / en 438 / pt 78 / fr 35 / de 35 / it 23（時間帯で大変動 → 全件保存必須） |
| NASDAQ ティッカー | unique 281・mentions 1,186（ETF・優先株含む） |
| ディレクトリ照合 | 実在率 **93.4%**（1,108/1,186）。未一致は上場廃止/改名/M&A（`ABC`/`DISCA`/`GPS`/`JWN`/`ENDP`…）・上場前（`SPCX`）・優先株（`AAM_pa`） |
| 出力 | CSV + parquet（14列: Article 11列 + `language`/`section`/`subsection`） |
| CLI | 収集: `--pages`/`--since`/`--validate`。分析時フィルタ: `--lang`/`--sections`/`--exclude-sections`/`--analyze` |

> 補足: 優先株は Reuters で `XXX_pa`（_p+クラス）表記。`convert_rics` 拡張時に `_p{X}` → NASDAQ 優先株表記（`XXX-{X}` / `XXX.PR{X}`）への対応を追加余地（現状は米株サフィックス規則の対象外で `rics_unmatched`/`nonus` 行き）。

---

## 8. 参考成果物
- 調査 JSON: `.tmp/site-investigation-reuters-2026-06-10.json`
- 調査レポート: `.tmp/site-reports/www.reuters.com/report.md` / `report.json`
- PoC（使い捨て）: `.tmp/reuters_poc.py`/`reuters_poc2.py`（DataDome 確定）, `.tmp/reuters_ric_nasdaq.py`（RIC↔NASDAQ 突合・一致率95.5%）
- 既存実装パターン: `src/news_scraper/cnbc.py`（サイトマップ + Playwright）, `session.py`, `types.py`, `retry.py`
- 自社ティッカー基準: `src/market/pipeline/ticker_normalizer.py`（`normalize_ticker`、入力＝NASDAQ 形式）

> AIDEV-NOTE: 本設計は技術面に集中（法務は非スコープ・各自判断）。bot 対策は DataDome（本文は Playwright 経由）。RIC→NASDAQ は「米株 RIC のサフィックス除去（実証一致率 95.5%）+ クラス株 末尾小文字→ドット」。
