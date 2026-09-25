import fnmatch
import re
from itertools import groupby
from posixpath import basename

from code_review_agent.diff_parsing import iter_added_lines
from code_review_agent.findings import Finding

TEST_FILE_PATTERNS = ("test_*.py", "*_test.py")
_DEF_RE = re.compile(r"^\s*(async\s+)?def\s+\w+\s*\(")
COMMENT = (
    "This hunk adds a new function/method with no corresponding test file "
    "changes in this diff."
)


def _is_test_file(path: str) -> bool:
    name = basename(path)
    return any(fnmatch.fnmatch(name, pattern) for pattern in TEST_FILE_PATTERNS)


def _diff_touches_a_test_file(diff: str) -> bool:
    for line in diff.splitlines():
        if not line.startswith("+++ "):
            continue
        path = line[len("+++ ") :]
        if path == "/dev/null":
            continue
        if path.startswith("b/"):
            path = path[2:]
        if _is_test_file(path):
            return True
    return False


def generate_test_coverage_findings(diff: str) -> list[Finding]:
    if _diff_touches_a_test_file(diff):
        return []

    findings: list[Finding] = []
    target_lines = (
        added_line
        for added_line in iter_added_lines(diff)
        if added_line.file.endswith(".py") and not _is_test_file(added_line.file)
    )
    for (file, _hunk_index), hunk_lines in groupby(
        target_lines, key=lambda added_line: (added_line.file, added_line.hunk_index)
    ):
        first_def_line = next(
            (line.line_num for line in hunk_lines if _DEF_RE.match(line.content)),
            None,
        )
        if first_def_line is not None:
            findings.append(
                Finding(
                    file=file,
                    line=first_def_line,
                    comment=COMMENT,
                    category="test-coverage",
                    severity="blocker",
                )
            )

    return findings
