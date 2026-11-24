#!/usr/bin/env python3
"""todo-cli: a local, account-free to-do list for students.

See spec.md for the full behavior. Standard library only.
"""

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime

DEFAULT_FILE = "tasks.json"
PRIORITIES = ("high", "medium", "low")
DATE_FORMAT = "%m-%d-%Y"  # what the user types and sees (R2)


class TodoError(Exception):
    """A user-facing error: bad input, unknown task, unreadable file."""


# ---------------------------------------------------------------- validation

def parse_due(text):
    """Turn 'MM-DD-YYYY' into ISO 'YYYY-MM-DD' (R2). None stays None."""
    if text is None:
        return None
    parts = text.split("-")
    if len(parts) != 3 or [len(p) for p in parts] != [2, 2, 4]:
        raise TodoError(f"due date must be MM-DD-YYYY, got {text!r}")
    try:
        return datetime.strptime(text, DATE_FORMAT).date().isoformat()
    except ValueError:
        raise TodoError(f"{text!r} is not a real date (expected MM-DD-YYYY)")


def format_due(iso):
    """Turn stored ISO 'YYYY-MM-DD' back into 'MM-DD-YYYY' for display."""
    if iso is None:
        return None
    return datetime.strptime(iso, "%Y-%m-%d").strftime(DATE_FORMAT)


def parse_priority(text):
    """Validate a priority (R3). None stays None; case-insensitive."""
    if text is None:
        return None
    value = text.strip().lower()
    if value not in PRIORITIES:
        raise TodoError(f"priority must be one of {', '.join(PRIORITIES)}, got {text!r}")
    return value


# ---------------------------------------------------------------- task list

def empty_store():
    return {"next_id": 1, "tasks": []}


def add_task(store, title, due=None, priority=None):
    """Add a task (R1-R3) and give it the next never-used number (R7)."""
    title = (title or "").strip()
    if not title:
        raise TodoError("task title cannot be empty")
    task = {
        "id": store["next_id"],
        "title": title,
        "due": parse_due(due),
        "priority": parse_priority(priority),
        "done": False,
    }
    store["tasks"].append(task)
    store["next_id"] += 1
    return task


def find_task(store, number):
    for task in store["tasks"]:
        if task["id"] == number:
            return task
    raise TodoError(f"no task numbered {number}")


def mark_done(store, number):
    """Mark a task done (R5). The task stays in the list."""
    task = find_task(store, number)
    task["done"] = True
    return task


def delete_task(store, number):
    """Remove a task (R6). Other tasks keep their numbers (R7)."""
    task = find_task(store, number)
    store["tasks"].remove(task)
    return task


def sorted_tasks(store):
    """All tasks, soonest due first, undated last, ties by number (R4, R5)."""
    return sorted(
        store["tasks"],
        key=lambda t: (t["due"] is None, t["due"] or "", t["id"]),
    )


# ---------------------------------------------------------------- storage

def data_path():
    return os.environ.get("TODO_FILE", DEFAULT_FILE)


def load(path):
    """Read tasks from disk (R8). A missing file means no tasks yet."""
    if not os.path.exists(path):
        return empty_store()
    try:
        with open(path, encoding="utf-8") as f:
            store = json.load(f)
        if not isinstance(store.get("next_id"), int) or not isinstance(store.get("tasks"), list):
            raise ValueError("missing next_id or tasks")
        # Guard R7 even if the file was hand-edited: never hand out a used number.
        highest = max((t["id"] for t in store["tasks"]), default=0)
        store["next_id"] = max(store["next_id"], highest + 1)
        return store
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as e:
        raise TodoError(f"cannot read {path}: {e}. The file was left unchanged.")


def save(store, path):
    """Write tasks atomically so a crash cannot wipe the file (R8)."""
    directory = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".tasks-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(store, f, indent=2)
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


# ---------------------------------------------------------------- CLI

def format_task(task):
    mark = "[x]" if task["done"] else "[ ]"
    line = f"{task['id']:>3}. {mark} {task['title']}"
    if task["due"]:
        line += f"  (due {format_due(task['due'])})"
    if task["priority"]:
        line += f"  [{task['priority']}]"
    return line


def build_parser():
    parser = argparse.ArgumentParser(
        prog="todo.py",
        description="A local to-do list. Tasks are saved to tasks.json "
                    "(or the file named by TODO_FILE).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="add a task")
    p_add.add_argument("title", help="what the task is")
    p_add.add_argument("--due", metavar="MM-DD-YYYY", help="optional due date")
    p_add.add_argument("--priority", metavar="LEVEL", help="optional: high, medium, or low")

    sub.add_parser("list", help="list all tasks, soonest due first")

    p_done = sub.add_parser("done", help="mark a task done")
    p_done.add_argument("number", type=int, help="task number from the list")

    p_del = sub.add_parser("delete", help="delete a task")
    p_del.add_argument("number", type=int, help="task number from the list")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    path = data_path()
    try:
        store = load(path)
        if args.command == "add":
            task = add_task(store, args.title, args.due, args.priority)
            save(store, path)
            print(f"Added task {task['id']}: {task['title']}")
        elif args.command == "list":
            tasks = sorted_tasks(store)
            if not tasks:
                print("No tasks yet. Add one with: python3 todo.py add \"Title\"")
            for task in tasks:
                print(format_task(task))
        elif args.command == "done":
            task = mark_done(store, args.number)
            save(store, path)
            print(f"Marked task {task['id']} done: {task['title']}")
        elif args.command == "delete":
            task = delete_task(store, args.number)
            save(store, path)
            print(f"Deleted task {task['id']}: {task['title']}")
    except TodoError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
