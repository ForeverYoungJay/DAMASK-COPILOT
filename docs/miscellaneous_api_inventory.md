# DAMASK Miscellaneous API Inventory

Source docs:

- Official miscellaneous page: https://damask-multiphysics.org/documentation/processing_tools/miscellaneous.html
- Local source checked against `./damask-3.0.2/python/damask`

## `damask.Table`

- Documented methods confirmed locally:
  - `load`
  - `load_ang`
  - `get`
  - `set`
  - `delete`
  - `rename`
  - `sort_by`
  - `append`
  - `join`
  - `save`
  - `copy`
  - `isclose`
  - `allclose`
- MCP tools:
  - `load_table`
  - `inspect_table`
  - `get_table_column`
  - `rename_table_column`
  - `sort_table_by`
- Internal-only:
  - `append`
  - `join`
  - `load_ang`
  - numeric comparison helpers
- Safety concerns:
  - column extraction can be large; summarize and optionally save `.npy`
  - rename/sort write paths must remain in `workspaces/`
- Example MCP names:
  - `get_table_column`
  - `sort_table_by`

## `damask.util`

- Documented functions confirmed locally:
  - `DREAM3D_base_group`
  - `DREAM3D_cell_data_group`
  - `Miller_to_Bravais`
  - `Bravais_to_Miller`
  - `scale_to_coprime`
  - `project_equal_angle`
  - `project_equal_area`
  - `hybrid_IA`
  - `dict_prune`
  - `dict_flatten`
- MCP tools:
  - `inspect_dream3d_base_group`
  - `inspect_dream3d_cell_data_group`
  - `miller_to_bravais`
  - `bravais_to_miller`
- Internal-only:
  - `dict_prune`
  - `dict_flatten`
  - plotting/projection helpers
  - progress helpers
- Safety concerns:
  - DREAM3D inspection can touch large files; return only resolved group names
- Example MCP names:
  - `inspect_dream3d_base_group`

## `damask.grid_filters`

- Documented functions confirmed locally:
  - `point_to_node`
  - `node_to_point`
  - `coordinates0_valid`
  - `ravel`
  - `unravel`
  - plus many internal Fourier-space operators like `curl`, `gradient`, `divergence`
- MCP tools:
  - `grid_point_to_node`
  - `grid_node_to_point`
  - `grid_ravel`
  - `grid_unravel`
  - `validate_regular_grid_coordinates`
- Internal-only:
  - direct Fourier-space field operators
  - indexing helpers
- Safety concerns:
  - transformed arrays can be large; summarize and optionally save `.npy`
- Example MCP names:
  - `grid_ravel`
  - `validate_regular_grid_coordinates`
