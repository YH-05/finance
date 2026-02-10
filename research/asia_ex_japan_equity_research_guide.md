# アジア（日本除く）個別株リサーチガイド

## 概要

アジア地域（日本除く）の株式ポートフォリオ運用における個別株リサーチの方法論をまとめたガイド。米国のSEC EDGAR のような統一的な情報公開システムが存在しないアジア市場において、どのように体系的に情報を収集・分析すべきかを整理する。

---

## 1. 各国の規制当局・取引所の開示システム

### 1.1 主要市場の開示プラットフォーム一覧

| 国/地域 | 取引所 | 開示システム | URL | 開示言語 | 整備度 |
|---------|--------|------------|-----|---------|--------|
| 香港 | HKEX | HKEXnews | https://www.hkexnews.hk | 英語/中国語 | ★★★★★ |
| 中国 | SSE / SZSE | 巨潮資訊網 (CNINFO) | https://www.cninfo.com.cn | 中国語（一部英語） | ★★★★☆ |
| 韓国 | KRX | DART (電子公示システム) | https://dart.fss.or.kr | 韓国語/英語 | ★★★★★ |
| 台湾 | TWSE | MOPS (公開資訊観測站) | https://mops.twse.com.tw | 中国語/英語 | ★★★★☆ |
| シンガポール | SGX | SGXNet | https://www.sgx.com | 英語 | ★★★★☆ |
| インド | BSE / NSE | BSE Listing Centre / NSE NEAPS | https://www.bseindia.com | 英語 | ★★★★☆ |
| タイ | SET | SET SMART | https://setsmart.set.or.th | タイ語/英語 | ★★★☆☆ |
| インドネシア | IDX | IDX Website | https://www.idx.co.id | インドネシア語/英語 | ★★★☆☆ |
| フィリピン | PSE | PSE EDGE | https://edge.pse.com.ph | 英語 | ★★★☆☆ |
| ベトナム | HOSE / HNX | 各取引所サイト | https://www.hsx.vn | ベトナム語（英語限定的） | ★★☆☆☆ |
| マレーシア | Bursa Malaysia | Bursa Malaysia Announcements | https://www.bursamalaysia.com | 英語/マレー語 | ★★★☆☆ |

### 1.2 各開示システムの詳細

#### 香港 - HKEXnews（推奨度: 最高）

- **開示書類**: 年報、中間報告、四半期報告（任意）、通函（Circular）、月次リターン、インサイダー取引
- **強み**: 英語と中国語の二言語開示が義務。開示品質が高い
- **注意点**: H株とレッドチップでは開示基準が異なる場合がある
- **IFRS準拠**: はい（HKFRS = IFRSとほぼ同等）
- **自動取得**: HKEXnewsはRSSフィード非提供だが、APIまたはスクレイピングで取得可能

#### 中国 - 巨潮資訊網 CNINFO

- **開示書類**: 年度報告、半年度報告、季度報告、臨時公告
- **強み**: A株の全開示書類を網羅。データ量は膨大
- **注意点**: 中国語のみの開示が大半。中国会計基準（CAS）を使用。IFRSとの差異に注意
- **自動取得**: APIが提供されている（中国語ドキュメント）

#### 韓国 - DART（推奨度: 最高）

- **開示書類**: 事業報告書、半期報告書、分期報告書、主要事項報告
- **強み**: SEC EDGARに匹敵する整備度。Open DART API（無料）を提供しており、プログラムからのデータ取得が容易
- **注意点**: 韓国語が主だが、英語開示も増加中（大型株）
- **IFRS準拠**: はい（K-IFRS）
- **自動取得**: Open DART API（https://opendart.fss.or.kr）で財務データ・開示書類を取得可能

#### 台湾 - MOPS

- **開示書類**: 年報、財務報告、重大訊息、月次売上高
- **強み**: 月次売上高データが公開されており、業績のリアルタイム追跡が可能
- **注意点**: 主に中国語。TIFRS（IFRSベース）を採用
- **自動取得**: 一部データはAPI経由で取得可能

#### インド - BSE / NSE

- **開示書類**: 年次報告書、四半期決算、コーポレートガバナンス報告
- **強み**: 英語での開示が標準。四半期決算の開示が義務化されており頻度が高い
- **注意点**: Ind AS（IFRSベース）を採用。関連当事者取引の開示に注意
- **自動取得**: BSE APIが利用可能

#### シンガポール - SGXNet

- **開示書類**: 年報、半期/四半期報告、SGXNet通知
- **強み**: 英語開示が標準。開示品質が高い
- **注意点**: 小型株は四半期報告が免除される場合がある
- **IFRS準拠**: SFRS(I) = IFRSと同等

---

## 2. 金融データプロバイダー

### 2.1 プロフェッショナル向け（有料）

| プロバイダー | アジアカバレッジ | 特徴 | 年間コスト目安 |
|-------------|----------------|------|---------------|
| Bloomberg Terminal | 最も包括的 | リアルタイムデータ、ニュース、アナリスト予想、チャット機能 | $24,000+ |
| Refinitiv Eikon (LSEG) | 非常に広い | Bloomberg次点。APIアクセスが充実 | $15,000+ |
| S&P Capital IQ | 広い | 財務データ・バリュエーション・M&Aデータに強い | $12,000+ |
| FactSet | 拡大中 | カスタマイズ性が高い。定量分析向き | $12,000+ |
| CEIC (ISI Emerging Markets) | アジアに強い | マクロ経済データに特化。新興国データが充実 | $5,000+ |

### 2.2 無料・低コスト代替

| ソース | 特徴 | アジアカバレッジ | 自動化 |
|--------|------|----------------|--------|
| **Yahoo Finance** | 基本的な株価・財務データ | 主要市場対応 | yfinance (Python) で取得可能 |
| **Google Finance** | 株価・基本指標 | 主要市場対応 | 非公式API |
| **TradingView** | チャート・テクニカル | 広い | 無料枠あり |
| **TIKR** | 詳細な財務データ | 新興市場含む | 無料枠あり（制限付き） |
| **Simply Wall St** | 財務データの可視化 | 広い | 無料枠あり |
| **Macrotrends** | 長期財務データ | 主に大型株 | なし |
| **Wisesheets** | Excel/Sheets連携 | 主要市場 | スプレッドシート連携 |
| **Financial Modeling Prep** | API提供 | 主要市場 | REST API（無料枠あり） |

### 2.3 アジア特化データソース

| ソース | 対象地域 | 特徴 |
|--------|---------|------|
| Wind (万得) | 中国 | 中国金融データの最も包括的なプロバイダー |
| Choice (東方財富) | 中国 | Windの低コスト代替 |
| KIS-VALUE | 韓国 | 韓国株の詳細データ |
| TEJ (台湾経済新報) | 台湾 | 台湾株の包括的データ |
| Ace Equity | インド | インド株の詳細データ |

---

## 3. アナリストレポート・リサーチソース

### 3.1 セルサイドリサーチ

| 証券会社/リサーチ | 強み | アクセス方法 |
|------------------|------|-------------|
| CLSA | アジア全域。独自の視点 | 口座開設 or 購入 |
| Macquarie | アジア全域。セクター分析に強い | 口座開設 or 購入 |
| Nomura Asia | アジア全域。日系の視点 | 口座開設 or 購入 |
| JP Morgan Asia | アジア全域。グローバルな文脈 | 口座開設 or 購入 |
| UBS Asia | アジア全域。ウェルスマネジメントの視点 | 口座開設 or 購入 |
| CITIC Securities | 中国A株に強い | 口座開設 |
| Samsung Securities | 韓国株に強い | 口座開設 |
| Yuanta Securities | 台湾株に強い | 口座開設 |

### 3.2 独立系リサーチ

| プラットフォーム | 特徴 | コスト |
|----------------|------|--------|
| **Smartkarma** | アジア特化の独立系リサーチプラットフォーム。100名超のアナリスト | 有料 |
| **Visible Alpha** | コンセンサス予想の詳細分解 | 有料 |
| **Seeking Alpha** | ユーザー投稿型。アジア銘柄の記事もあり | 無料枠あり |
| **Gurufocus** | バリュー投資家向け。国際株カバー | 無料枠あり |

---

## 4. ニュース・定性情報ソース

### 4.1 地域横断メディア

| メディア | 言語 | 特徴 | RSS対応 |
|---------|------|------|---------|
| Nikkei Asia | 英語 | アジアビジネス全般。質が高い | あり |
| Reuters Asia | 英語 | 速報性が高い | あり |
| Bloomberg Asia | 英語 | 市場分析が充実 | 一部 |
| CNBC Asia | 英語 | 市場動向中心 | あり |
| Financial Times - Asia | 英語 | 深い分析記事 | あり |

### 4.2 国・地域別メディア

| 国/地域 | メディア | 言語 | 特徴 |
|---------|---------|------|------|
| **中国** | Caixin Global | 英語 | 中国経済の最も信頼性の高いソース |
| **中国** | 36Kr | 中国語/英語 | テック・スタートアップ |
| **中国** | South China Morning Post | 英語 | 中国・香港全般 |
| **韓国** | Pulse by Maeil Business | 英語 | 韓国ビジネス・市場 |
| **韓国** | Korea Herald | 英語 | 韓国全般 |
| **台湾** | Taipei Times | 英語 | 台湾全般 |
| **台湾** | Digitimes | 英語 | 半導体・テック |
| **インド** | The Economic Times | 英語 | インド経済・市場 |
| **インド** | Livemint | 英語 | インドビジネス |
| **ASEAN** | The Straits Times | 英語 | シンガポール・ASEAN |
| **ASEAN** | Bangkok Post | 英語 | タイ |
| **ASEAN** | Jakarta Globe | 英語 | インドネシア |

### 4.3 セクター特化メディア

| セクター | メディア | 特徴 |
|---------|---------|------|
| 半導体 | Digitimes, SemiAnalysis, TechInsights | アジアサプライチェーンに強い |
| テック | 36Kr, Tech in Asia, KrASIA | アジアテックエコシステム |
| 不動産 | Mingtiandi | アジア不動産市場 |
| コモディティ | Platts, Argus | アジアのエネルギー・金属 |

---

## 5. マクロ経済・カントリーリスク情報

### 5.1 マクロ経済データソース

| ソース | 特徴 | コスト |
|--------|------|--------|
| FRED (St. Louis Fed) | 米国中心だが国際データも | 無料 |
| World Bank Open Data | 新興国のマクロ指標 | 無料 |
| IMF Data | 国際収支、財政データ | 無料 |
| Asian Development Bank (ADB) | アジア特化のマクロデータ | 無料 |
| OECD Data | 先進国のマクロ指標 | 無料 |
| Trading Economics | 広範なマクロデータ。予測値つき | 無料枠あり |

### 5.2 中央銀行・政府機関

| 国/地域 | 中央銀行 | 主な公開データ |
|---------|---------|--------------|
| 中国 | PBOC (人民銀行) | 金利、M2、外貨準備 |
| 香港 | HKMA | 為替介入、銀行統計 |
| 韓国 | BOK (韓国銀行) | ECOS経済統計システム |
| 台湾 | CBC (中央銀行) | 金融統計 |
| インド | RBI (インド準備銀行) | 金融政策、銀行統計 |
| シンガポール | MAS | 金融政策、マクロ統計 |
| タイ | BOT (タイ中央銀行) | 経済・金融統計 |
| インドネシア | BI (インドネシア銀行) | 金融政策、為替データ |

### 5.3 カントリーリスク評価

| ソース | 特徴 |
|--------|------|
| World Bank - Ease of Doing Business | ビジネス環境評価 |
| Transparency International - CPI | 腐敗認知指数 |
| Heritage Foundation - Economic Freedom | 経済自由度指数 |
| Political Risk Services (PRS) | 政治リスク評価 |
| Moody's / S&P / Fitch | ソブリン格付け |

---

## 6. アジア株リサーチの実践フレームワーク

### 6.1 スクリーニングフェーズ

```
目的: 投資候補のユニバースを構築

入力:
  - 地域・国の選定（マクロ環境に基づく）
  - セクター選定（テーマ・サイクルに基づく）
  - 定量フィルター（時価総額、流動性、ROE等）

ツール:
  - yfinance でスクリーニング実行
  - TradingView のスクリーナー
  - Bloomberg / Refinitiv のスクリーナー

出力:
  - 20-50銘柄の候補リスト
```

**スクリーニング時の最低条件**:
- 時価総額: $500M以上（流動性確保）
- 日次売買代金: $5M以上
- 上場年数: 3年以上（トラックレコード確保）

### 6.2 財務分析フェーズ

```
目的: 定量的な企業価値評価

入力:
  - 年報・決算データ（各国開示システムから取得）
  - 過去5-10年の財務時系列データ

分析項目:
  1. 収益性: ROE, ROA, 営業利益率, ROIC
  2. 成長性: 売上成長率, EPS成長率, CAGR
  3. 財務健全性: D/E ratio, Interest Coverage, FCF
  4. 効率性: 資産回転率, 在庫回転率, CCC
  5. バリュエーション: P/E, P/B, EV/EBITDA, PEG

ツール:
  - yfinance で基本データ取得
  - 年報から詳細データ手動抽出
  - スプレッドシートでモデル構築

出力:
  - 財務サマリーシート
  - バリュエーション比較表
```

### 6.3 定性分析フェーズ

```
目的: 事業の競争優位性と持続可能性の評価

入力:
  - 年報の経営者メッセージ・MD&A
  - 業界レポート
  - ニュース・アナリストレポート

分析項目:
  1. 事業モデル: 収益源、顧客構成、地理的分散
  2. 競争環境: 市場シェア、参入障壁、代替品の脅威
  3. 経営陣: トラックレコード、報酬体系、株式保有
  4. ESG: 環境リスク、社会的責任、ガバナンス
  5. 成長ドライバー: 新製品、新市場、M&A戦略

出力:
  - 定性分析レポート
  - SWOT分析
```

### 6.4 リスク評価フェーズ

```
目的: アジア株特有のリスクを評価

チェックリスト:
  □ ガバナンスリスク
    - 支配株主の持分比率と影響力
    - 関連当事者取引の規模と頻度
    - 独立取締役の割合と実効性
    - 監査法人の質（Big 4か否か）

  □ 規制リスク
    - 外国人投資制限（持分上限、産業規制）
    - 資本規制（配当送金、資金移動の制限）
    - 産業政策の変更リスク

  □ 為替リスク
    - 通貨のボラティリティ
    - ペッグ制 or 変動相場制
    - ヘッジコスト

  □ 流動性リスク
    - 日次売買代金
    - ビッド・アスクスプレッド
    - フリーフロート比率

  □ 地政学リスク
    - 米中関係の影響
    - 地域紛争リスク
    - サプライチェーンへの影響
```

### 6.5 投資判断フェーズ

```
目的: 総合的な投資判断

統合評価:
  1. 定量スコア（財務分析の結果）
  2. 定性スコア（事業品質の評価）
  3. リスクスコア（リスク要因の重み付け）
  4. バリュエーション判断（割安度）

ポジションサイジング考慮:
  - 確信度に応じたサイジング
  - カントリー集中度の上限設定
  - セクター集中度の上限設定
  - 通貨エクスポージャーの管理
```

---

## 7. アジア株特有の注意点

### 7.1 会計基準の違い

| 国/地域 | 会計基準 | IFRSとの互換性 | 主な差異ポイント |
|---------|---------|---------------|----------------|
| 香港 | HKFRS | ほぼ同等 | 実質的な差異なし |
| 中国 | CAS (中国会計基準) | 差異あり | 収益認識、金融商品、連結範囲 |
| 韓国 | K-IFRS | 同等 | 実質的な差異なし |
| 台湾 | TIFRS | 同等 | 実質的な差異なし |
| シンガポール | SFRS(I) | 同等 | 実質的な差異なし |
| インド | Ind AS | IFRS収斂 | 一部差異あり（リース、金融商品） |
| タイ | TFRS | IFRS収斂中 | 一部差異あり |
| インドネシア | SAK | IFRS収斂中 | 差異あり |

### 7.2 コーポレートガバナンスの特徴

| 国/地域 | ガバナンス特徴 | リスクレベル |
|---------|--------------|-------------|
| 香港 | 支配株主モデルが一般的。デュアルクラス株あり | 中 |
| 中国 | 国有企業の存在。党委員会の役割 | 高 |
| 韓国 | 財閥（チェボル）構造。循環出資 | 中〜高 |
| 台湾 | 家族経営が多い。テック企業はガバナンス良好 | 中 |
| シンガポール | 政府系企業（GLC）の存在。ガバナンス水準は高い | 低〜中 |
| インド | プロモーター持分が高い。関連当事者取引に注意 | 中〜高 |
| ASEAN | 国により大きく異なる。タイ・フィリピンは家族財閥が支配的 | 中〜高 |

### 7.3 外国人投資制限

| 国/地域 | 外国人持分上限 | 特別ルール |
|---------|--------------|-----------|
| 中国A株 | Stock Connect経由で制限あり | QFII/RQFII制度 |
| 台湾 | 業種により制限あり | 一部セクターは規制対象 |
| タイ | 49%（一般） | Foreign Board (F株) あり |
| インドネシア | セクターにより異なる | ネガティブリスト |
| フィリピン | 40%（一般） | 公益事業等は制限強い |
| インド | セクターにより24-100% | FDI Policy準拠 |
| ベトナム | 49%（一般）、銀行30% | 一部解除の動きあり |
| 韓国 | 制限なし（一部例外） | 比較的オープン |
| 香港 | 制限なし | 最もオープン |
| シンガポール | 制限なし（一部例外） | 金融・メディアに制限 |

---

## 8. 自動化・ツール活用

### 8.1 既存financeライブラリで対応可能な領域

| 機能 | パッケージ | 対応状況 | 備考 |
|------|-----------|---------|------|
| アジア株価データ取得 | `market` (yfinance) | 対応済み | ティッカーに市場サフィックス付与（例: `0700.HK`, `005930.KS`） |
| マクロ経済指標 | `market` (FRED) | 対応済み | 米国中心だが一部国際データあり |
| テクニカル分析 | `analyze` | 対応済み | アジア株にも適用可能 |
| ニュース収集 | `rss` | 拡張可能 | アジアメディアのRSSフィードを追加すれば対応 |
| SEC Filings | `edgar` | 米国のみ | アジアは未対応 |

### 8.2 yfinanceでのアジア株ティッカー形式

| 取引所 | サフィックス | 例 |
|--------|-----------|-----|
| 香港 | `.HK` | `0700.HK` (Tencent), `9988.HK` (Alibaba) |
| 中国 (上海) | `.SS` | `600519.SS` (貴州茅台) |
| 中国 (深圳) | `.SZ` | `000858.SZ` (五粮液) |
| 韓国 | `.KS` (KOSPI), `.KQ` (KOSDAQ) | `005930.KS` (Samsung), `035720.KQ` (Kakao) |
| 台湾 | `.TW` | `2330.TW` (TSMC), `2317.TW` (Foxconn) |
| シンガポール | `.SI` | `D05.SI` (DBS), `O39.SI` (OCBC) |
| インド (BSE) | `.BO` | `500325.BO` (Reliance) |
| インド (NSE) | `.NS` | `RELIANCE.NS` (Reliance) |
| タイ | `.BK` | `SCC.BK` (SCG), `PTT.BK` (PTT) |
| インドネシア | `.JK` | `BBCA.JK` (BCA), `TLKM.JK` (Telkom) |
| マレーシア | `.KL` | `1155.KL` (Maybank) |

### 8.3 拡張の可能性

以下の機能は新規開発により自動化が可能:

1. **韓国 DART API連携**: Open DART APIを使用した韓国企業の財務データ自動取得
2. **香港 HKEXnews スクレイピング**: 開示書類の自動取得・解析
3. **台湾 MOPS データ取得**: 月次売上高データの自動追跡
4. **アジアニュースRSSフィード統合**: 既存のRSSパッケージにアジアメディアを追加
5. **為替データ連携**: アジア通貨の為替データ自動取得・分析

---

## 9. 推奨リサーチワークフロー

### 9.1 日次ルーティン（15-30分）

```
1. アジア市場概況チェック
   └─ 主要指数: HSI, CSI300, KOSPI, TWSE, NIFTY50, STI
   └─ 為替: USD/CNY, USD/KRW, USD/TWD, USD/INR

2. ニュースチェック
   └─ Nikkei Asia / Reuters Asia / Bloomberg Asia
   └─ 保有銘柄の重要ニュースアラート

3. 開示チェック
   └─ 保有銘柄の新規開示書類
```

### 9.2 週次ルーティン（1-2時間）

```
1. セクターパフォーマンス分析
   └─ 国別・セクター別リターン比較

2. マクロデータ更新
   └─ 各国PMI, CPI, 貿易統計
   └─ 中央銀行の金融政策動向

3. ウォッチリスト更新
   └─ 新規候補の追加
   └─ 除外銘柄の判断
```

### 9.3 銘柄ディープダイブ（個別銘柄、2-4時間）

```
1. 年報精読（1-2時間）
   └─ MD&A, リスク要因, セグメント情報

2. 財務モデル構築（30-60分）
   └─ 過去5年の財務データ整理
   └─ 簡易バリュエーションモデル

3. 競合比較（30分）
   └─ 同業他社との定量比較
   └─ 地域別ポジショニング

4. リスク評価（30分）
   └─ ガバナンス、規制、為替、流動性
```

---

## 10. 参考リンク集

### 取引所・規制当局

| 名称 | URL |
|------|-----|
| HKEXnews | https://www.hkexnews.hk |
| CNINFO (巨潮資訊網) | https://www.cninfo.com.cn |
| DART (韓国電子公示) | https://dart.fss.or.kr |
| Open DART API | https://opendart.fss.or.kr |
| MOPS (台湾公開資訊) | https://mops.twse.com.tw |
| SGX | https://www.sgx.com |
| BSE India | https://www.bseindia.com |
| NSE India | https://www.nseindia.com |
| SET (タイ) | https://www.set.or.th |
| IDX (インドネシア) | https://www.idx.co.id |
| Bursa Malaysia | https://www.bursamalaysia.com |

### データ・分析

| 名称 | URL |
|------|-----|
| FRED | https://fred.stlouisfed.org |
| World Bank Open Data | https://data.worldbank.org |
| IMF Data | https://www.imf.org/en/Data |
| ADB Data Library | https://data.adb.org |
| Trading Economics | https://tradingeconomics.com |
| TIKR | https://tikr.com |

---

## Appendix A: インド通信セクター 詳細リサーチガイド

### A.1 セクター概要

インドの通信市場は世界第2位の加入者数（12億超）を持つ巨大市場。2016年のReliance Jioの参入を契機に価格破壊と業界再編が進み、現在は実質3社の寡占構造に収斂している。5G展開、固定ブロードバンド普及、デジタルインディア政策が成長ドライバー。

#### 主要プレイヤーとティッカー

| 企業 | ティッカー (NSE) | ティッカー (BSE) | 時価総額帯 | 特徴 |
|------|----------------|----------------|-----------|------|
| Reliance Jio (非上場) | - | - | - | Reliance Industries (RELIANCE.NS) の子会社。市場シェア首位 |
| Bharti Airtel | BHARTIARTL.NS | 532454.BO | Large Cap | 市場シェア2位。アフリカ事業も展開 |
| Vodafone Idea | IDEA.NS | 532822.BO | Mid Cap | 経営再建中。政府が株式転換で大株主化 |
| Indus Towers | INDUSTOWER.NS | 534816.BO | Large Cap | タワー会社。Airtel系列 |
| Tata Communications | TATACOMM.NS | 500483.BO | Mid Cap | エンタープライズ向け通信・デジタルインフラ |
| HFCL | HFCL.NS | 500183.BO | Mid Cap | 通信機器・光ファイバー製造 |
| Sterlite Technologies | STLTECH.NS | 532374.BO | Small Cap | 光ファイバー・ネットワーク設計 |
| Tejas Networks | TEJASNET.NS | 540595.BO | Mid Cap | 通信機器（Tata Group傘下） |
| Route Mobile | ROUTE.NS | 543228.BO | Mid Cap | CPaaS（クラウドコミュニケーション） |

> **注**: Reliance Jioは非上場だが、親会社Reliance Industries（RELIANCE.NS）の決算でJio Platformsのセグメント情報が開示される。Jio Financial Servicesは2023年に分社上場済（JIOFIN.NS）。

### A.2 規制当局・政府機関

| 機関 | 役割 | 公開データ | URL |
|------|------|----------|-----|
| **TRAI** (Telecom Regulatory Authority of India) | 通信規制当局。料金・品質・競争監督 | 加入者数、ARPU、QoSレポート、コンサルテーションペーパー | https://www.trai.gov.in |
| **DoT** (Department of Telecommunications) | 通信省。ライセンス・周波数割当 | ライセンス情報、周波数オークション結果、政策文書 | https://dot.gov.in |
| **WPC** (Wireless Planning & Coordination Wing) | 周波数管理 | 周波数割当状況 | DoT傘下 |
| **MeitY** (Ministry of Electronics & IT) | デジタルインディア政策 | デジタル経済統計、政策文書 | https://www.meity.gov.in |
| **CCI** (Competition Commission of India) | 競争法執行 | M&A審査、市場支配的地位の調査 | https://www.cci.gov.in |

#### TRAI 主要公開レポート（定期発行）

| レポート名 | 発行頻度 | 内容 | 重要度 |
|-----------|---------|------|--------|
| **Indian Telecom Services Performance Indicators** | 四半期 | 加入者数、ARPU、MoU、データ使用量の包括的統計 | ★★★★★ |
| **The Indian Telecom Services Performance Indicators** (Annual) | 年次 | 年間サマリー。長期トレンド分析に有用 | ★★★★★ |
| **Financial Data of Telecom Service Providers** | 年次 | 各社の売上・利益・投資額の比較 | ★★★★☆ |
| **Telecom Subscription Data** | 月次 | 月次加入者数（ワイヤレス/ワイヤライン/ブロードバンド） | ★★★★☆ |
| **QoS (Quality of Service) Reports** | 四半期 | 通話接続率、パケットロス、ダウンロード速度 | ★★★☆☆ |
| **Consultation Papers** | 不定期 | 新規制・料金改定等の事前協議。政策方向性の先行指標 | ★★★★★ |
| **Recommendations** | 不定期 | TRAIの政府への勧告。規制変更の直接的トリガー | ★★★★★ |

### A.3 セクター固有KPIと取得方法

| KPI | 定義 | データソース | 重要度 |
|-----|------|------------|--------|
| **加入者数** (Subscriber Base) | ワイヤレス/ブロードバンド/固定回線 | TRAI月次レポート、各社四半期決算 | ★★★★★ |
| **ARPU** (Average Revenue Per User) | ユーザーあたり月間売上 | 各社四半期決算 | ★★★★★ |
| **データ使用量** (Data per Sub per Month) | 1ユーザーあたり月間データ消費（GB） | TRAI四半期レポート、各社決算 | ★★★★☆ |
| **MoU** (Minutes of Usage) | 1ユーザーあたり月間通話時間 | TRAI四半期レポート | ★★★☆☆ |
| **チャーンレート** (Churn Rate) | 月次解約率 | 各社決算（一部非開示） | ★★★★☆ |
| **周波数保有** (Spectrum Holdings) | 帯域別保有量（MHz）と有効期限 | DoT、各社年報 | ★★★★★ |
| **4G/5G人口カバレッジ** | ネットワーク展開率 | 各社決算・投資家プレゼン | ★★★★☆ |
| **タワー数** | 保有/借用タワー数 | 各社決算、Indus Towers決算 | ★★★☆☆ |
| **CAPEX / Revenue比率** | 設備投資集約度 | 各社決算 | ★★★★☆ |
| **Net Debt / EBITDA** | レバレッジ指標 | 各社決算 | ★★★★★ |
| **AGR** (Adjusted Gross Revenue) | ライセンス料算定基準の売上 | 各社決算、DoT | ★★★★☆ |

### A.4 周波数（スペクトラム）分析

インド通信株のバリュエーションにおいて、周波数保有は極めて重要な要素。

#### 主要帯域と用途

| 帯域 | 周波数 | 用途 | 特徴 |
|------|--------|------|------|
| 700 MHz | 低帯域 | 5G（広域カバレッジ） | 建物内浸透性が高い。高額 |
| 800 MHz | 低帯域 | 4G LTE | CDMAからの転用 |
| 900 MHz | 低帯域 | 2G/4G | 最も歴史が長い帯域 |
| 1800 MHz | 中帯域 | 4G LTE | インドの4G主力帯域 |
| 2100 MHz | 中帯域 | 3G/4G | 3Gからの転用進行中 |
| 2300 MHz | 中帯域 | 4G TD-LTE | データ容量確保用 |
| 2500 MHz | 中帯域 | 4G/5G | 一部事業者のみ |
| 3300 MHz | 中帯域 | 5G（主力） | 5Gの中核帯域 |
| 26 GHz | ミリ波 | 5G（超高速） | 限定的エリアでの超高速通信 |

#### オークション結果の確認方法

- DoTウェブサイトの「Spectrum Auction」セクション
- 各社の年報・投資家プレゼンテーション内の周波数保有一覧
- TRAIの周波数関連コンサルテーションペーパー

### A.5 通信セクター固有の情報ソース

#### ニュース・業界メディア

| メディア | 特徴 | URL |
|---------|------|-----|
| **ETTelecom** (Economic Times) | インド通信専門。最も網羅的 | https://telecom.economictimes.indiatimes.com |
| **Tele.net (Voice&Data)** | 業界誌。技術・政策に強い | https://www.voicendata.com |
| **Medianama** | デジタル・通信政策分析 | https://www.medianama.com |
| **Light Reading (India)** | グローバル通信メディアのインド版 | https://www.lightreading.com |
| **TelecomTalk** | インド通信ニュース・レビュー | https://telecomtalk.info |
| **Telecom Lead** | アジア通信ニュース | https://www.telecomlead.com |
| **GSMA Intelligence** | グローバル通信データ・分析 | https://www.gsmaintelligence.com |
| **Analysys Mason** | 通信コンサルティング・リサーチ | https://www.analysysmason.com |

#### 業界団体・リサーチ機関

| 機関 | 役割 | 公開情報 |
|------|------|---------|
| **COAI** (Cellular Operators Association of India) | 民間通信事業者の業界団体 | 業界統計、政策提言、年次報告 |
| **GSMA** | グローバル移動体通信業界団体 | Mobile Economy India レポート（年次） |
| **ITU** (International Telecommunication Union) | 国連の通信機関 | 国際比較データ、ICT指標 |
| **ICRA / CRISIL / India Ratings** | インド格付機関 | セクターアウトルック、格付レポート |
| **NASSCOM** | ITサービス業界団体 | テレコム×IT融合トレンド |

#### 投資家プレゼンテーション取得先

| 企業 | IR URL | 四半期決算の特徴 |
|------|--------|-----------------|
| Bharti Airtel | https://www.airtel.in/about-bharti/equity/results | インド/アフリカセグメント別開示。ARPUトレンドが充実 |
| Vodafone Idea | https://www.myvi.in/about-us/investor-relations | AGR問題の進捗開示が重要 |
| Indus Towers | https://www.industowers.com/investors | テナント比率、コロケーション率の開示 |
| Reliance Industries | https://www.ril.com/investors | Jio Platformsセグメントとして開示 |

### A.6 通信セクター分析のチェックリスト

```
□ 加入者動向
  - 月次TRAI加入者データのトレンド
  - アクティブ加入者比率（名目 vs 実質）
  - ポートアウト（MNP）のネット流出入

□ 料金動向
  - 直近のタリフ改定（値上げ/値下げ）
  - TRAIのフロアプライス（最低料金）議論
  - 競合他社の料金プラン比較

□ 周波数
  - 各社の帯域別保有量
  - 周波数の有効期限と更新コスト
  - 次回オークションのスケジュールと予想価格

□ 規制リスク
  - AGR（Adjusted Gross Revenue）問題の進展
  - ライセンス料・SUC（Spectrum Usage Charge）の料率
  - TRAIコンサルテーションペーパーの方向性

□ 5G投資
  - CAPEX計画と進捗
  - 5Gカバレッジの拡大ペース
  - 5G収益化の進捗（B2B、FWA等）

□ 財務健全性
  - Net Debt / EBITDA
  - 周波数分割払い債務の残高とスケジュール
  - FCFの推移と配当余力
```

---

## Appendix B: インド不動産セクター 詳細リサーチガイド

### B.1 セクター概要

インドの不動産市場はGDPの約7-8%を占め、雇用の約15%を支える重要セクター。2016年のRERA（不動産規制法）施行を契機に業界の透明性が大幅に向上し、組織化が進行中。住宅、オフィス、リテール、物流/倉庫の4セグメントが主要カテゴリ。REIT（不動産投資信託）市場も2019年以降成長を続けている。

#### 主要プレイヤーとティッカー

**住宅デベロッパー（Residential）**

| 企業 | ティッカー (NSE) | ティッカー (BSE) | 主要都市 | 特徴 |
|------|----------------|----------------|---------|------|
| DLF | DLF.NS | 532868.BO | デリーNCR | 最大手。住宅+商業。DLF Cyber Cityを保有 |
| Godrej Properties | GODREJPROP.NS | 533150.BO | ムンバイ、バンガロール等 | Godrejグループ。ブランド力が強い |
| Macrotech Developers (Lodha) | LODHA.NS | 543287.BO | ムンバイ | ムンバイ最大手。ラグジュアリー+マスマーケット |
| Prestige Estates | PRESTIGE.NS | 543261.BO | バンガロール | 南インド最大手。住宅+商業+ホスピタリティ |
| Oberoi Realty | OBEROIRLTY.NS | 533273.BO | ムンバイ | 高級住宅特化。高マージン |
| Brigade Enterprises | BRIGADE.NS | 532929.BO | バンガロール | 南インド。住宅+オフィス+リテール |
| Sobha | SOBHA.NS | 532784.BO | バンガロール | 契約製造モデル。品質に定評 |
| Phoenix Mills | PHOENIXLTD.NS | 503100.BO | ムンバイ | モール運営（High Street Phoenix等） |

**REIT（不動産投資信託）**

| REIT | ティッカー (NSE) | 資産タイプ | スポンサー | 特徴 |
|------|----------------|----------|----------|------|
| Embassy Office Parks REIT | EMBASSY.NS | オフィス | Embassy Group + Blackstone | インド初のREIT。バンガロール中心 |
| Mindspace Business Parks REIT | MINDSPACE.NS | オフィス | K Raheja Corp + Blackstone | ハイデラバード、ムンバイ |
| Brookfield India Real Estate Trust | BIRET.NS | オフィス | Brookfield Asset Management | グルガオン、ノイダ中心 |
| Nexus Select Trust | NXST.NS | リテールモール | Blackstone | インド初のリテールREIT |

**不動産関連企業**

| 企業 | ティッカー | セグメント | 特徴 |
|------|----------|----------|------|
| Sunteck Realty | SUNTECK.NS | ラグジュアリー住宅 | ムンバイのBKC地区に強い |
| Mahindra Lifespace | MAHLIFE.NS | 住宅+工業団地 | Mahindraグループ。IC&IC（工業団地）事業 |
| Puravankara | PURVA.NS | 住宅 | バンガロール中心。Providentブランド（手頃価格帯） |
| Signature Global | SIGNATURE.NS | 手頃価格住宅 | デリーNCR。アフォーダブルハウジング |
| Raymond Realty | RAYMOND.NS 内 | 住宅 | テキスタイル大手Raymondの不動産部門 |

### B.2 規制当局・政府機関

| 機関 | 役割 | 公開データ | URL |
|------|------|----------|-----|
| **RERA** (Real Estate Regulatory Authority) | 不動産規制法に基づく各州の規制当局 | プロジェクト登録情報、デベロッパー情報、苦情 | 各州RERA（後述） |
| **RBI** (Reserve Bank of India) | 住宅ローン規制、不動産向け融資ガイドライン | 住宅ローン金利動向、不動産向け与信データ | https://www.rbi.org.in |
| **NHB** (National Housing Bank) | 住宅金融の監督機関 | **RESIDEX**（住宅価格指数）、HFC統計 | https://www.nhb.org.in |
| **MoHUA** (Ministry of Housing & Urban Affairs) | 住宅政策（PMAY等） | PMAY（住宅補助制度）進捗、都市開発統計 | https://mohua.gov.in |
| **SEBI** (Securities & Exchange Board of India) | REIT規制 | REIT規則、開示ガイドライン | https://www.sebi.gov.in |
| **CREDAI** (Confederation of Real Estate Developers' Associations of India) | デベロッパー業界団体 | 業界統計、市場レポート | https://credai.org |
| **NAREDCO** (National Real Estate Development Council) | 不動産開発評議会 | 政策提言、業界データ | https://www.naredco.in |

#### 主要州のRERAポータル

| 州 | RERAポータル | 特徴 |
|----|------------|------|
| **Maharashtra** (MahaRERA) | https://maharera.maharashtra.gov.in | 最も活発。ムンバイ・プネのプロジェクト。検索機能が充実 |
| **Karnataka** (K-RERA) | https://rera.karnataka.gov.in | バンガロールのプロジェクト |
| **Haryana** (H-RERA) | https://haryanarera.gov.in | グルガオンのプロジェクト |
| **UP** (UP-RERA) | https://www.up-rera.in | ノイダ・グレーターノイダのプロジェクト |
| **Tamil Nadu** (TN-RERA) | https://www.tnrera.in | チェンナイのプロジェクト |
| **Telangana** (TS-RERA) | https://rera.telangana.gov.in | ハイデラバードのプロジェクト |
| **Gujarat** (GujRERA) | https://gujrera.gujarat.gov.in | アーメダバードのプロジェクト |

> **RERAの活用法**: RERAポータルでは個別プロジェクトの登録状況、完了予定日、デベロッパーの過去実績を確認できる。投資判断の際、対象企業のプロジェクト進捗をクロスチェックする手段として有用。

### B.3 セクター固有KPIと取得方法

#### 住宅デベロッパーのKPI

| KPI | 定義 | データソース | 重要度 |
|-----|------|------------|--------|
| **Pre-sales (Bookings)** | 四半期の新規販売契約額（₹ Cr） | 各社四半期決算 | ★★★★★ |
| **Pre-sales Volume** | 販売面積（Mn sq ft） | 各社四半期決算 | ★★★★★ |
| **Collections** | 顧客からの代金回収額 | 各社四半期決算 | ★★★★★ |
| **Net Debt** | 純有利子負債 | 各社四半期決算 | ★★★★★ |
| **Net Debt / Equity** | レバレッジ指標 | 各社四半期決算 | ★★★★☆ |
| **Launch Pipeline** | 今後12-24ヶ月のプロジェクト発売計画 | 各社投資家プレゼン、ガイダンス | ★★★★★ |
| **Unsold Inventory** | 未販売在庫（面積・金額・月数） | 各社決算、JLL/Knight Frank | ★★★★☆ |
| **Average Realization** | 平均販売単価（₹/sq ft） | 各社四半期決算 | ★★★★☆ |
| **Completion Rate** | プロジェクト完了・引渡し面積 | 各社四半期決算 | ★★★☆☆ |
| **Land Bank** | 保有土地面積と開発可能GDV | 各社年報・投資家プレゼン | ★★★★★ |
| **GDV** (Gross Development Value) | ランドバンクの潜在開発総額 | 各社投資家プレゼン | ★★★★★ |
| **RERA登録数** | 各州RERAへの新規プロジェクト登録 | RERAポータル | ★★★☆☆ |

#### オフィス / REIT のKPI

| KPI | 定義 | データソース | 重要度 |
|-----|------|------------|--------|
| **Occupancy Rate** | 稼働率 | REIT四半期決算 | ★★★★★ |
| **Rent per sq ft per month** | 賃料単価 | REIT四半期決算 | ★★★★★ |
| **WALE** (Weighted Average Lease Expiry) | 加重平均リース残存期間 | REIT四半期決算 | ★★★★☆ |
| **NOI** (Net Operating Income) | 純営業利益 | REIT四半期決算 | ★★★★★ |
| **Distribution per Unit (DPU)** | ユニットあたり分配金 | REIT四半期決算 | ★★★★★ |
| **NAV per Unit** | ユニットあたり純資産価値 | REIT年次評価 | ★★★★★ |
| **Mark-to-Market Rent Spread** | 契約賃料 vs 市場賃料の乖離 | REIT四半期決算 | ★★★★☆ |
| **Net Absorption** | 純吸収面積（新規入居 - 退去） | JLL / CBRE / Knight Frank | ★★★★☆ |
| **New Completions** | 新規供給面積 | JLL / CBRE / Knight Frank | ★★★★☆ |
| **GCC** (Global Capability Center) 需要 | 多国籍企業のインド拠点需要 | NASSCOM、各REIT決算 | ★★★★☆ |

### B.4 不動産市場データプロバイダー

#### グローバル不動産コンサルティング

| 企業 | インドでの強み | 公開レポート | URL |
|------|-------------|------------|-----|
| **JLL India** | オフィス・住宅の最も包括的なデータ | 四半期マーケットレポート（都市別） | https://www.jll.co.in |
| **CBRE India** | オフィス・物流に強い | India Market Monitor（四半期） | https://www.cbre.co.in |
| **Knight Frank India** | 住宅・オフィス | India Real Estate Report（半期） | https://www.knightfrank.co.in |
| **Cushman & Wakefield India** | オフィス・リテール | マーケットビート（四半期） | https://www.cushmanwakefield.com/en/india |
| **Colliers India** | オフィス・物流 | マーケットレポート | https://www.colliers.com/en-in |
| **Savills India** | 高級住宅・オフィス | リサーチレポート | https://www.savills.co.in |
| **Anarock Property Consultants** | 住宅市場に特化。インド最大の独立系 | ANAROCK Research（非常に詳細） | https://www.anarock.com |

> **推奨**: JLL・Knight Frankの四半期レポートはPDF形式で無料公開されることが多い。ANAROCKは住宅市場の最も詳細な独立系データを提供。

#### オンライン不動産プラットフォーム（市場価格データ）

| プラットフォーム | 特徴 | データ活用 |
|----------------|------|----------|
| **99acres** (Info Edge) | インド最大の不動産ポータル | エリア別価格トレンド、需給データ |
| **MagicBricks** (Times Group) | 大手不動産ポータル | 価格指数、需要トレンド |
| **Housing.com** (REA Group) | PropTech。データ分析に強い | JEAP（住宅価格予測）、市場分析 |
| **Square Yards** | テック寄りの不動産プラットフォーム | プロジェクト比較、価格分析 |
| **PropTiger** (REA Group) | デベロッパー向けプラットフォーム | 一次取得者向けデータ、在庫分析 |
| **NoBroker** | P2P不動産プラットフォーム | 賃料のリアルタイムデータ |

### B.5 住宅価格指数

| 指数 | 発行機関 | 頻度 | 特徴 |
|------|---------|------|------|
| **NHB RESIDEX** | National Housing Bank | 四半期 | 公式住宅価格指数。50都市カバー。Assessment Price Index / Market Price Index の2種 |
| **RBI House Price Index** | Reserve Bank of India | 四半期 | RBI独自の住宅価格指数。10主要都市 |
| **Knight Frank KFAHI** | Knight Frank | 半期 | Affordability Index。購買力対比の住宅価格 |
| **JLL REIS** | JLL | 四半期 | 都市別の価格動向・在庫データ |

### B.6 不動産セクター固有の情報ソース

#### ニュース・業界メディア

| メディア | 特徴 | URL |
|---------|------|-----|
| **ET Realty** (Economic Times) | インド不動産専門。最も網羅的 | https://realty.economictimes.indiatimes.com |
| **Moneycontrol Real Estate** | 不動産市場ニュース・分析 | https://www.moneycontrol.com/real-estate/ |
| **Real Estate Developers** | 不動産開発ニュース | - |
| **Construction World** | 建設・インフラ業界誌 | https://www.constructionworld.in |
| **Track2Realty** | 不動産業界分析・ランキング | https://www.track2realty.track2media.com |
| **CRE Matrix** | 商業不動産データ分析 | https://www.crematrix.com |
| **Realty+ Magazine** | 不動産業界誌 | https://www.reaborede.com |
| **Indian Real Estate Forum** | 業界カンファレンス情報 | - |

#### 投資家プレゼンテーション取得先

| 企業 | IR URL | 決算の特徴 |
|------|--------|-----------|
| DLF | https://www.dlf.in/investors | DLF Cyber City（DCCDL）のリース収入が重要。住宅Pre-sales詳細 |
| Godrej Properties | https://www.godrejproperties.com/investors | 都市別Pre-sales内訳。ランドバンク追加の詳細 |
| Macrotech (Lodha) | https://www.lodhagroup.in/investors | ムンバイ市場の詳細。英国事業の進捗 |
| Prestige Estates | https://www.prestigeconstructions.com/investors | 住宅+オフィス+リテール+ホスピタリティの4セグメント |
| Embassy REIT | https://www.embassyofficeparks.com/investors | オフィス稼働率、賃料改定、GCC顧客動向 |
| Mindspace REIT | https://www.mindspacereit.com/investors | 都市別ポートフォリオ、WALE分析 |

### B.7 不動産セクター特有の規制・政策

#### 主要政策とインパクト

| 政策/制度 | 内容 | セクターへの影響 |
|----------|------|----------------|
| **RERA** (2016) | プロジェクト登録義務化、エスクロー口座、完了期限 | 透明性向上、零細デベロッパーの淘汰、大手に有利 |
| **GST** (2017) | 建設中物件: 5%（input tax credit無し）、完成物件: 免税 | 税制簡素化だが建設コスト構造に影響 |
| **PMAY** (Pradhan Mantri Awas Yojana) | 低所得者向け住宅補助（CLSS = Credit Linked Subsidy Scheme） | アフォーダブルハウジングの需要創出 |
| **FDI Policy** | 不動産開発: 100% FDI許可（条件付き）、完成物件: FDI禁止 | 外資の不動産開発参入ルール |
| **IBC** (Insolvency & Bankruptcy Code) | 不動産デベロッパーの倒産処理 | 住宅購入者を「金融債権者」として保護 |
| **Model Tenancy Act** (2021) | 賃貸市場の標準化 | 賃貸市場の組織化を促進 |
| **Capital Gains Tax** | 不動産売却益への課税（短期/長期） | 投資家の売買判断に影響 |
| **Stamp Duty** | 州ごとに異なる不動産取得税 | 購入コストに直結。減税措置がマーケット刺激策に |

#### 都市別の市場特性

| 都市 | 住宅市場の特徴 | オフィス市場の特徴 | 主要デベロッパー |
|------|--------------|------------------|----------------|
| **ムンバイ (MMR)** | 最大市場。高単価。再開発需要 | BKC、Lower Parel、Thane | Lodha, Oberoi, Godrej, Rustomjee |
| **デリーNCR** | グルガオン中心。供給過剰歴あり | サイバーシティ（DLF）、ノイダ | DLF, Signature Global, M3M |
| **バンガロール** | IT需要に強く連動。安定成長 | 最大のオフィス市場。GCC集積 | Prestige, Brigade, Sobha, Puravankara |
| **ハイデラバード** | 急成長市場。比較的手頃 | HITEC City中心。GCC需要旺盛 | My Home, Aparna, Ramky |
| **プネ** | IT・自動車産業。手頃な価格帯 | Hinjewadi IT Park中心 | Godrej, Kolte-Patil, VTP |
| **チェンナイ** | 安定的な需要。製造業も寄与 | OMR沿いにIT回廊 | Prestige, Casagrand, TVS Emerald |
| **コルカタ** | 比較的小規模。手頃な価格帯 | Rajarhat New Town中心 | PS Group, Merlin |

### B.8 不動産セクター分析のチェックリスト

```
□ 需給バランス
  - 都市別の在庫月数（Months of Inventory）
  - 新規発売（Launches） vs 販売（Absorption）比率
  - JLL / Knight Frank / ANAROCK の四半期レポート確認

□ 価格動向
  - NHB RESIDEX / RBI House Price Index のトレンド
  - エリア別マイクロマーケット価格
  - 手頃さ（Affordability）: 価格/年収比率

□ 住宅ローン環境
  - RBIのレポレート（現行金利）
  - 住宅ローン金利のトレンド
  - 住宅ローン残高の成長率（RBI統計）

□ デベロッパー分析
  - Pre-sales トレンド（最低4四半期）
  - Collections / Pre-sales 比率
  - Net Debt / Equity とレバレッジトレンド
  - ランドバンクの質（立地、取得コスト、開発タイムライン）
  - RERA登録状況とプロジェクト完了実績

□ オフィス/REIT分析
  - 稼働率トレンド
  - 新規供給パイプライン
  - GCC（Global Capability Center）需要動向
  - 賃料改定率（Mark-to-Market Spread）
  - Distribution Yield vs 10年国債利回り

□ 規制動向
  - RERA執行状況（州別の厳格さの違い）
  - Stamp Duty の優遇措置（州政府の景気刺激策）
  - GST変更の可能性
  - FDI Policy の変更
  - 都市計画・FSI（Floor Space Index）変更

□ マクロ要因
  - GDP成長率 → 不動産需要との相関
  - 都市化率の進展
  - 人口動態（ミレニアル世代の住宅需要）
  - IT/BPOセクターの成長 → オフィス需要
```

---

## Appendix C: インドセクター横断リファレンス

### C.1 インド市場共通のデータソース

| カテゴリ | ソース | 内容 | URL |
|---------|--------|------|-----|
| **企業開示** | BSE Listing Centre | 決算、取締役会決議、株主総会 | https://www.bseindia.com/corporates.html |
| **企業開示** | NSE Corporate Filings | 同上 | https://www.nseindia.com/companies-listing |
| **財務データ** | Screener.in | インド株の無料財務データ・スクリーニング | https://www.screener.in |
| **財務データ** | Trendlyne | 財務分析・スクリーニング・アラート | https://trendlyne.com |
| **財務データ** | Tijori Finance | 詳細な財務データ・セグメント分析 | https://tijorifinance.com |
| **格付** | CRISIL | インド最大の格付機関（S&Pグループ） | https://www.crisil.com |
| **格付** | ICRA | インド格付機関（Moody'sグループ） | https://www.icra.in |
| **格付** | India Ratings | インド格付機関（Fitchグループ） | https://www.indiaratings.co.in |
| **格付** | CARE Ratings | インド格付機関 | https://www.careratings.com |
| **インサイダー** | BSE/NSE SAST Disclosures | 大量保有・インサイダー取引 | 各取引所サイト |
| **MF/FII保有** | NSDL / CDSL | FPI（外国ポートフォリオ投資家）フロー | https://www.fpi.nsdl.co.in |
| **MF保有** | AMFI | 投資信託の月次ポートフォリオ開示 | https://www.amfiindia.com |

### C.2 インド株で特に有用な無料ツール

| ツール | 用途 | 特筆すべき機能 |
|--------|------|---------------|
| **Screener.in** | 財務分析・スクリーニング | 10年間の財務データ、カスタムスクリーナー、同業比較 |
| **Trendlyne** | アラート・分析 | バルクディール/ブロックディール通知、テクニカルスコア |
| **Tickertape** | スクリーニング・比較 | インド株に最適化されたUI、セクター比較 |
| **Moneycontrol** | 総合金融ポータル | ニュース、株価、決算、投信、IPO情報 |
| **Economic Times Markets** | 株価・ニュース | セクターヒートマップ、FII/DII統計 |
| **Investing.com India** | グローバル×インド | インド固有指標（Nifty先物、SGXNifty等） |

### C.3 インド固有のイベントカレンダー

通信・不動産セクターに影響する定期イベント:

| 時期 | イベント | 影響セクター | 注目点 |
|------|---------|------------|--------|
| **2月** | Union Budget（連邦予算案） | 全セクター | 住宅補助政策、通信投資計画、税制変更 |
| **4月** | RBI金融政策（年度初回） | 不動産（住宅ローン金利） | レポレートの方向性 |
| **4-6月** | 四半期決算（Q4 = 年度末） | 全セクター | 通年ガイダンス、配当宣言 |
| **7-9月** | 周波数オークション（不定期） | 通信 | 落札価格、各社の戦略 |
| **8-9月** | TRAI年次レポート | 通信 | 年間業界データの包括的レビュー |
| **10月** | 祝祭シーズン（Diwali前後） | 不動産 | 住宅販売のピーク。Pre-sales急増 |
| **通年** | RBI金融政策（隔月） | 不動産 | レポレート変更 → 住宅ローン金利 |
| **通年** | TRAI四半期レポート | 通信 | 加入者数・ARPU・QoSデータ |

---

*作成日: 2026-02-10*
*最終更新: 2026-02-10*
