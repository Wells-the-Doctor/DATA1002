#!/usr/bin/env python3
"""build the identifier map.

The rule: **a ticker is a display field, never a join key.** This script assembles
what identifiers we actually hold, per market, and records the gaps explicitly
rather than leaving them blank-and-silent.

Sources:
  US  : SSGA DIA + SPY issuer holdings (carry CUSIP + SEDOL)
  ASX : Betashares A200 basket (ticker + name) + ASX's own listed-companies
        directory (ticker + name + GICS industry group, owner-published)

Writes derived/identifier_map.csv
"""
from __future__ import annotations

import csv
from pathlib import Path

STAGE1 = Path(__file__).resolve().parent.parent
RAW = STAGE1 / "data" / "raw" / "constituents"
DER = STAGE1 / "data" / "derived"
ASX_DIR_CACHE = Path(__file__).resolve().parent / "asx_listed_companies.csv"
OUT = DER / "identifier_map.csv"

FIELDS = ["market", "ticker", "name", "isin", "cusip", "sedol",
          "in_a200_basket", "in_index_list", "source", "notes"]


def rows(p: Path) -> list[dict]:
    with p.open(encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    out: list[dict] = []

    # ---- US: identifiers come free with the issuer files -------------------
    for f, market in (("dow_30_weights_dia_owner_weights.csv", "US-Dow30"),
                      ("sp500_weights_spy_owner_weights.csv", "US-SP500")):
        for r in rows(DER / f):
            note = ""
            if r["ticker"] == "2682320D":
                note = ("successor entity of ONEOK (merger 2026-08-28); our list holds "
                        "the same company as OKE - a ticker join drops it")
            elif "CONTRA" in r["name"].upper():
                note = "contingent value right (corporate action), not a constituent"
            out.append({
                "market": market, "ticker": r["ticker"], "name": r["name"],
                "isin": "", "cusip": r.get("identifier", "").strip(),
                "sedol": r.get("sedol", "").strip(),
                "in_a200_basket": "", "in_index_list": "yes",
                "source": "issuer holdings (SSGA)", "notes": note,
            })

    # ---- ASX: ticker + name only. No ISIN source found. --------------------
    basket = {r["ticker"]: r for r in rows(DER / "asx200_weights_a200_owner_weights.csv")
              if r["asset_class"] == "Equities"}
    our_list = {r["Code"] for r in rows(RAW / "asx_200.csv")}

    dir_codes: dict[str, str] = {}
    if ASX_DIR_CACHE.exists():
        raw = list(csv.reader(ASX_DIR_CACHE.open(encoding="utf-8-sig")))
        for x in raw[2:]:
            if len(x) > 1 and x[1].strip():
                dir_codes[x[1].strip()] = x[0].strip()

    for code in sorted(set(basket) | set(dir_codes) | our_list):
        b = basket.get(code)
        notes = []
        if code not in dir_codes:
            notes.append("NOT in the ASX listed-companies directory")
        if code in basket and code not in our_list:
            notes.append("in the A200 basket, missing from our index list")
        if code in our_list and code not in basket:
            notes.append("in our index list, absent from the A200 basket")
        if code not in dir_codes and code not in basket:
            notes.append("ticker appears only in our index list")
        out.append({
            "market": "ASX", "ticker": code,
            "name": (b["name"] if b else dir_codes.get(code, "")),
            "isin": "", "cusip": "", "sedol": "",
            "in_a200_basket": "yes" if b else "",
            "in_index_list": "yes" if code in our_list else "",
            "source": "A200 basket + ASX listed-companies directory",
            "notes": "; ".join(notes) + ("; NO ISIN SOURCE HELD" if True else ""),
        })

    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(out)

    us = [r for r in out if r["market"].startswith("US")]
    asx = [r for r in out if r["market"] == "ASX"]
    print(f"identifier_map.csv: {len(out)} rows")
    print(f"  US  : {len(us)} rows · CUSIP present {sum(1 for r in us if r['cusip'])}"
          f" · SEDOL present {sum(1 for r in us if r['sedol'])} · ISIN present 0")
    print(f"  ASX : {len(asx)} rows · CUSIP 0 · SEDOL 0 · ISIN 0  <-- the named gap")
    print(f"written: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
