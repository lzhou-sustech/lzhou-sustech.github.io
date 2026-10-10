# arXiv manuscripts

Each JSON file stores one verified public arXiv record. Unpublished manuscripts appear under Preprints, newest first. For a verified published counterpart, the generator instead appends an arXiv link to its Publications citation.

Required fields: `id` (matching the filename), `arxivId`, `title`, `authors`, `year`, `url`, and `pdfUrl`. Optional fields include ISO `submitted` and `updated` dates, `journalRef`, and retained verification evidence. Use the canonical arXiv abstract and PDF URLs. A record such as `2609.24675` has filename `arxiv-2609-24675.json` and ID `arxiv-2609-24675`.

Use `publicationStatus: published` and `publishedPublicationIds: ["the-publication-id"]` for a confirmed published counterpart, or `publicationStatus: preprint` while no counterpart is confirmed. Record supporting source URLs in `publicationStatusEvidence`. The existing `publicationIds` field is historical relationship metadata and is not used to decide publication status; a partial conference version may be related without establishing that an expanded manuscript is published.

Delete the JSON file through the homepage's Manage papers link to remove a listing. Keep this README even if all records are removed. The build does not query arXiv or restore deleted records.

For a PDF upload, use `preprints/`. AI-assisted drafts that have not been fully checked belong in `ai-papers/`, which has a separate website page and upload button.
