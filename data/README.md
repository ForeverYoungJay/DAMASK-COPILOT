# DAMASK Copilot Data Layout

This repository is organized to support many materials and many research cases.

Recommended structure:

```text
data/
  materials/
    index.yaml
    <material_id>_demo.yaml
```

Project-specific literature and experiment files now live under:

```text
projects/
  <project_name>/
    literature/
      pdf/
      notes/
      bibliographies/
      source_lists/
    experimental/
      raw/
      processed/
      metadata/
      <case_name>/
        raw/
        processed/
        metadata/
```

Guidelines:

- `materials/`
  - Store internal demo parameter cards and material templates only.
- `projects/<project_name>/experimental/raw/`
  - Store original CSV/XLSX/TXT/JSON/YAML data files.
- `projects/<project_name>/experimental/processed/`
  - Store cleaned or unit-normalized datasets used for alignment.
- `projects/<project_name>/experimental/metadata/`
  - Store README files, units notes, specimen information, and test conditions.
- `projects/<project_name>/literature/pdf/`
  - Store downloaded papers for manual review.
- `projects/<project_name>/literature/notes/`
  - Store reading notes, summaries, and extraction memos.
- `projects/<project_name>/literature/bibliographies/`
  - Store `.bib`, RIS, or citation exports.
- `projects/<project_name>/literature/source_lists/`
  - Store DOI lists, URL lists, and arXiv ids that can be fed into the CLI.

Current system behavior:

- Experimental datasets can be passed directly with `--experimental-file`.
- Literature identifiers can be passed directly with `--literature-source`.
- Literature search can also run automatically through `LiteratureAgent`.
- Local literature files are useful for project organization and human review, even if they are not yet a first-class parser input.

Example:

```bash
damask-copilot materials run "Study Ni3Al L12 cold rolling anisotropy" \
  --dry-run \
  --llm \
  --project-name ni3al_l12 \
  --experimental-file projects/ni3al_l12/experimental/cold_rolling_anisotropy/raw/cold_rolling_curve.csv \
  --user-file projects/ni3al_l12/literature/cold_rolling_anisotropy/notes/reading_notes.md \
  --literature-source "doi:10.xxxx/xxxx"
```
