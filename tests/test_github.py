import httpx
import pytest
import respx

from code_review_agent.github import fetch_pr_diff


@respx.mock
def test_fetch_pr_diff_returns_diff_text():
    diff_text = (
        "diff --git a/foo.py b/foo.py\n"
        "index 1234567..89abcde 100644\n"
        "--- a/foo.py\n"
        "+++ b/foo.py\n"
        "@@ -1 +1 @@\n"
        "-old line\n"
        "+new line\n"
    )
    route = respx.get("https://api.github.com/repos/octocat/hello-world/pulls/42").mock(
        return_value=httpx.Response(200, text=diff_text)
    )

    with httpx.Client() as client:
        result = fetch_pr_diff(client, "octocat", "hello-world", 42)

    assert result == diff_text
    assert route.calls.last.request.headers["Accept"] == "application/vnd.github.v3.diff"


@respx.mock
def test_fetch_pr_diff_raises_on_not_found():
    respx.get("https://api.github.com/repos/octocat/hello-world/pulls/999").mock(
        return_value=httpx.Response(404, json={"message": "Not Found"})
    )

    with httpx.Client() as client:
        with pytest.raises(httpx.HTTPStatusError):
            fetch_pr_diff(client, "octocat", "hello-world", 999)
