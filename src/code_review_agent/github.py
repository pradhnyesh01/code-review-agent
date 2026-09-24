import httpx

from code_review_agent.findings import Finding

GITHUB_API = "https://api.github.com"
STYLE_GUIDE_PATH = ".github/REVIEW_GUIDE.md"
DEFAULT_REVIEW_BODY = "Automated review from code-review-agent."


def fetch_pr_diff(client: httpx.Client, owner: str, repo: str, pr_number: int) -> str:
    response = client.get(
        f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}",
        headers={"Accept": "application/vnd.github.v3.diff"},
    )
    response.raise_for_status()
    return response.text


def fetch_style_guide(client: httpx.Client, owner: str, repo: str) -> str:
    response = client.get(
        f"{GITHUB_API}/repos/{owner}/{repo}/contents/{STYLE_GUIDE_PATH}",
        headers={"Accept": "application/vnd.github.v3.raw"},
    )
    response.raise_for_status()
    return response.text


def post_review(
    client: httpx.Client,
    owner: str,
    repo: str,
    pr_number: int,
    findings: list[Finding],
    body: str = DEFAULT_REVIEW_BODY,
) -> dict:
    # event is always COMMENT, never REQUEST_CHANGES, regardless of severity —
    # see docs/adr/0002-review-verdict-always-comment.md
    response = client.post(
        f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}/reviews",
        json={
            "body": body,
            "event": "COMMENT",
            "comments": [
                {"path": finding.file, "line": finding.line, "body": finding.comment}
                for finding in findings
            ],
        },
    )
    response.raise_for_status()
    return response.json()
