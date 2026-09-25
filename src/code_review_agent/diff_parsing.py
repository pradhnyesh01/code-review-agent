import re
from dataclasses import dataclass
from typing import Iterator

_HUNK_HEADER_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


@dataclass(frozen=True)
class AddedLine:
    """A single added (+) line from a unified diff, with its position in the new file."""

    file: str
    line_num: int
    content: str
    hunk_index: int


def iter_added_lines(diff: str) -> Iterator[AddedLine]:
    """Walk a unified diff and yield each added line, in order.

    `hunk_index` increments once per `@@ ... @@` header encountered (across the whole
    diff), so consecutive `AddedLine`s sharing a `hunk_index` belong to the same hunk.
    """
    current_file: str | None = None
    current_line_num: int | None = None
    hunk_index = -1

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
            hunk_index += 1
            continue

        if current_file is None or current_line_num is None:
            continue

        if line.startswith("+"):
            yield AddedLine(
                file=current_file,
                line_num=current_line_num,
                content=line[1:],
                hunk_index=hunk_index,
            )
            current_line_num += 1
        elif line.startswith("-"):
            pass
        elif line.startswith("\\"):
            pass
        else:
            current_line_num += 1


def added_lines_by_file(diff: str) -> dict[str, dict[int, str]]:
    """Map each file in the diff to {new_file_line_number: added_line_content}."""
    result: dict[str, dict[int, str]] = {}
    for added_line in iter_added_lines(diff):
        result.setdefault(added_line.file, {})[added_line.line_num] = added_line.content
    return result
