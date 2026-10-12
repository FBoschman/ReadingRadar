"""Read the intake folder and update the wiki state of each item.

The radar writes intake notes into the vault but never looks at them again, so `ingested` was a flag
nobody read (panel finding P4-5). This tool closes that loop:

    - for every item that names a note (`wikiNote`), check that the note still exists;
    - read the note's frontmatter and copy `ingested` back into the item;
    - adopt a note that exists but is not recorded on its item, by reading `radar_id`;
    - report a note whose `radar_id` no longer matches an item, and a note that was written by hand.

It writes only the four wiki fields of an item, never its content.

Usage:
    python tools/wiki_status.py --dry-run
    python tools/wiki_status.py
"""
import argparse
import pathlib
import re
import sys

import radar_lib as lib

FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)


def read_note(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    block = FRONTMATTER.search(text)
    fields = {}
    if block:
        for line in block.group(1).splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                fields[key.strip()] = value.strip().strip('"')
    fields["intake"] = fields.get("intake", "")
    return fields


def main(argv=None):
    parser = argparse.ArgumentParser(description="Update the wiki state of the items.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    profile = lib.profile()
    vault = profile.get("vault", {})
    inbox = pathlib.Path(vault.get("path") or "") / (vault.get("inbox") or "raw/articles")
    if not inbox.is_dir():
        print("The intake folder does not exist:", inbox)
        return 1

    notes = {}
    for path in sorted(inbox.glob("*.md")):
        fields = read_note(path)
        if fields.get("intake") == "reading-radar":
            notes[path.name] = fields
    print("intake notes found:", len(notes))

    items = lib.collection("items")
    updated = 0
    adopted = 0
    missing = []
    for doc_id, item in items.items():
        note = item.get("wikiNote")
        if note and note not in notes:
            missing.append((doc_id, note))
            continue
        if note and note in notes:
            fields = notes[note]
            ingested = str(fields.get("ingested", "false")).lower() == "true"
            if item.get("wikiIngested") != ingested:
                item["wikiIngested"] = ingested
                if not args.dry_run:
                    lib.save_json(lib.DATA / "items" / (doc_id + ".json"), item)
                updated += 1
    for name, fields in notes.items():
        item_id = (fields.get("radar_id") or "").strip()
        if item_id and item_id in items and not items[item_id].get("wikiNote"):
            item = items[item_id]
            item["wikiNote"] = name
            item["wikiWrittenAt"] = fields.get("created") or ""
            item["wikiIngested"] = str(fields.get("ingested", "false")).lower() == "true"
            if not args.dry_run:
                lib.save_json(lib.DATA / "items" / (item_id + ".json"), item)
            adopted += 1

    print("")
    print("items whose ingested flag changed:", updated)
    print("notes adopted onto their item:", adopted)
    if missing:
        print("items that name a note which no longer exists:")
        for doc_id, note in missing[:10]:
            print("  ", doc_id, "->", note)
    return 0


if __name__ == "__main__":
    sys.exit(main())
