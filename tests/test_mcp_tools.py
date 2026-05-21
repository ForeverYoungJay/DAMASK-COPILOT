from damask_copilot.mcp_servers import (
    damask_server,
    damask_core_server,
    damask_misc_server,
    damask_postprocess_server,
    damask_preprocess_server,
    damask_runner_server,
    damask_validation_server,
)
from damask_mcp_adapter.api_registry import list_registered_servers


def test_server_tool_docstrings_exist():
    assert damask_core_server.check_damask_installation.__doc__
    assert damask_server.describe_damask_mcp.__doc__
    assert damask_preprocess_server.create_empty_material_yaml.__doc__
    assert damask_preprocess_server.create_material_yaml_from_template.__doc__
    assert damask_validation_server.validate_simulation_setup.__doc__
    assert damask_postprocess_server.inspect_result_file.__doc__
    assert damask_misc_server.inspect_table.__doc__
    assert damask_runner_server.run_damask_grid.__doc__


def test_server_registry_lists_validation_and_unified_servers():
    result = list_registered_servers()

    assert result["ok"] is True
    assert "validation" in result["servers"]
    assert "unified" in result["servers"]
