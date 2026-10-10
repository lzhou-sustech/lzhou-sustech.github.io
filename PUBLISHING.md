# Publish Lin Zhou’s website

Target account: `lzhou-sustech`
Repository: `lzhou-sustech/lzhou-sustech.github.io`
Website after successful deployment: https://lzhou-sustech.github.io/

This package contains the recovered approved site, configured for the renamed account. The local build has been tested; it has not been deployed to GitHub by this chat.

## Browser setup

1. Open https://github.com/new?owner=lzhou-sustech&name=lzhou-sustech.github.io&visibility=public . Create the public repository with a README if it does not already exist. Use the `main` branch. If the repository already exists, use that repository; do not create another.
2. Unzip this package. Open https://github.com/lzhou-sustech/lzhou-sustech.github.io/upload/main . Upload the extracted contents, not this ZIP and not an enclosing folder. GitHub permits up to 100 files per upload, so use these three batches, committing each to `main`:
   - All top-level files and folders EXCEPT `publications/` and `arxiv/`. Include the hidden `.github/` folder and its `workflows/pages.yml` file. On macOS, Command–Shift–Period toggles hidden files in Finder.
   - The complete `publications/` folder, retaining its folder name.
   - The complete `arxiv/` folder, retaining its folder name.
   After uploading, the repository root must contain `index.html`, `build.py`, `generate.py`, `content.json`, `styles.css`, `script.js`, and the other included files/folders. Initial workflow runs may fail until all uploads and Pages configuration are complete.
3. Open https://github.com/lzhou-sustech/lzhou-sustech.github.io/settings/pages . Under Build and deployment → Source, select **GitHub Actions**, NOT “Deploy from a branch.”
4. Open https://github.com/lzhou-sustech/lzhou-sustech.github.io/actions/workflows/pages.yml . Select **Run workflow**, choose `main`, and confirm **Run workflow**. Check that both the build and deploy jobs succeed.
5. Open https://lzhou-sustech.github.io/ after the successful deployment.

## Updating the website

The included workflow rebuilds the site after every push to `main`. Upload PDF and Remove controls direct maintainers to authenticated GitHub pages; they do not grant visitors editing permission. Regular preprints belong in `preprints/`; AI-assisted drafts belong in `ai-papers/`. The public AI-assisted-draft warning is unchanged.

## Local build

From this folder:

```sh
GITHUB_REPOSITORY=lzhou-sustech/lzhou-sustech.github.io GITHUB_REF_NAME=main python3 build.py
```

The deployable public files are staged in `_site/`. Source metadata and audit files are not included in the deployed Pages artifact, although they are visible in a public repository.

## Official documentation

- https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site
- https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site
- https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository
