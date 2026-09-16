#!/usr/bin/env python3
"""Canonical S&P 500 membership-year reconstruction, 2016-09-12 to 2026-09-11.

Replaces two earlier constructions that disagreed with each other by more than twelve per cent
(see scripts/README.md). Grain is one row per membership interval, so a company that left and later
rejoined is counted correctly. Validation: the reconstruction's implied mean index size is reported
alongside the total and must match the index's actual size.

Inputs:  data/raw/constituents/sp_500.csv, sp_500_changes.csv; data/raw/prices/us_panel_coverage.csv
Output:  printed summary (the interval-level and summary tables are written by the caller if needed)
Run:     python3 scripts/build_membership_canonical.py
"""
#!/usr/bin/env python3
"""Canonical rebuild: S&P 500 membership-years, 2016-09-12 .. 2026-09-11."""
import os, re
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RAW   = os.path.join(ROOT, "data", "raw")
WS    = pd.Timestamp("2016-09-12")     # window start = panel min(first)
WE    = pd.Timestamp("2026-09-11")     # window end   = panel max(last)
DIV   = 365.25                          # days -> years
TICK  = re.compile(r"^[A-Z][A-Z0-9-]{0,7}$")            # 1..8 chars, no pipe/space/junk
RECYCLE_EXCLUDE = {"Q", "SOLS", "PCLN", "POM", "CAM"}   # belt-and-braces only (see note)

def tick(txt):
    out = []
    for part in str(txt).replace("/", ",").replace(" and ", ",").split(","):
        p = part.strip().upper().replace(".", "-")
        if TICK.match(p):                       # GUARD 1 — rejects "ALLE |", "nan", ""
            out.append(p)
    return out

cur = pd.read_csv(os.path.join(RAW, "constituents/sp_500.csv"))
current = {t for s in cur[cur.columns[0]] for t in tick(s)}

ch = pd.read_csv(os.path.join(RAW, "constituents/sp_500_changes.csv"))
ch.columns = [c.strip() for c in ch.columns]
dcol = [c for c in ch.columns if "Effective" in c][0]
acol = [c for c in ch.columns if "Added"   in c and "Ticker" in c][0]
rcol = [c for c in ch.columns if "Removed" in c and "Ticker" in c][0]
ch["eff"] = pd.to_datetime(ch[dcol], errors="coerce")
ch = ch.dropna(subset=["eff"]).sort_values("eff")

bounds = {}
for _, r in ch.iterrows():
    d = str(r["eff"])[:10]
    for t in tick(r[rcol]): bounds.setdefault(t, []).append((d, "leave"))
    for t in tick(r[acol]): bounds.setdefault(t, []).append((d, "join"))

rows = []
for t in sorted(set(bounds) | current):
    bs = sorted(bounds.get(t, []))
    open_start = "pre-window" if (not bs or bs[0][1] == "leave") else None   # GUARD 2 — sentinel
    seg = []
    for d, kind in bs:
        if kind == "leave":
            seg.append((open_start, d)); open_start = None
        elif open_start is None:
            open_start = d
    if open_start is not None and (t in current or not bs):
        seg.append((open_start, None))
    for s, e in seg:
        rows.append({"ticker": t, "start": s, "end": e})

iv = pd.DataFrame(rows)
iv["s"] = pd.to_datetime(iv["start"], errors="coerce").fillna(WS).clip(lower=WS)  # GUARD 3 — clip
iv["e"] = pd.to_datetime(iv["end"],   errors="coerce").fillna(WE).clip(upper=WE)
iv = iv[iv["e"] > iv["s"]].copy()                                                 # GUARD 4 — drop empty
iv["years"] = (iv["e"] - iv["s"]).dt.days / DIV

cov = pd.read_csv(os.path.join(RAW, "prices/us_panel_coverage.csv"))
pf = pd.to_datetime(cov.set_index("ticker")["first"], errors="coerce")
pl = pd.to_datetime(cov.set_index("ticker")["last"],  errors="coerce")
iv["pfirst"] = iv["ticker"].map(pf); iv["plast"] = iv["ticker"].map(pl)
lo = pd.concat([iv["s"], iv["pfirst"]], axis=1).max(axis=1)     # GUARD 5 — interval, not span
hi = pd.concat([iv["e"], iv["plast"]],  axis=1).min(axis=1)
iv["covered_years"] = ((hi - lo).dt.days / DIV).clip(lower=0)
iv.loc[iv["pfirst"].isna() | iv["plast"].isna(), "covered_years"] = 0.0   # GUARD 5b — NaT ⇒ 0
iv["coverage_frac"] = iv["covered_years"] / iv["years"]
iv["reuse_flag"] = iv["ticker"].isin(RECYCLE_EXCLUDE)
iv["cov_class"] = pd.cut(iv["coverage_frac"], [-0.01, 1e-9, 0.999, 1.01],
                         labels=["none", "partial", "full"])

print(iv.groupby("cov_class", observed=True)[["years","covered_years"]].agg(["count","sum"]).round(1))
print(f"TOTAL membership-years = {iv['years'].sum():.1f}  "
      f"priceable = {iv['covered_years'].sum():.1f} "
      f"({100*iv['covered_years'].sum()/iv['years'].sum():.1f}%)")
grid = pd.date_range(WS, WE, freq="MS")
n = [int(((iv["s"] <= g) & (iv["e"] > g)).sum()) for g in grid]
print(f"VALIDATION mean index size = {sum(n)/len(n):.1f} (min {min(n)} max {max(n)})  [expected ~503]")
