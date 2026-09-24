import re

_HUNK_HEADER_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def added_lines_by_file(diff: str) -> dict[str, dict[int, str]]:
    """Map each file in the diff to {new_file_line_number: added_line_content}."""
    result: dict[str, dict[int, str]] = {}
    current_file: str | None = None
    current_line_num: int | None = None

    for line in diff.splitlines():
        if line.startswith("diff --git "):
            current_file = None
            current_line_num = None
            continue

        if line.startswith("+++ "):
            path = line[len("+++ ") :]
            current_file = None if path == "/dev/null" else path.removeprefix("b/")
            current_line_num = None
            continue

        header_match = _HUNK_HEADER_RE.match(line)
        if header_match:
            current_line_num = int(header_match.group(1))
            continue

        if current_file is None or current_line_num is None:
            continue

        if line.startswith("+"):
            result.setdefault(current_file, {})[current_line_num] = line[1:]
            current_line_num += 1
        elif line.startswith("-"):
            pass
        elif line.startswith("\\"):
            pass
        else:
            current_line_num += 1

    return result
