# DAMASK Copilot Data Layout

This repository is organized to support many materials and many research cases.

Recommended structure:

```text
data/
  materials/
    index.yaml
    <material_id>_demo.yaml

  experimental/
    <material_id>/
      raw/
      processed/
      metadata/
      <case_name>/
        raw/
        processed/
        metadata/

  literature/
    <material_id>/
      pdf/
      notes/
      bibliographies/
      source_lists/
      <case_name>/
        pdf/
        notes/
        bibliographies/
        source_lists/
```

Guidelines:

- `materials/`
  - Store internal parameter cards and material templates used by `ParameterAgent`.
- `experimental/<material_id>/raw/`
  - Store original CSV/XLSX/TXT/JSON/YAML data files.
- `experimental/<material_id>/processed/`
  - Store cleaned or unit-normalized datasets used for alignment.
- `experimental/<material_id>/metadata/`
  - Store README files, units notes, specimen information, and test conditions.
- `literature/<material_id>/pdf/`
  - Store downloaded papers for manual review.
- `literature/<material_id>/notes/`
  - Store reading notes, summaries, and extraction memos.
- `literature/<material_id>/bibliographies/`
  - Store `.bib`, RIS, or citation exports.
- `literature/<material_id>/source_lists/`
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
  --experimental-file data/experimental/ni3al_l12/raw/cold_rolling_curve.csv \
  --user-file data/literature/ni3al_l12/notes/reading_notes.md \
  --literature-source "doi:10.xxxx/xxxx"
```
