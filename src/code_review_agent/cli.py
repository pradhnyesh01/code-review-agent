import argparse
import os
import sys

import httpx
from dotenv import load_dotenv

from code_review_agent.github import fetch_pr_diff


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Print a GitHub pull request's diff.")
    parser.add_argument("repo", help="Target repo as owner/repo")
    parser.add_argument("pr_number", type=int, help="Pull request number")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    args = parse_args(argv if argv is not None else sys.argv[1:])

    owner, _, repo = args.repo.partition("/")
    if not owner or not repo:
        print(f"error: repo must be in owner/repo form, got {args.repo!r}", file=sys.stderr)
        return 2

    token = os.environ.get("GITHUB_PAT")
    if not token:
        print("error: GITHUB_PAT environment variable is not set", file=sys.stderr)
        return 2

    with httpx.Client(headers={"Authorization": f"Bearer {token}"}) as client:
        diff = fetch_pr_diff(client, owner, repo, args.pr_number)

    print(diff)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
