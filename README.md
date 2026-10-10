# Publication records

Each `.json` file is one public publication record. The filename must match its `id`, for example `journal-gray-wyner-2017.json`.

The homepage reads only this directory for publications. Delete a paper’s JSON file to remove its citation, then commit; the deployment automatically updates the site. It is not restored from `content.json`. Keep this README even if every paper is removed.

To add a paper, create a new JSON file containing `id`, `title`, `authors`, `year`, `venue`, `type` (`book`, `journal`, or `conference`), `status` (`published` or `accepted`), `topic`, and `selected` (boolean). Optional fields include `details` and an HTTPS `url`. Preserve author order and distinguish accepted work from published work.

Use the site’s **Manage papers** section to open the corresponding GitHub deletion page. GitHub authentication, repository permission, and confirmation are required. Removing a citation does not remove the publisher’s paper; removing a preprint PDF removes that file from the website. Previous versions remain in Git history.
