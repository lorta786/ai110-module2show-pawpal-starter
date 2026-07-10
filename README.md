# 🐾 PawPal+

**PawPal+** is a smart pet-care management system that helps a busy owner keep
their pets happy and healthy. It tracks daily routines — walks, feedings,
medications, and appointments — and uses lightweight scheduling algorithms to
sort, filter, detect conflicts, and roll recurring tasks forward.

The project is built "CLI-first": all logic lives in a UI-agnostic layer
(`pawpal_system.py`), is verified by a demo script (`main.py`) and an automated
test suite (`tests/`), and is then surfaced through a Streamlit UI (`app.py`).

## Scenario

A busy pet owner needs help staying consistent with pet care. PawPal+ lets them:

- Track care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time, duration, priority)
- Produce a daily plan, sorted sensibly, and flag scheduling conflicts

## ✨ Features

- **Object-oriented model** — `Owner` → `Pet` → `Task`, orchestrated by a `Scheduler` "brain."
- **Sort by time** — chronological `HH:MM` ordering (`Scheduler.sort_by_time`).
- **Sort by priority** — high → low, ties broken by time (`Scheduler.sort_by_priority`).
- **Filtering** — by pet or by completion status (`filter_by_pet`, `filter_by_status`).
- **Conflict detection** — flags any two tasks sharing a start time, returning warnings instead of crashing (`detect_conflicts`).
- **Recurring tasks** — completing a `daily`/`weekly` task auto-creates the next occurrence with the correct due date (`mark_task_complete` + `Task.next_occurrence`).
- **Next available slot** *(stretch)* — finds the earliest free gap that fits a requested duration (`next_available_slot`).
- **JSON persistence** *(stretch)* — save/reload the whole owner to `data.json` (`save_to_json`, `load_from_json`).
- **Priority scheduling** *(stretch)* — Low/Medium/High priority levels drive sorting.
- **Friendly output** *(stretch)* — status/priority/type emojis and an aligned table view (`format_table`, uses `tabulate` when available).

## 🧱 Architecture

| Class | Responsibility |
|-------|----------------|
| `Task` | A single activity: description, time, duration, priority, frequency, completion, due date. Knows how to spawn its next occurrence. |
| `Pet` | Stores pet details and its own list of tasks. |
| `Owner` | Manages multiple pets and exposes all their tasks. |
| `Scheduler` | The "brain": retrieves, sorts, filters, detects conflicts, and manages recurrence across pets. |


## 🚀 Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run the CLI demo

```bash
python main.py
```

### Run the Streamlit app

```bash
streamlit run app.py
```

## 🖥️ Sample Output

Output from running `python main.py` (proof the system runs correctly):

```
============================================================
TODAY'S SCHEDULE (sorted by time)
============================================================
Today's Schedule for Leo
------------------------
  ⬜ 08:00  🐕 Morning walk            30 min  🔴 high   · Biscuit
  ⬜ 08:00  🍽️ Feed breakfast          10 min  🔴 high   · Mochi
  ⬜ 12:00  💊 Give medication          5 min  🔴 high   · Biscuit
  ⬜ 14:30  🏥 Vet appointment         60 min  🟡 medium · Mochi
  ⬜ 18:00  🐕 Evening walk            30 min  🔴 high   · Biscuit
  ⚠️ Conflict at 08:00: Morning walk (Biscuit), Feed breakfast (Mochi)

============================================================
TODAY'S SCHEDULE (sorted by priority, then time)
============================================================
Today's Schedule for Leo
------------------------
  ⬜ 08:00  🐕 Morning walk            30 min  🔴 high   · Biscuit
  ⬜ 08:00  🍽️ Feed breakfast          10 min  🔴 high   · Mochi
  ⬜ 12:00  💊 Give medication          5 min  🔴 high   · Biscuit
  ⬜ 18:00  🐕 Evening walk            30 min  🔴 high   · Biscuit
  ⬜ 14:30  🏥 Vet appointment         60 min  🟡 medium · Mochi
  ⚠️ Conflict at 08:00: Morning walk (Biscuit), Feed breakfast (Mochi)

============================================================
CONFLICT DETECTION
============================================================
  ⚠️ Conflict at 08:00: Morning walk (Biscuit), Feed breakfast (Mochi)

============================================================
RECURRING TASKS: complete the daily morning walk
============================================================
  Before: 08:00 — Morning walk (30 min) [high] for Biscuit · pending
  After:  08:00 — Morning walk (30 min) [high] for Biscuit · done
  Auto-created next occurrence: 08:00 — Morning walk (30 min) [high] for Biscuit · pending
  Biscuit now has 4 tasks.

============================================================
NEXT AVAILABLE SLOT: find 45 free minutes
============================================================
  Earliest 45-minute opening today: 06:00

============================================================
PERSISTENCE: save + reload from data.json
============================================================
  Reloaded owner 'Leo' with 2 pets and 6 total tasks from disk.

============================================================
TABLE VIEW
============================================================
|    | Time   | Task            | Duration   | Priority   | Pet     |
|----|--------|-----------------|------------|------------|---------|
| ✅  | 08:00  | Morning walk    | 30 min     | high       | Biscuit |
| ⬜  | 08:00  | Morning walk    | 30 min     | high       | Biscuit |
| ⬜  | 08:00  | Feed breakfast  | 10 min     | high       | Mochi   |
| ⬜  | 12:00  | Give medication | 5 min      | high       | Biscuit |
| ⬜  | 14:30  | Vet appointment | 60 min     | medium     | Mochi   |
| ⬜  | 18:00  | Evening walk    | 30 min     | high       | Biscuit |
```

## 🧪 Testing PawPal+

Run the full suite from the repo root:

```bash
python -m pytest
```


Successful run:

```
============================== 16 passed in 0.02s ==============================
```


## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Sort by time | `Scheduler.sort_by_time()` | Ascending `HH:MM` via `sorted(key=lambda t: t.time)`. |
| Sort by priority | `Scheduler.sort_by_priority()` | High→low, ties broken by time (stretch). |
| Filtering | `Scheduler.filter_by_pet()`, `Scheduler.filter_by_status()` | By pet name or completion state. |
| Conflict handling | `Scheduler.detect_conflicts()` | Flags same-start-time collisions; returns warnings, never raises. |
| Recurring tasks | `Scheduler.mark_task_complete()` + `Task.next_occurrence()` | Daily → +1 day, weekly → +7 days via `timedelta`. |
| Next available slot | `Scheduler.next_available_slot()` | Earliest gap fitting a requested duration (stretch). |

## 📸 Demo Walkthrough

The Streamlit UI (`streamlit run app.py`) is organized as follows:

**Main UI features / user actions**

1. **Owner name** at the top and an **"Add pet"** form in the sidebar (name, species, breed).
2. An **"Add a task"** form — choose the pet, then set description, time, duration, priority, and frequency.
3. A **"Today's Schedule"** table with a **Sort by** toggle (time / priority) and a **Show** filter (all pets or one pet).
4. **Conflict warnings** rendered as yellow `st.warning` banners above the table.
5. A **"Mark a task complete"** control that completes a task and, for recurring tasks, auto-schedules the next occurrence.
6. A **"Find a free slot"** tool that returns the earliest opening for a requested number of minutes.
7. **Save / Load** buttons that persist the whole plan to `data.json`.

**Example workflow**

> Add a pet (*Biscuit, dog*) → add a task (*Morning walk, 08:00, high, daily*) →
> add another (*Feed breakfast, 08:00* for a second pet) → open **Today's
> Schedule** → PawPal+ sorts the tasks and shows a ⚠️ conflict banner for 08:00 →
> mark *Morning walk* complete → tomorrow's walk is auto-created.

**Key Scheduler behaviors shown:** chronological/priority sorting, per-pet and
status filtering, exact-time conflict warnings, and automatic daily/weekly
recurrence.

**Sample CLI output** from `python main.py`:

```
Today's Schedule for Leo
------------------------
  ⬜ 08:00  🐕 Morning walk            30 min  🔴 high   · Biscuit
  ⬜ 08:00  🍽️ Feed breakfast          10 min  🔴 high   · Mochi
  ⬜ 12:00  💊 Give medication          5 min  🔴 high   · Biscuit
  ⬜ 14:30  🏥 Vet appointment         60 min  🟡 medium · Mochi
  ⬜ 18:00  🐕 Evening walk            30 min  🔴 high   · Biscuit
  ⚠️ Conflict at 08:00: Morning walk (Biscuit), Feed breakfast (Mochi)
```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->

## 🧩 Stretch Features

### Data persistence (Challenge 2)
`save_to_json(owner, "data.json")` serializes the owner, pets, and tasks (dates
become ISO strings); `load_from_json("data.json")` rebuilds them via
`Owner.from_dict` / `Pet.from_dict` / `Task.from_dict`, returning `None` if the
file is missing. **Files modified:** `pawpal_system.py` (serialization methods
+ module functions), `main.py` and `app.py` (save/load calls).

### Priority scheduling (Challenge 3)
Each `Task` carries a `priority` of `low`/`medium`/`high`. `PRIORITY_ORDER` maps
these to a numeric rank so `Scheduler.sort_by_priority()` orders high → low,
then by time. See the "sorted by priority" block in the sample output above.

### Professional output formatting (Challenge 4)
`Task.status_emoji()` / `type_emoji()` and `PRIORITY_EMOJI` add ✅⬜🔴🟡🟢🐕🍽️💊
indicators; `Scheduler.format_table()` renders an aligned GitHub-style table via
the `tabulate` library, falling back to plain columns if it isn't installed.

### Next available slot (Challenge 1)
`Scheduler.next_available_slot(minutes)` sweeps the day around the incomplete
tasks and returns the first `HH:MM` where a gap of the requested length fits.
