# DATA1002 — Group Project Stage 1

Informatics: Data and Computation (2026 Semester 2) — collaborative data science
investigation. Groups of 4–5, same lab.

## Project

- **Research question (locked 2026-09-12):** How well does the index represent the
  market? (concentration, survivorship bias, constituent turnover)
- **Due:** 5 pm Sunday, end of Week 9
- **Value:** 20% of the unit
- **Format:** combined report (Sections A–E) + per-member code and dataset folders,
  submitted as a zip on Canvas

## Report structure

| Section | Content | Length | Mark |
|:--|:--|:--|:--|
| A | Introduction and project context | 1 page | Group |
| B | Data preparation (per member) | 2 pp/ind | Individual |
| C | Exploration, visualisation, insight (per member) | 4 pp/ind | Individual |
| D | Group findings, recommendations, Responsible AI | 2 pages | Group |
| E | References | — | Group |

## Repository layout

```
DATA1002/
├── README.md          # This file
├── data/
│   ├── raw/           # Original datasets (read-only source of truth)
│   └── cleaned/       # Cleaned/preprocessed datasets
├── scripts/           # Shared Python: cleaning, analysis, charting
├── report/            # Report source and assets
└── shared/            # Shared content across members
```

Per-member submission folders are assembled at packaging time (for the Canvas
zip), not tracked in the repository — the group works from one shared layout.

## Conventions

- **Professional register:** everything group-visible is written in a formal, professional register — no personal references, no emoticons, no local machine paths.
- **Data integrity:** `data/raw/` is read-only. Clean copies and derived outputs
  live in `data/cleaned/` or script outputs — never overwrite the originals.
