"""Check the data against SCHEMA.md. Run this before a commit.

Usage:
    python tools/validate.py

The check returns exit code 1 when a document breaks the schema, so that the weekly cycle can
refuse to commit a bad run. The inbox is a working folder and is not checked.
"""
import re
import sys

import radar_lib as lib

WARNINGS = []

ITEM_STATUS = ("new", "keep", "maybe", "skip")
ITEM_KINDS = ("paper", "discourse")
STRAND_KINDS = ("root", "frame", "method", "debate", "context")
REQUEST_STATUS = ("queued", "done", "no-references")


def problems_of_item(doc_id, doc):
    out = []
    codes = [theme.get("code") for theme in lib.profile().get("themes", [])]
    for field in ("kind", "title", "authors", "venue", "date", "url", "themes", "score", "why", "source", "status", "run"):
        if field not in doc:
            out.append("missing field: " + field)
    if doc.get("kind") not in ITEM_KINDS:
        out.append("kind must be paper or discourse: " + str(doc.get("kind")))
    if doc.get("status") not in ITEM_STATUS:
        out.append("status not allowed: " + str(doc.get("status")))
    if not isinstance(doc.get("themes"), list) or not doc.get("themes"):
        out.append("themes must be a non-empty list")
    else:
        for code in doc["themes"]:
            if code not in codes:
                out.append("unknown theme code: " + str(code))
    score = doc.get("score")
    if not isinstance(score, int) or score < 0 or score > 5:
        out.append("score must be a whole number between 0 and 5: " + str(score))
    if not re.match(r"^\d{4}(-\d{2}(-\d{2})?)?$", str(doc.get("date") or "")):
        out.append("date must be YYYY, YYYY-MM or YYYY-MM-DD: " + str(doc.get("date")))
    if doc.get("doi") and not str(doc_id).startswith("doi_"):
        out.append("a paper with a DOI must use a doi_ id")
    if not re.match(r"^(doi_|cons_|oa_|sg-|bs-|rss-)", str(doc_id)):
        out.append("the id does not follow a rule of SCHEMA.md")
    return out


def problems_of_lineage(doc_id, doc, item_ids):
    out = []
    if doc.get("itemId") not in item_ids:
        out.append("itemId does not exist in items: " + str(doc.get("itemId")))
    if doc_id != doc.get("itemId"):
        out.append("the lineage id must equal the item id")
    if not isinstance(doc.get("refs"), list) or not doc["refs"]:
        out.append("refs must be a non-empty list")
    else:
        for index, ref in enumerate(doc["refs"]):
            if not isinstance(ref, dict):
                out.append("reference %d is not an object" % index)
            elif not ref.get("t") and not ref.get("d"):
                if ref.get("a") or ref.get("y"):
                    WARNINGS.append("%s: reference %d carries only an author or a year. This is normal for a"
                                    " Crossref list, and the method field should say so." % (doc_id, index))
                else:
                    out.append("reference %d is empty: it has no author, no year, no title and no DOI" % index)
    if not isinstance(doc.get("strands"), list) or not doc["strands"]:
        out.append("strands must be a non-empty list")
    else:
        for strand in doc["strands"]:
            if strand.get("kind") not in STRAND_KINDS:
                out.append("strand kind not allowed: " + str(strand.get("kind")))
            for index in strand.get("refs", []):
                if not isinstance(index, int) or index < 0 or index >= len(doc.get("refs", [])):
                    out.append("a strand points to a reference that does not exist: " + str(index))
    if len(str(doc.get("narrative") or "")) < 80:
        out.append("the narrative is too short")
    if doc.get("confidence") not in ("low", "medium"):
        out.append("confidence must be low or medium")
    if not isinstance(doc.get("parsed"), int):
        out.append("parsed must be a whole number")
    return out


def policy_problems(doc_id, doc, allow):
    """The policy in meta/profile.json, checked against the record.

    The panel found four items below the score floor, fifteen without a caveat and a correction notice
    filed as a paper (P7-2, P3-3, P6-3). A record that breaks the written policy is an error, unless the
    reader has chosen to keep it: the allow-list in data/meta/policyAllowList.json carries the ids and
    the reason.
    """
    out = []
    floor = int(lib.profile().get("minScore", 3) or 3)
    if int(doc.get("score") or 0) < floor and doc_id not in set(allow.get("score", [])):
        out.append("score %s is below the floor of %d, and the record is not on the allow-list"
                   % (doc.get("score"), floor))
    if not str(doc.get("caveat") or "").strip() and doc_id not in set(allow.get("caveat", [])):
        out.append("no caveat, and the record is not on the allow-list")
    if lib.is_noise_title(doc.get("title")):
        out.append("the title is a correction, an erratum or a retraction")
    return out


def main():
    total_problems = 0
    allow = lib.load_json(lib.DATA / "meta" / "policyAllowList.json", {}) or {}
    items = lib.collection("items")
    lineage = lib.collection("lineage")
    events = lib.collection("events")
    requests = lib.collection("lineageRequests")
    meta = lib.collection("meta")
    item_ids = set(items.keys())

    for doc_id, doc in sorted(items.items()):
        for problem in problems_of_item(doc_id, doc):
            print("ITEM   %s: %s" % (doc_id, problem))
            total_problems += 1
        for problem in policy_problems(doc_id, doc, allow):
            print("POLICY %s: %s" % (doc_id, problem))
            total_problems += 1
    for doc_id, doc in sorted(lineage.items()):
        for problem in problems_of_lineage(doc_id, doc, item_ids):
            print("ROOTS  %s: %s" % (doc_id, problem))
            total_problems += 1
    for doc_id, doc in sorted(events.items()):
        if not doc.get("title") or not doc.get("url"):
            print("EVENT  %s: a title and a url are required" % doc_id)
            total_problems += 1
        if not (doc.get("start") or doc.get("deadline")):
            print("EVENT  %s: a start date or a deadline is required" % doc_id)
            total_problems += 1
    for doc_id, doc in sorted(requests.items()):
        if doc.get("status") not in REQUEST_STATUS:
            print("QUEUE  %s: status not allowed: %s" % (doc_id, doc.get("status")))
            total_problems += 1
    digest = meta.get("digest", {})
    for doc_id in digest.get("mustRead", []):
        if doc_id not in item_ids:
            print("DIGEST mustRead: %s is not in items" % doc_id)
            total_problems += 1

    print("")
    print("items: %d | roots: %d | events: %d | queue: %d" % (len(items), len(lineage), len(events), len(requests)))
    if WARNINGS:
        print("")
        print("warnings: %d" % len(WARNINGS))
        for line in WARNINGS[:12]:
            print("  " + line)
    print("problems:", total_problems)
    return 1 if total_problems else 0


if __name__ == "__main__":
    sys.exit(main())
