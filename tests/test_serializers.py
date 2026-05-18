import numpy as np

from damask_mcp_adapter.serializers import summarize_array, to_jsonable


def test_summarize_array_basic():
    summary = summarize_array(np.array([[1.0, 2.0], [3.0, 4.0]]))
    assert summary["shape"] == [2, 2]
    assert summary["size"] == 4


def test_to_jsonable_numpy_array_becomes_summary():
    payload = to_jsonable({"x": np.array([1, 2, 3])})
    assert payload["x"]["shape"] == [3]
