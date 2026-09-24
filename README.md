# code-review-agent

Agent that reviews GitHub pull requests against a repo's style guide and flags new logic that lacks test coverage. See [plan.md](plan.md), [CLAUDE.md](CLAUDE.md), and [CONTEXT.md](CONTEXT.md) for the design.

## Setup

```bash
uv sync
```

Then set up a GitHub PAT scoped to the Target Repo you want to review (see `docs/agents/` for the workflow used to provision it), and an OpenAI API key. Both are read from the `GITHUB_PAT` and `OPENAI_API_KEY` environment variables, or from a `.env` file in this directory.

## Usage

Review a pull request's diff against the Target Repo's Style Guide (`.github/REVIEW_GUIDE.md`) and print the resulting findings, one per line as JSON:

```bash
uv run code-review-agent <owner>/<repo> <pr-number>
```

## Webhook

`src/code_review_agent/webhook.py` wraps the same pipeline in a FastAPI `/webhook` endpoint, so opening
a PR on the Target Repo triggers a review automatically instead of running the CLI by hand.

Set `GITHUB_WEBHOOK_SECRET` (in addition to `GITHUB_PAT` and `OPENAI_API_KEY`) to the secret configured
on the GitHub webhook — every request's `X-Hub-Signature-256` header is verified against it via
HMAC-SHA256, and anything with a missing or invalid signature is rejected with `401`. Only `pull_request`
events with `action` of `opened` or `reopened` trigger a review; everything else (`synchronize`, `ping`,
other event types) returns `200` with `{"status": "ignored"}` and does no work.

Run it locally with:

```bash
uv run uvicorn code_review_agent.webhook:app --reload
```

Deployed on Railway at `https://code-review-agent-production-f3f0.up.railway.app`, with the webhook
registered on the Demo Repo (`pradhnyesh01/code-review-agent-demo`, Settings → Webhooks →
`https://code-review-agent-production-f3f0.up.railway.app/webhook`, content type `application/json`,
subscribed to "Pull requests" events). Verified end-to-end against real PRs on the Demo Repo, including
both the style-guide and test-coverage Finding passes.

To deploy elsewhere: push this repo to Railway (or Render) — the included `Procfile` gives it a start
command — and set `GITHUB_PAT`, `OPENAI_API_KEY`, and `GITHUB_WEBHOOK_SECRET` as environment variables on
the deployed service. Note: Railway's dashboard "Redeploy" re-runs the exact commit/image already live,
not `main`'s latest commit — to ship a new commit, trigger a fresh deploy from GitHub in the dashboard,
or run `railway up` (after `railway link`) to deploy the local checkout directly.

## Development

```bash
uv run pytest       # tests
uv run pyright src tests   # typecheck
```

This is a work in progress — see the open issues on this repo for the current build order. A full design-doc README (what didn't work, known failure modes, deployment) will replace this once the agent is deployed.
