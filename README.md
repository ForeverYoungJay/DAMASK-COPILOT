# DAMASK Copilot

Workflow-focused FastMCP adapters for the local DAMASK 3.0.2 Python source tree.

## Architecture

The project intentionally does not expose every DAMASK symbol as an MCP tool. Instead it wraps the main workflows:

- DAMASK installation and API inspection
- preprocessing and YAML generation
- simulation input validation
- controlled `DAMASK_grid` execution
- result inspection and export
- miscellaneous table, utility, and regular-grid helpers

Main adapter package:

- `src/damask_mcp_adapter/`

Compatibility and workflow modules:

- `src/damask_mcp_adapter/api_registry.py`
- `src/damask_mcp_adapter/modules/core.py`
- `src/damask_mcp_adapter/modules/config_material.py`
- `src/damask_mcp_adapter/modules/loading.py`
- `src/damask_mcp_adapter/modules/grid.py`
- `src/damask_mcp_adapter/modules/rotation.py`
- `src/damask_mcp_adapter/modules/result.py`
- `src/damask_mcp_adapter/modules/mechanics.py`
- `src/damask_mcp_adapter/modules/tensor.py`
- `src/damask_mcp_adapter/modules/runner.py`

FastMCP servers:

- `src/damask_copilot/mcp_servers/damask_core_server.py`
- `src/damask_copilot/mcp_servers/damask_preprocess_server.py`
- `src/damask_copilot/mcp_servers/damask_validation_server.py`
- `src/damask_copilot/mcp_servers/damask_runner_server.py`
- `src/damask_copilot/mcp_servers/damask_postprocess_server.py`
- `src/damask_copilot/mcp_servers/damask_misc_server.py`
- `src/damask_copilot/mcp_servers/damask_server.py`

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
- `damask.LoadcaseGrid`
- `damask.GeomGrid`
- `damask.Rotation`
- `damask.Result`
- `damask.seeds.from_random`
- `damask.mechanics`
- `damask.tensor`

## Documentation Mapping

The MCP tools are grouped by the official DAMASK processing-tools documentation:

- Core:
  - `check_damask_installation`
  - `get_damask_version`
  - `list_damask_modules`
  - `inspect_damask_class`
  - `inspect_damask_function`
- Pre-processing doc:
  - `create_simple_tension_load_yaml`
  - `create_simple_compression_load_yaml`
  - `create_material_yaml`
  - `create_material_yaml_from_template`
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
- Validation:
  - `validate_material_yaml_structure`
  - `validate_load_yaml_structure`
  - `inspect_geometry_material_indices`
  - `check_phase_homogenization_consistency`
  - `check_orientation_format`
  - `check_required_plasticity_parameters`
  - `check_material_indices`
  - `validate_simulation_setup`
- Runner:
  - `find_damask_executables`
  - `run_damask_grid`
  - `list_workspace_files`
  - `collect_result_files`
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

Unified server:

```bash
python3 -m damask_copilot.mcp_servers.damask_server
```

Or via the console script:

```bash
damask-mcp
```

Split servers remain available when you want finer-grained registration:

Core:

```bash
python3 -m damask_copilot.mcp_servers.damask_core_server
```

Preprocess:

```bash
python3 -m damask_copilot.mcp_servers.damask_preprocess_server
```

Validation:

```bash
python3 -m damask_copilot.mcp_servers.damask_validation_server
```

Runner:

```bash
python3 -m damask_copilot.mcp_servers.damask_runner_server
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
[mcp_servers.damask]
command = "/Users/yang/Library/CloudStorage/OneDrive-国立研究開発法人物質・材料研究機構/自分/DAMASK COPILOT/.venv/bin/python"
args = ["-m", "damask_copilot.mcp_servers.damask_server"]
cwd = "/Users/yang/Library/CloudStorage/OneDrive-国立研究開発法人物質・材料研究機構/自分/DAMASK COPILOT"
startup_timeout_sec = 30
tool_timeout_sec = 3600

[mcp_servers.damask.env]
PYTHONPATH = "/Users/yang/Library/CloudStorage/OneDrive-国立研究開発法人物質・材料研究機構/自分/DAMASK COPILOT/src"

[mcp_servers.damask-core]
command = "/Users/yang/Library/CloudStorage/OneDrive-国立研究開発法人物質・材料研究機構/自分/DAMASK COPILOT/.venv/bin/python"
args = ["-m", "damask_copilot.mcp_servers.damask_core_server"]
cwd = "/Users/yang/Library/CloudStorage/OneDrive-国立研究開発法人物質・材料研究機構/自分/DAMASK COPILOT"
startup_timeout_sec = 30
tool_timeout_sec = 60

[mcp_servers.damask-core.env]
PYTHONPATH = "/Users/yang/Library/CloudStorage/OneDrive-国立研究開発法人物質・材料研究機構/自分/DAMASK COPILOT/src"

[mcp_servers.damask-preprocess]
command = "/Users/yang/Library/CloudStorage/OneDrive-国立研究開発法人物質・材料研究機構/自分/DAMASK COPILOT/.venv/bin/python"
args = ["-m", "damask_copilot.mcp_servers.damask_preprocess_server"]
cwd = "/Users/yang/Library/CloudStorage/OneDrive-国立研究開発法人物質・材料研究機構/自分/DAMASK COPILOT"
startup_timeout_sec = 30
tool_timeout_sec = 120

[mcp_servers.damask-preprocess.env]
PYTHONPATH = "/Users/yang/Library/CloudStorage/OneDrive-国立研究開発法人物質・材料研究機構/自分/DAMASK COPILOT/src"

[mcp_servers.damask-validation]
command = "/Users/yang/Library/CloudStorage/OneDrive-国立研究開発法人物質・材料研究機構/自分/DAMASK COPILOT/.venv/bin/python"
args = ["-m", "damask_copilot.mcp_servers.damask_validation_server"]
cwd = "/Users/yang/Library/CloudStorage/OneDrive-国立研究開発法人物質・材料研究機構/自分/DAMASK COPILOT"
startup_timeout_sec = 30
tool_timeout_sec = 120

[mcp_servers.damask-validation.env]
PYTHONPATH = "/Users/yang/Library/CloudStorage/OneDrive-国立研究開発法人物質・材料研究機構/自分/DAMASK COPILOT/src"

[mcp_servers.damask-runner]
command = "/Users/yang/Library/CloudStorage/OneDrive-国立研究開発法人物質・材料研究機構/自分/DAMASK COPILOT/.venv/bin/python"
args = ["-m", "damask_copilot.mcp_servers.damask_runner_server"]
cwd = "/Users/yang/Library/CloudStorage/OneDrive-国立研究開発法人物質・材料研究機構/自分/DAMASK COPILOT"
startup_timeout_sec = 30
tool_timeout_sec = 3600

[mcp_servers.damask-runner.env]
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
