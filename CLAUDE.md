# CLAUDE.md

Guidance for working in this repository.

## Project
A command-line to-do list for students. `problem.md` holds the problem statement and
requirements (R1, R2, ...). `spec.md` turns them into exact behavior. When the two
disagree, ask before changing either.

## Rules
- Python 3, standard library only. Do not add third-party packages.
- No network access and no accounts (R9).
- Keep logic (parsing, validation, sorting, storage) in functions that do not print,
  so it can be unit tested. Printing and argument parsing stay in the CLI layer.
- Tests use `unittest`. Each test names the requirement ID(s) it checks in its name
  or docstring (for example `test_r4_undated_tasks_listed_last`). Test logic, not the
  exact text layout of `list`.
- Tests must never touch the real `tasks.json`; use a temporary file.
- Never commit saved data files (`tasks.json`, `*.jsonl`).

## Commands
- Run: `python3 todo.py --help`
- Test: `python3 -m unittest -v`

## Git
- Small commits; the message says what changed and why.
- Never undo, amend, or rewrite a commit. Fix mistakes with a new commit.
