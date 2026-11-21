# Weekly publication news

The authorized Weekly Research and Publication Watch checks Lin Zhou's arXiv and IEEE records on Mondays at approximately 09:54 Asia/Shanghai. It updates verified publication records, this site's News event ledger, and the live GitHub Pages site. The Monday GitHub Actions job is a deterministic rebuild of those records; running that build is not itself a new publication search.

## Verify sources

Use Lin Zhou's ORCID `0000-0002-5173-320X`, SUSTech affiliation, title, coauthors, and existing records to resolve author identity. Search both newly published papers and status changes to existing papers. Do not rely only on indexed web search or DBLP.

- Check the official arXiv author API, sorted by both submission and last-update date, plus abstract pages and version histories. The author query `au:"Zhou_Lin"` also returns unrelated same-name authors; identity must be verified.
- Check IEEE Xplore and IEEE publisher-deposited Crossref records. Query Crossref by exact ORCID and use an overlapping update-date window; also search titles and author/coauthor combinations because not every record contains an ORCID. Crossref can be read with ordinary Python `urllib.request` if a web-search open cannot retrieve its API.
- Deduplicate by DOI, arXiv ID, title, authors, and version lineage. Similar titles are insufficient to merge papers. The continuous-sequence TIT paper and the sole-author low-complexity sequence-matching preprint are different papers.
- Use actual arXiv submission/revision dates and publisher publication dates. Crossref `created`, `deposited`, and `indexed` timestamps, license-start defaults, conference dates, and provisional pages are not evidence of an exact first-online date.
- If a publisher record is verified but its online date is unavailable, use `publication-verified` and the date of the first verified website announcement. Keep that date fixed on later checks. Do not infer Early Access, a final volume/issue, pagination, or corresponding authorship when the source does not specify it.

## Update records and News

Keep the six-page navigation and the consolidated Preprints page. The former AI-Aided Papers page remains retired. Only the owner's verified work belongs in the website; related-literature alerts do not authorize publishing other researchers' papers or private research details.

Update the canonical citation in `publications.html` or `preprints.html` and its JSON metadata. Preserve stable publication IDs and historical submission/upload dates. Keep a published paper's arXiv link where a counterpart is verified. Add magazine articles with `data-type="magazine"`; do not add them to the journal count.

Record announcements in `publication-news.json`:

- `schemaVersion`: `1`.
- `lastChecked`: the actual date of a completed source check, `YYYY-MM-DD`. Advance it even when a completed check finds no new paper. Do not advance it for a build alone or an incomplete/failed check.
- `events`: stable unique event `id`, canonical `recordId`, `kind`, `date`, `title`, `url`, and nonempty primary `sources`; include `venue` for publications.
- Kinds: `arxiv-submission`, `arxiv-revision`, `publication-online`, `publication-issue`, `publication-verified`, or `accepted`.
- Source dates may be `YYYY-MM-DD`, `YYYY-MM`, or `YYYY` and must retain that precision. A `publication-verified` event requires a full check date, may include `publicationYear`, and is visibly labeled as verification rather than publication date.
- Replace a `publication-verified` event with `publication-online` when its exact source date is later confirmed; do not announce the same online publication twice.
- Keep all earlier events. Deduplicate arXiv submission events against the citation records. Accepted/forthcoming status must stay distinct from online publication.

If source access is partial, retain the last completed check date and report the limitation in the task result. Individual unavailable exact dates do not prevent a completed check when publisher-deposited evidence establishes the underlying record; preserve the uncertainty explicitly.

## Rebuild, publish, and verify

Read current `main` before editing. Run:

```sh
python3 -m unittest -v test_publication_news.py
python3 maintain_public_site.py
python3 update_page_presentation.py
```

Check that News contains the new events in chronological order, both publication maps agree with the citations, and the selected TIT list and navigation remain consistent. Re-running the presentation script should produce no further changes. Commit the source records, ledger, and generated HTML through authorized GitHub access. Use an expected-head check to avoid overwriting concurrent updates.

Verify the maintenance and GitHub Pages workflows and the live homepage before reporting publication as complete. If a write, build, or deployment fails, report the failure and retain the prepared changes for recovery. Do not substitute a successful build for a successful source check or a successful deployment.
