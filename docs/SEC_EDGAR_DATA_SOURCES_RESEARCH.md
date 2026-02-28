# SEC EDGAR Data Sources for Executive/Insider Financial Profiling

## Research Date: 2026-02-27
## Scope: Programmatic data sources beyond Form 4 for cross-referencing insider trading activity

---

## TABLE OF CONTENTS

1. [SEC EDGAR Full-Text Search API](#1-sec-edgar-full-text-search-api)
2. [SEC EDGAR Submissions/Ownership API](#2-sec-edgar-submissionsownership-api)
3. [DEF 14A Proxy Statements](#3-def-14a-proxy-statements)
4. [Schedule 13D/13G Beneficial Ownership](#4-schedule-13d13g-beneficial-ownership)
5. [Form 3 Initial Statement of Beneficial Ownership](#5-form-3-initial-statement-of-beneficial-ownership)
6. [Form 5 Annual Statement of Changes](#6-form-5-annual-statement-of-changes)
7. [10-K Annual Reports](#7-10-k-annual-reports)
8. [Form 144 Notice of Proposed Sale](#8-form-144-notice-of-proposed-sale)
9. [Insider Transactions Bulk Data Sets](#9-insider-transactions-bulk-data-sets)
10. [Executive Financial Profile Aggregation](#10-executive-financial-profile-aggregation)
11. [Cross-Reference Architecture](#11-cross-reference-architecture)
12. [Rate Limits and Access Requirements](#12-rate-limits-and-access-requirements)

---

## 1. SEC EDGAR FULL-TEXT SEARCH API

### Endpoint
```
POST https://efts.sec.gov/LATEST/search-index
```

This is the same backend that powers the public EDGAR Full-Text Search at
https://www.sec.gov/edgar/search/. It is NOT officially documented by the SEC
as a public API endpoint, but it is openly accessible without authentication.

### Query Parameters

| Parameter      | Type   | Description                                                    |
|----------------|--------|----------------------------------------------------------------|
| `q`            | string | Search terms. Supports quotes for exact phrases.               |
| `entityName`   | string | CIK or beginning/full name of filing entity.                   |
| `forms`        | string | Comma-separated form types (e.g., "4,DEF 14A,10-K,SC 13D").   |
| `dateRange`    | string | One of: `all`, `10y`, `5y`, `1y`, `30d`, `custom`.            |
| `startdt`      | string | Start date (YYYY-MM-DD) when dateRange=custom.                 |
| `enddt`        | string | End date (YYYY-MM-DD) when dateRange=custom.                   |
| `from`         | int    | Offset for pagination (default 0).                             |
| `size`         | int    | Results per page (max 100).                                    |
| `locationCode` | string | State or country code filter.                                  |

### Search Query Syntax
- **Implied AND**: All terms required by default.
- **Exact Phrase**: Use quotation marks: `"material weakness"`.
- **Exclusions**: Prefix with `-` or capitalize `NOT`: `-fraud` or `NOT fraud`.
- **OR logic**: `insider OR outsider`.
- **NEAR proximity**: `NEAR(insider, trading, 5)` -- terms within 5 words.
- **Wildcards**: Append `*` to stem: `compensat*`.
- **Case insensitive**: All searches.

### Searchable Filing Types (relevant to insider profiling)
All EDGAR filing types submitted electronically since 2001 are indexed:
- Forms 3, 4, 5 (ownership)
- DEF 14A (proxy statements)
- 10-K, 10-Q, 8-K (periodic reports)
- SC 13D, SC 13G (beneficial ownership)
- 13F-HR (institutional holdings)
- Form 144 (proposed sale notice)
- Form D (private placements)
- All amendments (e.g., 4/A, 10-K/A, SC 13D/A)

### Response Structure
```json
{
  "hits": {
    "total": {"value": 1234},
    "hits": [
      {
        "_source": {
          "adsh": "0001234567-24-001234",
          "cik": "0000320193",
          "display_names": ["APPLE INC"],
          "form": "DEF 14A",
          "file_date": "2024-01-15",
          "file_description": "Definitive Proxy Statement",
          "file_url": "https://www.sec.gov/Archives/..."
        },
        "_score": 15.234,
        "highlight": {
          "file_content": ["...highlighted <em>match</em>..."]
        }
      }
    ]
  }
}
```

### Cross-Reference with Form 4 Data
- Use `entityName` with an insider's CIK to find all filings mentioning that person.
- Search `q` for an executive's name across all DEF 14A and 10-K filings.
- Correlate filing dates from search results with Form 4 transaction dates.
- Search for specific transaction amounts or share quantities across filings.

### Forensic Use Cases
1. Search for executive name in 8-K filings to find departure/appointment events.
2. Search for "stock option" or "restricted stock" in DEF 14A for compensation grants.
3. Search for "related party" across 10-K filings to find undisclosed relationships.
4. Search for specific entity names from Form 4 footnotes in SC 13D filings.

---

## 2. SEC EDGAR SUBMISSIONS/OWNERSHIP API

### Primary Endpoint (JSON API -- data.sec.gov)
```
GET https://data.sec.gov/submissions/CIK{10-digit-CIK}.json
```

This endpoint works for BOTH companies AND individuals. When called with an
executive's personal CIK, it returns ALL filings that person has made.

### Response Fields (Submissions API)
```json
{
  "cik": "0001234567",
  "entityType": "individual",
  "name": "DOE JOHN A",
  "tickers": [],
  "exchanges": [],
  "formerNames": [{"name": "DOE JOHN", "from": "2015-01-01", "to": "2020-01-01"}],
  "filings": {
    "recent": {
      "accessionNumber": ["0001234567-24-001234", ...],
      "filingDate": ["2024-03-15", ...],
      "reportDate": ["2024-03-14", ...],
      "acceptanceDateTime": ["2024-03-15T16:30:00.000Z", ...],
      "form": ["4", "4", "3", "DEF 14A", ...],
      "primaryDocument": ["xslForm4X01/doc4.xml", ...],
      "primaryDocDescription": ["FORM 4", ...],
      "isXBRL": [0, 0, 0, 1, ...],
      "isInlineXBRL": [0, 0, 0, 1, ...]
    },
    "files": [
      {"name": "CIK0001234567-submissions-001.json", "filingCount": 1000}
    ]
  }
}
```

For entities with >1000 filings, additional files are referenced in the `files`
array and can be fetched at:
```
https://data.sec.gov/submissions/{filename}
```

### Legacy CGI Endpoint (HTML/Atom)
```
GET https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=&dateb=&owner=include&count=40&output=atom
```

| Parameter | Values                                    | Description                     |
|-----------|-------------------------------------------|---------------------------------|
| `action`  | `getcompany`                              | Required action type            |
| `CIK`     | CIK number or ticker                      | Target entity                   |
| `type`    | Form type filter (e.g., `4`, `SC 13D`)    | Empty for all types             |
| `dateb`   | YYYYMMDD                                  | Filings before this date        |
| `owner`   | `include`, `exclude`, `only`              | Ownership filing filter         |
| `count`   | 10-100                                    | Results per page                |
| `output`  | `atom`                                    | Returns Atom XML feed           |

### EDGAR Browse Interface (Current)
```
https://www.sec.gov/edgar/browse/?CIK={cik}&owner=include
```

### Individual Executive Filing History

CRITICAL INSIGHT: Every person who files with the SEC receives their own CIK.
The `data.sec.gov/submissions/CIK{cik}.json` endpoint returns ALL filings by
that CIK, regardless of type. For an individual executive, this means:

- All Form 3 filings (initial ownership at each company)
- All Form 4 filings (transaction reports at each company)
- All Form 5 filings (annual catch-up filings)
- All Form 144 filings (proposed sale notices)
- Any other filings where they are the filer

This is the CLOSEST thing to a "financial profile" view the SEC provides.

### Cross-Reference with Form 4 Data
- The `reporting_owner_cik` in Form 4 XML maps directly to the individual's CIK.
- Call submissions API with the individual's CIK to get their COMPLETE filing history.
- The issuer CIK in each filing links back to the company.
- Match Form 4 transaction dates against 8-K events filed by the company CIK.

### Bulk Download
```
https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip
```
Contains ALL filer submission histories. Size is several GB compressed.

---

## 3. DEF 14A (PROXY STATEMENTS)

### Acquisition Methods

#### Method A: Via Submissions API (recommended)
```
GET https://data.sec.gov/submissions/CIK{company-cik}.json
```
Filter the `filings.recent.form` array for entries matching `"DEF 14A"` or
`"DEFA14A"` (additional definitive proxy material).

#### Method B: Via Full-Text Search
```
POST https://efts.sec.gov/LATEST/search-index
Body: {"q": "executive compensation", "forms": "DEF 14A", "entityName": "0000320193"}
```

#### Method C: Direct Document Fetch
```
GET https://www.sec.gov/Archives/edgar/data/{cik}/{accession-no-dashes}/{primary-doc}
```

### Structured Data Available (Post-2022)

Since fiscal years ending on or after December 16, 2022, the SEC REQUIRES
Inline XBRL tagging for certain portions of DEF 14A using the **Executive
Compensation Disclosure (ECD) taxonomy**.

#### ECD Taxonomy Fields (Machine-Readable)
The following executive compensation data is now available in structured XBRL:

| XBRL Concept                          | Description                              |
|---------------------------------------|------------------------------------------|
| `ecd:PeoTotalCompAmt`                 | PEO (CEO) total compensation             |
| `ecd:PeoActuallyPaidCompAmt`          | PEO compensation actually paid           |
| `ecd:NonPeoNeoAvgTotalCompAmt`        | Average non-PEO NEO total comp           |
| `ecd:NonPeoNeoAvgCompActuallyPaidAmt` | Average non-PEO NEO comp actually paid   |
| `ecd:TotalShareholderRtnAmt`          | Total shareholder return                 |
| `ecd:PeerGroupTotalShareholderRtnAmt` | Peer group TSR                           |
| `ecd:NetIncomeAmt`                    | Company net income                       |
| `ecd:CompActuallyPaidVsTotalShareholderRtnTextBlock` | Pay vs. performance narrative |

Access via Company Facts API:
```
GET https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json
```
Then navigate: `facts > ecd > {concept} > units > USD`

#### XBRL US API (alternative)
```
GET https://api.xbrl.us/api/v1/report/search?report.source-name=sec&report.document-type=DEF 14A&fields=report.document-type,report.entity-name,report.filing-date
```
Note: Requires XBRL US membership for full access.

### Unstructured Data (All Years -- requires NLP/parsing)
- Summary Compensation Table (annual salary, bonus, stock awards, option awards)
- Outstanding Equity Awards at Fiscal Year-End
- Stock Ownership Guidelines
- Beneficial Ownership Table (shares held by officers/directors)
- Director compensation table
- Related party transactions
- Employment agreements
- Change-in-control provisions

### Cross-Reference with Form 4 Data
- Beneficial Ownership Table in DEF 14A shows total shares held as of record date.
- Compare with cumulative Form 4 post-transaction shares for consistency.
- Equity award grants in compensation table should match Form 4 acquisition codes (A, M).
- Stock ownership guidelines reveal minimum holding requirements.
- Employment agreements reveal vesting schedules that correlate with Form 4 exercise patterns.

---

## 4. SCHEDULE 13D/13G (BENEFICIAL OWNERSHIP >5%)

### Acquisition Methods

#### Method A: Via Submissions API
```
GET https://data.sec.gov/submissions/CIK{company-cik}.json
```
Filter for forms: `SC 13D`, `SC 13D/A`, `SC 13G`, `SC 13G/A`.

#### Method B: Via Full-Text Search
```
POST https://efts.sec.gov/LATEST/search-index
Body: {"q": "beneficial ownership", "forms": "SC 13D,SC 13G", "entityName": "{cik}"}
```

#### Method C: Via Legacy CGI
```
GET https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={company-cik}&type=SC+13D&dateb=&owner=include&count=40&output=atom
```

### Data Fields Available

Schedule 13D (active/activist investors):
- Reporting person identity and address
- Amount beneficially owned (shares and percentage)
- Source and amount of funds used for acquisition
- Purpose of transaction (passive, active, control intent)
- Contracts, arrangements, understandings
- Group formation details (wolf pack detection)
- Signature and certification

Schedule 13G (passive investors):
- Reporting person identity
- Amount beneficially owned (shares and percentage)
- Certification of passive intent
- Shared/sole voting power breakdown
- Shared/sole dispositive power breakdown

### Cross-Reference with Form 4 Data
- CIK of reporting person on SC 13D/G matches Form 4 reporting_owner_cik.
- Ownership percentage on SC 13D/G can be compared with Form 4 post-transaction shares.
- SC 13D/A amendments signal changes in intent -- correlate with Form 4 trading patterns.
- Group formation in SC 13D Item 5 reveals wolf pack coordination.
- Filing date gaps: If insider crosses 5% via Form 4 transactions but no SC 13D/G appears
  within 10 days, this is a potential violation (17 CFR 240.13d-1).

---

## 5. FORM 3 (INITIAL STATEMENT OF BENEFICIAL OWNERSHIP)

### Overview
Filed when a person becomes an insider (officer, director, or 10%+ beneficial owner).
Must be filed within 10 days of becoming an insider.

### Acquisition Methods

#### Method A: Via Individual's CIK Submissions
```
GET https://data.sec.gov/submissions/CIK{individual-cik}.json
```
Filter for `form == "3"`. Each Form 3 shows a new insider relationship.

#### Method B: Via Company CIK Submissions
```
GET https://data.sec.gov/submissions/CIK{company-cik}.json
```
Filter for `form == "3"`. Shows all new insiders for the company.

#### Method C: Via Bulk Insider Transactions Data Sets
See Section 9 below.

### XML Structure (Form 3)
```
https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{doc}.xml
```

Key XML elements:
```xml
<ownershipDocument>
  <issuer>
    <issuerCik>0000320193</issuerCik>
    <issuerName>Apple Inc</issuerName>
    <issuerTradingSymbol>AAPL</issuerTradingSymbol>
  </issuer>
  <reportingOwner>
    <reportingOwnerId>
      <rptOwnerCik>0001234567</rptOwnerCik>
      <rptOwnerName>DOE JOHN A</rptOwnerName>
    </reportingOwnerId>
    <reportingOwnerRelationship>
      <isDirector>true</isDirector>
      <isOfficer>true</isOfficer>
      <isTenPercentOwner>false</isTenPercentOwner>
      <officerTitle>Chief Financial Officer</officerTitle>
    </reportingOwnerRelationship>
  </reportingOwner>
  <nonDerivativeTable>
    <nonDerivativeHolding>
      <securityTitle><value>Common Stock</value></securityTitle>
      <postTransactionAmounts>
        <sharesOwnedFollowingTransaction><value>50000</value></sharesOwnedFollowingTransaction>
      </postTransactionAmounts>
      <ownershipNature>
        <directOrIndirectOwnership><value>D</value></directOrIndirectOwnership>
      </ownershipNature>
    </nonDerivativeHolding>
  </nonDerivativeTable>
</ownershipDocument>
```

### Cross-Reference with Form 4 Data
- Form 3 establishes the BASELINE ownership position for each insider.
- The first Form 4 after a Form 3 should show changes from that baseline.
- Date of Form 3 filing establishes when person became an insider -- critical for
  determining when MNPI duties began.
- Relationship flags (isDirector, isOfficer, isTenPercentOwner) from Form 3
  should match Form 4 filings.
- Officer title in Form 3 establishes the insider's role.

---

## 6. FORM 5 (ANNUAL STATEMENT OF CHANGES)

### Overview
Annual catch-all filing for transactions that were:
- Exempt from Form 4 reporting (e.g., small acquisitions, gifts)
- Not reported on Form 4 due to late filing
- Transactions in the prior fiscal year that should have been reported

Due within 45 days after the end of the issuer's fiscal year.

### Acquisition Methods
Same as Form 3 -- use Submissions API with individual or company CIK,
filter for `form == "5"`.

### XML Structure
Identical to Form 4 XML structure, with same elements:
- `<nonDerivativeTable>` with `<nonDerivativeTransaction>` entries
- `<derivativeTable>` with `<derivativeTransaction>` entries
- Same transaction codes, share counts, prices

### Cross-Reference with Form 4 Data
- Form 5 reveals transactions MISSED by Form 4 filings.
- Late Form 4 transactions may appear on Form 5 instead.
- Gift transactions (code G) often appear on Form 5.
- Compare Form 5 post-transaction holdings with last Form 4 post-transaction holdings
  for the fiscal year -- discrepancies indicate unreported transactions.
- ABSENCE of Form 5 when expected is itself a red flag (possible unreported transactions).

---

## 7. 10-K ANNUAL REPORTS

### Acquisition Methods

#### Method A: Via Submissions API
```
GET https://data.sec.gov/submissions/CIK{company-cik}.json
```
Filter for `form == "10-K"` or `form == "10-K/A"`.

#### Method B: Via XBRL Company Facts API
```
GET https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json
```
Returns all XBRL-tagged financial data from all 10-K filings.

#### Method C: Via XBRL Company Concept API
```
GET https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{concept}.json
```
Returns time-series for a specific financial metric.

### Structured Data Available (XBRL)
All financial statement data is available in structured XBRL:

| Category                | Key Concepts                                           |
|-------------------------|--------------------------------------------------------|
| Income Statement        | Revenues, NetIncomeLoss, EarningsPerShareBasic         |
| Balance Sheet           | Assets, Liabilities, StockholdersEquity                |
| Cash Flow               | NetCashProvidedByUsedInOperatingActivities              |
| Share Data              | CommonStockSharesOutstanding, WeightedAverageShares    |
| Executive Compensation  | (Via ECD taxonomy in embedded proxy data)              |

### Unstructured Data Requiring NLP/Parsing
- **Item 11 - Executive Compensation**: May incorporate DEF 14A by reference
- **Item 13 - Certain Relationships and Related Transactions**:
  - Related party transactions with executives
  - Loans to officers/directors
  - Business relationships with insider-controlled entities
- **Item 12 - Security Ownership of Certain Beneficial Owners**:
  - Beneficial ownership table
  - Equity compensation plan information
- **Item 10 - Directors, Executive Officers and Corporate Governance**:
  - Officer/director biographical information
  - Section 16(a) delinquent filer disclosure

### Cross-Reference with Form 4 Data
- Section 16(a) delinquent filer disclosure in 10-K reveals late Form 4 filers.
- Beneficial ownership table should reconcile with cumulative Form 4 data.
- Related party transactions may explain unusual Form 4 patterns (e.g., transfers
  to entities controlled by the insider).
- Executive compensation reveals anticipated option grants/vesting that should
  appear as future Form 4 transactions.
- Changes in officer/director roster correlate with Form 3 filings.

---

## 8. FORM 144 (NOTICE OF PROPOSED SALE)

### Overview
Filed by affiliates (insiders) who intend to sell restricted or control securities
under Rule 144. Required when sale exceeds 5,000 shares or $50,000 in any
three-month period.

IMPORTANT: Since April 13, 2023, Form 144 must be filed electronically on
EDGAR in XML format. Prior to this, paper/email filing was permitted.

### Acquisition Methods

#### Method A: Via Submissions API
```
GET https://data.sec.gov/submissions/CIK{individual-cik}.json
```
Filter for `form == "144"`.

#### Method B: Via Company CIK
```
GET https://data.sec.gov/submissions/CIK{company-cik}.json
```
Filter for `form == "144"` to see all proposed insider sales for the company.

#### Method C: Via Full-Text Search
```
POST https://efts.sec.gov/LATEST/search-index
Body: {"q": "{executive name}", "forms": "144", "dateRange": "custom", "startdt": "2023-04-13"}
```

### XML Fields (Post-April 2023)
```xml
<form144>
  <issuerInfo>
    <issuerName>Company Name</issuerName>
    <issuerCik>0000320193</issuerCik>
    <issuerTradingSymbol>AAPL</issuerTradingSymbol>
  </issuerInfo>
  <reportingPersonInfo>
    <reportingPersonName>John Doe</reportingPersonName>
    <reportingPersonCik>0001234567</reportingPersonCik>
    <affiliateStatus>true</affiliateStatus>
  </reportingPersonInfo>
  <securitiesInfo>
    <securityTitle>Common Stock</securityTitle>
    <noOfSecuritiesToBeSold>10000</noOfSecuritiesToBeSold>
    <aggregateMarketValue>1500000</aggregateMarketValue>
    <approximateDateOfSale>2024-03-15</approximateDateOfSale>
  </securitiesInfo>
  <pastSales>
    <pastThreeMonthsSales>
      <dateOfSale>2024-01-15</dateOfSale>
      <noOfSecuritiesSold>5000</noOfSecuritiesSold>
      <grossProceeds>750000</grossProceeds>
    </pastThreeMonthsSales>
  </pastSales>
  <brokerInfo>
    <brokerName>Goldman Sachs</brokerName>
  </brokerInfo>
</form144>
```

### Cross-Reference with Form 4 Data
- Form 144 is filed BEFORE the sale; Form 4 is filed AFTER.
- Compare proposed sale quantity on Form 144 with actual sale on subsequent Form 4.
- Discrepancies (filing 144 but not executing, or selling more than proposed)
  are investigative signals.
- Filing date proximity: Form 144 typically precedes Form 4 sale transaction by
  days to weeks.
- CIK matching: reportingPersonCik on Form 144 matches reporting_owner_cik on Form 4.
- Broker information on Form 144 can be cross-referenced with trading venue data.

---

## 9. INSIDER TRANSACTIONS BULK DATA SETS

### Endpoint
```
https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets
```

Quarterly bulk downloads of ALL Forms 3, 4, and 5 in flattened tabular format.

### Download Format
ZIP files containing TSV (tab-separated values) files, one per quarter:
```
https://www.sec.gov/files/structureddata/data/insider-transactions-data-sets/{year}q{quarter}.zip
```

### Tables and Key Fields

#### SUBMISSION Table (Primary Key: ACCESSION_NUMBER)
| Field                        | Description                                  |
|------------------------------|----------------------------------------------|
| ACCESSION_NUMBER             | Unique SEC submission identifier             |
| FILING_DATE                  | Date filed with SEC                          |
| DATE_OF_ORIGINAL_SUBMISSION  | Date of triggering event                     |
| ISSUERCIK                    | Issuer company CIK                           |
| ISSUERNAME                   | Issuer company name                          |
| ISSUERTRADINGSYMBOL          | Ticker symbol                                |
| RPTOWNERREMARKS              | Reporting owner remarks                      |
| AFF10B5ONE                   | 10b5-1 plan affirmation flag (added 2025)    |

#### REPORTINGOWNER Table (Key: ACCESSION_NUMBER + RPTOWNERCIK)
| Field              | Description                                     |
|--------------------|-------------------------------------------------|
| ACCESSION_NUMBER   | Links to SUBMISSION table                       |
| RPTOWNERCIK        | Reporting owner CIK                             |
| RPTOWNERNAME       | Reporting owner name                            |
| OFFICER            | Is officer flag                                 |
| DIRECTOR           | Is director flag                                |
| TENPERCENTOWNER    | Is 10%+ owner flag                              |
| OTHER              | Other relationship flag                         |
| RPTOWNERTITLE      | Officer/director title                          |
| RPTOWNERSTREET1    | Street address                                  |
| RPTOWNERSTATE      | State                                           |
| RPTOWNERSTATETEXT  | State description                               |
| RPTOWNERZIP        | ZIP code                                        |

#### NONDERIV_TRANS Table (Key: ACCESSION_NUMBER + NONDERIV_TRANS_SK)
| Field                   | Description                                  |
|-------------------------|----------------------------------------------|
| SECURITY_TITLE          | Security name                                |
| TRANS_DATE              | Transaction date                             |
| DEEMED_EXECUTION_DATE   | Deemed execution date                        |
| TRANS_FORM_TYPE         | Transaction form type                        |
| TRANS_CODE              | Transaction code (P, S, A, M, G, etc.)       |
| EQUITY_SWAP_INVOLVED    | Equity swap flag                             |
| TRANS_SHARES            | Number of shares                             |
| TRANS_PRICEPERSHARE     | Price per share                              |
| TRANS_ACQUIRED_DISP_CD  | Acquired (A) or Disposed (D)                 |
| SHRS_OWND_FOLWNG_TRANS  | Shares owned after transaction               |
| DIRECT_INDIRECT_OWNERSHIP | Direct (D) or Indirect (I)                 |

#### NONDERIV_HOLDING Table
Same structure as NONDERIV_TRANS but for holdings without transactions.

#### DERIV_TRANS Table (Key: ACCESSION_NUMBER + DERIV_TRANS_SK)
| Field                      | Description                               |
|----------------------------|-------------------------------------------|
| SECURITY_TITLE             | Derivative security name                  |
| CONV_EXERCISE_PRICE        | Conversion/exercise price                 |
| TRANS_DATE                 | Transaction date                          |
| TRANS_CODE                 | Transaction code                          |
| TRANS_SHARES               | Number of derivative securities           |
| TRANS_PRICEPERSHARE        | Transaction price                         |
| TRANS_ACQUIRED_DISP_CD     | Acquired (A) or Disposed (D)              |
| EXERCISE_DATE              | Exercise date                             |
| EXPIRATION_DATE            | Expiration date                           |
| UNDERLYING_SECURITY_TITLE  | Underlying security name                  |
| UNDERLYING_SECURITY_SHARES | Underlying shares                         |
| SHRS_OWND_FOLWNG_TRANS     | Derivative shares owned after transaction |

#### DERIV_HOLDING Table
Same as DERIV_TRANS but for holdings without transactions.

#### FOOTNOTES Table
| Field              | Description                                     |
|--------------------|-------------------------------------------------|
| ACCESSION_NUMBER   | Links to parent filing                          |
| FOOTNOTE_ID        | Footnote identifier (F1, F2, etc.)              |
| FOOTNOTE_TEXT      | Full footnote text                              |

### Cross-Reference with Form 4 Data
This IS the canonical Form 4 data in bulk format. Cross-referencing works via:
- `ACCESSION_NUMBER` links across all tables within a filing.
- `RPTOWNERCIK` links to the individual's Submissions API data.
- `ISSUERCIK` links to the company's Submissions API data.
- `ISSUERTRADINGSYMBOL` enables market data correlation.
- `AFF10B5ONE` flag identifies pre-planned trades under Rule 10b5-1 plans.

---

## 10. EXECUTIVE FINANCIAL PROFILE AGGREGATION

### Does the SEC Provide an Aggregated Executive Profile View?

**NO.** The SEC does not provide a single "financial profile" endpoint for
executives. There is no aggregated view of all holdings across companies.

However, a comprehensive executive profile CAN be constructed programmatically:

### Construction Method

```
Step 1: Get executive's CIK
   -> https://data.sec.gov/submissions/CIK{exec-cik}.json
   -> Returns: name, former names, ALL filing history

Step 2: Extract all companies (issuers) from filing history
   -> For each Form 3/4/5, extract issuerCik
   -> Build list of all companies where person is/was an insider

Step 3: For each company, get:
   a. All Form 3 filings -> initial positions
   b. All Form 4 filings -> transaction history
   c. All Form 5 filings -> annual catch-ups
   d. All Form 144 filings -> proposed sales
   e. Company DEF 14A -> compensation data
   f. Company 10-K -> related party transactions, beneficial ownership

Step 4: Cross-reference:
   a. SC 13D/13G filings where exec is reporting person
   b. 13F-HR filings if exec manages an investment fund
   c. Form D filings for private placement involvement
   d. Enforcement actions against the executive

Step 5: Aggregate into profile:
   - Total current holdings across all companies
   - Historical transaction timeline
   - Compensation history (from DEF 14A)
   - Relationship map (companies, roles, dates)
   - Trading pattern analysis
   - Red flag detection
```

### API Call Sequence for Profile Construction
```python
# 1. Get executive submissions
exec_data = GET(f"https://data.sec.gov/submissions/CIK{exec_cik}.json")

# 2. Extract unique issuer CIKs from filings
issuer_ciks = set()
for i, form in enumerate(exec_data['filings']['recent']['form']):
    if form in ('3', '4', '5', '144'):
        # Parse the filing XML to extract issuerCik
        accession = exec_data['filings']['recent']['accessionNumber'][i]
        primary_doc = exec_data['filings']['recent']['primaryDocument'][i]
        # Fetch and parse XML...

# 3. For each issuer, get compensation data
for issuer_cik in issuer_ciks:
    company_data = GET(f"https://data.sec.gov/submissions/CIK{issuer_cik}.json")
    # Filter for DEF 14A filings
    # Filter for 10-K filings
    # Filter for SC 13D/G filings

# 4. Get structured XBRL compensation data (post-2022)
for issuer_cik in issuer_ciks:
    facts = GET(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{issuer_cik}.json")
    ecd_data = facts.get('facts', {}).get('ecd', {})
    # Extract PeoTotalCompAmt, etc.
```

---

## 11. CROSS-REFERENCE ARCHITECTURE

### CIK as Universal Key

The Central Index Key (CIK) is the primary cross-reference identifier:

```
                    INDIVIDUAL CIK (e.g., 0001234567)
                              |
        +---------+-----------+----------+---------+
        |         |           |          |         |
     Form 3   Form 4      Form 5    Form 144   SC 13D/G
        |         |           |          |         |
        +----+----+-----------+----+-----+---------+
             |                     |
        COMPANY CIK           COMPANY CIK
     (issuerCik in XML)    (issuerCik in XML)
             |                     |
     +-------+-------+    +-------+-------+
     |       |       |    |       |       |
   10-K  DEF 14A   8-K  10-K  DEF 14A   8-K
```

### Cross-Reference Matrix

| Source A         | Source B         | Join Key                      | Correlation Purpose                              |
|------------------|------------------|-------------------------------|--------------------------------------------------|
| Form 4           | Form 3           | rptOwnerCik + issuerCik       | Baseline vs. current holdings                    |
| Form 4           | Form 5           | rptOwnerCik + issuerCik       | Reported vs. unreported transactions             |
| Form 4           | Form 144         | rptOwnerCik + issuerCik       | Proposed vs. actual sales                        |
| Form 4           | DEF 14A          | rptOwnerCik + issuerCik       | Trading vs. compensation grants                  |
| Form 4           | 8-K              | issuerCik + date proximity    | Trading vs. material events                      |
| Form 4           | 10-K             | issuerCik + fiscal year       | Trading vs. annual disclosures                   |
| Form 4           | SC 13D/G         | rptOwnerCik + issuerCik       | Transaction pattern vs. ownership intent         |
| DEF 14A          | 10-K             | issuerCik + fiscal year       | Compensation vs. performance                     |
| SC 13D           | 8-K              | issuerCik + date proximity    | Activist intent vs. corporate actions            |
| Form 144         | Form 4           | rptOwnerCik + date proximity  | Sale intent vs. execution                        |
| Form 3           | 8-K              | issuerCik + date proximity    | New insider vs. appointment announcement         |

### Date-Based Correlation Windows

| Event Pair                          | Window     | Significance                          |
|-------------------------------------|------------|---------------------------------------|
| Form 4 trade -> 8-K event          | -30 to +2d | Pre-announcement trading (MNPI)       |
| Form 3 filing -> 8-K appointment   | 0 to +10d  | Insider status establishment          |
| Form 144 filing -> Form 4 sale     | 0 to +90d  | Intent vs. execution gap              |
| SC 13D filing -> ownership cross    | 0 to +10d  | Timely 5% disclosure                  |
| DEF 14A grant date -> Form 4       | 0 to +2d   | Compensation grant reporting          |
| 10-K fiscal year end -> Form 5     | 0 to +45d  | Annual catch-up window                |

---

## 12. RATE LIMITS AND ACCESS REQUIREMENTS

### SEC EDGAR Rate Limits (All Endpoints)

| Parameter                | Value                                       |
|--------------------------|---------------------------------------------|
| Maximum requests/second  | 10 (per IP address, across all endpoints)   |
| JLAW recommended rate    | 6-9 req/sec (with adaptive throttling)      |
| Rate limit response      | HTTP 429 (Too Many Requests)                |
| Block response           | HTTP 403 (Forbidden) -- may include cooldown|
| Authentication required  | NO (for data.sec.gov and efts.sec.gov)      |
| API key required         | NO                                          |

### Required Headers

```http
User-Agent: CompanyName/Version (contact@email.com)
Accept: application/json
Accept-Encoding: gzip, deflate
```

The SEC REQUIRES a User-Agent header containing:
1. Company/project name
2. Contact email address

Requests without proper User-Agent may be blocked.

### Endpoint-Specific Notes

| Endpoint                  | Domain          | Auth  | Format | Notes                        |
|---------------------------|-----------------|-------|--------|------------------------------|
| Submissions API           | data.sec.gov    | None  | JSON   | Real-time updates            |
| Company Facts API         | data.sec.gov    | None  | JSON   | Real-time updates            |
| Company Concept API       | data.sec.gov    | None  | JSON   | Real-time updates            |
| Frames API                | data.sec.gov    | None  | JSON   | Real-time updates            |
| Full-Text Search          | efts.sec.gov    | None  | JSON   | Since 2001, all form types   |
| Filing Archives           | www.sec.gov     | None  | XML/HTML | Historical filings          |
| Insider Transactions Bulk | www.sec.gov     | None  | ZIP/TSV| Updated quarterly            |
| Company Tickers           | www.sec.gov     | None  | JSON   | ~10,000 tickers              |
| RSS Feeds                 | www.sec.gov     | None  | Atom   | Near real-time               |
| Legacy CGI search         | www.sec.gov     | None  | HTML/Atom | Older interface            |

### Bulk Downloads (for high-volume research)

| Dataset                    | URL                                                                  | Size    |
|----------------------------|----------------------------------------------------------------------|---------|
| All submissions            | https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip | ~5 GB  |
| All company facts (XBRL)  | https://www.sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip   | ~2 GB  |
| Insider transactions (quarterly) | https://www.sec.gov/files/structureddata/data/insider-transactions-data-sets/ | ~50-200 MB/quarter |

---

## APPENDIX A: JLAW EXISTING IMPLEMENTATION STATUS

The following data sources are already implemented in the JLAW codebase:

| Data Source         | Implementation File                                           | Status      |
|---------------------|---------------------------------------------------------------|-------------|
| Submissions API     | `src/integrations/sec_edgar/edgar_client.py`                  | Implemented |
| Company Facts API   | `src/integrations/sec_edgar/edgar_client.py`                  | Implemented |
| Form 4 XML Parsing  | `src/zero_dollar/acquisition/edgar_client.py`                 | Implemented |
| Full-Text Search    | `src/integrations/sec_edgar/sec_data_resources.py`            | Implemented |
| DEF 14A retrieval   | `src/integrations/sec_edgar_bulletproof_config.py` (Node 9)   | Partial     |
| SC 13D/G retrieval  | `src/integrations/sec_edgar_bulletproof_config.py` (Node 12)  | Partial     |
| 13F-HR retrieval    | `src/integrations/sec_edgar_bulletproof_config.py` (Node 13)  | Partial     |
| 8-K retrieval       | `src/integrations/sec_edgar_bulletproof_config.py` (Node 11)  | Partial     |
| Ownership Chain     | `src/zero_dollar/modules/ownership_chain.py`                  | Implemented |
| Insider Bulk Data   | `src/integrations/sec_edgar/sec_data_resources.py`            | Endpoint defined, parsing partial |
| Form 3 parsing      | NOT IMPLEMENTED                                               | Gap         |
| Form 5 parsing      | NOT IMPLEMENTED                                               | Gap         |
| Form 144 parsing    | NOT IMPLEMENTED                                               | Gap         |
| Executive profiling | NOT IMPLEMENTED                                               | Gap         |
| ECD XBRL parsing    | NOT IMPLEMENTED                                               | Gap         |

### Key Implementation Gaps for Insider Profiling

1. **Form 3 XML Parser**: Need dedicated parser for initial ownership statements.
   XML schema is similar to Form 4 but uses `<nonDerivativeHolding>` instead of
   `<nonDerivativeTransaction>` elements.

2. **Form 5 XML Parser**: Need parser for annual catch-up filings. XML schema
   identical to Form 4.

3. **Form 144 XML Parser**: Need parser for proposed sale notices. New XML schema
   since April 2023 -- different from Form 4 schema.

4. **Executive Profile Aggregator**: Need module that takes an individual CIK
   and constructs a complete financial profile across all companies and filing types.

5. **ECD XBRL Extraction**: Need parser for Executive Compensation Disclosure
   taxonomy data from DEF 14A filings (post-2022).

6. **DEF 14A NLP Parser**: Need extraction logic for unstructured compensation
   tables, beneficial ownership tables, and related party transactions from
   pre-2022 proxy statements.

---

## APPENDIX B: RECOMMENDED API CALL SEQUENCE FOR INVESTIGATION

### For a single insider investigation:

```
1. CIK Lookup
   GET https://www.sec.gov/files/company_tickers.json
   -> Find company CIK from ticker

2. Company Submissions
   GET https://data.sec.gov/submissions/CIK{company_cik}.json
   -> Extract all Form 3/4/5 filings
   -> Extract DEF 14A filings
   -> Extract 10-K filings
   -> Extract 8-K filings
   -> Extract SC 13D/G filings

3. Individual CIK Discovery
   Parse Form 4 XML files to extract rptOwnerCik values
   -> Build map: insider_name -> insider_cik

4. Individual Submissions
   GET https://data.sec.gov/submissions/CIK{insider_cik}.json
   -> ALL filings by this individual across ALL companies

5. Structured Financial Data
   GET https://data.sec.gov/api/xbrl/companyfacts/CIK{company_cik}.json
   -> XBRL financial metrics
   -> ECD executive compensation data (post-2022)

6. Full-Text Cross-Reference
   POST https://efts.sec.gov/LATEST/search-index
   Body: {"q": "{insider_name}", "forms": "8-K", "entityName": "{company_cik}"}
   -> Find all 8-K mentioning this insider (departure, appointment, etc.)

7. Enforcement History
   POST https://efts.sec.gov/LATEST/search-index
   Body: {"q": "{insider_name}", "forms": "LIT-REL,AAER"}
   -> Check for prior enforcement actions
```

### Estimated API Calls per Investigation
- 1 company + 5 insiders, 5 years of data:
  - Submissions: ~6 calls (1 company + 5 individuals)
  - Form 4 XML parsing: ~200-500 calls (depending on trading frequency)
  - XBRL facts: 1 call
  - Full-text searches: ~10-15 calls
  - DEF 14A documents: ~5 calls
  - 10-K documents: ~5 calls
  - **Total: ~230-530 calls, ~25-55 seconds at 10 req/sec**

---

## REFERENCES

- SEC EDGAR API Documentation: https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- SEC Developer Resources: https://www.sec.gov/about/developer-resources
- EDGAR Full-Text Search FAQ: https://www.sec.gov/edgar/search/efts-faq.html
- Insider Transactions Data Sets: https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets
- Insider Transactions README: https://www.sec.gov/files/insider_transactions_readme.pdf
- SEC Accessing EDGAR Data: https://www.sec.gov/os/accessing-edgar-data
- Inline XBRL Documentation: https://www.sec.gov/data-research/structured-data/inline-xbrl
- EDGAR XBRL Guide: https://www.sec.gov/files/edgar/filer-information/specifications/xbrl-guide.pdf
- ECD Taxonomy: SEC Executive Compensation Disclosure taxonomy
- XBRL US API: https://api.xbrl.us/
- 17 CFR 240.10b-5 (Securities fraud)
- 17 CFR 240.10b5-1 (Trading plans)
- 17 CFR 240.13d-1 (Beneficial ownership reporting)
- 17 CFR 240.16b (Short-swing profits)
- 17 CFR 239.144 (Form 144 filing requirements)
