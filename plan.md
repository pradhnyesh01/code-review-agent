# Code Review Agent — Project Plan

## Goal
Build an agent that reviews GitHub pull requests against a repo's own style/architecture guide, posts inline comments, and flags new logic that lacks test coverage. Resume-ready: real API integrations, real write-side effects, deployed and demoable.

## Accounts / Keys (all free)
- [ ] GitHub account (existing) — create a fine-grained Personal Access Token scoped to one test repo
- [ ] LLM API key — Anthropic or OpenAI (pay-as-you-go, pennies at this scale), OR Ollama locally (free, no signup)
- [ ] Railway or Render account (free tier) — for eventual deployment

## Architecture

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

## Build Order

### Step 1 — Local script, no webhook
- CLI script: takes a PR number, fetches the diff via `PyGithub` or raw REST calls
- Just print the diff to confirm GitHub API access works
- Milestone: can pull any PR's diff on command

### Step 2 — Add LLM review step
- Feed diff + style guide into a single prompt
- Parse response into structured JSON via Pydantic (file, line, comment, severity)
- Print findings, no posting yet
- Milestone: agent produces structured, validated review output

### Step 3 — Post comments back to GitHub
- Use GitHub's "create review comment" endpoint
- Test on a throwaway repo first — avoid spamming real PRs
- Milestone: agent posts real inline comments on a live PR

### Step 4 — Wrap in FastAPI + webhook
- Turn script into a `/webhook` endpoint
- Deploy to Railway/Render
- Register webhook on test repo pointing at deployed URL
- Milestone: opening a PR automatically triggers a review, end to end

### Step 5 — Test-coverage check (differentiator)
- Second pass: detect new functions/logic in the diff with no corresponding test changes
- Flag separately from style comments, with its own severity label
- Milestone: agent distinguishes "style nit" from "reliability risk"

## Stack Decisions
- **No LangChain/LangGraph** — hand-rolled tool-calling loop; simpler, more debuggable, reads better in the README
- **No GitHub App / OAuth** for v1 — PAT + single test repo is enough for a portfolio piece
- **No database** for v1 — stateless per-PR review is sufficient

## Deliverables for Resume
- [ ] Deployed, live URL (not "clone and run locally")
- [ ] README written as a design doc: what didn't work, why X over Y, known failure modes
- [ ] 5–10 tests covering the diff-parsing and structured-output logic
- [ ] Demo repo with a handful of real PRs showing the agent's comments

## Out of Scope (v1)
- Multi-repo support / GitHub App installation flow
- Fine-tuning or custom model training
- Multi-agent orchestration
