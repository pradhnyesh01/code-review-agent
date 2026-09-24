# Code Review Agent

An agent that reviews GitHub pull requests against a repo's own style guide and flags new logic that lacks test coverage, posting the results back as a single GitHub review.

## Language

**Target Repo**:
The repository whose pull requests the agent reviews. The fine-grained PAT is scoped to exactly one.
_Avoid_: test repo (ambiguous with this project's own pytest suite)

**Demo Repo**:
The specific Target Repo used for the public portfolio deliverable — a separate throwaway repo, not this code-review-agent repo itself.

**Style Guide**:
The single markdown file in a Target Repo, at a fixed conventional path (`.github/REVIEW_GUIDE.md`), that the agent checks a diff against. Required to exist; the agent fails loudly rather than silently skipping the check if it's missing.
_Avoid_: style/architecture guide, style/architecture doc

**Finding**:
A single structured review output for one location in a diff: `file`, `line`, `comment`, `category`, `severity`.
_Avoid_: comment, issue (comment collides with the GitHub PR comment it eventually becomes)

**Category**:
A Finding's classification: `style` (violates the Style Guide) or `test-coverage` (new logic with no corresponding test change).

**Severity**:
A Finding's urgency: `nit`, `warning`, or `blocker`. Style findings cap at `warning`; test-coverage findings may reach `blocker`.

**Review**:
The single batched GitHub `PullRequestReview` object the agent posts, bundling every Finding as an inline comment. v1 triggers on `opened` and `reopened` only — not `synchronize` — so a PR gets exactly one Review; re-reviewing on later pushes is out of scope.
_Avoid_: comment, individual comments
