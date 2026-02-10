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

## Appendix D: インドネシア市場 詳細リサーチガイド

### D.1 セクター概要

インドネシアはASEAN最大の経済規模（GDP約1.3兆ドル、2024年）と人口（約2.8億人）を持つ新興市場。IDX（Indonesia Stock Exchange）の時価総額は約9,400億ドル（2025年12月時点）に達し、ASEAN最大の株式市場となっている。2026年にはJCI（Jakarta Composite Index）が9,250に到達する見通しもある。

#### 主要セクターの概況

| セクター | GDP比/市場での位置づけ | 主な成長ドライバー |
|----------|----------------------|-------------------|
| **銀行** | IDX時価総額の約30%。4大銀行が中核 | 金融包摂（banked人口拡大）、デジタルバンキング、MSME向け融資拡大 |
| **通信** | 加入者数3.6億（世界4位）。3社寡占 | 5G展開、データ消費量増加、ブロードバンド普及、業界再編 |
| **消費財** | GDP約55%が個人消費。巨大な内需市場 | 人口増加、中間層拡大、都市化率上昇（現在57%→2030年に66%予測） |
| **資源/コモディティ** | 世界最大のニッケル生産国、石炭輸出大国 | ニッケルダウンストリーミング政策、EV向けバッテリー需要、石炭→再生エネ転換 |
| **不動産** | 都市化と住宅需要が牽引 | 新首都ヌサンタラ（IKN）建設、インフラ整備、住宅ローン普及 |
| **インフラ** | 政府の大規模インフラ投資 | 有料道路拡張、港湾・鉄道整備、電力インフラ拡充 |

#### IDXセクター指数一覧

| セクター指数 | コード | 対象 |
|-------------|--------|------|
| エネルギー | IDXENERGY | 石炭、石油ガス、再生エネ |
| 素材 | IDXBASIC | 化学、金属、鉱業 |
| 工業 | IDXINDUST | 製造業、自動車 |
| 一次消費財 | IDXNONCYC | 食品、飲料、生活必需品 |
| 二次消費財 | IDXCYCLIC | 小売、メディア、耐久消費財 |
| ヘルスケア | IDXHEALTH | 病院、製薬 |
| 金融 | IDXFINANCE | 銀行、保険、証券 |
| 不動産 | IDXPROPERT | 不動産開発、REIT |
| テクノロジー | IDXTECHNO | IT、フィンテック |
| インフラ | IDXINFRA | 通信、電力、有料道路 |
| 運輸・物流 | IDXTRANS | 海運、航空、物流 |

---

### D.2 主要プレイヤーとティッカー

#### 銀行セクター

| 企業 | ティッカー | 時価総額帯 | 特徴 |
|------|----------|-----------|------|
| Bank Central Asia (BCA) | BBCA.JK | Mega Cap (IDR 1,000兆超) | 民間最大手。CASA比率最高水準。ROE 24%。プレミアムバリュエーション |
| Bank Rakyat Indonesia (BRI) | BBRI.JK | Mega Cap (IDR 500-600兆) | 国有最大手。マイクロ・MSME融資に強い。国内最大の支店網 |
| Bank Mandiri | BMRI.JK | Large Cap (IDR 400-500兆) | 国有。法人・リテール両方。NIM 4.8%。ROE 18% |
| Bank Negara Indonesia (BNI) | BBNI.JK | Large Cap (IDR 150-200兆) | 国有。法人融資と海外ネットワーク。NIM 3.8% |
| Bank Syariah Indonesia (BSI) | BRIS.JK | Mid Cap | イスラム銀行最大手。3行統合（2021年） |
| Bank CIMB Niaga | BNGA.JK | Mid Cap | マレーシアCIMBグループ傘下。デュアルバンキング |
| Bank Danamon | BDMN.JK | Mid Cap | 三菱UFJ傘下。日系企業取引に強い |
| Bank Tabungan Negara (BTN) | BBTN.JK | Mid Cap | 国有。住宅ローン特化 |
| Bank Permata | BNLI.JK | Mid Cap | バンコクBank傘下 |
| Bank OCBC NISP | NISP.JK | Mid Cap | シンガポールOCBC傘下 |

#### 通信セクター

| 企業 | ティッカー | 時価総額帯 | 特徴 |
|------|----------|-----------|------|
| Telkom Indonesia | TLKM.JK | Mega Cap (IDR 300-400兆) | 国有最大手。Telkomsel（モバイル）、IndiHome（固定BB）。加入者シェア45% |
| Indosat Ooredoo Hutchison (IOH) | ISAT.JK | Large Cap | Ooredoo + CK Hutchison統合（2022年）。加入者9,500万、ARPU IDR 40,000 |
| XL Axiata | EXCL.JK | Mid Cap | マレーシアAxiata傘下。Smartfrenと統合（XL Smart）。加入者9,500万 |
| Smartfren Telecom | FREN.JK | Mid Cap | Sinar Masグループ。XL Axiataと統合 |
| Sarana Menara Nusantara | TOWR.JK | Large Cap | 通信タワー運営最大手。タワー数3万超 |
| Mitratel (Dayamitra Telekomunikasi) | MTEL.JK | Large Cap | Telkom傘下の通信タワー会社 |

#### 消費財セクター

| 企業 | ティッカー | 時価総額帯 | 特徴 |
|------|----------|-----------|------|
| Unilever Indonesia | UNVR.JK | Large Cap | 英蘭Unilever子会社。家庭用品・パーソナルケア。ブランド力圧倒的 |
| Indofood CBP Sukses Makmur | ICBP.JK | Large Cap | Salimグループ。即席麺（Indomie）、乳製品。海外展開加速 |
| Indofood Sukses Makmur | INDF.JK | Large Cap | Salimグループ。ICBPの親会社。小麦製粉、パーム油、流通 |
| Gudang Garam | GGRM.JK | Mid-Large Cap | クレテック（丁子入り）たばこ最大手 |
| HM Sampoerna | HMSP.JK | Large Cap | Philip Morris傘下。たばこ第2位 |
| Mayora Indah | MYOR.JK | Mid Cap | 菓子・飲料。Kopiko、Torabika等 |
| Kalbe Farma | KLBF.JK | Large Cap | 製薬・消費者ヘルスケア最大手 |
| Charoen Pokphand Indonesia | CPIN.JK | Large Cap | タイCPグループ傘下。飼料・鶏肉加工 |

#### 資源/コモディティセクター

| 企業 | ティッカー | 時価総額帯 | 特徴 |
|------|----------|-----------|------|
| Barito Renewables Energy | BREN.JK | Mega Cap (IDR 800兆+) | 再生可能エネルギー。地熱発電。IDX時価総額1位（2025年） |
| Bayan Resources | BYAN.JK | Mega Cap (IDR 660兆+) | 石炭採掘。低灰分・低硫黄炭 |
| Chandra Asri Pacific | TPIA.JK | Mega Cap (IDR 600兆+) | 石油化学。エチレン生産 |
| Adaro Energy Indonesia | ADRO.JK | Large Cap | 石炭最大手の一つ。アルミ精錬所建設中。グリーン転換推進 |
| Adaro Minerals Indonesia | ADMR.JK | Large Cap | Adaro傘下。冶金炭、アルミナ |
| Vale Indonesia | INCO.JK | Mid-Large Cap | ブラジルVale傘下。ニッケル採掘・精錬（スラウェシ） |
| Merdeka Copper Gold | MDKA.JK | Mid-Large Cap | 金・銅・ニッケル。多角化鉱山会社 |
| Merdeka Battery Materials | MBMA.JK | Large Cap | Merdeka傘下。ニッケルHPAL、EV向けバッテリー素材 |
| Aneka Tambang (Antam) | ANTM.JK | Mid Cap | 国有。金、ニッケル、ボーキサイト |
| Bukit Asam | PTBA.JK | Mid Cap | 国有石炭会社。スマトラ中心 |
| Bumi Resources | BUMI.JK | Mid Cap | Bakrieグループ。石炭。過去に大規模債務再編 |
| Harum Energy | HRUM.JK | Mid Cap | 石炭採掘。ニッケル事業に多角化中 |

#### 不動産セクター

| 企業 | ティッカー | 時価総額帯 | 特徴 |
|------|----------|-----------|------|
| Bumi Serpong Damai (BSD) | BSDE.JK | Large Cap | Sinar Masグループ。BSD City開発。住宅・商業・工業一体開発 |
| Ciputra Development | CTRA.JK | Mid-Large Cap | Ciputraグループ。全国展開。住宅・商業・ホスピタリティ |
| Pakuwon Jati | PWON.JK | Mid Cap | スラバヤ中心。モール運営+住宅開発。リカーリング収入比率高 |
| Lippo Karawaci | LPKR.JK | Mid Cap | Lippoグループ。病院（Siloam）、モール、住宅 |
| Summarecon Agung | SMRA.JK | Mid Cap | 都市開発（Summarecon Kelapa Gading等） |
| Alam Sutera Realty | ASRI.JK | Small-Mid Cap | Alam Sutera, Serpong地区開発 |
| Puradelta Lestari | DMAS.JK | Mid Cap | Sinar Masグループ。工業団地開発 |
| Pantai Indah Kapuk (PIK) 2 | PANI.JK | Large Cap | Agungグループ。PIK2大規模開発 |

#### インフラセクター

| 企業 | ティッカー | 時価総額帯 | 特徴 |
|------|----------|-----------|------|
| Astra International | ASII.JK | Large Cap (IDR 200兆) | 最大コングロマリット。自動車（トヨタ）、金融、インフラ、鉱業 |
| Jasa Marga | JSMR.JK | Mid Cap | 国有。有料道路運営最大手。インドネシアの有料道路の約75%を運営 |
| Waskita Karya | WSKT.JK | Small Cap | 国有建設。高速道路建設に強い |
| Wijaya Karya (WIKA) | WIKA.JK | Small Cap | 国有建設。ジャカルタ-バンドン高速鉄道 |
| PP (Pembangunan Perumahan) | PTPP.JK | Small Cap | 国有建設。インフラ・住宅 |
| Perusahaan Gas Negara | PGAS.JK | Mid Cap | 国有。天然ガス配送 |
| PLN (非上場) | - | - | 国有電力会社。インドネシア唯一の送配電事業者 |

---

### D.3 規制当局・政府機関

| 機関 | 役割 | 公開データ | URL |
|------|------|----------|-----|
| **OJK** (Otoritas Jasa Keuangan / 金融サービス庁) | 資本市場・銀行・ノンバンク金融の統合規制当局。2012年設立。開示規制（OJK Reg 45/2024で強化） | 企業開示書類、規制文書、金融統計、ファンド情報 | https://www.ojk.go.id |
| **IDX** (Indonesia Stock Exchange / Bursa Efek Indonesia) | 株式取引所運営。上場審査、売買監視、リサーチレポート公開 | 上場企業データ、財務諸表、セクター指数、統計レポート、アナリストレポート | https://www.idx.co.id |
| **Bank Indonesia** (BI / インドネシア銀行) | 中央銀行。金融政策、為替安定、決済システム | BI-Rate、外貨準備高、国際収支、為替データ、マクロ統計 | https://www.bi.go.id |
| **BPS** (Badan Pusat Statistik / 中央統計局) | 国家統計機関 | GDP、インフレ率、失業率、貿易統計、人口統計、エネルギー統計 | https://www.bps.go.id |
| **Kementerian ESDM** (エネルギー鉱物資源省) | エネルギー・鉱業の監督規制 | 鉱業生産データ、エネルギー統計ハンドブック（HEESI）、石炭基準価格（HBA） | https://www.esdm.go.id |
| **Kementerian Keuangan** (財務省) | 財政政策、国債管理 | 国家予算、国債データ、税制情報 | https://www.kemenkeu.go.id |
| **BKPM / DPMPTSP** (投資調整庁) | 外国直接投資の規制・促進。ネガティブリスト/ポジティブリスト管理 | FDI統計、投資規制リスト、ライセンス情報 | https://www.bkpm.go.id |
| **KPPU** (事業競争監視委員会) | 独禁法執行、M&A審査 | 競争政策文書、審査結果 | https://www.kppu.go.id |
| **LPS** (預金保険機構) | 銀行預金保険、銀行破綻処理 | 保証預金金利上限 | https://www.lps.go.id |

#### OJK主要規制

| 規制 | 内容 | 投資家への影響 |
|------|------|--------------|
| OJK Reg 45/2024 | 発行体・公開会社の規制強化 | コーポレートガバナンス向上、投資家保護強化 |
| OJK Reg 4/2024 | 株式保有・変動報告義務 | インサイダー取引監視強化 |
| 重要情報即時開示義務 | 材料情報の即時開示（従来は2営業日以内→即時に変更） | 情報の即時性向上 |

---

### D.4 セクター固有KPIと取得方法

#### 銀行セクター

| KPI | 定義 | データソース | 重要度 |
|-----|------|------------|--------|
| **NIM** (Net Interest Margin) | 純金利マージン。BCA 5.5%、Mandiri 4.8%、BNI 3.8%（2025年） | 各行四半期決算、OJK銀行統計 | ★★★★★ |
| **NPL Ratio** (Non-Performing Loan) | 不良債権比率。Mandiri 1.24%、BCA 2.1%、BRI 2.94% | 各行四半期決算、OJK銀行統計 | ★★★★★ |
| **LDR** (Loan to Deposit Ratio) | 預貸率。BI規制上限92% | 各行四半期決算 | ★★★★☆ |
| **CASA Ratio** | 当座・普通預金比率。低コスト資金調達能力を示す。BCAが業界最高水準（80%超） | 各行四半期決算 | ★★★★★ |
| **CAR** (Capital Adequacy Ratio) | 自己資本比率。規制最低8% | 各行四半期決算、OJK | ★★★★☆ |
| **ROE** (Return on Equity) | 株主資本利益率。BCA 24%、Mandiri 18%、BNI 15% | 各行四半期決算 | ★★★★★ |
| **Cost of Credit** (CoC) | 貸倒引当金繰入率 | 各行四半期決算 | ★★★★☆ |
| **CIR** (Cost to Income Ratio) | 経費率。効率性指標 | 各行四半期決算 | ★★★★☆ |
| **MSME Loan Ratio** | 中小零細企業向け融資比率（規制上の義務あり） | 各行四半期決算 | ★★★☆☆ |

#### 通信セクター

| KPI | 定義 | データソース | 重要度 |
|-----|------|------------|--------|
| **加入者数** (Subscriber Base) | ワイヤレス/ブロードバンド。Telkomsel 1.7億、IOH 9,500万、XL Smart 9,500万 | 各社四半期決算 | ★★★★★ |
| **ARPU** (Average Revenue Per User) | ユーザーあたり月間売上。業界平均 IDR 35,000-45,000 (USD 2.3-3.0) | 各社四半期決算 | ★★★★★ |
| **データ使用量** (Data/Sub/Month) | 1ユーザーあたり月間データ消費（GB） | 各社四半期決算 | ★★★★☆ |
| **チャーンレート** (Churn Rate) | 月次解約率 | 各社四半期決算 | ★★★★☆ |
| **タワー数** (Tower Count) | 保有/借用タワー数。TOWR 3万超、MTEL 3.6万超 | 各社決算、タワー会社決算 | ★★★☆☆ |
| **4G/5G人口カバレッジ** | ネットワーク展開率 | 各社決算・投資家プレゼン | ★★★★☆ |
| **CAPEX / Revenue比率** | 設備投資集約度 | 各社決算 | ★★★★☆ |
| **Net Debt / EBITDA** | レバレッジ指標 | 各社決算 | ★★★★★ |

#### 消費財セクター

| KPI | 定義 | データソース | 重要度 |
|-----|------|------------|--------|
| **Revenue Growth** | 売上成長率（オーガニック/M&A区分） | 各社四半期決算 | ★★★★★ |
| **Gross Margin** | 粗利率。原材料コスト変動の影響 | 各社四半期決算 | ★★★★★ |
| **Operating Margin** | 営業利益率。広告宣伝費の影響 | 各社四半期決算 | ★★★★☆ |
| **Distribution Reach** | 流通チャネル数、販売店数 | 各社年報、投資家プレゼン | ★★★★☆ |
| **Volume Growth** | 数量ベース成長率（価格効果と区別） | 各社決算 | ★★★★☆ |
| **Market Share** | カテゴリ別シェア（Nielsen等） | 各社投資家プレゼン、業界レポート | ★★★★★ |
| **ASP** (Average Selling Price) | 平均販売単価の推移 | 各社決算 | ★★★☆☆ |

#### 資源/コモディティセクター

| KPI | 定義 | データソース | 重要度 |
|-----|------|------------|--------|
| **Production Volume** | 石炭: 百万トン、ニッケル: 千トン | 各社四半期決算、ESDM | ★★★★★ |
| **ASP** (Average Selling Price) | 平均販売価格。石炭基準価格（HBA）との比較 | 各社四半期決算、ESDM月次HBA | ★★★★★ |
| **Cash Cost** | トンあたり現金コスト。ストリップ比率の影響 | 各社四半期決算 | ★★★★★ |
| **Stripping Ratio** | 石炭の剥土比率（表土:石炭）。コストに直結 | 各社四半期決算 | ★★★★☆ |
| **Reserves & Resources** | 埋蔵量と鉱量資源量。JORC規格 | 各社年報 | ★★★★☆ |
| **Overburden Removal** | 表土除去量 | 各社四半期決算 | ★★★☆☆ |
| **HBA** (Harga Batubara Acuan) | インドネシア石炭基準価格。ESDM月次発表 | ESDM公式サイト | ★★★★★ |
| **DMO** (Domestic Market Obligation) | 国内供給義務（生産量の25%） | ESDM | ★★★★☆ |
| **ニッケル含有量/品位** | 鉱石品位 | 各社年報 | ★★★★☆ |

#### 不動産セクター

| KPI | 定義 | データソース | 重要度 |
|-----|------|------------|--------|
| **Marketing Sales** (Pre-sales) | 四半期の新規販売契約額 | 各社四半期決算 | ★★★★★ |
| **Revenue Recognition** | 引渡し/完工ベースの売上計上 | 各社四半期決算 | ★★★★☆ |
| **Recurring Income Ratio** | リカーリング収入比率（モール・オフィス賃料等） | 各社四半期決算 | ★★★★★ |
| **Land Bank** | 保有土地面積（ヘクタール） | 各社年報 | ★★★★☆ |
| **Net Debt / Equity** | レバレッジ指標 | 各社四半期決算 | ★★★★★ |
| **Occupancy Rate** | モール・オフィスの稼働率 | 各社四半期決算 | ★★★★☆ |
| **ASP per sqm** | 平方メートルあたり平均販売単価 | 各社決算 | ★★★☆☆ |

---

### D.5 情報ソース

#### ニュース・メディア

| メディア | 言語 | 特徴 | URL |
|---------|------|------|-----|
| **Kontan** | インドネシア語 | 最も詳細な金融・投資ニュース。個別銘柄分析が充実 | https://www.kontan.co.id |
| **Bisnis Indonesia** | インドネシア語 | 老舗ビジネス紙。業界動向に強い | https://www.bisnis.com |
| **Jakarta Globe** | 英語 | インドネシアのビジネス・経済を英語で報道 | https://jakartaglobe.id |
| **Jakarta Post** | 英語 | 英語の総合紙。政治・経済全般 | https://www.thejakartapost.com |
| **CNBC Indonesia** | インドネシア語 | 市場動向・投資ニュース。動画コンテンツ充実 | https://www.cnbcindonesia.com |
| **IDN Financials** | 英語 | IDX上場企業の財務データ・ニュース。英語でアクセス可能 | https://www.idnfinancials.com |
| **Detik Finance** | インドネシア語 | 速報性の高い経済ニュース | https://finance.detik.com |
| **Kompas** | インドネシア語 | インドネシア最大手メディア。政治・経済全般 | https://www.kompas.com |
| **Tempo** | インドネシア語/英語 | 調査報道に定評。英語版あり | https://en.tempo.co |
| **Investor Daily** | インドネシア語 | 投資家向け専門紙 | https://investor.id |
| **Sectors.app** | 英語 | IDX上場企業の財務データAPI。セクター分析、カレンダー | https://sectors.app |

#### 業界レポート・リサーチ（現地証券会社）

| 証券会社 | 特徴 | リサーチアクセス |
|---------|------|----------------|
| **Mandiri Sekuritas** | 国有系。フルカバレッジ。マクロ分析に強い | 口座開設でアクセス |
| **BCA Sekuritas** | BCA傘下。銀行・消費財に強い | 口座開設でアクセス |
| **Mirae Asset Sekuritas Indonesia** | 韓国系。テック・バリュー分析 | 口座開設でアクセス (https://miraeasset.co.id) |
| **BNI Sekuritas** | 国有系。中大型株中心 | 口座開設でアクセス |
| **CGS International (旧CGS-CIMB)** | マレーシア系。ASEAN横断分析 | 口座開設でアクセス |
| **Verdhana Research (旧Credit Suisse Indonesia)** | 独立系。コングロマリット分析に定評 | https://verdhanaresearch.com |
| **Bahana Sekuritas** | 国有系。IPOアドバイザリーに強い | 口座開設でアクセス |
| **Macquarie Sekuritas Indonesia** | 外資系。セクター横断分析 | 口座開設でアクセス |
| **JP Morgan Indonesia** | 外資系。グローバル投資家向け | 機関投資家向け |
| **Morgan Stanley Indonesia** | 外資系。戦略・マクロ分析 | 機関投資家向け |

#### 独立系リサーチ・グローバル

| ソース | 特徴 |
|--------|------|
| **IDX Equity Research Reports** | IDX公式サイトでアナリストレポートを公開 (https://www.idx.co.id/en/listed-companies/equity-research-report/) |
| **Smartkarma** | アジア特化独立系プラットフォーム。インドネシア銘柄も豊富 |
| **Seeking Alpha** | ユーザー投稿型。大型株の英語分析あり |
| **Simply Wall St** | IDX銘柄の財務可視化 (https://simplywall.st/markets/id) |

#### 投資家プレゼンテーション取得先

| 企業 | IR URL | 決算の特徴 |
|------|--------|-----------|
| BCA (BBCA) | https://www.bca.co.id/en/tentang-bca/Hubungan-Investor | CASA比率の推移、NIMの安定性、デジタルバンキング指標が充実 |
| BRI (BBRI) | https://www.ir-bri.com/ar.html | マイクロ/MSME融資の詳細、CoC推移、デジタル化進捗 |
| Bank Mandiri (BMRI) | https://www.bankmandiri.co.id/en/web/ir | セグメント別（リテール/法人/トレジャリー）開示が詳細 |
| BNI (BBNI) | https://www.bni.co.id/en-us/company/investorrelation | 海外拠点別実績、法人融資ポートフォリオ分析 |
| Telkom (TLKM) | https://www.telkom.co.id/sites/about-telkom/en_US/investor-relation | Telkomsel/IndiHome/データセンター別セグメント。加入者詳細 |
| Astra International (ASII) | https://www.astra.co.id/Investor-Relations | 自動車/金融/鉱業/インフラ等の多セグメント開示。トヨタ販売台数データ |
| Adaro Energy (ADRO) | https://www.adaro.com/pages/read/11/25/Investor-Relations | 石炭販売量・ASP・キャッシュコスト推移。グリーン転換計画 |

---

### D.6 インドネシア固有の注意点

#### 外国人投資制限（ネガティブリスト / ポジティブインベストメントリスト）

2021年のオムニバス法（雇用創出法）施行以降、インドネシアはネガティブリスト（DNI）からポジティブインベストメントリスト（PIL）へ移行。規制対象業種を100から6に大幅削減。

**基本原則**: 特段の制限がない業種は外国人100%出資が可能

| カテゴリ | 内容 |
|---------|------|
| **投資禁止（6業種）** | 麻薬関連、CITES附属書I記載種の漁業、化学兵器関連等 |
| **政府限定** | 武器・弾薬製造等 |
| **協同組合・MSME限定** | 一部小規模事業 |
| **外資制限あり** | セクター別に上限設定（通信、メディア、物流等） |
| **条件付き開放** | 特定条件（パートナーシップ義務等）で外資参入可能 |

**株式市場での外国人保有**:
- IDX上場株の外国人保有は原則自由（直接投資のFDI制限とは別）
- ただし一部セクター（銀行は40%制限あり等）で個別制限が存在
- 外国人投資家はIDX時価総額の約40-70%（フリーフロートベース）を保有

**最低投資額**: 2025年にBKPM Regulation No.5により外資系企業の最低払込資本がIDR 100億からIDR 25億に引き下げ

#### 鉱業法（ダウンストリーム義務化）

| 政策 | 内容 | 影響 |
|------|------|------|
| **ニッケル鉱石輸出禁止** (2020年~) | 未加工ニッケル鉱石の輸出を全面禁止 | 国内精錬・加工産業の急成長。輸出額$1B→$20Bに急増 |
| **鉱業法改正** (Law No.2/2025) | 国内加工施設建設企業への優遇。VAT免税、輸出関税免除、法人税優遇 | 外資の精錬所建設投資を促進 |
| **DMO** (国内市場義務) | 石炭生産量の25%を国内供給義務（電力用、割引価格） | 石炭企業の利益率に影響 |
| **IUP/IUPK制度** | 採掘許可制度。期限付き。更新時に追加条件 | 許可更新リスク |

**市場への影響**: インドネシアは世界のニッケル生産の約62%を占め（2025年）、2026年には70%に達する見通し。中国企業の精錬所投資が活発。

#### 会計基準（SAK / IFRS収斂状況）

| 項目 | 内容 |
|------|------|
| **基準名** | SAK (Standar Akuntansi Keuangan) / PSAK (Pernyataan SAK) |
| **IFRS収斂** | 2015年1月1日付で実質的にIFRSに収斂完了 |
| **4つの柱** | Pillar 1: 国際SAK（IFRS完全採用）、Pillar 2: インドネシアSAK（IFRS収斂+ローカル調整）、Pillar 3: ETAP（中小企業向け簡易基準）、Pillar 4: EMKM（零細企業向け） |
| **設定機関** | DSAK IAI（インドネシア会計士協会の財務会計基準委員会） |
| **IFRSとの差異** | 一部のIFRS基準が未採用（インドネシアの状況に不適合なもの）。連結・金融商品・収益認識で軽微な差異あり |
| **監査** | Big 4全社がインドネシアに拠点。大型株はBig 4監査が一般的 |

#### ガバナンス特徴

**コングロマリット構造**

インドネシアの上場企業の多くは家族経営のコングロマリットグループに属している。

| グループ | 創業家 | 主な上場企業 | 注意点 |
|---------|--------|------------|--------|
| **Salim Group** | Anthoni Salim | INDF, ICBP, MPPA | 食品を中心にインドネシア最大級。創業者は華人系 |
| **Sinar Mas Group** | Widjaja家 | BSDE, DMAS, FREN, SMBR | 不動産、製紙（APP）、パーム油。6人の子息が分割管理 |
| **Astra Group** | Jardine Matheson | ASII, UNTR, AALI | 香港系Jardineが実質支配。最も透明性が高い |
| **Lippo Group** | Mochtar Riady家 | LPKR, MLPL, LPPF | 不動産、病院、リテール。関連当事者取引に要注意 |
| **Djarum Group** | Hartono家 | BBCA (17%保有) | たばこが祖業。BCA株保有が最大の資産 |
| **Bakrie Group** | Bakrie家 | BUMI, ELTY | 政治と結びつきが強い。過去に深刻なガバナンス問題 |
| **CT Corp** | Chairul Tanjung | BNBR, MEGA, BHIT | メディア（Trans TV）、金融、リテール |

**国有企業（BUMN）の役割**

インドネシア経済において国有企業（Badan Usaha Milik Negara = BUMN）は極めて重要な存在。

| 上場BUMN | セクター | 特徴 |
|----------|--------|------|
| BRI (BBRI) | 銀行 | マイクロ融資最大手 |
| Bank Mandiri (BMRI) | 銀行 | 資産規模最大 |
| BNI (BBNI) | 銀行 | 法人・海外 |
| Telkom (TLKM) | 通信 | 通信インフラ独占的地位 |
| Jasa Marga (JSMR) | インフラ | 有料道路75% |
| Antam (ANTM) | 鉱業 | 金・ニッケル |
| Bukit Asam (PTBA) | 鉱業 | 石炭 |
| PGN (PGAS) | エネルギー | 天然ガス配送 |

**BUMN投資の注意点**:
- 政府が過半数株主のため、政策目的（社会的義務、インフラ投資等）が利益最大化に優先される場合がある
- 政権交代時に経営陣が変更されるリスク
- 他のBUMN間での非経済的取引が発生する可能性

#### 通貨リスク（IDR）

| 項目 | 内容 |
|------|------|
| **為替レート** | USD/IDR 16,400-16,800（2025年7月時点）。アジア通貨で最もパフォーマンスが悪い |
| **変動要因** | 米ドル金利差、経常収支、FPI（外国ポートフォリオ投資）フロー、コモディティ価格 |
| **BI政策** | BI-Rate 4.75%（2025年11月）。為替防衛のためスポット市場・DNDF市場で介入 |
| **インフレ** | 2025年6月に5.2%（目標レンジ2-4%を超過）。金融政策の制約要因 |
| **見通し** | 2026年末にUSD/IDR 16,700前後に安定する予測 |
| **ヘッジ** | DNDF（Domestic Non-Deliverable Forward）市場が存在。NDF市場も利用可能 |

**IDR投資の実務的影響**:
- インドネシア株のリターンは「株価リターン + IDRのドル建て変動」の合成
- 石炭・パーム油等のコモディティ輸出企業はIDR安が追い風（ドル建て収入）
- 銀行・通信・消費財等の内需企業はIDR安の直接的な影響は限定的
- 但し、輸入コスト（原材料、設備投資）上昇のインフレ波及効果に注意

#### 流動性の課題

| 項目 | 内容 |
|------|------|
| **フリーフロート規制** | 従来は7.5%と低水準。2022年以降段階的に引き上げ（時価総額別: 15-25%） |
| **上位集中** | 時価総額上位50社がIDX全体の75%を占める |
| **小型株リスク** | 日次売買代金が極めて少ない銘柄が多数。ビッド・アスクスプレッドが広い |
| **外国人投資家の影響** | フリーフロートベースで40-70%を保有。資金流出入が市場ボラティリティに直結 |
| **MSCI問題** | 2025年のMSCI見直しでインドネシアのウェイト低下。OJK・IDXが対策強化中 |

**実務上の目安**:
- 時価総額 IDR 50兆以上: 流動性問題なし
- 時価総額 IDR 10-50兆: 大口取引時に注意
- 時価総額 IDR 10兆未満: 流動性リスク高。ポジション構築/解消に時間を要する

---

### D.7 分析チェックリスト

#### セクター横断チェックリスト

```
□ マクロ環境
  - GDP成長率（BI/BPS発表）→ 内需セクターへの影響
  - インフレ率 → 消費財の価格転嫁力、BI利上げ/利下げ方向性
  - BI-Rate → 銀行NIM、不動産ローン需要
  - USD/IDR → コモディティ企業の恩恵、輸入コスト
  - 経常収支 → IDR安定性の先行指標

□ ガバナンスリスク
  - 支配株主の持分比率と影響力
  - コングロマリットグループ内の関連当事者取引
  - BUMN（国有企業）か民間か → 政策リスクの有無
  - 独立取締役の割合と実効性
  - 監査法人の質（Big 4か否か）
  - 過去のガバナンス問題の有無

□ 規制リスク
  - 外国人投資制限の有無（セクター別）
  - ポジティブインベストメントリストでの位置づけ
  - 産業政策の変更リスク（鉱業法、通信規制等）
  - 税制変更リスク（タバコ物品税等）

□ 為替・流動性
  - IDR変動の株価・業績への影響度
  - フリーフロート比率
  - 日次売買代金の十分性
  - MSCI/FTSEインデックスでのウェイト

□ バリュエーション
  - P/E, P/B, EV/EBITDA → 同業比較（国内・ASEAN横断）
  - 配当利回り → インドネシアは高配当銘柄が多い
  - ROE-PBR相関でのフェアバリュー判断
```

#### 銀行セクター固有チェックリスト

```
□ NIM推移とBI-Rateとの相関
□ CASA比率の改善/悪化トレンド
□ NPL比率と引当金カバレッジ率
□ CoC（Cost of Credit）のトレンド
□ MSME融資比率（規制上の義務達成状況）
□ デジタルバンキング戦略（モバイル取引比率）
□ 資本適足性（CAR）と成長余地
□ 信用成長率 vs 名目GDP成長率
```

#### 通信セクター固有チェックリスト

```
□ 加入者数のネット増減
□ ARPUトレンド（データ収入の構成比増加）
□ 業界再編の進捗（XL+Smartfren統合効果）
□ 5G投資計画と周波数保有状況
□ タワーリース契約の条件（タワー会社との交渉力）
□ 固定ブロードバンド（FTTH）の展開状況
□ 規制動向（周波数割当、料金規制）
□ CAPEX サイクルの位置（投資回収期か投資拡大期か）
```

#### 資源セクター固有チェックリスト

```
□ コモディティ価格見通し（石炭HBA、ニッケルLME）
□ 生産量ガイダンス vs 実績
□ キャッシュコスト推移（ストリップ比率の影響）
□ 採掘許可（IUP/IUPK）の残存期間と更新リスク
□ DMO（国内供給義務）の影響
□ ダウンストリーミング戦略（精錬所建設計画）
□ 環境規制リスク（脱炭素政策、森林破壊問題）
□ 配当政策（コモディティ企業は高配当傾向）
□ 鉱山のロケーション（カリマンタン、スマトラ、スラウェシ）
```

#### 不動産セクター固有チェックリスト

```
□ マーケティングセールス（Pre-sales）のトレンド
□ リカーリング収入比率の推移
□ ランドバンクの質（立地、取得原価、開発タイムライン）
□ Net Debt / Equityとレバレッジ管理
□ 住宅ローン金利環境（BI-Rate連動）
□ 新首都ヌサンタラ（IKN）関連の恩恵
□ 地域別の需給バランス（ジャカルタ、スラバヤ、メダン等）
□ 政府の住宅補助政策（FLPP等）の影響
```

---

## Appendix E: タイ市場 詳細リサーチガイド

### E.1 セクター概要

タイ証券取引所（SET: Stock Exchange of Thailand）はASEAN第3位の規模を持つ市場で、時価総額は約3,800億ドル（2025年4月時点）。SET50/SET100指数を代表指数とし、エネルギー・銀行・通信セクターが市場利益の約50%を占める。CP Group・TCC Group・Crown Property Bureau（王室財産局）など巨大コングロマリットの影響力が大きく、外国人投資制限（49%上限）とNVDR制度が市場構造上の特徴。2026年のSET Index目標は1,301-1,400ポイント圏（24アナリスト・ファンドマネージャー調査）。

#### セクター別概況

| セクター | 概況 |
|---------|------|
| **銀行** | 11行構成。2025年通年合算純利益2,654億バーツ（前年比+3.6%）。KTBとTTBの「スーパーバンク」構想進行中。平均配当利回り6%前後 |
| **エネルギー** | PTTグループ中心の国営エネルギーセクターがSETの中核。上流（PTTEP）から下流（TOP, IRPC）、石化（PTTGC）、再エネ（GPSC, GULF）まで垂直統合 |
| **観光・ホスピタリティ** | 2026年外国人観光客約3,550万人、観光収入1.64兆バーツ見込み。中国人観光客は2019年比34%減と回復遅延 |
| **不動産** | 2025年市場規模約588億ドル、2030年までCAGR 5.59%で772億ドルに成長見込み。地震リスク懸念で住宅販売37%減少 |
| **食品・農業** | CP Foods（CPF）は世界有数の規模。Thai Union（TU）は水産加工の世界的リーダー。SET上場農業・食品セクター46社 |
| **通信** | True Corp（旧DTAC統合）とAISの実質2社独占（HHI 5,000）。MVNOは全社サービス停止 |
| **ヘルスケア** | BDMS（Bangkok Dusit Medical Services）が最大の民間病院ネットワーク。Bumrungrad（BH）は国際的医療ツーリズムのハブ |

---

### E.2 主要プレイヤーとティッカー

#### 銀行

| 企業名 | ティッカー | 時価総額帯 | 特徴 |
|--------|-----------|-----------|------|
| Bangkok Bank | BBL.BK | 約97億USD | タイ最古の商業銀行。CET1 18.0%, CAR 22.6%。保守的経営 |
| Kasikornbank | KBANK.BK | 約144億USD | 2025年純利益首位（496億バーツ）。デジタルバンキングに注力 |
| SCB X (Siam Commercial Bank) | SCB.BK | 約141億USD | 王室財産局系。FinTech・デジタルプラットフォーム戦略 |
| Krungthai Bank | KTB.BK | 約127億USD | 国営銀行。支店数最多（924支店）。TTBとの合併協議中 |
| Bank of Ayudhya (Krungsri) | BAY.BK | Large | 三菱UFJ系列。消費者金融・クレジットカードに強み |
| TMBThanachart Bank | TTB.BK | Mid-Large | TMB+Thanachart合併（2021年）。KTBとの「スーパーバンク」合併協議中 |
| Kiatnakin Phatra Bank | KKP.BK | Mid | 証券・資産運用に強い。リサーチレポートの質が高い |
| TISCO Financial Group | TISCO.BK | Mid | 自動車ローン・リースに特化 |

#### エネルギー

| 企業名 | ティッカー | 時価総額帯 | 特徴 |
|--------|-----------|-----------|------|
| PTT | PTT.BK | 約283億USD | 国営石油ガス最大手。天然ガス・国際トレーディング・石化 |
| PTT Exploration & Production | PTTEP.BK | 約134億USD | タイ唯一の上場E&P。2025-2029に212.5億ドル投資計画 |
| Gulf Energy Development | GULF.BK | 約191億USD | 独立系発電（IPP）。タイ及び海外で電力事業 |
| Banpu | BANPU.BK | Mid | 石炭→クリーンエネルギー移行中。豪州・インドネシアに資産 |
| Thai Oil | TOP.BK | Mid-Large | PTT系列。製油・石化。DJSI認定 |
| IRPC | IRPC.BK | Mid | PTT系列。石化・製油の統合型コンプレックス |
| Global Power Synergy | GPSC.BK | Mid-Large | PTT系列。電力・再エネ |
| Bangchak Corporation | BCP.BK | Mid | 製油・バイオ燃料・リテール（加油站） |

#### 食品・農業

| 企業名 | ティッカー | 時価総額帯 | 特徴 |
|--------|-----------|-----------|------|
| Charoen Pokphand Foods | CPF.BK | Large | CP Group傘下。飼料・養殖・食品加工の世界的大手 |
| Thai Union Group | TU.BK | Mid-Large | 水産加工世界最大手。Chicken of the Sea等ブランド保有 |
| CP ALL | CPALL.BK | 約122億USD | CP Group傘下。セブンイレブン・タイランド運営（約14,000店） |
| Carabao Group | CBG.BK | Mid | エナジードリンク「Carabao」。ASEAN全域に展開 |
| Betagro | BTG.BK | Mid | 養鶏・食品加工。タイ国内市場中心 |

#### 不動産

| 企業名 | ティッカー | 時価総額帯 | 特徴 |
|--------|-----------|-----------|------|
| Central Pattana | CPN.BK | 約75億USD | タイ最大の不動産デベロッパー。商業施設（セントラルワールド等）運営 |
| Land & Houses | LH.BK | 約13億USD | 住宅デベロッパー大手。低層住宅に強み |
| AP (Thailand) | AP.BK | Mid | 住宅デベロッパー。コンドミニアム+タウンハウス |
| Asset World Corp | AWC.BK | Mid-Large | TCC Group系。ホスピタリティ・商業不動産 |
| Sansiri | SIRI.BK | Mid | 住宅デベロッパー。プレミアムブランド |
| Origin Property | ORI.BK | Mid | コンドミニアム中心。若年層向けマーケティング |

#### 通信

| 企業名 | ティッカー | 時価総額帯 | 特徴 |
|--------|-----------|-----------|------|
| Advanced Info Service (AIS) | ADVANC.BK | 約288億USD | 収益規模でタイ最大の通信会社。Intouch Holdings傘下 |
| True Corporation | TRUE.BK | 約123億USD | True+DTAC合併（2023年）。加入者数4,850万で最大。CP Group系 |

#### ヘルスケア

| 企業名 | ティッカー | 時価総額帯 | 特徴 |
|--------|-----------|-----------|------|
| Bangkok Dusit Medical Services | BDMS.BK | Large | タイ最大の民間病院ネットワーク。50施設超 |
| Bumrungrad Hospital | BH.BK | Mid-Large | 国際的医療ツーリズムのフラッグシップ。外国人患者比率高い |
| Bangkok Chain Hospital | BCH.BK | Mid | 地方都市中心の病院チェーン |
| Thonburi Healthcare | THG.BK | Mid | バンコク西部を中心に病院運営 |
| Princ Hospital | PRINC.BK | Mid | 急成長中の病院チェーン |

#### 観光・ホスピタリティ

| 企業名 | ティッカー | 時価総額帯 | 特徴 |
|--------|-----------|-----------|------|
| Airports of Thailand | AOT.BK | 約240億USD | 国営。スワンナプーム空港含む6空港運営。財務省70%保有 |
| Minor International | MINT.BK | Mid-Large | Anantara・Avani等のホテルブランド。レストラン事業も |
| The Erawan Group | ERW.BK | Mid | グランドハイアットエラワン等運営。予算ホテルにも展開 |
| Dusit Thani | DUSIT.BK | Small-Mid | タイ発の高級ホテルブランド |
| Central Plaza Hotel | CENTEL.BK | Mid | Central Group系。センタラホテル＆リゾート運営 |

#### その他（素材・インフラ・テック）

| 企業名 | ティッカー | 時価総額帯 | 特徴 |
|--------|-----------|-----------|------|
| Siam Cement Group | SCC.BK | 約69億USD | 王室財産局系。セメント・建材・石化・パッケージング |
| Delta Electronics (Thailand) | DELTA.BK | 約760億USD | 台湾Delta系。電子部品。SET時価総額最大 |
| Indorama Ventures | IVL.BK | Mid-Large | PET樹脂の世界最大手。グローバル展開 |
| BTS Group Holdings | BTS.BK | Mid | バンコクBTSスカイトレイン運営。広告・不動産 |

---

### E.3 規制当局・政府機関

| 機関 | 役割 | 公開データ | URL |
|------|------|-----------|-----|
| **SEC Thailand**（証券取引委員会） | 資本市場の監督・規制。1992年設立の独立機関 | 上場企業開示書類、ファンド情報、ライセンス情報 | https://www.sec.or.th/EN |
| **SET**（タイ証券取引所） | 株式市場の運営。SET/mai/LiVe Exchangeの3市場 | 企業情報（SET SMART）、インデックス、市場統計 | https://www.set.or.th/en/home |
| **BOT**（タイ中央銀行） | 金融政策、金融システム安定、為替政策 | 金利、外貨準備、経済統計、金融政策決定 | https://www.bot.or.th/en/statistics.html |
| **NBTC**（通信放送委員会） | 放送・通信産業の規制、周波数割当 | 周波数オークション、加入者統計、QoSレポート | https://www.nbtc.go.th/Home.aspx?lang=en-us |
| **NESDC**（経済社会開発評議会） | 経済計画策定、GDP統計発表 | GDP四半期速報、国民経済計算、経済見通し | https://www.nesdc.go.th/en/info/national-accounts/ |
| **BOI**（投資委員会） | 外国投資誘致、投資優遇措置 | 投資統計、インセンティブ情報、EEC政策 | https://www.boi.go.th |
| **MOC**（商務省） | 外国事業法（FBA）の執行、貿易統計 | 輸出入統計、外国事業ライセンス | https://www.moc.go.th |
| **SET SMART** | SET提供の企業情報検索システム | 財務データ、大株主、Factsheet | https://setsmart.set.or.th |

#### SET SMART / SET Factsheetの使い方

SETの各企業ページ（`https://www.set.or.th/en/market/product/stock/quote/{TICKER}/factsheet`）で以下が取得可能:
- 財務諸表サマリー（5年分）
- 主要財務指標（ROE, ROA, P/E, P/BV, 配当利回り）
- 大株主構成
- Foreign Holding比率
- NVDR比率

---

### E.4 セクター固有KPIと取得方法

#### 銀行

| KPI | 定義 | 重要度 | 取得方法 |
|-----|------|--------|---------|
| NIM (Net Interest Margin) | 純金利収益/平均運用資産 | ★★★★★ | 各行決算資料、SET Factsheet |
| NPL Ratio | 不良債権比率 | ★★★★★ | BOT金融統計、各行決算 |
| Coverage Ratio | 引当金/NPL | ★★★★☆ | 各行決算資料（BBL: 300.3%等） |
| LDR (Loan-to-Deposit Ratio) | 貸出/預金比率 | ★★★★☆ | 各行決算資料 |
| CASA Ratio | 当座・普通預金比率 | ★★★★☆ | 各行決算IR資料 |
| CAR (Capital Adequacy Ratio) | 自己資本比率 | ★★★★☆ | BOT統計、各行決算（BBL: 22.6%等） |
| CET1 Ratio | 普通株式等Tier1比率 | ★★★★☆ | BOT統計、各行決算（BBL: 18.0%等） |
| Fee Income Ratio | 手数料収入/営業収益 | ★★★☆☆ | 各行決算IR資料 |
| Credit Cost | 信用コスト | ★★★★☆ | 各行決算（業界平均1.14%） |

#### エネルギー

| KPI | 定義 | 重要度 | 取得方法 |
|-----|------|--------|---------|
| 生産量 (Production Volume) | 原油・ガスの日量生産 | ★★★★★ | PTTEP決算・オペレーションレビュー |
| GRM (Gross Refining Margin) | 精製マージン | ★★★★★ | TOP, IRPC, BCP決算資料 |
| 石化マージン (Petchem Spread) | 石化製品のスプレッド | ★★★★☆ | PTTGC, IRPC決算資料 |
| GRM-Benchmark vs Actual | ベンチマークGRMとの乖離 | ★★★★☆ | TOP, BCP IR資料 |
| EBITDA Margin | EBITDA/売上高 | ★★★★☆ | SET Factsheet、各社決算 |
| Capex / 投資計画 | 設備投資額（5年計画等） | ★★★☆☆ | PTTEP: 212.5億ドル（2025-2029） |
| ESG / Clean Energy比率 | 再エネ・クリーンエネルギー収益比率 | ★★★☆☆ | 各社サステナビリティレポート |

#### 食品・農業

| KPI | 定義 | 重要度 | 取得方法 |
|-----|------|--------|---------|
| 飼料販売量 | 飼料の販売トン数 | ★★★★★ | CPF決算・オペレーションレビュー |
| 養殖生産量 | エビ・魚の生産量 | ★★★★☆ | CPF, TU決算資料 |
| 輸出比率 | 海外売上/総売上 | ★★★★☆ | 各社決算・地域別セグメント |
| 原材料コスト | 飼料原料（大豆粕、魚粉等）価格 | ★★★★☆ | CBOT先物、各社決算 |
| Same-Store Sales Growth | 既存店売上成長率 | ★★★☆☆ | CPALL（セブンイレブン）決算 |

#### 観光・ヘルスケア

| KPI | 定義 | 重要度 | 取得方法 |
|-----|------|--------|---------|
| RevPAR | 客室あたり売上（ホテル） | ★★★★★ | MINT, ERW, CENTEL決算IR |
| 稼働率 (Occupancy Rate) | 客室稼働率 | ★★★★★ | MINT, ERW決算IR |
| 外国人患者比率 | 外国人患者/総患者 | ★★★★★ | BDMS, BH決算IR |
| ARPOB (Avg Revenue per Occupied Bed) | 病床あたり平均収入 | ★★★★☆ | BDMS, BH決算IR |
| 外国人観光客数 | 月次入国者統計 | ★★★★☆ | TAT（タイ国政府観光庁）、BOT統計 |
| ADR (Average Daily Rate) | 平均客室単価 | ★★★★☆ | ホテル各社決算IR |
| PAX（空港利用者数） | 旅客数 | ★★★★☆ | AOT月次統計 |

#### 不動産

| KPI | 定義 | 重要度 | 取得方法 |
|-----|------|--------|---------|
| Pre-sales | 契約済み未引渡し販売額 | ★★★★★ | 各デベロッパー決算IR |
| Backlog | 未引渡し残高 | ★★★★★ | AP, SIRI, ORI決算IR |
| Transfer Revenue | 引渡し完了に伴う収益認識額 | ★★★★☆ | 各デベロッパー決算IR |
| Same-mall Rental Growth | 既存モール賃料成長率 | ★★★★☆ | CPN決算IR |
| 稼働率 (Occupancy Rate) | 商業施設の入居率 | ★★★★☆ | CPN決算IR |
| 住宅ローン金利 | 主要行の住宅ローン変動金利 | ★★★☆☆ | BOT金融統計 |

#### 通信

| KPI | 定義 | 重要度 | 取得方法 |
|-----|------|--------|---------|
| 加入者数 (Subscribers) | モバイル加入者数 | ★★★★★ | ADVANC, TRUE決算IR（TRUE: 4,850万） |
| ARPU | 加入者あたり平均収入 | ★★★★★ | ADVANC, TRUE決算IR |
| EBITDA Margin | EBITDA/売上高 | ★★★★☆ | ADVANC, TRUE決算（TRUE: 65.3%） |
| データ使用量 / 加入者 | 1加入者あたり月間データ量 | ★★★☆☆ | 各社決算IR |
| 5G カバレッジ率 | 5G対応エリアの人口カバー率 | ★★★☆☆ | NBTC統計、各社IR |

---

### E.5 情報ソース

#### ニュース・メディア

| メディア | 言語 | 特徴 | URL |
|---------|------|------|-----|
| **Bangkok Post** | 英語 | タイ最古の英字新聞。ビジネス・市場報道が充実 | https://www.bangkokpost.com/business |
| **The Nation Thailand** | 英語 | デジタル中心。政治・ビジネス・国際ニュース | https://www.nationthailand.com |
| **Kaohoon International** | 英語 | SET市場・証券アナリスト情報に特化 | https://www.kaohooninternational.com |
| **Prachachat Turakij** | タイ語 | タイ語ビジネス日刊紙。市場・政策に強い | https://www.prachachat.net |
| **Manager Online** | タイ語 | タイ語ニュース。ビジネス・政治 | https://mgronline.com |
| **Thai Rath（タイラット）** | タイ語/英語 | タイ最大の日刊紙。英語版あり | https://en.thairath.co.th |
| **SET News** | タイ語/英語 | SET公式ニュース・企業開示 | https://www.set.or.th/en/market/news-and-alert |
| **Thai PBS World** | 英語 | 公共放送。政策・経済分析 | https://www.thaipbsworld.com |

#### 業界リサーチ

| 証券会社/リサーチ | 特徴 | アクセス方法 |
|------------------|------|-------------|
| **Bualuang Securities (BLS)** | Bangkok Bank系。幅広いセクターカバレッジ | https://www.bualuang.co.th/en/tools-lists/tools/bls-research |
| **KGI Securities (Thailand)** | KGI系。マクロ・セクター分析 | 口座開設で閲覧 |
| **Kiatnakin Phatra Securities (KKPS)** | リサーチ品質が高い。ヘルスケア・銀行分析に定評 | 口座開設で閲覧 |
| **Maybank Kim Eng (Thailand)** | Maybank系。ASEAN横断リサーチ | https://kelive.maybank.co.th |
| **Kasikorn Securities** | KBANK系。個人投資家向けリサーチも充実 | 口座開設で閲覧 |
| **Phatra Securities** | 機関投資家向け。独立系リサーチに定評 | 口座開設で閲覧 |
| **Asia Plus Securities** | 中小型株カバレッジ | 口座開設で閲覧 |
| **TISCO Securities** | セクターレポート | 口座開設で閲覧 |
| **Krungsri Research** | Bank of Ayudhya系。産業アウトルックが充実 | https://www.krungsri.com/en/research/industry |

#### 投資家プレゼンテーション取得先

| 企業 | IR URL | 決算特徴 |
|------|--------|---------|
| PTT | https://www.pttplc.com/en/investor-relations | 四半期決算。セグメント別（上流・下流・石化・その他）の詳細開示 |
| PTTEP | https://www.pttep.com/en/investor-relations | 四半期決算。生産量・CAPEX・コスト分析が充実 |
| ADVANC (AIS) | https://investor.ais.co.th | 四半期決算。加入者数・ARPU・データ使用量の詳細 |
| TRUE | https://investor.truecorp.co.th | 四半期決算。合併後のシナジー進捗レポート |
| BBL | https://www.bangkokbank.com/en/Investor-Relations | 四半期決算。資産の質・CAR・セグメント別分析 |
| KBANK | https://www.kasikornbank.com/en/Investors | 四半期決算。デジタルバンキングKPIの開示が充実 |
| BDMS | https://investor.bdms.co.th | 四半期決算。病院別・国籍別患者データ |
| CPN | https://www.centralpattana.co.th/en/investor-relations | 四半期決算。モール別稼働率・賃料データ |
| CPF | https://www.cpfworldwide.com/en/investor | 四半期決算。国別セグメント（タイ・中国・ベトナム等） |
| AOT | https://investor.airportthai.co.th | 四半期決算。空港別PAX・非航空収入データ |
| MINT | https://www.minor.com/en/investor-relations | 四半期決算。地域別（アジア・欧州）ホテルKPI |

---

### E.6 タイ固有の注意点

#### 外国人投資制限（Foreign Board / NVDR制度）

**外国人持株制限**
- **一般的な上限**: 49%（Foreign Business Act B.E. 2542に基づく）
- 銀行・通信・メディア・運輸など特定セクターではさらに厳しい制限あり
- SET上の外国人持株比率（Foreign Limit）はSET Factsheetで確認可能

**NVDR（Non-Voting Depository Receipt）**
- SET子会社のThai NVDR Co., Ltd.が発行
- **メリット**: Foreign Limitを超えて投資可能。配当受取権・売買差益は保持
- **デメリット**: 議決権なし。コーポレートガバナンスへの関与不可
- **注意**: 支配株主がNVDRを通じて議決権を維持しつつ経済的エクスポージャーを売却するケースがあり、企業集中を助長する側面がある

**Foreign Board（F株）**
- 外国人持株上限に達した場合、Foreign Boardで外国人間のみの取引が可能
- F株は通常、Main Boardより高いプレミアムで取引される

#### 外国事業法（Foreign Business Act）

- 外国企業の参入が制限されるセクター: メディア、農業、小売、サービス、天然資源等
- 2025年4月: 内閣がFBA改正を承認。「保護」から「競争力構築」へ方針転換
- **ハイテクセクター免除（提案中）**: AI/ML、ロボティクス、EV、半導体、デジタルプラットフォーム、バイオテクノロジー分野の外国企業はFBLが不要になる方向

#### 会計基準（TFRS / IFRS収斂状況）

- タイはTFRS（Thai Financial Reporting Standards）を採用
- TFRSはIFRSと1対1の対応関係。IFRSの翻訳版（1年の適用遅延あり）
- TFRS 17（保険契約）は2025年1月1日から適用開始
- 会計職業法B.E. 2547により、英語→タイ語への翻訳が必須
- **実務上**: 大型株の英語開示は充実しているが、中小型株はタイ語のみの場合あり

#### 王室財産局（Crown Property Bureau）関連企業

王室財産局（2025年以降「Privy Purse Bureau」に改称）は推定370-594億ドルの資産を保有し、以下の主要企業の大株主:

| 企業 | ティッカー | 王室財産局の関与 |
|------|-----------|----------------|
| Siam Commercial Bank | SCB.BK | 歴史的に王室財産局が大株主 |
| Siam Cement Group | SCC.BK | 王室財産局が筆頭株主 |

- 王室財産局関連企業の経営は独立性が高いが、ガバナンス構造の理解は重要
- タイ国内では王室関連のセンシティブなトピックは不敬罪（Lese-majeste）の対象となりうるため、現地メディアの報道には制約がある

#### コングロマリット構造

タイ経済は少数のファミリー系コングロマリットが支配的:

| グループ | 創業者/支配者 | 主要上場企業 | 主要セクター |
|---------|-------------|------------|------------|
| **CP Group** | Chearavanont家 | CPF, CPALL, TRUE, CPH | 農業、食品、通信、小売 |
| **TCC Group** | Charoen Sirivadhanabhakdi | ThaiBev（SGX上場）, BJC, AWC | 酒類・飲料、小売、不動産 |
| **Central Group** | Chirathivat家 | CPN, CENTEL, CRC | 小売、不動産、ホスピタリティ |
| **King Power** | Srivaddhanaprabha家 | 非上場（King Power International） | 免税店、旅行小売 |
| **PTT Group** | 国営 | PTT, PTTEP, PTTGC, TOP, IRPC, GPSC | エネルギー、石化 |
| **Thai Beverage (ThaiBev)** | Charoen Sirivadhanabhakdi | SGX上場 | 酒類、飲料。タイ非上場（酒類上場禁止のため） |

**注意**: ThaiBev（タイ・ビバレッジ）はタイでの酒類企業上場が禁止されているためシンガポールSGXに上場。TCC Groupの分析にはSGXの情報も必要。

#### 通貨リスク（THB）

- タイバーツ（THB）はBOTの管理変動相場制
- 輸出依存度が高い経済構造（GDP比約60%）のため、THBは対ドルで景気感応的
- 2025年のBOT利下げによりTHB安圧力あり
- 外国人投資家のリターンはTHBの為替変動に大きく影響される
- BOTの外貨準備は約2,000億ドル超（十分な水準）

#### 政治リスク

- タイは1932年以降、軍事クーデターが13回（成功ベース）発生
- 2023年総選挙でMove Forward Partyが第1党になるも、保守派・軍部の影響で政権取れず
- 2024年にMove Forward Partyは解党命令（憲法裁判所）
- 政治不安定性は市場のディスカウント要因。SET IndexのP/Eは他のASEAN市場と比較して低め
- 軍・王室・財閥の三角関係がタイ政治経済の基底構造
- 政治的な政策変更リスク（デジタルウォレット政策、最低賃金引上げ等）に注意

#### EEC（東部経済回廊）

- チャチューンサオ、チョンブリー、ラヨーンの3県をカバー
- 2025年上半期のFDI・国内投資は1,880件、1.05兆バーツ（前年比+138%）
- EEC投資額はうち6,606億バーツ（62%）
- 税制優遇: CIT免税最長15年、外国人専門職の一律17%所得税率
- 対象産業: 自動車（EV）、ロボティクス、航空・物流、バイオテク、デジタル

---

### E.7 分析チェックリスト

#### 基本チェック

```
□ SET Factsheetで基本財務指標を確認（P/E, P/BV, ROE, 配当利回り）
□ 過去5年の財務推移を確認（売上成長、利益成長、ROE推移）
□ Foreign Holding比率とNVDR比率を確認
□ 大株主構成を確認（コングロマリット系か、国営か、外資系か）
□ Free Float比率を確認（SET50/100の組入れ基準に影響）
```

#### コングロマリット分析

```
□ 対象企業が属するコングロマリットグループを特定
□ 関連会社間取引（Related Party Transactions）を確認
□ グループ内の資金循環・持株構造を理解
□ CP Group系、TCC Group系、Central Group系、PTT Group系のいずれかに該当するか
```

#### セクター固有チェック

**銀行:**
```
□ NIM, NPL比率, Coverage比率の推移
□ 信用コスト（Credit Cost）のガイダンス
□ デジタルバンキング指標（MAU, デジタル取引比率）
```

**エネルギー:**
```
□ 原油・ガス価格のシナリオ分析
□ GRM/石化マージンの方向性
□ クリーンエネルギー移行計画のCapex配分
```

**食品:**
```
□ 原材料コスト（大豆粕、魚粉、とうもろこし）の動向
□ 国別セグメント（タイ国内 vs 海外）の利益率差異
```

**観光・ヘルスケア:**
```
□ 外国人観光客の国籍別トレンド（中国回復状況に注目）
□ 外国人患者比率と国籍別構成（中東、日本、中国等）
```

**不動産:**
```
□ Pre-salesトレンドとバックログの質（引渡し予定時期）
□ 金利環境と住宅ローン承認率
```

**通信:**
```
□ ARPU成長とデータ使用量の関係
□ True-DTAC合併後のシナジー実現状況
```

#### マクロ・カントリーリスク

```
□ GDP成長率（NESDC四半期発表）
□ BOT政策金利の方向性
□ THB/USD為替レートの動向
□ 政治情勢（政権安定性、選挙スケジュール）
□ 中国経済のタイへの影響（貿易、観光、投資）
```

#### バリュエーション

```
□ SET50/100内のセクター平均P/Eとの比較
□ 配当利回り（タイ銀行株の高配当は魅力的だが持続性を検証）
□ PBR（簿価割れ銘柄のバリュートラップに注意）
□ EV/EBITDA（特にエネルギー・通信セクター）
□ ASEAN域内のピア比較（インドネシア、マレーシア、フィリピン等の同業と比較）
```

#### 実務・アクセス

```
□ 取引通貨（THB）の為替ヘッジ要否
□ 外国人持株制限の確認（Foreign Limit到達銘柄はF株 or NVDR経由）
□ 配当に対する源泉徴収税（10%）の確認
□ 取引時間: 10:00-12:30, 14:30-16:30（タイ時間, GMT+7）
□ yfinanceティッカー形式: `{TICKER}.BK`（例: `PTT.BK`, `SCB.BK`, `ADVANC.BK`）
```

#### 参考リンク集

| カテゴリ | URL |
|---------|-----|
| SET（メイン） | https://www.set.or.th/en/home |
| SET SMART | https://setsmart.set.or.th |
| SEC Thailand | https://www.sec.or.th/EN |
| BOT統計 | https://www.bot.or.th/en/statistics.html |
| BOT経済見通し | https://www.bot.or.th/en/thai-economy/economic-outlook.html |
| NESDC国民経済計算 | https://www.nesdc.go.th/en/info/national-accounts/ |
| BOI | https://www.boi.go.th |
| NBTC | https://www.nbtc.go.th/Home.aspx?lang=en-us |
| Krungsri Industry Outlook | https://www.krungsri.com/en/research/industry |
| Bualuang Research | https://www.bualuang.co.th/en/tools-lists/tools/bls-research |
| Bangkok Post Business | https://www.bangkokpost.com/business |
| Nation Thailand | https://www.nationthailand.com |
| Kaohoon International | https://www.kaohooninternational.com |

---

## Appendix F: フィリピン市場 詳細リサーチガイド

### F.1 セクター概要

フィリピン株式市場（Philippine Stock Exchange, PSE）は、国内時価総額約13.65兆ペソ（2025年末時点、前年比6.29%減）を持つASEAN主要市場の一つ。PSE Composite Index（PSEi）は30銘柄で構成され、年2回（2月・8月）リバランスを実施する。

市場の特徴は**コングロマリット（持株会社）の支配的存在**で、SM Group、Ayala Group、JG Summit、Aboitiz Group、MVP（Pangilinan）Group、San Miguel Corporationなどの財閥が経済の中核を占める。

2025年はPSEiが年間7.29%下落。特にHolding Firms（持株会社）指数が15.12%下落と最も大きな打撃を受けた。一方、BSPの利下げサイクル（ピーク6.5%から4.5%まで175bp引き下げ）を背景に、銀行セクターは2026年の市場回復を牽引すると期待されている。

#### 主要セクター分類

| セクター | 説明 | PSEi構成比（概算） |
|---------|------|-------------------|
| Holding Firms（持株会社） | SM, AC, JGS, AEV, AGI, GTCAP, DMC, LTG, MPI, SMC | 最大 |
| Financials（金融） | BDO, BPI, MBT, SECB | 大 |
| Property（不動産） | SMPH, ALI, MEG, RLC | 大 |
| Services（サービス） | TEL, GLO, ICT, CNVRG | 中 |
| Industrial（産業） | AP, MER, FGEN, JFC, URC | 中 |
| Mining & Oil（鉱業・石油） | SCC, NIKL等 | 小 |

---

### F.2 主要プレイヤーとティッカー

#### コングロマリット（Holding Firms）

| 企業名 | PSEティッカー | yfinance | 時価総額帯 | 主要子会社・事業 |
|--------|-------------|----------|-----------|----------------|
| **SM Investments Corp** | SM | SM.PS | 超大型 | SMPH（不動産）、BDO（銀行）、SM Retail（小売） |
| **Ayala Corporation** | AC | AC.PS | 大型 | ALI（不動産）、BPI（銀行）、GLO（通信）、ACEN（エネルギー） |
| **JG Summit Holdings** | JGS | JGS.PS | 大型（約1,880億ペソ） | URC（食品）、Cebu Pacific（航空）、Robinsons（小売・不動産）、Petrochemicals |
| **Aboitiz Equity Ventures** | AEV | AEV.PS | 大型（約1,696億ペソ） | AP（電力）、UnionBank（銀行）、Aboitiz Land、Pilmico（飼料） |
| **San Miguel Corporation** | SMC | SMC.PS | 大型（約2,026億ペソ） | Petron（石油）、SMC Global Power（電力）、インフラ、食品・飲料 |
| **Alliance Global Group** | AGI | AGI.PS | 中型（約670億ペソ） | Megaworld（不動産）、Emperador（酒類）、McDonald's PH、Travellers Intl（カジノ） |
| **GT Capital Holdings** | GTCAP | GTCAP.PS | 中型 | Metrobank（銀行）、Toyota PH、Federal Land（不動産）、AXA PH（保険） |
| **DMCI Holdings** | DMC | DMC.PS | 中型 | DMCI Homes（不動産）、Semirara Mining & Power、DMCI Mining |
| **Metro Pacific Investments** | MPI | MPI.PS | 中型 | Meralco（配電）、MPIC Toll Roads、Maynilad（水道）、Metro Pacific Hospital |
| **LT Group** | LTG | LTG.PS | 中型 | PNB（銀行）、Tanduay（酒類）、PAL Holdings（航空）、タバコ |
| **ICTSI** | ICT | ICT.PS | 超大型（約1.2兆ペソ） | グローバル港湾運営（30ヶ国以上） |

> **注**: ICTSIは2026年1月時点で時価総額約1.2兆ペソとフィリピン最大の企業。持株会社ではなく港湾運営専業だが、PSEiの主要構成銘柄。

#### 銀行（Financials）

| 企業名 | PSEティッカー | yfinance | 総資産（2025Q1） | 特徴 |
|--------|-------------|----------|-----------------|------|
| **BDO Unibank** | BDO | BDO.PS | 4.83兆ペソ | フィリピン最大の銀行。SM Group系列。資産・資本・預金・貸出全て首位 |
| **Bank of the Phil. Islands (BPI)** | BPI | BPI.PS | - | Ayala Group系列。消費者向け成長が強い。NIMが相対的に高い |
| **Metropolitan Bank (Metrobank)** | MBT | MBT.PS | 3.51兆ペソ | GT Capital系列。資産規模2位。堅実な経営 |
| **Security Bank** | SECB | SECB.PS | - | 2025Q1で資産成長率32.7%と最速。三菱UFJが出資 |
| **China Banking Corp** | CHIB | CHIB.PS | - | SM Group系列。中型ながら安定成長 |
| **Union Bank of the Philippines** | UBP | UBP.PS | - | Aboitiz Group系列。デジタルバンキングに強い |
| **Philippine National Bank** | PNB | PNB.PS | - | LT Group系列。リテール・企業向けバランス型 |
| **Rizal Commercial Banking** | RCB | RCB.PS | - | 住友三井系出資。2025Q1資産成長率17.3% |

#### 不動産（Property）

| 企業名 | PSEティッカー | yfinance | 時価総額帯 | 特徴 |
|--------|-------------|----------|-----------|------|
| **SM Prime Holdings** | SMPH | SMPH.PS | 超大型 | フィリピン最大の不動産デベロッパー。モール・住宅・オフィス・ホテル。9B USD PH拡張計画 |
| **Ayala Land** | ALI | ALI.PS | 大型 | Ayala Group不動産部門。高級～中間層向け |
| **Megaworld Corp** | MEG | MEG.PS | 中型 | AGI系列。タウンシップ開発に強み |
| **Robinsons Land** | RLC | RLC.PS | 中型 | JG Summit系列。モール・住宅・オフィス・ホテル・物流 |
| **Vista Land** | VLL | VLL.PS | 中型 | Villar Group。手頃な価格帯の住宅に強い |
| **Filinvest Land** | FLI | FLI.PS | 小型 | Gotianun Group。住宅・商業 |

#### 通信（Telecoms / Services）

| 企業名 | PSEティッカー | yfinance | モバイル加入者数 | 特徴 |
|--------|-------------|----------|----------------|------|
| **PLDT Inc** | TEL | TEL.PS | 約5,900万 | 最大手。Smart Communications（モバイル）。FTTH加入者363万、ARPU 1,485ペソ |
| **Globe Telecom** | GLO | GLO.PS | 約6,300万 | Ayala Group系列。モバイルサービス収入1,100億ペソ超 |
| **Converge ICT Solutions** | CNVRG | CNVRG.PS | - | 固定ブロードバンド専業。250万超の加入者 |
| **DITO Telecommunity** | DITO | DITO.PS | 約1,500万（2025年7月） | 第3の通信事業者（Dennis Uy / China Telecom出資） |

#### ユーティリティ / エネルギー

| 企業名 | PSEティッカー | yfinance | 発電容量 | 特徴 |
|--------|-------------|----------|---------|------|
| **Manila Electric (Meralco)** | MER | MER.PS | 配電専業 | フィリピン最大の配電会社。メトロマニラ含む9,337km2をカバー |
| **Aboitiz Power** | AP | AP.PS | 5,745 MW | 最大の発電容量（全体の22.47%）。AEV系列 |
| **First Gen Corp** | FGEN | FGEN.PS | 3,393 MW | Lopez Group系列。天然ガス・地熱・水力・風力・太陽光 |
| **ACEN Corp** | ACEN | ACEN.PS | - | Ayala Group再エネ部門。東南アジア最大級の再エネ企業を目指す |
| **Semirara Mining & Power** | SCC | SCC.PS | - | DMCI系列。石炭採掘+火力発電の垂直統合 |

#### 消費財（Consumer）

| 企業名 | PSEティッカー | yfinance | 時価総額帯 | 特徴 |
|--------|-------------|----------|-----------|------|
| **Jollibee Foods Corp** | JFC | JFC.PS | 大型 | フィリピン最大のQSR企業。Jollibee、Chowking、Greenwich等。グローバル展開 |
| **Universal Robina Corp** | URC | URC.PS | 大型（約1,562億ペソ） | JG Summit系列。スナック・飲料・砂糖。配当利回り約4.7% |
| **Monde Nissin** | MONDE | MONDE.PS | 大型（約1,060億ペソ） | Lucky Me!（インスタント麺）、SkyFlakes。Quorn（英国植物性食品）保有 |
| **Emperador Inc** | EMP | EMP.PS | 中型 | AGI系列。ブランデー・ウイスキー（Whyte & Mackay, Fundador） |
| **Century Pacific Food** | CNPF | CNPF.PS | 中型 | 缶詰食品（Century Tuna等）、ココナッツ製品 |

---

### F.3 規制当局・政府機関

| 機関 | 役割 | 公開データ | URL |
|------|------|----------|-----|
| **SEC Philippines** | 証券規制、企業登録・監督、開示義務管理 | 企業財務報告（17-A, 17-Q）、大量保有報告 | https://www.sec.gov.ph/ |
| **PSE** | 証券取引所運営、上場審査、自主規制機関（SRO） | 株価データ、指数構成、取引統計 | https://www.pse.com.ph/ |
| **PSE EDGE** | PSEの電子開示システム | 上場企業の適時開示、財務報告、株主構成、外国人持分比率 | https://edge.pse.com.ph/ |
| **BSP** (Bangko Sentral ng Pilipinas) | 中央銀行。金融政策、銀行監督、為替管理 | 政策金利、銀行統計、OFW送金統計、BOP、外貨準備 | https://www.bsp.gov.ph/ |
| **PSA** (Philippine Statistics Authority) | 中央統計機関 | GDP、CPI、雇用統計、貿易統計、人口統計 | https://psa.gov.ph/ |
| **NTC** (National Telecommunications Commission) | 通信規制。周波数管理、ライセンス | 通信事業者統計、周波数割当情報 | https://ntc.gov.ph/ |
| **BOI** (Board of Investments) | 投資促進、投資優遇措置の管理 | 投資インセンティブ、優先投資分野（IPP） | https://boi.gov.ph/ |
| **PEZA** (Philippine Economic Zone Authority) | 経済特区の管理・運営 | PEZA登録企業、特区情報、税制優遇 | https://www.peza.gov.ph/ |
| **ERC** (Energy Regulatory Commission) | エネルギー規制 | 電力料金、発電ライセンス、WESM（卸電力市場）データ | https://www.erc.gov.ph/ |
| **DOE** (Department of Energy) | エネルギー政策 | エネルギー需給統計、再エネ政策 | https://www.doe.gov.ph/ |
| **NEDA** (National Economic and Development Authority) | 経済開発計画 | Philippine Development Plan、マクロ経済見通し | https://www.neda.gov.ph/ |

---

### F.4 セクター固有KPIと取得方法

#### コングロマリット

| KPI | 定義 | データソース | 重要度 |
|-----|------|------------|--------|
| **セグメント別利益構成** | 各事業セグメントの利益貢献度 | 各社年報・四半期決算 | ★★★★★ |
| **SOTP (Sum of the Parts)** | 各子会社の評価合計 | アナリストレポート、各子会社の時価総額 | ★★★★★ |
| **NAV Discount / Premium** | 持株会社株価 vs 子会社持分時価総額 | PSE株価データ、各社IR資料 | ★★★★★ |
| **配当方針** | 子会社→持株会社への配当フロー | 各社年報、配当履歴 | ★★★★☆ |
| **純有利子負債** | 持株会社レベルの負債 | 各社四半期決算 | ★★★★☆ |
| **投資パイプライン** | 新規投資・M&A計画 | IR資料、ニュース | ★★★★☆ |

#### 銀行

| KPI | 定義 | データソース | 重要度 |
|-----|------|------------|--------|
| **NIM** | 純金利マージン | 各行四半期決算 | ★★★★★ |
| **NPL Ratio** | 不良債権比率 | 各行四半期決算、BSP統計 | ★★★★★ |
| **CASA Ratio** | 当座預金・普通預金比率 | 各行四半期決算 | ★★★★☆ |
| **CAR** | 自己資本比率 | 各行四半期決算、BSP | ★★★★☆ |
| **ROE** | 自己資本利益率 | 各行四半期決算 | ★★★★★ |
| **Cost-to-Income Ratio** | 経費率 | 各行四半期決算 | ★★★★☆ |
| **Loan Growth** | 貸出金成長率 | 各行四半期決算、BSP統計 | ★★★★☆ |
| **Provision Coverage Ratio** | 貸倒引当金カバレッジ | 各行四半期決算 | ★★★★☆ |

#### 不動産

| KPI | 定義 | データソース | 重要度 |
|-----|------|------------|--------|
| **Reservation Sales** | 新規予約販売額（住宅） | 各社四半期決算・IR資料 | ★★★★★ |
| **Rental Revenue** | 賃貸収入（モール・オフィス） | 各社四半期決算 | ★★★★★ |
| **Occupancy Rate** | モール・オフィス稼働率 | 各社四半期決算・IR資料 | ★★★★★ |
| **Land Bank** | 保有土地面積・開発可能面積 | 各社年報・IR資料 | ★★★★☆ |
| **Net Debt / Equity** | レバレッジ | 各社四半期決算 | ★★★★☆ |
| **Same-Mall Sales Growth** | 既存モール売上成長率 | SMPH、RLC等のIR資料 | ★★★★☆ |

#### 通信

| KPI | 定義 | データソース | 重要度 |
|-----|------|------------|--------|
| **加入者数** | モバイル / ブロードバンド加入者 | 各社四半期決算、NTC | ★★★★★ |
| **ARPU** | ユーザーあたり月間売上 | 各社四半期決算 | ★★★★★ |
| **Service Revenue** | サービス収入（機器販売除く） | 各社四半期決算 | ★★★★★ |
| **EBITDA Margin** | EBITDA利益率 | 各社四半期決算 | ★★★★☆ |
| **CAPEX / Revenue** | 設備投資比率 | 各社四半期決算 | ★★★★☆ |

#### ユーティリティ / エネルギー

| KPI | 定義 | データソース | 重要度 |
|-----|------|------------|--------|
| **発電容量** (Installed Capacity, MW) | 総設備容量 | 各社年報・IR資料、DOE | ★★★★★ |
| **販売電力量** (Energy Sold, GWh) | 販売した電力量 | 各社四半期決算 | ★★★★★ |
| **燃料ミックス** | 石炭/天然ガス/再エネ/地熱の構成比 | 各社年報、DOE | ★★★★☆ |
| **Contracted vs Spot** | 長期契約 vs スポット売電比率 | 各社決算 | ★★★★☆ |
| **RE Portfolio** | 再エネポートフォリオ（MW） | 各社IR資料 | ★★★★☆ |

#### 消費財

| KPI | 定義 | データソース | 重要度 |
|-----|------|------------|--------|
| **Revenue Growth** | 売上成長率（国内/海外別） | 各社四半期決算 | ★★★★★ |
| **Gross Margin** | 粗利益率 | 各社四半期決算 | ★★★★★ |
| **Same-Store Sales Growth** | 既存店売上成長率（JFC等QSR） | 各社四半期決算 | ★★★★★ |
| **Store Count** | 店舗数・出店計画 | 各社四半期決算・IR資料 | ★★★★☆ |
| **Market Share** | カテゴリ別市場シェア | Nielsen、各社IR資料 | ★★★★☆ |

---

### F.5 情報ソース

#### ニュース・メディア

| メディア | 言語 | 特徴 | URL |
|---------|------|------|-----|
| **Inquirer.net (Business)** | 英語 | フィリピン最大の英字紙。ビジネスセクションが充実 | https://business.inquirer.net/ |
| **Philippine Star (Business)** | 英語 | 主要英字紙。企業・市場ニュースに強い | https://www.philstar.com/business |
| **BusinessWorld Online** | 英語 | 経済・金融専門紙。最も詳細な金融報道 | https://www.bworldonline.com/ |
| **Business Mirror** | 英語 | マカティ拠点のビジネス専門紙 | https://businessmirror.com.ph/ |
| **Manila Bulletin (Business)** | 英語 | 歴史ある全国紙 | https://mb.com.ph/category/business |
| **Rappler (Business)** | 英語 | デジタルメディア。データジャーナリズムに強い | https://www.rappler.com/business/ |
| **Bilyonaryo** | 英語 | フィリピン富裕層・企業ニュース特化 | https://bilyonaryo.com/ |

#### 業界リサーチ・証券会社

| 証券会社 | 特徴 | URL |
|---------|------|-----|
| **COL Financial** | フィリピン最大のオンライン証券。リサーチレポート充実 | https://www.colfinancial.com/ |
| **First Metro Securities** | Metrobank系列。機関投資家向けリサーチ | https://www.firstmetrosec.com.ph/ |
| **BPI Securities (BPI Trade)** | Ayala/BPI系列。リサーチレポート | https://www.bpiexpressonline.com/bpitrade |
| **BDO Nomura Securities** | BDO系列（野村提携）。機関投資家向け | - |
| **Macquarie Philippines** | 外資系。機関投資家向けアジアリサーチ | - |
| **J.P. Morgan Philippines** | 外資系。銀行セクター等のフラッグシップレポート | - |

#### 投資家プレゼンテーション取得先

| 企業 | IR URL | 決算の特徴 |
|------|--------|-----------|
| **SM Investments** | https://www.sminvestments.com/investors/ | 統合報告書。SM Retail、SMPH、BDOのセグメント別分析 |
| **Ayala Corporation** | https://ayala.com/investor-relations/ | ポートフォリオ企業のNAV分析 |
| **SM Prime Holdings** | https://www.smprime.com/quarterly-financials | モール・住宅・オフィスのセグメント別KPI |
| **BDO Unibank** | https://www.bdo.com.ph/investor-relations | 銀行KPIダッシュボード |
| **PLDT Inc** | https://main.pldt.com/investor-relations | 個人・法人・デジタルのセグメント別開示 |
| **Globe Telecom** | https://www.globe.com.ph/about-us/investor-relations.html | モバイル・Home Broadband・企業別KPI |
| **Meralco** | https://company.meralco.com.ph/ | 配電KPI、子会社発電事業 |
| **Jollibee Foods** | https://www.jollibeegroup.com/investor-relations/ | ブランド別・地域別開示 |
| **ICTSI** | https://www.ictsi.com/investors | グローバル港湾別のスループット・収益開示 |

#### 無料データソース

| ソース | 特徴 | URL |
|--------|------|-----|
| **PSE EDGE** | PSE上場企業の全開示書類 | https://edge.pse.com.ph/ |
| **Dividends.ph** | フィリピン株の配当、P/E、時価総額データ | https://dividends.ph/ |
| **Pesobility** | フィリピン株の株価・財務データ・スクリーニング | https://www.pesobility.com/ |
| **Simply Wall St** | フィリピン株の財務データ可視化 | https://simplywall.st/stocks/ph |

---

### F.6 フィリピン固有の注意点

#### 外国人投資制限（60/40ルール）

フィリピンの外国人投資制限は1987年憲法に根拠を持つ。

**憲法上の規制（60/40ルール）**:
- 土地所有: フィリピン国民/法人のみ（外国人は所有不可、リースは可能）
- マスメディア: 外国人持分は0%（完全にフィリピン国民のみ）
- 広告業: 外国人持分30%まで
- 公益事業（Public Utilities）: 外国人持分40%まで

**Public Service Act改正（RA 11659, 2022年3月署名、2023年4月施行）**:

改正により「公益事業（Public Utility）」の定義が限定され、以下のみが40%制限の対象:
1. 配電
2. 送電
3. 石油パイプライン
4. 水道パイプライン・下水道
5. 港湾
6. 公共交通車両

**100%外資参入が可能になったセクター**: 通信、鉄道、空港、高速道路、物流

> **投資上の注意**: PSE上場株の外国人持分上限は企業ごとに異なる。PSE EDGEで各社の「Foreign Ownership Limit」と現在の外国人持分比率を確認すること。

#### 会計基準（PFRS / IFRS）

- フィリピンはIFRSを**PFRS（Philippine Financial Reporting Standards）**として採用
- PFRSはIFRSとほぼ同等であり、国際比較が容易
- 3つのフレームワーク: PFRS（上場企業）、PFRS for SMEs（中規模企業）、PFRS for SEs（小規模企業）
- 決算期: 多くの企業が12月末決算。一部企業は3月末（Ayala等）

#### コングロマリット構造（財閥）

| 財閥グループ | 創業家 | 主要上場企業 | 主要セクター |
|-------------|--------|------------|------------|
| **SM Group** | Sy Family | SM, SMPH, BDO, CHIB | 不動産、銀行、小売 |
| **Ayala Group** | Zobel-Ayala Family | AC, ALI, BPI, GLO, ACEN | 不動産、銀行、通信、エネルギー |
| **JG Summit** | Gokongwei Family | JGS, URC, RLC, RRHI | 食品、不動産、航空、石化 |
| **Aboitiz Group** | Aboitiz Family | AEV, AP, UBP | 電力、銀行、食品、土地 |
| **San Miguel** | Cojuangco→Ang | SMC, Petron | エネルギー、インフラ、食品 |
| **MVP/First Pacific** | Pangilinan | TEL, MPI | 通信、インフラ、配電 |
| **AGI/Tan Group** | Andrew Tan | AGI, MEG, EMP | 不動産、酒類、カジノ |
| **GT Capital** | George Ty Family | GTCAP, MBT | 銀行、自動車、不動産 |
| **Villar Group** | Villar Family | VLL, AllHome | 不動産（手頃価格帯）、小売 |
| **DMCI Group** | Consunji Family | DMC, SCC | 建設、鉱業、電力、不動産 |
| **Razon Group** | Razon Family | ICT, BLOOM | 港湾、カジノ |

#### 通貨リスク（PHP）

- フィリピンペソ（PHP）は変動相場制（managed float）
- 2025年はUSD/PHPが55-58ペソ/ドルのレンジで推移
- OFW送金（2024年: USD 383.4億、GDP比約8.3%）がペソの下支え要因
- 米ドル金利差、地政学リスク、経常収支赤字が変動要因

#### OFW送金の経済的重要性

- 2024年のOFW個人送金: USD 383.4億（過去最高）。GDP比約8.3%
- 送金は個人消費（GDP の約70%）の重要な下支え
- 不動産需要（特にOFW家族向け住宅）の主要ドライバー
- BSPの送金統計は月次で公表（約2ヶ月遅れ）

#### 流動性の課題

- PSEiは30銘柄で構成だが、時価総額・売買代金の集中度が高い
- 中小型株は流動性が極めて低い
- 2025年は外国人のネット売越しが518億ペソに達し、流動性がさらに悪化
- フリーフロート比率が低い（財閥の持分が高い）銘柄が多い

#### その他の注意点

- **人口ボーナス**: 人口約1.17億人（2024年推計）、中央年齢約25歳。ASEAN最若年国の一つ
- **BPO（Business Process Outsourcing）**: 英語力を活かしたIT-BPM産業が成長
- **自然災害リスク**: 台風常襲地域。毎年20以上の台風が上陸/接近
- **税制**: CREATE法で法人税率が25%に引き下げ

---

### F.7 分析チェックリスト

```
□ マクロ環境
  - GDP成長率（PSA発表、四半期）
  - BSP政策金利の方向性（年8回の金融政策会合）
  - インフレ率（PSA月次CPI）
  - OFW送金トレンド（BSP月次統計）
  - PHP/USD為替レート推移

□ 市場環境
  - PSEi水準とバリュエーション（P/E、P/B）
  - 外国人ネット売買動向（PSE日次公表）
  - セクター別パフォーマンス
  - PSEi構成銘柄の入替（2月・8月リバランス）

□ 企業分析（共通）
  - 外国人持分上限と現在の外国人持分比率（PSE EDGE確認）
  - 支配株主（財閥）の持分比率と影響力
  - 関連当事者取引の規模と内容（年報の注記確認）
  - 監査法人（Big 4か否か: SGV/EY, Isla Lipana/PwC, KPMG, Deloitte）
  - 配当方針と配当利回り
  - 流動性（日次売買代金、フリーフロート比率）

□ コングロマリット固有
  - NAVディスカウント/プレミアムの計算
  - SOTP分析（各子会社の持分価値合計）
  - 子会社→親会社の配当フロー
  - 新規投資・M&A計画と資金調達方法

□ yfinanceティッカー形式: `{TICKER}.PS`（例: `SM.PS`, `BDO.PS`, `TEL.PS`）
```

---

## Appendix G: シンガポール市場 詳細リサーチガイド

### G.1 セクター概要

シンガポール証券取引所（SGX）はアジアの金融ハブとして、東南アジア最大級の株式市場を運営している。Straits Times Index（STI）は30銘柄で構成され、時価総額の約50%を3大銀行（DBS, OCBC, UOB）が占める。

#### 市場の主要特性

| 特性 | 内容 |
|------|------|
| 取引所 | Singapore Exchange（SGX） |
| 主要指数 | Straits Times Index（STI）、FTSE ST All-Share Index |
| 取引通貨 | SGD（シンガポールドル） |
| 取引時間 | 9:00-12:00, 13:00-17:00（SGT / UTC+8） |
| 決済 | T+2 |
| ティッカー形式 | `.SI`（例: `D05.SI`） |
| 開示言語 | 英語（標準） |
| 会計基準 | SFRS(I) = IFRSと同等 |
| REIT数 | 約40銘柄、時価総額S$1,000億超 |

#### セクター別構成

| セクター | 特徴 | STI構成比（概算） |
|---------|------|-----------------|
| 銀行・金融 | 3大銀行がSTIの約50%を占める | 50%超 |
| REIT | 約40銘柄、アジア最大のREIT市場の一つ | 15-20% |
| 通信 | Singtel中心。2025年にM1→Simba統合 | 5-8% |
| 不動産 | CapitaLand系、CDL、UOL等 | 8-10% |
| 海運・産業 | Keppel, Sembcorp, Yangzijiang等 | 8-10% |
| テクノロジー | SGX上場は限定的。Sea/GrabはNYSE/NASDAQ上場 | 3-5% |

---

### G.2 主要プレイヤーとティッカー

#### 銀行・金融

| 企業 | ティッカー | 時価総額帯 | 特徴 |
|------|----------|-----------|------|
| **DBS Group** | D05.SI | Mega Cap（S$1,500億超） | 東南アジア最大の銀行。SGX最大の上場企業。Wealth Management、デジタルバンキングに強い |
| **OCBC** | O39.SI | Large Cap | 3行中で保険事業（Great Eastern）に強み。AUM成長が顕著 |
| **UOB** | U11.SI | Large Cap（S$580億） | ASEAN展開に積極的。Citiのリテール買収でASEANプレゼンス拡大 |
| **SGX** | S68.SI | Large Cap | 取引所運営会社。デリバティブ取引に強み |

> **注**: DBS, OCBC, UOBの3行合計時価総額はS$1,800億超で、STIの約50%を占める。

#### S-REIT（シンガポール不動産投資信託）

**商業・オフィスREIT**

| REIT | ティッカー | スポンサー | 特徴 |
|------|----------|----------|------|
| **CapitaLand Integrated Commercial Trust (CICT)** | C38U.SI | CapitaLand Investment | SGX最大のREIT。S$259億ポートフォリオ |
| **Mapletree Pan Asia Commercial Trust (MPACT)** | N2IU.SI | Mapletree Investments | VivoCity、Mapletree Business City等 |
| **Suntec REIT** | T82U.SI | ARA Asset Management | Suntec City、Marina Bay中心 |
| **Keppel REIT** | K71U.SI | Keppel | シンガポールCBD中心のプレミアムオフィス |

**産業・物流REIT**

| REIT | ティッカー | スポンサー | 特徴 |
|------|----------|----------|------|
| **CapitaLand Ascendas REIT** | A17U.SI | CapitaLand Investment | シンガポール最大の産業REIT。米国・欧州にも展開 |
| **Mapletree Industrial Trust** | ME8U.SI | Mapletree Investments | データセンター比率が高い。北米展開 |
| **Mapletree Logistics Trust** | M44U.SI | Mapletree Investments | アジア太平洋地域の物流施設 |

**データセンターREIT**

| REIT | ティッカー | スポンサー | 特徴 |
|------|----------|----------|------|
| **Keppel DC REIT** | AJBU.SI | Keppel | アジア初のデータセンター特化REIT |
| **Digital Core REIT** | DCRU.SI | Digital Realty | 世界最大のDC事業者がスポンサー |

**ヘルスケアREIT**

| REIT | ティッカー | スポンサー | 特徴 |
|------|----------|----------|------|
| **Parkway Life REIT (PLife)** | C2PU.SI | IHH Healthcare | シンガポールの病院、日本の介護施設。ディフェンシブ銘柄 |

**ホスピタリティREIT**

| REIT | ティッカー | スポンサー | 特徴 |
|------|----------|----------|------|
| **CDL Hospitality Trusts** | J85.SI | City Developments | シンガポール、日本、欧州等のホテル |
| **Far East Hospitality Trust** | Q5T.SI | Far East Organization | シンガポール中心 |
| **Ascott Residence Trust** | HMN.SI | CapitaLand Investment | 世界15カ国以上に展開 |

#### 通信

| 企業 | ティッカー | 時価総額帯 | 特徴 |
|------|----------|-----------|------|
| **Singtel** | Z74.SI | Large Cap | シンガポール最大の通信会社。Optus（豪州）、地域テレコムへの出資（Airtel, AIS, Globe等） |
| **StarHub** | CC3.SI | Mid Cap | 2025年にMyRepublic買収。配当利回り約5.6% |
| **NetLink NBN Trust** | CJLU.SI | Mid Cap | シンガポールの光ファイバーインフラ所有・運営。規制収益モデル |

> **注**: 2025年にSimba（M1を統合）が誕生し、Singtel、Simba（Keppel系）、StarHubの3社体制に再編。

#### 不動産

| 企業 | ティッカー | 時価総額帯 | 特徴 |
|------|----------|-----------|------|
| **CapitaLand Investment (CLI)** | 9CI.SI | Large Cap | アジア最大級の不動産投資マネジャー。AUM S$1,000億超 |
| **City Developments (CDL)** | C09.SI | Large Cap | シンガポール最大級のデベロッパー |
| **UOL Group** | U14.SI | Mid-Large Cap | UOB系の不動産会社 |
| **Hongkong Land** | H78.SI | Large Cap | Jardine Matheson系 |
| **Frasers Property** | TQ5.SI | Mid Cap | タイCharoen Pokphand系 |

#### 海運・産業コングロマリット

| 企業 | ティッカー | 時価総額帯 | 特徴 |
|------|----------|-----------|------|
| **Keppel** | BN4.SI | Large Cap | 資産運用・インフラ・データセンター・不動産に再編 |
| **Sembcorp Industries** | U96.SI | Large Cap | エネルギー・都市開発。再生可能エネルギーに注力 |
| **Yangzijiang Shipbuilding** | BS6.SI | Large Cap | 中国ベースの造船会社。コンテナ船の受注好調 |
| **Seatrium** | 5E2.SI | Large Cap | 海洋エンジニアリング |
| **Jardine Matheson** | J36.SI | Large Cap | アジア最大級のコングロマリット |
| **Wilmar International** | F34.SI | Large Cap | 世界最大のパーム油トレーダー |

#### テクノロジー

| 企業 | ティッカー | 上場市場 | 特徴 |
|------|----------|---------|------|
| **Sea Limited** | SE | NYSE | シンガポール本社。Shopee（EC）、Garena（ゲーム）、SeaMoney（フィンテック） |
| **Grab Holdings** | GRAB | NASDAQ | シンガポール本社。配車・デリバリー・フィンテック |
| **Venture Corporation** | V03.SI | SGX | エレクトロニクスEMS |
| **AEM Holdings** | AWX.SI | SGX | 半導体テスト機器 |

> **注**: Sea LimitedとGrabはシンガポール本社だがNYSE/NASDAQ上場。SGX上場のテック企業は限定的。

---

### G.3 規制当局・政府機関

| 機関 | 役割 | 公開データ | URL |
|------|------|----------|-----|
| **MAS**（金融管理局） | 中央銀行機能 + 金融規制当局。金融政策（S$NEER管理） | 金融政策声明、銀行統計、REIT規則 | https://www.mas.gov.sg |
| **SGX RegCo** | SGXの規制部門。上場規則の執行 | 上場規則、執行措置、規制ガイダンス | https://www.sgx.com/regulation |
| **ACRA**（会計企業規制庁） | 企業登記・会計基準監督 | 企業登記情報、会計基準（SFRS） | https://www.acra.gov.sg |
| **SingStat**（統計局） | 国家統計機関 | GDP、CPI、貿易統計、住宅価格指数 | https://www.singstat.gov.sg |
| **MTI**（通商産業省） | 経済政策立案 | 経済調査・見通し、産業政策 | https://www.mti.gov.sg |
| **IMDA**（情報通信メディア開発庁） | 通信・メディア規制 | 通信統計、デジタル経済フレームワーク（GDP比18.6%） | https://www.imda.gov.sg |
| **URA**（都市再開発庁） | 都市計画、不動産規制（ABSD等） | 不動産価格指数、取引データ | https://www.ura.gov.sg |

#### 開示プラットフォーム

| システム | 内容 | URL |
|---------|------|-----|
| **SGXNet** | 上場企業の法定開示プラットフォーム | https://www.sgx.com/sgxnet |
| **SGX Company Announcements** | 企業発表の検索・閲覧 | https://www.sgx.com/securities/company-announcements |
| **SGX RuleBook** | 上場規則 | https://rulebook.sgx.com |

---

### G.4 セクター固有KPIと取得方法

#### 銀行セクター

| KPI | 定義 | データソース | 重要度 |
|-----|------|------------|--------|
| **NIM** | 純利鞘。2024年平均約2.1% | 各行四半期決算 | ★★★★★ |
| **NPL Ratio** | DBS 1.1%, OCBC 0.9%, UOB 1.5%（2024年末） | 各行四半期決算 | ★★★★★ |
| **CET1 Ratio** | 3行平均15.3%（2024年末） | 各行四半期決算、MAS | ★★★★★ |
| **ROE** | 自己資本利益率 | 各行四半期決算 | ★★★★★ |
| **Fee Income** | ウェルスマネジメント、投資銀行、トレーディング | 各行四半期決算 | ★★★★☆ |
| **Wealth Management AUM** | ウェルスマネジメント運用資産残高 | 各行四半期決算 | ★★★★☆ |
| **Cost-to-Income Ratio** | 経費率 | 各行四半期決算 | ★★★★☆ |
| **Dividend Payout Ratio** | 配当性向 | 各行決算 | ★★★★☆ |

#### S-REIT セクター

| KPI | 定義 | データソース | 重要度 |
|-----|------|------------|--------|
| **DPU**（Distribution Per Unit） | ユニットあたり分配金 | 各REIT半期/四半期決算 | ★★★★★ |
| **Distribution Yield** | 分配利回り | 各REIT決算、市場データ | ★★★★★ |
| **NAV per Unit** | ユニットあたり純資産価値 | 各REIT決算 | ★★★★★ |
| **Gearing Ratio** | 総借入/総資産。上限50%（MAS規制） | 各REIT四半期決算 | ★★★★★ |
| **ICR**（Interest Coverage Ratio） | 最低1.5倍（MAS規制） | 各REIT四半期決算 | ★★★★★ |
| **WALE** | 加重平均リース残存期間（年） | 各REIT四半期決算 | ★★★★☆ |
| **Occupancy Rate** | 稼働率 | 各REIT四半期決算 | ★★★★★ |
| **NPI**（Net Property Income） | 純不動産収入 | 各REIT四半期決算 | ★★★★★ |
| **Rental Reversion** | リース更新時の賃料改定率 | 各REIT四半期決算 | ★★★★☆ |
| **Sponsor Pipeline** | スポンサーからの取得可能資産 | 各REIT投資家プレゼン | ★★★★☆ |
| **P/NAV** | プレミアム/ディスカウント | 市場データ | ★★★★☆ |

#### 不動産セクター

| KPI | 定義 | データソース | 重要度 |
|-----|------|------------|--------|
| **ASP**（Average Selling Price） | 平均販売単価（PSF） | URA取引データ、各社決算 | ★★★★★ |
| **Launch Sales** | 新規プロジェクト販売状況 | URA月次データ | ★★★★★ |
| **Unsold Inventory** | 未販売在庫 | URA四半期データ | ★★★★☆ |
| **GLS**（Government Land Sales） | 政府土地売却 | URA/HDB | ★★★★☆ |
| **Private Residential Price Index** | 民間住宅価格指数 | URA四半期 | ★★★★★ |

#### 海運・造船セクター

| KPI | 定義 | データソース | 重要度 |
|-----|------|------------|--------|
| **Order Book** | 受注残高（隻数・金額） | 各社四半期決算 | ★★★★★ |
| **Utilization Rate** | 設備稼働率 | 各社四半期決算 | ★★★★☆ |
| **Gross Margin** | 粗利率 | 各社四半期決算 | ★★★★★ |
| **Delivery Schedule** | 引渡しスケジュール | 各社投資家プレゼン | ★★★★☆ |

---

### G.5 情報ソース

#### ニュース・メディア

| メディア | 言語 | 特徴 | URL |
|---------|------|------|-----|
| **The Straits Times** | 英語 | シンガポール最大の日刊紙 | https://www.straitstimes.com |
| **The Business Times** | 英語 | 東南アジアを代表する金融日刊紙 | https://www.businesstimes.com.sg |
| **CNA**（Channel NewsAsia） | 英語 | 24時間ニュース放送 | https://www.channelnewsasia.com |
| **The Edge Singapore** | 英語 | 投資・ビジネス週刊誌 | https://www.theedgesingapore.com |
| **NextInsight** | 英語 | 個人投資家向けメディア | https://www.nextinsight.net |
| **The Smart Investor** | 英語 | SGX関連の投資教育・分析 | https://thesmartinvestor.com.sg |
| **SGinvestors.io** | 英語 | SGX上場銘柄の情報集約プラットフォーム | https://sginvestors.io |

#### 業界リサーチ

| 証券会社 | 特徴 | アクセス方法 |
|---------|------|-------------|
| **DBS Vickers / DBS Research** | SGX銘柄の最も包括的なカバレッジ | DBS口座開設、一部無料公開 |
| **OCBC Investment Research** | 銀行・REIT分析に強い | OCBC口座、一部無料 |
| **UOB Kay Hian** | ASEAN全域をカバー | 口座開設 |
| **CGS International** | 東南アジア全域 | 口座開設 |
| **Phillip Securities** | リテール投資家向け | PhillipCapital口座 |

#### S-REIT 専門データソース

| ソース | 特徴 | URL |
|--------|------|-----|
| **REITAS** | S-REIT業界団体 | https://www.reitas.sg |
| **S-REIT Data（Fifth Person）** | S-REITの日次更新データ | https://sreit.fifthperson.com |
| **REITDATA** | S-REITの詳細データベース | https://reitdata.com |
| **REITsWeek** | S-REITの週次分析 | https://www.reitsweek.com |

#### 不動産市場データ

| ソース | 特徴 | URL |
|--------|------|-----|
| **URA REALIS** | URA公式の不動産取引データ（有料） | https://www.ura.gov.sg/reis/index |
| **URA Statistics** | 不動産統計 | https://www.ura.gov.sg/property-market-information |
| **EdgeProp** | 不動産価格・取引データポータル | https://www.edgeprop.sg |

#### 投資家プレゼンテーション取得先

| 企業 | IR URL | 決算の特徴 |
|------|--------|-----------|
| **DBS Group** | https://www.dbs.com/investor | 四半期決算。NIM、Fee Income、Wealth AUMの詳細 |
| **OCBC** | https://www.ocbc.com/group/investors | 四半期決算。Great Eastern保険事業のセグメント |
| **UOB** | https://www.uobgroup.com/investor-relations | 四半期決算。ASEAN地域別セグメント |
| **Singtel** | https://www.singtel.com/about-us/investor-relations | 半期決算。地域テレコム出資先の持分法損益 |
| **CapitaLand Investment** | https://www.capitalandinvest.com/investor-relations | 半期決算。AUM成長、Fee-Related Earnings |
| **CICT** | https://www.cict.com.sg/investor-relations | 半期決算。DPU、Occupancy、WALE、Rental Reversion |
| **Keppel DC REIT** | https://www.keppeldcreit.com/en/investor-relations | 半期決算。DC稼働率、電力コスト |

---

### G.6 シンガポール固有の注意点

#### S-REIT制度の詳細

S-REITはシンガポール市場の最大の差別化要因であり、約40銘柄、時価総額S$1,000億超。

**税制優遇**

| 項目 | 内容 |
|------|------|
| **税透過性** | 課税所得の90%以上を分配すれば、REIT法人レベルでは非課税 |
| **個人投資家（非居住者）** | 分配金に10%源泉徴収（2025年12月末まで軽減措置） |
| **法人投資家** | 通常の法人税率（17%）で課税 |

**レバレッジ規制（MAS）**

| 規制項目 | 内容 |
|---------|------|
| **Aggregate Leverage Limit** | 総資産の**50%**が上限 |
| **ICR** | 最低**1.5倍** |

**スポンサー制度**

| 項目 | 内容 |
|------|------|
| **スポンサーの役割** | 資産パイプライン提供、経営支援、ブランド信用力 |
| **主要スポンサー** | CapitaLand Investment（7 REIT）、Mapletree Investments（3 REIT）、Frasers Property（2 REIT）、Keppel（3 REIT） |

**S-REIT分析フレームワーク**

```
□ 収益安定性
  - Occupancy Rate（> 90%が目安）
  - WALE（3年以上が望ましい）
  - テナント集中度（トップ10テナントの占有率）
  - Rental Reversion（正のリバージョンが望ましい）

□ 財務健全性
  - Gearing Ratio（< 40%が保守的、> 45%は注意）
  - ICR（> 2.5倍が望ましい）
  - 固定金利比率（> 70%が理想的）
  - Weighted Average Debt Maturity（3年以上が望ましい）

□ 成長ポテンシャル
  - スポンサーパイプラインの規模
  - AEI（Asset Enhancement Initiative）計画
  - 海外展開の多様化

□ バリュエーション
  - Distribution Yield vs 10年SGS利回り（スプレッド）
  - P/NAV（プレミアム/ディスカウント）
  - 同セクターREITとのYield比較
```

#### 政府系企業（GLC）の影響力

| 投資会社 | 運用資産 | 主要保有企業（SGX上場） |
|---------|---------|---------------------|
| **Temasek Holdings** | US$2,880億超（2024年） | DBS（29%）, Singtel（52%）, Keppel, Sembcorp, ST Engineering |
| **GIC** | US$7,440億超（2022年推定） | 直接的なSGX大量保有は限定的（非開示方針） |

- Temasek系GLCは**SGX時価総額の約25%**を占める
- GLCは非GLC企業と比べて**バリュエーションプレミアム**が認められる傾向

#### 外国人投資制限

シンガポールは基本的に**オープンな投資環境**。

| セクター | 制限内容 |
|---------|---------|
| **銀行** | MASの承認なく銀行株の5%超取得不可 |
| **メディア** | 外国人持分に制限 |
| **不動産（住居用）** | 外国人のHDB購入不可。ABSD（追加買主印紙税）が課される |
| **その他上場株** | 原則として制限なし |

#### 不動産クーリングメジャー（ABSD等）

**ABSD（Additional Buyer's Stamp Duty）**

| 買主区分 | 1件目 | 2件目 | 3件目以降 |
|---------|------|------|---------|
| シンガポール市民 | 0% | 20% | 30% |
| 永住権保有者（SPR） | 5% | 30% | 35% |
| **外国人** | **60%** | 60% | 60% |

> **注**: 2023年4月の改定で外国人のABSDが30%→60%に倍増。

**その他の規制**

| 規制 | 内容 |
|------|------|
| **TDSR** | 月間債務返済額が月収の55%を超えてはならない |
| **LTV** | 初回住宅ローン: 75% |
| **SSD** | 購入後3年以内の売却に課税 |

#### SGDの安定性とMASの金融政策

MASは世界でもユニークな**為替レートベースの金融政策**を採用。

| 項目 | 内容 |
|------|------|
| **政策ツール** | S$NEER（名目実効為替レート）のバンド管理 |
| **BBCフレームワーク** | Basket（通貨バスケット）、Band（変動許容幅）、Crawl（緩やかな増価トレンド） |
| **政策レビュー** | 年2回（通常4月・10月） |
| **SGDの特性** | 長期的に緩やかな増価トレンド。為替リスクは他の新興国通貨より低い |

#### 会計基準

| 項目 | 内容 |
|------|------|
| **基準名** | SFRS(I)（Singapore Financial Reporting Standards - International） |
| **IFRSとの互換性** | 実質的に同等 |
| **銀行固有** | MASが銀行向けに貸倒引当金の修正要件を発行 |

---

### G.7 分析チェックリスト

#### シンガポール株 共通チェックリスト

```
□ 企業概要
  - GLC（政府系）か否か。Temasek/GIC持分の確認
  - 海外売上比率（シンガポール以外のエクスポージャー）

□ 財務分析
  - 過去5年の売上・利益トレンド
  - ROE、ROA
  - 配当政策と配当利回り
  - キャッシュフロー推移

□ バリュエーション
  - P/E、P/B、EV/EBITDA
  - 配当利回り vs SGS（シンガポール国債）利回り

□ ガバナンス
  - 独立取締役比率
  - 関連当事者取引の有無・規模
  - SGXコーポレートガバナンスコード準拠状況

□ リスク要因
  - SGD為替リスク
  - 金利環境（MAS政策、米金利との連動）
  - 地政学リスク（米中関係、ASEAN地域リスク）
```

#### S-REIT 詳細分析チェックリスト

```
□ ポートフォリオ品質
  - 資産タイプ（オフィス/リテール/産業/DC/ヘルスケア等）
  - 地理的分散（シンガポール比率、海外資産の通貨リスク）
  - テナントプロファイル

□ 収益安定性
  - Occupancy Rate（過去4四半期トレンド）
  - WALE（By NLA and By Gross Revenue）
  - Rental Reversion

□ 財務健全性
  - Gearing Ratio（< 40%: 保守的、> 45%: 注意）
  - ICR（> 2.5x: 良好）
  - Fixed Rate Debt比率（> 70%: 良好）
  - Weighted Average Debt Maturity（> 3年: 良好）

□ 成長戦略
  - スポンサーパイプライン
  - AEI計画と過去のROI

□ バリュエーション
  - Distribution Yield vs セクター平均
  - Distribution Yield vs 10年SGS利回り（スプレッド）
  - P/NAV
  - DPU成長率トレンド

□ 金利感応度
  - MASの金融政策方向性
  - 変動金利借入の比率
  - 金利1%上昇時のDPUへの影響
```

#### 銀行セクター分析チェックリスト

```
□ 収益構造
  - NIMトレンドと方向性
  - Fee Income構成（Wealth Management, Trade Finance等）
  - Non-Interest Income / Total Income比率

□ 資産品質
  - NPL Ratioトレンド
  - NPL Coverage Ratio（> 100%が望ましい）
  - セクター別・地域別のNPL内訳

□ 資本・自己資本
  - CET1 Ratio（> 13%: 良好）
  - 配当政策（Payout Ratio、特別配当の有無）
  - 自社株買い計画

□ 地域展開
  - ASEAN展開
  - 中国・香港エクスポージャー

□ 競争環境
  - デジタルバンク（GrabとSeaがライセンス取得済）
  - Wealth Management競争
```

#### 参考リンク集

| カテゴリ | URL |
|---------|-----|
| SGX | https://www.sgx.com |
| MAS | https://www.mas.gov.sg |
| SingStat | https://www.singstat.gov.sg |
| URA | https://www.ura.gov.sg |
| SGXNet | https://www.sgx.com/sgxnet |
| REITAS | https://www.reitas.sg |
| S-REIT Data | https://sreit.fifthperson.com |
| SGinvestors.io | https://sginvestors.io |
| The Business Times | https://www.businesstimes.com.sg |
| CNA | https://www.channelnewsasia.com |

---

## Appendix H: ベトナム市場 詳細リサーチガイド

### H.1 セクター概要

ベトナム株式市場はホーチミン証券取引所（HOSE）とハノイ証券取引所（HNX）で構成され、統括組織としてベトナム証券取引所（VNX）が存在する。2025年10月にFTSE Russellがベトナムをフロンティア市場からSecondary Emerging Market（新興市場）へ格上げすることを発表し、2026年9月21日から正式に反映される予定。これにより、USD 50-70億規模の外国資本流入が見込まれている。

VN-Indexは2026年2月時点で約1,754ポイント前後で推移。市場時価総額は約2,880億USDに達し、年間成長率は約7.89%。2026年のVN-Index目標は1,920ポイント、EPS成長率14.5%が見込まれており、2026年フォワードP/E 12.7倍はヒストリカル平均を下回る。

#### 主要セクター構成

| セクター | 特徴 | 時価総額ウェイト |
|---------|------|---------------|
| **銀行** | VN-Index最大セクター。国有銀行3行+民間銀行群。Basel II/III移行中 | 約30-35% |
| **不動産** | 2024年新土地法施行で回復基調。法的承認の遅延が構造的課題 | 約10-15% |
| **テクノロジー/IT** | FPT Corpが圧倒的。AIブーム・半導体参入で成長加速 | 約5-8% |
| **製造業** | 鉄鋼（Hoa Phat）、乳業（Vinamilk）等。輸出依存度高い | 約8-10% |
| **ユーティリティ/エネルギー** | PV Gas、REE Corp等。再生可能エネルギーへの転換進行中 | 約5-8% |
| **航空** | VietJet Air（LCC）とVietnam Airlines（FSC）の2社体制 | 約3-5% |
| **証券** | SSI、VNDirect、HSC等。市場活況時に業績レバレッジ | 約3-5% |
| **消費財** | 小売・食品。国内消費拡大に連動 | 約5-7% |

#### 経済概況（2025-2026）

- GDP成長率: 2025年上期7.5%（過去10年超で最高）
- 製造業: FDI（外国直接投資）流入が堅調、特にサムスン・LG等韓国企業の集積
- 人口: 約1億人、若年層比率が高い（メディアンエイジ約31歳）
- 一人当たりGDP: 約4,500 USD（中所得国トラップ回避が課題）

### H.2 主要プレイヤーとティッカー

#### H.2.1 銀行セクター

| 企業名 | ティッカー | 取引所 | 時価総額帯 | 所有形態 | 特徴 |
|--------|----------|--------|----------|---------|------|
| Vietcombank | VCB | HOSE | Large Cap | 国有 | 最大手。外銀パートナーシップ（みずほ15%）。高いブランド力。CAR 12%。CASA 34.8% |
| VietinBank | CTG | HOSE | Large Cap | 国有 | 第2位。三菱UFJ 19.73%出資。リテール・法人バランス型 |
| BIDV | BID | HOSE | Large Cap | 国有 | 第3位。韓国ハナ銀行15%出資。総資産最大。地方ネットワーク広い |
| Techcombank | TCB | HOSE | Large Cap | 民間 | CASA比率36.5%で業界トップクラス。手数料収入比率高い。ビングループ関連 |
| MB Bank | MBB | HOSE | Large Cap | 民間 | 軍系出身。CASA比率36.5%。バンカシュアランス成長。デジタルバンキング注力 |
| VP Bank | VPB | HOSE | Large Cap | 民間 | コンシューマーファイナンス子会社FE Credit保有。SMFG 15%出資。リテール強い |
| ACB | ACB | HOSE | Large Cap | 民間 | リテール特化。堅実経営。不動産エクスポージャー低い |
| HDBank | HDB | HOSE | Mid Cap | 民間 | ベトマムアビエーション（VJC）関連。消費者金融HD SAISON保有 |
| SHB | SHB | HOSE | Mid Cap | 民間 | 中小企業・個人向け。アグレッシブな成長戦略 |
| TPBank | TPB | HOSE | Mid Cap | 民間 | デジタルバンキング先駆者。LiveBankブランド |
| VIB | VIB | HOSE | Mid Cap | 民間 | リテール・自動車ローン特化。CBA 20%出資 |
| OCB | OCB | HOSE | Mid Cap | 民間 | 青山グループ（日系）15%出資 |
| Sacombank | STB | HOSE | Mid Cap | 民間 | 経営再建進展中。不良債権処理が焦点 |

> **注**: 国有3行（VCB, CTG, BID）は政府持分が50%超。SBVの信用成長率上限に直接影響を受ける。

#### H.2.2 不動産セクター

| 企業名 | ティッカー | 取引所 | 時価総額帯 | 特徴 |
|--------|----------|--------|----------|------|
| Vinhomes | VHM | HOSE | Large Cap | ベトナム最大手住宅デベロッパー。Vingroup子会社。広大な土地バンク。Royal Island・Wonder City等大型プロジェクト |
| Vingroup | VIC | HOSE | Large Cap | ベトナム最大コングロマリット。不動産・自動車（VinFast）・リテール・ヘルスケア・教育 |
| Novaland | NVL | HOSE | Mid Cap | 債務再構築中。Aqua City等大型プロジェクトの法的承認が進展。回復途上 |
| Khang Dien House | KDH | HOSE | Mid Cap | ホーチミン市東部に特化。タウンシップ開発。堅実な財務 |
| Dat Xanh Group | DXG | HOSE | Mid Cap | 不動産仲介+開発。南部地域に強い |
| Nam Long | NLG | HOSE | Mid Cap | 手頃な価格帯の住宅に特化。日系パートナー（阪急阪神）と提携 |
| Phat Dat Real Estate | PDR | HOSE | Mid Cap | 産業用不動産・住宅開発。中部・南部 |
| Becamex IDC | BCM | HOSE | Mid Cap | ビンズオン省の産業団地開発。FDI流入の恩恵 |

#### H.2.3 テクノロジー/IT セクター

| 企業名 | ティッカー | 取引所 | 時価総額帯 | 特徴 |
|--------|----------|--------|----------|------|
| FPT Corporation | FPT | HOSE | Large Cap | ベトナム最大IT企業。ITサービス・通信・教育の3事業。海外IT売上VND 35兆超（前年比+15%）。AI・半導体に参入。2030年までにグローバルDXトップ50目標 |
| CMC Corporation | CMG | HOSE | Mid Cap | ITインフラ・ソリューション・グローバル事業・教育の4セグメント。SIerとして国内トップ2。Samsung SDS提携 |
| Viettel Group | 非上場 | - | - | 軍系通信最大手。アフリカ・東南アジアに事業展開。IT子会社が急成長 |

> **注**: FPTはベトナムIT株の代名詞。半導体テスト・パッケージング工場（2026年1月発表）により半導体関連銘柄としても注目。

#### H.2.4 製造業セクター

| 企業名 | ティッカー | 取引所 | 時価総額帯 | セクター | 特徴 |
|--------|----------|--------|----------|---------|------|
| Hoa Phat Group | HPG | HOSE | Large Cap | 鉄鋼 | ベトナム最大鉄鋼メーカー。Dung Quat製鉄所（年産800万トン）。国内鉄鋼価格に業績連動。時価総額VND 206兆 |
| Vinamilk | VNM | HOSE | Large Cap | 乳業 | ベトナム最大乳業。国内シェア50%超。海外展開（中東・東南アジア）。配当利回り高い。時価総額VND 145兆 |
| Hoa Sen Group | HSG | HOSE | Mid Cap | 鉄鋼・建材 | 鋼板・屋根材。輸出比率高い |
| Masan Group | MSN | HOSE | Large Cap | コングロマリット | 食品（Masan Consumer）・鉱業（Masan High-Tech Materials, タングステン世界大手）・小売（WinMart, VinCommerce買収） |
| Petrovietnam系 | 複数 | HOSE/HNX | 各種 | 石油・ガス | PVD（掘削）, PVS（サービス）, BSR（精製）, OIL（探査・開発） |

#### H.2.5 ユーティリティ/エネルギーセクター

| 企業名 | ティッカー | 取引所 | 時価総額帯 | 特徴 |
|--------|----------|--------|----------|------|
| PV Gas | GAS | HOSE | Large Cap | ベトナム最大ガス企業。ペトロベトナム子会社。P/E 12.4倍。EV/EBITDA 5.9倍。時価総額VND 145兆 |
| PV Power | POW | HOSE | Mid Cap | ペトロベトナム系発電。ガスタービン中心。Siemens・GE・東芝製設備。再エネ転換中 |
| REE Corporation | REE | HOSE | Mid Cap | 多角化ユーティリティ。水力・風力・太陽光発電ポートフォリオ（総容量2,845MW、国内設備容量の約3.3%）。火力からの撤退を推進 |
| PetroVietnam | 非上場 | - | - | 国営石油・ガス企業。多数の上場子会社を保有 |

#### H.2.6 航空セクター

| 企業名 | ティッカー | 取引所 | 時価総額帯 | 特徴 |
|--------|----------|--------|----------|------|
| VietJet Air | VJC | HOSE | Large Cap | ベトナム最大LCC。国内線シェア首位級。国際線拡大中（豪州・インド等）。時価総額VND 98兆 |
| Vietnam Airlines | HVN | HOSE | Mid Cap | フラッグキャリア。国有。債務再構築後の回復途上。時価総額VND 73兆 |
| Bamboo Airways | QH | 非上場 | - | FLC Group系列。経営難。再編中 |

#### H.2.7 証券セクター

| 企業名 | ティッカー | 取引所 | 時価総額帯 | 特徴 |
|--------|----------|--------|----------|------|
| SSI Securities | SSI | HOSE | Large Cap | 最大手証券。資本金VND 19.6兆。リサーチ充実。外国人顧客に強い |
| VNDirect Securities | VND | HOSE | Large Cap | 資本金VND 15.2兆。リテール・リサーチ充実 |
| Techcom Securities | TCBS | HOSE | Large Cap | Techcombank系列。債券引受トップ。資本金VND 19.6兆 |
| Ho Chi Minh City Securities | HCM | HOSE | Mid Cap | HSCブランド。外国機関投資家に強い |
| Vietcap Securities | VCI | HOSE | Mid Cap | 投資銀行・リサーチに強み |
| MB Securities | MBS | HOSE | Mid Cap | MB Bank系列 |
| VPS Securities | VPS | HNX | Mid Cap | 市場シェア上位。リテール強い |

### H.3 規制当局・政府機関

| 機関 | 英語名 | 役割 | 公開データ | URL |
|------|--------|------|----------|-----|
| **SSC** | State Securities Commission | 証券市場の監督・規制。ライセンス発行、開示規制、市場監視 | 規制通達、開示書類、市場統計 | https://ssc.gov.vn |
| **HOSE** | Ho Chi Minh Stock Exchange | 株式・ETFの上場・取引。大型株中心 | 株価データ、開示書類、指数情報 | https://www.hsx.vn |
| **HNX** | Hanoi Stock Exchange | 債券・デリバティブ取引（株式はHOSEに統合予定）。中小型株 | 債券データ、デリバティブ | https://hnx.vn |
| **VNX** | Vietnam Exchange | HOSE・HNXの統括組織。100%国有 | 市場統合情報 | https://vnx.vn |
| **SBV** | State Bank of Vietnam | 中央銀行。金融政策、為替管理、信用成長率上限設定、銀行監督 | 金利、為替レート、M2、信用成長率 | https://www.sbv.gov.vn |
| **GSO** | General Statistics Office | 統計総局（MPI傘下）。経済統計の公式ソース | GDP、CPI、工業生産、貿易統計、人口 | https://www.gso.gov.vn |
| **MPI** | Ministry of Planning and Investment | 計画投資省。FDI認可、経済計画 | FDI統計、投資環境レポート | https://www.mpi.gov.vn |
| **MOF** | Ministry of Finance | 財務省。税制、国有企業管理、会計基準 | 財政データ、国有企業情報 | https://www.mof.gov.vn |
| **MOIT** | Ministry of Industry and Trade | 商工省。産業政策、貿易管理、エネルギー | 産業統計、貿易データ | https://moit.gov.vn |
| **VSDC** | Vietnam Securities Depository and Clearing Corporation | 証券の保管・決済・清算 | 決済データ | https://www.vsd.vn |

#### 主要公開データ

| データ | 発行元 | 頻度 | 内容 | 重要度 |
|-------|--------|------|------|--------|
| 信用成長率（Credit Growth） | SBV | 月次/四半期 | 各銀行への信用上限配分を含む。銀行株に直接影響 | ★★★★★ |
| CPI（消費者物価指数） | GSO | 月次 | SBVの金融政策判断材料 | ★★★★☆ |
| GDP成長率 | GSO | 四半期 | 経済成長率。政府目標との乖離に注目 | ★★★★☆ |
| FDI登録額・実行額 | MPI | 月次 | 外国直接投資の動向。製造業セクターに影響 | ★★★★☆ |
| PMI（購買担当者景気指数） | S&P Global | 月次 | 製造業の景況感 | ★★★★☆ |
| 貿易収支 | GSO/税関 | 月次 | 輸出入データ。輸出依存型企業の先行指標 | ★★★☆☆ |
| 為替レート（USD/VND） | SBV | 日次 | 中心レート+/-5%バンド。通貨リスク管理 | ★★★★★ |

### H.4 セクター固有KPIと取得方法

#### H.4.1 銀行セクター

| KPI | 定義 | データソース | 重要度 | 備考 |
|-----|------|------------|--------|------|
| **NIM** (Net Interest Margin) | 純金利マージン | 四半期決算 | ★★★★★ | 2025年1Q: 業界平均3.31%（2019年以来最低）。低金利環境で圧縮傾向 |
| **NPL** (Non-Performing Loan Ratio) | 不良債権比率 | 四半期決算、SBV | ★★★★★ | 公式NPL + 要注意債権 + VAMC売却分の「実質NPL」を確認すること |
| **CASA** (Current Account Savings Account) | 要求払預金比率 | 四半期決算 | ★★★★★ | 調達コスト優位性の指標。TCB 36.5%、MBB 36.5%、VCB 34.8%がトップ |
| **CAR** (Capital Adequacy Ratio) | 自己資本比率 | 年次報告、半期 | ★★★★☆ | Basel II基準への移行完了。Basel III移行中。VCBは12%達成 |
| **CIR** (Cost-to-Income Ratio) | 経費率 | 四半期決算 | ★★★★☆ | 効率性指標。デジタルバンキング投資による一時的上昇に注意 |
| **ROE** | 自己資本利益率 | 四半期/年次 | ★★★★★ | 上位行15-25%。国有行はやや低い傾向 |
| **信用成長率** (Credit Growth) | 貸出金増加率 | SBV、各行決算 | ★★★★★ | SBVが各行に年間上限を割当。2026年目標15%。上限撤廃の動きあり |
| **引当率** (Provision Coverage) | 不良債権引当金/NPL | 四半期決算 | ★★★★☆ | VCBは200%超と突出 |
| **VAMC残高** | 資産管理会社への売却不良債権 | 年次報告 | ★★★★☆ | オフバランスの実質NPL把握に必須 |

> **SBV信用成長率管理**: SBVは各銀行に年間の信用成長率上限を割り当て、上半期に一部、下半期に追加枠を付与する。2025年は16%上限だったが、2026年から上限撤廃の方向（効率性・持続性ベースの新フレームワークへ移行）。

#### H.4.2 不動産セクター

| KPI | 定義 | データソース | 重要度 | 備考 |
|-----|------|------------|--------|------|
| **Pre-sales** | 引渡前販売額・戸数 | 四半期決算、投資家プレゼン | ★★★★★ | 将来の売上認識の先行指標 |
| **未販売在庫** (Unsold Inventory) | 販売可能な在庫戸数 | 四半期決算 | ★★★★☆ | 在庫回転率と併せて確認 |
| **土地バンク** (Land Bank) | 開発用土地面積 | 年次報告、投資家プレゼン | ★★★★★ | Vinhomes（VHM）が圧倒的。法的承認状況の確認が必須 |
| **法的承認状況** | プロジェクトの許認可取得状況 | 決算説明会、ニュース | ★★★★★ | ベトナム不動産最大のボトルネック。1/50許可、建設許可、販売許可等の進捗 |
| **粗利益率** | 売上総利益率 | 四半期決算 | ★★★★☆ | プロジェクトミックスにより変動大 |
| **純負債/資本比率** | レバレッジ | 四半期決算 | ★★★★★ | NVL等高レバレッジ企業の信用リスク評価 |

> **2024年新不動産法**: 2024年8月施行の新土地法・住宅法・不動産事業法により、外国人は1プロジェクトのアパートメント30%まで、1区あたり戸建て250棟まで所有可能。在外ベトナム人（Viet Kieu）は内国民と同等の土地使用権を取得可能に。

#### H.4.3 テクノロジー/ITセクター

| KPI | 定義 | データソース | 重要度 | 備考 |
|-----|------|------------|--------|------|
| **IT人材数** | 技術者総数 | 年次報告、投資家プレゼン | ★★★★☆ | FPT: 約7万人超。人材獲得・離職率が成長のボトルネック |
| **海外売上比率** | 総売上に占める海外IT売上 | 四半期決算 | ★★★★★ | FPTの海外IT売上VND 35兆超（+15% YoY）。DX需要が牽引 |
| **受注残** (Backlog/Pipeline) | 新規受注額・受注残高 | 投資家プレゼン | ★★★★★ | 将来売上の先行指標 |
| **顧客数・大口顧客** | Fortune 500企業等の顧客数 | 年次報告 | ★★★★☆ | FPTはForbes Global 2000の100社超にサービス提供 |
| **オフショアデリバリー拠点** | 海外拠点数・地域 | 年次報告 | ★★★☆☆ | FPT: 日本・米国・欧州・APAC等30カ国以上 |

#### H.4.4 製造業セクター

| KPI | 定義 | データソース | 重要度 | 備考 |
|-----|------|------------|--------|------|
| **生産量** (Production Volume) | 鉄鋼トン数、乳製品リットル数等 | 四半期決算 | ★★★★★ | HPG: Dung Quat年間800万トン |
| **ASP** (Average Selling Price) | 製品平均販売価格 | 四半期決算、業界データ | ★★★★★ | 国内鉄鋼価格は国際市況に連動。HPGは中国鉄鋼輸出量に大きく影響される |
| **輸出比率** | 総売上に占める輸出 | 四半期決算 | ★★★★☆ | 為替リスクと貿易政策リスクの評価 |
| **原材料コスト** | 主要原材料の調達コスト | 決算説明会 | ★★★★☆ | 鉄鉱石（HPG）、原乳（VNM）等 |
| **設備稼働率** | 生産能力に対する実績比率 | 投資家プレゼン | ★★★☆☆ | 設備投資判断の参考 |

#### H.4.5 ユーティリティ/エネルギーセクター

| KPI | 定義 | データソース | 重要度 |
|-----|------|------------|--------|
| **発電量** (Generation Output) | 発電所ごとのGWh | 四半期決算、EVN | ★★★★★ |
| **設備容量** (Installed Capacity) | MW | 年次報告 | ★★★★☆ |
| **再エネ比率** | ポートフォリオに占める再エネ | 年次報告 | ★★★★☆ |
| **PPA条件** | 電力購入契約の価格・期間 | 年次報告（一部非開示） | ★★★★☆ |
| **配当利回り** | DPS/株価 | 決算データ | ★★★★☆ |

### H.5 情報ソース

#### H.5.1 ニュース・メディア

| メディア | 言語 | 特徴 | URL |
|---------|------|------|-----|
| **VnExpress International** | 英語 | ベトナム最大手オンラインメディアの英語版。経済・ビジネス記事が充実 | https://e.vnexpress.net |
| **VietnamNet** | 英語/越語 | 政治・経済全般。英語記事あり | https://vietnamnet.vn/en |
| **Vietnam Investment Review** | 英語 | MPI傘下の投資専門メディア。FDI・政策情報が充実 | https://vir.com.vn |
| **The Investor** | 英語 | 投資家向けニュース。企業・市場分析 | https://theinvestor.vn |
| **VnEconomy** | 英語/越語 | 経済専門。ベトナム経済タイムズの英語版 | https://en.vneconomy.vn |
| **Saigon Times** | 英語/越語 | ホーチミン市の経済メディア | https://thesaigontimes.vn |
| **Vietnam News** | 英語 | VNA（ベトナム通信社）の英語版。政府系公式メディア | https://vietnamnews.vn |
| **CafeF** | 越語 | ベトナム最大の金融・証券情報サイト。リアルタイム株価・ニュース | https://cafef.vn |
| **Vietstock** | 越語/英語 | 証券・投資情報ポータル。財務データ・株価チャート | https://en.vietstock.vn |
| **VietstockFinance** | 英語 | Vietstockの金融データツール。企業財務データ | https://finance.vietstock.vn/?languageid=2 |
| **Vietnam Briefing** | 英語 | Dezan Shira & Associates運営。法規制・投資環境解説 | https://www.vietnam-briefing.com |

#### H.5.2 証券会社リサーチ（現地系）

| 証券会社 | リサーチ言語 | 特徴 | URL |
|---------|------------|------|-----|
| **SSI Securities** | 英語/越語 | 最大手。マクロ・セクター・個別銘柄レポート。Monthly Market Outlookが有用 | https://www.ssi.com.vn/en |
| **VNDirect Securities** | 英語/越語 | 包括的リサーチ。セクターレポート・イニシエーションが充実 | https://www.vndirect.com.vn |
| **HSC (Ho Chi Minh City Securities)** | 英語/越語 | 外国機関投資家向け。英語レポートの質が高い | https://www.hsc.com.vn |
| **Vietcap Securities** | 英語/越語 | 投資銀行に強み。リサーチセンター公開 | https://www.vietcap.com.vn |
| **VCBS (Vietcombank Securities)** | 越語/一部英語 | VCB系列。銀行セクター分析に強い | https://www.vcbs.com.vn |
| **KB Securities Vietnam** | 英語/越語 | 韓国KB系列。セクターレポート | https://www.kbsec.com.vn |
| **MBS (MB Securities)** | 英語/越語 | 個別銘柄アップデート | https://www.mbs.com.vn |
| **MAS (Mirae Asset Securities Vietnam)** | 英語/越語 | 韓国ミレアセット系列。バンキングセクター分析 | https://masvn.com |
| **ACBS (ACB Securities)** | 越語/一部英語 | ACB系列。セクターアウトルック | https://acbs.com.vn |
| **FiinGroup** | 英語/越語 | 金融データ・信用格付け。セクタープレビュー | https://fiingroup.vn |

#### H.5.3 証券会社リサーチ（外資系）

| 証券会社 | 特徴 |
|---------|------|
| **Maybank Kim Eng Vietnam** | ASEAN系。ベトナムカバレッジ広い |
| **CLSA Vietnam** | アジア独立系。深い分析 |
| **VinaCapital** | ベトナム特化ファンド。定期的なインサイトレポート |
| **Dragon Capital** | ベトナム最大外資系ファンド。市場レポート |
| **JP Morgan Vietnam** | グローバル系。大型株カバレッジ |
| **UOB Kay Hian Vietnam** | シンガポール系。ASEAN比較に強い |

#### H.5.4 投資家プレゼンテーション取得先（主要企業IR）

| 企業 | IR URL | 決算特徴 |
|------|--------|---------|
| Vietcombank (VCB) | https://www.vietcombank.com.vn/en/Investors | 四半期開示。英語IR資料あり。CAR・NIM・NPLの詳細開示 |
| Techcombank (TCB) | https://techcombank.com/investor-relations | NDRプレゼンが充実。CASA・手数料収入の詳細 |
| FPT Corporation (FPT) | https://fpt.com/en/investor-relations | 月次売上速報あり。セグメント別・地域別開示が詳細 |
| Vinhomes (VHM) | https://vinhomes.vn/en/investor-relations | Pre-sales・土地バンクの詳細開示 |
| Vinamilk (VNM) | https://www.vinamilk.com.vn/en/investors | 市場シェア・製品別売上の開示 |
| Hoa Phat (HPG) | https://www.hoaphat.com.vn/en/investor-relations | 月次生産量速報。製品別・地域別売上 |
| VietJet Air (VJC) | https://ir.vietjetair.com | Load Factor・RPK等の航空KPI |
| SSI Securities (SSI) | https://www.ssi.com.vn/en/investor-relations | ブローカレッジシェア・AUM |

#### H.5.5 金融データプラットフォーム

| プラットフォーム | 特徴 | URL |
|----------------|------|-----|
| **VietstockFinance** | ベトナム株の包括的な財務データ（英語対応） | https://finance.vietstock.vn/?languageid=2 |
| **CafeF** | リアルタイム株価、チャート、ニュース（越語） | https://cafef.vn |
| **FiinPro** | プロフェッショナル向けベトナム金融データ端末（有料） | https://fiingroup.vn |
| **StoxPlus** (FiinGroup) | ベトナム企業の信用・財務データ | https://fiingroup.vn |
| **Yahoo Finance (.VN)** | ベトナム株の基本データ（ティッカーに.VN付与） | https://finance.yahoo.com |
| **Investing.com** | ベトナム株の株価・チャート・ニュース | https://www.investing.com |
| **TradingView** | テクニカルチャート（HOSE:VCB等の形式） | https://www.tradingview.com |

#### H.5.6 yfinanceでのベトナム株ティッカー形式

| 取引所 | サフィックス | 例 |
|--------|-----------|-----|
| HOSE | `.VN` | `VCB.VN` (Vietcombank), `FPT.VN` (FPT Corp), `VNM.VN` (Vinamilk) |
| HNX | `.VN` | `SHS.VN` (SHS Securities) |
| VN-Index | `^VNINDEX.VN` | VN-Index |

> **注意**: yfinanceでのベトナム株データは遅延がある場合がある。リアルタイムデータはCafeF/Vietstockを推奨。

### H.6 ベトナム固有の注意点

#### H.6.1 MSCI/FTSE 新興市場格上げ問題

**FTSE Russell格上げ（確定）**:
- 2025年10月7日: FTSE RussellがベトナムのSecondary Emerging Market格上げを発表
- 2026年3月: 中間レビュー（最終確認）
- 2026年9月21日: 正式反映予定
- 推定資金流入: USD 50-70億（短期）

**MSCI格上げ（中長期目標）**:
- 現状: MSCI Frontier Markets Index構成国
- 目標: 2026-2027年に格上げ検討、政府は2030年までのEM基準達成を計画
- MSCIはFTSEより基準が厳しく、特に市場アクセシビリティ（外国人投資制限、資本移動の自由度）を重視
- 詳細は後述「H.7 MSCI格上げロードマップ」参照

#### H.6.2 外国人投資制限（FOL: Foreign Ownership Limit）

| セクター | 外国人持分上限 | 備考 |
|---------|--------------|------|
| 一般 | 49% | デフォルト上限 |
| 銀行 | 30% | 戦略投資家は1社15%まで |
| 証券 | 49%（一部100%） | 外資100%証券会社の設立が可能に |
| 航空 | 34% | 安全保障上の制限 |
| テレコム | 49% | ネットワークインフラ |
| 不動産 | 制限あり | 土地所有は不可。建物のみ（アパート30%/プロジェクト、戸建て250棟/区） |
| IT/テクノロジー | 49%-100% | サービス内容により異なる |

**2025年の重要規制変更**:
- 2025年9月施行の新政令により、企業が恣意的にFOLを低く設定することを禁止。法定上限までの外国人投資が原則可能に。
- 企業は12カ月以内にFOL上限を公式報告する義務

#### H.6.3 会計基準（VAS / IFRS収斂）

**現状**:
- ベトナム会計基準（VAS）はIFRSとの間に重要な差異あり
- 主な差異: 収益認識、金融商品評価、連結範囲、公正価値測定
- 企業はVASベースの個別財務諸表+連結財務諸表を作成

**IFRSロードマップ**:
- **Phase 1（2022-2025）**: 自発的適用期間。国有企業・上場大企業にIFRS適用を奨励
- **Phase 2（2025以降）**: 段階的義務化。国有企業・上場企業・大規模非上場公開企業にIFRS連結財務諸表の作成を義務付け
- **2026年1月**: 新会計通達（Circular 200改正版）施行予定。IFRSとの収斂を大幅に進める
- **実態**: 移行は遅延気味。多くの企業が準備不足

> **投資家への影響**: VASベースの財務諸表は利益が過大/過小に表示される場合がある。特に不動産セクターの収益認識タイミング、銀行のNPL分類、金融資産の公正価値評価に注意。

#### H.6.4 国有企業の民営化（Equitization）

- 「Equitization」= ベトナム式民営化。国有企業を株式会社化し、国・従業員・民間が株式保有
- 2016-2020年: 128社中39社のみ完了（目標達成率30%）。大幅に遅延
- 2026年1月: 決議79号により新たな財務メカニズム導入。民営化収益の全額利用、内部留保比率の引き上げ
- 政府方針: 戦略セクター（銀行・エネルギー・通信・インフラ）では国有持分過半維持が基本
- 直近は民営化加速よりも、国有企業の成長目標達成（2026年売上成長10%以上）に重点

#### H.6.5 不動産法改正（2024年施行）の影響

- **土地法（2024年8月施行）**: 土地使用権の透明性向上、補償基準の明確化
- **住宅法（2024年8月施行）**: 外国人・在外ベトナム人の所有権拡大
- **不動産事業法（2025年1月施行）**: 事業ライセンス要件の簡素化
- **影響**: 停滞していたプロジェクト承認の再開。2025年にHCM市・ハノイで4万戸超の新規供給予測（前年比10%増）
- **残存リスク**: 法改正後も地方政府レベルでの実行・解釈に時間がかかる

#### H.6.6 信用成長率のSBV管理

- SBVは年間の信用成長率目標を設定（2025年: 16%、2026年: 15%）
- 各銀行に個別の信用成長率上限（Credit Quota）を割当
- 配分基準: 前年の経営スコア・ランキング結果 x 共通係数
- CAR・ガバナンス・資産品質の良い銀行ほど高い上限が付与
- **2026年からの変更**: 首相指示により上限制度（Quota制）撤廃の方向。効率性・持続性ベースの新フレームワークへ移行予定
- **投資家への影響**: 信用上限の配分は銀行の貸出成長・利益成長に直結。上限撤廃は大手民間銀行に有利

#### H.6.7 通貨リスク（VND）

**為替制度**:
- 管理変動相場制（Managed Float）。SBVが日次中心レートを設定し、商業銀行は+/-5%バンド内で取引
- 実質的にはUSDに対して緩やかな減価を許容するクローリングペッグに近い

**直近の動向（2025-2026）**:
- 2025年8-9月: VNDが対USD過去最安値（26,400-26,436）を記録
- SBVは約USD 44億のフォワード外貨売却で対応
- 2026年2月時点: 約25,300-25,500 VND/USD
- 2026年見通し: 26,000-26,800 VND/USD（アナリスト予測レンジ）

**減価要因**: 米ドル高、米国実質金利上昇、ベトナムの金融緩和期待、輸入増・外貨需要増、ポートフォリオフロー変動

**SBVの対応**: フォワード外貨売却、FXスワップによるVND流動性供給、FX上限レートの安定維持

> **投資家へのリスク**: VNDは年率2-4%程度の対USD減価が長期的なデフォルト想定。急激な減価局面では外国人投資家の実質リターンを毀損。

#### H.6.8 Pre-funding Requirement（買付前入金要件）の撤廃

- **旧制度**: 外国人投資家は株式購入注文時に口座に全額入金が必要（T+0入金）
- **撤廃**: 2024年11月、Circular 68/2024/TT-BTC（2024年9月18日）及びCircular 18/2025/TT-BTC（2025年4月26日）により外国法人投資家のPre-funding要件を撤廃
- **新制度**: 証券会社が顧客の財務能力をデューデリジェンスで評価。全額入金は不要
- **影響**: FTSE格上げの重要な前提条件。外国人投資家の取引利便性が大幅に向上

#### H.6.9 KYC/AML規制の強化

- ベトナムはFATF（金融活動作業部会）の「グレーリスト」対応を進行中
- マネーロンダリング防止法の改正（2023年施行）
- 証券口座開設時のKYC要件強化
- 外国人投資家は投資登録証明書（IRC）が必要なケースあり

### H.7 MSCI格上げロードマップ

#### H.7.1 現在のステータス

| 分類体系 | 現在の分類 | 目標分類 | ステータス |
|---------|----------|---------|----------|
| **FTSE Russell** | Frontier → **Secondary Emerging（確定）** | Secondary Emerging | 2026年9月21日反映予定。2026年3月中間レビュー |
| **MSCI** | Frontier Markets | Emerging Markets | 中長期目標（2026-2030年） |

#### H.7.2 FTSE格上げの条件と達成状況

| 条件 | 達成状況 | 備考 |
|------|---------|------|
| Pre-funding要件の撤廃 | 達成 | Circular 68/2024で対応 |
| DVP（Delivery vs Payment）決済 | 進行中 | VSDC子会社設立によるCCP機能整備 |
| 市場アクセス改善 | 達成 | グローバルブローカーの参入可能性 |
| 情報開示の英語化 | 進行中 | VN30企業に英語開示義務化（2025年1月〜） |
| 十分な市場規模・流動性 | 達成 | 市場時価総額USD 2,880億 |

#### H.7.3 MSCI格上げの追加条件

| 条件 | 現状 | 必要な対応 |
|------|------|----------|
| 外国人投資制限の緩和 | FOL 49%維持 | FOL上限の引き上げまたはNon-Voting Depository Receipt（NVDR）の導入 |
| 資本移動の自由度 | 一部制限あり | 送金・為替規制の緩和 |
| 市場インフラ | 改善中 | CCP（Central Counterparty）の完全稼働（2027年Q1予定） |
| 投資家登録制度 | 存在 | 簡素化が必要 |
| 空売り・貸株 | 制限的 | 制度整備が必要 |
| 市場アクセシビリティ | 改善中 | オフショア取引の拡充 |

#### H.7.4 インフラ改革ロードマップ

| 時期 | 施策 | 内容 |
|------|------|------|
| 2025年Q3-2026年Q1 | VSDC子会社設立 | CCP機能の整備 |
| 2026年Q1-Q2 | 新決済通達 | Circular 119/2020の改正版。決済制度の近代化 |
| 2025年Q3-2026年Q4 | 会計基準改革 | 新会計フレームワークの導入 |
| 2026年 | ITシステム刷新 | 取引・決済システムのアップグレード |
| 2027年Q1 | CCP本格稼働 | Central Counterpartyの完全運用開始 |

#### H.7.5 格上げ時のインパクト推定

**FTSE格上げ（2026年9月）**:
- パッシブ資金流入: USD 10-15億（FTSE Emerging Indexトラッカー）
- アクティブ資金流入: USD 40-55億（中期的）
- VN-Indexへの影響: 10-15%の上昇圧力（格上げ前の織り込み含む）
- 最も恩恵を受ける銘柄: VN30構成銘柄、特に外国人持分に余裕がある銘柄

**MSCI格上げ（仮に実現した場合）**:
- パッシブ資金流入: USD 50-80億（MSCI EMトラッカーの規模が大きい）
- ベトナムのMSCI EM内ウェイト: 推定0.5-1.0%
- 台湾・韓国等の既存EM国からのリアロケーション圧力

#### H.7.6 FTSE格上げ対象銘柄

FTSE Russellは28銘柄をEmerging Market Indexの編入候補として公表。VN30構成銘柄が中心で、VCB, FPT, VHM, HPG, VNM, GAS, TCB, MBB, VIC, VJC等の大型株が含まれる。

### H.8 分析チェックリスト

#### H.8.1 マクロ環境チェック

```
□ GDP成長率（四半期）
  - 政府目標（2026年: 8%以上）との乖離
  - セクター別GDP寄与度

□ 金融政策
  - SBVリファイナンスレート
  - 信用成長率の実績 vs 目標
  - 各銀行への信用上限配分

□ 為替
  - USD/VND中心レートの推移
  - SBVの介入状況（外貨準備の変動）
  - NDF市場のプレミアム

□ インフレ
  - CPI（GSO月次）
  - コアCPI（食品・エネルギー除く）

□ 貿易・FDI
  - 貿易収支（輸出入データ）
  - FDI登録額・実行額
  - 主要FDI元国（韓国・日本・シンガポール・中国等）

□ MSCI/FTSE格上げ進捗
  - FTSE中間レビュー結果（2026年3月）
  - MSCI年次分類レビュー（6月・11月）
  - 市場インフラ改革の進捗
```

#### H.8.2 銘柄分析チェック

```
□ 財務分析
  - 過去5年の売上・利益トレンド
  - ROE・ROAの推移
  - 負債構造（短期/長期、外貨建て比率）
  - FCF（フリーキャッシュフロー）

□ バリュエーション
  - P/E（trailing/forward）
  - P/B
  - EV/EBITDA
  - PEG Ratio
  - 同業他社比較（国内+ASEAN同業）

□ ガバナンス
  - 支配株主の持分比率
  - 国有持分の有無と政府関与度
  - 関連当事者取引の規模
  - 監査法人（Big 4か否か）
  - 独立取締役の割合

□ 流動性
  - 日次売買代金
  - フリーフロート比率
  - 外国人持分余裕（FOL上限 - 現在の外国人保有率）

□ 為替リスク
  - 外貨建て収入/支出の比率
  - 外貨建て借入の有無
  - ヘッジ状況

□ VAS/IFRS差異
  - 収益認識のタイミング（特に不動産）
  - 金融資産の評価方法
  - NPL分類基準（銀行の場合）
  - 減損テストの実施状況
```

#### H.8.3 セクター別追加チェック

**銀行**:
```
□ NIM推移とガイダンス
□ NPL比率（公式 + VAMC残高 + 要注意債権 = 実質NPL）
□ CASA比率の推移
□ CAR（Basel II/III準拠）
□ SBV信用成長率上限 vs 実績
□ 引当率（Provision Coverage）
□ ROEの持続可能性
```

**不動産**:
```
□ Pre-salesの推移と認識スケジュール
□ 土地バンクの規模・立地・法的ステータス
□ プロジェクト承認パイプライン（1/50許可、建設許可、販売許可）
□ 資金調達構造（社債依存度、銀行借入条件）
□ 新土地法の影響評価
```

**テクノロジー/IT**:
```
□ 海外IT売上成長率
□ 新規受注額・受注残高
□ IT人材数と離職率
□ DX/AI関連サービスの比率
□ 顧客集中度（上位10顧客比率）
```

#### H.8.4 ベトナム固有リスクチェック

```
□ FTSE格上げの最終確認（2026年3月中間レビュー）
□ FOL（外国人投資制限）の残余枠
□ VND為替リスク（年率2-4%減価想定）
□ VAS会計基準の限界（IFRS換算で利益が変動する可能性）
□ 情報の非対称性（ベトナム語資料の限定的アクセス）
□ 国有企業の政策リスク（SBV信用管理、国有持分維持）
□ 不動産セクターの法的リスク（承認遅延、法改正の実行ギャップ）
□ 地政学リスク（南シナ海、米中対立の影響）
□ 資本規制リスク（配当送金、資金移動に時間がかかるケースあり）
□ Pre-funding撤廃後の実務的な制約有無
```

#### 参考情報

**ベトナム市場の開示制度**

| 項目 | 内容 |
|------|------|
| 開示言語 | ベトナム語（大型株は英語併記義務化進行中） |
| 決算頻度 | 四半期（年4回） |
| 会計年度 | 1月-12月（カレンダーイヤー） |
| 会計基準 | VAS（ベトナム会計基準）。IFRS移行中 |
| 監査 | Big 4 + 現地大手（A&C, AASC等） |
| 開示プラットフォーム | 各取引所サイト（HOSE: hsx.vn, HNX: hnx.vn） |
| 整備度 | ★★☆☆☆（アジア主要市場の中で最も限定的） |

**主要指数**

| 指数名 | 構成 | 特徴 |
|--------|------|------|
| **VN-Index** | HOSE全上場銘柄 | メインベンチマーク |
| **VN30** | 時価総額・流動性上位30銘柄 | デリバティブ（先物）の原資産 |
| **VNX Allshare** | HOSE+HNX全銘柄 | 市場全体のパフォーマンス |
| **HNX-Index** | HNX上場銘柄 | 中小型株中心 |
| **FTSE Vietnam 30** | FTSE基準の上位30銘柄 | FTSE格上げ対象の参考 |

**取引制度**

| 項目 | 内容 |
|------|------|
| 取引時間 | 9:00-11:30, 13:00-14:45（現地時間、GMT+7） |
| 決済 | T+2 |
| 値幅制限 | HOSE: +/-7%, HNX: +/-10% |
| ロットサイズ | 100株 |
| 空売り | 制限的（制度整備中） |
| デリバティブ | VN30先物、国債先物（HNX） |
| ETF | VN30 ETF（SSIAM, Dragon Capital等が運用） |

---

*作成日: 2026-02-10*
*最終更新: 2026-02-10*
