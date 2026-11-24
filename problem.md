# Problem
Keeping track of tasks is crucial to the life of a student. Tracking meetings,
assignments, due dates, and quiz dates can be hard, and having one place to store all
that information can save your life. The trouble a lot of students have nowadays is
that there are too many apps to spread tasks across, and those apps often need accounts
or put up too many barriers to entering and storing information easily.

# Initial requirements
- R1: The user can add a task from the command line.
- R2: A task can optionally have a due date, typed as month-day-year (MM-DD-YYYY),
  for example 12-05-2026.
- R3: A task can optionally have a priority of high, medium, or low.
- R4: The user can list their tasks. Tasks are listed by due date, soonest first, and
  tasks with no due date are listed last.
- R5: The user can mark a task as done. Done tasks are still shown in the list, marked
  as done.
- R6: The user can delete a task.
- R7: Each task has a number shown in the list, which is used to mark it done or delete
  it. A task's number never changes.
- R8: Tasks are saved to a file, so they are still there the next time the program runs.
- R9: No account or internet connection is needed.
