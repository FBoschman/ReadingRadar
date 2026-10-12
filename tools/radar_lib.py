"""Shared functions for the Reading Radar local cycle.

This module holds the id rules from SCHEMA.md, the file helpers and one network helper.
It uses the standard library only. No package install is needed.

Rules that every caller must obey:
    - Never overwrite a document that exists.
    - One request each second, with the reader's email address on Crossref and OpenAlex calls.
    - A failed source is recorded with a short reason. It is never hidden.
"""
import datetime
import json
import pathlib
import re
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
MAILTO = "fb0068674@windesheim.nl"
USER_AGENT = "reading-radar/1.0 (mailto:" + MAILTO + ")"
PAUSE_SECONDS = 1.0
_last_call = [0.0]


# ---------------------------------------------------------------- time and files
def today():
    return datetime.date.today().isoformat()


def stamp():
    return datetime.datetime.now().replace(microsecond=0).isoformat()


def load_json(path, default=None):
    """Read one JSON document. A byte-order mark is tolerated: a reader who saves the actions file
    from Notepad or from PowerShell gets one, and the browser download does not. See the field note of
    12 October 2026 in tools/panel/CONSOLIDATION.md."""
    path = pathlib.Path(path)
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save_json(path, doc, sort_keys=False):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=sort_keys)
    path.write_text(text + "\n", encoding="utf-8", newline="\n")


def profile():
    return load_json(DATA / "meta" / "profile.json", {})


def collection(name):
    folder = DATA / name
    if not folder.is_dir():
        return {}
    return {path.stem: load_json(path) for path in sorted(folder.glob("*.json"))}


def write_document(collection_name, doc_id, doc):
    """Write one document into a collection. Refuse to overwrite an existing one."""
    path = DATA / collection_name / (doc_id + ".json")
    if path.exists():
        raise FileExistsError("document exists, not overwritten: " + str(path))
    save_json(path, doc)


def known_ids():
    """Every item id that already exists, in the collection and in the inbox."""
    ids = set(collection("items").keys())
    inbox = DATA / "inbox" / "items"
    if inbox.is_dir():
        ids |= {path.stem for path in inbox.glob("*.json")}
    return ids


def known_keys():
    """The normalised URLs and titles that already exist, so the same article cannot enter twice.

    The id rules are deterministic going forward, but records written by an earlier implementation can
    still collide through a different id. This guard catches that case.
    """
    urls = set()
    titles = set()
    for doc in list(collection("items").values()):
        if doc.get("url"):
            urls.add(normalise_url(doc["url"]))
        if len(str(doc.get("title") or "")) > 25:
            titles.add(re.sub(r"[^a-z0-9]+", " ", str(doc["title"]).lower()).strip())
    inbox = DATA / "inbox" / "items"
    if inbox.is_dir():
        for path in inbox.glob("*.json"):
            doc = load_json(path, {}) or {}
            if doc.get("url"):
                urls.add(normalise_url(doc["url"]))
            if len(str(doc.get("title") or "")) > 25:
                titles.add(re.sub(r"[^a-z0-9]+", " ", str(doc["title"]).lower()).strip())
    return urls, titles


# ---------------------------------------------------------------- the id rules
def id_for_doi(doi):
    """SCHEMA.md: 'doi_' + the DOI, with every character outside [A-Za-z0-9_-.~:@+] as '_'."""
    return "doi_" + re.sub(r"[^A-Za-z0-9_\-\.~:@+]", "_", str(doi).strip())


def id_for_openalex(work_id):
    """A work with no DOI. OpenAlex gives https://openalex.org/W123. Keep the short form."""
    return "oa_" + str(work_id).rstrip("/").split("/")[-1]


def slug(text, limit=46):
    text = re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")
    return text[:limit].strip("-")


def normalise_url(url):
    """A URL reduced to what identifies the article, so the same page cannot enter twice."""
    text = str(url or "").strip().lower()
    text = re.sub(r"^https?://", "", text)
    text = text.split("#")[0].split("?")[0]
    return text.rstrip("/")


def id_for_url(url):
    """A deterministic id for discourse: a hash of the normalised URL, not a truncated slug."""
    import hashlib
    return "sl-" + hashlib.sha1(normalise_url(url).encode("utf-8")).hexdigest()[:10]


NOISE_TITLES = ("correction", "erratum", "retraction", "author correction",
                "publisher correction", "corrigendum", "editorial board")


def is_noise_title(title):
    """Corrections, errata and retractions arrive with the type of an article. Drop them by title."""
    words = str(title or "").strip().lower()
    for prefix in NOISE_TITLES:
        if words.startswith(prefix):
            return True
    return False


def id_for_discourse(prefix, url):
    tail = str(url).rstrip("/").split("/")[-1]
    return prefix + slug(tail or url)


# ---------------------------------------------------------------- the network
def fetch(url, accept="application/json", retries=2, timeout=30):
    """One GET. A pause in front, two retries, a short backoff. Raises on a hard failure."""
    for attempt in range(retries + 1):
        wait = PAUSE_SECONDS - (time.time() - _last_call[0])
        if wait > 0:
            time.sleep(wait)
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                _last_call[0] = time.time()
                return response.read()
        except urllib.error.HTTPError as exc:
            _last_call[0] = time.time()
            if exc.code in (429, 500, 502, 503) and attempt < retries:
                time.sleep(5 * (attempt + 1))
                continue
            raise
        except Exception:
            _last_call[0] = time.time()
            if attempt < retries:
                time.sleep(3 * (attempt + 1))
                continue
            raise
    raise RuntimeError("unreachable")


def fetch_json(url, **kwargs):
    return json.loads(fetch(url, **kwargs).decode("utf-8", "replace"))


def fetch_text(url, **kwargs):
    return fetch(url, accept="text/html,*/*", **kwargs).decode("utf-8", "replace")


# ---------------------------------------------------------------- text helpers
def clean_markup(text):
    """Crossref sends an abstract with XML tags. Remove the tags and the entities."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", str(text))
    for entity, char in (("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'), ("&#x2019;", "'")):
        text = text.replace(entity, char)
    return re.sub(r"\s+", " ", text).strip()


def openalex_abstract(index):
    """OpenAlex sends an inverted index. Rebuild the text in the right order."""
    if not index:
        return ""
    places = {}
    for word, positions in index.items():
        for position in positions:
            places[position] = word
    return " ".join(places[key] for key in sorted(places))


def shorten(text, limit=400):
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return cut + "..."


def date_from_parts(parts):
    """Crossref gives [[2026, 10, 5]]. Return YYYY-MM-DD or YYYY-MM."""
    if not parts or not parts[0]:
        return ""
    year = parts[0][0]
    month = parts[0][1] if len(parts[0]) > 1 else None
    day = parts[0][2] if len(parts[0]) > 2 else None
    if month and day:
        return "%04d-%02d-%02d" % (year, month, day)
    if month:
        return "%04d-%02d" % (year, month)
    return str(year)


def doi_from_text(text):
    match = re.search(r"10\.\d{4,9}/[^\s\"'<>]+", str(text or ""))
    if not match:
        return ""
    return match.group(0).rstrip(".,;)")
