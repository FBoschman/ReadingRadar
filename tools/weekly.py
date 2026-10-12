"""Run the parts of the weekly cycle that a script can do.

Steps, in order:
    1. harvest the sources
    2. fill the missing abstracts from OpenAlex
    3. write the run log
    4. validate the data
    5. rebuild the bundle
    6. commit and push

The judgement pass, the digest and the lineage narrative are decisions. They are NOT part of this
script. The run log says so in plain words when they have not run.

Usage:
    python tools/weekly.py --dry-run
    python tools/weekly.py --since 2026-10-05
    python tools/weekly.py --no-push
"""
import argparse
import subprocess
import sys

import radar_lib as lib

OK = "ok"


def call(command, dry_run=False):
    """Run a command. Print the output. Return True on success."""
    print("")
    print("$ " + " ".join(command))
    if dry_run:
        print("  (dry run: not executed)")
        return True
    result = subprocess.run(command, cwd=str(lib.ROOT), capture_output=True, text=True)
    if result.stdout:
        print(result.stdout.rstrip())
    if result.stderr:
        print(result.stderr.rstrip())
    if result.returncode != 0:
        print("  command failed with code", result.returncode)
        return False
    return True


def update_run_log(dry_run):
    """Record the harvest in meta/lastRun.json, unless a completed record already exists for the day."""
    harvest = lib.load_json(lib.DATA / "inbox" / "run.json", {}) or {}
    if not harvest:
        print("run log: no harvest record found; nothing written")
        return
    current = lib.load_json(lib.DATA / "meta" / "lastRun.json", {}) or {}
    if current.get("date") == harvest.get("date") and int(current.get("kept") or 0) > 0:
        print("run log: a completed record for %s exists; it was left unchanged" % harvest["date"])
        return
    counts = harvest.get("counts", {})
    doc = {
        "date": harvest.get("date"),
        "label": "Weekly harvest (local, automatic)",
        "harvested": counts.get("seen", 0),
        "unique": counts.get("candidates", 0),
        "kept": 0,
        "sources": harvest.get("sources", []),
        "notes": ("Harvest and abstract enrichment only. The judgement pass, the digest and the roots "
                  "narrative are decisions and have not run yet. Score the candidates in "
                  "data/inbox/items with data/inbox/judgement.json, then run tools/promote.py, then "
                  "write the digest and tools/lineage.py for the roots. A run with kept: 0 means the "
                  "queue is full and the radar is waiting for a reader."),
    }
    print("run log: %s, %s candidates, %s" % (doc["date"], doc["unique"],
                                              "no source failed" if all(OK in s.get("status", "") for s in doc["sources"]) else "see the source lines"))
    if not dry_run:
        lib.save_json(lib.DATA / "meta" / "lastRun.json", doc)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run the automatic part of the weekly radar cycle.")
    parser.add_argument("--since", default=None, help="first publication date. Default: the last run date")
    parser.add_argument("--limit", type=int, default=10, help="maximum rows for each harvest query")
    parser.add_argument("--enrich-limit", type=int, default=60, help="maximum abstracts to fill")
    parser.add_argument("--dry-run", action="store_true", help="print the plan and change nothing")
    parser.add_argument("--no-push", action="store_true", help="commit but do not push")
    args = parser.parse_args(argv)

    last = lib.load_json(lib.DATA / "meta" / "lastRun.json", {}) or {}
    since = args.since or last.get("date") or lib.today()
    print("weekly cycle for", lib.today(), "| window from", since)

    if not call([sys.executable, "tools/harvest.py", "--since", since, "--limit", str(args.limit)], args.dry_run):
        print("the harvest failed. The cycle stops here.")
        return 1
    if not call([sys.executable, "tools/enrich.py", "--limit", str(args.enrich_limit)], args.dry_run):
        print("the enrichment failed. The cycle stops here.")
        return 1

    update_run_log(args.dry_run)

    if not call([sys.executable, "tools/validate.py"], args.dry_run):
        print("the data breaks the schema. Nothing was committed.")
        return 1
    if not call([sys.executable, "tools/build_bundle.py"], args.dry_run):
        return 1

    inbox = len(list((lib.DATA / "inbox" / "items").glob("*.json")))
    drafts = len(list((lib.DATA / "inbox" / "lineage").glob("*.json")))

    if not args.dry_run:
        call(["git", "add", "-A"])
        status = subprocess.run(["git", "status", "--porcelain"], cwd=str(lib.ROOT),
                                capture_output=True, text=True).stdout.strip()
        if not status:
            print("no change to commit. The radar had nothing new.")
            return 0
        message = ("Weekly harvest %s: %d candidates in the queue, %d roots drafts, %d items in the collection"
                   % (lib.today(), inbox, drafts, len(lib.collection("items"))))
        if not call(["git", "commit", "-m", message]):
            return 1
        if args.no_push:
            print("commit made. The push was skipped on request.")
            return 0
        call(["git", "pull", "--rebase", "--autostash"])
        if not call(["git", "push"]):
            print("the push failed. The commit is local only.")
            return 1

    print("")
    print("the cycle is done.")
    print("waiting in the queue: %d candidates, %d roots drafts" % (inbox, drafts))
    if inbox:
        print("The judgement pass is yours: python tools/queue.py, then data/inbox/judgement.json, then tools/promote.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
