import argparse
import os
import sys

import httpx
from dotenv import load_dotenv
from openai import OpenAI

from code_review_agent.github import fetch_pr_diff, fetch_style_guide, post_review
from code_review_agent.review import generate_style_findings


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Review a GitHub pull request's diff against its repo's style guide."
    )
    parser.add_argument("repo", help="Target repo as owner/repo")
    parser.add_argument("pr_number", type=int, help="Pull request number")
    return parser.parse_args(argv)


def require_env(name: str) -> str | None:
    value = os.environ.get(name)
    if not value:
        print(f"error: {name} environment variable is not set", file=sys.stderr)
    return value


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    args = parse_args(argv if argv is not None else sys.argv[1:])

    owner, _, repo = args.repo.partition("/")
    if not owner or not repo:
        print(f"error: repo must be in owner/repo form, got {args.repo!r}", file=sys.stderr)
        return 2

    token = require_env("GITHUB_PAT")
    if not token:
        return 2

    openai_api_key = require_env("OPENAI_API_KEY")
    if not openai_api_key:
        return 2

    openai_client = OpenAI(api_key=openai_api_key)

    with httpx.Client(headers={"Authorization": f"Bearer {token}"}) as client:
        diff = fetch_pr_diff(client, owner, repo, args.pr_number)
        style_guide = fetch_style_guide(client, owner, repo)

        findings = generate_style_findings(openai_client, diff, style_guide)
        for finding in findings:
            print(finding.model_dump_json())

        review = post_review(client, owner, repo, args.pr_number, findings)

    print(f"Posted review: {review.get('html_url', review)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
