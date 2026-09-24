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

## Development

```bash
uv run pytest       # tests
uv run pyright src tests   # typecheck
```

This is a work in progress — see the open issues on this repo for the current build order. A full design-doc README (what didn't work, known failure modes, deployment) will replace this once the agent is deployed.
