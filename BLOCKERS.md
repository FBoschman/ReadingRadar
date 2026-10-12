# BLOCKERS — what fails, and what works instead

State as of 12 October 2026, after two consecutive runs with the main sources down. Read this
before harvesting; it is the difference between a thin run and a wasted one.

---

## 1. Fetch provenance rule (the big one)

**Symptom:** every fetch returns `PROVENANCE_REQUIRED` — "the permission request for this URL was
not answered in time and was withdrawn".

**Cause:** in a scheduled, unattended run the fetch tool will only load a URL that has already
appeared **verbatim in a web-search result**. Any other URL raises a permission prompt, and nobody
is there to answer it.

**What was tested on 12 October:**

| Test | Result |
| --- | --- |
| `api.crossref.org/works?...` direct | refused |
| Fetch the Crossref docs page first, then the API | still refused — host-level clearing does not happen |
| `link.springer.com/journal/11625/aims-and-scope` surfaced by search, then fetch `/articles` on the same host | refused — the rule is strictly **per URL**, not per host |
| `public.api.bsky.app/xrpc/...` | refused |
| Article URL printed inside a page that was itself fetched | refused — only web-search results count |

**Consequences:** no API at all (Crossref, Bluesky, any RSS feed), and no constructed query URL.
Without Crossref's `from-pub-date` filter there is no way to filter by date at harvest time.

**The fix is on the task side, not in the prompt.** Either:

- give the scheduled task a permission mode that auto-approves fetches, or
- paste the Crossref, Bluesky and feed base URLs into the stored prompt in a form the permission
  layer accepts.

Until one of those happens, every run will be degraded. Say so in the run report; do not quietly
absorb it.

---

## 2. Shell egress proxy

**Symptom:** `curl: (56) CONNECT tunnel failed, response 403` for `api.crossref.org:443`.

So the shell is not a fallback for the fetch tool. The proxy status endpoint confirms a
`connect_rejected` policy denial for that host.

---

## 3. ScienceDirect

**Symptom:** `ROBOTS_DISALLOWED` on any `sciencedirect.com` URL, including journal listing pages
that web search surfaced.

**Consequence:** all ten Elsevier titles on the journal watch are dark — Futures, Environmental
Science & Policy, Environmental Innovation and Societal Transitions, Teaching and Teacher
Education, Thinking Skills and Creativity, Learning Culture and Social Interaction, Computers and
Education: AI, Landscape and Urban Planning, Geoforum, International Journal of Educational
Research. This is separate from blocker 1 and will not be fixed by a permission change.

Partial workaround: those journals' papers do surface through the semantic paper-search tool and
through web search of repository copies.

---

## 4. Publisher sites that could not be reached

- `tandfonline.com` — five watch titles (Educational Action Research, Studies in Higher Education,
  Educational Philosophy and Theory, Higher Education Research & Development, Environmental
  Education Research).
- `journals.sagepub.com` — Action Research.
- `journals.sub.uni-hamburg.de` (EDeR) fetches fine but the issue page yields no readable table of
  contents through markdown conversion; go to individual article pages instead.
- `jprm.scholasticahq.com` (Journal of Participatory Research Methods) **is** fetchable. Put it
  first in the rotation.

---

## 5. Vault / local file access

No file access to the reader's own machine from a cloud run since 5 October 2026. Intake notes
cannot be written to the Obsidian vault; deliver them in the report instead. See
`meta/profile.vault.lastWrite`.

---

## The route that does work

Found on 12 October and worth keeping as the primary fallback:

1. **Web-search for a publisher's journal listing page.** Queries of the form
   `"<journal name> articles in press"` or `"<journal name> journal <id> articles springer"` reliably
   surface URLs such as:
   - `https://link.springer.com/journal/<id>/articles`
   - `https://link.springer.com/journal/<id>/online-first`
2. **Fetch that listing page.** It gives title, all authors and the exact publication date for
   several papers at once — far better value per fetch than article pages.
3. **Web-search the title of anything promising**, restricted to the publisher's domain. The
   result URL contains the DOI, so you get the DOI without a fetch.
4. **Fetch individual article pages** only where you need the abstract or the reference list.
   Springer article pages carry both; they truncate at about 100k characters, so for a long paper
   fetch the reference list with an offset.

This is how Sustainability Science and Systemic Practice and Action Research were swept this week,
producing 5 of the 18 items, and how the one lineage document was built.

**Honesty requirement for this route:** it has no date filter, so the window has to be widened to
"published in 2026 and not already on the radar". Every item dated before the window carries its
exact date and a `caveat` saying it is outside the week. Items where only the listing page was read
say so in the `caveat` too — the abstract was not read, so method and scope are unverified.

---

## Known candidates dropped for metadata reasons — worth chasing by hand

From the 5 October run, both strong and both on the reader's patch:

- Gulikers et al., *Transdisciplinary learning environments that stimulate co-creation and
  co-learning between students and external partners*, Humanities and Social Sciences
  Communications, 11 Dutch cases —
  https://consensus.app/papers/details/d474ff2727f85a0087235b7dafab1c8b/
- Backhaus et al., *Generalization as local and translocal embedding: interrogating governance and
  deconstructing democratization in living labs* —
  https://consensus.app/papers/details/84c8a297240258c0af72047ec3570220/

Both were dropped only because their year is 2025 and the 12-month rule could not be checked
without a month.
