# Public preprint PDFs

While signed in to the owning GitHub account, use Add file → Upload files in this folder to publish a PDF. Commit the upload to `main`.

The public website lists PDFs from this folder with Read PDF and Download PDF links. Upload and deletion controls are not displayed on the public website. GitHub requires repository write access to change the published site.

Use a descriptive filename. Optionally upload a JSON file with the same stem to supply a title and authors, for example `paper.pdf` and `paper.json`:

```json
{"title": "Full paper title", "authors": ["Author One", "Author Two"]}
```

To update a paper, replace its PDF with the same filename and commit the change. To remove it from the current listing, delete its PDF here and commit the change. Prior commits and downloaded copies may retain it.

IMPORTANT: This repository is public. Only upload papers you are ready to release. Files committed here are public even before the website refreshes; this folder is not private draft storage.
