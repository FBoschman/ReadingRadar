"""Apply the actions that the radar interface exports.

The dashboard is a static file, so it cannot write to the data. It exports one JSON file instead:

    {
      "triage": {"<item id>": {"status": "keep"}},
      "rootsRequests": ["<item id>"]
    }

A triage mark updates that item's `status` and adds `triagedAt`. This is the only write path into a
finished item, and it changes exactly two fields: the reader's own decision and its date.

A roots request appends a queued entry to data/lineageRequests, when the item has a DOI and no lineage
document yet.

Usage:
    python tools/apply_actions.py --file radar-actions.json --dry-run
    python tools/apply_actions.py --file radar-actions.json
"""
import argparse
import subprocess
import sys

import radar_lib as lib

STATUSES = ("keep", "maybe", "skip")


def apply_triage(actions, dry_run):
    changed = 0
    problems = 0
    for doc_id, action in sorted((actions.get("triage") or {}).items()):
        status = str((action or {}).get("status", "")).strip()
        if status not in STATUSES:
            print("SKIP  %s: status must be keep, maybe or skip" % doc_id)
            problems += 1
            continue
        path = lib.DATA / "items" / (doc_id + ".json")
        if not path.is_file():
            print("SKIP  %s: no such item" % doc_id)
            problems += 1
            continue
        item = lib.load_json(path, {}) or {}
        if item.get("status") == status:
            continue
        item["status"] = status
        item["triagedAt"] = lib.today()
        if not dry_run:
            lib.save_json(path, item)
        print("%s %s -> %s" % ("WOULD SET" if dry_run else "SET", doc_id, status))
        changed += 1
    return changed, problems


def apply_roots(actions, dry_run):
    changed = 0
    problems = 0
    done = set(lib.collection("lineage").keys())
    for doc_id in (actions.get("rootsRequests") or []):
        item = lib.load_json(lib.DATA / "items" / (doc_id + ".json"), None)
        if not item:
            print("SKIP  roots %s: no such item" % doc_id)
            problems += 1
            continue
        if doc_id in done:
            print("SKIP  roots %s: a lineage document already exists" % doc_id)
            continue
        if not item.get("doi"):
            print("SKIP  roots %s: the item has no DOI, so Crossref cannot give a reference list" % doc_id)
            problems += 1
            continue
        target = lib.DATA / "lineageRequests" / (doc_id + ".json")
        if target.exists():
            continue
        request = {"itemId": doc_id, "doi": item["doi"], "title": item.get("title", ""),
                   "requestedAt": lib.stamp(), "status": "queued"}
        if not dry_run:
            lib.save_json(target, request)
        print("%s roots request for %s" % ("WOULD QUEUE" if dry_run else "QUEUED", doc_id))
        changed += 1
    return changed, problems


def main(argv=None):
    parser = argparse.ArgumentParser(description="Apply the actions that the radar exported.")
    parser.add_argument("--file", required=True, help="the JSON file the radar exported")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--notes", action="store_true",
                        help="also refresh the wiki notes of the items that were touched")
    args = parser.parse_args(argv)

    path = lib.ROOT / args.file if not str(args.file).startswith(("C:", "c:")) else args.file
    actions = lib.load_json(path, None)
    if not isinstance(actions, dict):
        raise SystemExit("No actions found in " + str(path))
    triaged, triage_problems = apply_triage(actions, args.dry_run)
    queued, roots_problems = apply_roots(actions, args.dry_run)
    if args.notes and not args.dry_run:
        subprocess.run([sys.executable, str(lib.ROOT / "tools" / "vault_notes.py"), "--rewrite"],
                       cwd=str(lib.ROOT))
    print("")
    print("triage marks applied: %d | roots requests queued: %d | refused: %d"
          % (triaged, queued, triage_problems + roots_problems))
    return 0


if __name__ == "__main__":
    sys.exit(main())
