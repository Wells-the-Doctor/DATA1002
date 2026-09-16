#!/usr/bin/env python3
"""
Stage 1 — RAW data acquisition.

Fetches every route verified as available on 2026-09-12 and saves exactly what the
source returned, unmodified, under data/raw/. Nothing is cleaned here: this
is the "original data as obtained" copy the specification asks us to keep.

Sources:
  - Index level series            yfinance
  - Constituent lists             Wikipedia tables (plus HTML snapshots for provenance)
  - Constituent daily prices      yfinance (bulk)

Writes: data/raw/index_levels/, data/raw/constituents/, data/raw/prices/,
        data/raw/source_snapshots/, data/raw/MANIFEST.json
"""
import os, io, json, datetime, warnings, traceback

warnings.filterwarnings("ignore")
import pandas as pd
import requests
import yfinance as yf

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw")
RETRIEVED = datetime.date.today().isoformat()
UA = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
    )
}
MANIFEST = []


def log(msg):
    print(msg, flush=True)


def record(kind, name, source, url, path, rows, cols, note=""):
    MANIFEST.append(
        {
            "kind": kind,
            "name": name,
            "source": source,
            "source_url": url,
            "retrieved": RETRIEVED,
            "file": os.path.relpath(path, BASE),
            "rows": int(rows),
            "cols": int(cols),
            "bytes": os.path.getsize(path),
            "note": note,
        }
    )


def save(df, rel, kind, name, source, url, note=""):
    path = os.path.join(BASE, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    kb = os.path.getsize(path) / 1024
    log(f"    saved {rel}  shape={df.shape}  {kb:.0f} KB")
    record(kind, name, source, url, path, df.shape[0], df.shape[1], note)
    return path


def flatten(df):
    """Collapse MultiIndex column labels into single strings."""
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = [" ".join(str(x) for x in tup).strip() for tup in df.columns]
    else:
        df = df.copy()
        df.columns = [str(c).strip() for c in df.columns]
    return df


# ─────────────────────────────────────────────────── 1. index level series
log("\n[1] index level series (yfinance)")
INDEXES = {
    "asx_200": "^AXJO",
    "all_ordinaries": "^AORD",
    "asx_300": "^AXKO",
    "asx_small_ordinaries": "^AXSO",
    "sp_500": "^GSPC",
    "dow_jones_30": "^DJI",
    "nasdaq_100": "^NDX",
    "ftse_100": "^FTSE",
    "nikkei_225": "^N225",
    "hang_seng": "^HSI",
}
try:
    frames = []
    for name, tk in INDEXES.items():
        h = yf.Ticker(tk).history(period="max", auto_adjust=False)
        if not len(h):
            log(f"    {name:22s} EMPTY")
            continue
        h = h.reset_index()
        h.insert(0, "index_name", name)
        h.insert(1, "symbol", tk)
        h["retrieved"] = RETRIEVED
        frames.append(h)
        log(f"    {name:22s} rows={len(h):5d}  {str(h['Date'].iloc[0])[:10]} -> {str(h['Date'].iloc[-1])[:10]}")
    if frames:
        allidx = pd.concat(frames, ignore_index=True)
        save(allidx, "index_levels/index_levels_all.csv", "index_levels", "Index level series (10 indices)", "yfinance (Yahoo Finance)", "https://finance.yahoo.com/")
except Exception:
    log("    FAILED: " + traceback.format_exc().splitlines()[-1])

# ─────────────────────────────────────────────────── 2. constituent lists
log("\n[2] constituent lists (Wikipedia)")
WIKI = {
    "asx_20": ("https://en.wikipedia.org/wiki/S%26P/ASX_20", "S&P/ASX 20"),
    "asx_50": ("https://en.wikipedia.org/wiki/S%26P/ASX_50", "S&P/ASX 50"),
    "asx_200": ("https://en.wikipedia.org/wiki/S%26P/ASX_200", "S&P/ASX 200"),
    "sp_500": ("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies", "S&P 500 (current)"),
    "sp_500_changes": ("https://en.wikipedia.org/wiki/Historical_components_of_the_S%26P_500", "S&P 500 (membership changes)"),
    "ftse_100": ("https://en.wikipedia.org/wiki/FTSE_100_Index", "FTSE 100"),
}
TICKER_COLS = {"code", "symbol", "ticker"}
constituents = {}

for key, (url, label) in WIKI.items():
    try:
        r = requests.get(url, headers=UA, timeout=45)
        # keep the raw page for provenance
        snap = os.path.join(BASE, "source_snapshots", f"{key}_wikipedia.html")
        os.makedirs(os.path.dirname(snap), exist_ok=True)
        with open(snap, "w", encoding="utf-8") as fh:
            fh.write(r.text)
        tables = pd.read_html(io.StringIO(r.text))
        pick = None
        for t in tables:
            cols = [str(c).lower() for c in flatten(t).columns]
            if any(c in TICKER_COLS for c in cols) and t.shape[0] >= 15:
                if pick is None or t.shape[0] > pick.shape[0]:
                    pick = t
        if pick is None:
            log(f"    {key:16s} no constituent table found ({len(tables)} tables)")
            continue
        df = flatten(pick)
        constituents[key] = df
        save(df, f"constituents/{key}.csv", "constituents", label, "Wikipedia (CC BY-SA)", url,
             note=f"{len(tables)} tables on page; snapshot saved")
    except Exception:
        log(f"    {key:16s} FAILED: {traceback.format_exc().splitlines()[-1]}")

# ─────────────────────────────────────────────────── 3. constituent prices
log("\n[3] constituent daily prices (yfinance, 10y)")


def ticker_from(df, market):
    """Pull the ticker column out of a constituent table and map to Yahoo symbols."""
    col = None
    for c in df.columns:
        if str(c).strip().lower() in TICKER_COLS:
            col = c
            break
    if col is None:
        return []
    vals = df[col].astype(str).str.strip()
    out = []
    for v in vals:
        if not v or v.lower() == "nan" or len(v) > 8:
            continue
        if market == "asx":
            out.append((v.upper() + ".AX") if not v.upper().endswith(".AX") else v.upper())
        elif market == "lse":
            base = v.upper().replace(".L", "")
            out.append(base + ".L")
        else:
            out.append(v.upper().replace(".", "-"))
    return sorted(set(out))


MARKETS = [("asx", "asx_200"), ("us", "sp_500"), ("lse", "ftse_100")]
for market, key in MARKETS:
    try:
        df = constituents.get(key)
        if df is None:
            log(f"    {market}: no constituent list available, skipped")
            continue
        tickers = ticker_from(df, market)
        log(f"    {market}: {len(tickers)} tickers -> downloading 10y daily")
        data = yf.download(tickers, period="10y", interval="1d", auto_adjust=False,
                           threads=True, progress=False, group_by="column")
        if not len(data):
            log(f"    {market}: download returned nothing")
            continue
        # coverage report
        if "Close" in data.columns.get_level_values(0):
            cov = data["Close"].notna().sum()
            log(f"    {market}: {int((cov > 0).sum())}/{len(tickers)} tickers returned data")
        out = data.copy()
        out.columns = [" | ".join(str(x) for x in tup) if isinstance(tup, tuple) else str(tup)
                       for tup in out.columns]
        out = out.reset_index()
        save(out, f"prices/{market}_constituents_10y_daily.csv", "prices",
             f"{market.upper()} constituent daily prices (10y)",
             "yfinance (Yahoo Finance)", "https://finance.yahoo.com/",
             note=f"{len(tickers)} tickers requested")
    except Exception:
        log(f"    {market}: FAILED: {traceback.format_exc().splitlines()[-1]}")

# ─────────────────────────────────────────────────── 4. manifest
man_path = os.path.join(BASE, "MANIFEST.json")
os.makedirs(BASE, exist_ok=True)
with open(man_path, "w", encoding="utf-8") as fh:
    json.dump(
        {"retrieved": RETRIEVED, "base": BASE, "note": "Raw pulls, unmodified as obtained.", "files": MANIFEST},
        fh, indent=2,
    )
log(f"\n[4] manifest written: {man_path}  ({len(MANIFEST)} entries)")
log("acquisition complete")
