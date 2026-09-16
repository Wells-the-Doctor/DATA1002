#!/usr/bin/env python3
"""
Stage 1 — membership intervals, v2: multiple intervals per ticker + integrity checks.

v1 recorded a single join/leave pair per ticker, which mis-models any company that left
and later rejoined (audit example: MCK carries a 1994 exit but sits in the index today).

v2 walks the 407 change events backwards from today's membership, recording every
boundary, then rebuilds alternating intervals per ticker — and reports the conflicts it
cannot resolve, because those are findings about the source, not bugs to hide.

Outputs:
  constituents/sp500_membership_intervals.csv   (rewritten, one row per interval)
  derived/sp500_membership_integrity.md         (conflict register + counts)
"""
import os, warnings, datetime

warnings.filterwarnings("ignore")
import pandas as pd

RAW = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw")
DER = os.path.join(RAW, "..", "derived")
os.makedirs(DER, exist_ok=True)
WINDOW_START, WINDOW_END = "2016-09-12", "2026-09-11"


def log(m):
    print(m, flush=True)


def split_tickers(cell):
    out = []
    for part in str(cell).replace("/", ",").replace(" and ", ",").split(","):
        p = part.strip().upper()
        if p and p.lower() != "nan" and 1 < len(p) <= 8:
            out.append(p.replace(".", "-"))
    return out


cur = pd.read_csv(os.path.join(RAW, "constituents/sp_500.csv"))
current = {str(s).strip().upper().replace(".", "-") for s in cur[cur.columns[0]]
           if str(s).strip() and str(s).lower() != "nan"}

ch = pd.read_csv(os.path.join(RAW, "constituents/sp_500_changes.csv"))
ch.columns = [c.strip() for c in ch.columns]
dcol = [c for c in ch.columns if "Effective" in c][0]
acol = [c for c in ch.columns if "Added" in c and "Ticker" in c][0]
rcol = [c for c in ch.columns if "Removed" in c and "Ticker" in c][0]
ch["eff"] = pd.to_datetime(ch[dcol], errors="coerce")
ch = ch.dropna(subset=["eff"]).sort_values("eff", ascending=False)

boundaries = {}
for _, row in ch.iterrows():
    d = str(row["eff"])[:10]
    for t in split_tickers(row[rcol]):
        boundaries.setdefault(t, []).append((d, "leave"))
    for t in split_tickers(row[acol]):
        boundaries.setdefault(t, []).append((d, "join"))

rows, multi, reentry_gaps, never_joined = [], [], [], []
for t in sorted(set(boundaries) | current):
    bs = sorted(boundaries.get(t, []))
    intervals, open_start = [], "pre-window"
    for d, kind in bs:
        if kind == "leave":
            intervals.append((open_start, d))
            open_start = None
        else:  # join
            if open_start is None:
                open_start = d
    if open_start is not None and (t in current or not bs):
        intervals.append((open_start, None))
    # integrity: in the index today but the last recorded boundary was a departure
    if t in current and bs and bs[-1][1] == "leave":
        reentry_gaps.append(t)
    if not bs and t in current:
        never_joined.append(t)
    if len(intervals) > 1:
        multi.append(t)
    for s, e in intervals:
        rows.append({"ticker": t, "start": s, "end": e, "in_index_today": t in current})

out = pd.DataFrame(rows).sort_values(["ticker", "start"])
out.to_csv(os.path.join(RAW, "constituents/sp500_membership_intervals.csv"), index=False)
log(f"intervals written: {len(out)} rows for {out.ticker.nunique()} tickers")
log(f"  tickers with >1 interval (left and rejoined): {len(multi)} {multi[:12]}")
log(f"  currently a member but last recorded event was a departure (=source gap): {len(reentry_gaps)} {reentry_gaps[:12]}")
log(f"  current members never mentioned in the change table at all: {len(never_joined)}")

# coverage by membership-years, now honouring multiple intervals
cov = pd.read_csv(os.path.join(RAW, "prices/us_panel_coverage.csv"))
status = dict(zip(cov["ticker"], cov["status"]))
out["s"] = pd.to_datetime(out["start"], errors="coerce").fillna(pd.Timestamp(WINDOW_START)).clip(lower=pd.Timestamp(WINDOW_START))
out["e"] = pd.to_datetime(out["end"], errors="coerce").fillna(pd.Timestamp(WINDOW_END)).clip(upper=pd.Timestamp(WINDOW_END))
out = out[out["e"] > out["s"]].copy()
out["years"] = (out["e"] - out["s"]).dt.days / 365.25
out["status"] = out["ticker"].map(status).fillna("not_requested")
tot = out["years"].sum()
by = out.groupby("status")["years"].sum().sort_values(ascending=False)
log("\nmembership-years in the 10y window, by price status:")
for k, v in by.items():
    log(f"    {k:14s} {v:8.0f}  ({v/tot*100:5.1f}%)")
log(f"    TOTAL          {tot:8.0f}")

with open(os.path.join(DER, "sp500_membership_integrity.md"), "w") as fh:
    fh.write("# S&P 500 membership reconstruction — integrity register\n\n")
    fh.write(f"Built {datetime.date.today()} from the 407 change events (Wikipedia), walked backwards from today's 503 members.\n\n")
    fh.write(f"- Intervals: **{len(out)}** across **{out.ticker.nunique()}** tickers\n")
    fh.write(f"- Tickers that left and rejoined: **{len(multi)}** — {', '.join(multi[:20])}\n")
    fh.write(f"- **Source gaps** — currently a member but the last recorded event is a departure: **{len(reentry_gaps)}** — {', '.join(reentry_gaps[:20])}\n")
    fh.write(f"- Current members never mentioned in the change table: **{len(never_joined)}**\n\n")
    fh.write("## Membership-years by price status (10y window)\n\n")
    for k, v in by.items():
        fh.write(f"- {k}: {v:,.0f} years ({v/tot*100:.1f}%)\n")
    fh.write(f"\nTotal: {tot:,.0f} membership-years.\n")
log("\nwritten: derived/sp500_membership_integrity.md")
