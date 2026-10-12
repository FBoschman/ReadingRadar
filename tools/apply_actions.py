"""Apply the actions that the radar interface exports.

The dashboard is a static file, so it cannot write to the data. It exports one JSON file instead:

    {
      "triage": {"<id>": {"status": "keep"}},
      "promotions": {"<id>": {"reason": "one line on why this matters"}},
      "rootsRequests": ["<id>"]
    }

An id can name a finished item (data/items) or a candidate that still waits in the queue
(data/inbox/items). Both are resolved. Until 12 October 2026 only the item collection was searched,
so every mark a reader made in the Queue view was refused as "no such item".

Triage:
    * A finished item gets `status` and `triagedAt`. This is the only write path into a finished item,
      and it changes exactly two fields: the reader's own decision and its date.
    * A candidate gets `status` and `triagedAt` in the inbox, so that the queue shows the decision and
      the calibration card counts it. A `skip` and a `maybe` stop there: nothing is invented.
    * A `keep` on a candidate is a promotion, and a promotion needs a sentence. When the file carries
      a `promotions` entry with a reason, the candidate passes the same check as tools/promote.py and
      becomes a finished item. Without a reason the tool refuses that mark and says what is missing.

A roots request appends a queued entry to data/lineageRequests, when the item has a DOI and no lineage
document yet.

Usage:
    python tools/apply_actions.py --file radar-actions.json --dry-run
    python tools/apply_actions.py --file radar-actions.json
    python tools/apply_actions.py --file radar-actions.json --notes

On Windows, when `python` is not on the PATH, use the launcher: py tools\apply_actions.py --file ...

The exit code is 1 when at least one action was refused, so that a caller sees it.
"""
import argparse
import subprocess
import sys

import promote
import radar_lib as lib

STATUSES = ("keep", "maybe", "skip")
STOCK_CAVEAT = ("Kept from the queue from the title and the metadata. The tool wrote this line: check "
                "the method, the sample and the source before you cite it.")


def resolve(doc_id):
    """Return (kind, path) for an id in the item collection or in the queue. (None, None) if absent."""
    for kind, folder in (("item", lib.DATA / "items"), ("candidate", lib.DATA / "inbox" / "items")):
        path = folder / (doc_id + ".json")
        if path.is_file():
            return kind, path
    return None, None


def decision_from(action, candidate):
    """Build the judgement that a reader's keep implies, from the reason that reader wrote."""
    action = action or {}
    floor = int(lib.profile().get("minScore", 3) or 3)
    reason = str(action.get("reason") or action.get("why") or "").strip()
    caveat = str(action.get("caveat") or "").strip() or STOCK_CAVEAT
    score = action.get("score")
    return {
        "score": floor if score in (None, "") else score,
        "themes": action.get("themes") or list(candidate.get("themeGuess") or []),
        "why": reason,
        "caveat": caveat,
        "wildcard": bool(action.get("wildcard")),
    }


def apply_promotions(actions, dry_run):
    """Promote the candidates that the reader kept with a reason. Returns (ids promoted, refusals)."""
    promoted = set()
    problems = 0
    for doc_id, action in sorted((actions.get("promotions") or {}).items()):
        kind, path = resolve(doc_id)
        if kind is None:
            print("REFUSE %s: no item and no candidate carries that id" % doc_id)
            problems += 1
            continue
        if kind == "item":
            continue  # a finished document is handled by the triage block
        candidate = lib.load_json(path, {}) or {}
        decision = decision_from(action, candidate)
        issues = promote.check(candidate, decision)
        if issues:
            print("REFUSE %s: %s" % (doc_id, "; ".join(issues)))
            problems += 1
            continue
        item = promote.build_item(candidate, decision)
        item["status"] = "keep"
        item["triagedAt"] = lib.today()
        if dry_run:
            print("WOULD PROMOTE %s  score %s  %s" % (doc_id, item["score"], (item.get("title") or "")[:60]))
        else:
            lib.write_document("items", doc_id, item)
            path.unlink()
            print("PROMOTED %s  score %s  %s" % (doc_id, item["score"], (item.get("title") or "")[:60]))
        promoted.add(doc_id)
    return promoted, problems


def apply_triage(actions, dry_run, promoted):
    changed = 0
    problems = 0
    for doc_id, action in sorted((actions.get("triage") or {}).items()):
        status = str((action or {}).get("status", "")).strip()
        if status not in STATUSES:
            print("REFUSE %s: status must be keep, maybe or skip" % doc_id)
            problems += 1
            continue
        if doc_id in promoted:
            continue  # the promotion already wrote the decision
        kind, path = resolve(doc_id)
        if kind is None:
            print("REFUSE %s: no item and no candidate carries that id" % doc_id)
            problems += 1
            continue
        doc = lib.load_json(path, {}) or {}
        if kind == "candidate" and status == "keep":
            print("REFUSE %s: a keep on a candidate is a promotion, and a promotion needs a line. "
                  "Write one line in the Queue view, or mark it maybe." % doc_id)
            problems += 1
            continue
        if doc.get("status") == status:
            continue
        doc["status"] = status
        doc["triagedAt"] = lib.today()
        if not dry_run:
            lib.save_json(path, doc)
        print("%s %s -> %s%s" % ("WOULD SET" if dry_run else "SET", doc_id, status,
                                 " (candidate, still in the queue)" if kind == "candidate" else ""))
        changed += 1
    return changed, problems


def apply_roots(actions, dry_run):
    changed = 0
    problems = 0
    done = set(lib.collection("lineage").keys())
    for doc_id in (actions.get("rootsRequests") or []):
        kind, path = resolve(doc_id)
        if kind is None:
            print("REFUSE roots %s: no item and no candidate carries that id" % doc_id)
            problems += 1
            continue
        item = lib.load_json(path, {}) or {}
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
    promoted, promotion_problems = apply_promotions(actions, args.dry_run)
    triaged, triage_problems = apply_triage(actions, args.dry_run, promoted)
    queued, roots_problems = apply_roots(actions, args.dry_run)
    if args.notes and not args.dry_run:
        subprocess.run([sys.executable, str(lib.ROOT / "tools" / "vault_notes.py"), "--rewrite"],
                       cwd=str(lib.ROOT))
    refused = promotion_problems + triage_problems + roots_problems
    print("")
    print("promoted: %d | triage marks applied: %d | roots requests queued: %d | refused: %d"
          % (len(promoted), triaged, queued, refused))
    if refused:
        print("A refused action changed nothing. Read the line above it for the reason.")
    return 0 if refused == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
