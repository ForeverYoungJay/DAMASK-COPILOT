# DAMASK Pre-Processing API Inventory

Source docs:

- Official pre-processing page: https://damask-multiphysics.org/documentation/processing_tools/pre-processing.html
- Local source checked against `./damask-3.0.2/python/damask`

## `damask.YAML`

- Documented methods:
  - `load`
  - `save`
  - `delete`
  - dict-like methods such as `update`, `keys`, `items`
- MCP tools:
  - `validate_yaml_file`
- Internal-only:
  - generic dict methods
  - raw `save` and `load` plumbing
- Safety concerns:
  - writes must stay inside `workspaces/`
  - YAML can contain arbitrary nested structures, so MCP should validate mapping-shaped input
- Example MCP names:
  - `validate_yaml_file`

## `damask.ConfigMaterial`

- Documented methods:
  - `load`
  - `save`
  - `from_table`
  - `load_DREAM3D`
  - `material_add`
  - `material_rename_phase`
  - `material_rename_homogenization`
  - properties `is_complete`, `is_valid`
- MCP tools:
  - `create_empty_material_yaml`
  - `inspect_material_yaml`
  - `validate_material_yaml`
  - `add_material_entry`
- Internal-only:
  - rename helpers
  - `from_table`
  - `load_DREAM3D`
- Safety concerns:
  - in-place writes must remain inside `workspaces/`
  - `load_DREAM3D` can touch large HDF5 inputs and is better kept internal for later
- Example MCP names:
  - `create_empty_material_yaml`
  - `add_material_entry`

## `damask.Rotation`

- Documented methods confirmed locally:
  - `from_random`
  - `from_quaternion`
  - `from_Euler_angles`
  - `as_quaternion`
  - `as_Euler_angles`
- MCP tools:
  - `create_random_orientations`
  - `convert_euler_to_quaternion`
  - `convert_quaternion_to_euler`
- Internal-only:
  - less common constructors like `from_ODF`, `from_cubochoric`, `from_axis_angle`
- Safety concerns:
  - arrays can get large quickly, so return summaries rather than full orientation banks
- Example MCP names:
  - `create_random_orientations`

## `damask.seeds`

- Documented functions confirmed locally:
  - `from_random`
  - `from_Poisson_disc`
  - `from_grid`
- MCP tools:
  - `create_random_seeds`
- Internal-only:
  - `from_Poisson_disc`
  - `from_grid`
- Safety concerns:
  - seed clouds are arrays, so summarize or save instead of returning large payloads
- Example MCP names:
  - `create_random_seeds`

## `damask.GeomGrid`

- Documented methods confirmed locally:
  - `load`
  - `save`
  - `from_Voronoi_tessellation`
  - `from_Laguerre_tessellation`
  - `from_minimal_surface`
  - `scale`
  - `renumber`
  - `sort`
  - `clean`
  - `show`
- MCP tools:
  - `create_voronoi_grid`
  - `inspect_grid`
  - `scale_grid`
  - `renumber_grid`
  - `clean_grid`
- Internal-only:
  - `show`
  - `from_Laguerre_tessellation`
  - `from_minimal_surface`
  - geometric transforms like `rotate`, `mirror`, `flip`
- Safety concerns:
  - grid files are written artifacts and must stay inside `workspaces/`
  - `show` is GUI-oriented and unsuitable for MCP
  - large voxel arrays should be summarized
- Example MCP names:
  - `create_voronoi_grid`
  - `clean_grid`
