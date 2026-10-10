# AI-assisted working drafts

Upload PDFs here using **Upload PDF** on the AI-Aided Papers page after the site is published. GitHub authentication and repository permission are required. Commit the upload; the deployment automatically lists the PDF on `ai-aided-papers.html`.

Every entry is labeled **Not fully checked**. The page states: “AI-assisted working drafts. These results have not been fully checked and may contain errors.”

This folder is separate from `preprints/` and from verified arXiv metadata in `arxiv/`. Files are not moved between sections automatically. No private manuscript is included initially.

Filenames become displayed titles. Optional metadata may be placed in `content.json` under `aiPapers`, using the exact `pdf` path `ai-papers/filename.pdf` and the same optional title, authors, version, year, updated date, and abstract fields as uploaded preprints.

To remove a draft, use **Manage AI-Aided Papers** on that page, confirm its deletion on GitHub, and commit. The draft disappears after deployment; previous file versions remain in Git history. Keep this README even when no PDFs remain.
