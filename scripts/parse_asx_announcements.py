#!/usr/bin/env python3
"""parse the S&P/ASX announcement archive into one change log.

Two document shapes require two extractors:
  TABLE  quarterly rebalances carry an explicit  Action | Code | Company  table
         (the ASX 20/50/100/200/300 tables are segmented by index header)
  PROSE  ad-hoc documents (removals, additions, demergers) are written as sentences,
         e.g. "...it will remove Qube Holdings Limited (XASX: QUB) from the S&P/ASX 200
         Index... replaced by Develop Global Limited (XASX: DVP)... effective prior to
         the open of trading on Thursday, July 09, 2026."

Each row records which extractor produced it, so prose rows can be audited separately.

Writes derived/asx_changes.csv
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

STAGE1 = Path(__file__).resolve().parent.parent
TXT_DIR = Path("/tmp/ws3_text")
OUT = STAGE1 / "data" / "derived" / "asx_changes.csv"

HEADER_RE = re.compile(r"^\s*(S&P/ASX\s+\d+)\s+Index\s*[–-]\s*(.+?)\s*$")
ROW_RE = re.compile(
    r"^\s*(?:S&P/ASX\s+\d+\s+)?(Addition|Removal)\s+([A-Z0-9]{1,6})\s+(\S.*?)\s*$")
CODE_RE = re.compile(r"\(XASX:\s*([A-Z0-9]{1,6})\)")
EFF_RE = re.compile(
    r"effective[^.]{0,80}?on\s+(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s*"
    r"([A-Z][a-z]+)\s+(\d{1,2}),\s*(\d{4})", re.I)
MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"], 1)}


def iso(month: str, day: str, year: str) -> str:
    m = MONTHS.get(month.lower())
    return f"{int(year):04d}-{m:02d}-{int(day):02d}" if m else ""


def effective_iso_table(raw: str, fallback_year: int) -> str:
    t = (raw.replace("After Market Close", "").replace("At the Open", "")
            .replace("Effective", "").replace("Prior to the Open", ""))
    m = re.search(r"([A-Z][a-z]+)\.?\s+(\d{1,2}),?\s*(\d{4})", t)
    if m and m.group(1).lower() in MONTHS:
        return iso(m.group(1), m.group(2), m.group(3))
    m = re.search(r"([A-Z][a-z]+)\.?\s+(\d{1,2})\b(?!\s*,?\s*\d{4})", t)
    if m and m.group(1).lower() in MONTHS:
        return iso(m.group(1), m.group(2), str(fallback_year))
    return ""


def parse_prose(text: str, ann_date: str, src: str) -> list[dict]:
    """Extract ad-hoc events. Sentence-level, conservative."""
    out: list[dict] = []
    flat = re.sub(r"\s+", " ", text)
    eff = ""
    m = EFF_RE.search(flat)
    if m:
        eff = iso(m.group(1), m.group(2), m.group(3))

    # "...will remove <Company> (XASX: CODE) from the S&P/ASX 200 Index..."
    for m in re.finditer(
            r"(?:will\s+)?remove(?:s)?\s+(.{3,80}?)\s*\(XASX:\s*([A-Z0-9]{1,6})\)", flat, re.I):
        out.append({"announcement_date": ann_date, "index": "S&P/ASX200",
                    "effective_date": eff, "effective_as_reported": "",
                    "action": "Removal", "code": m.group(2),
                    "company": m.group(1).strip(), "source_file": src,
                    "source_url": "", "extractor": "prose"})
    # "...replaced by <Company> (XASX: CODE)..."
    for m in re.finditer(
            r"replaced\s+by\s+(.{3,80}?)\s*\(XASX:\s*([A-Z0-9]{1,6})\)", flat, re.I):
        out.append({"announcement_date": ann_date, "index": "S&P/ASX200",
                    "effective_date": eff, "effective_as_reported": "",
                    "action": "Addition", "code": m.group(2),
                    "company": m.group(1).strip(), "source_file": src,
                    "source_url": "", "extractor": "prose"})
    # "...will add <Company> (XASX: CODE)..."
    for m in re.finditer(
            r"(?:will\s+)?add(?:s)?\s+(.{3,80}?)\s*\(XASX:\s*([A-Z0-9]{1,6})\)", flat, re.I):
        out.append({"announcement_date": ann_date, "index": "S&P/ASX200",
                    "effective_date": eff, "effective_as_reported": "",
                    "action": "Addition", "code": m.group(2),
                    "company": m.group(1).strip(), "source_file": src,
                    "source_url": "", "extractor": "prose"})
    return out


def main() -> int:
    rows: list[dict] = []
    url_by_date: dict[str, str] = {}
    lst = STAGE1 / "data" / "derived" / "asx200_announcement_index.csv"
    if lst.exists():
        with lst.open(encoding="utf-8") as fh:
            url_by_date = {r["date"]: r["url"] for r in csv.DictReader(fh)}

    for f in sorted(TXT_DIR.glob("*.txt")):
        stem = f.stem
        d = re.match(r"^(\d{4})-?(\d{2})-?(\d{2})", stem)
        if not d:
            continue
        ann_date = f"{d.group(1)}-{d.group(2)}-{d.group(3)}"
        ann_year = int(d.group(1))
        text = f.read_text(encoding="utf-8", errors="replace")
        src = stem + ".pdf"

        index = eff_raw = None
        found_table = False
        for line in text.splitlines():
            h = HEADER_RE.match(line)
            if h:
                index, eff_raw = h.group(1), h.group(2)
                continue
            r = ROW_RE.match(line)
            if r and index:
                found_table = True
                rows.append({
                    "announcement_date": ann_date,
                    "index": index.replace(" ", ""),
                    "effective_date": effective_iso_table(eff_raw or "", ann_year),
                    "effective_as_reported": eff_raw or "",
                    "action": r.group(1), "code": r.group(2), "company": r.group(3),
                    "source_file": src, "source_url": url_by_date.get(ann_date, ""),
                    "extractor": "table",
                })
        if not found_table:
            rows.extend(parse_prose(text, ann_date, src))

    # dedupe exact repeats (some documents are re-issued under two filenames)
    seen = set()
    deduped = []
    for r in rows:
        key = (r["announcement_date"], r["index"], r["action"], r["code"],
               r["effective_date"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(r)

    deduped.sort(key=lambda r: (r["announcement_date"], r["index"],
                                r["action"], r["code"]))
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(deduped[0].keys()))
        w.writeheader()
        w.writerows(deduped)

    by_ex = {}
    for r in deduped:
        by_ex[r["extractor"]] = by_ex.get(r["extractor"], 0) + 1
    q = [r for r in deduped if r["index"] == "S&P/ASX200"]
    print(f"change log: {len(deduped)} rows ({len(rows)} before dedupe) "
          f"from {len(list(TXT_DIR.glob('*.txt')))} documents")
    print(f"  by extractor: {by_ex}")
    print(f"  S&P/ASX200 rows: {len(q)} · additions "
          f"{sum(1 for r in q if r['action'] == 'Addition')} · removals "
          f"{sum(1 for r in q if r['action'] == 'Removal')}")
    print(f"  no effective date: {sum(1 for r in deduped if not r['effective_date'])}")
    print(f"  span: {deduped[0]['announcement_date']} -> {deduped[-1]['announcement_date']}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
