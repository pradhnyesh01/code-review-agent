import fnmatch
import re
from posixpath import basename

from code_review_agent.findings import Finding

TEST_FILE_PATTERNS = ("test_*.py", "*_test.py")
_DEF_RE = re.compile(r"^\+\s*(async\s+)?def\s+\w+\s*\(")
_HUNK_HEADER_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")
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
    current_file: str | None = None
    current_line_num: int | None = None
    hunk_first_new_def_line: int | None = None

    def flush_hunk() -> None:
        nonlocal hunk_first_new_def_line
        if hunk_first_new_def_line is not None and current_file is not None:
            findings.append(
                Finding(
                    file=current_file,
                    line=hunk_first_new_def_line,
                    comment=COMMENT,
                    category="test-coverage",
                    severity="blocker",
                )
            )
        hunk_first_new_def_line = None

    for line in diff.splitlines():
        if line.startswith("diff --git "):
            flush_hunk()
            current_file = None
            current_line_num = None
            continue

        if line.startswith("+++ "):
            flush_hunk()
            path = line[len("+++ ") :]
            if path == "/dev/null":
                current_file = None
            else:
                current_file = path[2:] if path.startswith("b/") else path
            current_line_num = None
            continue

        header_match = _HUNK_HEADER_RE.match(line)
        if header_match:
            flush_hunk()
            current_line_num = int(header_match.group(1))
            continue

        is_python_target = (
            current_file is not None
            and current_file.endswith(".py")
            and not _is_test_file(current_file)
        )
        if not is_python_target or current_line_num is None:
            continue

        if line.startswith("+"):
            if hunk_first_new_def_line is None and _DEF_RE.match(line):
                hunk_first_new_def_line = current_line_num
            current_line_num += 1
        elif line.startswith("-"):
            pass
        elif line.startswith("\\"):
            pass
        else:
            current_line_num += 1

    flush_hunk()
    return findings
