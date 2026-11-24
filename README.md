# todo-cli

A simple to-do list for students that runs in the terminal. Add tasks with an optional
due date and priority, list them with the soonest due first, mark them done, and delete
them. Tasks are saved to a local file, so there is no account, no internet connection,
and nothing to install beyond Python 3 (standard library only).

See `problem.md` for the requirements and `spec.md` for the exact behavior.

## Run it

```
python3 todo.py add "Essay draft" --due 12-05-2026 --priority high
python3 todo.py add "Call advisor"
python3 todo.py list
python3 todo.py done 2
python3 todo.py delete 1
python3 todo.py --help
```

Example `list` output:

```
  1. [ ] Essay draft  (due 12-05-2026)  [high]
  2. [x] Call advisor
```

- Due dates are typed as `MM-DD-YYYY`. Priority is `high`, `medium`, or `low`.
- Each task's number stays the same forever, even after other tasks are deleted.
- Tasks are saved in `tasks.json` in the current directory. To use a different file,
  set `TODO_FILE`, for example `TODO_FILE=~/school.json python3 todo.py list`.

## Run the tests

```
python3 -m unittest -v
```

Each test's name includes the requirement ID it checks (for example
`test_r4_undated_tasks_listed_last`).
