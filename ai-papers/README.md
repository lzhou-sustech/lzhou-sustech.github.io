# Public AI-aided paper PDFs

While signed in to the owning GitHub account, use Add file → Upload files in this folder to publish an AI-aided working paper. Commit the upload to `main`.

The AI-Aided Papers page lists PDFs from this folder with Read PDF and Download PDF links and retains its warning that these working drafts have not been fully checked. Upload and deletion controls are not displayed on the public website. GitHub requires repository write access to change the site.

Use a descriptive filename. Optionally add a JSON file with the same stem to supply a title and authors, for example `paper.pdf` and `paper.json`:

```json
{"title": "Full paper title", "authors": ["Author One", "Author Two"]}
```

Replace a PDF with the same filename to update it. Delete the PDF to remove it from the current listing. Commit each change to `main`. Prior commits and downloaded copies may retain deleted versions.

IMPORTANT: This repository is public. Only upload papers you are ready to release. Files committed here are public even before the website refreshes; this folder is not private draft storage.

An arXiv PDF can also be linked without copying the binary into GitHub: add a JSON-only record here with `title`, `authors`, `year`, `pdfUrl` (for example `https://arxiv.org/pdf/2609.24675`), and `arxivUrl`. Include the original `submitted` date and the `updated` listing date (YYYY-MM-DD); the site links the official arXiv PDF, labels the paper as an arXiv preprint when `citationType` is set to `arXiv preprint`, and sorts AI-Aided Papers in reverse chronological order by original arXiv submission date (`submitted`), or by the documented manuscript revision date (`updated`) when no submission date exists. The website displays that date as “Submitted” or “Updated” alongside each citation. This type of record has no local PDF file.

## Date audit trail

The AI-Aided Papers page distinguishes source submission history from public website file history:

- The first website upload/first link is the earliest commit of the local PDF or the metadata-only link. GitHub's publishing workflow uses full Git history and displays these dates in China Standard Time (UTC+08).
- Every Git commit that replaces a hosted PDF is shown as a separate PDF-update date, with calendar-day duplicates collapsed. PDF history excludes citation-only edits.
- For arXiv records, `submitted` is the original arXiv submission date. Add verified subsequent arXiv revisions to `arxivRevisionDates` in ascending order. For example, `["2026-09-30"]` records v2 of an arXiv paper. Never use the date of a website update as an arXiv submission/revision date.
- The optional `siteFirstUploaded` and `pdfRevisionDates` provide fallback dates when the site is generated outside a full Git checkout. Update these fallback values when changing PDFs so non-Git builds show the same audit trail.
- The page remains sorted in reverse chronological order, using the original arXiv submission date for arXiv papers and the latest documented revision date for other working papers.

Only publicly committed file changes can be reconstructed automatically. Earlier private drafting versions cannot be dated from Git history.
