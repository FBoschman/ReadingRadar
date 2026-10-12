# Panel score, round 1

Reviewers: 8 (P1, P2, P3, P4, P5, P6, P7, P8)
Cells: 200 | passes: 142 | Wilson 95% lower bound: 0.6436 (gate 0.95)

## The gate

| Gate | Requirement | Result |
| --- | --- | --- |
| G1a | no open S1 defect | FAIL (15) |
| G1b | no S2 defect on a core-loop feature | FAIL (4) |
| G2a | 7 of 8 reviewers accept every feature | FAIL (14 features) |
| G2b | 8 of 8 on the eight core features | FAIL (8 features) |
| G3 | pooled lower bound 0.95 or more | FAIL at 0.6436 |
| G4 | median usefulness 4 or more on every feature | FAIL (16 features) |

**Verdict: NOT YET**

The cells that hold the gate:
- F03 (See the must-read set of the run): accepted by 6 of 8 - refused by P3, P7
- F04 (Browse the whole collection): accepted by 5 of 8 - refused by P2, P5, P6
- F06 (Search the collection): accepted by 4 of 8 - refused by P1, P2, P3, P6
- F09 (See the abstract that the why was written from): accepted by 1 of 8 - refused by P1, P2, P3, P4, P5, P6, P7
- F10 (See the provenance of the record): accepted by 3 of 8 - refused by P1, P2, P3, P4, P6
- F11 (Mark an item keep, maybe or skip): accepted by 3 of 8 - refused by P1, P2, P4, P5, P6
- F12 (See what the radar learned from the triage): accepted by 4 of 8 - refused by P1, P2, P4, P7
- F13 (See the coverage of the journal watch): accepted by 6 of 8 - refused by P2, P3
- F14 (See which sources failed): accepted by 6 of 8 - refused by P3, P8
- F16 (See the wiki state of an item): accepted by 6 of 8 - refused by P1, P4
- F17 (Follow an item into the wiki): accepted by 6 of 8 - refused by P1, P4
- F19 (Carry thinker candidates into the note): accepted by 6 of 8 - refused by P3, P4
- F23 (Browse and judge the candidate queue): accepted by 1 of 8 - refused by P1, P2, P3, P4, P5, P7, P8
- F25 (Run and inspect the weekly cycle): accepted by 6 of 8 - refused by P6, P8
- the pooled bound needs about 190 passes of 200; this round has 142

## Every feature

| Feature | Core | Accepted | Median usefulness | Refused by |
| --- | --- | --- | --- | --- |
| F01 Open the radar and see the state of the week | yes | 7 of 8 | 5.0 | P5 |
| F02 Reach the items that the digest names |  | 7 of 8 | 3.0 | P1 |
| F03 See the must-read set of the run |  | 6 of 8 | 4.0 | P3, P7 |
| F04 Browse the whole collection | yes | 5 of 8 | 4.0 | P2, P5, P6 |
| F05 Filter by theme, status, kind, run and score |  | 8 of 8 | 4.0 | - |
| F06 Search the collection | yes | 4 of 8 | 3.0 | P1, P2, P3, P6 |
| F07 Order the list for the task at hand |  | 7 of 8 | 3.5 | P2 |
| F08 Open one item and read its record | yes | 7 of 8 | 4.0 | P5 |
| F09 See the abstract that the why was written fr | yes | 1 of 8 | 2.0 | P1, P2, P3, P4, P5, P6, P7 |
| F10 See the provenance of the record |  | 3 of 8 | 2.0 | P1, P2, P3, P4, P6 |
| F11 Mark an item keep, maybe or skip | yes | 3 of 8 | 2.5 | P1, P2, P4, P5, P6 |
| F12 See what the radar learned from the triage |  | 4 of 8 | 2.5 | P1, P2, P4, P7 |
| F13 See the coverage of the journal watch |  | 6 of 8 | 3.5 | P2, P3 |
| F14 See which sources failed |  | 6 of 8 | 4.0 | P3, P8 |
| F15 See that the data is stale |  | 7 of 8 | 4.0 | P8 |
| F16 See the wiki state of an item | yes | 6 of 8 | 3.0 | P1, P4 |
| F17 Follow an item into the wiki |  | 6 of 8 | 3.0 | P1, P4 |
| F18 Correct or repeat a wiki note |  | 7 of 8 | 3.0 | P4 |
| F19 Carry thinker candidates into the note |  | 6 of 8 | 3.0 | P3, P4 |
| F20 Browse the roots documents |  | 8 of 8 | 4.0 | - |
| F21 Start a roots trace from an item |  | 7 of 8 | 3.0 | P1 |
| F22 See the queue of roots drafts |  | 7 of 8 | 3.5 | P1 |
| F23 Browse and judge the candidate queue | yes | 1 of 8 | 3.0 | P1, P2, P3, P4, P5, P7, P8 |
| F24 Act on the health advice |  | 7 of 8 | 4.0 | P5 |
| F25 Run and inspect the weekly cycle |  | 6 of 8 | 3.5 | P6, P8 |

## S1 findings (15)

- **F11** There is no way to mark an item keep, maybe or skip, anywhere. The calibration the whole scoring method depends on cannot happen.
- **F09** No item carries an abstract, so I cannot check the reason against the source. 138 of 213 candidates do carry one.
- **F23** The 213 candidates of the queue cannot be read in the radar. The Health card shows a count.
- **F13** Recall of the harvest is 29% (115 of 395). The cause is `--limit 10` per journal, which truncates the query before relevance is considered.
- **F06** The kept share of 14% is not evidence of strictness: it is the effect of a thin shortlist. A filter cannot recover a paper the query never r
- **F04** The discourse id rule is not deterministic, so one article entered twice.
- **F10** No record shows whether the `why` was written from an abstract or from a title alone, and no record shows how exact the date is. Citation de
- **F16** The radar never shows whether a note exists for an item. 26 notes were written this morning and the radar cannot say so.
- **F17** A note carries no identifier of the radar record, so nobody can walk from the wiki to the radar.
- **F04** The 162 item rows are `div` elements with a click handler. `tabindex` appears 0 times and `keydown` 0 times in `index.html`, so the list is 
- **F01** The radar is not published, so T10 cannot start.
- **F09** `tools/promote.py` builds the item from `ITEM_FIELDS`, which omits `abstract` and `abstractSource`. Every promoted item loses the abstract t
- **F04** The id rule for discourse is derived from the URL tail and truncated at 46 characters, so two implementations of the same rule produce two i
- **F15** If the weekly task fails, nothing tells the reader. The last run stays in `lastRun.json` and the app shows its age, but nobody opens the app
- **F23** Nothing bounds the queue. It grew from 0 to 213 in one day, and no run prunes it. The bundle carries a number, so the growth is invisible in

## S2 findings (20)

- **F16** The radar never says whether an intake note exists for an item, even though 26 notes were written this morning.
- **F02** The digest names authors in prose. No link reaches the item it discusses, so I search by hand.
- **F06** I cannot search the abstract or the themes. Searching "offloading" finds the items whose title says offloading.
- **F07** There is no order that answers "what is new since I last looked" against "what is strongest for my current paper". `run` and `score` are sep
- **F12** No relevance feedback reaches the ranker. The radar cannot learn that the reader wants fewer Dutch policy items, which is exactly the signal
- **F13** The last run swept 20 of 20 titles, and that is reported as a success, but 280 papers in the window were not returned by the queries. The co
- **F03** The collection breaks its own policy: 4 items below `minScore` 3, 15 without a caveat, and a correction notice filed as a paper.
- **F14** A failure is recorded with a reason, which is good, but the record is replaced by the next run. There is no history of a source that failed 
- **F18** A rewritten note loses the link between the old and the new version. `--rewrite` overwrites in place, which is fine for the pipeline but bad
- **F19** `xray_confidence` and `thinker_candidates` are declared in the contract and always empty. A pipeline that reads them learns to ignore them.
- **F16** The `ingested` flag is never updated, so the radar cannot tell a delivered note from a wiki page.
- **F04** The item row is announced as a group of text, not as a control, and the selected row is marked by a colour shadow only.
- **F24** When a filter changes the count, nothing announces it. A screen-reader user hears no feedback after typing in the search box.
- **F25** `validate.py` checks the shape but not the policy: it passes a collection with four items below `minScore`, fifteen items without a caveat a
- **F25** `meta/lastRun.json` is replaced by each run, so the only history of a failing source is git. That is defensible, but the document says it "i
- **F03** A correction notice is filed as a paper ("Correction: Epistemic laundering: generative AI and the naturalization..."). Corrections, errata a
- **F03** An item below the profile's own floor sits in the collection: Dutch lobby news at score 2, when `minScore` is 3.
- **F12** The reason field is uneven in quality, and nothing measures it. Two legacy items carry a reason shorter than 60 characters.
- **F25** The task pushes to a public repository unattended. The validator protects the schema, not the content, so a bad run is published before anyo
- **F25** The task runs only when the user is logged on, with "start when available". A laptop that is shut for a week loses those runs entirely: ther

## S3 findings (15)

- **F05** The theme filter is single-valued, and 41 items carry one theme only, which suggests under-tagging rather than a clean theme.
- **F06** The relevance sample holds a correction notice as if it were a paper ("Correction: Epistemic laundering...").
- **F25** There is no export. A librarian cannot take the record into a reference manager.
- **F19** The frontmatter carries `xray_confidence` and `thinker_candidates` and both are empty on every note, so a downstream pipeline would read a p
- **F19** The note does not record which theme *names* it belongs to, only the codes, so a wiki reader sees `[par, dec]` with no legend.
- **F08** There is no explicit focus style, so keyboard focus depends on the browser default and on the OS.
- **F09** The abstract would be a long text block in a two-column grid; on a phone that becomes a very long scroll with the metadata above it.
- **F25** The bundle grows with the collection and the queue; at 213 candidates it is 304 KB, which is fine, but nothing bounds it.
- **F10** `MANIFEST.json` is now generated, which is good, but it silently changed meaning: `exportedAt` used to mean the cloud export, and it now mea
- **F07** The scores cluster high: 30 items at 5 and 68 at 4 of 162. A 0-to-5 scale in which 60% of the corpus is 4 or 5 cannot separate a must-read f
- **F05** Theme tagging is thin: 41 items carry one theme, and the sample suggests the single code is often the topic of the venue rather than the arg
- **F23** I cannot see the 213 candidates, so I cannot tell whether the two false-positive kinds are rare or common. My 10% figure rests on twenty ite
- **F25** The log grows without rotation and is written with a fixed name per day.
- **F25** The vault path, the mail address and the thesis of the polite pool are hard-coded, so the kit is bound to this machine and this reader.
- **F14** A source that fails is recorded, but the record is one run deep, so a streak (Crossref down for three weeks) looks like a single event.

