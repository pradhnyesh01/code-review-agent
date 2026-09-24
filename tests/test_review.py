from unittest.mock import MagicMock

import pytest

from code_review_agent.findings import Finding
from code_review_agent.review import StyleFinding, StyleReview, generate_style_findings


def _mock_openai_client(parsed: StyleReview | None, refusal: str | None = None) -> MagicMock:
    client = MagicMock()
    message = MagicMock(parsed=parsed, refusal=refusal)
    completion = MagicMock()
    completion.choices = [MagicMock(message=message)]
    client.chat.completions.parse.return_value = completion
    return client


def test_generate_style_findings_returns_findings_from_parsed_response():
    parsed = StyleReview(
        findings=[
            StyleFinding(file="foo.py", line=3, comment="use snake_case", severity="warning"),
            StyleFinding(file="bar.py", line=10, comment="missing docstring", severity="nit"),
        ]
    )
    client = _mock_openai_client(parsed)

    findings = generate_style_findings(client, diff="a diff", style_guide="a guide")

    assert findings == [
        Finding(file="foo.py", line=3, comment="use snake_case", category="style", severity="warning"),
        Finding(file="bar.py", line=10, comment="missing docstring", category="style", severity="nit"),
    ]


def test_generate_style_findings_sends_diff_and_style_guide_to_openai():
    client = _mock_openai_client(StyleReview(findings=[]))

    generate_style_findings(client, diff="the-diff-text", style_guide="the-guide-text")

    _, kwargs = client.chat.completions.parse.call_args
    content = " ".join(message["content"] for message in kwargs["messages"])
    assert "the-diff-text" in content
    assert "the-guide-text" in content
    assert kwargs["response_format"] is StyleReview


def test_generate_style_findings_raises_when_model_refuses():
    client = _mock_openai_client(parsed=None, refusal="I can't help with that")

    with pytest.raises(RuntimeError, match="I can't help with that"):
        generate_style_findings(client, diff="a diff", style_guide="a guide")


def test_generate_style_findings_raises_with_fallback_message_when_no_refusal_given():
    client = _mock_openai_client(parsed=None, refusal=None)

    with pytest.raises(RuntimeError, match="no reason given"):
        generate_style_findings(client, diff="a diff", style_guide="a guide")


def test_generate_style_findings_propagates_api_errors():
    client = MagicMock()
    client.chat.completions.parse.side_effect = RuntimeError("context_length_exceeded")

    with pytest.raises(RuntimeError, match="context_length_exceeded"):
        generate_style_findings(client, diff="a diff", style_guide="a guide")
