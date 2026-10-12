# Panel score, round 2

Reviewers: 8 (P1, P2, P3, P4, P5, P6, P7, P8)
Cells: 200 | passes: 196 | Wilson 95% lower bound: 0.9497 (gate 0.95)

## The gate

| Gate | Requirement | Result |
| --- | --- | --- |
| G1a | no open S1 defect | pass |
| G1b | no S2 defect on a core-loop feature | FAIL (3) |
| G2a | 7 of 8 reviewers accept every feature | FAIL (1 features) |
| G2b | 8 of 8 on the eight core features | pass |
| G3 | pooled lower bound 0.95 or more | FAIL at 0.9497 |
| G4 | median usefulness 4 or more on every feature | FAIL (1 features) |

**Verdict: NOT YET**

The cells that hold the gate:
- F12 (See what the radar learned from the triage): accepted by 4 of 8 - refused by P1, P2, P6, P7
- the pooled bound needs about 190 passes of 200; this round has 196

## Every feature

| Feature | Core | Accepted | Median usefulness | Refused by |
| --- | --- | --- | --- | --- |
| F01 Open the radar and see the state of the week | yes | 8 of 8 | 5.0 | - |
| F02 Reach the items that the digest names |  | 8 of 8 | 4.0 | - |
| F03 See the must-read set of the run |  | 8 of 8 | 4.0 | - |
| F04 Browse the whole collection | yes | 8 of 8 | 4.0 | - |
| F05 Filter by theme, status, kind, run and score |  | 8 of 8 | 4.0 | - |
| F06 Search the collection | yes | 8 of 8 | 4.0 | - |
| F07 Order the list for the task at hand |  | 8 of 8 | 4.0 | - |
| F08 Open one item and read its record | yes | 8 of 8 | 4.0 | - |
| F09 See the abstract that the why was written fr | yes | 8 of 8 | 4.0 | - |
| F10 See the provenance of the record |  | 8 of 8 | 4.0 | - |
| F11 Mark an item keep, maybe or skip | yes | 8 of 8 | 4.0 | - |
| F12 See what the radar learned from the triage |  | 4 of 8 | 2.5 | P1, P2, P6, P7 |
| F13 See the coverage of the journal watch |  | 8 of 8 | 4.0 | - |
| F14 See which sources failed |  | 8 of 8 | 4.0 | - |
| F15 See that the data is stale |  | 8 of 8 | 4.0 | - |
| F16 See the wiki state of an item | yes | 8 of 8 | 4.0 | - |
| F17 Follow an item into the wiki |  | 8 of 8 | 4.0 | - |
| F18 Correct or repeat a wiki note |  | 8 of 8 | 4.0 | - |
| F19 Carry thinker candidates into the note |  | 8 of 8 | 4.0 | - |
| F20 Browse the roots documents |  | 8 of 8 | 4.5 | - |
| F21 Start a roots trace from an item |  | 8 of 8 | 4.0 | - |
| F22 See the queue of roots drafts |  | 8 of 8 | 4.0 | - |
| F23 Browse and judge the candidate queue | yes | 8 of 8 | 4.0 | - |
| F24 Act on the health advice |  | 8 of 8 | 4.0 | - |
| F25 Run and inspect the weekly cycle |  | 8 of 8 | 4.0 | - |

## S1 findings (0)


## S2 findings (9)

- **F12** My decisions are counted but not used. The calibration card names a source that earns no keep, and nothing follows from it.
- **F23** I can read and mark the queue, but a candidate I like still needs `promote.py`, a judgement file and a score. The queue is where the work is
- **F12** No relevance feedback reaches anything. The calibration view computes what the reader kept and skipped, and no weight, filter or ranking fol
- **F23** The queue can be read and marked but not promoted, so the 213 candidates cannot become items without leaving the page.
- **F18** A rewrite replaces the note in place. The vault is not under version control, and the note itself records no change.
- **F08** The selected state is carried by a background shadow and by `aria-pressed`. The visual mark is weaker than the semantic one.
- **F12** Decisions are stored and displayed, never consumed. No weight, exclusion or score reads them.
- **F12** The radar knows what I skipped and does nothing with it. In a personal watch, that is the one feature that saves time every week.
- **F25** The task still pushes unattended to a public repository. The validator guards the schema and the policy, not the taste of the content.

## S3 findings (17)

- **F09** Where no abstract exists (about a third of the collection) the reason rests on a title, and the record says so honestly. That is right, but 
- **F02** The digest now lists the items it names, which is what I asked for. The prose still does not link in place.
- **F13** Theme queries remain a sample of ten relevance-ranked rows. That is a reasonable watch, but it is not coverage, and the report does not dist
- **F05** The theme filter is still single-valued.
- **F09** 55 of 160 items have no abstract from Crossref or OpenAlex. Their reasons rest on a title and the record says so.
- **F13** The journal coverage is now measured per title. Two of the twenty returned fewer rows than the journal published, which is expected with a p
- **F10** The provenance line names the abstract source and the date precision. It does not name the query that found the item.
- **F17** The back-link points at the item file in the repository, not at the radar page. A wiki reader who is not a programmer gets a JSON file.
- **F19** `radar_theme_names` is one string of names. A pipeline that wants them as a list must split on commas, and a name with a comma would break.
- **F09** A long abstract in a two-column grid is a heavy block on a phone.
- **F23** Each queue row holds three buttons plus a link, so a keyboard user needs four tab stops per row and 800 for the list.
- **F25** `sourceHistory.json` keeps 52 entries and nothing reads it. A streak is recorded but not shown.
- **F23** The bundle carries 300 candidates and reports the cap. The queue rule drops a candidate after four runs or thirty days, and the drop list is
- **F07** The score distribution still clusters: 30 items at 5 in the earlier collection, 149 items undecided.
- **F05** Theme tagging is thin: a single theme on a quarter of the items.
- **F25** The log is one file per day with no rotation and no summary, so a year of runs is a folder of text.
- **F15** The staleness rule is ten days and lives in the page. A run that fails while the data is fresh (a same-day failure) shows no banner.

## Change since round 1

- lower bound: 0.644 to 0.950
- S1 findings: 15 to 0
- features below the floor: 14 to 1
- features below the quality median: 16 to 1

