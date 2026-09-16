#!/usr/bin/env python3
"""
verify_raw_integrity.py — the tamper alarm for data/raw/

THE RULE: files in data/raw/ are originals. They are never edited. Cleaning happens on
copies in data/cleaned/.

This script re-hashes every file under data/raw/ and compares against the SHA-256 record
taken at freeze time (data/derived/manifest_annotated.json -> _sha256).

  exit 0  all originals intact
  exit 1  DRIFT — something changed an original (the important outcome)
  exit 2  error (missing record, unreadable file)

Usage:
    python3 scripts/verify_raw_integrity.py            # check
    python3 scripts/verify_raw_integrity.py --rehash   # re-freeze after an INTENTIONAL re-pull
    python3 scripts/verify_raw_integrity.py --quiet    # exit code only
"""
import hashlib, json, os, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "data", "raw")
REC = os.path.join(BASE, "data", "derived", "manifest_annotated.json")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def current_hashes():
    out = {}
    for root, _, files in os.walk(RAW):
        for fn in sorted(files):
            p = os.path.join(root, fn)
            out[os.path.relpath(p, RAW)] = {"sha256": sha256(p), "bytes": os.path.getsize(p)}
    return out


def main():
    quiet = "--quiet" in sys.argv
    rehash = "--rehash" in sys.argv

    if not os.path.exists(REC):
        print(f"ERROR: no freeze record at {REC}", file=sys.stderr)
        return 2
    rec = json.load(open(REC))
    frozen = rec.get("_sha256")
    if not frozen:
        print("ERROR: the freeze record carries no _sha256 block", file=sys.stderr)
        return 2

    now = current_hashes()
    changed, missing, added = [], [], []
    for rel, meta in frozen.items():
        if rel not in now:
            missing.append(rel)
        elif now[rel]["sha256"] != meta["sha256"]:
            changed.append((rel, meta["bytes"], now[rel]["bytes"]))
    for rel in now:
        if rel not in frozen:
            added.append(rel)

    if rehash:
        rec["_sha256"] = now
        rec["_hash_count"] = len(now)
        rec["_refrozen_at"] = __import__("datetime").datetime.now().astimezone().isoformat(timespec="seconds")
        json.dump(rec, open(REC, "w"), indent=1)
        if not quiet:
            print(f"RE-FROZEN: {len(now)} files hashed -> {os.path.relpath(REC, BASE)}")
            for r in added:
                print(f"  + newly covered: {r}")
        return 0

    if not quiet:
        print(f"raw/ integrity check — {len(frozen)} files in the freeze record, {len(now)} on disk")
        print(f"  intact : {len(frozen) - len(changed) - len(missing)}")
        print(f"  CHANGED: {len(changed)}")
        print(f"  MISSING: {len(missing)}")
        print(f"  NEW    : {len(added)}  (not in the freeze record — a raw file was added since freeze)")

    if changed or missing:
        print("\n  ❌ DRIFT DETECTED — an ORIGINAL was edited or removed:", file=sys.stderr)
        for rel, was, now_b in changed:
            print(f"     CHANGED  {rel}   {was:,} -> {now_b:,} bytes", file=sys.stderr)
        for rel in missing:
            print(f"     MISSING  {rel}", file=sys.stderr)
        print("\n  Restore from git:  git checkout -- data/raw/<file>", file=sys.stderr)
        print("  Or, if the change was intentional:  python3 scripts/verify_raw_integrity.py --rehash",
              file=sys.stderr)
        return 1

    if added and not quiet:
        print("  (new files are expected while we are still acquiring; re-freeze when the corpus settles)")
    if not quiet:
        print("  [OK] all originals byte-identical to freeze time")
    return 0


if __name__ == "__main__":
    sys.exit(main())
