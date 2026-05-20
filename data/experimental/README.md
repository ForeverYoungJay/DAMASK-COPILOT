# Experimental Data

Store experimental datasets by material id.

Recommended layout:

```text
data/experimental/<material_id>/
  raw/
  processed/
  metadata/

data/experimental/<material_id>/<case_name>/
  raw/
  processed/
  metadata/
```

Examples:

- `raw/`: original tensile curves, rolling data, EBSD exports
- `processed/`: interpolated or unit-normalized CSV files
- `metadata/`: README, units, temperature, strain rate, specimen geometry
