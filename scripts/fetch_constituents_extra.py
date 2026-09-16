#!/usr/bin/env python3
"""
Stage 1 — extra constituent acquisition (found via API research, 2026-09-12).

Routes identified as free and scriptable, no API key required:
  - stockanalysis.com : Dow 30 list, Nasdaq-100 list
  - api.nasdaq.com    : Nasdaq-100 (official, JSON)
  - ja.wikipedia       : Dow 30 components + Dow membership changes,
                         Nikkei 225 membership changes

Nikkei 225 *current components* remain unavailable without a browser or a paid
package; only its membership-change history is free.

Appends to data/raw/MANIFEST.json.
"""
import os, io, json, datetime, warnings, traceback

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
new = []


def flatten(df):
    df = df.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [" ".join(str(x) for x in tup).strip() for tup in df.columns]
    else:
        df.columns = [str(c).strip() for c in df.columns]
    return df


def save_csv(df, rel, name, source, url, note=""):
    path = os.path.join(BASE, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    print(f"  saved {rel}  shape={df.shape}")
    new.append({"kind": "constituents", "name": name, "source": source, "source_url": url,
                "retrieved": RETRIEVED, "file": rel, "rows": int(df.shape[0]), "cols": int(df.shape[1]),
                "bytes": os.path.getsize(path), "note": note})


# ── 1. stockanalysis.com lists (US indices)
print("[1] stockanalysis.com")
for slug, name, rel in [
    ("dow-jones-stocks", "Dow Jones 30 (stockanalysis)", "constituents/dow_30_stockanalysis.csv"),
    ("nasdaq-100-stocks", "Nasdaq-100 (stockanalysis)", "constituents/nasdaq_100_stockanalysis.csv"),
]:
    url = f"https://stockanalysis.com/list/{slug}/"
    try:
        r = requests.get(url, headers=UA, timeout=35)
        snap = os.path.join(BASE, "source_snapshots", f"{slug}_stockanalysis.html")
        with open(snap, "w", encoding="utf-8") as fh:
            fh.write(r.text)
        tab = max(pd.read_html(io.StringIO(r.text)), key=lambda t: t.shape[0])
        save_csv(flatten(tab), rel, name, "stockanalysis.com", url, note="free, no key; HTML snapshot saved")
    except Exception:
        print(f"  {slug}: FAILED {traceback.format_exc().splitlines()[-1][:80]}")

# ── 2. api.nasdaq.com (official JSON)
print("[2] api.nasdaq.com")
try:
    url = "https://api.nasdaq.com/api/quote/list-type/nasdaq100"
    r = requests.get(url, headers=UA, timeout=30)
    path = os.path.join(BASE, "constituents", "nasdaq_100_nasdaq_api.json")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(r.text)
    rows = r.json()["data"]["data"]["rows"]
    df = pd.DataFrame(rows)
    csv_path = os.path.join(BASE, "constituents", "nasdaq_100_nasdaq_api.csv")
    df.to_csv(csv_path, index=False)
    print(f"  saved nasdaq_100_nasdaq_api.{{json,csv}}  rows={len(df)}")
    new.append({"kind": "constituents", "name": "Nasdaq-100 (api.nasdaq.com)", "source": "Nasdaq (official API)",
                "source_url": url, "retrieved": RETRIEVED, "file": "constituents/nasdaq_100_nasdaq_api.csv",
                "rows": len(df), "cols": df.shape[1], "bytes": os.path.getsize(csv_path),
                "note": "free, no API key, User-Agent header required; raw JSON kept alongside"})
except Exception:
    print(f"  FAILED {traceback.format_exc().splitlines()[-1][:80]}")

# ── 3. ja.wikipedia (Dow components + changes; Nikkei changes)
print("[3] ja.wikipedia")
JA_DOW = "https://ja.wikipedia.org/wiki/%E3%83%80%E3%82%A6%E5%B9%B3%E5%9D%87%E6%A0%AA%E4%BE%A1"
JA_NIKKEI = "https://ja.wikipedia.org/wiki/%E6%97%A5%E7%B5%8C%E5%B9%B3%E5%9D%87%E6%A0%AA%E4%BE%A1"


def fetch_tables(url, key):
    r = requests.get(url, headers=UA, timeout=40)
    os.makedirs(os.path.join(BASE, "source_snapshots"), exist_ok=True)
    with open(os.path.join(BASE, "source_snapshots", f"{key}_ja_wikipedia.html"), "w", encoding="utf-8") as fh:
        fh.write(r.text)
    return [flatten(t) for t in pd.read_html(io.StringIO(r.text))]


def pick(tables, needles, label):
    for t in tables:
        cols = " ".join(str(c) for c in t.columns)
        if any(n in cols for n in needles) and t.shape[0] >= 15:
            return t, label
    return None, None


for key, url, needles, label, name in [
    ("dow_30_ja", JA_DOW, ["シンボル", "企業名"], "dow components", "Dow Jones 30 (ja.wikipedia)"),
    ("dow_30_changes_ja", JA_DOW, ["入替"], "dow changes", "Dow Jones 30 membership changes (ja.wikipedia)"),
    ("nikkei_225_changes_ja", JA_NIKKEI, ["除外", "採用"], "nikkei changes", "Nikkei 225 membership changes (ja.wikipedia)"),
]:
    try:
        tab, _ = pick(fetch_tables(url, key), needles, label)
        if tab is None:
            print(f"  {key}: no table matched {needles}")
            continue
        save_csv(tab, f"constituents/{key}.csv", name, "ja.wikipedia (CC BY-SA)", url,
                 note=f"column-matched on {needles}; HTML snapshot saved")
    except Exception:
        print(f"  {key}: FAILED {traceback.format_exc().splitlines()[-1][:80]}")

# ── 4. manifest
man_path = os.path.join(BASE, "MANIFEST.json")
with open(man_path, encoding="utf-8") as fh:
    man = json.load(fh)
names = {e["name"] for e in new}
man["files"] = [e for e in man["files"] if e["name"] not in names] + new
man["extra_pass"] = RETRIEVED
with open(man_path, "w", encoding="utf-8") as fh:
    json.dump(man, fh, indent=2)
print(f"\nmanifest now {len(man['files'])} entries")
