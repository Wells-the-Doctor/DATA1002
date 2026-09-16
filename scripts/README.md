# Stage 1 — dataset acquisition and quality pipeline

Python 3.12. Third-party dependencies: `pandas`, `requests`, `yfinance`, `openpyxl`.
Everything else is the standard library.

Each script resolves the project root **relative to its own file location**, so the repository can
be cloned to any machine or path without modification.

## Layout assumed

```
<project root>/
├── data/
│   ├── raw/        original downloads — read-only, not tracked (see .gitignore)
│   └── cleaned/    cleaned and derived outputs
└── scripts/        these scripts
```

`data/raw/` is the source of truth and is never edited. Derived outputs are written to
`data/cleaned/` or to a script-specified output path.

## Credentials

Three scripts query vendor APIs and read their keys from the environment, or from a `.env` file in
the project root:

```
FMP_API_KEY=...          # Financial Modeling Prep (free tier)
FINNHUB_API_KEY=...      # Finnhub (free tier)
```

Copy `.env.example` to `.env` and fill it in. `.env` is gitignored and must never be committed.
The three scripts that require keys are `fetch_upgrades.py`, `fetch_survivorship_panel.py` and
`build_membership_pointintime.py`; the remainder need no credentials.

## Pipeline

### 1. Acquisition

| Script | Purpose |
|:--|:--|
| `fetch_raw.py` | Primary acquisition: index level series, constituent lists, and 10-year daily price panels |
| `fetch_constituents_extra.py` | Supplementary constituent sources (independent Dow 30 and Nasdaq-100 routes) |
| `fetch_patch_constituents.py` | Repairs two constituent tables missed by the first pass |
| `fetch_upgrades.py` | Sources that require no browser session (needs `FINNHUB_API_KEY`) |
| `fetch_owner_weights.py` | Owner-published index weights and fund holdings: S&P 500 (SPY), Nasdaq-100 (QQQ), Dow 30 (DIA), ASX 200 (A200) |
| `fetch_survivorship_panel.py` | Survivorship-safe US price panel: current, added and removed members (`FMP_API_KEY`, `FINNHUB_API_KEY`) |

### 2. S&P/ASX 200 announcement archive and change log

| Script | Purpose |
|:--|:--|
| `enumerate_asx_announcements.py` | Enumerate the published quarterly rebalance announcement documents |
| `harvest_asx_announcements.py` | Download the archive (union of two publication routes) |
| `build_announcement_index.py` | Build the document index (date, type, file, URL) |
| `parse_asx_announcements.py` | Parse the archive into a single membership change log |

### 3. Derived builds

| Script | Purpose |
|:--|:--|
| `build_identifier_map.py` | Cross-market identifier map (CUSIP, SEDOL, ISIN where available) |
| `reconcile_owner_weights.py` | Reconciliation of the owner-published weights against the held lists |
| `build_membership_canonical.py` | **Canonical** S&P 500 membership-year reconstruction, 2016-09-12 → 2026-09-11 |
| `build_membership_pointintime.py` | Point-in-time membership, first construction — **superseded** (see below) |
| `build_membership_v2.py` | Membership intervals, second construction — **superseded** (see below) |

### 4. Integrity

| Script | Purpose |
|:--|:--|
| `verify_raw_integrity.py` | SHA-256 tamper alarm over `data/raw/`. `--rehash` re-establishes the baseline after an intentional re-pull |

## A note on the two superseded membership builds

Two earlier constructions of S&P 500 index membership are retained for auditability, and both are
superseded by `build_membership_canonical.py`:

- **`build_membership_pointintime.py`** collapses each ticker to a single most-recent join and a
  single most-recent leave. A company that left and later rejoined produces an inverted interval and
  is silently credited zero years, which materially understates the total.
- **`build_membership_v2.py`** builds intervals per ticker correctly, but treats an internal
  "pre-window" marker as a truthy value, which inflates the total. Its output file was also saved
  ad hoc, without a producing script.

Neither figure should be cited. `build_membership_canonical.py` reproduces the corrected total
(5,036.5 membership-years over the stated window) and carries an independent acceptance test: the
reconstruction's implied mean index size must match the index's actual size. Its output carries a
stated window, a stated grain, and a disclosed completeness bound.
