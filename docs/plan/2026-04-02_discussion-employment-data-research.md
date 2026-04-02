# 議論メモ: 米国雇用関連データ取得方法の調査

**日付**: 2026-04-02
**議論ID**: disc-2026-04-02-employment-data-research
**参加**: ユーザー + AI

## 背景・コンテキスト

マクロ経済分析・雇用市場モニタリングの拡充のため、以下の米国雇用関連データをPythonで取得する方法を調査。FREDで取得可能なものはシリーズIDを特定し、`data/config/fred_series.json` に追加する。

### 調査対象

1. 米国公式雇用統計
2. ADP雇用統計
3. 米国連邦政府、州政府、地方政府雇用者数
4. 米国ISM製造業「雇用」、製造業雇用者数
5. （米労務省）派遣社員数、全社員数
6. （米労務省）コールセンター雇用者数
7. （米労務省）年齢別の失業率
8. （サンフランシスコ連銀）インフレ率の需要・供給の要因分解
9. Indeed求人数
10. JOLTS求人数

## 議論のサマリー

### FRED で取得可能（22系列を追加）

#### "Population, Employment, & Labor Force" カテゴリに追加（15系列）

| シリーズID | 日本語名 | 頻度 | 用途 |
|-----------|---------|------|------|
| `U6RATE` | U-6 失業率（広義） | 月次 | 労働市場スラック |
| `CIVPART` | 労働参加率 | 月次 | 構造的変化の把握 |
| `USPRIV` | 民間全雇用者数 | 月次 | PAYEMS-政府=民間 |
| `ADPMNUSNERSA` | ADP雇用統計（月次） | 月次 | 公式NFPの先行指標 |
| `USGOVT` | 政府雇用者数（合計） | 月次 | 政府セクター全体 |
| `CES9091000001` | 連邦政府雇用者数 | 月次 | DOGE影響追跡 |
| `CES9092000001` | 州政府雇用者数 | 月次 | 州財政の反映 |
| `CES9093000001` | 地方政府雇用者数 | 月次 | 教員・公共サービス |
| `MANEMP` | 製造業雇用者数 | 月次 | 関税・リショアリング効果 |
| `TEMPHELPS` | 派遣社員数 | 月次 | 景気先行指標 |
| `JTSHIL` | JOLTS 採用件数 | 月次 | 実際の採用ペース |
| `JTSQUL` | JOLTS 自発的離職件数 | 月次 | 労働者の転職意欲 |
| `JTSTSL` | JOLTS 離職件数（合計） | 月次 | 全離職の規模 |
| `JTSLDL` | JOLTS 解雇件数 | 月次 | レイオフの規模 |
| `IHLIDXUS` | Indeed 求人指数 | 日次 | リアルタイム求人動向 |

#### 新カテゴリ "Unemployment Rate by Age"（6系列）

| シリーズID | 日本語名 | 頻度 |
|-----------|---------|------|
| `LNS14000012` | 失業率: 16-19歳 | 月次 |
| `LNS14000036` | 失業率: 20-24歳 | 月次 |
| `LNS14000089` | 失業率: 25-34歳 | 月次 |
| `LNS14000091` | 失業率: 35-44歳 | 月次 |
| `LNS14000093` | 失業率: 45-54歳 | 月次 |
| `LNS14024230` | 失業率: 55歳以上 | 月次 |

### FRED で取得不可（3項目）

| データ | 理由 | 代替取得方法 |
|--------|------|-------------|
| ISM製造業「雇用」指数 (NAPMEI) | 2024年6月にFREDから全22 ISM系列が削除 | ISM公式サイト直接、またはサードパーティAPI |
| コールセンター雇用者数 (NAICS 56142) | 全国レベルはFREDにない（州レベルのみ） | BLS QCEW API (`data.bls.gov/cew/`) |
| SF連銀インフレ需給分解 | FRED未登録 | SF Fed サイトからCSV直接DL (`frbsf.org`) |

### FRED ID の注意点

BLSのCESソースコード（例: `CES9000000001`）とFREDシリーズID（例: `USGOVT`）は異なる場合がある。以下は必ずFREDのニーモニックIDを使用すること:

| BLS CES コード | FRED シリーズID |
|---------------|---------------|
| CES9000000001 | `USGOVT` |
| CES3000000001 | `MANEMP` |
| CES0500000001 | `USPRIV` |
| CES6056132001 | `TEMPHELPS` |

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-04-02-001 | fred_series.json に雇用関連22系列を追加完了 | マクロ経済分析・雇用市場モニタリング拡充 |
| dec-2026-04-02-002 | FRED外3データソースの取得方法を特定 | ISM→直接、QCEW→BLS API、SF Fed→CSV DL |

## アクションアイテム

| ID | 内容 | 優先度 | ステータス |
|----|------|--------|----------|
| act-2026-04-02-004 | 追加22系列のFREDデータ初回同期 (`sync_historical --all`) | 高 | pending |
| act-2026-04-02-001 | ISM製造業雇用指数の取得スクリプト実装 | 中 | pending |
| act-2026-04-02-003 | SF連銀インフレ需給分解データのDL・パーサー実装 | 中 | pending |
| act-2026-04-02-002 | BLS QCEW APIからコールセンター雇用者数取得の実装 | 低 | pending |

## 既存シリーズ（変更前から存在）

| シリーズID | 日本語名 | 備考 |
|-----------|---------|------|
| `UNRATE` | 失業率 | 既存 |
| `CES0500000003` | 平均時給（名目） | 既存、description更新 |
| `PAYEMS` | 非農業部門雇用者数 | 既存 |
| `ICSA` | 新規失業保険申請件数 | 既存 |
| `JTSJOL` | JOLTS 求人件数 | 既存 |

## 変更したファイル

- `data/config/fred_series.json` - 22系列追加、1カテゴリ新設

## 参考情報

- FRED API: https://fred.stlouisfed.org/
- BLS QCEW: https://www.bls.gov/cew/
- SF Fed Supply/Demand PCE: https://www.frbsf.org/research-and-insights/data-and-indicators/supply-and-demand-driven-pce-inflation/
- ISM: https://www.ismworld.org/
- Indeed Hiring Lab (FRED): IHLIDXUS（日次、2020年2月1日=100）
- ADP National Employment Report (FRED release rid=194): 月次129系列
