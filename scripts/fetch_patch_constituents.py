#!/usr/bin/env python3
"""
Stage 1 — patch for two constituent tables missed by the first acquisition pass.

The first pass matched ticker columns by exact name. Two pages label them
differently (multi-index headers), so the tables were skipped. This re-fetches
them with word-level column matching and updates the manifest.

Targets: S&P/ASX 20 constituents, S&P 500 membership changes.
"""
import os, io, json, datetime, warnings

warnings.filterwarnings("ignore")
import pandas as pd
import requests

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw")
RETRIEVED = datetime.date.today().isoformat()
UA = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
    )
}
TICKER_WORDS = {"code", "symbol", "ticker", "tickers", "ric"}

TARGETS = {
    "asx_20": ("https://en.wikipedia.org/wiki/S%26P/ASX_20", "S&P/ASX 20"),
    "sp_500_changes": (
        "https://en.wikipedia.org/wiki/Historical_components_of_the_S%26P_500",
        "S&P 500 (membership changes)",
    ),
}


def flatten(df):
    df = df.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [" ".join(str(x) for x in tup).strip() for tup in df.columns]
    else:
        df.columns = [str(c).strip() for c in df.columns]
    return df


def words_of(cols):
    out = set()
    for c in cols:
        cleaned = str(c).lower().replace("(", " ").replace(")", " ").replace("'", " ").replace(",", " ")
        out |= {w for w in cleaned.split() if w}
    return out


new_entries = []
for key, (url, label) in TARGETS.items():
    try:
        r = requests.get(url, headers=UA, timeout=45)
        snapshot = os.path.join(BASE, "source_snapshots", f"{key}_wikipedia.html")
        os.makedirs(os.path.dirname(snapshot), exist_ok=True)
        with open(snapshot, "w", encoding="utf-8") as fh:
            fh.write(r.text)

        tables = pd.read_html(io.StringIO(r.text))
        best, best_shape = None, None
        for t in tables:
            if t.shape[0] < 15:
                continue
            if words_of(flatten(t).columns) & TICKER_WORDS:
                if best is None or t.shape[0] > best.shape[0]:
                    best, best_shape = flatten(t), t.shape
        if best is None:
            print(f"  {key:16s} still not found ({len(tables)} tables)")
            continue

        path = os.path.join(BASE, "constituents", f"{key}.csv")
        best.to_csv(path, index=False)
        print(f"  {key:16s} saved shape={best.shape}  cols={list(best.columns)[:8]}")
        print(f"  {'':16s} first row: {list(best.iloc[0])[:6]}")
        new_entries.append(
            {
                "kind": "constituents",
                "name": label,
                "source": "Wikipedia (CC BY-SA)",
                "source_url": url,
                "retrieved": RETRIEVED,
                "file": os.path.relpath(path, BASE),
                "rows": int(best.shape[0]),
                "cols": int(best.shape[1]),
                "bytes": os.path.getsize(path),
                "note": f"{len(tables)} tables on page; word-level column match; snapshot saved",
            }
        )
    except Exception as e:
        print(f"  {key:16s} FAILED {type(e).__name__}: {str(e)[:90]}")

man_path = os.path.join(BASE, "MANIFEST.json")
if os.path.exists(man_path):
    with open(man_path, encoding="utf-8") as fh:
        man = json.load(fh)
    names = {e["name"] for e in new_entries}
    man["files"] = [e for e in man["files"] if e["name"] not in names] + new_entries
    man["patched"] = RETRIEVED
    with open(man_path, "w", encoding="utf-8") as fh:
        json.dump(man, fh, indent=2)
    print(f"\nmanifest updated: {len(man['files'])} entries")
