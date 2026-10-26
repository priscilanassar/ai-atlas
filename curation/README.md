# Instagram curation batch

The 2026-10-25 batch contains 15 user-supplied references. Public metadata was
read in the browser without signing in. This is an import snapshot, not a
scheduled scraper. Images and videos have not been downloaded.

From the folder containing manage.py:

```powershell
.\.venv\Scripts\python.exe manage.py import_curation curation/instagram-batch-2026-10-25.json
```

Reimporting the same Instagram shortcode skips the existing submission and
preserves review edits, including when the account prefix or carousel index differs.

## Review

1. Open `/admin/archive/curationsubmission/` as an administrator.
2. Open the original post and check authorship and whether the work uses AI.
3. Complete the project title, artist, category and project year. Caption text is
   only a suggested title; the publishing account may differ from the artist.
4. Add a reviewed cover URL, description and tools. Instagram preview URLs are
   temporary and are not automatically copied into published projects.
5. Confirm AI use and leave the submission status as Pending review.
6. Select the completed submissions in the list and run
   “Publish reviewed submissions to the Atlas”.

The publication action skips incomplete, rejected or already published records.
It keeps the source URL on the published project. Publication dates from
Instagram are kept separate from project creation dates.

The two Fendi references are separate posts and may belong to the same series;
review them together to decide whether to publish one project or two.
The requested slide for DYhrI8QjfC8 is slide 3; the Instagram preview may still
show slide 1. Location, colors and AI tools have not been guessed.
