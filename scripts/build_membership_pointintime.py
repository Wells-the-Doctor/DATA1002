#!/usr/bin/env python3
"""
Stage 1 — point-in-time index membership, and what share of it we can actually price.

(A) Full FMP delisted-companies list (paginated) — dated exit evidence.
(B) Rebuild S&P 500 membership backwards from today's 503 using the 407 change events,
    producing a per-ticker membership interval table (join date / leave date).
(C) Measure survivorship coverage: how many membership-years are priceable, using the
    survivorship-safe panel built in the previous step.

Outputs (data/raw/):
  constituents/us_delisted_fmp.csv        (rewritten, full list)
  constituents/sp500_membership_intervals.csv
  derived/sp500_membership_coverage.csv
"""
import os, json, time, datetime, warnings, traceback

warnings.filterwarnings("ignore")
import pandas as pd
import requests

RAW = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw")
DER = os.path.join(RAW, "..", "derived")
os.makedirs(DER, exist_ok=True)
RETRIEVED = datetime.date.today().isoformat()


def log(m):
    print(m, flush=True)


# ── (A) FMP delisted list, paginated ───────────────────────────────────────────
log("[A] FMP delisted-companies — paginating")
env = os.environ.get("DATA1002_ENV_FILE", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
fk = next((l.split("=", 1)[1].strip() for l in open(env) if l.startswith("FMP_API_KEY=")), None)
rows, page = [], 0
while page < 25:
    try:
        r = requests.get("https://financialmodelingprep.com/stable/delisted-companies",
                         params={"page": page, "limit": 100, "apikey": fk}, timeout=30)
        d = r.json()
    except Exception:
        log("    page %d failed: %s" % (page, traceback.format_exc().splitlines()[-1][:60]))
        break
    if not isinstance(d, list) or not d:
        break
    rows.extend(d)
    page += 1
if rows:
    del_df = pd.DataFrame(rows).drop_duplicates(subset=["symbol"])
    del_df.to_csv(os.path.join(RAW, "constituents/us_delisted_fmp.csv"), index=False)
    dates = pd.to_datetime(del_df["delistedDate"], errors="coerce")
    log(f"    pages {page} · rows {len(del_df)} · delisting dates {str(dates.min())[:10]} -> {str(dates.max())[:10]}")
else:
    del_df = pd.DataFrame()
    log("    no rows returned")

# ── (B) membership intervals, reconstructed backwards ──────────────────────────
log("\n[B] rebuilding membership intervals from the 407 change events")


def split_tickers(cell):
    s = str(cell)
    out = []
    for part in s.replace("/", ",").replace(" and ", ",").split(","):
        p = part.strip().upper()
        if p and p.lower() != "nan" and len(p) <= 8:
            out.append(p.replace(".", "-"))
    return out


cur = pd.read_csv(os.path.join(RAW, "constituents/sp_500.csv"))
current = {str(s).strip().upper().replace(".", "-") for s in cur[cur.columns[0]] if str(s).strip() and str(s).lower() != "nan"}

ch = pd.read_csv(os.path.join(RAW, "constituents/sp_500_changes.csv"))
ch.columns = [c.strip() for c in ch.columns]
date_col = [c for c in ch.columns if "Effective" in c][0]
add_col = [c for c in ch.columns if "Added" in c and "Ticker" in c][0]
rem_col = [c for c in ch.columns if "Removed" in c and "Ticker" in c][0]
ch["eff"] = pd.to_datetime(ch[date_col], errors="coerce")
ch = ch.dropna(subset=["eff"]).sort_values("eff", ascending=False)
log(f"    events {len(ch)} · window {str(ch['eff'].min())[:10]} -> {str(ch['eff'].max())[:10]}")

join, leave = {}, {}
for _, row in ch.iterrows():
    d = str(row["eff"])[:10]
    for t in split_tickers(row[add_col]):
        join.setdefault(t, d)          # walking backwards: first add we meet is the join
    for t in split_tickers(row[rem_col]):
        leave.setdefault(t, d)         # ditto for the leave

tickers = sorted(set(join) | set(leave) | current)
recs = []
for t in tickers:
    j = join.get(t, "pre-window")
    l = leave.get(t, None)
    recs.append({"ticker": t, "join_date": j, "leave_date": l,
                 "in_index_today": t in current,
                 "join_known": j != "pre-window"})
inter = pd.DataFrame(recs).sort_values(["leave_date", "ticker"], na_position="last")
inter.to_csv(os.path.join(RAW, "constituents/sp500_membership_intervals.csv"), index=False)
log(f"    intervals {len(inter)} · currently in index {int(inter.in_index_today.sum())} · exits recorded {int(inter.leave_date.notna().sum())} · joins unknown {int((~inter.join_known).sum())}")

# ── (C) survivorship coverage: membership-years vs priceable ───────────────────
log("\n[C] membership coverage — what share of index history is priceable")
cov = pd.read_csv(os.path.join(RAW, "prices/us_panel_coverage.csv"))
status = dict(zip(cov["ticker"], cov["status"]))
WINDOW_START = pd.Timestamp("2016-09-12")
WINDOW_END = pd.Timestamp("2026-09-11")
inter["start"] = pd.to_datetime(inter["join_date"], errors="coerce").fillna(WINDOW_START)
inter["end"] = pd.to_datetime(inter["leave_date"], errors="coerce").fillna(WINDOW_END)
inter["start"] = inter["start"].clip(lower=WINDOW_START)
inter["end"] = inter["end"].clip(upper=WINDOW_END)
inter["years_in_window"] = ((inter["end"] - inter["start"]).dt.days / 365.25).clip(lower=0)
inter["price_status"] = inter["ticker"].map(status).fillna("not_requested")
inter["priceable_years"] = inter.apply(lambda r: r["years_in_window"] if r["price_status"] == "priced" else 0, axis=1)
tot = inter["years_in_window"].sum()
ok = inter["priceable_years"].sum()
part = inter.loc[inter["price_status"] == "partial", "years_in_window"].sum()
log(f"    membership-years in window : {tot:,.0f}")
log(f"    priceable (full series)    : {ok:,.0f}  ({ok/tot*100:.1f}%)")
log(f"    partial only               : {part:,.0f}  ({part/tot*100:.1f}%)")
log(f"    no data at all             : {tot-ok-part:,.0f}  ({(tot-ok-part)/tot*100:.1f}%)")
inter.groupby("price_status")["years_in_window"].agg(["count", "sum"]).round(1).to_csv(
    os.path.join(DER, "sp500_membership_coverage.csv"))
log(f"    written: derived/sp500_membership_coverage.csv")

# (A) match our unpriced names against the FMP exit list
if len(del_df):
    dead = set(inter.loc[inter["price_status"].isin(["dead", "partial", "not_requested"]), "ticker"])
    hit = del_df[del_df["symbol"].astype(str).str.upper().isin(dead)]
    log(f"\n    FMP exit list: {len(del_df)} companies · matched to our unpriced members: {len(hit)}")
    if len(hit):
        log(hit[["symbol", "companyName", "delistedDate"]].head(12).to_string(index=False))
