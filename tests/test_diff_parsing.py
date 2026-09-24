from code_review_agent.diff_parsing import added_lines_by_file


def test_maps_added_lines_to_their_new_file_line_numbers():
    diff = (
        "diff --git a/foo.py b/foo.py\n"
        "index 1234567..89abcde 100644\n"
        "--- a/foo.py\n"
        "+++ b/foo.py\n"
        "@@ -1,2 +1,3 @@\n"
        " existing()\n"
        "+added_line()\n"
        " more_existing()\n"
    )

    result = added_lines_by_file(diff)

    assert result == {"foo.py": {2: "added_line()"}}


def test_tracks_multiple_added_lines_across_a_hunk():
    diff = (
        "diff --git a/foo.py b/foo.py\n"
        "index 1234567..89abcde 100644\n"
        "--- a/foo.py\n"
        "+++ b/foo.py\n"
        "@@ -1,1 +1,3 @@\n"
        "+first()\n"
        "+second()\n"
        " existing()\n"
    )

    result = added_lines_by_file(diff)

    assert result == {"foo.py": {1: "first()", 2: "second()"}}


def test_removed_lines_do_not_consume_a_new_line_number():
    diff = (
        "diff --git a/foo.py b/foo.py\n"
        "index 1234567..89abcde 100644\n"
        "--- a/foo.py\n"
        "+++ b/foo.py\n"
        "@@ -1,2 +1,2 @@\n"
        "-old_value = 1\n"
        "+new_value = 2\n"
    )

    result = added_lines_by_file(diff)

    assert result == {"foo.py": {1: "new_value = 2"}}


def test_tracks_separate_files_independently():
    diff = (
        "diff --git a/foo.py b/foo.py\n"
        "index 1234567..89abcde 100644\n"
        "--- a/foo.py\n"
        "+++ b/foo.py\n"
        "@@ -1,1 +1,2 @@\n"
        " existing()\n"
        "+in_foo()\n"
        "diff --git a/bar.py b/bar.py\n"
        "index 1234567..89abcde 100644\n"
        "--- a/bar.py\n"
        "+++ b/bar.py\n"
        "@@ -1,1 +1,2 @@\n"
        " existing()\n"
        "+in_bar()\n"
    )

    result = added_lines_by_file(diff)

    assert result == {"foo.py": {2: "in_foo()"}, "bar.py": {2: "in_bar()"}}


def test_new_file_creation_is_tracked_from_dev_null():
    diff = (
        "diff --git a/foo.py b/foo.py\n"
        "new file mode 100644\n"
        "index 0000000..bca495c\n"
        "--- /dev/null\n"
        "+++ b/foo.py\n"
        "@@ -0,0 +1,2 @@\n"
        "+def new_function():\n"
        "+    pass\n"
    )

    result = added_lines_by_file(diff)

    assert result == {"foo.py": {1: "def new_function():", 2: "    pass"}}


def test_returns_empty_dict_for_diff_with_no_additions():
    diff = (
        "diff --git a/foo.py b/foo.py\n"
        "index 1234567..89abcde 100644\n"
        "--- a/foo.py\n"
        "+++ b/foo.py\n"
        "@@ -1,1 +1,1 @@\n"
        " existing()\n"
    )

    result = added_lines_by_file(diff)

    assert result == {}
