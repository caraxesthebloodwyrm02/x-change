from __future__ import annotations

import unittest

from xchange.nudge import suggest_path_semantics


class SuggestPathSemanticsTests(unittest.TestCase):
    # ------------------------------------------------------------------ #
    # Command branch: failure_command is a non-empty string               #
    # ------------------------------------------------------------------ #

    def test_with_failure_command_contains_command_label(self) -> None:
        result = suggest_path_semantics(failure_command="cd /oops")
        self.assertIn("Failure command:", result)

    def test_with_failure_command_echoes_the_command(self) -> None:
        result = suggest_path_semantics(failure_command="cd /oops")
        self.assertIn("cd /oops", result)

    def test_with_failure_command_contains_path_basics(self) -> None:
        result = suggest_path_semantics(failure_command="cd /oops")
        self.assertIn("Path basics", result)

    # ------------------------------------------------------------------ #
    # None branch: failure_command is None                                #
    # ------------------------------------------------------------------ #

    def test_none_yields_student_failure_message(self) -> None:
        result = suggest_path_semantics(failure_command=None)
        self.assertIn("Student failure captured.", result)

    def test_none_omits_failure_command_label(self) -> None:
        result = suggest_path_semantics(failure_command=None)
        self.assertNotIn("Failure command:", result)

    def test_none_contains_path_basics(self) -> None:
        result = suggest_path_semantics(failure_command=None)
        self.assertIn("Path basics", result)

    # ------------------------------------------------------------------ #
    # Empty-string branch: "" is falsy → same output as None              #
    # ------------------------------------------------------------------ #

    def test_empty_string_yields_student_failure_message(self) -> None:
        result = suggest_path_semantics(failure_command="")
        self.assertIn("Student failure captured.", result)

    def test_empty_string_omits_failure_command_label(self) -> None:
        result = suggest_path_semantics(failure_command="")
        self.assertNotIn("Failure command:", result)

    # ------------------------------------------------------------------ #
    # Universal content: `ls` and cat appear in every branch              #
    # ------------------------------------------------------------------ #

    def test_ls_present_in_command_branch(self) -> None:
        result = suggest_path_semantics(failure_command="cd /oops")
        self.assertIn("`ls`", result)

    def test_cat_present_in_command_branch(self) -> None:
        result = suggest_path_semantics(failure_command="cd /oops")
        self.assertIn("cat", result)

    def test_ls_present_in_none_branch(self) -> None:
        result = suggest_path_semantics(failure_command=None)
        self.assertIn("`ls`", result)

    def test_cat_present_in_none_branch(self) -> None:
        result = suggest_path_semantics(failure_command=None)
        self.assertIn("cat", result)


if __name__ == "__main__":
    unittest.main()
