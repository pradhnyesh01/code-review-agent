from typing import Literal

from openai import OpenAI
from pydantic import BaseModel

from code_review_agent.findings import Finding

DEFAULT_MODEL = "gpt-4o-mini"

SYSTEM_PROMPT = (
    "You are a meticulous code reviewer. Compare the given pull request diff "
    "against the target repository's style guide and report every style "
    "guide violation as a finding. Only flag lines that actually appear in "
    "the diff, using the file path and line number shown there. If there "
    "are no violations, return an empty list of findings."
)


class StyleFinding(BaseModel):
    file: str
    line: int
    comment: str
    severity: Literal["nit", "warning"]


class StyleReview(BaseModel):
    findings: list[StyleFinding]


def generate_style_findings(client: OpenAI, diff: str, style_guide: str) -> list[Finding]:
    completion = client.chat.completions.parse(
        model=DEFAULT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Style guide:\n{style_guide}\n\nDiff:\n{diff}",
            },
        ],
        response_format=StyleReview,
    )
    message = completion.choices[0].message
    if message.parsed is None:
        reason = message.refusal or "no reason given"
        raise RuntimeError(f"OpenAI did not return a parsed review: {reason}")

    return [
        Finding(
            file=finding.file,
            line=finding.line,
            comment=finding.comment,
            category="style",
            severity=finding.severity,
        )
        for finding in message.parsed.findings
    ]
