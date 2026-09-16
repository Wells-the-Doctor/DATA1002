#!/usr/bin/env python3
"""Acquire owner-published index weights.

Replaces borrowed/derived weight fields with issuer-published holdings files.

Sources (all plain fetches, no key, no browser):
  WS1.2  Dow 30        SPDR Dow Jones Industrial Average ETF (DIA) holdings  -> SSGA
  WS1.3  S&P 500       SPDR S&P 500 ETF Trust (SPY) holdings                 -> SSGA
  WS1.4  ASX 200       Betashares Australia 200 ETF (A200) portfolio holdings
  WS1.5  FTSE 100      -- NOT ACQUIRED. See WS1.5 note in the run summary.

Writes:
  raw/constituents/*            the pulls, byte-for-byte as served
  derived/*_owner_weights.csv   normalised tables for use
  derived/manifest_annotated.json  annotation-layer rows (capture_method, as-of,
                                   rights, status, snapshot, sha256)

Rule: never edit raw/. This script only ever creates files there.
"""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from datetime import date
from io import StringIO
from pathlib import Path

STAGE1 = Path(__file__).resolve().parent.parent
RAW = STAGE1 / "data" / "raw"
DERIVED = STAGE1 / "data" / "derived"
MANIFEST = DERIVED / "manifest_annotated.json"

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

SOURCES = [
    {
        "ws": "1.2",
        "kind": "index_weights",
        "name": "Dow 30 weights (issuer-published, DIA basket)",
        "issuer": "State Street Global Advisors (SPDR)",
        "url": "https://www.ssga.com/us/en/intermediary/library-content/products/"
               "fund-data/etfs/us/holdings-daily-us-en-dia.xlsx",
        "raw_file": "constituents/dow_30_weights_dia.xlsx",
        "proxy_note": "DIA basket is the price-weighted Dow 30; a proxy for the index "
                      "(ETF holds cash and residual positions).",
    },
    {
        "ws": "1.3",
        "kind": "index_weights",
        "name": "S&P 500 weights (issuer-published, SPY basket)",
        "issuer": "State Street Global Advisors (SPDR)",
        "url": "https://www.ssga.com/us/en/intermediary/library-content/products/"
               "fund-data/etfs/us/holdings-daily-us-en-spy.xlsx",
        "raw_file": "constituents/sp500_weights_spy.xlsx",
        "proxy_note": "SPY basket is a full-replication S&P 500 proxy; weights are "
                      "fund weights, not index weights (cash drag applies).",
    },
    {
        "ws": "1.4",
        "kind": "index_weights",
        "name": "ASX 200 weights (issuer-published, A200 basket)",
        "issuer": "Betashares",
        "url": "https://www.betashares.com.au/files/csv/A200_Portfolio_Holdings.csv",
        "raw_file": "constituents/asx200_weights_a200.csv",
        "proxy_note": "A200 basket is a full-replication S&P/ASX 200 proxy; weights are "
                      "fund weights. Carries shares/units and market value per line.",
    },
]


def fetch(url: str) -> bytes:
    """Fetch via curl.

    Note: Python's urllib on this interpreter fails TLS verification against these
    hosts (incomplete local CA chain). curl is the transport the routes were probed
    with, so we use it rather than papering over the CA problem.
    """
    proc = subprocess.run(
        ["curl", "-sS", "-L", "--max-time", "120", "-A", UA, url],
        capture_output=True,
        check=True,
    )
    if not proc.stdout:
        raise SystemExit(f"empty response from {url}")
    return proc.stdout


def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def sga_xlsx_to_rows(path: Path) -> list[dict]:
    """Parse a State Street holdings .xlsx into normalised rows."""
    import openpyxl

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()

    hdr_i = next(i for i, r in enumerate(rows)
                 if r and str(r[0] or "").strip() == "Name" and "Weight" in [str(x) for x in r])
    hdr = [str(x).strip() if x is not None else "" for x in rows[hdr_i]]
    idx = {c: hdr.index(c) for c in ("Name", "Ticker", "Identifier", "SEDOL", "Weight",
                                     "Shares Held", "Local Currency") if c in hdr}

    as_of = ""
    for r in rows[:hdr_i]:
        cells = [str(x) for x in r if x]
        for c in cells:
            if c.startswith("As of"):
                as_of = c.replace("As of", "").strip()

    out = []
    for r in rows[hdr_i + 1:]:
        if not r or not r[idx["Ticker"]]:
            continue
        tick = str(r[idx["Ticker"]]).strip()
        if not tick or tick.lower() in ("nan", "-"):
            continue
        try:
            w = float(r[idx["Weight"]])
        except (TypeError, ValueError):
            continue
        if w <= 0:
            continue
        out.append({
            "ticker": tick,
            "name": str(r[idx["Name"]] or "").strip(),
            "identifier": str(r[idx.get("Identifier", 0)] or "").strip() if "Identifier" in idx else "",
            "sedol": str(r[idx.get("SEDOL", 0)] or "").strip() if "SEDOL" in idx else "",
            "weight_pct": w,
            "shares": r[idx.get("Shares Held", 0)] if "Shares Held" in idx else "",
            "currency": str(r[idx.get("Local Currency", 0)] or "").strip() if "Local Currency" in idx else "",
        })
    return out, as_of


def betashares_csv_to_rows(path: Path) -> tuple[list[dict], str]:
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()

    as_of = ""
    for l in lines[:12]:
        if l.lower().startswith("date,"):
            as_of = l.split(",", 1)[1].strip()

    hdr_i = next(i for i, l in enumerate(lines) if l.startswith("Ticker,Name"))
    rdr = csv.DictReader(StringIO("\n".join(lines[hdr_i:])))
    out = []
    for r in rdr:
        tick = (r.get("Ticker") or "").strip()
        if not tick or "\n" in tick or tick.startswith('"'):
            continue
        try:
            w = float(r.get("Weight (%)") or "")
        except ValueError:
            continue
        out.append({
            "ticker": tick.replace(" AT", "").strip(),
            "ticker_as_reported": tick,
            "name": (r.get("Name") or "").strip(),
            "asset_class": (r.get("Asset Class") or "").strip(),
            "sector": (r.get("Sector") or "").strip(),
            "country": (r.get("Country") or "").strip(),
            "currency": (r.get("Currency") or "").strip(),
            "weight_pct": w,
            "shares": (r.get("Shares/Units (#)") or "").strip(),
            "market_value": (r.get("Market Value (AUD)") or "").strip(),
        })
    return out, as_of


def write_csv(rows: list[dict], path: Path) -> None:
    if not rows:
        raise SystemExit(f"refusing to write empty file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    DERIVED.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {"files": []}
    existing = {e.get("file") for e in manifest.get("files", [])}

    today = date.today().isoformat()
    summary = []

    for src in SOURCES:
        raw_path = RAW / src["raw_file"]
        print(f"[{src['ws']}] fetching {src['url'][:88]}")
        blob = fetch(src["url"])
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_bytes(blob)

        if raw_path.suffix == ".xlsx":
            rows, as_of = sga_xlsx_to_rows(raw_path)
        else:
            rows, as_of = betashares_csv_to_rows(raw_path)

        rel = raw_path.relative_to(RAW).as_posix()
        derived_name = rel.replace("constituents/", "").replace(".xlsx", ".csv")
        derived_name = derived_name.replace("_dia.csv", "_dia_owner_weights.csv") \
                                   .replace("_spy.csv", "_spy_owner_weights.csv") \
                                   .replace("_a200.csv", "_a200_owner_weights.csv")
        derived_path = DERIVED / derived_name
        write_csv(rows, derived_path)

        wsum = sum(r["weight_pct"] for r in rows)
        digest = sha256_of(raw_path)
        summary.append((src["ws"], src["name"], len(rows), round(wsum, 3), as_of,
                        raw_path.stat().st_size, digest[:12]))

        entry = {
            "kind": src["kind"],
            "name": src["name"],
            "source": src["issuer"],
            "source_url": src["url"],
            "retrieved": today,
            "file": rel,
            "rows": len(rows),
            "cols": len(rows[0]) if rows else 0,
            "bytes": raw_path.stat().st_size,
            "note": src["proxy_note"],
            "capture_method": "script",
            "source_as_of": f"issuer file dated {as_of}" if as_of else "not stated in file",
            "rights": "issuer-published public holdings file; no key, no login",
            "status": "active",
            "snapshot": None,
            "sha256": digest,
            "derived": f"derived/{derived_name}",
            "ws": src["ws"],
        }
        manifest["files"] = [e for e in manifest.get("files", []) if e.get("file") != rel]
        manifest["files"].append(entry)
        existing.add(rel)

    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")

    print("\n=== WS1 acquisition summary ===")
    print(f"{'ws':<5}{'rows':>6}{'wsum%':>9}  {'as-of':<12}{'bytes':>9}  sha256:12")
    for ws, name, n, ws_, as_of, b, d in summary:
        print(f"{ws:<5}{n:>6}{ws_:>9}  {as_of:<12}{b:>9}  {d}")
    print(f"\nmanifest entries now: {len(manifest['files'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
