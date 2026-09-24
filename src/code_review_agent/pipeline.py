import httpx
from openai import OpenAI

from code_review_agent.findings import Finding
from code_review_agent.github import fetch_pr_diff, fetch_style_guide
from code_review_agent.review import generate_style_findings


def generate_findings_for_pr(
    client: httpx.Client,
    openai_client: OpenAI,
    owner: str,
    repo: str,
    pr_number: int,
) -> list[Finding]:
    diff = fetch_pr_diff(client, owner, repo, pr_number)
    style_guide = fetch_style_guide(client, owner, repo)
    return generate_style_findings(openai_client, diff, style_guide)
