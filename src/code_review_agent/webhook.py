import hashlib
import hmac
import os

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request
from openai import OpenAI

from code_review_agent.github import post_review
from code_review_agent.pipeline import generate_findings_for_pr

load_dotenv()

app = FastAPI()

TRIGGER_ACTIONS = {"opened", "reopened"}


def verify_signature(payload: bytes, signature_header: str | None, secret: str) -> bool:
    if not signature_header:
        return False
    digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    expected_header = f"sha256={digest}"
    return hmac.compare_digest(expected_header, signature_header)


@app.post("/webhook")
async def handle_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None),
    x_github_event: str | None = Header(default=None),
) -> dict:
    body = await request.body()

    secret = os.environ.get("GITHUB_WEBHOOK_SECRET")
    if not secret:
        raise HTTPException(status_code=500, detail="GITHUB_WEBHOOK_SECRET is not configured")
    if not verify_signature(body, x_hub_signature_256, secret):
        raise HTTPException(status_code=401, detail="invalid signature")

    payload = await request.json()

    if x_github_event != "pull_request" or payload.get("action") not in TRIGGER_ACTIONS:
        return {"status": "ignored"}

    owner = payload["repository"]["owner"]["login"]
    repo = payload["repository"]["name"]
    pr_number = payload["pull_request"]["number"]

    token = os.environ.get("GITHUB_PAT")
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not token or not openai_api_key:
        raise HTTPException(
            status_code=500, detail="GITHUB_PAT or OPENAI_API_KEY is not configured"
        )

    openai_client = OpenAI(api_key=openai_api_key)
    with httpx.Client(headers={"Authorization": f"Bearer {token}"}) as client:
        findings = generate_findings_for_pr(client, openai_client, owner, repo, pr_number)
        review = post_review(client, owner, repo, pr_number, findings)

    return {
        "status": "reviewed",
        "findings": len(findings),
        "review_url": review.get("html_url"),
    }
