#!/usr/bin/env python3
"""
Stage 1 — dataset upgrades that need no browser (2026-09-12).

A. Nasdaq-100 sector/industry enrichment  (Finnhub profile2, free tier)
B. ASX 200 weights                        (derived from the market-cap column)
C. Dow 30 weights                         (derived from prices; price-weighted)
D. Dow Jones full membership history      (Wikipedia, structure recon)

Outputs to data/derived/ (kept separate from data/raw/) and appends to the manifest.
"""
import os, io, json, time, datetime, warnings, traceback

warnings.filterwarnings("ignore")
import pandas as pd
import requests
import yfinance as yf

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
RAW = os.path.join(BASE, "raw")
DER = os.path.join(BASE, "derived")
os.makedirs(DER, exist_ok=True)
RETRIEVED = datetime.date.today().isoformat()
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"}

env = os.environ.get("DATA1002_ENV_FILE", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
FINNHUB = next((l.split("=", 1)[1].strip() for l in open(env) if l.startswith("FINNHUB_API_KEY=")), None)
new = []


def record(rel, kind, name, source, url, rows, cols, note):
    path = os.path.join(BASE, rel)
    new.append({"kind": kind, "name": name, "source": source, "source_url": url, "retrieved": RETRIEVED,
                "file": rel, "rows": int(rows), "cols": int(cols),
                "bytes": os.path.getsize(path) if os.path.exists(path) else 0, "note": note})


# ─────────────────────────────────────────────── A. Nasdaq-100 sectors
print("[A] Nasdaq-100 sector enrichment (Finnhub profile2)")
try:
    ndx = pd.read_csv(os.path.join(RAW, "constituents/nasdaq_100_nasdaq_api.csv"))
    sym_col = "symbol" if "symbol" in ndx.columns else ndx.columns[0]
    syms = [s for s in ndx[sym_col].astype(str).str.strip() if s and s.lower() != "nan"]
    print(f"    {len(syms)} symbols · pacing for the free tier")
    rows, fails = [], []
    for i, s in enumerate(syms, 1):
        try:
            r = requests.get("https://finnhub.io/api/v1/stock/profile2",
                             params={"symbol": s, "token": FINNHUB}, timeout=15)
            d = r.json() if r.status_code == 200 else {}
            if isinstance(d, dict) and d:
                rows.append({"symbol": s, "name": d.get("name"), "industry": d.get("finnhubIndustry"),
                             "exchange": d.get("exchange"), "currency": d.get("currency"),
                             "market_cap_musd": d.get("marketCapitalization"),
                             "share_outstanding_musd": d.get("shareOutstanding"),
                             "ipo": d.get("ipo"), "country": d.get("country"), "logo": d.get("logo")})
            else:
                fails.append((s, r.status_code))
        except Exception:
            fails.append((s, "err"))
        time.sleep(1.05)
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(DER, "nasdaq_100_sectors_finnhub.csv"), index=False)
    print(f"    saved {out.shape} · {len(fails)} failures {fails[:5]}")
    record("derived/nasdaq_100_sectors_finnhub.csv", "derived", "Nasdaq-100 sectors/industry (Finnhub)",
           "Finnhub profile2 (free tier)", "https://finnhub.io/docs/api/company-profile2", out.shape[0], out.shape[1],
           "sector/industry enrichment; 1 call per constituent")
except Exception:
    print("    FAILED:", traceback.format_exc().splitlines()[-1][:90])

# ─────────────────────────────────────────────── B. ASX 200 weights
print("[B] ASX 200 weights (derived)")
try:
    asx = pd.read_csv(os.path.join(RAW, "constituents/asx_200.csv"))
    capcol = [c for c in asx.columns if "apitalis" in str(c)][0]
    asx["market_cap_aud"] = pd.to_numeric(asx[capcol], errors="coerce")
    total = asx["market_cap_aud"].sum()
    asx["weight_pct_full_cap"] = (asx["market_cap_aud"] / total * 100).round(4)
    asx["rank"] = asx["market_cap_aud"].rank(ascending=False).astype("Int64")
    out = asx.sort_values("rank")
    out.to_csv(os.path.join(DER, "asx_200_weights_full_cap.csv"), index=False)
    print(f"    saved {out.shape} · total A${total/1e9:,.1f}bn · top5 {out.head(5)['weight_pct_full_cap'].sum():.1f}% "
          f"· top10 {out.head(10)['weight_pct_full_cap'].sum():.1f}%")
    record("derived/asx_200_weights_full_cap.csv", "derived", "ASX 200 weights (derived, full cap)",
           "derived from Wikipedia market-capitalisation column", "https://en.wikipedia.org/wiki/S%26P/ASX_200",
           out.shape[0], out.shape[1],
           "weights are FULL market cap, not float-adjusted; reconcile against published index weights")
except Exception:
    print("    FAILED:", traceback.format_exc().splitlines()[-1][:90])

# ─────────────────────────────────────────────── C. Dow 30 weights
print("[C] Dow 30 weights (derived from prices)")
try:
    dow = pd.read_csv(os.path.join(RAW, "constituents/dow_30_stockanalysis.csv"))
    sc = "Symbol" if "Symbol" in dow.columns else dow.columns[1]
    syms = [s for s in dow[sc].astype(str).str.strip() if s and s.lower() != "nan"]
    px = {}
    for s in syms:
        h = yf.Ticker(s).history(period="5d", auto_adjust=False)
        if len(h):
            px[s] = float(h["Close"].iloc[-1])
    tot = sum(px.values())
    dw = pd.DataFrame([{"symbol": s, "last_close": p, "price_weight_pct": round(p / tot * 100, 4)} for s, p in px.items()])
    dw = dw.sort_values("price_weight_pct", ascending=False)
    dw.to_csv(os.path.join(DER, "dow_30_weights_price_weighted.csv"), index=False)
    print(f"    saved {dw.shape} · heaviest {dw.iloc[0]['symbol']} {dw.iloc[0]['price_weight_pct']:.1f}% "
          f"· lightest {dw.iloc[-1]['symbol']} {dw.iloc[-1]['price_weight_pct']:.1f}%")
    record("derived/dow_30_weights_price_weighted.csv", "derived", "Dow 30 weights (derived, price-weighted)",
           "derived from live prices (yfinance)", "https://finance.yahoo.com/", dw.shape[0], dw.shape[1],
           "price weights computed as price / sum(prices); divisor cancels in the ratio")
except Exception:
    print("    FAILED:", traceback.format_exc().splitlines()[-1][:90])

# ─────────────────────────────────────────────── D. Dow history recon
print("[D] Dow Jones historical components — structure recon")
try:
    url = "https://en.wikipedia.org/wiki/Historical_components_of_the_Dow_Jones_Industrial_Average"
    r = requests.get(url, headers=UA, timeout=45)
    with open(os.path.join(RAW, "source_snapshots/dow_history_wikipedia.html"), "w", encoding="utf-8") as fh:
        fh.write(r.text)
    tabs = pd.read_html(io.StringIO(r.text))
    keep = [(t.shape, [str(c)[:22] for c in list(t.columns)[:5]]) for t in tabs if 5 <= t.shape[0] <= 200]
    print(f"    {len(tabs)} tables · {len(keep)} in range")
    for shape, cols in keep[:10]:
        print(f"      {shape} cols={cols}")
except Exception:
    print("    FAILED:", traceback.format_exc().splitlines()[-1][:90])

# ─────────────────────────────────────────────── manifest
man_path = os.path.join(RAW, "MANIFEST.json")
with open(man_path, encoding="utf-8") as fh:
    man = json.load(fh)
names = {e["name"] for e in new}
man["files"] = [e for e in man["files"] if e["name"] not in names] + new
man["upgrade_pass"] = RETRIEVED
with open(man_path, "w", encoding="utf-8") as fh:
    json.dump(man, fh, indent=2)
print(f"\nmanifest now {len(man['files'])} entries")
