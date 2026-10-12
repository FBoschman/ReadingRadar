# PROJECT — what the Reading Radar is for

## Purpose

A weekly watch on research and professional debate across eight themes, filtered hard for one
reader. It is not a literature database and not a news feed. The test for any item is: does this
change what Ferry writes, teaches or argues this month?

Three outputs per run:

1. New scored items in `items`, each with a one-or-two-sentence `why` and one `caveat`.
2. A short `meta/digest` naming authors and linking findings to live projects.
3. Up to five `lineage` documents — the intellectual ancestry of a paper, read off its reference
   list, never from memory.

## The reader

Ferry Boschman, Lectoraat Urban Innovation, Windesheim (Dutch university of applied sciences).
Reads English, Dutch and German. Works in British English and metric units.

Live projects the radar serves — use these to judge usefulness:

- **CDC Urban Innovation course** — participatory research in public space, bachelor level.
- **Digital Twin Flevoland** — regional digital twin, multi-stakeholder.
- **CARN 2026 workshop 'Substrate Matters'** (Utrecht, 5–7 November 2026) — draws on Juarrero
  (enabling constraints, emergence), Levin, Tsing and Santos.
- **Papers on AI and Professional Criticality** — generative AI, epistemic agency, professional
  judgement.
- **FUNGI**, an Obsidian research wiki with an `/ingest` pipeline that consumes radar intake notes.

## Style for every written field

- Direct, plain, concise. No marketing register.
- British English, metric.
- Say the limitation. A `caveat` that says "none" is almost always a failure of attention.
- Never invent metadata. Title, authors, venue, date, DOI and URL come from a fetched source or
  they stay empty. Only `why`, `caveat`, `score` and `themes` are the agent's own.
- Where a field could not be verified, say so in the `caveat` rather than guessing.

## The eight themes

| Code | Theme | Keywords |
| --- | --- | --- |
| `eco` | Learning ecosystems | learning ecosystem, multi-stakeholder learning, living lab, co-creation, triple/quadruple helix, leren in ecosystemen |
| `td` | Transdisciplinary research | transdisciplinary, knowledge co-production, knowledge integration, societal actors, transdisciplinair |
| `cx` | Complexity in education | complexity theory, enabling constraints, emergence, complexiteit onderwijs |
| `dbr` | Design-based research | design-based research, educational design research, design principles, ontwerpgericht onderzoek |
| `par` | Participatory action research | participatory action research, co-design, community-based, actieonderzoek |
| `ai` | AI & curriculum | generative AI, epistemic agency, cognitive offloading, AI literacy |
| `dec` | Decolonial & epistemic justice | epistemic justice, decolonising curriculum, ecology of knowledges, pluriversal |
| `pc` | Professional criticality | critical thinking, professional judgement, onderzoekend vermogen, professioneel kritisch oordelen |

Themes are also the rotation order for the paper-search tool (index 0 = `eco` … index 7 = `pc`).
`meta/profile.consensus.nextTheme` holds the next index to use.

## Scoring

Score each surviving candidate 0–5 on four things together:

1. **Fit** with the eight themes.
2. **Novelty** — does it say something the radar does not already hold?
3. **Usefulness** for the live projects listed above.
4. **Critical angle** — does it interrogate its own framing, or just apply it?

Keep items at or above `meta/profile.minScore` (currently 3). Then add 1–2 **wildcards**: good
quality, low keyword fit, `wildcard: true`. Cap at 30 new items per run.

Calibrate against the reader's own signals, which live in the `status` field of existing items:

- `keep` — he wants more like this.
- `maybe` — borderline.
- `skip` — he does not want more like this. Read the skipped titles before scoring; they are the
  most informative part of the corpus.
- `new` — not yet triaged.

As of this export: 1 keep, 0 maybe, 10 skip, 123 new — see `data/MANIFEST.json` for the live
counts. Triage is still sparse, so weight the skip set heavily: so far it is community-service
reports with thin research design, generic AI-and-epistemic-justice think pieces, and Dutch
science-policy news with no research content.

## Exclusions (hard drop, never score)

- Community-service reports with no research design.
- Journals flagged as questionable or predatory.
- Ideological-political education (China) curriculum papers.
- Off-topic curriculum papers that merely use a theme keyword.

The live list is `meta/profile.exclusions`. Treat it as additive: when the reader marks something
`skip` for a reason that will recur, propose adding it.

## Cadence

Weekly, Monday 06:00 Europe/Amsterdam, unattended. A run that finds nothing should say so plainly
rather than padding. A run where a source fails should record the failure in
`meta/lastRun.sources` with a short reason, and tell the reader if the failure blocks the radar's
core — see `BLOCKERS.md`.

## Vault handoff (optional, currently not working)

`meta/profile.vault` describes an Obsidian wiki on the reader's own machine. Intake notes for items
scoring 4+ go to `raw/articles` as markdown with frontmatter, for the `/ingest` pipeline to pick
up. Two rules are absolute: never write or edit anything under `wiki/`, and never touch
`raw/fieldwork` or `raw/legacy`. Cloud runs have had no file access to that machine since
5 October 2026, so notes have been delivered in chat instead.
