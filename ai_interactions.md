# AI Interactions Log

> Documents the stretch features that used an AI agent and a prompt comparison.

---

## Agent Workflow (SF7)

**What task did you give the agent?**

Two multi-step tasks: (1) scaffold the four classes in `pawpal_system.py` from
the Phase 1 UML, and (2) once the core was working, add the algorithmic layer —
sorting, filtering, conflict detection, and recurring-task logic — plus the
stretch features (JSON persistence, priority sorting, a `next_available_slot`
search, and emoji/table formatting).

**What did the agent do?**

- Generated the `Task`, `Pet`, `Owner`, and `Scheduler` classes in
  `pawpal_system.py`, using `@dataclass` for `Task`/`Pet`/`Owner`.
- Added `sort_by_time`, `sort_by_priority`, `filter_by_pet`, `filter_by_status`,
  `detect_conflicts`, and `mark_task_complete` (which calls
  `Task.next_occurrence` to roll recurring tasks forward with `timedelta`).
- Added stretch methods: `next_available_slot`, `save_to_json`/`load_from_json`
  with `to_dict`/`from_dict` on each class, and `format_table`.
- Wrote `main.py` to exercise all of it in the terminal, and
  `tests/test_pawpal.py` (16 tests).
- Wired `app.py` to the logic layer using `st.session_state` to persist the
  `Owner` across reruns.

**Files modified:** `pawpal_system.py`, `main.py`, `app.py`,
`tests/test_pawpal.py`, `diagrams/uml_draft.mmd`, `diagrams/uml_final.mmd`,
`conftest.py`, `README.md`, `requirements.txt`.

**What did you have to verify or fix manually?**

- The recurrence demo in `main.py` originally grabbed the wrong task (insertion
  order returned the evening walk instead of the morning walk); I changed it to
  select by description so the demo reads correctly.
- I added a root `conftest.py` after checking that a bare `pytest` invocation
  (not just `python -m pytest`) could still import `pawpal_system`.
- I changed `detect_conflicts` from raising an exception to returning warning
  strings, so a collision doesn't crash the schedule.
- I verified every change by running `python main.py` and `python -m pytest`
  (16 passed) and by launching `streamlit run app.py` to confirm it loads.

---

## Prompt Comparison (SF11)

> Task compared: the logic for rescheduling a recurring ("daily"/"weekly") task
> when it is marked complete.

| | Option A | Option B |
|-|----------|----------|
| **Model / tool used** | Assistant chat, prompt: *"write recurrence logic"* | Assistant chat, prompt: *"using `datetime.timedelta`, return a NEW Task for the next due date; +1 day for daily, +7 for weekly; leave one-off tasks alone"* |
| **Prompt** | Vague, no constraints | Specific about dates, return value, and the one-off case |
| **Response summary** | Mutated the existing task's date in place and toggled `completed` back to `False` | Created a fresh `Task` for the next occurrence and returned `None` for one-off tasks |
| **What was useful** | Showed the `timedelta` idea | Correct separation: history (the completed task) stays, a new task is spawned |
| **Problems noticed** | Rewriting the same object loses the record that today's task was done; no handling of `"once"` | Slightly more code, but behavior is right |
| **Decision** | Rejected | **Adopted** |

**Which approach did you use in your final implementation and why?**

Option B. Mutating a task in place (Option A) would erase the fact that today's
task was completed — bad for any future "what did I do today" view — and it
silently mishandled one-off tasks. Option B keeps the completed task as a record
and adds a distinct next occurrence, which is what `Task.next_occurrence()` and
`Scheduler.mark_task_complete()` do in the final code.
