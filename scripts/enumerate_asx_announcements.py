#!/usr/bin/env python3
"""enumerate S&P/ASX 200 quarterly rebalance announcements.

Route: files.marketindex.com.au mirrors the S&P DJI announcement PDF at a
predictable path -- /files/announcements/{YYYYMMDD}-asx200-rebalance.pdf
(missing dates return 403, not 404, so a HEAD is a clean existence test).

Scans the first three Fridays of each announcement month (Mar/Jun/Sep/Dec),
because the owner publishes ~1-2 weeks before the quarterly effective date.

Writes: asx200_announcements.csv  (date, url, http, bytes)
"""
from __future__ import annotations

import csv
import datetime
import subprocess
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent / "asx200_announcements.csv"
BASE = "https://files.marketindex.com.au/files/announcements/{d}-asx200-rebalance.pdf"


def fridays(year: int, month: int, take: int = 3) -> list[datetime.date]:
    d = datetime.date(year, month, 1)
    out: list[datetime.date] = []
    while d.month == month and len(out) < take:
        if d.weekday() == 4:
            out.append(d)
        d += datetime.timedelta(days=1)
    return out


def probe(url: str) -> tuple[str, int]:
    r = subprocess.run(
        ["curl", "-sS", "-L", "--max-time", "20", "-A", "Mozilla/5.0",
         "-o", "/dev/null", "-w", "%{http_code}|%{size_download}", url],
        capture_output=True, text=True)
    code, _, size = (r.stdout.strip() or "000|0").partition("|")
    return code, int(size or 0)


def main() -> int:
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 2006
    end = int(sys.argv[2]) if len(sys.argv) > 2 else 2026
    rows = []
    for year in range(start, end + 1):
        for month in (3, 6, 9, 12):
            for d in fridays(year, month):
                url = BASE.format(d=d.strftime("%Y%m%d"))
                code, size = probe(url)
                if code in ("200", "206"):
                    rows.append({"date": d.isoformat(), "url": url,
                                 "http": code, "bytes": size})
                    print(f"  HIT {d.isoformat()}  {size:>8} bytes")
    rows.sort(key=lambda r: r["date"])
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["date", "url", "http", "bytes"])
        w.writeheader()
        w.writerows(rows)
    years = sorted({r["date"][:4] for r in rows})
    print(f"\n{len(rows)} announcements · {rows[0]['date']} -> {rows[-1]['date']} "
          f"· {len(years)} calendar years present")
    missing = [y for y in range(int(rows[0]['date'][:4]), int(rows[-1]['date'][:4]) + 1)
               if str(y) not in years]
    print(f"years with no hit between first and last: {missing or 'none'}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
