# Projects Directory

Use `projects/` for one folder per scientific study.

Suggested structure:

```text
projects/
  ni3al_calibration/
    goal.yaml
    literature/
    experimental/
    notes/
    inputs/
```

Guidelines:

- Put project-specific files under `projects/<project_name>/`.
- Keep literature under `projects/<project_name>/literature/`.
- Keep experiments under `projects/<project_name>/experimental/`.
- Treat `data/materials/` as a fake/demo material-parameter dataset only.
- Future SQL-backed material databases should replace the demo parameter source without changing project folders.
- If `--project-dir` is not provided, DAMASK Copilot will try to discover a matching project under `projects/`.
