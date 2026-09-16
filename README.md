# DATA1002 — Group Project, Stage 1

Informatics: Data and Computation (2026 Semester 2) — collaborative data science
investigation.

## Project

- **Research question:** What does the market move with? Index returns and five
  economic measurements — real GDP growth, nominal GDP growth, inflation,
  unemployment and gross national income — across six countries, 1990–2025.
  *(Reframed from the earlier representativeness question; see `PROJECT_DESIGN.md` §1
  and confirm with the group.)*
- **Design:** six countries — Australia, the United States, the United Kingdom,
  France, Japan and China. One member per country; one member takes two.
- **Scope note:** the investigation measures **association, not causation**. Every
  country applies the same window, grain, definitions and chart set, so the six
  sections are directly comparable.
- **Due:** 5:00 pm, Sunday 11 October 2026 · **Value:** 20% of the unit
- **Format:** combined report as a PDF, plus per-member code and data folders,
  submitted as one compressed file on Canvas.

## Project design (summary)

The full design is in [`PROJECT_DESIGN.md`](PROJECT_DESIGN.md). This is the short form.

**The question.** What does the market move with? The index is the subject; each
economic measurement is something it may or may not move with.

**Measurements tested:** real GDP growth · nominal GDP growth · inflation ·
unemployment · gross national income.

**Countries and indices.** Six countries, one member each, with one member taking two.
Each country carries a headline index and a broad-market index where one can be
sourced.

**Individual questions** (Sections B and C, one member per country):

1. **What moves with the index** — how strongly does each measurement correlate with
   the index's total return?
2. **Money or volume** — is the correlation with nominal growth stronger than with real
   growth?
3. **Always, or in particular periods** — do the correlations hold by decade and by
   inflation regime?
4. **Both directions of the cycle** — are they different in expansions and contractions,
   and does the index lead or lag the measurement?
5. **Which index, in the same country** — does the broad-market index behave differently
   from the headline index?

**Group question** (Section D, once all six countries are complete): **do the six
countries tell the same story?** The group's work is collation, not re-analysis — a
shared results schema lets the six country studies stack directly.

**The data contract**, binding on every country (`PROJECT_DESIGN.md` §3): window
1990–2025, subject to availability · quarterly analysis grain, with each series retained
at its native frequency · ten or more attributes per country · local currency primary,
US dollar as a robustness check · the national statistical authority as the
authoritative source, with harmonised sources used for cross-country comparison.

**Method in one line.** Correlate the index's total return against each measurement
(Pearson and Spearman, reporting the number of observations and a confidence interval),
then test stability by decade and by regime, the cycle, and the second index.

**Read it as association, not causation.** Every reported relationship is co-movement
only. The verb throughout is "moves with" — never "follows" or "responds to".

## Repository layout

```
DATA1002/
├── README.md            # This file
├── PROJECT_DESIGN.md    # The agreed design: question, data contract, method, division
├── Stage1_Roadmap.md    # Schedule, marks breakdown, submission requirements
├── data/
│   ├── raw/             # Original downloads, unmodified — read-only (not tracked)
│   └── cleaned/         # Cleaned and derived outputs
├── scripts/             # Shared Python: acquisition, cleaning, quality checks
├── report/              # Quarto source and rendered report
└── shared/              # Cross-member material (charts, tables, definitions)
```

## How the work divides

| Part | Owner | Notes |
|:--|:--|:--|
| Data acquisition, all six countries | Shared | One dataset per country, each documented in `data/README.md` |
| Cleaning, quality checks and analysis | Each member, for their own country | Section B (2 pages) and Section C (4 pages) |
| Introduction and context (Section A) | Group | 1 page |
| Findings, recommendations, Responsible AI (Section D) | Group | 2 pages |
| Report build and packaging | Group | Quarto to PDF; one submitter |

## How to run

The report is a Quarto document. Python handles data preparation and analysis;
R (`ggplot2`) produces the charts.

```bash
quarto render report/report.qmd --to typst     # PDF via Typst (no LaTeX required)
```

`quarto --version` and `Rscript --version` should both resolve before rendering.

## Conventions

- **Professional register:** everything group-visible is written in a formal,
  professional register — no personal references, no emoticons, no local machine
  paths.
- **Data integrity:** `data/raw/` is read-only. Clean copies and derived outputs
  live in `data/cleaned/` or in script outputs — never overwrite the originals.
- **Provenance:** every dataset entry records its source, retrieval date,
  restrictions on use, structure, and assessed strengths and limitations.
- **Data policy — this repository is public.** It carries code and written material
  only. Datasets are not redistributed here; see `data/README.md` for the sources
  and their terms.
- **AI-assisted work** is permitted and is disclosed: what was assisted, how the
  output was verified, and where a suggestion was rejected.
