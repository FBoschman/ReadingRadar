"""Complete a lineage draft with the judgement fields.

The draft holds the references from Crossref. The strands, the narrative, the forYou and the
absent fields are a decision by a person or an agent. That decision goes into
data/inbox/lineage-judgement.json:

    {
      "doi_10.1000_example": {
        "strands": [{"name": "...", "kind": "frame", "note": "...", "refs": [0, 1, 2]}],
        "narrative": "Two or three paragraphs, British English, naming authors and years.",
        "forYou": "One sentence that links the lineage to the reader's work.",
        "absent": "One sentence on the notable absences."
      }
    }

This tool checks the result against SCHEMA.md, writes data/lineage/<id>.json and removes the draft.

Usage:
    python tools/complete_lineage.py --dry-run
    python tools/complete_lineage.py
"""
import argparse
import sys

import radar_lib as lib

STRAND_KINDS = ("root", "frame", "method", "debate", "context")


def check(draft, decision):
    problems = []
    if not isinstance(decision, dict):
        return ["the decision is not an object"]
    strands = decision.get("strands")
    if not isinstance(strands, list) or not strands:
        problems.append("strands must be a non-empty list")
    else:
        if len(strands) > 8:
            problems.append("a maximum of 8 strands is allowed")
        used = set()
        for strand in strands:
            if strand.get("kind") not in STRAND_KINDS:
                problems.append("strand kind not allowed: " + str(strand.get("kind")))
            if not strand.get("name"):
                problems.append("a strand needs a name")
            for index in strand.get("refs", []):
                if not isinstance(index, int) or index < 0 or index >= len(draft["refs"]):
                    problems.append("a strand points outside the reference list: " + str(index))
                else:
                    used.add(index)
        missing = [i for i in range(len(draft["refs"])) if i not in used]
        if missing:
            problems.append("%d references are in no strand. Add a final 'Other / case context' strand"
                            % len(missing))
    if len(str(decision.get("narrative") or "")) < 80:
        problems.append("the narrative is too short")
    if len(str(decision.get("forYou") or "")) < 20:
        problems.append("the forYou sentence is missing")
    if len(str(decision.get("absent") or "")) < 20:
        problems.append("the absent sentence is missing")
    return problems


def main(argv=None):
    parser = argparse.ArgumentParser(description="Complete a lineage draft.")
    parser.add_argument("--dry-run", action="store_true", help="check only, write nothing")
    args = parser.parse_args(argv)

    decisions = lib.load_json(lib.DATA / "inbox" / "lineage-judgement.json", {})
    if not decisions:
        raise SystemExit("No decisions found in data/inbox/lineage-judgement.json")

    done = 0
    refused = 0
    for doc_id, decision in sorted(decisions.items()):
        draft = lib.load_json(lib.DATA / "inbox" / "lineage" / (doc_id + ".json"), None)
        if draft is None:
            print("SKIP  %s: no draft in the inbox" % doc_id)
            refused += 1
            continue
        if (lib.DATA / "lineage" / (doc_id + ".json")).exists():
            print("SKIP  %s: the lineage document already exists" % doc_id)
            refused += 1
            continue
        problems = check(draft, decision)
        if problems:
            print("FAIL  %s: %s" % (doc_id, "; ".join(problems)))
            refused += 1
            continue
        draft["strands"] = decision["strands"]
        draft["narrative"] = decision["narrative"].strip()
        draft["forYou"] = decision["forYou"].strip()
        draft["absent"] = decision["absent"].strip()
        if args.dry_run:
            print("OK    %s: %d strands, %d references" % (doc_id, len(draft["strands"]), draft["parsed"]))
        else:
            lib.write_document("lineage", doc_id, draft)
            (lib.DATA / "inbox" / "lineage" / (doc_id + ".json")).unlink()
            print("WROTE %s: %d strands, %d references" % (doc_id, len(draft["strands"]), draft["parsed"]))
        done += 1

    print("")
    print("completed:", done, "| refused:", refused, "| dry run:", bool(args.dry_run))
    return 0 if refused == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
