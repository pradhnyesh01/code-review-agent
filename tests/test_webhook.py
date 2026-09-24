import hashlib
import hmac
import json

import httpx
import respx
from fastapi.testclient import TestClient

from code_review_agent.findings import Finding
from code_review_agent.webhook import app

client = TestClient(app)


def sign(secret: str, body: bytes) -> str:
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def pull_request_payload(action: str, pr_number: int = 42) -> dict:
    return {
        "action": action,
        "pull_request": {"number": pr_number},
        "repository": {"name": "hello-world", "owner": {"login": "octocat"}},
    }


def post_webhook(monkeypatch, payload: dict, event: str = "pull_request", secret: str = "test-secret"):
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", secret)
    body = json.dumps(payload).encode()
    return client.post(
        "/webhook",
        content=body,
        headers={
            "X-Hub-Signature-256": sign(secret, body),
            "X-GitHub-Event": event,
            "Content-Type": "application/json",
        },
    )


def test_rejects_request_with_missing_signature(monkeypatch):
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "test-secret")
    payload = pull_request_payload("opened")

    response = client.post(
        "/webhook",
        content=json.dumps(payload).encode(),
        headers={"X-GitHub-Event": "pull_request", "Content-Type": "application/json"},
    )

    assert response.status_code == 401


def test_rejects_request_with_invalid_signature(monkeypatch):
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "test-secret")
    payload = pull_request_payload("opened")

    response = client.post(
        "/webhook",
        content=json.dumps(payload).encode(),
        headers={
            "X-Hub-Signature-256": "sha256=" + "0" * 64,
            "X-GitHub-Event": "pull_request",
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 401


def test_rejects_request_signed_with_wrong_secret(monkeypatch):
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "test-secret")
    payload = pull_request_payload("opened")
    body = json.dumps(payload).encode()

    response = client.post(
        "/webhook",
        content=body,
        headers={
            "X-Hub-Signature-256": sign("some-other-secret", body),
            "X-GitHub-Event": "pull_request",
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 401


def test_ignores_non_pull_request_events(monkeypatch):
    response = post_webhook(monkeypatch, {"zen": "hello"}, event="ping")

    assert response.status_code == 200
    assert response.json()["status"] == "ignored"


def test_ignores_synchronize_action(monkeypatch):
    response = post_webhook(monkeypatch, pull_request_payload("synchronize"))

    assert response.status_code == 200
    assert response.json()["status"] == "ignored"


@respx.mock
def test_triggers_review_pipeline_on_opened_action(monkeypatch):
    monkeypatch.setenv("GITHUB_PAT", "test-token")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    diff_text = "diff --git a/foo.py b/foo.py\n+added line\n"
    guide_text = "# Style Guide\n"
    respx.get("https://api.github.com/repos/octocat/hello-world/pulls/42").mock(
        return_value=httpx.Response(200, text=diff_text)
    )
    respx.get(
        "https://api.github.com/repos/octocat/hello-world/contents/.github/REVIEW_GUIDE.md"
    ).mock(return_value=httpx.Response(200, text=guide_text))
    review_url = "https://github.com/octocat/hello-world/pull/42#pullrequestreview-1"
    post_route = respx.post(
        "https://api.github.com/repos/octocat/hello-world/pulls/42/reviews"
    ).mock(return_value=httpx.Response(200, json={"id": 1, "html_url": review_url}))

    findings = [Finding(file="foo.py", line=1, comment="use snake_case", category="style", severity="warning")]

    def fake_generate_style_findings(openai_client, diff, style_guide):
        assert diff == diff_text
        assert style_guide == guide_text
        return findings

    monkeypatch.setattr(
        "code_review_agent.pipeline.generate_style_findings", fake_generate_style_findings
    )

    response = post_webhook(monkeypatch, pull_request_payload("opened"))

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "reviewed"
    assert body["findings"] == 1
    assert body["review_url"] == review_url
    sent_body = json.loads(post_route.calls.last.request.content)
    assert sent_body["event"] == "COMMENT"


@respx.mock
def test_triggers_review_pipeline_on_reopened_action(monkeypatch):
    monkeypatch.setenv("GITHUB_PAT", "test-token")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    respx.get("https://api.github.com/repos/octocat/hello-world/pulls/42").mock(
        return_value=httpx.Response(200, text="diff --git a/foo.py b/foo.py\n")
    )
    respx.get(
        "https://api.github.com/repos/octocat/hello-world/contents/.github/REVIEW_GUIDE.md"
    ).mock(return_value=httpx.Response(200, text="# Style Guide\n"))
    respx.post("https://api.github.com/repos/octocat/hello-world/pulls/42/reviews").mock(
        return_value=httpx.Response(200, json={"id": 2, "html_url": "https://example.com/2"})
    )
    monkeypatch.setattr(
        "code_review_agent.pipeline.generate_style_findings", lambda openai_client, diff, style_guide: []
    )

    response = post_webhook(monkeypatch, pull_request_payload("reopened"))

    assert response.status_code == 200
    assert response.json()["status"] == "reviewed"


def test_returns_error_when_github_pat_missing(monkeypatch):
    monkeypatch.delenv("GITHUB_PAT", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    response = post_webhook(monkeypatch, pull_request_payload("opened"))

    assert response.status_code == 500
