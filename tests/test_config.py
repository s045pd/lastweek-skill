from engine.config import _parse_env_file, brave_key, github_token


def test_parse_env_file_ignores_comments(tmp_path):
    path = tmp_path / "env"
    path.write_text("# hi\nGITHUB_TOKEN=abc\nBRAVE_API_KEY='k'\n\n", encoding="utf-8")
    values = _parse_env_file(path)
    assert values["GITHUB_TOKEN"] == "abc"
    assert values["BRAVE_API_KEY"] == "k"


def test_token_helpers_read_mapping(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("BRAVE_API_KEY", raising=False)
    monkeypatch.delenv("LASTWEEK_BRAVE_API_KEY", raising=False)
    values = {"GITHUB_TOKEN": "t", "BRAVE_API_KEY": "b"}
    assert github_token(values) == "t"
    assert brave_key(values) == "b"
