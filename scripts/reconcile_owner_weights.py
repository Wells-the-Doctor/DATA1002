#!/usr/bin/env python3
"""Reconciliation of the owner-published weights against the held lists.

Answers, with counts:
  1.2  Dow 30     : does the DIA basket name the same 30 companies we hold, and does
                    our price-weighted derivation agree with the issuer's weights?
  1.3  S&P 500    : does the SPY basket reconcile with our 503-name list? (one name out)
  1.4  ASX 200    : does the A200 basket reconcile with our (stale) list, and how far is
                    our full-cap approximation from the issuer's float-adjusted weights?

Writes derived/owner_weights_reconciliation.md
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

STAGE1 = Path(__file__).resolve().parent.parent
RAW = STAGE1 / "data" / "raw" / "constituents"
DER = STAGE1 / "data" / "derived"
OUT = DER / "owner_weights_reconciliation.md"


def rows(p: Path) -> list[dict]:
    with p.open(encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return float("nan")
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    dx = sum((a - mx) ** 2 for a in xs) ** 0.5
    dy = sum((b - my) ** 2 for b in ys) ** 0.5
    return num / (dx * dy) if dx and dy else float("nan")


def main() -> int:
    L: list[str] = []
    add = L.append

    # ---------------- 1.2 Dow 30 ----------------
    dia = rows(DER / "dow_30_weights_dia_owner_weights.csv")
    ours_dow = rows(RAW / "dow_30_stockanalysis.csv")
    ours_w = {r["symbol"]: float(r["price_weight_pct"])
              for r in rows(DER / "dow_30_weights_price_weighted.csv")}

    dia_t = {r["ticker"] for r in dia}
    our_t = {r["Symbol"] for r in ours_dow}
    only_dia, only_ours = sorted(dia_t - our_t), sorted(our_t - dia_t)

    pairs = [(r["ticker"], float(r["weight_pct"])) for r in dia if r["ticker"] in ours_w]
    corr = pearson([p[1] for p in pairs], [ours_w[p[0]] for p in pairs])
    worst = max(pairs, key=lambda p: abs(p[1] - ours_w[p[0]]), default=("", 0.0))

    add("### WS1.2 — Dow 30 (DIA basket) vs our holdings & derivation\n")
    add(f"- Names: DIA **{len(dia_t)}** · ours **{len(our_t)}** · "
        f"set-equal: **{dia_t == our_t}**")
    if only_dia or only_ours:
        add(f"- Divergence: only-in-DIA {only_dia or '—'} · only-ours {only_ours or '—'}")
    add(f"- Issuer weight sum: **{sum(float(r['weight_pct']) for r in dia):.3f}%**")
    add(f"- Our price-weighted derivation vs issuer weights: **r = {corr:.4f}** over "
        f"{len(pairs)} names; largest gap **{abs(worst[1] - ours_w[worst[0]]):.3f}pp** "
        f"({worst[0]}: issuer {worst[1]:.3f} vs ours {ours_w[worst[0]]:.3f})")
    add("- Top 5 (issuer): " + " · ".join(
        f"{r['ticker']} {float(r['weight_pct']):.2f}%" for r in
        sorted(dia, key=lambda r: -float(r["weight_pct"]))[:5]))
    add("")

    # ---------------- 1.3 S&P 500 ----------------
    spy = rows(DER / "sp500_weights_spy_owner_weights.csv")
    ours_sp = rows(RAW / "sp_500.csv")

    # The issuer file carries two non-constituent lines, both of which break a naive
    # ticker join. Classify them rather than counting them as "extra names".
    artifacts = []
    real = []
    for r in spy:
        tk = r["ticker"]
        nm = r["name"].upper()
        if tk.startswith("2602335D") or "CONTRA" in nm:
            artifacts.append((tk, r["name"], r["identifier"], "contingent value right"))
        elif not tk.isalpha() and tk not in {r["Symbol"] for r in ours_sp}:
            artifacts.append((tk, r["name"], r["identifier"], "successor entity (corporate action)"))
        else:
            real.append(r)

    spy_t = {r["ticker"] for r in real}
    our_sp_t = {r["Symbol"] for r in ours_sp}
    add("### WS1.3 — S&P 500 (SPY basket) vs our 503-name list\n")
    add(f"- Issuer lines: **{len(spy)}** — of which **{len(real)}** carry a ticker and "
        f"**{len(artifacts)}** are corporate-action lines (not constituents):")
    for tk, nm, cid, kind in artifacts:
        add(f"    - `{tk}` = *{nm.strip()}* ({cid}) — {kind}")
    add(f"- Constituent comparison: SPY **{len(spy_t)}** vs ours **{len(our_sp_t)}**")
    add(f"- only-in-SPY: **{sorted(spy_t - our_sp_t)}** · only-ours: **{sorted(our_sp_t - spy_t)}**")
    add(f"- Issuer weight sum (all lines): **{sum(float(r['weight_pct']) for r in spy):.3f}%**")
    add("- **Reading:** the two 'extras' are one CVR and the ONEOK successor entity "
        "`FALCON TOPCO INC` (CUSIP 30609A109, the top company created by the ONEOK merger "
        "reported in ONEOK's 8-K of 2026-08-28). It is the *same holding* our list holds as "
        "`OKE`; the divergence is a **naming artifact, not a composition gap**. A ticker-keyed "
        "join would have silently dropped ONEOK (see WS10.1).")
    add(f"- CUSIP coverage: **{sum(1 for r in spy if r['identifier'].strip())}/{len(spy)}** lines carry an identifier")
    add("- Top 5 (issuer): " + " · ".join(
        f"{r['ticker']} {float(r['weight_pct']):.2f}%" for r in
        sorted(spy, key=lambda r: -float(r["weight_pct"]))[:5]))
    add("")

    # ---------------- 1.4 ASX 200 ----------------
    a200 = rows(DER / "asx200_weights_a200_owner_weights.csv")
    ours_asx = rows(RAW / "asx_200.csv")
    approx = {r["Code"]: float(r["weight_pct_full_cap"])
              for r in rows(DER / "asx_200_weights_full_cap.csv")}

    # Separate the fund's cash line from its equity lines before comparing composition.
    cash = [r for r in a200 if r["asset_class"].strip() != "Equities"]
    a200_eq = [r for r in a200 if r["asset_class"].strip() == "Equities"]
    a200_w = {r["ticker"]: float(r["weight_pct"]) for r in a200_eq}

    a_t, o_t = set(a200_w), set(approx)
    add("### WS1.4 — ASX 200 (A200 basket) vs our held list & full-cap approximation\n")
    add(f"- Issuer lines: **{len(a200)}** — **{len(a200_eq)}** equities + "
        f"**{len(cash)}** cash ({', '.join(r['ticker'] + ' ' + r['weight_pct'] + '%' for r in cash)})")
    add(f"- Equity comparison: A200 **{len(a_t)}** vs ours **{len(o_t)}** · "
        f"set-equal: **{a_t == o_t}** · common **{len(a_t & o_t)}**")
    add(f"- Divergence — in A200 not ours (**{len(a_t - o_t)}**): **{sorted(a_t - o_t)}**")
    add(f"- Divergence — in ours not A200 (**{len(o_t - a_t)}**): **{sorted(o_t - a_t)}**")
    add(f"- Weight held by the A200-only names: **{sum(a200_w[c] for c in a_t - o_t):.2f}%**")
    add(f"- Issuer equity weight sum: **{sum(a200_w.values()):.3f}%** (cash excluded)")

    common = sorted(a_t & o_t)
    a_v = [a200_w[c] for c in common]
    o_v = [approx[c] for c in common]
    add(f"- Our full-cap approximation vs issuer float-adj weights (n={len(common)}): "
        f"**r = {pearson(a_v, o_v):.4f}**")
    add(f"- Mean absolute weight gap: **{sum(abs(a - o) for a, o in zip(a_v, o_v)) / len(common):.3f}pp**")

    add("\n**Top 10 — issuer vs our approximation**\n")
    add("| # | A200 code | issuer % | ours % | gap pp |")
    add("|--:|:--|--:|--:|--:|")
    top10 = sorted(a200_eq, key=lambda r: -float(r["weight_pct"]))[:10]
    for i, r in enumerate(top10, 1):
        wv = float(r["weight_pct"])
        o = approx.get(r["ticker"])
        gap = f"{wv - o:+.3f}" if o is not None else "n/a"
        add(f"| {i} | {r['ticker']} | {wv:.3f} | "
            f"{o:.3f} | {gap} |" if o is not None else f"| {i} | {r['ticker']} | {wv:.3f} | — | n/a |")
    add("")

    OUT.write_text("# Owner-weights reconciliation (WS1.2–1.4)\n\n"
                   "Generated by `scripts/reconcile_owner_weights.py`.\n\n" + "\n".join(L) + "\n")
    print("\n".join(L))
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
