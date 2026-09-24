import httpx

GITHUB_API = "https://api.github.com"


def fetch_pr_diff(client: httpx.Client, owner: str, repo: str, pr_number: int) -> str:
    response = client.get(
        f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}",
        headers={"Accept": "application/vnd.github.v3.diff"},
    )
    response.raise_for_status()
    return response.text
