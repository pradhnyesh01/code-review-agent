import httpx
import respx

from code_review_agent.cli import main


@respx.mock
def test_main_prints_diff_for_valid_pr(capsys, monkeypatch):
    monkeypatch.setenv("GITHUB_PAT", "test-token")
    diff_text = "diff --git a/foo.py b/foo.py\n+added line\n"
    respx.get("https://api.github.com/repos/octocat/hello-world/pulls/42").mock(
        return_value=httpx.Response(200, text=diff_text)
    )

    exit_code = main(["octocat/hello-world", "42"])

    assert exit_code == 0
    assert capsys.readouterr().out == diff_text + "\n"


def test_main_errors_when_github_pat_is_unset(capsys, monkeypatch):
    monkeypatch.delenv("GITHUB_PAT", raising=False)
    # load_dotenv() searches upward from the caller's file location (not cwd),
    # which would find this repo's own .env and its real GITHUB_PAT. Stub it
    # out: dotenv's own search behavior isn't this test's concern.
    monkeypatch.setattr("code_review_agent.cli.load_dotenv", lambda: None)

    exit_code = main(["octocat/hello-world", "42"])

    assert exit_code == 2
    assert "GITHUB_PAT" in capsys.readouterr().err


def test_main_errors_on_malformed_repo_argument(capsys, monkeypatch):
    monkeypatch.setenv("GITHUB_PAT", "test-token")

    exit_code = main(["not-owner-slash-repo", "42"])

    assert exit_code == 2
    assert "owner/repo" in capsys.readouterr().err
