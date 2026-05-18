from damask_copilot.mcp_servers import (
    damask_misc_server,
    damask_postprocess_server,
    damask_preprocess_server,
)


def test_server_tool_docstrings_exist():
    assert damask_preprocess_server.create_empty_material_yaml.__doc__
    assert damask_postprocess_server.inspect_result_file.__doc__
    assert damask_misc_server.inspect_table.__doc__
