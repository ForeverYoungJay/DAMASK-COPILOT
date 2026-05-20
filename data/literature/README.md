# Literature Data

Store literature assets by material id.

Recommended layout:

```text
data/literature/<material_id>/
  pdf/
  notes/
  bibliographies/
  source_lists/

data/literature/<material_id>/<case_name>/
  pdf/
  notes/
  bibliographies/
  source_lists/
```

Examples:

- `pdf/`: downloaded papers
- `notes/`: markdown notes, extraction notes, mechanism summaries
- `bibliographies/`: `.bib`, RIS, EndNote exports
- `source_lists/`: text files with DOI, URL, or arXiv ids

CLI support:

- `--literature-file data/literature/<material_id>/<case_name>/notes/reading_notes.md`
- `--source-list-file data/literature/<material_id>/<case_name>/source_lists/seed_sources.txt`
