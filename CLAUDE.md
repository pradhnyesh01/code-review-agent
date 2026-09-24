# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

Tickets #2 (fetch and print a PR diff via CLI), #3 (generate structured style findings from a diff, no
posting), and #4 (post findings as a single GitHub Review) are implemented. The project is a
`uv`-managed Python package at `src/code_review_agent/`, with a `code-review-agent` console script entry
point. The CLI fetches a PR's diff and the Target Repo's Style Guide (`.github/REVIEW_GUIDE.md`), sends
both to OpenAI via Structured Outputs, and posts the resulting `Finding`s back to GitHub as one batched
`PullRequestReview` (event always `COMMENT` — see `docs/adr/0002-review-verdict-always-comment.md`).

Ticket #5 (wrap the pipeline in a FastAPI webhook) is fully done, deployment included:
`src/code_review_agent/webhook.py` exposes `/webhook`, verifies `X-Hub-Signature-256` via HMAC-SHA256
against `GITHUB_WEBHOOK_SECRET`, and runs the same fetch → generate → post pipeline only for
`pull_request` events with `action` `opened` or `reopened`. It's deployed on Railway
(`https://code-review-agent-production-f3f0.up.railway.app`), the webhook is registered on the Demo Repo
(`pradhnyesh01/code-review-agent-demo`), and an end-to-end run against real PRs has been confirmed —
see the Webhook section of `README.md` for the deploy steps.

Ticket #6 (Python test-coverage check as a second Finding pass) is implemented and verified live:
`src/code_review_agent/test_coverage.py` parses the raw diff directly (no LLM call) for hunks that add a
new top-level function or method (`+def ...`) in a non-test `.py` file, and only emits a
`category: test-coverage`, `severity: blocker` `Finding` when no `test_*.py`/`*_test.py` file appears
anywhere in the same diff. `pipeline.py` runs it alongside `generate_style_findings` so both land in the
same posted Review; confirmed on a real Demo Repo PR after deploying.

Note for future deploys: Railway's dashboard "Redeploy" re-runs the *same* commit/image already live —
it does not pull `main`'s latest commit. To ship a new commit, either connect a fresh deploy from
GitHub's latest commit in the dashboard, or run `railway up` from the repo root (after `railway link`)
to deploy the local checkout directly.

Build/test commands:

```bash
uv sync                      # install dependencies
uv run pytest                # run tests
uv run pyright src tests     # typecheck
uv run code-review-agent <owner>/<repo> <pr-number>   # run the CLI
```

See the open issues on this repo (starting from #1) for the remaining build order.

## Goal

Build an agent that reviews GitHub pull requests against a repo's own style/architecture guide, posts
inline review comments, and flags new logic that lacks test coverage. It's meant to be a resume-ready
project: real API integrations, real write-side effects (posting to GitHub), deployed and demoable — not
just a local script.

## Planned architecture

```
GitHub PR event (webhook)
        |
        v
FastAPI endpoint (/webhook)
        |
        v
Fetch PR diff via GitHub API
        |
        v
Agent loop:
  1. Read diff
  2. Read style/architecture guide (markdown file in repo)
  3. Check diff against guide
  4. Check: does new logic have corresponding test changes?
  5. Produce structured findings (Pydantic model: file, line, comment, severity)
        |
        v
Post review comments back via GitHub API
```

## Build order (see plan.md for full detail)

1. **Local script, no webhook** — CLI script that fetches a PR's diff via `PyGithub` or raw REST calls and
   prints it, to confirm GitHub API access works.
2. **LLM review step** — feed diff + style guide into a single prompt, parse the response into structured
   JSON via Pydantic (file, line, comment, severity), print findings without posting.
3. **Post comments back to GitHub** — use GitHub's "create review comment" endpoint; test against a
   throwaway repo first, not a real PR.
4. **Wrap in FastAPI + webhook** — turn the script into a `/webhook` endpoint, deploy to Railway/Render,
   register the webhook on the test repo.
5. **Test-coverage check** — a second pass that detects new functions/logic in the diff with no
   corresponding test changes, flagged separately from style comments with its own severity label.

## Key stack decisions

- **No LangChain/LangGraph** — the agent loop is hand-rolled tool-calling, intentionally kept simple and
  debuggable.
- **No GitHub App / OAuth for v1** — a fine-grained PAT scoped to a single test repo is sufficient.
- **No database for v1** — each PR review is stateless.
- LLM backend is OpenAI, via Structured Outputs (see `docs/adr/0001-openai-for-llm-backend.md`).

## Out of scope (v1)

- Multi-repo support / GitHub App installation flow
- Fine-tuning or custom model training
- Multi-agent orchestration

## Agent skills

### Issue tracker

Issues are tracked in this repo's GitHub Issues (uses the `gh` CLI). See `docs/agents/issue-tracker.md`.

### Triage labels

Default five canonical roles (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout: one `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.
