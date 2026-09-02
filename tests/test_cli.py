from engine.cli import build_parser


def test_parser_defaults_are_week_native():
    parser = build_parser()
    args = parser.parse_args(["OpenClaw"])
    assert args.topic == ["OpenClaw"]
    assert args.window == "rolling"
    assert args.shape == "pulse"
    assert args.emit == "brief"
    assert args.wow is False
    assert args.depth == "normal"


def test_parser_accepts_iso_week_and_wow():
    parser = build_parser()
    args = parser.parse_args(
        ["Nvidia", "--iso-week", "2026-W35", "--wow", "--shape", "wrap", "--emit", "json"]
    )
    assert args.iso_week == "2026-W35"
    assert args.wow is True
    assert args.shape == "wrap"
    assert args.emit == "json"


def test_doctor_subcommand_exists():
    parser = build_parser()
    args = parser.parse_args(["doctor"])
    assert args.topic == ["doctor"]
