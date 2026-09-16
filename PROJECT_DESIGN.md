# Stage 1 — Project Design

**Status:** proposal for group review. On adoption, this document supersedes the
project-question section of `Stage1_Roadmap.md`; the roadmap's schedule, marks
breakdown and submission requirements remain in force.

**Prepared:** 16 September 2026.

---

## 1. The question

> **What does the market move with? Index returns and five economic measurements
> across six countries, 1990–2025.**

The index is the subject. Each economic measurement is something the index may or may
not move with; the investigation measures how closely it does, and whether the answer
holds across countries, across periods and across the cycle.

**One wording discipline.** The verb throughout is **moves with**. Never "follows",
"responds to" or "is driven by" — those assert a direction or a cause that a
correlation cannot support.

**Measurements** (the economy side, §3.3): real GDP growth · nominal GDP growth ·
inflation · unemployment · gross national income.
**Indices** (the market side, §3.5): a headline index and a broad-market index in
each country.

### 1.1 Individual questions — Sections B and C, one member per country

| # | Question | How it is answered | Chart |
|:--:|:--|:--|:--|
| **1** | **What moves with the index?** How strongly does the index's total return correlate with each measurement? | Pearson and Spearman per measurement, with *n* and a confidence interval | small multiples |
| **2** | **Money or volume?** Is the correlation with nominal growth stronger than with real growth, and does that hold in every country? | paired comparison per country | paired bars |
| **3** | **Always, or in particular periods?** Do the correlations hold by decade and by inflation regime, or are they driven by one phase? | decade split and regime split | decade panel |
| **4** | **Both directions of the cycle?** Is the correlation different in expansions and contractions, and does the index lead or lag the measurement? | conditional correlation; lead–lag against unemployment | lead–lag chart |
| **5** | **Which index, in the same country?** Does the broad-market index show a different pattern from the headline index? | headline versus broad index, same country, same measures | paired comparison |

Each member answers questions 1–5 for their own country. The measurements, the window,
the grain and the definitions are fixed by §3, so the six sets of answers are
comparable.

### 1.2 The group question — Section D, once all six countries are complete

> **Do the six countries tell the same story?**

The group's work is **collation, not re-analysis**: §1.3 fixes a results schema so the
six country studies stack without re-derivation. Section D then reports the
cross-country pattern, the recommendations, the limitations, and the account of
AI-assisted work.

### 1.3 Shared results schema

Every member records their results in one table, one row per (country, index,
measurement):

| Column | Content |
|:--|:--|
| `country` · `index` · `index_role` | the index, and whether it is the headline or the broad-market one |
| `measurement` | real GDP growth · nominal GDP growth · inflation · unemployment · GNI |
| `window` · `n` · `grain` | stated per member, never assumed |
| `pearson` · `spearman` · `ci_low` · `ci_high` | the statistic and its interval |
| `decade_split` · `regime_split` · `expansion` · `contraction` | results for questions 3 and 4 |
| `notes` | data limitations affecting that row |

Six such tables concatenate into the cross-country comparison. The schema is what makes
the group question answerable at all.

### 1.4 Scope limits

**Association, not causation.** The investigation measures co-movement and how closely
it holds. It does not claim that any economic measurement causes index returns, or the
reverse. Stated wherever a result is reported.

**"Moves with" is not "should move with".** No measurement is treated as the correct
definition of the economy. GNI is included because in some countries it differs
materially from GDP, not because it is the more valid measure.

**Change of question.** The group previously locked the representativeness question
("How well does the index represent the market?", 12 September 2026). This design
replaces it. The two belong to the same family — an index measured against the real
economy — but they require different data and different analysis, so **the group must
confirm the change before work proceeds.**

### 1.5 Stakeholders — Section A

- **Individual investors and retirement savers.** If particular measurements move with
the market and others do not, that changes which signal is worth watching.
- **Analysts and financial commentators.** The claim that a given economic signal
moves the market becomes testable rather than assumed.
- **Fund managers and benchmark owners.** The index is the standard against which
performance is judged.
- **Policymakers.** Whether market movements carry information about the measured
economy is an empirical question, and this design treats it as one.

---

## 2. Scope and allocation

| Country | Headline index (market side) | Member |
|:--|:--|:--|
| Australia | S&P/ASX 200 | Member 3 |
| United States | S&P 500 | Lead (shared with China) |
| United Kingdom | FTSE 100 | Member 2 |
| France | CAC 40 | Member 4 |
| Japan | Nikkei 225 | Member 5 |
| China | Shanghai Composite (see §3.5) | Lead (shared with the United States) |

Every country contributes the same shape of evidence: its indices, the five economic
measurements, and the correlations between them. Each member also carries a
broad-market index where one can be sourced (§3.5).

---

## 3. The data contract

Six members working independently will not produce a comparable report unless the
definitions are fixed centrally. This section is binding on every country's work.

### 3.1 Window

**1990–2025**, subject to availability. Where a country's series begins later, the
actual start is stated and used, never extrapolated backwards.

### 3.2 Grain — quarterly for analysis, native frequency for storage

**Monthly was considered and rejected for the analysis.** No national statistical
authority in scope publishes GDP monthly: official GDP is quarterly in all six
countries, and monthly GDP exists only as modelled estimates (nowcast proxies such
as the OECD monthly GDP series). Because GDP is the economy-side variable, quarterly
is the binding grain.

Series published more frequently — consumer prices, interest rates, exchange rates
and the index itself — are **retained at their native frequency** (monthly or daily)
in the raw data; only the analysis panel is quarterly. This preserves information and
maximises the record count.

Quarterly also satisfies the requirement that a member's cleaned dataset carry **at
least 100 records**: 1990Q1–2025Q4 is 144 quarters, where 36 annual observations
would fail. A correlation estimated on roughly 140 quarterly observations is also far
more informative than one estimated on 36 annual points.

### 3.3 Attributes — ten or more per country

Each country's dataset carries the **five measurements** that §1 tests, plus the market
side, plus enough supporting series to reach ten attributes.

**Mandatory — the five measurements**

1. real GDP growth
2. nominal GDP growth
3. inflation — the consumer price index, and its rate of change
4. unemployment rate
5. gross national income

**Mandatory — the market side**

6. index level, for the headline index and the broad-market index
7. index total return — price return plus dividends, or price-only where dividends are
   unavailable, which is stated

**Supporting — to reach ten attributes, and to explain divergence**

8. GDP per capita
9. population
10. exchange rate against the US dollar
11. policy interest rate or the 10-year government bond yield
12. industrial production, or broad money

Where a country cannot supply one of these, the omission is disclosed and the affected
test is recorded as not applicable rather than silently dropped.

**Frequency exception.** GNI is published annually in the harmonised sources, and
quarterly only for some countries. The GNI test is therefore run on annual data and
labelled as such wherever it is reported, while the other four measurements are tested
at the quarterly grain.

### 3.4 Currency

**Local currency is primary.** Comparing local-currency returns against local-currency
GDP growth measures the relationship between the market and the economy without the
exchange rate between them. A US-dollar variant is reported as a secondary
robustness check, because an overseas investor experiences the market in their own
currency.

### 3.5 Index choice — two or three per country

Each country carries a **headline index** (the one usually cited) and a **broad-market
index**, with a third segment index where a clean free series exists. The pair is not
mere redundancy: the large-cap and broad indices differ in exactly the way the
investigation cares about, since large-cap indices are more internationally exposed
(the FTSE 100 earns largely abroad; the FTSE 250 is domestically oriented) while the
broad index sits closer to the domestic economy. A pair therefore tests the
composition channel of any divergence.

| Country | Headline | Broad market | Third (where available) |
|:--|:--|:--|:--|
| Australia | S&P/ASX 200 | All Ordinaries | ASX Small Ordinaries |
| United States | S&P 500 | Wilshire 5000 | S&P MidCap 400 / Russell 2000 |
| United Kingdom | FTSE 100 | FTSE All-Share | FTSE 250 |
| France | CAC 40 | CAC All-Tradable | CAC Mid 60 |
| Japan | Nikkei 225 | TOPIX | TOPIX Small |
| China | CSI 300 | Shanghai Composite | Shenzhen Component |

**Availability, checked 16 September 2026** on the free market-data route: the
headline index and at least one further index are directly available for every
country (for example All Ordinaries and ASX Small Ordinaries for Australia; Wilshire
5000, Russell 2000 and S&P MidCap 400 for the United States; FTSE 250 for the United
Kingdom; Shenzhen Component for China). Several **broad-market series are not on that
route** — TOPIX, CAC All-Tradable, FTSE All-Share and CSI 300 returned no usable
history — so where a series cannot be sourced directly, either an alternative direct
route is used or the **issuer exchange-traded fund that tracks that index** is used
as a stated proxy.

Two rules follow:

- **A fund proxy must be identified, not assumed.** Before an exchange-traded fund
  stands in for an index, confirm from the issuer what index it actually tracks. A
  fund that tracks a different index is not a proxy for this one; this distinction
  has already produced one error in this project and is treated as a check, not a
  formality. Tracking difference and fees are disclosed where a fund is used.
- **Two indices are not independent evidence.** Where two indices share most of their
  constituents, the second is a robustness check on the first, not a second
  observation. This is stated wherever both are reported.

**China.** The Shanghai Composite is capitalisation-weighted but heavily weighted
toward state-linked issuers and dominated by domestic retail trading; the CSI 300 is
the institutional benchmark. Both are used, the choice is disclosed, and the third
series (Shenzhen Component) carries a different sector profile again.

**Price versus total return.** Indices are commonly published as price indices.
Where a dividend series is available the total return is computed, because dividends
are part of what an investor earns and their omission understates the market side of
the comparison. Where only a price index is available, this is stated on the chart.

### 3.6 Sources

Two tiers, both cited:

1. **National statistical authority** — Australian Bureau of Statistics, US Bureau of
   Economic Analysis and Bureau of Labor Statistics, UK Office for National
   Statistics, INSEE, Statistics Bureau of Japan and Cabinet Office, National Bureau
   of Statistics of China.
2. **Harmonised cross-country sources** — OECD, World Bank, IMF.

The national series is authoritative for that country; the harmonised series is used
for cross-country comparison. Where the two differ, the difference is recorded.

### 3.7 Data handling rules

- Missing values are disclosed, never interpolated silently.
- Every dataset records its retrieval date and the publisher's own vintage.
- Nominal and real figures are labelled unambiguously; a deflator is never assumed.
- `data/raw/` is read-only; all cleaning operates on copies.

---

## 4. Method

Applied identically in each country, so the six results can be read against each
other.

1. **Assemble** the country panel to the contract in §3.
2. **Describe** — plot and summarise each series; note the period, the grain, and any
   structural breaks.
3. **Correlate** — for each of the five measurements, correlate the index total return
   against that measurement, reporting Pearson and Spearman, the number of observations
   and a confidence interval. Flow measures on the economy side are used as **growth
   rates**; correlations between the two *levels* are reported separately and labelled,
   because two trending series correlate almost by construction.
4. **Test stability** — recompute by decade, on a rolling window, and across inflation
   regimes, so that a single phase cannot be presented as the whole story.
5. **Test the cycle** — recompute separately for expansions and contractions, using the
   unemployment rate as the regime marker, and test whether the index leads or lags the
   measurement.
6. **Compare indices** — repeat the analysis for the broad-market index and report the
   difference (§1.1, question 5).
7. **Interpret divergence** — where a correlation is weak or absent, examine the
   candidates: inflation, the profit share of GDP, valuation change, currency and index
   composition. This is descriptive accounting, not causal identification.
8. **Report honestly** — a weak or absent relationship is a finding, not a failure, and
   is reported in the same voice as a strong one.

**Multiple comparisons.** The design tests many pairings, so a small number of
apparently strong results is expected by chance. The correlation between the index and
each of the five measurements is therefore the **primary, pre-registered test**; the
decade, regime, cycle and cross-index splits are reported **as exploratory**, and are
labelled as such wherever they appear.

---

## 5. Visualisation plan

Charts are produced in **R with `ggplot2`**, identically in form for every country,
so comparison across the six is immediate. Each member produces two to three charts,
each accompanied by a written evaluation of how the data are encoded and of the
design's strengths and limitations — the evaluation carries its own marks and is not
optional commentary.

Standard chart set:

| Chart | Purpose | Encoding note to evaluate |
|:--|:--|:--|
| Correlation summary, one panel per measurement | answers question 1 across the five measurements | ordering and scale choices; whether intervals are shown |
| Paired bars, nominal against real growth | answers question 2 | the pair is the message, so a common scale is mandatory |
| Time series, index against one measurement | shows co-movement over time | dual axes are widely criticised; the critique is stated and an indexed single scale or two stacked panels is discussed |
| Decade panel | answers question 3 | shows whether one period drives the result |
| Lead–lag chart, index against unemployment | answers question 4 | the lag axis must be labelled, and no direction is implied |
| Headline against broad index, same country | answers question 5 | identical scales across the pair |
| Small multiples, six countries (group section) | makes the six directly comparable | identical scales across panels; the cost of small panels is acknowledged |

The group assembles a shared chart style (fonts, palette, axis conventions) in
`shared/` so the six sections look like one report.

---

## 6. Deliverables and division of labour

**Individual (75 marks).** Each member, for their own country:

- the raw dataset as obtained and the cleaned dataset
- Python code for cleaning and quality checking, and for the summary analysis
- two to three charts with a written evaluation of each
- Section B (data preparation, 2 pages) and Section C (exploration, visualisation,
  insight, 4 pages)

**Group (25 marks).**

- Section A, Introduction and context (1 page): the question, why it matters, the
  stakeholders, and the data obtained
- Section D, Findings, recommendations and Responsible AI (2 pages)
- Cover page and the AI-assisted decision statement (150 words maximum)
- The report assembled as a PDF (Quarto), and the submission package

---

## 7. Build and reproducibility

- **Report:** Quarto, rendered to PDF through **Typst** (`quarto render report/report.qmd
  --to typst`). No LaTeX installation is required.
- **Analysis:** Python (pandas, numpy) for acquisition, cleaning and statistics.
- **Charts:** R with `ggplot2`.
- **Reproducibility:** each member's code runs from the repository root and resolves
  its own file paths; no absolute local paths are committed. This repository is
  public and carries code and written material only — no datasets.

---

## 8. Risks and disclosures

| Risk | Response |
|:--|:--|
| **Reading causation into a correlation** | §1 states the limit; every result is reported as association |
| **The naive result** | Studies across countries commonly find GDP growth and equity returns only weakly related; the design tests this rather than assuming it |
| **A measurement is not the economy** | no measurement is treated as the correct definition of the economy (§1.4); composition, foreign revenue and listed-versus-unlisted differences are treated in §4 as explanations of divergence |
| **Multiple comparisons** | many pairings are tested; one primary pre-registered test per measurement, and every split labelled exploratory (§4) |
| **Currency choice drives the result** | local currency is primary and the USD variant is reported beside it |
| **China's data quality** | official series are contested in the literature; the sources are named, the index choice is disclosed, and the limitation is stated rather than hidden |
| **Six members, six methods** | §3 is binding; the shared chart style keeps the sections visually comparable |
| **Small sample** | quarterly grain maximises observations; n and confidence intervals are always reported |
| **AI-assisted work** | recorded as it happens: what was assisted, how it was verified, where a suggestion was rejected |

---

## 9. Schedule

Per `Stage1_Roadmap.md`: Week 7 datasets and data quality; Week 8 analysis and
visualisation; Week 9 reporting and submission. Final submission 5:00 pm, Sunday
11 October 2026.

---

## 10. Decisions required

**From the group:**

1. Confirmation of the question change (§1).
2. Confirmation of the window and grain (§3.1, §3.2).
3. Confirmation of the country-to-member allocation (§2).
4. Agreement that the data contract in §3 is binding on all six sections.

**Resolved in this document, on evidence:**

- quarterly grain, since the 100-record requirement rules out annual data (§3.2)
- local currency primary, USD secondary (§3.4)
- both Chinese indices acquired, the choice disclosed (§3.5)
- two-tier source hierarchy, national authority plus harmonised comparison (§3.6)
