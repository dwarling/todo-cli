# todo-cli specification (version 1)

This document turns the requirements in `problem.md` (R1–R9) into concrete behavior.
Every requirement ID below is the same ID used in `problem.md` and in the tests.

## Overview

`todo.py` is a single-file command-line program written in Python 3 using only the
standard library. It stores tasks in a local JSON file. No account, network access, or
third-party package is needed (R9).

## Commands

```
python3 todo.py add TITLE [--due MM-DD-YYYY] [--priority high|medium|low]
python3 todo.py list
python3 todo.py done NUMBER
python3 todo.py delete NUMBER
```

### add (R1, R2, R3, R7)
- Adds a task with the given title. The title must not be empty or only whitespace.
- `--due` is optional. It must be a real calendar date written `MM-DD-YYYY`
  (for example `12-05-2026`). Anything else (wrong order, wrong separators, `02-30-2026`)
  is rejected with an error message and nothing is saved.
- `--priority` is optional. Allowed values are `high`, `medium`, `low`
  (case-insensitive; stored lowercase). Anything else is rejected.
- The new task gets the next unused number (see R7) and the program prints it.

### list (R4, R5, R7)
- Shows every task, including done ones.
- Order: tasks with a due date come first, sorted by due date, soonest first. Tasks
  with no due date come last. Ties (same due date, or both without a due date) are
  ordered by task number, smallest first.
- Each line shows the task number, a done marker (`[x]` done, `[ ]` not done), the
  title, and the due date (as `MM-DD-YYYY`) and priority when present.
- If there are no tasks, it prints a short message saying so.

### done NUMBER (R5, R7)
- Marks the task with that number as done. Marking an already-done task done again is
  allowed and has no further effect.
- An unknown number is an error; nothing changes.

### delete NUMBER (R6, R7)
- Removes the task with that number permanently.
- An unknown number is an error; nothing changes.

## Task numbers (R7)
- Numbers start at 1 and increase by one for each task added.
- A task keeps its number forever. Deleting a task never renumbers the others, and a
  deleted task's number is never reused, even after the program restarts. The file
  stores the next number to hand out so this holds across runs.

## Storage (R8, R9)
- Tasks are saved to `tasks.json` in the current directory. Setting the environment
  variable `TODO_FILE` to a path uses that file instead.
- If the file does not exist, the program starts with no tasks; the file is created on
  the first change.
- File format:
  ```json
  {"next_id": 3, "tasks": [
    {"id": 1, "title": "Essay draft", "due": "2026-12-05", "priority": "high", "done": false},
    {"id": 2, "title": "Call advisor", "due": null, "priority": null, "done": true}
  ]}
  ```
  Due dates are stored as ISO `YYYY-MM-DD` so they sort correctly; they are shown to
  the user as `MM-DD-YYYY`.
- Writes go to a temporary file that is then renamed over the real file, so a crash
  mid-write does not destroy existing tasks.
- If the file exists but cannot be read as valid task data, the program prints an error
  and exits without overwriting it.

## Errors
- Invalid input prints a one-line message to standard error and exits with status 1.
  Success exits with status 0.

## Out of scope for version 1
Editing tasks, undoing done, filtering or sorting by priority, recurring tasks,
reminders, and syncing between devices.
