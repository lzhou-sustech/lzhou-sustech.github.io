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
