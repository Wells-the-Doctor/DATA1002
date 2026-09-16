#!/usr/bin/env python3
"""harvest the S&P/ASX 200 announcement archive (union of both routes).

Route A (ISO-named):     files.marketindex.com.au/files/announcements/{YYYYMMDD}-asx200-{type}.pdf
Route B (canonical):     files.marketindex.com.au/files/announcements/rebalance/{YYYY}-rebalance-{month}.pdf

Route A carries the ad-hoc events (removals / additions / demergers); route B carries
the quarterly rebalances the ISO set is missing. The union is what makes the change log
complete enough to walk membership backwards.

PDFs -> raw/asx_announcements/  ·  text layer -> /tmp/ws3_text (regenerable)
"""
from __future__ import annotations

import csv
import subprocess
from pathlib import Path

STAGE1 = Path(__file__).resolve().parent.parent
INDEX = STAGE1 / "data" / "derived" / "asx200_announcement_index.csv"
PDF_DIR = STAGE1 / "data" / "raw" / "asx_announcements"
TXT_DIR = Path("/tmp/ws3_text")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"

# Route B documents for quarters route A lacks (confirmed reachable).
ROUTE_B = [
    ("2017-03-03", "rebalance/2017-rebalance-march.pdf"),
    ("2017-03-03", "rebalance/2017-rebalance-march-updated.pdf"),
    ("2020-09-04", "20200904-asx200-rebalance.pdf"),
    ("2020-12-11", "20201211-asx200-rebalance.pdf"),
    ("2021-09-03", "20210903-asx200-rebalance.pdf"),
]
BASE = "https://files.marketindex.com.au/files/announcements/"


def fetch(url: str, dest: Path) -> bool:
    if dest.exists() and dest.stat().st_size > 5000:
        return True
    r = subprocess.run(["curl", "-sS", "-L", "--max-time", "60", "-A", UA,
                        "-o", str(dest), url], capture_output=True)
    return r.returncode == 0 and dest.exists() and dest.stat().st_size > 5000


def main() -> int:
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    TXT_DIR.mkdir(parents=True, exist_ok=True)

    jobs: list[tuple[str, str, str]] = []          # (date, filename, url)
    with INDEX.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            jobs.append((r["date"], r["file"], r["url"]))
    seen = {f for _, f, _ in jobs}
    for date, rel in ROUTE_B:
        fn = rel.split("/")[-1]
        if fn not in seen:
            jobs.append((date, fn, BASE + rel))

    ok = failed = 0
    for date, fn, url in jobs:
        pdf = PDF_DIR / fn
        if not fetch(url, pdf):
            print(f"  FAIL download {fn}")
            failed += 1
            continue
        txt = TXT_DIR / f"{fn[:-4]}.txt"
        if subprocess.run(["pdftotext", "-layout", str(pdf), str(txt)],
                          capture_output=True).returncode != 0:
            print(f"  FAIL pdftotext {fn}")
            failed += 1
            continue
        ok += 1

    print(f"harvest: {ok} documents converted · {failed} failed · {len(jobs)} attempted")
    print(f"pdfs in raw/asx_announcements: {len(list(PDF_DIR.glob('*.pdf')))}")
    print(f"text files: {len(list(TXT_DIR.glob('*.txt')))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
