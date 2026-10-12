"""Write intake notes for the strongest items into the Obsidian vault.

The profile describes the vault: notes go to raw/articles as intake for the /ingest pipeline.
Two rules are absolute and this tool obeys them: never write or edit anything under wiki/, and
never touch raw/fieldwork or raw/legacy.

The cloud run has had no file access to the reader's machine since 5 October 2026, so notes were
delivered in chat instead. From the reader's own machine the handover works again.

Usage:
    python tools/vault_notes.py --dry-run
    python tools/vault_notes.py                 # items of the last run at or above autoMin
    python tools/vault_notes.py --run all       # every item at or above autoMin without a note
"""
import argparse
import json
import pathlib
import re
import sys

import radar_lib as lib


def surname(authors):
    """The family name of the first author. Skip an initial or a very short token."""
    first = str(authors or "").split(",")[0].strip()
    tokens = [t for t in re.split(r"\s+", first) if t]
    if not tokens:
        return "unknown"
    chosen = tokens[0]
    if len([c for c in chosen if c.isalpha()]) < 3 and len(tokens) > 1:
        chosen = tokens[-1]
    chosen = "".join(c for c in chosen if c.isalpha() or c == "-")
    return chosen if len(chosen) >= 2 else "unknown"


def short_title(title, limit=48):
    text = re.sub(r"[^A-Za-z0-9 ]+", " ", str(title or "")).strip().lower()
    words = text.split()
    out = ""
    for word in words:
        if len(out) + len(word) + 1 > limit:
            break
        out = (out + "-" + word) if out else word
    return out or "untitled"


def year_of(date_text):
    match = re.match(r"(\d{4})", str(date_text or ""))
    return match.group(1) if match else ""


def note_text(item, theme_names, doc_id):
    doi = item.get("doi") or ""
    themes = ", ".join(item.get("themes") or [])
    names = ", ".join(theme_names.get(code, code) for code in (item.get("themes") or []))
    # Quote every free-text value: a colon inside a title would break the frontmatter.
    def q(value):
        return json.dumps(str(value or ""), ensure_ascii=False)

    lines = [
        "---",
        "title: " + q(item.get("title")),
        "source: " + q(item.get("url")),
        "authors: " + q(item.get("authors")),
        "year: " + year_of(item.get("date")),
        "published: " + q(item.get("date")),
        "created: " + lib.today(),
        "venue: " + q(item.get("venue")),
        "doi: " + q(doi),
        "description: " + q(item.get("why")),
        "intake: reading-radar",
        "ingested: false",
        "radar_id: " + q(doc_id),
        "radar_url: " + q("https://github.com/FBoschman/ReadingRadar/blob/main/data/items/" + doc_id + ".json"),
        "radar_score: " + str(item.get("score")),
        "radar_themes: [" + themes + "]",
        "radar_theme_names: " + q(names),
        "tags: [reading-radar, " + themes + "]",
        "---",
        "",
        "# " + str(item.get("title") or ""),
        "",
        "**Why the radar kept it.** " + str(item.get("why") or ""),
        "",
        "**What to check.** " + str(item.get("caveat") or ""),
        "",
    ]
    if names:
        lines.append("**Themes.** " + names)
        lines.append("")
    abstract = str(item.get("abstract") or "").strip()
    if abstract:
        lines.append("## Abstract")
        lines.append("")
        lines.append(abstract)
        lines.append("")
        lines.append("_Abstract from " + str(item.get("abstractSource") or "the source") + "._")
        lines.append("")
    lines.append("_Intake note from the Reading Radar. The note is for the /ingest pipeline. "
                 "The radar does not edit anything in wiki/._")
    lines.append("")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Write intake notes into the vault.")
    parser.add_argument("--dry-run", action="store_true", help="print the plan and write nothing")
    parser.add_argument("--run", default="last", help="'last' for the last run date, or 'all'")
    parser.add_argument("--rewrite", action="store_true",
                        help="overwrite an existing note when it was written by the radar")
    args = parser.parse_args(argv)

    profile = lib.profile()
    vault = profile.get("vault", {})
    root = pathlib.Path(vault.get("path") or "")
    if not root.is_dir():
        raise SystemExit("The vault path does not exist: " + str(root))
    inbox = root / (vault.get("inbox") or "raw/articles")
    if not inbox.is_dir():
        raise SystemExit("The intake folder does not exist: " + str(inbox))
    for guarded in ("wiki", "raw/fieldwork", "raw/legacy"):
        if str(inbox).lower().endswith(guarded.replace("/", "\\").lower()):
            raise SystemExit("Refused: the intake folder is a guarded folder.")

    minimum = int(vault.get("autoMin", 4) or 4)
    if not vault.get("auto", True):
        print("The vault step is switched off in the profile. Nothing to do.")
        return 0

    last = lib.load_json(lib.DATA / "meta" / "lastRun.json", {}) or {}
    run_date = last.get("date")
    theme_names = {theme.get("code"): theme.get("name") for theme in profile.get("themes", [])}
    items = lib.collection("items")
    written = 0
    skipped = 0
    for doc_id, item in sorted(items.items()):
        if int(item.get("score") or 0) < minimum:
            continue
        if args.run == "last" and run_date and item.get("run") != run_date:
            continue
        name = "%s-%s-%s.md" % (surname(item.get("authors")), year_of(item.get("date")), short_title(item.get("title")))
        target = inbox / name
        if target.exists():
            if not args.rewrite:
                skipped += 1
                continue
            existing = target.read_text(encoding="utf-8", errors="replace")
            if "intake: reading-radar" not in existing:
                print("KEEP  %s: written by hand, not by the radar" % name)
                skipped += 1
                continue
        if args.dry_run:
            print("WOULD WRITE", target)
        else:
            target.write_text(note_text(item, theme_names, doc_id), encoding="utf-8", newline="\n")
            item["wikiNote"] = name
            item["wikiWrittenAt"] = lib.today()
            item["wikiIngested"] = False
            lib.save_json(lib.DATA / "items" / (doc_id + ".json"), item)
            print("WROTE", target.name)
        written += 1
    print("")
    print("notes written:", written, "| already there:", skipped, "| intake folder:", inbox)
    return 0


if __name__ == "__main__":
    sys.exit(main())
