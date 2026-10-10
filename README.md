# Lin Zhou — academic homepage

A simple, responsive academic homepage for GitHub Pages, with a light-gray sidebar, modest serif headings, blue links, and compact publication lists. The homepage includes an academic profile, research areas, publications, preprints, appointments, education, teaching, professional service, and contact information.

## Files

- `index.html` — complete, pre-rendered homepage; readable with JavaScript disabled.
- `ai-aided-papers.html` — separate page for AI-assisted PDFs, each labeled Not fully checked.
- `arxiv/` — canonical verified arXiv metadata, one JSON file per paper.
- `ai-papers/` — AI-assisted PDFs, isolated from regular preprints.
- `styles.css` — simple academic layout, responsive navigation, accessible focus styles, and print styling.
- `script.js` — optional publication search and collection filters.
- `content.json` — editable academic profile and optional preprint metadata.
- `publications/` — one canonical JSON file per publication; delete its file to remove a listing.
- `generate.py` — standard-library Python generator that rebuilds both pages from their canonical data and discovers uploaded PDFs.
- `build.py` — builds the site and stages public files in `_site/`.
- `.github/workflows/pages.yml` — automatically builds and deploys the site after a commit to `main`.
- `preprints/` — PDFs uploaded by the site maintainer.
- `assets/lin-zhou.jpg` — portrait obtained from the SUSTech faculty website.
- `assets/favicon.svg` — LZ favicon.
- `.nojekyll` — serves the project as plain static files.

No package manager, third-party fonts, analytics, cookies, or external JavaScript is required. The included GitHub Actions workflow rebuilds and publishes the site using standard-library Python. Relative asset links support both a personal GitHub Pages site and a repository project site.

## Edit the content

1. Edit `content.json` for profile details, or the relevant file in `publications/` for a publication.
2. Commit the edited source files to `main`; the deployment automatically rebuilds the homepage.
3. For a local preview, run `python3 generate.py`.

Open `index.html` directly to inspect the page, or use your preferred static preview tool. Search and filters run locally and do not send queries anywhere.

The generator loads publications only from `publications/*.json`, preserving author order and the distinction between published and accepted work. An accepted item uses `"status": "accepted"` and displays **To appear**. Set `"selected": true` to include a work in the default Selected collection. Supported publication types are `book`, `journal`, and `conference`. Every record is rendered in the page without JavaScript; the controls provide Selected, All, Articles, Conferences, and Books views when JavaScript is available.

For a journal or magazine record (`"type": "journal"`), set `"correspondingAuthor": true` only when Lin Zhou is identified as a corresponding author. This adds a superscript asterisk directly after his name. `false`, `null`, or a missing field leaves the name unmarked; an unmarked entry does not assert that he was not a corresponding author. The field must be a boolean or `null`, and does not add markers to books, conference papers, or preprints.

Adding or removing a publication file updates the collection counts at the next automated deployment; for local changes, run the generator. The live result count is calculated automatically. Each citation ends with an explicit [IEEE] or [Publisher] link to its official publication page, followed by [arXiv] where a verified version is available.

## Remove a paper

Open **Manage papers** below the publication list. Each publication, arXiv listing, and uploaded preprint has a **Remove** link. AI-assisted PDFs have their own manager on the AI-Aided Papers page. It opens that file’s deletion page on GitHub, where you sign in, confirm the deletion, and commit it. The deployment then removes the entry from the website. Only authorized repository maintainers can delete files.

A publication is stored in `publications/<id>.json`; removing this file removes its citation. An arXiv listing is stored in `arxiv/<id>.json`; removing it removes only the local listing, not the paper on arXiv. An uploaded preprint is stored under `preprints/`; removing the PDF removes the file and its listing. This does not remove articles from a publisher or arXiv, and Git history retains previous file versions. The feature does not automatically remove any papers.

On a local preview before GitHub Pages setup, Remove controls are disabled. Live links are derived from the repository and branch supplied by GitHub Actions; no credentials are embedded in the page. There is no browser-only deletion or local-storage hiding.

Keep `publications/README.md` even if you remove every paper. No backup publication array is read from `content.json`, so deleted entries will not reappear during a rebuild.

## Upload a preprint PDF

Once the GitHub repository is connected and the automated deployment is configured, use **Upload PDF** in the Preprints section:

1. Sign in to GitHub if prompted.
2. Drag your PDF onto GitHub’s upload page for the `preprints/` folder.
3. Commit the upload. The deployment workflow rebuilds the homepage and publishes the new PDF link.

No title form or metadata editing is required. Every PDF in `preprints/` appears automatically; its filename becomes the displayed title, with underscores and hyphens replaced by spaces. Choose a readable filename, such as `Paper_Title.pdf`. Uploads use GitHub’s authenticated interface; the public website has no anonymous upload form.

During GitHub Actions deployment, the button’s target is derived automatically from `GITHUB_REPOSITORY` and `GITHUB_REF_NAME`. For deployments outside Actions, an optional `profile.preprintUploadUrl` can supply the repository’s HTTPS upload URL. Until the repository is configured, the local preview shows a disabled Upload PDF button labeled “Available after GitHub Pages setup.” For local edits, add the PDF to `preprints/` and run `python3 generate.py`.

Optional metadata can be added later in the `preprints` array of `content.json`. Match the literal repository path in `pdf` (for example, `preprints/Paper_Title.pdf`). Supported optional fields are `title`, `authors`, `year`, `version`, `updated` (`YYYY-MM-DD`), `abstract`, `arxiv_url`, and `code_url`. The last two must use HTTPS. Local PDF paths must stay beneath `preprints/`; traversal and non-HTTPS external links are rejected. Metadata for a removed PDF is ignored, and removing its PDF removes the corresponding card at the next rebuild.

Only PDFs deliberately uploaded to this folder are shown. No manuscripts from private conversations or the source CV have been added.

## arXiv listings

Verified arXiv papers are stored in `arxiv/<id>.json`. Required fields are `id`, `arxivId`, `title`, `authors`, `year`, `url` (the paper’s HTTPS arXiv abstract URL), and `pdfUrl` (its HTTPS arXiv PDF URL). Optional fields are `submitted`, `updated` (both `YYYY-MM-DD`), `journalRef`, and `topic`. A record may use `id: arxiv-2609-24675` and `arxivId: 2609.24675`; its filename must match the `id`.

Set `publicationStatus` to `published` when a published counterpart is verified, and put its canonical publication IDs in `publishedPublicationIds`. The generator adds **[arXiv]** after those publication citations and omits that arXiv record from Preprints. Set `publicationStatus` to `preprint` when no published counterpart has been confirmed. A related conference paper alone does not establish that a distinct extended manuscript has been published. The retained `publicationStatusEvidence` records the verification basis.

The Preprints section displays the ten newest remaining submissions first and places any older records in an expandable list. Uploaded PDFs have a separate subsection. Builds read the saved metadata only and make no network requests. Deleting an arXiv record removes its link or listing without automatic re-import. Deleting a publication removes its citation; its published arXiv version does not reappear as an unpublished preprint.

The downloadable HTML previews include both the homepage and AI-Aided Papers in one file, with internal navigation. This avoids relying on a separate HTML file being served by the preview viewer. The GitHub package retains two separate web pages and ordinary relative links.

## AI-Aided Papers

The **AI-Aided Papers** page is separate from regular Preprints. It displays the notice: **AI-assisted working drafts. These results have not been fully checked and may contain errors.** Every PDF is labeled **Not fully checked**.

After deployment, select **Upload PDF** on that page, upload the PDF to GitHub’s `ai-papers/` folder, and commit. It appears automatically on `ai-aided-papers.html`; no metadata editing is required. The upload target is derived from the repository and branch in Actions. For another deployment, `profile.aiPaperUploadUrl` can supply a valid HTTPS upload target. Local controls stay disabled until configured.

Optional `aiPapers` metadata in `content.json` uses the same fields as uploaded preprints, but its `pdf` path must begin with `ai-papers/`. The two upload folders cannot reference each other. Only explicitly uploaded PDFs are included; no private drafts have been added. Use the page’s **Manage AI-Aided Papers** control to remove a PDF through GitHub confirmation. The deployment publishes the page and PDFs, not source metadata or folder README files.

## GitHub Pages

1. On GitHub, create a repository named `lzhou-sustech.github.io` under the `lzhou-sustech` account. A public repository works with GitHub Free.
2. Commit this folder’s **complete contents** to the repository root on the `main` branch, including `.github/workflows/pages.yml`, `build.py`, `generate.py`, `publications/`, `arxiv/`, `preprints/`, and `ai-papers/`. The root should contain `index.html`, not an additional enclosing folder. Using Git or GitHub Desktop helps preserve the workflow’s `.github/` directory; uploading only the visible website files is insufficient for automatic PDF updates.
3. Open the repository’s **Settings → Pages**. Under **Build and deployment**, select **GitHub Actions** as the source.
4. Push a commit to `main`, or run the **Publish website and preprints** workflow from the **Actions** tab. After deployment completes, the personal site is available at `https://lzhou-sustech.github.io/`.

Keep `index.html`, `styles.css`, `script.js`, `content.json`, `publications/`, and `assets/` together. The included workflow runs `python build.py` and publishes `_site/`; no manual rebuild is needed after a PDF upload. Relative paths also allow use in an ordinary project repository.

Official guidance: [Creating a GitHub Pages site](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site) and [Configuring a publishing source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).

## Content provenance

The biography was adapted from the IEEE biography supplied by Lin Zhou on 10 October 2026. Other academic details and the original publication set were transcribed from his CV: 32 papers in its journal section, 2 magazine/survey articles, and 3 books/monographs. Later additions and bibliographic updates are maintained in the individual publication records. Selection, publication status, and category counts are derived from these records.

The public contact is `zhoul9@sustech.edu.cn`. Private under-review and planned manuscripts, grant proposals and budgets, personal/office addresses, and a download of the source CV are not included. Public arXiv manuscripts appear in Preprints regardless of their later publication status.

The portrait source is:
`https://www.sustech.edu.cn/uploads/medium/2026/09/07110043_84308.jpg`

Book links come from the links embedded in the supplied CV. Institutional, Google Scholar, and DBLP links likewise come from the CV.

The broadcast-channel dispersion article uses its verified final publication year, **2026** (DOI: [10.1109/TCOMM.2025.3626028](https://doi.org/10.1109/TCOMM.2025.3626028)). See [PUBLICATION_AUDIT.md](PUBLICATION_AUDIT.md) for publication additions, corrections, sources, and coverage limits.

See [ARXIV_AUDIT.md](ARXIV_AUDIT.md) for the 48 verified arXiv records, primary sources, deduplication, and the record pending identity confirmation.
