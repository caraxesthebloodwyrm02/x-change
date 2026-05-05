from __future__ import annotations

from typing import Optional


def suggest_path_semantics(*, failure_command: Optional[str]) -> str:
  # v0 deterministic nudge: use your requested mental model.
  # '.' is "current directory" (relative to where you are now)
  # '/' is the path separator for absolute paths.
  cmd_hint = f"Failure command: `{failure_command}`" if failure_command else "Student failure captured."
  return (
    f"{cmd_hint}\n\n"
    "Path basics to try next time:\n"
    "- `.` means the current directory (relative root for your prompt).\n"
    "- `/` separates folders in an absolute path (e.g. `/home/<name>/project/file.txt`).\n"
    "- Workflow: run `ls` to see names in the current directory, then use `cat ./<name>` or `bash ./script.sh`.\n"
    "If you still hit an error, send the exact terminal output and we’ll shrink the scope to the two characters that matter."
  )

