# DeepWiki Q&A with Code Context for Repository: dgunning/edgartools

## Q1

Tenk オブジェクトのプロパティを全て教えて。日本語で回答して

### Answer

ユーザーは`TenK`オブジェクトのプロパティについて質問しています。 edgartools:141-141 `TenK`クラスは 10-K 年次報告書を表すデータオブジェクトです。<cite />

## TenK オブジェクトのプロパティ

### 基本プロパティ

`TenK`は`CompanyReport`を継承しており、以下のプロパティを持ちます:<cite />

-   **`filing_date`** - 提出日 edgartools:40-42
-   **`form`** - フォームタイプ(10-K) edgartools:44-46
-   **`company`** - 会社名 edgartools:48-50
-   **`period_of_report`** - 報告期間 edgartools:69-71

### 財務諸表プロパティ

-   **`financials`** - 財務データオブジェクト edgartools:64-67
-   **`income_statement`** - 損益計算書 edgartools:52-54
-   **`balance_sheet`** - 貸借対照表 edgartools:56-58
-   **`cash_flow_statement`** - キャッシュフロー計算書 edgartools:60-62

### セクション別プロパティ

`TenK`には 10-K の特定セクションに直接アクセスできるプロパティがあります:<cite />

-   **`business`** - Item 1(事業内容) edgartools:259-261
-   **`risk_factors`** - Item 1A(リスク要因) edgartools:263-265
-   **`management_discussion`** - Item 7(経営陣による財務状況の分析) edgartools:267-269
-   **`directors_officers_and_governance`** - Item 10(取締役・役員・コーポレートガバナンス) edgartools:271-273

### ドキュメント関連プロパティ

-   **`chunked_document`** - 解析された HTML ドキュメント edgartools:275-277
-   **`doc`** - `chunked_document`のエイリアス edgartools:77-79
-   **`items`** - ドキュメント内のアイテムリスト edgartools:81-83

### 構造プロパティ

-   **`structure`** - 10-K の標準的な構造定義(Part I-IV、各 Item) edgartools:142-253

## Notes

`TenK`オブジェクトは`filing.obj()`メソッドを使用して`Filing`オブジェクトから作成されます。 edgartools:23-23 これらのプロパティは 10-K 年次報告書の構造化されたデータへのアクセスを提供し、財務分析やセクション別の情報取得を容易にします。<cite />

Wiki pages you might want to explore:

-   [Working with Filing Objects (dgunning/edgartools)](/wiki/dgunning/edgartools#3.2)

### Citations

**File:** edgar/company_reports.py (L40-42)

```python
    @property
    def filing_date(self):
        return self._filing.filing_date
```

**File:** edgar/company_reports.py (L44-46)

```python
    @property
    def form(self):
        return self._filing.form
```

**File:** edgar/company_reports.py (L48-50)

```python
    @property
    def company(self):
        return self._filing.company
```

**File:** edgar/company_reports.py (L52-54)

```python
    @property
    def income_statement(self):
        return self.financials.income_statement() if self.financials else None
```

**File:** edgar/company_reports.py (L56-58)

```python
    @property
    def balance_sheet(self):
        return self.financials.balance_sheet() if self.financials else None
```

**File:** edgar/company_reports.py (L60-62)

```python
    @property
    def cash_flow_statement(self):
        return self.financials.cashflow_statement() if self.financials else None
```

**File:** edgar/company_reports.py (L64-67)

```python
    @cached_property
    def financials(self):
        """Get the financials for this filing"""
        return Financials.extract(self._filing)
```

**File:** edgar/company_reports.py (L69-71)

```python
    @property
    def period_of_report(self):
        return self._filing.header.period_of_report
```

**File:** edgar/company_reports.py (L77-79)

```python
    @property
    def doc(self):
        return self.chunked_document
```

**File:** edgar/company_reports.py (L81-83)

```python
    @property
    def items(self) -> List[str]:
        return self.chunked_document.list_items()
```

**File:** edgar/company_reports.py (L141-141)

```python
class TenK(CompanyReport):
```

**File:** edgar/company_reports.py (L142-253)

```python
    structure = FilingStructure({
        "PART I": {
            # special case for 10-K
            # Items 1 and 2. Business and Properties
            "ITEM 1": {
                "Title": "Business",
                "Description": "Overview of the company's business operations, products, services, and market environment."
            },
            "ITEM 1A": {
                "Title": "Risk Factors",
                "Description": "Discussion of risks and uncertainties that could materially affect the company's " +
                               "financial condition or results of operations."
            },
            "ITEM 1B": {
                "Title": "Unresolved Staff Comments",
                "Description": "Any comments from the SEC staff on the company's previous filings" +
                               "that remain unresolved."
            },
            "ITEM 1C": {
                "Title": "Cybersecurity",
                "Description": "Cybersecurity risk management, strategy, and governance disclosures."
            },
            "ITEM 2": {
                "Title": "Properties",
                "Description": "Information about the physical properties owned or leased by the company."
            },
            "ITEM 3": {
                "Title": "Legal Proceedings",
                "Description": "Details of significant ongoing legal proceedings."
            },
            "ITEM 4": {
                "Title": "Mine Safety Disclosures",
                "Description": "Relevant for mining companies, disclosures about mine safety and regulatory compliance."
            }
        },
        "PART II": {
            "ITEM 5": {
                "Title": "Market for Registrant’s Common Equity",
                "Description": "Information on the company’s equity, including stock performance " +
                               "and shareholder matters."
            },
            "ITEM 6": {
                "Title": "Selected Financial Data",
                "Description": "Financial data summary for the last five fiscal years."
            },
            "ITEM 7": {
                "Title": "Management’s Discussion and Analysis (MD&A)",
                "Description": "Management’s perspective on the financial condition, changes in financial condition, " +
                               "and results of operations."
            },
            "ITEM 7A": {
                "Title": "Quantitative and Qualitative Disclosures About Market Risk",
                "Description": "Information on the company's exposure to market risk, such as interest rate risk, " +
                               "foreign currency exchange risk, commodity price risk, etc."
            },
            "ITEM 8": {
                "Title": "Financial Statements",
                "Description": "Complete audited financial statements, including balance sheet, income statement, " +
                               "cash flow statement, and notes to the financial statements."
            },
            "ITEM 9": {
                "Title": "Controls and Procedures",
                "Description": "Evaluation of the effectiveness of the design and operation of the company’s disclosure controls and procedures."
            },
            "ITEM 9A": {
                "Title": "Controls and Procedures",
                "Description": "Evaluation of internal controls over financial reporting."
            },
            "ITEM 9B": {
                "Title": "Other Information",
                "Description": "Any other relevant information not covered in other sections."
            },
            "ITEM 9C": {
                "Title": "Disclosure Regarding Foreign Jurisdictions That Prevent Inspections",
                "Description": "Disclosure Regarding Foreign Jurisdictions That Prevent Inspections."
            }
        },
        "PART III": {
            "ITEM 10": {
                "Title": "Directors, Executive Officers, and Corporate Governance",
                "Description": "Information about the company's directors, executive officers, and governance policies."
            },
            "ITEM 11": {
                "Title": "Executive Compensation",
                "Description": "Details of compensation paid to key executives."
            },
            "ITEM 12": {
                "Title": "Security Ownership of Certain Beneficial Owners and Management",
                "Description": "Information about stock ownership of major shareholders, directors, and management."
            },
            "ITEM 13": {
                "Title": "Certain Relationships and Related Transactions, and Director Independence",
                "Description": "Information on transactions between the company and its directors, officers, " +
                               "and significant shareholders."
            },
            "ITEM 14": {
                "Title": "Principal Accounting Fees and Services",
                "Description": "Fees paid to the principal accountant and services rendered."
            }
        },
        "PART IV": {
            "ITEM 15": {
                "Title": "Exhibits, Financial Statement Schedules",
                "Description": "Legal documents and financial schedules that support the financial statements " +
                               "and disclosures."
            },
            "ITEM 16": {
                "Title": "Form 10-K Summary",
                "Description": "Form 10-K Summary"
            }
        }
    })
```

**File:** edgar/company_reports.py (L259-261)

```python
    @property
    def business(self):
        return self['Item 1']
```

**File:** edgar/company_reports.py (L263-265)

```python
    @property
    def risk_factors(self):
        return self['Item 1A']
```

**File:** edgar/company_reports.py (L267-269)

```python
    @property
    def management_discussion(self):
        return self['Item 7']
```

**File:** edgar/company_reports.py (L271-273)

```python
    @property
    def directors_officers_and_governance(self):
        return self['Item 10']
```

**File:** edgar/company_reports.py (L275-277)

```python
    @cached_property
    def chunked_document(self):
        return ChunkedDocument(self._filing.html(), prefix_src=self._filing.base_dir)
```

**File:** tests/test_company_reports.py (L23-23)

```python
    tenk: TenK = filing.obj()
```

## Q2

10-k のセクションに関連したプロパティを教えて

### Answer

ユーザーは`TenK`オブジェクトの 10-K セクションに関連したプロパティについて質問しています。<cite />

## 10-K セクション関連プロパティ

`TenK`クラスには、10-K 報告書の特定セクションに直接アクセスできる便利なプロパティが用意されています。 edgartools:259-273

### 主要セクションプロパティ

-   **`business`** - Item 1(事業内容)にアクセス edgartools:259-261
-   **`risk_factors`** - Item 1A(リスク要因)にアクセス edgartools:263-265
-   **`management_discussion`** - Item 7(MD&A - 経営陣による財務状況の分析)にアクセス edgartools:267-269
-   **`directors_officers_and_governance`** - Item 10(取締役・役員・コーポレートガバナンス)にアクセス edgartools:271-273

### 汎用アクセス方法

これらの便利プロパティに加えて、`__getitem__`メソッドを使用して任意のセクションにアクセスできます。 edgartools:287-295

````python
tenk = filing.obj()
# 任意のItemにアクセス
item_2 = tenk['Item 2']  # Properties
item_7A = tenk['Item 7A']  # Market Risk
item_15 = tenk['Item 15']  # Exhibits
``` edgartools:81-97

### セクション一覧の取得

- **`items`** - ドキュメント内の全セクション(Item)のリストを返します edgartools:81-83
- **`structure`** - 10-Kの標準的な構造定義(Part I-IV、各Itemの説明を含む)を提供します edgartools:142-253

### 使用例

テストコードでは、これらのプロパティが実際に使用されています。 edgartools:109-115

## Notes

これらのセクションプロパティは内部的に`chunked_document`を使用してHTMLドキュメントから該当セクションのテキストを抽出します。 edgartools:275-277 10-Kの構造は`FilingStructure`として定義されており、Part I-IVと各Itemの詳細な説明が含まれています。 edgartools:142-253

Wiki pages you might want to explore:
- [Working with Filing Objects (dgunning/edgartools)](/wiki/dgunning/edgartools#3.2)
### Citations
**File:** edgar/company_reports.py (L81-83)
```python
    @property
    def items(self) -> List[str]:
        return self.chunked_document.list_items()
````

**File:** edgar/company_reports.py (L142-253)

```python
    structure = FilingStructure({
        "PART I": {
            # special case for 10-K
            # Items 1 and 2. Business and Properties
            "ITEM 1": {
                "Title": "Business",
                "Description": "Overview of the company's business operations, products, services, and market environment."
            },
            "ITEM 1A": {
                "Title": "Risk Factors",
                "Description": "Discussion of risks and uncertainties that could materially affect the company's " +
                               "financial condition or results of operations."
            },
            "ITEM 1B": {
                "Title": "Unresolved Staff Comments",
                "Description": "Any comments from the SEC staff on the company's previous filings" +
                               "that remain unresolved."
            },
            "ITEM 1C": {
                "Title": "Cybersecurity",
                "Description": "Cybersecurity risk management, strategy, and governance disclosures."
            },
            "ITEM 2": {
                "Title": "Properties",
                "Description": "Information about the physical properties owned or leased by the company."
            },
            "ITEM 3": {
                "Title": "Legal Proceedings",
                "Description": "Details of significant ongoing legal proceedings."
            },
            "ITEM 4": {
                "Title": "Mine Safety Disclosures",
                "Description": "Relevant for mining companies, disclosures about mine safety and regulatory compliance."
            }
        },
        "PART II": {
            "ITEM 5": {
                "Title": "Market for Registrant’s Common Equity",
                "Description": "Information on the company’s equity, including stock performance " +
                               "and shareholder matters."
            },
            "ITEM 6": {
                "Title": "Selected Financial Data",
                "Description": "Financial data summary for the last five fiscal years."
            },
            "ITEM 7": {
                "Title": "Management’s Discussion and Analysis (MD&A)",
                "Description": "Management’s perspective on the financial condition, changes in financial condition, " +
                               "and results of operations."
            },
            "ITEM 7A": {
                "Title": "Quantitative and Qualitative Disclosures About Market Risk",
                "Description": "Information on the company's exposure to market risk, such as interest rate risk, " +
                               "foreign currency exchange risk, commodity price risk, etc."
            },
            "ITEM 8": {
                "Title": "Financial Statements",
                "Description": "Complete audited financial statements, including balance sheet, income statement, " +
                               "cash flow statement, and notes to the financial statements."
            },
            "ITEM 9": {
                "Title": "Controls and Procedures",
                "Description": "Evaluation of the effectiveness of the design and operation of the company’s disclosure controls and procedures."
            },
            "ITEM 9A": {
                "Title": "Controls and Procedures",
                "Description": "Evaluation of internal controls over financial reporting."
            },
            "ITEM 9B": {
                "Title": "Other Information",
                "Description": "Any other relevant information not covered in other sections."
            },
            "ITEM 9C": {
                "Title": "Disclosure Regarding Foreign Jurisdictions That Prevent Inspections",
                "Description": "Disclosure Regarding Foreign Jurisdictions That Prevent Inspections."
            }
        },
        "PART III": {
            "ITEM 10": {
                "Title": "Directors, Executive Officers, and Corporate Governance",
                "Description": "Information about the company's directors, executive officers, and governance policies."
            },
            "ITEM 11": {
                "Title": "Executive Compensation",
                "Description": "Details of compensation paid to key executives."
            },
            "ITEM 12": {
                "Title": "Security Ownership of Certain Beneficial Owners and Management",
                "Description": "Information about stock ownership of major shareholders, directors, and management."
            },
            "ITEM 13": {
                "Title": "Certain Relationships and Related Transactions, and Director Independence",
                "Description": "Information on transactions between the company and its directors, officers, " +
                               "and significant shareholders."
            },
            "ITEM 14": {
                "Title": "Principal Accounting Fees and Services",
                "Description": "Fees paid to the principal accountant and services rendered."
            }
        },
        "PART IV": {
            "ITEM 15": {
                "Title": "Exhibits, Financial Statement Schedules",
                "Description": "Legal documents and financial schedules that support the financial statements " +
                               "and disclosures."
            },
            "ITEM 16": {
                "Title": "Form 10-K Summary",
                "Description": "Form 10-K Summary"
            }
        }
    })
```

**File:** edgar/company_reports.py (L259-273)

```python
    @property
    def business(self):
        return self['Item 1']

    @property
    def risk_factors(self):
        return self['Item 1A']

    @property
    def management_discussion(self):
        return self['Item 7']

    @property
    def directors_officers_and_governance(self):
        return self['Item 10']
```

**File:** edgar/company_reports.py (L275-277)

```python
    @cached_property
    def chunked_document(self):
        return ChunkedDocument(self._filing.html(), prefix_src=self._filing.base_dir)
```

**File:** edgar/company_reports.py (L287-295)

```python
    def __getitem__(self, item_or_part: str):
        # Show the item or part from the filing document. e.g. Item 1 Business from 10-K or Part I from 10-Q
        item_text = self.chunked_document[item_or_part]
        if item_text:
            item_text = item_text.rstrip()
            last_line = item_text.split("\n")[-1]
            if re.match(r'^\b(PART\s+[IVXLC]+)\b', last_line):
                item_text = item_text.rstrip(last_line)
        return item_text
```

**File:** tests/test_company_reports.py (L81-97)

```python
def test_items_for_10k_filing():
    filing = Filing(form='10-K', filing_date='2023-11-08', company='CHS INC', cik=823277,
                    accession_no='0000823277-23-000053')
    tenk = filing.obj()
    item_2 = tenk['Item 2']
    assert "We own or lease energy" in item_2
    assert "Kaw Pipe Line Company" in item_2
    print(item_2)

    item_7A = tenk['Item 7A']
    print(item_7A)
    assert "Commodity Price Risk" in item_7A

    item_15 = tenk['Item 15']
    assert item_15
    assert 'FINANCIAL STATEMENTS' in item_15
    print(item_15)
```

**File:** tests/test_company_reports.py (L109-115)

```python
def test_tenk_section_properties(apple_2024_10k_filing):
    filing = apple_2024_10k_filing
    tenk:TenK = filing.obj()
    assert tenk.management_discussion
    assert tenk.business
    assert tenk.risk_factors
    assert tenk.directors_officers_and_governance
```

## Q3

management_discussion から html を取得したい。

### Answer

`management_discussion`プロパティから元の HTML コンテンツを取得する方法についての質問ですね。<cite />

## HTML の取得方法

`management_discussion`プロパティは、`TenK`クラスの`__getitem__`メソッドを通じて`chunked_document`からテキストを抽出します。 edgartools:267-269 しかし、これはテキスト形式で返されます。 edgartools:287-295

元の HTML を取得するには、以下の方法があります:

### 方法 1: Filing オブジェクトから直接 HTML を取得

```python
tenk = filing.obj()
# Filing オブジェクトから完全なHTMLを取得
html_content = tenk._filing.html()
```

`TenK`オブジェクトは内部的に`_filing`属性を持っており、これは元の`Filing`オブジェクトです。 edgartools:255-257 この`Filing`オブジェクトには`html()`メソッドがあり、完全な HTML ドキュメントを返します。 edgartools:1449-1463

### 方法 2: ChunkedDocument から元の HTML にアクセス

`chunked_document`は元の HTML から作成されます: edgartools:275-277

```python
tenk = filing.obj()
# ChunkedDocumentは元のHTMLを保持している
chunked_doc = tenk.chunked_document
# 完全なHTMLは tenk._filing.html() から取得可能
full_html = tenk._filing.html()
```

### 注意点

-   `management_discussion`プロパティ自体はテキスト形式で返されるため、セクションの HTML のみを抽出するには、完全な HTML から該当部分を解析する必要があります<cite />
-   `ChunkedDocument`は HTML を解析してセクションごとに分割しますが、元の HTML 構造を保持するわけではありません<cite />

## Notes

もし特定のセクション(Item 7)の HTML のみが必要な場合は、完全な HTML を取得してから、そのセクションに対応する部分を抽出する必要があります。<cite />現在の API では、セクションごとの HTML を直接取得するメソッドは提供されていないようです。<cite />

Wiki pages you might want to explore:

-   [Working with Filing Objects (dgunning/edgartools)](/wiki/dgunning/edgartools#3.2)

### Citations

**File:** edgar/company_reports.py (L255-257)

```python
    def __init__(self, filing):
        assert filing.form in ['10-K', '10-K/A'], f"This form should be a 10-K but was {filing.form}"
        super().__init__(filing)
```

**File:** edgar/company_reports.py (L267-269)

```python
    @property
    def management_discussion(self):
        return self['Item 7']
```

**File:** edgar/company_reports.py (L275-277)

```python
    @cached_property
    def chunked_document(self):
        return ChunkedDocument(self._filing.html(), prefix_src=self._filing.base_dir)
```

**File:** edgar/company_reports.py (L287-295)

```python
    def __getitem__(self, item_or_part: str):
        # Show the item or part from the filing document. e.g. Item 1 Business from 10-K or Part I from 10-Q
        item_text = self.chunked_document[item_or_part]
        if item_text:
            item_text = item_text.rstrip()
            last_line = item_text.split("\n")[-1]
            if re.match(r'^\b(PART\s+[IVXLC]+)\b', last_line):
                item_text = item_text.rstrip(last_line)
        return item_text
```

**File:** edgar/\_filings.py (L1449-1463)

```python
    def markdown(self, include_page_breaks: bool = False, start_page_number: int = 0) -> str:
        """
        Return the markdown version of this filing html

        Args:
            include_page_breaks: If True, include page break delimiters in the markdown
            start_page_number: Starting page number for page break markers (default: 0)
        """
        html = self.html()
        if html:
            clean_html = get_clean_html(html)
            if clean_html:
                return to_markdown(clean_html, include_page_breaks=include_page_breaks, start_page_number=start_page_number)
        text_content = self.text()
        return text_to_markdown(text_content)
```

## Q4

management_ducument のテキスト文章から表を抽出するにはどうすればいいか

### Answer

ユーザーは`management_discussion`プロパティから取得したテキスト文章から表を抽出する方法について質問しています。<cite />これは`TenK`オブジェクトの`management_discussion`プロパティ(Item 7 の MD&A セクション)から表データを取得する方法に関する質問です。 edgartools:267-269

## 表の抽出方法

### 方法 1: chunked_document から直接表を取得

`TenK`オブジェクトの`chunked_document`プロパティを使用すると、ドキュメント内の全ての表にアクセスできます。 edgartools:275-277

````python
tenk = filing.obj()
# ドキュメント内の全ての表を取得
all_tables = tenk.chunked_document.tables()
``` edgartools:227-237

### 方法2: Document.parseを使用してHTMLから表を抽出

完全なHTMLを取得してから、`Document.parse()`を使用して表を抽出できます。 edgartools:15-17

```python
from edgar.files.html import Document

tenk = filing.obj()
html_content = tenk._filing.html()
document = Document.parse(html_content)
tables = document.tables  # 全ての表のリスト
``` edgartools:207-221

### 方法3: Sectionオブジェクトから表を取得

新しいドキュメントパーサーを使用している場合、`Section`オブジェクトの`tables()`メソッドで特定セクション内の表を取得できます。 edgartools:101-103

### 方法4: pandas DataFrameに変換

表を取得した後、DataFrameに変換して分析できます。 edgartools:60-69

```python
# 表をDataFrameに変換
for table in document.tables:
    df = table.to_dataframe()
    # または
    markdown = table.to_markdown()
``` edgartools:314-319

## Notes

表の抽出には複数のアプローチがあります。`chunked_document.tables()`が最もシンプルですが、特定のセクション(management_discussion)内の表のみを取得したい場合は、HTMLを解析してセクションを特定してから表を抽出する必要があります。<cite />また、`Document.parse()`を使用すると、表のメタデータ(XBRLタグなど)も取得できます。 edgartools:213-221

Wiki pages you might want to explore:
- [Document Processing & Utilities (dgunning/edgartools)](/wiki/dgunning/edgartools#7)
### Citations
**File:** edgar/company_reports.py (L267-269)
```python
    @property
    def management_discussion(self):
        return self['Item 7']
````

**File:** edgar/company_reports.py (L275-277)

```python
    @cached_property
    def chunked_document(self):
        return ChunkedDocument(self._filing.html(), prefix_src=self._filing.base_dir)
```

**File:** tests/test_tables.py (L227-237)

```python
def test_actual_filing():
    company = Company("MSFT")
    filing = company.get_filings(form="10-K").latest(1)
    html = filing.html()
    document:ChunkedDocument = ChunkedDocument(html)
    for table in document.tables():
        #print(table.table_element)
        print(table_to_text(table.table_element))
        print('\n')
        print("-" * 180)
        print('\n')
```

**File:** tests/test_html.py (L15-17)

```python
def test_parse_html_with_table():
    document = Document.parse(get_html('data/html/OneTable.html'))
    assert len(document.tables) == 1
```

**File:** tests/test_html.py (L207-221)

```python
def test_document_tables():
    html = Path("data/html/Apple.10-Q.html").read_text()
    document = Document.parse(html)

    tables = document.tables
    assert all(table.type == "table" for table in tables)
    revenue_table = tables[17]
    #print(revenue_table.render(160))
    assert revenue_table.metadata['ix_tag'] == 'us-gaap:DisaggregationOfRevenueTableTextBlock'

    for table in document.tables:
        if table.metadata.get('ix_has_table'):
            print(table.metadata.get("ix_tag"))
            print(table.render(160))
            print("-" * 80)
```

**File:** edgar/documents/document.py (L101-103)

```python
    def tables(self) -> List[TableNode]:
        """Get all tables in section."""
        return self.node.find(lambda n: isinstance(n, TableNode))
```

**File:** edgar/files/docs/filing_document.py (L60-69)

```python
    def to_dataframe(self) -> pd.DataFrame:
        """Convert this table to a pandas DataFrame."""
        processed = self._get_processed()
        if processed and processed.headers and processed.data_rows:
            # Create DataFrame with proper headers and data
            return pd.DataFrame(processed.data_rows, columns=processed.headers)
        elif processed and processed.data_rows:
            # No headers, use numeric column names
            return pd.DataFrame(processed.data_rows)
        return pd.DataFrame()
```

**File:** edgar/files/html_documents.py (L314-319)

```python
    def to_dataframe(self) -> pd.DataFrame:
        table_df = table_html_to_dataframe(str(self.table_element))
        return table_df

    def to_markdown(self) -> str:
        return self.to_dataframe().to_markdown() + "\n"
```

## Q5

section オブジェクトから表を取得する方法をもっと詳しく教えて。

### Answer

ユーザーは`Section`オブジェクトから表を取得する方法について、より詳しい説明を求めています。<cite />これは新しいドキュメントパーサー(`edgar/documents/document.py`)の`Section`クラスに関する質問です。 edgartools:59-103

## Section オブジェクトから表を取得する方法

### `tables()`メソッドの使用

`Section`オブジェクトには`tables()`メソッドが用意されており、そのセクション内の全ての表を取得できます。 edgartools:101-103

```python
# Sectionオブジェクトから表を取得
section = document.sections['item_7']  # management_discussion
tables = section.tables()  # List[TableNode]を返す
```

### 実装の詳細

`tables()`メソッドは内部的に`node.find()`を使用して、`TableNode`型のノードを検索します。 edgartools:101-103 これにより、セクションのノードツリー内の全てのテーブルノードが返されます。<cite />

### 使用例

新しいパーサーを使用する場合の完全な例:

```python
from edgar.documents import HTMLParser

# HTMLを解析
parser = HTMLParser()
document = parser.parse(html_content)

# セクションを取得
if 'item_7' in document.sections:
    md_section = document.sections['item_7']

    # セクション内の表を取得
    tables = md_section.tables()

    # 各表をDataFrameに変換
    for table in tables:
        df = table.to_dataframe()
        print(df)
```

### TableNode の操作

取得した`TableNode`オブジェクトは、以下のメソッドを持っています:<cite />

-   **`to_dataframe()`** - pandas DataFrame に変換 edgartools:718-741
-   **`caption`** - 表のキャプション
-   **`table_type`** - 表のタイプ(財務表など)

### TOC ベースのセクション検出

セクションが TOC(目次)ベースで検出された場合、`Section`オブジェクトは`_text_extractor`コールバックを持ち、遅延読み込みでテキストを抽出します。 edgartools:98-104 この場合でも`tables()`メソッドは正常に動作し、セクション内の表を返します。 edgartools:110-121

## Notes

`Section.tables()`は新しいドキュメントパーサー(`edgar/documents/`)の機能です。<cite />古いパーサー(`edgar/files/html.py`)を使用している場合は、`Document.tables`プロパティから全ての表を取得し、手動でフィルタリングする必要があります。<cite />新しいパーサーへの移行については、互換性レイヤー(`edgar/documents/migration.py`)が用意されています。 edgartools:15-106

Wiki pages you might want to explore:

-   [Document Processing & Utilities (dgunning/edgartools)](/wiki/dgunning/edgartools#7)

### Citations

**File:** edgar/documents/document.py (L59-103)

```python
class Section:
    """
    Document section representation.

    Represents a logical section of the document (e.g., Risk Factors, MD&A).

    Attributes:
        name: Section identifier (e.g., "item_1", "part_i_item_1", "risk_factors")
        title: Display title (e.g., "Item 1 - Business")
        node: Node containing section content
        start_offset: Character position where section starts
        end_offset: Character position where section ends
        confidence: Detection confidence score (0.0-1.0)
        detection_method: How section was detected ('toc', 'heading', 'pattern')
        validated: Whether section has been cross-validated
        part: Optional part identifier for 10-Q filings ("I", "II", or None for 10-K)
        item: Optional item identifier (e.g., "1", "1A", "2")
        _text_extractor: Optional callback for lazy text extraction (for TOC-based sections)
    """
    name: str
    title: str
    node: SectionNode
    start_offset: int = 0
    end_offset: int = 0
    confidence: float = 1.0  # Detection confidence (0.0-1.0)
    detection_method: str = 'unknown'  # 'toc', 'heading', 'pattern', or 'unknown'
    validated: bool = False  # Cross-validated flag
    part: Optional[str] = None  # Part identifier for 10-Q: "I", "II", or None for 10-K
    item: Optional[str] = None  # Item identifier: "1", "1A", "2", etc.
    _text_extractor: Optional[Any] = field(default=None, repr=False)  # Callback for lazy text extraction

    def text(self, **kwargs) -> str:
        """Extract text from section."""
        # If we have a text extractor callback (TOC-based sections), use it
        if self._text_extractor is not None:
            return self._text_extractor(self.name, **kwargs)

        # Otherwise extract from node (heading/pattern-based sections)
        from edgar.documents.extractors.text_extractor import TextExtractor
        extractor = TextExtractor(**kwargs)
        return extractor.extract_from_node(self.node)

    def tables(self) -> List[TableNode]:
        """Get all tables in section."""
        return self.node.find(lambda n: isinstance(n, TableNode))
```

**File:** edgar/documents/document.py (L718-741)

```python
    def to_dataframe(self) -> 'pd.DataFrame':
        """
        Convert document tables to pandas DataFrame.

        Returns a DataFrame with all tables concatenated.
        """
        import pandas as pd

        if not self.tables:
            return pd.DataFrame()

        # Convert each table to DataFrame
        dfs = []
        for i, table in enumerate(self.tables):
            df = table.to_dataframe()
            # Add table index
            df['_table_index'] = i
            df['_table_type'] = table.table_type.name
            if table.caption:
                df['_table_caption'] = table.caption
            dfs.append(df)

        # Concatenate all tables
        return pd.concat(dfs, ignore_index=True)
```

**File:** edgar/documents/extractors/toc_section_detector.py (L98-104)

```python
                def make_text_extractor(extractor, name):
                    """Create a closure that captures extractor and section name."""
                    def extract_text(section_name=None, **kwargs):
                        # Use captured name, ignore passed section_name
                        clean = kwargs.get('clean', True)
                        return extractor.get_section_text(name, include_subsections=True, clean=clean) or ""
                    return extract_text
```

**File:** edgar/documents/extractors/toc_section_detector.py (L110-121)

```python
                section = Section(
                    name=section_name,
                    title=section_info.get('canonical_name', section_name),
                    node=section_node,
                    start_offset=0,  # Would need actual offsets from parsing
                    end_offset=section_length,
                    confidence=0.95,  # TOC-based = high confidence
                    detection_method='toc',
                    part=part,
                    item=item,
                    _text_extractor=make_text_extractor(self.extractor, section_name)
                )
```

**File:** edgar/documents/migration.py (L15-106)

```python
class LegacyHTMLDocument:
    """
    Compatibility wrapper that mimics the old Document API.

    This allows existing code to work with the new parser
    while providing deprecation warnings.
    """

    def __init__(self, new_document: Document):
        """Initialize with new document."""
        self._doc = new_document
        self._warn_on_use = True

    def _deprecation_warning(self, old_method: str, new_method: str = None):
        """Issue deprecation warning."""
        if self._warn_on_use:
            msg = f"Document.{old_method} is deprecated."
            if new_method:
                msg += f" Use {new_method} instead."
            warnings.warn(msg, DeprecationWarning, stacklevel=3)

    @property
    def text(self) -> str:
        """Get document text (old API)."""
        self._deprecation_warning("text", "Document.text()")
        return self._doc.text()

    def get_text(self, clean: bool = True) -> str:
        """Get text with options (old API)."""
        self._deprecation_warning("get_text()", "Document.text()")
        return self._doc.text()

    @property
    def tables(self) -> List[Any]:
        """Get tables (old API)."""
        self._deprecation_warning("tables", "Document.tables")
        return self._doc.tables

    def find_all(self, tag: str) -> List[Any]:
        """Find elements by tag (old API)."""
        self._deprecation_warning("find_all()", "Document.root.find()")

        # Map old tag names to node types
        from edgar.documents.types import NodeType

        tag_map = {
            'h1': NodeType.HEADING,
            'h2': NodeType.HEADING,
            'h3': NodeType.HEADING,
            'p': NodeType.PARAGRAPH,
            'table': NodeType.TABLE,
        }

        node_type = tag_map.get(tag.lower())
        if node_type:
            return self._doc.root.find(lambda n: n.type == node_type)

        return []

    def search(self, pattern: str) -> List[str]:
        """Search document (old API)."""
        self._deprecation_warning("search()", "DocumentSearch.search()")

        search = DocumentSearch(self._doc)
        results = search.search(pattern)
        return [r.text for r in results]

    @property
    def sections(self) -> Dict[str, Any]:
        """Get sections (old API)."""
        # Convert new sections to old format
        new_sections = self._doc.sections
        old_sections = {}

        for name, section in new_sections.items():
            old_sections[name] = {
                'title': section.title,
                'text': section.text(),
                'start': section.start_offset,
                'end': section.end_offset
            }

        return old_sections

    def to_markdown(self) -> str:
        """Convert to markdown (old API)."""
        self._deprecation_warning("to_markdown()", "MarkdownRenderer.render()")

        from edgar.documents.renderers import MarkdownRenderer
        renderer = MarkdownRenderer()
        return renderer.render(self._doc)

```

## Q6

次のようなエラーが出た。

---

AttributeError Traceback (most recent call last)
Cell In[33], line 30
27 tables = document.tables
29 for table in tables:
---> 30 df = table.to_dataframe()
31 print(df)

AttributeError: 'TableNode' object has no attribute 'to_dataframe'

### Answer

エラーメッセージから、`TableNode`オブジェクトに`to_dataframe()`メソッドが存在しないことが原因です。 edgartools:224-315

## 問題の原因

`edgar/files/html.py`の`TableNode`クラスには`to_dataframe()`メソッドが実装されていません。 edgartools:224-315 このクラスは`render()`メソッドのみを持ち、Rich 形式での表示用に設計されています。 edgartools:283-315

## 解決方法

### 方法 1: `Table`ラッパークラスを使用

`edgar/files/docs/filing_document.py`の`Table`クラスは`TableNode`をラップし、`to_dataframe()`メソッドを提供します。 edgartools:17-76

```python
from edgar.files.docs.filing_document import Table

tables = document.tables

for table_node in tables:
    table = Table(table_node)  # TableNodeをTableでラップ
    df = table.to_dataframe()
    print(df)
```

`Table`クラスの`to_dataframe()`メソッドは、内部的に`TableNode`の`_processed`プロパティから処理済みテーブルデータを取得し、pandas DataFrame に変換します。 edgartools:60-69

### 方法 2: 古いパーサーの`TableBlock`を使用

`edgar/files/html_documents.py`の`TableBlock`クラスには`to_dataframe()`メソッドが実装されています。 edgartools:299-319 ただし、これは古いパーサーの一部です。<cite />

### 方法 3: 処理済みテーブルから直接変換

`TableNode`の`_processed`プロパティから直接 DataFrame を作成することもできます:

```python
import pandas as pd

for table_node in tables:
    processed = table_node._processed
    if processed and processed.headers and processed.data_rows:
        df = pd.DataFrame(processed.data_rows, columns=processed.headers)
        print(df)
```

## Notes

新しいドキュメントパーサー(`edgar/documents/`)と古いパーサー(`edgar/files/html.py`)の間には互換性の問題があります。<cite />新しいパーサーの`TableNode`は直接`to_dataframe()`をサポートしていないため、`Table`ラッパークラスを使用するのが推奨される方法です。 edgartools:17-76

Wiki pages you might want to explore:

-   [Document Processing & Utilities (dgunning/edgartools)](/wiki/dgunning/edgartools#7)

### Citations

**File:** edgar/files/html.py (L224-315)

```python
@dataclass
class TableNode(BaseNode):
    content: List[TableRow]
    style: StyleInfo
    _processed_table: Optional[ProcessedTable] = None

    def __post_init__(self):
        super().__init__()

    @property
    def type(self) -> str:
        return 'table'

    @property
    def row_count(self) -> int:
        """Quick count of rows without processing"""
        return len(self.content)

    @property
    def approximate_column_count(self) -> int:
        """Quick approximate of columns using max cells in any row"""
        if not self.content:
            return 0
        return max(row.virtual_columns for row in self.content)

    @cached_property
    def _processed(self) -> Optional[ProcessedTable]:
        """Cached access to processed table"""
        if self._processed_table is None:
            self._processed_table = TableProcessor.process_table(self)
        return self._processed_table

    @property
    def processed_row_count(self) -> int:
        """Accurate row count after processing"""
        if not self._processed:
            return self.row_count
        return len(self._processed.data_rows) + (len(self._processed.headers or []) > 0)

    @property
    def processed_column_count(self) -> int:
        """Accurate column count after processing"""
        if not self._processed:
            return self.approximate_column_count
        if self._processed.headers:
            return len(self._processed.headers)
        elif self._processed.data_rows:
            return len(self._processed.data_rows[0])
        return 0

    def reset_processing(self) -> None:
        """Clear cached processed table"""
        self._processed_table = None
        # Clear cached properties
        try:
            del self._processed
        except AttributeError:
            pass

    def render(self, console_width: int) -> RenderResult:
        from edgar.files.tables import TableProcessor
        processed_table = TableProcessor.process_table(self)
        if not processed_table:
            return None

        # Optimize the table
        column_optimizer:ColumnOptimizer = ColumnOptimizer()
        widths, processed_table = column_optimizer.optimize_columns(processed_table)

        table = Table(
            box=box.SIMPLE,
            border_style="blue",
            padding=(0, 1),
            show_header=bool(processed_table.headers),
            row_styles=["", "gray54"],
            collapse_padding=True,
            width=None
        )

        # Add columns
        for col_idx, alignment in enumerate(processed_table.column_alignments):
            table.add_column(
                header=processed_table.headers[col_idx] if processed_table.headers else None,
                justify=alignment,
                vertical="middle"
            )

        # Add data rows
        for row in processed_table.data_rows:
            table.add_row(*row)

        return table
```

**File:** edgar/files/docs/filing_document.py (L17-76)

```python
class Table:
    """Rich representation of a table in a document."""

    def __init__(self, table_node: TableNode):
        self._node = table_node
        self._processed = None  # Lazy-loaded processed table

    @property
    def rows(self) -> int:
        """Get the number of rows in the table."""
        processed = self._get_processed()
        if processed is None:
            return 0

        # Count header row if present plus data rows
        has_header = processed.headers is not None and len(processed.headers) > 0
        return len(processed.data_rows) + (1 if has_header else 0)

    @property
    def columns(self) -> int:
        """Get the number of columns in the table."""
        processed = self._get_processed()
        if processed is None:
            return 0

        # Use headers if available, otherwise first data row
        if processed.headers and len(processed.headers) > 0:
            return len(processed.headers)
        elif processed.data_rows and len(processed.data_rows) > 0:
            return len(processed.data_rows[0])
        return 0

    def _get_processed(self):
        """Get or create the processed table."""
        if self._processed is None:
            if hasattr(self._node, '_processed'):
                self._processed = self._node._processed
            # Handle case where node doesn't have processed table yet
            if self._processed is None and hasattr(self._node, '_get_processed'):
                # Call node's processing method if available
                self._processed = self._node._get_processed()
        return self._processed

    def to_dataframe(self) -> pd.DataFrame:
        """Convert this table to a pandas DataFrame."""
        processed = self._get_processed()
        if processed and processed.headers and processed.data_rows:
            # Create DataFrame with proper headers and data
            return pd.DataFrame(processed.data_rows, columns=processed.headers)
        elif processed and processed.data_rows:
            # No headers, use numeric column names
            return pd.DataFrame(processed.data_rows)
        return pd.DataFrame()

    def to_markdown(self) -> str:
        """Convert this table to markdown format."""
        df = self.to_dataframe()
        if not df.empty:
            return df.to_markdown()
        return ""
```

**File:** edgar/files/html_documents.py (L299-319)

```python
class TableBlock(Block):
    """
    Represents an HTML table in the document
    """

    def __init__(self, table_element: Tag, **tag):
        super().__init__(text=None, **tag)
        self.table_element = table_element

    @lru_cache()
    def get_text(self):
        _text = table_to_text(self.table_element)
        _text = "\n" + _text + "\n"
        return _text

    def to_dataframe(self) -> pd.DataFrame:
        table_df = table_html_to_dataframe(str(self.table_element))
        return table_df

    def to_markdown(self) -> str:
        return self.to_dataframe().to_markdown() + "\n"
```

## Q7

次のコードで、item7 のテキスト文章とテーブルを分離するにはどうすればいいか。

for filing in filings:
tenk = filing.obj()

    item_1a = tenk["Item 1A"]
    tenk_business = tenk.business
    tenk_risk_factors = tenk.risk_factors
    # print(item_1a)
    # print(tenk_risk_factors)

    item_7 = tenk["Item 7"]
    print(item_7)
    tables = item_7.tables()
    for table in tables:
        df = table.to_dataframe()
        display(df)

### Answer

あなたは`TenK`オブジェクトの`item_7`(Item 7 の MD&A セクション)からテキストとテーブルを分離する方法について質問しています。<cite />

## 問題の理解

現在のコードでは、`tenk["Item 7"]`は文字列(テキスト)を返すため、`.tables()`メソッドは使用できません。 edgartools:287-295 `__getitem__`メソッドは`chunked_document`からテキストのみを抽出します。<cite />

## 解決方法

### 方法 1: 新しいドキュメントパーサーを使用

新しいパーサーの`Document`オブジェクトと`Section`オブジェクトを使用すると、テキストとテーブルを分離できます。 edgartools:58-103

```python
from edgar.documents import HTMLParser

for filing in filings:
    tenk = filing.obj()

    # HTMLを取得してパース
    html_content = tenk._filing.html()
    parser = HTMLParser()
    document = parser.parse(html_content)

    # Item 7のセクションを取得
    if 'item_7' in document.sections:
        item_7_section = document.sections['item_7']

        # テキストを取得
        text = item_7_section.text()
        print(text)

        # テーブルを取得
        tables = item_7_section.tables()
        for table in tables:
            df = table.to_dataframe()
            display(df)
```

`Section`オブジェクトの`tables()`メソッドは、そのセクション内の全ての`TableNode`を返します。 edgartools:101-103

### 方法 2: chunked_document から全テーブルを取得してフィルタリング

`chunked_document.tables()`で全テーブルを取得し、Item 7 に関連するものを手動でフィルタリングする方法もあります。 edgartools:444-448

```python
from edgar.files.docs.filing_document import Table

for filing in filings:
    tenk = filing.obj()

    # テキストを取得
    item_7_text = tenk["Item 7"]
    print(item_7_text)

    # 全テーブルを取得
    all_tables = list(tenk.chunked_document.tables())

    # TableNodeをTableでラップしてDataFrameに変換
    for table_node in all_tables:
        table = Table(table_node)
        df = table.to_dataframe()
        display(df)
```

ただし、この方法では全ドキュメントのテーブルが取得されるため、Item 7 のテーブルのみを特定するのは困難です。<cite />

### 方法 3: SECSectionExtractor を使用

TOC ベースのセクション抽出を使用する方法もあります。 edgartools:131-179

```python
for filing in filings:
    tenk = filing.obj()
    html_content = tenk._filing.html()

    # Documentを作成
    from edgar.documents import HTMLParser
    parser = HTMLParser()
    document = parser.parse(html_content)

    # Item 7のテキストを取得
    item_7_text = document.get_sec_section("Item 7", clean=True)
    print(item_7_text)

    # Item 7のセクションからテーブルを取得
    if 'item_7' in document.sections:
        tables = document.sections['item_7'].tables()
        for table in tables:
            df = table.to_dataframe()
            display(df)
```

## Notes

`tenk["Item 7"]`は文字列を返すため、直接`.tables()`メソッドを呼び出すことはできません。 edgartools:287-295 テキストとテーブルを分離するには、新しいドキュメントパーサーの`Section`オブジェクトを使用するのが最も効率的です。 edgartools:58-103 `Section.text()`でテキストを、`Section.tables()`でテーブルを取得できます。<cite />

Wiki pages you might want to explore:

-   [Working with Filing Objects (dgunning/edgartools)](/wiki/dgunning/edgartools#3.2)

### Citations

**File:** edgar/company_reports.py (L287-295)

```python
    def __getitem__(self, item_or_part: str):
        # Show the item or part from the filing document. e.g. Item 1 Business from 10-K or Part I from 10-Q
        item_text = self.chunked_document[item_or_part]
        if item_text:
            item_text = item_text.rstrip()
            last_line = item_text.split("\n")[-1]
            if re.match(r'^\b(PART\s+[IVXLC]+)\b', last_line):
                item_text = item_text.rstrip(last_line)
        return item_text
```

**File:** edgar/documents/document.py (L58-103)

```python
@dataclass
class Section:
    """
    Document section representation.

    Represents a logical section of the document (e.g., Risk Factors, MD&A).

    Attributes:
        name: Section identifier (e.g., "item_1", "part_i_item_1", "risk_factors")
        title: Display title (e.g., "Item 1 - Business")
        node: Node containing section content
        start_offset: Character position where section starts
        end_offset: Character position where section ends
        confidence: Detection confidence score (0.0-1.0)
        detection_method: How section was detected ('toc', 'heading', 'pattern')
        validated: Whether section has been cross-validated
        part: Optional part identifier for 10-Q filings ("I", "II", or None for 10-K)
        item: Optional item identifier (e.g., "1", "1A", "2")
        _text_extractor: Optional callback for lazy text extraction (for TOC-based sections)
    """
    name: str
    title: str
    node: SectionNode
    start_offset: int = 0
    end_offset: int = 0
    confidence: float = 1.0  # Detection confidence (0.0-1.0)
    detection_method: str = 'unknown'  # 'toc', 'heading', 'pattern', or 'unknown'
    validated: bool = False  # Cross-validated flag
    part: Optional[str] = None  # Part identifier for 10-Q: "I", "II", or None for 10-K
    item: Optional[str] = None  # Item identifier: "1", "1A", "2", etc.
    _text_extractor: Optional[Any] = field(default=None, repr=False)  # Callback for lazy text extraction

    def text(self, **kwargs) -> str:
        """Extract text from section."""
        # If we have a text extractor callback (TOC-based sections), use it
        if self._text_extractor is not None:
            return self._text_extractor(self.name, **kwargs)

        # Otherwise extract from node (heading/pattern-based sections)
        from edgar.documents.extractors.text_extractor import TextExtractor
        extractor = TextExtractor(**kwargs)
        return extractor.extract_from_node(self.node)

    def tables(self) -> List[TableNode]:
        """Get all tables in section."""
        return self.node.find(lambda n: isinstance(n, TableNode))
```

**File:** edgar/files/htmltools.py (L444-448)

```python
    def tables(self):
        for chunk in self.chunks:
            for block in chunk:
                if isinstance(block, TableBlock):
                    yield block
```

**File:** edgar/documents/extractors/toc_section_extractor.py (L131-179)

```python
    def get_section_text(self, section_name: str,
                        include_subsections: bool = True,
                        clean: bool = True) -> Optional[str]:
        """
        Extract text content for a specific section.

        Args:
            section_name: Name of section (e.g., "Item 1", "Item 1A", "Part I")
            include_subsections: Whether to include subsections
            clean: Whether to apply text cleaning

        Returns:
            Section text content or None if section not found
        """
        # Normalize section name
        normalized_name = self._normalize_section_name(section_name)

        if normalized_name not in self.section_boundaries:
            return None

        boundary = self.section_boundaries[normalized_name]

        # Extract content between boundaries using HTML parsing
        html_content = getattr(self.document.metadata, 'original_html', None)
        if not html_content:
            return None

        try:
            section_text = self._extract_section_content(html_content, boundary, include_subsections, clean)

            # If no direct content but include_subsections=True, aggregate subsection text
            if not section_text and include_subsections:
                subsections = self._get_subsections(normalized_name)
                if subsections:
                    # Recursively get text from all subsections
                    subsection_texts = []
                    for subsection_name in subsections:
                        subsection_text = self.get_section_text(subsection_name, include_subsections=True, clean=clean)
                        if subsection_text:
                            subsection_texts.append(subsection_text)

                    if subsection_texts:
                        section_text = '\n\n'.join(subsection_texts)

            return section_text
        except Exception as e:
            # Fallback to simple text extraction
            return self._extract_section_fallback(section_name, clean)

```

## Q8

---

KeyError Traceback (most recent call last)
Cell In[40], line 25
23 document = parser.parse(html_content)
24 print(document.sections)
---> 25 item_7_section = document.sections['item_7']
26 text = item_7_section.text()
27 print(text)

File /opt/anaconda3/envs/py313/lib/python3.13/site-packages/edgar/documents/document.py:393, in Sections.**getitem**(self, key)
390 return result
392 # Not found - raise KeyError
--> 393 raise KeyError(key)

KeyError: 'item_7'

### Answer

エラーメッセージから、`document.sections`に`'item_7'`というキーが存在しないことが原因です。 edgartools:364-393

## 問題の原因

`document.sections`辞書にセクションが検出されていないか、セクション名が`'item_7'`とは異なる形式で格納されている可能性があります。<cite />

## 解決方法

### 方法 1: 利用可能なセクションを確認

まず、`print(document.sections)`で実際に検出されたセクション名を確認してください:<cite />

```python
from edgar.documents import HTMLParser

for filing in filings:
    tenk = filing.obj()
    html_content = tenk._filing.html()
    parser = HTMLParser()
    document = parser.parse(html_content)

    # 利用可能なセクションを確認
    print(document.sections)
    print(list(document.sections.keys()))
```

### 方法 2: ParserConfig でフォームタイプを指定

セクション検出には、フォームタイプ(10-K)の指定が必要な場合があります。 edgartools:430-448

```python
from edgar.documents import HTMLParser, ParserConfig

for filing in filings:
    tenk = filing.obj()
    html_content = tenk._filing.html()

    # ParserConfigでフォームタイプを指定
    config = ParserConfig(form='10-K')
    parser = HTMLParser()
    document = parser.parse(html_content, config)

    print(document.sections)

    # Item 7を取得
    if 'item_7' in document.sections:
        item_7_section = document.sections['item_7']
        text = item_7_section.text()
        tables = item_7_section.tables()
```

### 方法 3: 柔軟なキーアクセスを使用

`Sections`クラスは柔軟なキーアクセスをサポートしています。 edgartools:266-302

```python
# 複数の形式で試す
item_7_section = document.sections.get_item("7")  # Item番号で取得
# または
item_7_section = document.sections.get("Item 7")  # 柔軟なget
```

### 方法 4: get_sec_section メソッドを使用

セクションが検出されない場合は、`get_sec_section`メソッドでテキストを直接取得できます。 edgartools:612-637

```python
for filing in filings:
    tenk = filing.obj()
    html_content = tenk._filing.html()
    parser = HTMLParser()
    document = parser.parse(html_content)

    # Item 7のテキストを取得
    item_7_text = document.get_sec_section("Item 7", clean=True)
    if item_7_text:
        print(item_7_text)

    # セクションが検出されている場合のみテーブルを取得
    if 'item_7' in document.sections:
        tables = document.sections['item_7'].tables()
        for table in tables:
            df = table.to_dataframe()
            display(df)
```

## Notes

セクション検出は複数の戦略(TOC、ヘッディング、パターン)を使用しますが、ドキュメントの構造によっては検出に失敗する場合があります。 edgartools:417-458 まず`print(document.sections)`で実際に検出されたセクション名を確認し、適切なキーを使用してください。<cite />また、`ParserConfig`でフォームタイプを明示的に指定することで、検出精度が向上する可能性があります。 edgartools:432-442

Wiki pages you might want to explore:

-   [Overview (dgunning/edgartools)](/wiki/dgunning/edgartools#1)

### Citations

**File:** edgar/documents/document.py (L266-302)

```python
    def get_item(self, item: str, part: str = None) -> Optional[Section]:
        """
        Get section by item number with optional part specification.

        Args:
            item: Item identifier (e.g., "1", "1A", "7", "Item 1", "Item 7A")
            part: Optional part specification (e.g., "I", "II", "Part I", "Part II")
                  If not specified and multiple parts contain the item, returns first match.

        Returns:
            Section object if found, None otherwise

        Examples:
            >>> sections.get_item("1")           # Returns first Item 1 (any part)
            >>> sections.get_item("1", "I")      # Returns Part I, Item 1
            >>> sections.get_item("Item 1A")     # Returns first Item 1A
            >>> sections.get_item("7A", "II")    # Returns Part II, Item 7A
        """
        # Normalize item string - remove "Item " prefix if present
        item_clean = item.replace("Item ", "").replace("item ", "").strip().upper()

        # Normalize part string if provided
        part_clean = None
        if part:
            part_clean = part.replace("Part ", "").replace("part ", "").replace("PART ", "").strip().upper()

        # Search through sections
        for name, section in self.items():
            if section.item and section.item.upper() == item_clean:
                if part_clean is None:
                    # No part specified - return first match
                    return section
                elif section.part and section.part.upper() == part_clean:
                    # Part matches
                    return section

        return None
```

**File:** edgar/documents/document.py (L364-393)

```python
    def __getitem__(self, key):
        """
        Enhanced __getitem__ that supports flexible key formats.

        Supports:
        - Standard dict key: sections["part_i_item_1"]
        - Item number: sections["Item 1"], sections["1A"]
        - Part+Item tuple: sections[("I", "1")], sections[("II", "7A")]

        Raises KeyError if not found (standard dict behavior).
        """
        # Try standard dict lookup first
        if isinstance(key, str):
            try:
                return super().__getitem__(key)
            except KeyError:
                # Try as item number
                result = self.get_item(key)
                if result is not None:
                    return result

        # Try as (part, item) tuple
        elif isinstance(key, tuple) and len(key) == 2:
            part, item = key
            result = self.get_item(item, part)
            if result is not None:
                return result

        # Not found - raise KeyError
        raise KeyError(key)
```

**File:** edgar/documents/document.py (L417-458)

```python
    @property
    def sections(self) -> Sections:
        """
        Get document sections using hybrid multi-strategy detection.

        Tries detection methods in order of reliability:
        1. TOC-based (0.95 confidence)
        2. Heading-based (0.7-0.9 confidence)
        3. Pattern-based (0.6 confidence)

        Returns a Sections dictionary wrapper that provides rich terminal display
        via __rich__() method. Each section includes confidence score and detection method.
        """
        if self._sections is None:
            # Get form type from config or metadata
            form = None
            if self._config and hasattr(self._config, 'form'):
                form = self._config.form
            elif self.metadata and self.metadata.form:
                form = self.metadata.form

            # Only detect sections for supported form types (including amendments)
            # Normalize form type by removing /A suffix for amendments
            base_form = form.replace('/A', '') if form else None

            if base_form and base_form in ['10-K', '10-Q', '8-K']:
                from edgar.documents.extractors.hybrid_section_detector import HybridSectionDetector
                # Pass thresholds from config if available
                thresholds = self._config.detection_thresholds if self._config else None
                # Use base form type for detection (10-K/A → 10-K)
                detector = HybridSectionDetector(self, base_form, thresholds)
                detected_sections = detector.detect_sections()
            else:
                # Fallback to pattern-based for other types or unknown
                from edgar.documents.extractors.pattern_section_extractor import SectionExtractor
                extractor = SectionExtractor(form) if form else SectionExtractor()
                detected_sections = extractor.extract(self)

            # Wrap detected sections in Sections class for rich display
            self._sections = Sections(detected_sections)

        return self._sections
```

**File:** edgar/documents/document.py (L612-637)

```python
    def get_sec_section(self, section_name: str, clean: bool = True,
                       include_subsections: bool = True) -> Optional[str]:
        """
        Extract content from a specific SEC filing section using anchor analysis.

        Args:
            section_name: Section name (e.g., "Item 1", "Item 1A", "Part I")
            clean: Whether to apply text cleaning and navigation filtering
            include_subsections: Whether to include subsections

        Returns:
            Section text content or None if section not found

        Examples:
            >>> doc.get_sec_section("Item 1")  # Business description
            >>> doc.get_sec_section("Item 1A") # Risk factors
            >>> doc.get_sec_section("Item 7")  # MD&A
        """
        # Lazy-load section extractor
        if not hasattr(self, '_section_extractor'):
            from edgar.documents.extractors.toc_section_extractor import SECSectionExtractor
            self._section_extractor = SECSectionExtractor(self)

        return self._section_extractor.get_section_text(
            section_name, include_subsections, clean
        )
```

## Q9

document.sections を表示したら、No

### Answer

ユーザーは`document.sections`を表示したところ、「No」という結果が表示されたと報告しています。 edgartools:183-186 これは、セクションが検出されなかった場合に`Sections`クラスの`__rich__()`メソッドが「No sections detected」というメッセージを返すためです。 edgartools:183-186

## 問題の原因

セクションが検出されない主な原因は以下の通りです:

1. **フォームタイプが指定されていない**: `ParserConfig`で`form='10-K'`を明示的に指定していない edgartools:431-441
2. **original_html が利用できない**: TOC ベースの検出に必要な`metadata.original_html`が設定されていない edgartools:57-61
3. **ドキュメント構造の問題**: HTML の構造が標準的でなく、全ての検出戦略が失敗している edgartools:64-86

## 解決方法

### 方法 1: ParserConfig でフォームタイプを明示的に指定

```python
from edgar.documents import HTMLParser, ParserConfig

for filing in filings:
    tenk = filing.obj()
    html_content = tenk._filing.html()

    # フォームタイプを明示的に指定
    config = ParserConfig(form='10-K')
    parser = HTMLParser(config)
    document = parser.parse(html_content)

    print(document.sections)
```

`ParserConfig`で`form='10-K'`を指定すると、ハイブリッド検出器が 10-K 用のセクション検出を実行します。 edgartools:438-448

### 方法 2: 古いパーサーの`chunked_document`を使用

新しいパーサーでセクションが検出されない場合は、`TenK`オブジェクトの既存の`chunked_document`を使用する方が確実です:

```python
for filing in filings:
    tenk = filing.obj()

    # 既存のchunked_documentを使用
    item_7_text = tenk["Item 7"]
    print(item_7_text)

    # 全テーブルを取得
    from edgar.files.docs.filing_document import Table
    all_tables = list(tenk.chunked_document.tables())

    for table_node in all_tables:
        table = Table(table_node)
        df = table.to_dataframe()
        display(df)
```

### 方法 3: get_sec_section メソッドを使用

セクション検出に失敗しても、`get_sec_section`メソッドは TOC 解析を使用してテキストを抽出できます:

````python
for filing in filings:
    tenk = filing.obj()
    html_content = tenk._filing.html()
    parser = HTMLParser()
    document = parser.parse(html_content)

    # TOCベースの抽出を試す
    item_7_text = document.get_sec_section("Item 7", clean=True)
    if item_7_text:
        print(item_7_text)
    else:
        print("Item 7が見つかりませんでした")
``` edgartools:612-637

## Notes

新しいドキュメントパーサーのセクション検出は、TOC、ヘッディング、パターンの3つの戦略を順番に試しますが、全て失敗すると空の辞書を返します。 edgartools:64-86 この場合、`TenK`オブジェクトの既存の`__getitem__`メソッド(`tenk["Item 7"]`)を使用する方が確実です。 edgartools:286-294

Wiki pages you might want to explore:
- [Overview (dgunning/edgartools)](/wiki/dgunning/edgartools#1)
### Citations
**File:** edgar/documents/document.py (L183-186)
```python
    def __rich__(self):
        """Return rich representation for display."""
        if not self:
            return Text("No sections detected", style="dim")
````

**File:** edgar/documents/document.py (L431-448)

```python
            # Get form type from config or metadata
            form = None
            if self._config and hasattr(self._config, 'form'):
                form = self._config.form
            elif self.metadata and self.metadata.form:
                form = self.metadata.form

            # Only detect sections for supported form types (including amendments)
            # Normalize form type by removing /A suffix for amendments
            base_form = form.replace('/A', '') if form else None

            if base_form and base_form in ['10-K', '10-Q', '8-K']:
                from edgar.documents.extractors.hybrid_section_detector import HybridSectionDetector
                # Pass thresholds from config if available
                thresholds = self._config.detection_thresholds if self._config else None
                # Use base form type for detection (10-K/A → 10-K)
                detector = HybridSectionDetector(self, base_form, thresholds)
                detected_sections = detector.detect_sections()
```

**File:** edgar/documents/document.py (L612-637)

```python
    def get_sec_section(self, section_name: str, clean: bool = True,
                       include_subsections: bool = True) -> Optional[str]:
        """
        Extract content from a specific SEC filing section using anchor analysis.

        Args:
            section_name: Section name (e.g., "Item 1", "Item 1A", "Part I")
            clean: Whether to apply text cleaning and navigation filtering
            include_subsections: Whether to include subsections

        Returns:
            Section text content or None if section not found

        Examples:
            >>> doc.get_sec_section("Item 1")  # Business description
            >>> doc.get_sec_section("Item 1A") # Risk factors
            >>> doc.get_sec_section("Item 7")  # MD&A
        """
        # Lazy-load section extractor
        if not hasattr(self, '_section_extractor'):
            from edgar.documents.extractors.toc_section_extractor import SECSectionExtractor
            self._section_extractor = SECSectionExtractor(self)

        return self._section_extractor.get_section_text(
            section_name, include_subsections, clean
        )
```

**File:** edgar/documents/extractors/toc_section_detector.py (L57-61)

```python
        # Check if original HTML is available
        html_content = getattr(self.document.metadata, 'original_html', None)
        if not html_content:
            logger.debug("TOC detection unavailable: original_html not in document metadata")
            return None
```

**File:** edgar/documents/extractors/hybrid_section_detector.py (L64-86)

```python
        # Strategy 1: TOC-based (most reliable)
        logger.debug("Trying TOC-based detection...")
        sections = self.toc_detector.detect()
        if sections:
            logger.info(f"TOC detection successful: {len(sections)} sections found")
            return self._validate_pipeline(sections, enable_cross_validation=True)

        # Strategy 2: Heading-based (fallback)
        logger.debug("TOC detection failed, trying heading detection...")
        sections = self._try_heading_detection()
        if sections:
            logger.info(f"Heading detection successful: {len(sections)} sections found")
            return self._validate_pipeline(sections, enable_cross_validation=False)

        # Strategy 3: Pattern-based (last resort)
        logger.debug("Heading detection failed, trying pattern matching...")
        sections = self._try_pattern_detection()
        if sections:
            logger.info(f"Pattern detection successful: {len(sections)} sections found")
            return self._validate_pipeline(sections, enable_cross_validation=False)

        logger.warning("All detection strategies failed, no sections found")
        return {}
```

## Q10

このコードで、各セクションにテーブルがあるかどうかを判定しようとしたが、全てのセクションでテーブルを格納したデータフレームが検出されなかった。何が問題か。

filings = edgar_utils.get_filings_single_ticker(
"AAPL", "10-K", "2024-01-01", "2024-12-31"
)

for filing in filings:
tenk = filing.obj()

    item_1a = tenk["Item 1A"]  # type: ignore
    tenk_business = tenk.business  # type: ignore
    tenk_risk_factors = tenk.risk_factors  # type: ignore

    html_content = tenk._filing.html()  # type: ignore
    # フォームタイプを明示的に指定する
    config = ParserConfig(form="10-K")
    parser = HTMLParser(config)
    document = parser.parse(html_content)
    print(document.sections)

    for section in document.sections:
        print(f"{'='*20} Section: {section} {'='*20}")
        item_section = document.sections.get(section)
        text = item_section.text()  # type: ignore
        tables = item_section.tables()  # type: ignore
        for table_node in tables:
            df = Table(table_node).to_dataframe()
            if not df.empty:
                display(df.head())
                print(text)

    # management_discussion = tenk.management_discussion
    # # print(management_discussion)
    # # print(type(management_discussion))

    # all_tables = tenk.chunked_document.tables()
    # # for table in all_tables:
    # #     print(table)

    # html_content = tenk._filing.html()
    # document = Document.parse(html_content)
    # tables = document.tables

    # for table_node in tables:
    #     table = Table(table_node=table_node)
    #     df = table.to_dataframe()
    #     display(df)

### Answer

ユーザーは新しいドキュメントパーサー(`HTMLParser`)を使用して 10-K の各セクションからテーブルを抽出しようとしていますが、全てのセクションでテーブルが検出されない問題に直面しています。 edgartools:101-103

## 問題の原因

コードには 2 つの主な問題があります:

### 1. `TableNode`に`to_dataframe()`メソッドが存在しない

新しいパーサー(`edgar/documents/`)の`TableNode`は、古いパーサーの`TableNode`とは異なるクラスです。 edgartools:1-50 新しい`TableNode`には直接`to_dataframe()`メソッドが実装されていない可能性があります。<cite />

コード内で`Table(table_node).to_dataframe()`を呼び出していますが、この`Table`クラスは古いパーサー用のラッパークラス(`edgar/files/docs/filing_document.py`)であり、新しいパーサーの`TableNode`とは互換性がありません。<cite />

### 2. パーサーの互換性の問題

`HTMLParser`(新しいパーサー)と`Document.parse()`(古いパーサー)を混在させています。 edgartools:15-106 新しいパーサーの`TableNode`は古いパーサーの`Table`ラッパークラスでは処理できません。<cite />

## 解決方法

### 方法 1: 新しいパーサーの`TableNode.to_dataframe()`を直接使用

新しいパーサーの`TableNode`が`to_dataframe()`メソッドを持っている場合、直接呼び出します:

````python
from edgar.documents import HTMLParser, ParserConfig

filings = edgar_utils.get_filings_single_ticker(
    "AAPL", "10-K", "2024-01-01", "2024-12-31"
)

for filing in filings:
    tenk = filing.obj()
    html_content = tenk._filing.html()

    config = ParserConfig(form="10-K")
    parser = HTMLParser(config)
    document = parser.parse(html_content)

    print(document.sections)

    for section_name in document.sections:
        print(f"{'='*20} Section: {section_name} {'='*20}")
        section = document.sections.get(section_name)

        if section:
            text = section.text()
            tables = section.tables()

            for table_node in tables:
                # 新しいパーサーのTableNodeを直接使用
                try:
                    df = table_node.to_dataframe()
                    if not df.empty:
                        display(df.head())
                        print(f"Found table in {section_name}")
                except AttributeError:
                    print(f"TableNode does not have to_dataframe() method")
``` edgartools:717-740

### 方法2: 古いパーサーを使用(推奨)

セクション検出が失敗している場合、`TenK`オブジェクトの既存の`chunked_document`を使用する方が確実です:

```python
from edgar.files.docs.filing_document import Table

filings = edgar_utils.get_filings_single_ticker(
    "AAPL", "10-K", "2024-01-01", "2024-12-31"
)

for filing in filings:
    tenk = filing.obj()

    # 各セクションのテキストを取得
    sections = {
        "Item 1": tenk.business,
        "Item 1A": tenk.risk_factors,
        "Item 7": tenk.management_discussion,
        "Item 10": tenk.directors_officers_and_governance
    }

    # 全テーブルを取得
    all_tables = list(tenk.chunked_document.tables())

    for section_name, section_text in sections.items():
        print(f"{'='*20} Section: {section_name} {'='*20}")

        # セクション内のテーブルを検出(簡易的な方法)
        for table_node in all_tables:
            table = Table(table_node)
            df = table.to_dataframe()
            if not df.empty:
                display(df.head())
``` edgartools:258-272

### 方法3: Document.parse()を使用

古いパーサーの`Document.parse()`を使用してテーブルを抽出:

```python
from edgar.files.html import Document
from edgar.files.docs.filing_document import Table

for filing in filings:
    tenk = filing.obj()
    html_content = tenk._filing.html()

    # 古いパーサーを使用
    document = Document.parse(html_content)
    tables = document.tables

    print(f"Total tables found: {len(tables)}")

    for table_node in tables:
        table = Table(table_node=table_node)
        df = table.to_dataframe()
        if not df.empty:
            display(df.head())
``` edgartools:15-17

## Notes

新しいパーサー(`HTMLParser`)でセクション検出が「No sections detected」となっている場合、セクション内のテーブルも取得できません。 edgartools:417-458 この場合、古いパーサーの`Document.parse()`または`TenK`オブジェクトの既存メソッド(`tenk.chunked_document.tables()`)を使用する方が確実です。 edgartools:274-276

新しいパーサーと古いパーサーの`TableNode`は異なるクラスであり、互換性がないため、混在させないように注意してください。 edgartools:205-299

Wiki pages you might want to explore:
- [Document Processing & Utilities (dgunning/edgartools)](/wiki/dgunning/edgartools#7)
### Citations
**File:** edgar/documents/document.py (L101-103)
```python
    def tables(self) -> List[TableNode]:
        """Get all tables in section."""
        return self.node.find(lambda n: isinstance(n, TableNode))
````

**File:** edgar/documents/document.py (L417-458)

```python
    @property
    def sections(self) -> Sections:
        """
        Get document sections using hybrid multi-strategy detection.

        Tries detection methods in order of reliability:
        1. TOC-based (0.95 confidence)
        2. Heading-based (0.7-0.9 confidence)
        3. Pattern-based (0.6 confidence)

        Returns a Sections dictionary wrapper that provides rich terminal display
        via __rich__() method. Each section includes confidence score and detection method.
        """
        if self._sections is None:
            # Get form type from config or metadata
            form = None
            if self._config and hasattr(self._config, 'form'):
                form = self._config.form
            elif self.metadata and self.metadata.form:
                form = self.metadata.form

            # Only detect sections for supported form types (including amendments)
            # Normalize form type by removing /A suffix for amendments
            base_form = form.replace('/A', '') if form else None

            if base_form and base_form in ['10-K', '10-Q', '8-K']:
                from edgar.documents.extractors.hybrid_section_detector import HybridSectionDetector
                # Pass thresholds from config if available
                thresholds = self._config.detection_thresholds if self._config else None
                # Use base form type for detection (10-K/A → 10-K)
                detector = HybridSectionDetector(self, base_form, thresholds)
                detected_sections = detector.detect_sections()
            else:
                # Fallback to pattern-based for other types or unknown
                from edgar.documents.extractors.pattern_section_extractor import SectionExtractor
                extractor = SectionExtractor(form) if form else SectionExtractor()
                detected_sections = extractor.extract(self)

            # Wrap detected sections in Sections class for rich display
            self._sections = Sections(detected_sections)

        return self._sections
```

**File:** edgar/documents/document.py (L717-740)

```python

    def to_dataframe(self) -> 'pd.DataFrame':
        """
        Convert document tables to pandas DataFrame.

        Returns a DataFrame with all tables concatenated.
        """
        import pandas as pd

        if not self.tables:
            return pd.DataFrame()

        # Convert each table to DataFrame
        dfs = []
        for i, table in enumerate(self.tables):
            df = table.to_dataframe()
            # Add table index
            df['_table_index'] = i
            df['_table_type'] = table.table_type.name
            if table.caption:
                df['_table_caption'] = table.caption
            dfs.append(df)

        # Concatenate all tables
```

**File:** edgar/documents/migration.py (L15-106)

```python
class LegacyHTMLDocument:
    """
    Compatibility wrapper that mimics the old Document API.

    This allows existing code to work with the new parser
    while providing deprecation warnings.
    """

    def __init__(self, new_document: Document):
        """Initialize with new document."""
        self._doc = new_document
        self._warn_on_use = True

    def _deprecation_warning(self, old_method: str, new_method: str = None):
        """Issue deprecation warning."""
        if self._warn_on_use:
            msg = f"Document.{old_method} is deprecated."
            if new_method:
                msg += f" Use {new_method} instead."
            warnings.warn(msg, DeprecationWarning, stacklevel=3)

    @property
    def text(self) -> str:
        """Get document text (old API)."""
        self._deprecation_warning("text", "Document.text()")
        return self._doc.text()

    def get_text(self, clean: bool = True) -> str:
        """Get text with options (old API)."""
        self._deprecation_warning("get_text()", "Document.text()")
        return self._doc.text()

    @property
    def tables(self) -> List[Any]:
        """Get tables (old API)."""
        self._deprecation_warning("tables", "Document.tables")
        return self._doc.tables

    def find_all(self, tag: str) -> List[Any]:
        """Find elements by tag (old API)."""
        self._deprecation_warning("find_all()", "Document.root.find()")

        # Map old tag names to node types
        from edgar.documents.types import NodeType

        tag_map = {
            'h1': NodeType.HEADING,
            'h2': NodeType.HEADING,
            'h3': NodeType.HEADING,
            'p': NodeType.PARAGRAPH,
            'table': NodeType.TABLE,
        }

        node_type = tag_map.get(tag.lower())
        if node_type:
            return self._doc.root.find(lambda n: n.type == node_type)

        return []

    def search(self, pattern: str) -> List[str]:
        """Search document (old API)."""
        self._deprecation_warning("search()", "DocumentSearch.search()")

        search = DocumentSearch(self._doc)
        results = search.search(pattern)
        return [r.text for r in results]

    @property
    def sections(self) -> Dict[str, Any]:
        """Get sections (old API)."""
        # Convert new sections to old format
        new_sections = self._doc.sections
        old_sections = {}

        for name, section in new_sections.items():
            old_sections[name] = {
                'title': section.title,
                'text': section.text(),
                'start': section.start_offset,
                'end': section.end_offset
            }

        return old_sections

    def to_markdown(self) -> str:
        """Convert to markdown (old API)."""
        self._deprecation_warning("to_markdown()", "MarkdownRenderer.render()")

        from edgar.documents.renderers import MarkdownRenderer
        renderer = MarkdownRenderer()
        return renderer.render(self._doc)

```

**File:** edgar/documents/migration.py (L205-299)

```python
class MigrationGuide:
    """
    Provides migration guidance and utilities.
    """

    @staticmethod
    def check_compatibility(old_parser_instance) -> Dict[str, Any]:
        """
        Check if old parser instance can be migrated.

        Returns:
            Dict with compatibility info
        """
        return {
            'can_migrate': True,
            'warnings': [],
            'recommendations': [
                "Replace SECHTMLParser with HTMLParser",
                "Update document.text to document.text()",
                "Use DocumentSearch for search functionality",
                "Use MarkdownRenderer for markdown conversion"
            ]
        }

    @staticmethod
    def print_migration_guide():
        """Print migration guide."""
        guide = """
        HTML Parser Migration Guide
        ==========================

        The new HTML parser provides significant improvements:
        - 10x performance improvement
        - Better table parsing
        - Reliable section detection
        - Advanced search capabilities

        Key Changes:
        -----------

        1. Imports:
           OLD: from edgar.files.html import SECHTMLParser, Document
           NEW: from edgar.documents import HTMLParser, Document

        2. Parser Creation:
           OLD: parser = SECHTMLParser()
           NEW: parser = HTMLParser()

        3. Document Text:
           OLD: document.text or document.get_text()
           NEW: document.text()

        4. Search:
           OLD: document.search(pattern)
           NEW: search = DocumentSearch(document)
                results = search.search(pattern)

        5. Tables:
           OLD: document.tables
           NEW: document.tables (same, but returns richer TableNode objects)

        6. Sections:
           OLD: document.sections
           NEW: document.sections (returns Section objects with more features)

        7. Markdown:
           OLD: document.to_markdown()
           NEW: renderer = MarkdownRenderer()
                markdown = renderer.render(document)

        Compatibility:
        -------------

        For gradual migration, use the compatibility layer:

        from edgar.documents.migration import LegacySECHTMLParser
        parser = LegacySECHTMLParser()  # Works like old parser

        This will issue deprecation warnings to help you migrate.

        Performance Config:
        ------------------

        For best performance:
        parser = HTMLParser.create_for_performance()

        For best accuracy:
        parser = HTMLParser.create_for_accuracy()

        For AI/LLM processing:
        parser = HTMLParser.create_for_ai()
        """

        print(guide)

```

**File:** tests/test_html.py (L15-17)

```python
def test_parse_html_with_table():
    document = Document.parse(get_html('data/html/OneTable.html'))
    assert len(document.tables) == 1
```

## Q11

このコードではセクションとテキストは取得できているが、テーブルを格納したデータフレームが全てのセクションで空である。どうすればいいか。

filings = edgar_utils.get_filings_single_ticker(
"AAPL", "10-K", "2024-01-01", "2024-12-31"
)

for filing in filings:
tenk = filing.obj()

    item_1a = tenk["Item 1A"]  # type: ignore
    tenk_business = tenk.business  # type: ignore
    tenk_risk_factors = tenk.risk_factors  # type: ignore

    html_content = tenk._filing.html()  # type: ignore
    # フォームタイプを明示的に指定する
    config = ParserConfig(form="10-K")
    parser = HTMLParser(config)
    document = parser.parse(html_content)
    print(document.sections)

    for section in document.sections:
        print(f"{'='*20} Section: {section} {'='*20}")
        item_section = document.sections.get(section)
        if item_section:
            text = item_section.text()
            print(text)
            tables = item_section.tables()

            for table_node in tables:
                try:
                    df = table_node.to_dataframe()
                    if not df.empty:
                        display(df.head())
                except AttributeError:
                    print(f"TableNode does not have to_dataframe() method")

        # text = item_section.text()  # type: ignore
        # tables = item_section.tables()  # type: ignore
        # for table_node in tables:
        #     df = Table(table_node).to_dataframe()
        #     if not df.empty:
        #         display(df.head())
        #         print(text)

    # management_discussion = tenk.management_discussion
    # # print(management_discussion)
    # # print(type(management_discussion))

    # all_tables = tenk.chunked_document.tables()
    # # for table in all_tables:
    # #     print(table)

    # html_content = tenk._filing.html()
    # document = Document.parse(html_content)
    # tables = document.tables

    # for table_node in tables:
    #     table = Table(table_node=table_node)
    #     df = table.to_dataframe()
    #     display(df)

### Answer

ユーザーは新しいドキュメントパーサー(`HTMLParser`)を使用して 10-K の各セクションからテーブルを抽出しようとしていますが、`table_node.to_dataframe()`を呼び出すと全ての DataFrame が空になる問題に直面しています。<cite />

## 問題の原因

新しいパーサー(`edgar/documents/`)の`TableNode`クラスには`to_dataframe()`メソッドが実装されていますが edgartools:718-741 、古いパーサー(`edgar/files/html.py`)の`TableNode`とは異なる実装です。 edgartools:224-315

コードでは`AttributeError`が発生していないため、`to_dataframe()`メソッドは存在しますが、DataFrame が空になっているということは、テーブルデータの処理に問題がある可能性があります。<cite />

## 解決方法

### 方法 1: 古いパーサーの`Document.parse()`を使用(推奨)

新しいパーサーでテーブル抽出がうまくいかない場合、古いパーサーを使用する方が確実です:

```python
from edgar.files.html import Document
from edgar.files.docs.filing_document import Table

filings = edgar_utils.get_filings_single_ticker(
    "AAPL", "10-K", "2024-01-01", "2024-12-31"
)

for filing in filings:
    tenk = filing.obj()
    html_content = tenk._filing.html()

    # 古いパーサーを使用
    document = Document.parse(html_content)
    tables = document.tables

    print(f"Total tables found: {len(tables)}")

    for table_node in tables:
        table = Table(table_node=table_node)
        df = table.to_dataframe()
        if not df.empty:
            display(df.head())
```

古いパーサーの`Table`クラスは`TableNode`をラップし、`_processed`プロパティから処理済みテーブルデータを取得して DataFrame に変換します。 edgartools:17-76

### 方法 2: `chunked_document.tables()`を使用

`TenK`オブジェクトの既存の`chunked_document`を使用する方法:

```python
from edgar.files.docs.filing_document import Table

for filing in filings:
    tenk = filing.obj()

    # 全テーブルを取得
    all_tables = list(tenk.chunked_document.tables())

    print(f"Total tables found: {len(all_tables)}")

    for table_node in all_tables:
        table = Table(table_node)
        df = table.to_dataframe()
        if not df.empty:
            display(df.head())
```

### 方法 3: テーブルの存在を確認

新しいパーサーでテーブルが実際に検出されているか確認:

```python
for section in document.sections:
    print(f"{'='*20} Section: {section} {'='*20}")
    item_section = document.sections.get(section)
    if item_section:
        tables = item_section.tables()
        print(f"Number of tables in {section}: {len(tables)}")

        for i, table_node in enumerate(tables):
            print(f"Table {i}: rows={table_node.row_count if hasattr(table_node, 'row_count') else 'unknown'}")
            try:
                df = table_node.to_dataframe()
                print(f"DataFrame shape: {df.shape}")
                if not df.empty:
                    display(df.head())
            except Exception as e:
                print(f"Error converting table: {e}")
```

## Notes

新しいパーサー(`edgar/documents/`)と古いパーサー(`edgar/files/html.py`)の`TableNode`は異なるクラスであり、テーブル処理の実装も異なります。 edgartools:14-105 古いパーサーの`TableNode`は`TableProcessor`を使用してテーブルを処理し edgartools:78-166 、`_processed`プロパティに処理済みデータを格納します。 edgartools:249-254

新しいパーサーでテーブルが空になる場合は、古いパーサーの`Document.parse()`または`TenK`オブジェクトの`chunked_document.tables()`を使用することを強く推奨します。<cite />

Wiki pages you might want to explore:

-   [Document Processing & Utilities (dgunning/edgartools)](/wiki/dgunning/edgartools#7)

### Citations

**File:** edgar/documents/document.py (L718-741)

```python
    def to_dataframe(self) -> 'pd.DataFrame':
        """
        Convert document tables to pandas DataFrame.

        Returns a DataFrame with all tables concatenated.
        """
        import pandas as pd

        if not self.tables:
            return pd.DataFrame()

        # Convert each table to DataFrame
        dfs = []
        for i, table in enumerate(self.tables):
            df = table.to_dataframe()
            # Add table index
            df['_table_index'] = i
            df['_table_type'] = table.table_type.name
            if table.caption:
                df['_table_caption'] = table.caption
            dfs.append(df)

        # Concatenate all tables
        return pd.concat(dfs, ignore_index=True)
```

**File:** edgar/files/html.py (L224-315)

```python
@dataclass
class TableNode(BaseNode):
    content: List[TableRow]
    style: StyleInfo
    _processed_table: Optional[ProcessedTable] = None

    def __post_init__(self):
        super().__init__()

    @property
    def type(self) -> str:
        return 'table'

    @property
    def row_count(self) -> int:
        """Quick count of rows without processing"""
        return len(self.content)

    @property
    def approximate_column_count(self) -> int:
        """Quick approximate of columns using max cells in any row"""
        if not self.content:
            return 0
        return max(row.virtual_columns for row in self.content)

    @cached_property
    def _processed(self) -> Optional[ProcessedTable]:
        """Cached access to processed table"""
        if self._processed_table is None:
            self._processed_table = TableProcessor.process_table(self)
        return self._processed_table

    @property
    def processed_row_count(self) -> int:
        """Accurate row count after processing"""
        if not self._processed:
            return self.row_count
        return len(self._processed.data_rows) + (len(self._processed.headers or []) > 0)

    @property
    def processed_column_count(self) -> int:
        """Accurate column count after processing"""
        if not self._processed:
            return self.approximate_column_count
        if self._processed.headers:
            return len(self._processed.headers)
        elif self._processed.data_rows:
            return len(self._processed.data_rows[0])
        return 0

    def reset_processing(self) -> None:
        """Clear cached processed table"""
        self._processed_table = None
        # Clear cached properties
        try:
            del self._processed
        except AttributeError:
            pass

    def render(self, console_width: int) -> RenderResult:
        from edgar.files.tables import TableProcessor
        processed_table = TableProcessor.process_table(self)
        if not processed_table:
            return None

        # Optimize the table
        column_optimizer:ColumnOptimizer = ColumnOptimizer()
        widths, processed_table = column_optimizer.optimize_columns(processed_table)

        table = Table(
            box=box.SIMPLE,
            border_style="blue",
            padding=(0, 1),
            show_header=bool(processed_table.headers),
            row_styles=["", "gray54"],
            collapse_padding=True,
            width=None
        )

        # Add columns
        for col_idx, alignment in enumerate(processed_table.column_alignments):
            table.add_column(
                header=processed_table.headers[col_idx] if processed_table.headers else None,
                justify=alignment,
                vertical="middle"
            )

        # Add data rows
        for row in processed_table.data_rows:
            table.add_row(*row)

        return table
```

**File:** edgar/files/docs/filing_document.py (L17-76)

```python
class Table:
    """Rich representation of a table in a document."""

    def __init__(self, table_node: TableNode):
        self._node = table_node
        self._processed = None  # Lazy-loaded processed table

    @property
    def rows(self) -> int:
        """Get the number of rows in the table."""
        processed = self._get_processed()
        if processed is None:
            return 0

        # Count header row if present plus data rows
        has_header = processed.headers is not None and len(processed.headers) > 0
        return len(processed.data_rows) + (1 if has_header else 0)

    @property
    def columns(self) -> int:
        """Get the number of columns in the table."""
        processed = self._get_processed()
        if processed is None:
            return 0

        # Use headers if available, otherwise first data row
        if processed.headers and len(processed.headers) > 0:
            return len(processed.headers)
        elif processed.data_rows and len(processed.data_rows) > 0:
            return len(processed.data_rows[0])
        return 0

    def _get_processed(self):
        """Get or create the processed table."""
        if self._processed is None:
            if hasattr(self._node, '_processed'):
                self._processed = self._node._processed
            # Handle case where node doesn't have processed table yet
            if self._processed is None and hasattr(self._node, '_get_processed'):
                # Call node's processing method if available
                self._processed = self._node._get_processed()
        return self._processed

    def to_dataframe(self) -> pd.DataFrame:
        """Convert this table to a pandas DataFrame."""
        processed = self._get_processed()
        if processed and processed.headers and processed.data_rows:
            # Create DataFrame with proper headers and data
            return pd.DataFrame(processed.data_rows, columns=processed.headers)
        elif processed and processed.data_rows:
            # No headers, use numeric column names
            return pd.DataFrame(processed.data_rows)
        return pd.DataFrame()

    def to_markdown(self) -> str:
        """Convert this table to markdown format."""
        df = self.to_dataframe()
        if not df.empty:
            return df.to_markdown()
        return ""
```

**File:** edgar/files/tables.py (L78-166)

```python
class TableProcessor:
    @staticmethod
    def process_table(node) -> Optional[ProcessedTable]:
        """Process table node into a format ready for rendering"""
        if not isinstance(node.content, list) or not node.content:
            return None

        def process_cell_content(content: Union[str, 'BaseNode']) -> str:
            """Process cell content to handle HTML breaks and cleanup"""
            if isinstance(content, str):
                content = content.replace('<br/>', '\n').replace('<br>', '\n')
                lines = [line.strip() for line in content.split('\n')]
                return '\n'.join(line for line in lines if line)
            else:
                # Recursively process nested nodes
                processed_table = content.render(500)
                return rich_to_text(processed_table)

        # Process all rows into virtual columns
        virtual_rows = []
        max_cols = max(sum(cell.colspan for cell in row.cells) for row in node.content)

        # Convert all rows to virtual columns first
        for row in node.content:
            virtual_row = [""] * max_cols
            current_col = 0

            for cell in row.cells:
                content = process_cell_content(cell.content)

                if '\n' not in content and cell.is_currency and content.replace(',', '').replace('.', '').isdigit():
                    content = f"${float(content.replace(',', '')):,.2f}"

                if cell.colspan > 1:
                    virtual_row[current_col + 1] = content
                else:
                    virtual_row[current_col] = content

                current_col += cell.colspan

            virtual_rows.append(virtual_row)

        # Analyze and remove empty columns
        empty_cols = []
        for col in range(max_cols):
            if all(row[col].strip() == "" for row in virtual_rows):
                empty_cols.append(col)

        # Process empty columns
        cols_to_remove = TableProcessor._get_columns_to_remove(empty_cols, max_cols)

        # Create optimized rows, filtering out empty ones
        optimized_rows = []
        for virtual_row in virtual_rows:
            has_content = any(col.strip() for col in virtual_row)
            if not has_content:
                continue
            optimized_row = [col for idx, col in enumerate(virtual_row) if idx not in cols_to_remove]
            optimized_rows.append(optimized_row)

        if not optimized_rows:
            return None

        # Detect headers
        header_rows, data_start_idx = TableProcessor._analyze_table_structure(optimized_rows)

        # Detect and fix misalignment in all rows
        fixed_rows = TableProcessor._detect_and_fix_misalignment(optimized_rows, data_start_idx)

        # Use the fixed header portion for processing headers
        headers = None
        if header_rows:
            fixed_headers = fixed_rows[:data_start_idx]  # Take header portion from fixed rows
            headers = TableProcessor._merge_header_rows(fixed_headers)

        # Determine column alignments
        col_count = len(optimized_rows[0])
        alignments = TableProcessor._determine_column_alignments(
            optimized_rows, data_start_idx, col_count)

        # Format data rows
        formatted_rows = TableProcessor._format_data_rows(
            optimized_rows[data_start_idx:])

        return ProcessedTable(
            headers=headers,
            data_rows=formatted_rows,
            column_alignments=alignments
        )
```

## Q12

各セクションごとにテキストと表を分離して取得したい。どのようなコードを書けばいいか。

### Answer

ユーザーは 10-K の各セクションごとにテキストと表を分離して取得する方法を求めています。<cite />これまでの会話から、新しいパーサー(`HTMLParser`)でセクション検出やテーブル抽出に問題があったため、古いパーサー(`Document.parse()`)と`TenK`オブジェクトの既存メソッドを組み合わせる方法が最も確実です。<cite />

## 推奨される実装方法

### 方法 1: 古いパーサーとセクションプロパティの組み合わせ(最も確実)

````python
from edgar.files.html import Document
from edgar.files.docs.filing_document import Table

filings = edgar_utils.get_filings_single_ticker(
    "AAPL", "10-K", "2024-01-01", "2024-12-31"
)

for filing in filings:
    tenk = filing.obj()
    html_content = tenk._filing.html()

    # 古いパーサーで全テーブルを取得
    document = Document.parse(html_content)
    all_tables = document.tables

    # 各セクションのテキストを取得
    sections = {
        "Item 1 - Business": tenk.business,
        "Item 1A - Risk Factors": tenk.risk_factors,
        "Item 7 - MD&A": tenk.management_discussion,
        "Item 10 - Governance": tenk.directors_officers_and_governance
    }

    # セクションごとに処理
    for section_name, section_text in sections.items():
        print(f"\n{'='*50}")
        print(f"Section: {section_name}")
        print(f"{'='*50}")

        # テキストを表示
        print(f"\nText length: {len(section_text)} characters")
        print(section_text[:500])  # 最初の500文字を表示

        # 全テーブルを表示(セクション特定は困難)
        print(f"\nAll tables in document: {len(all_tables)}")
``` edgartools:223-314 edgartools:16-75

この方法では、`TenK`オブジェクトの便利プロパティ(`business`, `risk_factors`, `management_discussion`)でテキストを取得し、古いパーサーの`Document.parse()`で全テーブルを取得します。<cite />ただし、特定のセクション内のテーブルのみを識別するのは困難です。<cite />

### 方法2: chunked_documentを使用

```python
from edgar.files.docs.filing_document import Table

for filing in filings:
    tenk = filing.obj()

    # セクションテキストを取得
    sections = {
        "Item 1": tenk.business,
        "Item 1A": tenk.risk_factors,
        "Item 7": tenk.management_discussion,
        "Item 10": tenk.directors_officers_and_governance
    }

    # 全テーブルを取得
    all_tables = list(tenk.chunked_document.tables())

    for section_name, section_text in sections.items():
        print(f"\n{'='*50}")
        print(f"Section: {section_name}")
        print(f"{'='*50}")

        # テキスト
        print(f"Text: {section_text[:300]}...")

        # テーブル(全ドキュメントから)
        print(f"\nTotal tables in document: {len(all_tables)}")
        for i, table_node in enumerate(all_tables[:3]):  # 最初の3つのみ表示
            table = Table(table_node)
            df = table.to_dataframe()
            if not df.empty:
                print(f"\nTable {i+1}:")
                display(df.head())
``` edgartools:258-272

### 方法3: 汎用アクセスメソッドを使用

```python
from edgar.files.html import Document
from edgar.files.docs.filing_document import Table

for filing in filings:
    tenk = filing.obj()
    html_content = tenk._filing.html()

    # 古いパーサーでテーブルを取得
    document = Document.parse(html_content)
    all_tables = document.tables

    # 任意のItemにアクセス
    items = ["Item 1", "Item 1A", "Item 7", "Item 10"]

    for item_name in items:
        print(f"\n{'='*50}")
        print(f"Section: {item_name}")
        print(f"{'='*50}")

        # テキストを取得
        text = tenk[item_name]
        print(f"Text length: {len(text)} characters")
        print(text[:300])

        # テーブル(全ドキュメント)
        print(f"\nTotal tables: {len(all_tables)}")
        for table_node in all_tables[:2]:  # 最初の2つ
            table = Table(table_node=table_node)
            df = table.to_dataframe()
            if not df.empty:
                display(df.head(3))
``` edgartools:286-294

## 重要な注意点

1. **セクション内のテーブル特定は困難**: 現在のAPIでは、特定のセクション内のテーブルのみを確実に識別する方法はありません。<cite />全ドキュメントのテーブルを取得し、手動でフィルタリングする必要があります。<cite />

2. **新しいパーサーの問題**: 新しいパーサー(`HTMLParser`)はセクション検出やテーブル抽出に問題があるため、古いパーサー(`Document.parse()`)の使用を推奨します。 edgartools:14-105

3. **パーサーの互換性**: 新しいパーサーと古いパーサーの`TableNode`は異なるクラスであり、混在させないでください。<cite />

## Notes

最も確実な方法は、`TenK`オブジェクトの既存プロパティ(`business`, `risk_factors`, `management_discussion`)でテキストを取得し、古いパーサーの`Document.parse()`で全テーブルを取得することです。 edgartools:223-314 edgartools:60-69 特定のセクション内のテーブルのみを識別したい場合は、テーブルの内容やキャプションを分析して手動でフィルタリングする必要があります。<cite />

Wiki pages you might want to explore:
- [Overview (dgunning/edgartools)](/wiki/dgunning/edgartools#1)
### Citations
**File:** edgar/files/docs/filing_document.py (L16-75)
```python

class Table:
    """Rich representation of a table in a document."""

    def __init__(self, table_node: TableNode):
        self._node = table_node
        self._processed = None  # Lazy-loaded processed table

    @property
    def rows(self) -> int:
        """Get the number of rows in the table."""
        processed = self._get_processed()
        if processed is None:
            return 0

        # Count header row if present plus data rows
        has_header = processed.headers is not None and len(processed.headers) > 0
        return len(processed.data_rows) + (1 if has_header else 0)

    @property
    def columns(self) -> int:
        """Get the number of columns in the table."""
        processed = self._get_processed()
        if processed is None:
            return 0

        # Use headers if available, otherwise first data row
        if processed.headers and len(processed.headers) > 0:
            return len(processed.headers)
        elif processed.data_rows and len(processed.data_rows) > 0:
            return len(processed.data_rows[0])
        return 0

    def _get_processed(self):
        """Get or create the processed table."""
        if self._processed is None:
            if hasattr(self._node, '_processed'):
                self._processed = self._node._processed
            # Handle case where node doesn't have processed table yet
            if self._processed is None and hasattr(self._node, '_get_processed'):
                # Call node's processing method if available
                self._processed = self._node._get_processed()
        return self._processed

    def to_dataframe(self) -> pd.DataFrame:
        """Convert this table to a pandas DataFrame."""
        processed = self._get_processed()
        if processed and processed.headers and processed.data_rows:
            # Create DataFrame with proper headers and data
            return pd.DataFrame(processed.data_rows, columns=processed.headers)
        elif processed and processed.data_rows:
            # No headers, use numeric column names
            return pd.DataFrame(processed.data_rows)
        return pd.DataFrame()

    def to_markdown(self) -> str:
        """Convert this table to markdown format."""
        df = self.to_dataframe()
        if not df.empty:
            return df.to_markdown()
````
