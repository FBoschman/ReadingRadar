"""Harvest candidate items from the sources that work from this machine.

Usage:
    python tools/harvest.py --dry-run
    python tools/harvest.py --since 2026-10-05
    python tools/harvest.py --source openalex --limit 10

The script writes candidates to data/inbox/items/. A candidate holds the metadata from the
source and an empty judgement block. It is not an item until a person or an agent scores it.

The script never overwrites a document that exists. It records the state of every source in
data/inbox/run.json, with a short reason when a source fails.
"""
import argparse
import json
import re
import sys
import urllib.parse
import xml.etree.ElementTree as ElementTree

import radar_lib as lib

SOURCES = ("crossref-themes", "crossref-journals", "openalex", "bluesky", "scienceguide", "rss")

# One research question for each theme. The paper search uses these. Edit them if a theme drifts.
QUESTIONS = {
    "eco": "How do learning ecosystems and living labs support multi-stakeholder learning in cities?",
    "td": "How do transdisciplinary research partnerships handle power and knowledge integration with societal actors?",
    "cx": "How does complexity theory inform education through enabling constraints and emergence?",
    "dbr": "How is design-based research conducted with practitioners to produce transferable design principles?",
    "par": "How does participatory action research with communities build knowledge and change practice?",
    "ai": "How does generative AI change epistemic agency, cognitive offloading and professional judgement?",
    "dec": "How do epistemic justice and decolonial approaches change curriculum and knowledge production?",
    "pc": "How are professional criticality and onderzoekend vermogen developed in higher education?",
}


def make_candidate(doc_id, kind, title, authors, venue, date, url, doi, source, abstract, themes, lang="", extra=None):
    doc = {
        "id": doc_id,
        "kind": kind,
        "title": title,
        "authors": authors,
        "venue": venue,
        "date": date,
        "url": url,
        "doi": doi,
        "lang": lang,
        "source": source,
        "run": lib.today(),
        "abstract": lib.clean_markup(abstract),
        "themeGuess": themes,
        "found": lib.stamp(),
        "status": "candidate",
        "judgement": {"score": None, "themes": [], "why": "", "caveat": "", "wildcard": False},
    }
    if extra:
        doc.update(extra)
    return doc


def add(store, doc, known, stats):
    """Add a candidate. Skip a duplicate. Merge a second source into the first record."""
    if doc is None:
        return
    doc_id = doc["id"]
    if doc_id in known:
        stats["known"] += 1
        return
    if doc_id in store:
        first = store[doc_id]
        if doc["source"] not in first["source"]:
            first["source"] = first["source"] + ", " + doc["source"]
        if not first.get("abstract") and doc.get("abstract"):
            first["abstract"] = doc["abstract"]
        for theme in doc.get("themeGuess", []):
            if theme not in first["themeGuess"]:
                first["themeGuess"].append(theme)
        stats["merged"] += 1
        return
    store[doc_id] = doc
    stats["new"] += 1


# ---------------------------------------------------------------- Crossref
def crossref_author_list(message):
    names = []
    for author in message.get("author", []) or []:
        name = author.get("family") or author.get("name") or ""
        if name:
            names.append(name)
    if not names:
        return ""
    if len(names) > 3:
        return ", ".join(names[:3]) + " et al."
    return ", ".join(names)


def crossref_rows(items, label, theme, stats):
    out = []
    for message in items:
        doi = (message.get("DOI") or "").strip()
        title = (message.get("title") or [""])[0]
        if not doi or not title:
            continue
        container = (message.get("container-title") or [""])[0]
        date = lib.date_from_parts(message.get("published", {}).get("date-parts"))
        out.append(make_candidate(
            lib.id_for_doi(doi), "paper", lib.clean_markup(title), crossref_author_list(message),
            lib.clean_markup(container), date, "https://doi.org/" + doi, doi,
            label, message.get("abstract", ""), [theme] if theme else []))
    stats["seen"] += len(items)
    return out


def harvest_crossref_themes(since, limit, stats):
    themes = lib.profile().get("themes", [])
    rows = []
    for theme in themes:
        params = {
            "query": ",".join(theme.get("keywords", [])[:4]),
            "filter": "from-pub-date:%s,type:journal-article" % since,
            "rows": str(limit),
            "select": "DOI,title,author,container-title,published,abstract",
            "mailto": lib.MAILTO,
        }
        data = lib.fetch_json("https://api.crossref.org/works?" + urllib.parse.urlencode(params))
        rows += crossref_rows(data["message"]["items"], "Crossref topic: " + theme["name"], theme["code"], stats)
    return rows, "%d theme queries" % len(themes)


def harvest_crossref_journals(since, limit, stats):
    watch = [j for j in lib.profile().get("journalWatch", []) if j.get("on") and j.get("issn")]
    rows = []
    swept = 0
    for entry in watch:
        params = {
            "filter": "from-pub-date:%s" % since,
            "rows": str(limit),
            "sort": "published",
            "order": "desc",
            "select": "DOI,title,author,published,container-title,abstract",
            "mailto": lib.MAILTO,
        }
        url = "https://api.crossref.org/journals/%s/works?%s" % (entry["issn"], urllib.parse.urlencode(params))
        try:
            data = lib.fetch_json(url)
        except Exception as exc:
            stats["failed_journals"].append("%s: %s" % (entry["name"], str(exc)[:50]))
            continue
        swept += 1
        rows += crossref_rows(data["message"]["items"], "Journal watch: " + entry["name"], "", stats)
    return rows, "%d of %d journals swept" % (swept, len(watch))


# ---------------------------------------------------------------- OpenAlex
def harvest_openalex(since, limit, stats):
    profile = lib.profile()
    config = profile.get("consensus", {})
    themes = profile.get("themes", [])
    if not themes:
        return [], "no themes in the profile"
    if not config.get("on"):
        return [], "off in the profile"
    per_week = max(1, int(config.get("perWeek", 2) or 2))
    start = int(config.get("nextTheme", 0) or 0)
    chosen = [themes[(start + step) % len(themes)] for step in range(min(per_week, len(themes)))]
    rows = []
    used = []
    for theme in chosen:
        question = QUESTIONS.get(theme["code"], theme["name"]).replace("?", "").replace("*", "")
        params = {
            "filter": "from_publication_date:%s,type:article" % since,
            "search": question,
            "per-page": str(limit),
            "select": "id,doi,title,publication_date,authorships,primary_location,abstract_inverted_index,language",
            "mailto": lib.MAILTO,
        }
        data = lib.fetch_json("https://api.openalex.org/works?" + urllib.parse.urlencode(params))
        used.append(theme["code"])
        stats["seen"] += len(data.get("results", []))
        for work in data.get("results", []):
            title = work.get("title") or ""
            if not title:
                continue
            doi = (work.get("doi") or "").replace("https://doi.org/", "").strip()
            doc_id = lib.id_for_doi(doi) if doi else lib.id_for_openalex(work.get("id", ""))
            names = [a.get("author", {}).get("display_name", "") for a in (work.get("authorships") or [])]
            names = [n for n in names if n]
            authors = ", ".join(names[:3]) + (" et al." if len(names) > 3 else "")
            venue = ((work.get("primary_location") or {}).get("source") or {}).get("display_name") or ""
            rows.append(make_candidate(
                doc_id, "paper", lib.clean_markup(title), authors, venue,
                work.get("publication_date") or "",
                "https://doi.org/" + doi if doi else work.get("id", ""), doi,
                "OpenAlex: " + theme["name"], lib.openalex_abstract(work.get("abstract_inverted_index")),
                [theme["code"]], lang=work.get("language") or "", extra={"openalex": work.get("id", "")}))
    return rows, "themes: " + ", ".join(used)


# ---------------------------------------------------------------- Bluesky
def harvest_bluesky(since, limit, stats):
    config = lib.profile().get("bluesky", {})
    accounts = list(config.get("accounts", []))[: int(config.get("maxAccounts", 40) or 40)]
    rows = []
    for handle in accounts:
        url = "https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed?actor=%s&limit=%d" % (
            urllib.parse.quote(handle), min(limit + 10, 50))
        data = lib.fetch_json(url)
        stats["seen"] += len(data.get("feed", []))
        for entry in data.get("feed", []):
            post = entry.get("post", {})
            record = post.get("record", {})
            created = (record.get("createdAt") or "")[:10]
            if created and created < since:
                continue
            text = record.get("text") or ""
            if not text:
                continue
            rkey = post.get("uri", "").rstrip("/").split("/")[-1]
            post_url = "https://bsky.app/profile/%s/post/%s" % (handle, rkey)
            doi = lib.doi_from_text(text)
            if doi:
                try:
                    message = lib.fetch_json("https://api.crossref.org/works/%s?mailto=%s" % (doi, lib.MAILTO))["message"]
                    rows.append(make_candidate(
                        lib.id_for_doi(doi), "paper", lib.clean_markup((message.get("title") or [""])[0]),
                        crossref_author_list(message), lib.clean_markup((message.get("container-title") or [""])[0]),
                        lib.date_from_parts(message.get("published", {}).get("date-parts")),
                        "https://doi.org/" + doi, doi, "Bluesky: @" + handle,
                        message.get("abstract", ""), [], extra={"post": post_url}))
                    continue
                except Exception:
                    pass
            rows.append(make_candidate(
                lib.id_for_discourse("bs-", post_url), "discourse", lib.shorten(text, 120),
                "Bluesky", "Bluesky", created, post_url, "", "Bluesky: @" + handle, text, []))
    return rows, "%d accounts" % len(accounts)


# ---------------------------------------------------------------- ScienceGuide
def harvest_scienceguide(since, limit, stats):
    html = lib.fetch_text("https://www.scienceguide.nl/artikel-type/nieuws/")
    pattern = re.compile(r'href="(https://www\.scienceguide\.nl/(\d{4})/(\d{2})/[^"#?]+)"[^>]*>(.{0,400}?)</a>', re.S)
    rows = []
    seen = set()
    for match in pattern.finditer(html):
        url = match.group(1)
        month = "%s-%s" % (match.group(2), match.group(3))
        title = lib.clean_markup(re.sub(r"<[^>]+>", " ", match.group(4)))
        if url in seen or len(title) < 25:
            continue
        seen.add(url)
        if month < since[:7]:
            continue
        rows.append(make_candidate(
            lib.id_for_discourse("sg-", url), "discourse", title, "ScienceGuide", "ScienceGuide",
            month, url, "", "ScienceGuide", title, [], lang="nl"))
        if len(rows) >= limit:
            break
    stats["seen"] += len(seen)
    return rows, "%d links on the news index" % len(seen)


# ---------------------------------------------------------------- RSS and Atom
def harvest_rss(since, limit, stats):
    feeds = [f for f in lib.profile().get("rssFeeds", []) if f.get("on", True) and f.get("url")]
    if not feeds:
        return [], "none configured"
    rows = []
    for feed in feeds:
        label = feed.get("label", "?")
        try:
            root = ElementTree.fromstring(lib.fetch_text(feed["url"]))
        except Exception as exc:
            stats["failed_journals"].append("RSS %s: %s" % (label, str(exc)[:40]))
            continue
        nodes = list(root.iter("item"))[:limit]
        for node in nodes:
            title = (node.findtext("title") or "").strip()
            link = (node.findtext("link") or "").strip()
            if not title or not link:
                continue
            date = (node.findtext("{http://purl.org/dc/elements/1.1/date}") or node.findtext("pubDate") or "")[:10]
            if date and date < since:
                continue
            rows.append(make_candidate(
                lib.id_for_discourse("rss-", link), "discourse", lib.clean_markup(title),
                label, label, date, link, "", "RSS: " + label,
                node.findtext("description") or "", []))
    return rows, "%d feeds" % len(feeds)


HARVESTERS = {
    "crossref-themes": harvest_crossref_themes,
    "crossref-journals": harvest_crossref_journals,
    "openalex": harvest_openalex,
    "bluesky": harvest_bluesky,
    "scienceguide": harvest_scienceguide,
    "rss": harvest_rss,
}

LABELS = {
    "crossref-themes": "Crossref topic search (8 themes)",
    "crossref-journals": "Journal watch (Crossref by ISSN)",
    "openalex": "OpenAlex paper search",
    "bluesky": "Bluesky",
    "scienceguide": "ScienceGuide",
    "rss": "RSS feeds",
}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Harvest candidates for the Reading Radar.")
    parser.add_argument("--since", default=None, help="first publication date, YYYY-MM-DD")
    parser.add_argument("--limit", type=int, default=20, help="maximum rows for each query")
    parser.add_argument("--source", action="append", choices=SOURCES, help="only these sources")
    parser.add_argument("--dry-run", action="store_true", help="print the result and write nothing")
    args = parser.parse_args(argv)

    last = lib.load_json(lib.DATA / "meta" / "lastRun.json", {}) or {}
    since = args.since or last.get("date") or lib.today()
    run_date = lib.today()
    known = lib.known_ids()
    stats = {"seen": 0, "new": 0, "merged": 0, "known": 0, "failed_journals": []}
    store = {}
    states = []

    for name in (args.source or list(SOURCES)):
        try:
            rows, note = HARVESTERS[name](since, args.limit, stats)
            for doc in rows:
                add(store, doc, known, stats)
            states.append({"name": LABELS[name], "status": "ok - %s, %d candidates" % (note, len(rows))})
        except Exception as exc:
            states.append({"name": LABELS[name], "status": "failed - " + str(exc)[:150]})
    if stats["failed_journals"]:
        states.append({"name": "Journal and feed detail",
                       "status": "partial - " + "; ".join(stats["failed_journals"][:8])})

    print("run date       :", run_date)
    print("window from    :", since)
    print("rows seen      :", stats["seen"])
    print("new candidates :", len(store))
    print("merged sources :", stats["merged"])
    print("already known  :", stats["known"])
    for state in states:
        print("   %-38s %s" % (state["name"], state["status"]))

    if args.dry_run:
        print("\ndry run: no file was written")
        return 0

    for doc_id, doc in sorted(store.items()):
        lib.save_json(lib.DATA / "inbox" / "items" / (doc_id + ".json"), doc)
    lib.save_json(lib.DATA / "inbox" / "run.json", {
        "date": run_date,
        "since": since,
        "sources": states,
        "counts": {"seen": stats["seen"], "candidates": len(store),
                   "merged": stats["merged"], "known": stats["known"]},
        "candidates": sorted(store.keys()),
    })
    print("\nwrote %d candidates to data/inbox/items/" % len(store))
    return 0


if __name__ == "__main__":
    sys.exit(main())
