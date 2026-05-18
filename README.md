# DAMASK Copilot

Workflow-focused MCP adapters for the local DAMASK 3.0.2 Python source tree.

## Architecture

The project intentionally does not expose every DAMASK symbol as an MCP tool. Instead it wraps the main workflows:

- preprocessing and YAML generation
- result inspection and export
- miscellaneous table, utility, and regular-grid helpers

Main adapter package:

- `src/damask_mcp_adapter/`

Thin MCP servers:

- `src/damask_copilot/mcp_servers/damask_preprocess_server.py`
- `src/damask_copilot/mcp_servers/damask_postprocess_server.py`
- `src/damask_copilot/mcp_servers/damask_misc_server.py`

## Safety Rules

- All MCP tools return JSON-serializable dictionaries.
- All file writes are restricted to `workspaces/`.
- The runner never uses `shell=True`.
- Large arrays are summarized instead of returned directly.
- DAMASK APIs are wrapped only when confirmed from the local `damask-3.0.2/python/damask` source.

## DAMASK APIs Wrapped

The current adapter uses confirmed DAMASK APIs including:

- `damask.ConfigMaterial`
- `damask.YAML`
- `damask.GeomGrid`
- `damask.Rotation`
- `damask.Result`
- `damask.seeds.from_random`
- `damask.mechanics`
- `damask.tensor`

## Documentation Mapping

The MCP tools are grouped by the official DAMASK processing-tools documentation:

- Pre-processing doc:
  - `validate_yaml_file`
  - `create_empty_material_yaml`
  - `inspect_material_yaml`
  - `validate_material_yaml`
  - `add_material_entry`
  - `create_random_orientations`
  - `convert_euler_to_quaternion`
  - `convert_quaternion_to_euler`
  - `create_random_seeds`
  - `create_voronoi_grid`
  - `inspect_grid`
  - `scale_grid`
  - `renumber_grid`
  - `clean_grid`
- Post-processing doc:
  - `inspect_result_file`
  - `list_result_data`
  - `list_result_increments`
  - `list_result_fields`
  - `add_strain`
  - `add_equivalent_mises`
  - `add_deviator`
  - `add_spherical`
  - `add_gradient`
  - `add_divergence`
  - `add_curl`
  - `export_result_vtk`
  - `extract_volume_average`
  - `extract_stress_strain_curve`
- Miscellaneous doc:
  - `load_table`
  - `inspect_table`
  - `get_table_column`
  - `rename_table_column`
  - `sort_table_by`
  - `inspect_dream3d_base_group`
  - `inspect_dream3d_cell_data_group`
  - `miller_to_bravais`
  - `bravais_to_miller`
  - `grid_point_to_node`
  - `grid_node_to_point`
  - `grid_ravel`
  - `grid_unravel`
  - `validate_regular_grid_coordinates`

## Install

Install the package and runtime dependencies:

```bash
python3 -m pip install -e .
```

For tests:

```bash
python3 -m pip install -e .[dev]
```

The adapter imports DAMASK directly from the local source tree at `./damask-3.0.2/python`.

## Run MCP Servers

Preprocess:

```bash
python3 -m damask_copilot.mcp_servers.damask_preprocess_server
```

Postprocess:

```bash
python3 -m damask_copilot.mcp_servers.damask_postprocess_server
```

Misc:

```bash
python3 -m damask_copilot.mcp_servers.damask_misc_server
```

## Codex MCP Configuration

Example `.codex/config.toml`:

```toml
[mcp_servers.damask-preprocess]
command = "/Users/yang/Library/CloudStorage/OneDrive-国立研究開発法人物質・材料研究機構/自分/DAMASK COPILOT/.venv/bin/python"
args = ["-m", "damask_copilot.mcp_servers.damask_preprocess_server"]
cwd = "/Users/yang/Library/CloudStorage/OneDrive-国立研究開発法人物質・材料研究機構/自分/DAMASK COPILOT"
startup_timeout_sec = 30
tool_timeout_sec = 120

[mcp_servers.damask-preprocess.env]
PYTHONPATH = "/Users/yang/Library/CloudStorage/OneDrive-国立研究開発法人物質・材料研究機構/自分/DAMASK COPILOT/src"

[mcp_servers.damask-postprocess]
command = "/Users/yang/Library/CloudStorage/OneDrive-国立研究開発法人物質・材料研究機構/自分/DAMASK COPILOT/.venv/bin/python"
args = ["-m", "damask_copilot.mcp_servers.damask_postprocess_server"]
cwd = "/Users/yang/Library/CloudStorage/OneDrive-国立研究開発法人物質・材料研究機構/自分/DAMASK COPILOT"
startup_timeout_sec = 30
tool_timeout_sec = 300

[mcp_servers.damask-postprocess.env]
PYTHONPATH = "/Users/yang/Library/CloudStorage/OneDrive-国立研究開発法人物質・材料研究機構/自分/DAMASK COPILOT/src"

[mcp_servers.damask-misc]
command = "/Users/yang/Library/CloudStorage/OneDrive-国立研究開発法人物質・材料研究機構/自分/DAMASK COPILOT/.venv/bin/python"
args = ["-m", "damask_copilot.mcp_servers.damask_misc_server"]
cwd = "/Users/yang/Library/CloudStorage/OneDrive-国立研究開発法人物質・材料研究機構/自分/DAMASK COPILOT"
startup_timeout_sec = 30
tool_timeout_sec = 120

[mcp_servers.damask-misc.env]
PYTHONPATH = "/Users/yang/Library/CloudStorage/OneDrive-国立研究開発法人物質・材料研究機構/自分/DAMASK COPILOT/src"
```

If you prefer to use a different Python interpreter, update `command` and keep `PYTHONPATH` pointed at `src`.

## Verification Commands

Once dependencies are installed, run:

```bash
python -c "import damask; print(damask.__version__)"
python -m pytest tests
```
