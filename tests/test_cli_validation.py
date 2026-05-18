import pytest

from damask_copilot.cli import build_parser


def test_cli_rejects_approve_without_full_run():
    parser = build_parser()

    args = parser.parse_args(["graph", "run", "Study FCC aluminum under uniaxial tension", "--approve"])

    with pytest.raises(SystemExit):
        if args.approve and not args.allow_full_run:
            parser.error("--approve can only be used together with --full-run.")
