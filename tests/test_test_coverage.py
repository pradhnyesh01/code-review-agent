from code_review_agent.findings import Finding
from code_review_agent.test_coverage import generate_test_coverage_findings


def _diff(*, path: str = "foo.py", hunk_header: str = "@@ -1,3 +1,4 @@ def existing():", body: str) -> str:
    return (
        f"diff --git a/{path} b/{path}\n"
        "index 1234567..89abcde 100644\n"
        f"--- a/{path}\n"
        f"+++ b/{path}\n"
        f"{hunk_header}\n"
        f"{body}"
    )


def test_flags_new_top_level_function_with_no_test_file_in_diff():
    diff = _diff(
        body=(
            " existing()\n"
            "+\n"
            "+def new_function():\n"
            "+    pass\n"
        )
    )

    findings = generate_test_coverage_findings(diff)

    assert findings == [
        Finding(
            file="foo.py",
            line=3,
            comment=(
                "This hunk adds a new function/method with no corresponding "
                "test file changes in this diff."
            ),
            category="test-coverage",
            severity="blocker",
        )
    ]


def test_flags_new_method_inside_a_class():
    diff = _diff(
        body=(
            " class Foo:\n"
            "+    def new_method(self):\n"
            "+        pass\n"
        )
    )

    findings = generate_test_coverage_findings(diff)

    assert len(findings) == 1
    assert findings[0].line == 2


def test_flags_new_async_function():
    diff = _diff(body="+async def new_function():\n+    pass\n")

    findings = generate_test_coverage_findings(diff)

    assert len(findings) == 1


def test_no_finding_when_test_file_matching_test_prefix_appears_in_diff():
    func_diff = _diff(body="+def new_function():\n+    pass\n")
    test_diff = _diff(path="tests/test_foo.py", body="+def test_new_function():\n+    pass\n")

    findings = generate_test_coverage_findings(func_diff + test_diff)

    assert findings == []


def test_no_finding_when_test_file_matching_test_suffix_appears_in_diff():
    func_diff = _diff(body="+def new_function():\n+    pass\n")
    test_diff = _diff(path="foo_test.py", body="+def test_new_function():\n+    pass\n")

    findings = generate_test_coverage_findings(func_diff + test_diff)

    assert findings == []


def test_no_finding_when_hunk_only_modifies_existing_code():
    diff = _diff(body="-old_value = 1\n+old_value = 2\n")

    findings = generate_test_coverage_findings(diff)

    assert findings == []


def test_no_finding_for_new_function_in_non_python_file():
    diff = _diff(path="foo.js", body="+def new_function():\n")

    findings = generate_test_coverage_findings(diff)

    assert findings == []


def test_one_finding_per_hunk_even_with_multiple_new_functions():
    diff = _diff(body="+def one():\n+    pass\n+def two():\n+    pass\n")

    findings = generate_test_coverage_findings(diff)

    assert len(findings) == 1


def test_separate_findings_for_separate_hunks_in_same_file():
    diff = (
        "diff --git a/foo.py b/foo.py\n"
        "index 1234567..89abcde 100644\n"
        "--- a/foo.py\n"
        "+++ b/foo.py\n"
        "@@ -1,2 +1,3 @@\n"
        " existing()\n"
        "+def one():\n"
        "+    pass\n"
        "@@ -10,2 +11,3 @@\n"
        " existing_two()\n"
        "+def two():\n"
        "+    pass\n"
    )

    findings = generate_test_coverage_findings(diff)

    assert [f.line for f in findings] == [2, 12]


def test_no_finding_when_diff_has_no_new_function():
    diff = _diff(body=" existing()\n+existing_call()\n")

    findings = generate_test_coverage_findings(diff)

    assert findings == []
