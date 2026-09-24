from typing import Literal

from openai import OpenAI
from pydantic import BaseModel

from code_review_agent.diff_parsing import added_lines_by_file
from code_review_agent.findings import Finding

DEFAULT_MODEL = "gpt-4o-mini"

SYSTEM_PROMPT = (
    "You are a meticulous code reviewer. Compare the given pull request diff "
    "against the target repository's style guide and report every style "
    "guide violation as a finding. Only flag lines that actually appear in "
    "the diff, using the file path and line number shown there. For each "
    "finding, set `quote` to the exact line of code you are flagging, "
    "copied character-for-character from the diff — never paraphrased or "
    "reconstructed from memory. Before reporting a naming-convention "
    "violation, spell out the identifier's exact characters and confirm it "
    "truly breaks the guide's stated convention; never report a finding "
    "whose violating name and suggested replacement are identical, and "
    "never report code that already conforms to the guide. If there are no "
    "violations, return an empty list of findings."
)


class StyleFinding(BaseModel):
    file: str
    line: int
    quote: str
    comment: str
    severity: Literal["nit", "warning"]


class StyleReview(BaseModel):
    findings: list[StyleFinding]


def _normalize(text: str) -> str:
    return " ".join(text.split())


def _is_grounded(finding: StyleFinding, added_lines: dict[str, dict[int, str]]) -> bool:
    line_content = added_lines.get(finding.file, {}).get(finding.line)
    if line_content is None:
        return False
    quote = _normalize(finding.quote)
    return bool(quote) and quote in _normalize(line_content)


def generate_style_findings(client: OpenAI, diff: str, style_guide: str) -> list[Finding]:
    completion = client.chat.completions.parse(
        model=DEFAULT_MODEL,
        temperature=0,
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

    added_lines = added_lines_by_file(diff)

    return [
        Finding(
            file=finding.file,
            line=finding.line,
            comment=finding.comment,
            category="style",
            severity=finding.severity,
        )
        for finding in message.parsed.findings
        if _is_grounded(finding, added_lines)
    ]
