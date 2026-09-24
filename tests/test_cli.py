import httpx
import respx

from code_review_agent.cli import main
from code_review_agent.findings import Finding


@respx.mock
def test_main_prints_style_findings_for_valid_pr(capsys, monkeypatch):
    monkeypatch.setenv("GITHUB_PAT", "test-token")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    diff_text = "diff --git a/foo.py b/foo.py\n+added line\n"
    guide_text = "# Style Guide\n"
    respx.get("https://api.github.com/repos/octocat/hello-world/pulls/42").mock(
        return_value=httpx.Response(200, text=diff_text)
    )
    respx.get(
        "https://api.github.com/repos/octocat/hello-world/contents/.github/REVIEW_GUIDE.md"
    ).mock(return_value=httpx.Response(200, text=guide_text))

    findings = [Finding(file="foo.py", line=1, comment="use snake_case", category="style", severity="warning")]
    recorded_args = {}

    def fake_generate_style_findings(client, diff, style_guide):
        recorded_args["diff"] = diff
        recorded_args["style_guide"] = style_guide
        return findings

    monkeypatch.setattr(
        "code_review_agent.cli.generate_style_findings", fake_generate_style_findings
    )

    exit_code = main(["octocat/hello-world", "42"])

    assert exit_code == 0
    assert recorded_args == {"diff": diff_text, "style_guide": guide_text}
    assert capsys.readouterr().out == findings[0].model_dump_json() + "\n"


def test_main_errors_when_github_pat_is_unset(capsys, monkeypatch):
    monkeypatch.delenv("GITHUB_PAT", raising=False)
    # load_dotenv() searches upward from the caller's file location (not cwd),
    # which would find this repo's own .env and its real GITHUB_PAT. Stub it
    # out: dotenv's own search behavior isn't this test's concern.
    monkeypatch.setattr("code_review_agent.cli.load_dotenv", lambda: None)

    exit_code = main(["octocat/hello-world", "42"])

    assert exit_code == 2
    assert "GITHUB_PAT" in capsys.readouterr().err


def test_main_errors_when_openai_api_key_is_unset(capsys, monkeypatch):
    monkeypatch.setenv("GITHUB_PAT", "test-token")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    exit_code = main(["octocat/hello-world", "42"])

    assert exit_code == 2
    assert "OPENAI_API_KEY" in capsys.readouterr().err


def test_main_errors_on_malformed_repo_argument(capsys, monkeypatch):
    monkeypatch.setenv("GITHUB_PAT", "test-token")

    exit_code = main(["not-owner-slash-repo", "42"])

    assert exit_code == 2
    assert "owner/repo" in capsys.readouterr().err
