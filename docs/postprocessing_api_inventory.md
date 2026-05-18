# DAMASK Post-Processing API Inventory

Source docs:

- Official post-processing page: https://damask-multiphysics.org/documentation/processing_tools/post-processing.html
- Local source checked against `./damask-3.0.2/python/damask`

## `damask.Result`

- Documented methods confirmed locally:
  - `view`
  - `list_data`
  - `get`
  - `place`
  - `export_VTK`
  - `export_XDMF`
  - `add_deviator`
  - `add_equivalent_Mises`
  - `add_spherical`
  - `add_strain`
  - `add_gradient`
  - `add_divergence`
  - `add_curl`
- MCP tools:
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
- Internal-only:
  - raw `view` composition
  - `get` and `place` recursion details
  - export modes beyond VTK for now
- Safety concerns:
  - `add_*` methods mutate the HDF5 result file, so only workspace-local files should be writable
  - `get` and `place` can yield very large arrays; MCP should summarize or save derived tabular outputs
- Example MCP names:
  - `inspect_result_file`
  - `add_strain`
  - `extract_stress_strain_curve`

## Low-level HDF5 inspection

- Documented object:
  - not a DAMASK class, but useful for safe file introspection before `damask.Result`
- MCP tools:
  - `inspect_hdf5_result`
- Internal-only:
  - raw HDF5 traversal mechanics
- Safety concerns:
  - inspect metadata only and cap the number of returned items
- Example MCP names:
  - `inspect_hdf5_result`
