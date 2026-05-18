from damask_copilot.graph.checkpoints import ALLOWED_MSGPACK_TYPES, build_checkpointer


def test_build_checkpointer_uses_explicit_msgpack_allowlist():
    checkpointer = build_checkpointer(enabled=True)

    assert checkpointer is not None
    allowed = getattr(checkpointer.serde, "_allowed_msgpack_modules", None)
    assert allowed is not None

    expected = {(model.__module__, model.__name__) for model in ALLOWED_MSGPACK_TYPES}
    assert expected.issubset(set(allowed))
