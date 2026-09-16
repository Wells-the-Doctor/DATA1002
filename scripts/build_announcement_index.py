#!/usr/bin/env python3
"""the complete S&P/ASX 200 announcement index.

Source: Market Index's ASX 200 announcements page (158 documents, 2011-2026),
harvested 2026-09-13 through the browser (the page is bot-walled to scripts).
The list is embedded verbatim so the index is reproducible without re-scraping.

Document types present:
  rebalance  quarterly review          addition  ad-hoc addition
  removal    ad-hoc removal            demerger  demerger event
  update     correction                no-change no change this quarter
  consultation / adjournment / rebalance-delayed  procedural

Writes derived/asx200_announcement_index.csv
"""
from __future__ import annotations

import csv
from pathlib import Path

STAGE1 = Path(__file__).resolve().parent.parent
OUT = STAGE1 / "data" / "derived" / "asx200_announcement_index.csv"
BASE = "https://files.marketindex.com.au/files/announcements/"

NAMES = """20110415-asx200-removal.pdf,20110502-asx200-addition.pdf,20110527-asx200-addition.pdf,20110602-asx200-removal.pdf,20110603-asx200-rebalance.pdf,20110902-asx200-rebalance.pdf,20111026-asx200-removal.pdf,20111111-asx200-addition.pdf,20111125-asx200-removal.pdf,20111202-asx200-rebalance.pdf,20120302-asx200-rebalance.pdf,20120321-asx200-removal.pdf,20120405-asx200-removal.pdf,20120412-asx200-removal.pdf,20120601-asx200-rebalance.pdf,20120620-asx200-removal.pdf,20120720-asx200-removal.pdf,20120907-asx200-rebalance.pdf,20121207-asx200-rebalance.pdf,20130301-asx200-rebalance.pdf,20130607-asx200-rebalance.pdf,20130906-asx200-rebalance.pdf,20131108-asx200-removal.pdf,20131202-asx200-no-change.pdf,20131206-asx200-rebalance.pdf,20131210-asx200-addition.pdf,20140212-asx200-removal.pdf,20140307-asx200-rebalance.pdf,20140423-asx200-removal.pdf,20140520-asx200-removal.pdf,20140606-asx200-rebalance.pdf,20140707-asx200-removal.pdf,20140714-asx200-removal.pdf,20140808-asx200-removal.pdf,20140815-asx200-removal.pdf,20140905-asx200-rebalance.pdf,20141008-asx200-removal.pdf,20141205-asx200-rebalance.pdf,20150224-asx200-removal.pdf,20150306-asx200-rebalance.pdf,20150507-asx200-removal.pdf,20150507-bhp-demerger.pdf,20150515-asx200-removal.pdf,20150522-asx200-removal.pdf,20150605-asx200-rebalance.pdf,20150820-asx200-removal.pdf,20150903-asx200-removal.pdf,20150904-asx200-rebalance.pdf,20151204-asx200-rebalance.pdf,20160125-asx200-demerger.pdf,20160201-asx200-removal.pdf,20160204-asx200-removal.pdf,20160311-asx200-rebalance.pdf,20160414-asx200-removal.pdf,20160503-asx200-removal.pdf,20160610-asx200-rebalance.pdf,20160617-asx200-demerger.pdf,20160621-asx200-removal.pdf,20160722-asx200-removal.pdf,20160902-asx200-rebalance.pdf,20161205-asx200-removal.pdf,20161209-asx200-rebalance.pdf,20170421-asx200-removal.pdf,20170609-asx200-rebalance.pdf,20170728-asx200-removal.pdf,20170901-asx200-rebalance.pdf,20171107-asx200-addition.pdf,20171206-asx200-removal.pdf,20171208-asx200-rebalance.pdf,20180309-asx200-rebalance.pdf,20180503-asx200-removal.pdf,20180507-asx200-update.pdf,20180518-asx200-removal.pdf,20180524-asx200-demerger.pdf,20180608-asx200-rebalance.pdf,20180831-asx200-removal.pdf,20180905-asx200-update.pdf,20180907-asx200-rebalance.pdf,20180910-asx200-removal.pdf,20181004-asx200-removal.pdf,20181011-asx200-removal.pdf,20181114-asx200-demerger.pdf,20181121-asx200-removal.pdf,20181129-asx200-removal.pdf,20181214-asx200-rebalance.pdf,20190308-asx200-rebalance.pdf,20190415-asx200-removal.pdf,20190614-asx200-rebalance.pdf,20190731-asx200-removal.pdf,20190906-asx200-rebalance.pdf,20191107-asx200-removal.pdf,20191205-asx200-removal.pdf,20191213-asx200-rebalance.pdf,20200313-asx200-rebalance.pdf,20200316-asx200-demerger.pdf,20200323-asx200-rebalance-delayed.pdf,20200612-asx200-rebalance.pdf,20200625-asx200-demerger.pdf,20200630-asx200-removal.pdf,20210127-asx200-removal.pdf,20210416-asx200-removal.pdf,20210618-asx200-demerger.pdf,20210622-asx200-removal.pdf,20210708-asx200-removal.pdf,20211124-asx200-removal.pdf,20211207-asx200-removal.pdf,20211208-asx200-removal.pdf,20220112-asx200-consultation.pdf,20220114-asx200-removal.pdf,20220201-asx200-removal.pdf,20220203-asx200-removal.pdf,20220304-asx200-rebalance.pdf,20220407-asx200-removal.pdf,20220517-asx200-demerger.pdf,20220519-asx200-removal.pdf,20220520-asx200-adjournment.pdf,20220603-asx200-rebalance.pdf,20220615-asx200-removal.pdf,20220715-asx200-removal.pdf,20220725-asx200-demerger.pdf,20220902-asx200-rebalance.pdf,20221202-asx200-rebalance.pdf,20230106-asx200-removal.pdf,20230303-asx200-rebalance.pdf,20230413-asx200-removal.pdf,20230602-asx200-rebalance.pdf,20230718-asx200-removal.pdf,20230728-asx200-demerger.pdf,20230901-asx200-rebalance.pdf,20231013-asx200-removal.pdf,20231024-asx200-removal.pdf,20231201-asx200-rebalance.pdf,20231219-asx200-removal.pdf,20240201-asx200-removal.pdf,20240301-asx200-rebalance.pdf,20240502-asx200-removal.pdf,20240531-asx200-removal.pdf,20240607-asx200-rebalance.pdf,20240611-asx200-removal.pdf,20240719-asx200-removal.pdf,20240906-asx200-rebalance.pdf,20240918-asx200-removal.pdf,20241206-asx200-rebalance.pdf,20250228-asx200-removal.pdf,20250307-asx200-rebalance.pdf,20250416-asx200-removal.pdf,20250606-asx200-rebalance.pdf,20250715-asx200-removal.pdf,20250905-asx200-rebalance.pdf,20250909-asx200-removal.pdf,20250922-asx200-removal.pdf,20251205-asx200-rebalance.pdf,20260306-asx200-rebalance.pdf,20260413-asx200-removal.pdf,20260415-asx200-removal.pdf,20260606-asx200-rebalance.pdf,20260703-asx200-removal.pdf,20260904-asx200-rebalance.pdf"""


def main() -> int:
    names = [n for n in NAMES.split(",") if n]
    rows = []
    for n in names:
        stem = n[:-4]
        date = f"{stem[:4]}-{stem[4:6]}-{stem[6:8]}"
        rest = stem[9:]
        kind = "rebalance" if rest == "rebalance" else rest.replace("asx200-", "")
        rows.append({"date": date, "type": kind, "file": n, "url": BASE + n})
    rows.sort(key=lambda r: r["date"])

    types: dict[str, int] = {}
    for r in rows:
        types[r["type"]] = types.get(r["type"], 0) + 1

    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["date", "type", "file", "url"])
        w.writeheader()
        w.writerows(rows)

    quarters = {f"{r['date'][:4]}Q{(int(r['date'][5:7]) + 2) // 3}"
                for r in rows if r["type"] == "rebalance"}
    allq = []
    for y in range(2011, 2027):
        for q in (1, 2, 3, 4):
            allq.append(f"{y}Q{q}")
    missing = [q for q in allq if q not in quarters and q >= "2011Q3"]
    print(f"announcement index: {len(rows)} documents · {rows[0]['date']} -> {rows[-1]['date']}")
    print(f"  types: {dict(sorted(types.items(), key=lambda x: -x[1]))}")
    print(f"  quarterly rebalances found: {len(quarters)}")
    print(f"  quarters with NO rebalance document: {missing}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
