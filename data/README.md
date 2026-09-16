# Data — sources, provenance, restrictions and known limitations

This document describes the dataset assembled for the Stage 1 investigation into how well an index
represents its market, covering index concentration, membership survivorship and constituent
turnover.

It records, for every dataset family: its source, its provenance, the restrictions on its use, its
structure, and its assessed strengths and limitations. Where a limitation could not be resolved, it
is stated rather than omitted.

## 1. Repository layout

```
data/
├── raw/        original downloads, unmodified — read-only source of truth (not tracked)
└── cleaned/    cleaned and derived outputs
```

`data/raw/` holds each file exactly as retrieved. It is never edited: cleaning operates on copies,
and all derived outputs are written elsewhere. A SHA-256 record of every file in `data/raw/` is
maintained, and `scripts/verify_raw_integrity.py` reports any change, addition or removal. This
matters because the investigation depends on being able to demonstrate that the inputs have not
drifted.

## 2. Dataset families

| Family | Content | Source class | Coverage |
|:--|:--|:--|:--|
| Index level series | Daily OHLC, dividend and split history for 10 indices | Market data distributor | S&P 500 from 1927; Nikkei 225 from 1965; ASX 300 only from 2013. Common window across all ten: 2013-03-06 → 2026-09-11 |
| Constituent lists | Current membership for S&P 500, Dow 30, Nasdaq-100, FTSE 100, S&P/ASX 20/50/200, Nikkei 225 | Index owner (Nikkei 225); community-maintained encyclopaedia (others, cross-checked against independent sources) | Point-in-time snapshot, 2026-09-12 |
| Membership change history | Dated additions and removals with reasons | Community-maintained encyclopaedia, sampled against the index owner's own announcements | S&P 500: 407 events, 1976 → 2026 |
| S&P/ASX 200 announcement archive | Published quarterly rebalance and ad-hoc change announcements | **Index owner** (S&P Dow Jones Indices, re-hosted) | 163 documents, 2011-04-15 → 2026-09-04; parsed to 537 change events |
| Daily price panels | 10-year daily OHLCV per constituent, one panel per market | Market data distributor | ASX 200: 200/200 tickers; S&P 500: 503/503; FTSE 100: 100/100 |
| Survivorship-safe price panel | Daily prices for current members plus historical additions and removals | Market data distributor | 877 tickers, ~1.54 million rows, 2016-09-12 → 2026-09-11 |
| Owner-published index weights | Issuer fund holdings: S&P 500 (SPY), Nasdaq-100 (QQQ), Dow 30 (DIA), ASX 200 (A200) | Fund issuer | Dated issuer publications, September 2026 |
| Identifier map | Cross-market identifiers (CUSIP, SEDOL, ISIN) | Derived | 2,590 rows |

## 3. Restrictions on use

The dataset is assembled from free public sources. Several of them restrict redistribution, and this
record states that plainly:

| Source class | Position |
|:--|:--|
| Index owner (Nikkei) | The index owner's terms require permission for reproduction beyond personal use or quotation. Redistribution is not permitted. Use here is analytical, local and cited. |
| Fund issuers (SPY, QQQ, DIA, A200) | Daily holdings are published for information. Redistribution is not licensed. |
| Market data distributors (index levels and price panels) | The distributors' terms bar redistribution of the underlying data. |
| Aggregators (constituent lists, weights, whole-market lists) | Display-only or otherwise restrictive terms. Cite the site and the retrieval date; do not redistribute. |
| Community-maintained encyclopaedia content | Reproducible with attribution and share-alike. |
| Index owner announcement documents | Public regulatory-style publications, mirrored for analysis. |

**Consequence for this repository:** the raw corpus is deliberately **not** tracked. It is a
public repository, and publishing restricted source data here would not be permissible. The
acquisition scripts in `scripts/` are included so the corpus can be rebuilt from source by any group
member.

## 4. Assessed quality and known limitations

Every dataset family was assessed against its originating authority rather than against the file we
hold. The distinctions that matter:

**Verified against the originating authority.** Nikkei 225 component count (225/225 codes and
names, from the index owner's own page); the S&P 500 constituent count and four sampled membership
changes against the index owner's announcements; the Nasdaq-100 constituent set against the
exchange's own endpoint; the Dow 30 basket against an independently maintained list.

**Single-source, disclosed.** The daily price panels and index level series rest on one market data
distributor. They are internally consistent and complete for the claimed universes, but no second
price view is held. Any figure drawn from prices carries that exposure.

**Known to be stale or degraded, and labelled as such.**

- The S&P/ASX 200 constituent list is materially out of date. It retains companies removed from the
  index as long ago as 2017 and omits additions made since late 2025. It must not be used as the
  universe definition for ASX analysis until rebuilt. The index owner's announcement archive is the
  authority for the rebuild.
- The S&P/ASX 50 list holds 49 rows for a 50-member index and contains a listed fund that is not an
  index constituent.
- One published set of index weights was found to be systematically overstated (by roughly ten per
  cent per line, while still summing to 100 per cent, so no internal check detects it). It has been
  retired and replaced with the index owner's own fund holdings.
- A fund holdings file originally treated as an S&P/ASX 200 proxy is now known to track a different
  index. It is retained for comparison and is explicitly not an S&P/ASX 200 source.
- A delisted-companies file is a single page of an unknown-length list and is not used for index
  membership.

**Definitional decisions now fixed.** Two earlier reconstructions of S&P 500 membership
under-reported and over-reported the same quantity by different mechanisms, and disagreed with each
other by more than twelve per cent. One canonical reconstruction replaces both. It states its
window, its grain and its handling of companies that left and rejoined; and it is validated by an
independent test — the reconstruction's implied average index size must match the index's actual
size, which the two earlier versions failed and the canonical version passes.

**Identifier weakness.** The identifier map carries no ISIN values, and identifiers are present only
for two US baskets. ASX listings have no durable identifier in the dataset, and ticker symbols are
reused over time, so any join on ticker alone can silently merge two different companies. A
date-bounded or identifier-keyed join is required.

**Coverage.** Some genuinely delisted companies in the survivorship panel have no price data, and the
proportion is stated in the analysis rather than implied. The change history for membership is
incomplete by its own source's admission: a material minority of join dates are unknown, which
bounds the precision of any membership-year total.

## 5. Reproducibility

`scripts/` contains the full acquisition and derivation pipeline, ordered and documented in
`scripts/README.md`. Original inputs are never modified; derived outputs are regenerable. Every
figure quoted in the report should be traceable to a script output and a source.

## 6. Responsible use

Three positions are recorded explicitly:

1. Restricted source data is used analytically and is **not** redistributed.
2. Where a source could not be verified against its originating authority, the limitation is
   disclosed rather than presented as assurance.
3. Where a rebuild is required for a figure to be citable, the figure is withheld until the rebuild
   is complete, rather than quoted with a caveat.

AI tools were used to assist with code generation, data extraction and documentation review. All
numerical claims were recomputed independently, and source claims were checked against the
originating authority, before being accepted.
