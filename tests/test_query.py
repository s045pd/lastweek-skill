from engine.query import clean_topic, parse_hints, split_compare, tokenize


def test_clean_topic_strips_week_language_not_the_subject():
    assert clean_topic("OpenClaw this week") == "OpenClaw"
    assert clean_topic("what happened last week with Nvidia") == "with Nvidia"
    assert clean_topic("GPT-4o") == "GPT-4o"
    assert clean_topic("this week") == ""
    assert clean_topic("weekly wrap") == ""


def test_split_compare_finds_vs_and_versus():
    assert split_compare("Claude vs Codex") == ("Claude", "Codex")
    assert split_compare("Claude versus Codex") == ("Claude", "Codex")
    assert split_compare("Claude") is None
    assert split_compare("versus") is None


def test_tokenize_drops_tiny_noise():
    tokens = tokenize("The OpenClaw agent on HN")
    assert "openclaw" in tokens
    assert "the" not in tokens
    assert "on" not in tokens


def test_parse_hints_reads_known_keys_only():
    hints = parse_hints(
        {
            "subreddits": ["LocalLLaMA", "MachineLearning"],
            "github_user": "octocat",
            "github_repos": ["octocat/hello-world"],
            "extra_queries": ["release notes"],
            "ignored": "nope",
        }
    )
    assert hints.subreddits == ["LocalLLaMA", "MachineLearning"]
    assert hints.github_user == "octocat"
    assert hints.github_repos == ["octocat/hello-world"]
    assert hints.extra_queries == ["release notes"]
