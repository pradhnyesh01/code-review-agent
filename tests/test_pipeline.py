from unittest.mock import MagicMock

import httpx
import respx

from code_review_agent.findings import Finding
from code_review_agent.pipeline import generate_findings_for_pr


@respx.mock
def test_generate_findings_for_pr_combines_style_and_test_coverage_findings(monkeypatch):
    diff_text = (
        "diff --git a/foo.py b/foo.py\n"
        "index 1234567..89abcde 100644\n"
        "--- a/foo.py\n"
        "+++ b/foo.py\n"
        "@@ -1,1 +1,2 @@\n"
        " existing()\n"
        "+def new_function():\n"
    )
    respx.get("https://api.github.com/repos/octocat/hello-world/pulls/42").mock(
        return_value=httpx.Response(200, text=diff_text)
    )
    respx.get(
        "https://api.github.com/repos/octocat/hello-world/contents/.github/REVIEW_GUIDE.md"
    ).mock(return_value=httpx.Response(200, text="# Style Guide\n"))

    style_finding = Finding(
        file="foo.py", line=1, comment="use snake_case", category="style", severity="warning"
    )
    monkeypatch.setattr(
        "code_review_agent.pipeline.generate_style_findings",
        lambda client, diff, style_guide: [style_finding],
    )

    with httpx.Client() as client:
        findings = generate_findings_for_pr(client, MagicMock(), "octocat", "hello-world", 42)

    assert style_finding in findings
    assert any(f.category == "test-coverage" for f in findings)
