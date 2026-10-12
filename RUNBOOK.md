# RUNBOOK — the weekly cycle

Unattended. Never ask a question mid-run; make the reasonable call and record it in
`meta/lastRun.notes`.

---

## The local route (used from 12 October 2026)

The weekly task in the cloud cannot fetch any API: a scheduled run may only load a URL that already
appeared word for word in a web-search result. Every API and every constructed query URL is refused.
That is why two runs in a row were thin. The cycle therefore runs on the reader's own machine, where
every source works.

The steps of one weekly cycle, in order:

1. **Harvest.** `python tools/harvest.py --since <the last run date> --limit 10`
   It writes candidates to `data/inbox/items/` and the state of every source to `data/inbox/run.json`.
   Use a wider `--since` only as a catch-up, and say so in the digest.
2. **Enrich.** `python tools/enrich.py --limit 60`
   Crossref has no abstract for every publisher. This step fills the gap from OpenAlex by DOI, so that
   the judgement pass can write an honest caveat.
3. **Queue.** `python tools/queue.py --min-match 2 --limit 40`
   A ranked shortlist. The rank is a hint from the theme keywords, not a score.
4. **Judge.** Write `data/inbox/judgement.json` and run `python tools/promote.py`.
   Score each candidate 0 to 5, keep the items at or above `meta/profile.minScore`, and add one or two
   wildcards. Cap: 30 items for one run. Every item needs a `why` and a `caveat`. This step is a
   decision by a person or an agent. A script cannot do it.
5. **Roots.** `python tools/lineage.py --top 5` (or `--queue`), then write
   `data/inbox/lineage-judgement.json` and run `python tools/complete_lineage.py`.
   The narrative and the strands may only name works that appear in `refs`.
6. **Digest.** Write `data/meta/digest.json`: the week, the headline, three or four paragraphs, three
   to five must-read ids from this run.
7. **Run log and profile.** Write `data/meta/lastRun.json` with one line for each source, and update
   `meta/profile.json` where the run changed the configuration (the journal states, the theme
   rotation, the Bluesky state).
8. **Vault.** `python tools/vault_notes.py`
   Intake notes for the items at score 4 and higher go to `raw/articles`. Never write in `wiki/`, and
   never touch `raw/fieldwork` or `raw/legacy`.
9. **Check and publish.** `python tools/validate.py`, then `python tools/build_bundle.py`, then commit
   and push. The dashboard reads the bundle.

`python tools/weekly.py` runs steps 1, 2, 7 and 9 in one command. It does not run the judgement pass,
the roots narrative or the digest, because those are decisions. The task catches up on a missed start.

## Step 1 — Load state

1. Read `meta/profile`. This is configuration.
2. Read `meta/lastRun` for the previous run date (`since`) and which sources failed last time.
   Do not retry a source that failed for a structural reason — read `BLOCKERS.md` first.
3. List `items` (limit 1000). You need two things: the set of existing ids, and the titles of
   everything marked `keep`, `maybe` and `skip` as scoring calibration.
4. List `lineageRequests` and the ids in `lineage`.

---

## Step 2 — Harvest

Collect anything published since `since`. Pace web fetches: roughly 20 s between calls, 60 s after
a rate-limit response. Add `&mailto=<the reader's email>` to every Crossref URL.

### 2a. Topic search — one query per theme

```
https://api.crossref.org/works
  ?query=<the theme's keywords>
  &filter=from-pub-date:<since>,type:journal-article
  &rows=20
  &select=DOI,title,author,container-title,published,abstract
  &mailto=<email>
```

Ask for a JSON array of `{doi, title, authors (first 3 surnames), journal, date,
abstract_first_sentence}`.

### 2b. Journal watch — every entry with `on: true`

```
https://api.crossref.org/journals/<ISSN>/works
  ?filter=from-pub-date:<since>&rows=25&sort=published&order=desc
  &select=DOI,title,author,published,abstract&mailto=<email>
```

- No ISSN on the entry? Look it up once with
  `https://api.crossref.org/journals?query=<name>&rows=3&mailto=<email>` and store the ISSN only
  if the title matches.
- ISSN returns nothing, or a different journal? Write a short reason into that entry's `status`.
- Short of time? Rotate, so every journal is covered at least every two weeks, and record which
  were skipped.

### 2c. Semantic paper search (currently the most reliable source)

Only if `consensus.on`. Run **exactly** `consensus.perWeek` searches, never more — the quota is
shared with the reader's own use.

- Take themes in order starting at `consensus.nextTheme`, wrapping around the eight.
- For each, write one natural-language research question from the theme's name, its keywords and
  the reader's angle. Example for `td`: *"How do transdisciplinary research partnerships handle
  power and knowledge integration with societal actors?"*
- Call the tool with **only** `query` and `year_min` = the year 12 months ago. No other filters.
- Fire the searches **one at a time**. Fired together, the second has hit a rate limit.
- Keep only papers published in the last 12 months that are not already in `items`. Where the tool
  returns a year but no month, say so in the `caveat` rather than dropping a strong candidate.
- Use the paper URL the tool returns when there is no DOI.
- On a quota or rate-limit message: stop searching, record the message in `meta/lastRun.sources`,
  do not retry.
- Afterwards set `consensus.nextTheme` to the next unused index, and record which themes were
  searched in `meta/lastRun.notes`.

### 2d. RSS feeds

Fetch each `rssFeeds` url, ask for items published since `since` as
`{title, link, date, authors, summary}`. Set each entry's `status` to `"ok"` or a short reason
(`"blocked by robots.txt"`, `"not a feed"`, `"needs login"`). An item whose link contains a DOI is
a paper; otherwise it is discourse.

### 2e. Bluesky — public data only, never sign in

Account set = `bluesky.accounts` plus the members of the reader's list named `bluesky.listName`.

```
https://public.api.bsky.app/xrpc/app.bsky.graph.getLists?actor=<bluesky.handle>
https://public.api.bsky.app/xrpc/app.bsky.graph.getList?list=<list uri>&limit=100
https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed?actor=<handle>&limit=30&filter=posts_no_replies
```

Cap at `bluesky.maxAccounts` (40). Keep posts created since `since` that link to a paper, a call or
an event, or carry substantial discussion on the themes. Skip jokes, personal posts and general
news. A post linking to a DOI or publisher page becomes a paper item (resolve the metadata);
otherwise a discourse item with `title` = first sentence of the post, `authors` =
`Display Name (@handle)`, `venue` = `"Bluesky"`,
`url` = `https://bsky.app/profile/<handle>/post/<rkey>`, `source` = `"Bluesky: @handle"`.
Set `bluesky.status` to `""` on success or a short reason on failure.

### 2f. Discourse

`https://www.scienceguide.nl/` — recent articles on Dutch higher education and research policy.
The news index is at `https://www.scienceguide.nl/artikel-type/nieuws/`.

### 2g. Calls and events

A couple of searches across Regieorgaan SIA, NRO, CARN, ITD Alliance and EERA/ECER, plus anything
found in Bluesky posts. **Only add an event whose dates you read on the source page.**

### 2h. Write back configuration changes

One update to `meta/profile` carrying any changed `journalWatch` / `rssFeeds` status or ISSN,
the new `consensus.nextTheme`, and `bluesky.status`. Keep every other field and all the reader's
choices unchanged.

---

## Step 3 — Deduplicate and drop noise

- Build the id (see `SCHEMA.md`) and skip ids that already exist.
- Same paper from several sources → one document, all sources listed in `source`.
- Drop anything in `meta/profile.exclusions`.

---

## Step 4 — Score and write

Score 0–5 as set out in `PROJECT.md`. Keep items at or above `minScore`, plus 1–2 wildcards. Cap
at 30. Write each as a `set` into `items` with every field in the schema, `status: "new"`,
`run` = today.

Never invent metadata. Everything except `why`, `caveat`, `score` and `themes` must come from the
fetched source.

---

## Step 5 — ROOTS (intellectual lineage)

Up to five papers per run: every `lineageRequests` entry with `status: "queued"` first, then this
run's must-reads with no lineage document yet.

1. Fetch `https://api.crossref.org/works/<DOI>?mailto=<email>` and ask for `reference-count` plus
   **every** entry of the `reference` array, one per line as
   `first-author-surname|year|title|journal|DOI`, parsed from `unstructured` where needed,
   spellings copied exactly.
2. Where entries carry only DOIs, resolve them in one call:
   `https://api.crossref.org/works?filter=doi:A,doi:B,...&select=DOI,title,author,issued,container-title&mailto=<email>`
   (about 20 DOIs per call).
3. No reference list? Write `lineageRequests/<id>` with `status: "no-references"` and a note, and
   move on. Never reconstruct references from memory.
4. Group the references into 3–8 strands. See `SCHEMA.md` for `kind` values.
5. Write `lineage/<itemId>` with every field in the schema.
6. Set `lineageRequests/<id>` to `done`.

Fallback when Crossref is unreachable: the reference list printed on the publisher's own article
page can be read instead. If you do that, say so verbatim in `source` and `method`, and keep the
same constraint — strands and narrative may only name works in `refs`.

---

## Step 6 — Digest, run log, events

Write `meta/digest` and `meta/lastRun` (see `SCHEMA.md` for both), and any new `events`.

---

## Step 7 — Housekeeping

Delete `items` with `status: "skip"` whose `run` date is more than 12 weeks old, and their lineage
documents. Batch writes, 50 per batch.

---

## Step 8 — Report

Finish with a short summary: how many items added and from which source, how many papers traced,
the headline, and any source that failed. If the run is unattended, push that summary to the reader
rather than leaving it in a transcript nobody reads. Lead with the single most important sentence.
