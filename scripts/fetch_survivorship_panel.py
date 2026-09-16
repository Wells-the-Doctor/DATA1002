#!/usr/bin/env python3
"""
Stage 1 — survivorship-safe price panel (US).

The bias in our first price pull: it asked Yahoo for TODAY's constituents, so every
company that left the index was never requested. This script asks for the UNION of
current and historical members, then reports honestly who could be priced and who
could not — because the unpriced names are the survivorship population.

Inputs : constituents/sp_500.csv (current, 503)
         constituents/sp_500_changes.csv (407 events: 373 unique removed, 384 added)
Outputs: prices/us_panel_long.csv          long format: ticker,date,ohlcv,adj_close
         prices/us_panel_coverage.csv      per-ticker status, rows, first/last date
         constituents/us_delisted_fmp.csv  FMP dated delisting list (free tier)
"""
import os, sys, json, time, datetime, warnings, traceback

warnings.filterwarnings("ignore")
import pandas as pd
import requests
import yfinance as yf

RAW = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw")
OUT = os.path.join(RAW, "prices")
os.makedirs(OUT, exist_ok=True)
LONG_CSV = os.path.join(OUT, "us_panel_long.csv")
COV_CSV = os.path.join(OUT, "us_panel_coverage.csv")
RETRIEVED = datetime.date.today().isoformat()
CHUNK = 100


def log(m):
    print(m, flush=True)


def norm(t):
    """Wikipedia symbols -> Yahoo symbols (BRK.B -> BRK-B)."""
    return str(t).strip().upper().replace(".", "-")


# ── 1. build the union ticker set ──────────────────────────────────────────────
log("[1] building the union of current + historical constituents")
cur = pd.read_csv(os.path.join(RAW, "constituents/sp_500.csv"))
cur_syms = [norm(s) for s in cur[cur.columns[0]].astype(str) if str(s).strip() and str(s).lower() != "nan"]

ch = pd.read_csv(os.path.join(RAW, "constituents/sp_500_changes.csv"))
ch.columns = [str(c).strip() for c in ch.columns]
rem_col = [c for c in ch.columns if "Removed" in c and "Ticker" in c][0]
add_col = [c for c in ch.columns if "Added" in c and "Ticker" in c][0]


def clean(series):
    return [str(v).strip().upper() for v in series if str(v).strip() and str(v).lower() != "nan"]


removed = [norm(t) for t in clean(ch[rem_col])]
added = [norm(t) for t in clean(ch[add_col])]
current_set, removed_set, added_set = set(cur_syms), set(removed), set(added)
union = sorted(current_set | removed_set | added_set)
log(f"    current {len(current_set)} · removed {len(removed_set)} · added {len(added_set)} · UNION {len(union)}")

# ── 2. download in chunks, appending long-format rows ──────────────────────────
log(f"[2] downloading 10y daily for {len(union)} tickers in chunks of {CHUNK}")
if os.path.exists(LONG_CSV):
    os.remove(LONG_CSV)
coverage = []
t0 = time.time()
for i in range(0, len(union), CHUNK):
    chunk = union[i:i + CHUNK]
    try:
        data = yf.download(chunk, period="10y", interval="1d", auto_adjust=False,
                           threads=True, progress=False, group_by="column")
    except Exception:
        log(f"    chunk {i//CHUNK+1}: FAILED {traceback.format_exc().splitlines()[-1][:70]}")
        continue
    if not len(data):
        continue
    frames = []
    for tk in chunk:
        try:
            sub = data.xs(tk, axis=1, level=1) if isinstance(data.columns, pd.MultiIndex) else data
        except Exception:
            continue
        sub = sub.dropna(how="all")
        if not len(sub):
            coverage.append({"ticker": tk, "status": "dead", "rows": 0, "first": None, "last": None})
            continue
        sub = sub.reset_index().rename(columns={c: str(c).lower().replace(" ", "_") for c in sub.columns})
        sub.insert(0, "ticker", tk)
        frames.append(sub)
        cov = int(sub["close"].notna().sum()) if "close" in sub.columns else 0
        status = "priced" if cov >= 200 else ("partial" if cov > 0 else "dead")
        coverage.append({"ticker": tk, "status": status, "rows": int(len(sub)),
                         "first": str(sub.iloc[0, 1])[:10], "last": str(sub.iloc[-1, 1])[:10]})
    if frames:
        out = pd.concat(frames, ignore_index=True)
        out.to_csv(LONG_CSV, mode="a", header=not os.path.exists(LONG_CSV), index=False)
    done = min(i + CHUNK, len(union))
    log(f"    chunk {i//CHUNK+1}/{(len(union)+CHUNK-1)//CHUNK}: {done}/{len(union)} tickers · {time.time()-t0:.0f}s elapsed")

cov = pd.DataFrame(coverage)
cov["in_current_index"] = cov["ticker"].isin(current_set)
cov["was_removed"] = cov["ticker"].isin(removed_set)
cov["was_added"] = cov["ticker"].isin(added_set)
cov = cov.sort_values(["status", "ticker"])
cov.to_csv(COV_CSV, index=False)

log("\n[3] coverage summary")
log(cov["status"].value_counts().to_string())
for label, mask in [("current index members", cov["in_current_index"]),
                    ("REMOVED members", cov["was_removed"])]:
    sub = cov[mask]
    vc = sub["status"].value_counts().to_dict()
    log(f"    {label}: {len(sub)} tickers -> {vc}")

# ── 3. FMP dated delisting list (free tier) ────────────────────────────────────
log("\n[4] FMP delisted-companies (free tier)")
try:
    env = os.environ.get("DATA1002_ENV_FILE", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    fk = next((l.split("=", 1)[1].strip() for l in open(env) if l.startswith("FMP_API_KEY=")), None)
    r = requests.get("https://financialmodelingprep.com/stable/delisted-companies",
                     params={"page": 0, "limit": 500, "apikey": fk}, timeout=40)
    d = r.json()
    if isinstance(d, list) and d:
        del_df = pd.DataFrame(d)
        path = os.path.join(RAW, "constituents/us_delisted_fmp.csv")
        del_df.to_csv(path, index=False)
        dead = set(cov.loc[cov["status"].isin(["dead", "partial"]), "ticker"])
        hit = del_df[del_df["symbol"].astype(str).str.upper().isin(dead)]
        log(f"    list rows: {len(del_df)} · our unpriced tickers found in it: {len(hit)} {list(hit['symbol'])[:10]}")
        if len(hit):
            log(hit[["symbol", "companyName", "exchange", "delistedDate"]].head(10).to_string(index=False))
    else:
        log(f"    unexpected response: {str(d)[:120]}")
except Exception:
    log("    FAILED: " + traceback.format_exc().splitlines()[-1][:90])

log(f"\ndone in {time.time()-t0:.0f}s · {LONG_CSV}")
