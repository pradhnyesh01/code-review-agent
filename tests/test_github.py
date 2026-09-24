import json

import httpx
import pytest
import respx

from code_review_agent.findings import Finding
from code_review_agent.github import fetch_pr_diff, fetch_style_guide, post_review


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


@respx.mock
def test_fetch_style_guide_returns_file_contents():
    guide_text = "# Style Guide\n\nUse snake_case for functions.\n"
    route = respx.get(
        "https://api.github.com/repos/octocat/hello-world/contents/.github/REVIEW_GUIDE.md"
    ).mock(return_value=httpx.Response(200, text=guide_text))

    with httpx.Client() as client:
        result = fetch_style_guide(client, "octocat", "hello-world")

    assert result == guide_text
    assert route.calls.last.request.headers["Accept"] == "application/vnd.github.v3.raw"


@respx.mock
def test_fetch_style_guide_raises_when_missing():
    respx.get(
        "https://api.github.com/repos/octocat/hello-world/contents/.github/REVIEW_GUIDE.md"
    ).mock(return_value=httpx.Response(404, json={"message": "Not Found"}))

    with httpx.Client() as client:
        with pytest.raises(httpx.HTTPStatusError):
            fetch_style_guide(client, "octocat", "hello-world")


@respx.mock
def test_post_review_posts_one_comment_per_finding_with_event_comment():
    findings = [
        Finding(file="foo.py", line=3, comment="use snake_case", category="style", severity="warning"),
        Finding(file="bar.py", line=10, comment="missing docstring", category="style", severity="nit"),
    ]
    route = respx.post(
        "https://api.github.com/repos/octocat/hello-world/pulls/42/reviews"
    ).mock(return_value=httpx.Response(200, json={"id": 1, "html_url": "https://github.com/octocat/hello-world/pull/42#pullrequestreview-1"}))

    with httpx.Client() as client:
        result = post_review(client, "octocat", "hello-world", 42, findings)

    sent_body = json.loads(route.calls.last.request.content)
    assert sent_body["event"] == "COMMENT"
    assert sent_body["comments"] == [
        {"path": "foo.py", "line": 3, "body": "use snake_case"},
        {"path": "bar.py", "line": 10, "body": "missing docstring"},
    ]
    assert result["html_url"].endswith("#pullrequestreview-1")


@respx.mock
def test_post_review_always_uses_event_comment_regardless_of_severity():
    findings = [
        Finding(file="foo.py", line=3, comment="missing tests", category="test-coverage", severity="blocker"),
    ]
    route = respx.post(
        "https://api.github.com/repos/octocat/hello-world/pulls/42/reviews"
    ).mock(return_value=httpx.Response(200, json={"id": 2}))

    with httpx.Client() as client:
        post_review(client, "octocat", "hello-world", 42, findings)

    sent_body = json.loads(route.calls.last.request.content)
    assert sent_body["event"] == "COMMENT"


@respx.mock
def test_post_review_posts_empty_comments_when_no_findings():
    route = respx.post(
        "https://api.github.com/repos/octocat/hello-world/pulls/42/reviews"
    ).mock(return_value=httpx.Response(200, json={"id": 3}))

    with httpx.Client() as client:
        post_review(client, "octocat", "hello-world", 42, [])

    sent_body = json.loads(route.calls.last.request.content)
    assert sent_body["comments"] == []
    assert sent_body["event"] == "COMMENT"


@respx.mock
def test_post_review_raises_on_error():
    respx.post("https://api.github.com/repos/octocat/hello-world/pulls/42/reviews").mock(
        return_value=httpx.Response(422, json={"message": "Validation Failed"})
    )

    with httpx.Client() as client:
        with pytest.raises(httpx.HTTPStatusError):
            post_review(client, "octocat", "hello-world", 42, [])
