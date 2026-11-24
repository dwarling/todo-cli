"""Unit tests for todo.py logic. Each test names the requirement(s) it checks.

Run with: python3 -m unittest -v
These tests cover behavior, not the exact text layout of `list`.
"""

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

import todo


class TempFileMixin:
    """Point the program at a throwaway data file so the real tasks.json is never touched."""

    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self._dir.name, "tasks.json")
        patcher = mock.patch.dict(os.environ, {"TODO_FILE": self.path})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self._dir.cleanup)

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = todo.main(list(argv))
        return code, out.getvalue(), err.getvalue()


class TestAdd(unittest.TestCase):
    def test_r1_add_task_with_title_only(self):
        store = todo.empty_store()
        task = todo.add_task(store, "Read chapter 3")
        self.assertEqual(task["title"], "Read chapter 3")
        self.assertIsNone(task["due"])
        self.assertIsNone(task["priority"])
        self.assertFalse(task["done"])
        self.assertEqual(store["tasks"], [task])

    def test_r1_title_is_trimmed(self):
        task = todo.add_task(todo.empty_store(), "  Lab report  ")
        self.assertEqual(task["title"], "Lab report")

    def test_r1_empty_title_rejected(self):
        store = todo.empty_store()
        for title in ("", "   "):
            with self.assertRaises(todo.TodoError):
                todo.add_task(store, title)
        self.assertEqual(store["tasks"], [])


class TestDueDate(unittest.TestCase):
    def test_r2_due_date_mm_dd_yyyy_accepted(self):
        task = todo.add_task(todo.empty_store(), "Essay", due="12-05-2026")
        self.assertEqual(task["due"], "2026-12-05")

    def test_r2_due_date_round_trips_to_display_format(self):
        self.assertEqual(todo.format_due(todo.parse_due("01-09-2027")), "01-09-2027")

    def test_r2_wrong_formats_rejected(self):
        for bad in ("2026-12-05", "12/05/2026", "12-5-2026", "1-05-2026",
                    "12-05-26", "tomorrow", "", "12-05-2026-1"):
            with self.subTest(due=bad), self.assertRaises(todo.TodoError):
                todo.parse_due(bad)

    def test_r2_impossible_dates_rejected(self):
        for bad in ("02-30-2026", "13-01-2026", "00-10-2026", "02-29-2027"):
            with self.subTest(due=bad), self.assertRaises(todo.TodoError):
                todo.parse_due(bad)

    def test_r2_leap_day_accepted(self):
        self.assertEqual(todo.parse_due("02-29-2028"), "2028-02-29")

    def test_r2_bad_date_does_not_add_task(self):
        store = todo.empty_store()
        with self.assertRaises(todo.TodoError):
            todo.add_task(store, "Essay", due="2026-12-05")
        self.assertEqual(store["tasks"], [])
        self.assertEqual(store["next_id"], 1)


class TestPriority(unittest.TestCase):
    def test_r3_each_priority_accepted(self):
        store = todo.empty_store()
        for level in ("high", "medium", "low"):
            with self.subTest(priority=level):
                self.assertEqual(todo.add_task(store, "t", priority=level)["priority"], level)

    def test_r3_priority_is_case_insensitive(self):
        self.assertEqual(todo.parse_priority("HIGH"), "high")
        self.assertEqual(todo.parse_priority("Medium"), "medium")

    def test_r3_unknown_priority_rejected(self):
        for bad in ("urgent", "1", "", "hi"):
            with self.subTest(priority=bad), self.assertRaises(todo.TodoError):
                todo.parse_priority(bad)

    def test_r2_r3_due_and_priority_together(self):
        task = todo.add_task(todo.empty_store(), "Quiz", due="11-30-2026", priority="low")
        self.assertEqual((task["due"], task["priority"]), ("2026-11-30", "low"))


class TestListOrder(unittest.TestCase):
    def ids(self, store):
        return [t["id"] for t in todo.sorted_tasks(store)]

    def test_r4_sorted_by_due_date_soonest_first(self):
        store = todo.empty_store()
        todo.add_task(store, "later", due="03-01-2027")   # 1
        todo.add_task(store, "soon", due="11-30-2026")    # 2
        todo.add_task(store, "middle", due="12-15-2026")  # 3
        self.assertEqual(self.ids(store), [2, 3, 1])

    def test_r4_sort_is_by_date_not_by_text(self):
        # As MM-DD-YYYY text, "01-01-2027" < "12-31-2026"; by date it is later.
        store = todo.empty_store()
        todo.add_task(store, "new year", due="01-01-2027")  # 1
        todo.add_task(store, "nye", due="12-31-2026")       # 2
        self.assertEqual(self.ids(store), [2, 1])

    def test_r4_undated_tasks_listed_last(self):
        store = todo.empty_store()
        todo.add_task(store, "no date")                  # 1
        todo.add_task(store, "dated", due="06-01-2030")  # 2
        todo.add_task(store, "also no date")             # 3
        todo.add_task(store, "earlier", due="01-01-2026")  # 4
        self.assertEqual(self.ids(store), [4, 2, 1, 3])

    def test_r4_r7_ties_ordered_by_number(self):
        store = todo.empty_store()
        todo.add_task(store, "b", due="12-05-2026")  # 1
        todo.add_task(store, "a", due="12-05-2026")  # 2
        self.assertEqual(self.ids(store), [1, 2])

    def test_r4_empty_list(self):
        self.assertEqual(todo.sorted_tasks(todo.empty_store()), [])


class TestDone(unittest.TestCase):
    def test_r5_mark_done(self):
        store = todo.empty_store()
        todo.add_task(store, "Essay")
        todo.mark_done(store, 1)
        self.assertTrue(store["tasks"][0]["done"])

    def test_r5_done_tasks_still_listed(self):
        store = todo.empty_store()
        todo.add_task(store, "a")
        todo.add_task(store, "b")
        todo.mark_done(store, 1)
        listed = todo.sorted_tasks(store)
        self.assertEqual([t["id"] for t in listed], [1, 2])
        self.assertEqual([t["done"] for t in listed], [True, False])

    def test_r5_marking_done_twice_is_harmless(self):
        store = todo.empty_store()
        todo.add_task(store, "a")
        todo.mark_done(store, 1)
        todo.mark_done(store, 1)
        self.assertTrue(store["tasks"][0]["done"])

    def test_r5_r7_unknown_number_rejected(self):
        store = todo.empty_store()
        todo.add_task(store, "a")
        with self.assertRaises(todo.TodoError):
            todo.mark_done(store, 99)
        self.assertFalse(store["tasks"][0]["done"])


class TestDelete(unittest.TestCase):
    def test_r6_delete_removes_task(self):
        store = todo.empty_store()
        todo.add_task(store, "a")
        todo.add_task(store, "b")
        todo.delete_task(store, 1)
        self.assertEqual([t["title"] for t in store["tasks"]], ["b"])

    def test_r6_r7_unknown_number_rejected(self):
        store = todo.empty_store()
        todo.add_task(store, "a")
        with self.assertRaises(todo.TodoError):
            todo.delete_task(store, 2)
        self.assertEqual(len(store["tasks"]), 1)

    def test_r6_r7_deleted_task_cannot_be_deleted_again(self):
        store = todo.empty_store()
        todo.add_task(store, "a")
        todo.delete_task(store, 1)
        with self.assertRaises(todo.TodoError):
            todo.delete_task(store, 1)


class TestNumbers(unittest.TestCase):
    def test_r7_numbers_start_at_one_and_increase(self):
        store = todo.empty_store()
        self.assertEqual([todo.add_task(store, t)["id"] for t in "abc"], [1, 2, 3])

    def test_r7_delete_does_not_renumber_others(self):
        store = todo.empty_store()
        for t in "abc":
            todo.add_task(store, t)
        todo.delete_task(store, 2)
        self.assertEqual({t["title"]: t["id"] for t in store["tasks"]}, {"a": 1, "c": 3})

    def test_r7_deleted_number_never_reused(self):
        store = todo.empty_store()
        todo.add_task(store, "a")
        todo.add_task(store, "b")
        todo.delete_task(store, 2)  # delete the newest one
        self.assertEqual(todo.add_task(store, "c")["id"], 3)

    def test_r7_number_does_not_change_when_sort_order_changes(self):
        store = todo.empty_store()
        todo.add_task(store, "undated")              # 1
        todo.add_task(store, "dated", due="12-01-2026")  # 2, listed first
        listed = todo.sorted_tasks(store)
        self.assertEqual([(t["id"], t["title"]) for t in listed], [(2, "dated"), (1, "undated")])


class TestStorage(TempFileMixin, unittest.TestCase):
    def test_r8_missing_file_means_no_tasks(self):
        self.assertEqual(todo.load(self.path), todo.empty_store())
        self.assertFalse(os.path.exists(self.path))

    def test_r8_save_then_load_round_trip(self):
        store = todo.empty_store()
        todo.add_task(store, "Essay", due="12-05-2026", priority="high")
        todo.add_task(store, "Call advisor")
        todo.mark_done(store, 2)
        todo.save(store, self.path)
        self.assertEqual(todo.load(self.path), store)

    def test_r7_r8_next_number_survives_restart(self):
        store = todo.empty_store()
        todo.add_task(store, "a")
        todo.add_task(store, "b")
        todo.delete_task(store, 2)
        todo.save(store, self.path)
        reloaded = todo.load(self.path)
        self.assertEqual(todo.add_task(reloaded, "c")["id"], 3)

    def test_r7_r8_hand_edited_next_id_cannot_reuse_numbers(self):
        with open(self.path, "w") as f:
            json.dump({"next_id": 1, "tasks": [{"id": 5, "title": "x", "due": None,
                                                "priority": None, "done": False}]}, f)
        store = todo.load(self.path)
        self.assertEqual(todo.add_task(store, "y")["id"], 6)

    def test_r8_corrupt_file_is_an_error_and_left_alone(self):
        with open(self.path, "w") as f:
            f.write("{not json")
        with self.assertRaises(todo.TodoError):
            todo.load(self.path)
        code, _, err = self.run_cli("add", "x")
        self.assertEqual(code, 1)
        self.assertIn("error", err)
        with open(self.path) as f:
            self.assertEqual(f.read(), "{not json")

    def test_r8_save_leaves_no_temp_files(self):
        todo.save(todo.empty_store(), self.path)
        self.assertEqual(os.listdir(self._dir.name), ["tasks.json"])

    def test_r8_todo_file_env_var_selects_path(self):
        self.assertEqual(todo.data_path(), self.path)


class TestNoAccountOrNetwork(unittest.TestCase):
    def test_r9_imports_only_stdlib_and_no_network_modules(self):
        import ast
        import sys
        with open(todo.__file__, encoding="utf-8") as f:
            tree = ast.parse(f.read())
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                names.add(node.module.split(".")[0])
        self.assertTrue(names <= sys.stdlib_module_names, names - sys.stdlib_module_names)
        network = {"socket", "ssl", "http", "urllib", "ftplib", "smtplib", "asyncio"}
        self.assertFalse(names & network, names & network)


class TestCommandLine(TempFileMixin, unittest.TestCase):
    """End-to-end through main(): each command changes the saved file as expected."""

    def saved(self):
        return todo.load(self.path)

    def test_r1_r2_r3_r8_add_command_saves_task(self):
        code, out, _ = self.run_cli("add", "Essay", "--due", "12-05-2026", "--priority", "high")
        self.assertEqual(code, 0)
        self.assertIn("1", out)
        [task] = self.saved()["tasks"]
        self.assertEqual((task["title"], task["due"], task["priority"]),
                         ("Essay", "2026-12-05", "high"))

    def test_r2_bad_date_command_fails_and_saves_nothing(self):
        code, _, err = self.run_cli("add", "Essay", "--due", "2026-12-05")
        self.assertEqual(code, 1)
        self.assertIn("MM-DD-YYYY", err)
        self.assertFalse(os.path.exists(self.path))

    def test_r3_bad_priority_command_fails(self):
        code, _, _ = self.run_cli("add", "Essay", "--priority", "urgent")
        self.assertEqual(code, 1)
        self.assertFalse(os.path.exists(self.path))

    def test_r5_r8_done_command_persists(self):
        self.run_cli("add", "Essay")
        code, _, _ = self.run_cli("done", "1")
        self.assertEqual(code, 0)
        self.assertTrue(self.saved()["tasks"][0]["done"])

    def test_r6_r8_delete_command_persists(self):
        self.run_cli("add", "a")
        self.run_cli("add", "b")
        code, _, _ = self.run_cli("delete", "1")
        self.assertEqual(code, 0)
        self.assertEqual([t["id"] for t in self.saved()["tasks"]], [2])

    def test_r5_r6_unknown_number_command_fails(self):
        for cmd in ("done", "delete"):
            with self.subTest(command=cmd):
                code, _, err = self.run_cli(cmd, "7")
                self.assertEqual(code, 1)
                self.assertIn("7", err)

    def test_r4_r5_list_command_shows_every_task_in_order(self):
        self.run_cli("add", "undated")
        self.run_cli("add", "later", "--due", "01-15-2027")
        self.run_cli("add", "sooner", "--due", "12-01-2026")
        self.run_cli("done", "3")
        code, out, _ = self.run_cli("list")
        self.assertEqual(code, 0)
        # Order only, not layout: each title appears, in the R4 order.
        positions = [out.index(title) for title in ("sooner", "later", "undated")]
        self.assertEqual(positions, sorted(positions))


if __name__ == "__main__":
    unittest.main()
