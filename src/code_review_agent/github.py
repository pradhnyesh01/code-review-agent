import httpx

GITHUB_API = "https://api.github.com"
STYLE_GUIDE_PATH = ".github/REVIEW_GUIDE.md"


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
