"""Automated test suite for PawPal+.

Run with:  python -m pytest

Covers the core behaviors and the key edge cases: task completion, task
addition, chronological sorting, priority sorting, filtering, recurrence,
conflict detection, the next-available-slot algorithm, an empty pet, and
JSON persistence round-tripping.
"""

from datetime import date

from pawpal_system import Owner, Pet, Task, Scheduler, save_to_json, load_from_json


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def build_owner() -> Owner:
    """Create a small owner/pet/task world used by several tests."""
    owner = Owner("Test Owner")
    dog = owner.add_pet(Pet("Rex", species="dog"))
    cat = owner.add_pet(Pet("Cleo", species="cat"))
    dog.add_task(Task("Evening walk", time="18:00", priority="high"))
    dog.add_task(Task("Morning walk", time="07:00", priority="high"))
    cat.add_task(Task("Feed", time="12:00", priority="medium"))
    return owner


# --------------------------------------------------------------------------- #
# Core behaviors
# --------------------------------------------------------------------------- #

def test_mark_complete_changes_status():
    """mark_complete() should flip a task from pending to done."""
    task = Task("Walk", time="08:00")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_adding_task_increases_pet_count():
    """Adding a task to a Pet increases that pet's task_count."""
    pet = Pet("Buddy")
    assert pet.task_count == 0
    pet.add_task(Task("Walk", time="08:00"))
    assert pet.task_count == 1
    pet.add_task(Task("Feed", time="09:00"))
    assert pet.task_count == 2


def test_add_task_stamps_pet_name():
    """A task should learn its pet's name when attached."""
    pet = Pet("Buddy")
    task = pet.add_task(Task("Walk"))
    assert task.pet_name == "Buddy"


# --------------------------------------------------------------------------- #
# Sorting
# --------------------------------------------------------------------------- #

def test_sort_by_time_is_chronological():
    """sort_by_time() returns tasks in ascending HH:MM order."""
    scheduler = Scheduler(build_owner())
    times = [t.time for t in scheduler.sort_by_time()]
    assert times == ["07:00", "12:00", "18:00"]


def test_sort_by_priority_then_time():
    """sort_by_priority() puts high-priority first, ties broken by time."""
    owner = Owner("P")
    pet = owner.add_pet(Pet("Dog"))
    pet.add_task(Task("Low task", time="06:00", priority="low"))
    pet.add_task(Task("High late", time="20:00", priority="high"))
    pet.add_task(Task("High early", time="09:00", priority="high"))
    scheduler = Scheduler(owner)
    ordered = [t.description for t in scheduler.sort_by_priority()]
    assert ordered == ["High early", "High late", "Low task"]


# --------------------------------------------------------------------------- #
# Filtering
# --------------------------------------------------------------------------- #

def test_filter_by_pet():
    """filter_by_pet() returns only the named pet's tasks."""
    scheduler = Scheduler(build_owner())
    rex_tasks = scheduler.filter_by_pet("Rex")
    assert len(rex_tasks) == 2
    assert all(t.pet_name == "Rex" for t in rex_tasks)


def test_filter_by_status():
    """filter_by_status() separates done from pending tasks."""
    scheduler = Scheduler(build_owner())
    all_tasks = scheduler.get_all_tasks()
    all_tasks[0].mark_complete()
    assert len(scheduler.filter_by_status(completed=True)) == 1
    assert len(scheduler.filter_by_status(completed=False)) == 2


# --------------------------------------------------------------------------- #
# Recurrence
# --------------------------------------------------------------------------- #

def test_daily_recurrence_creates_next_day():
    """Completing a daily task creates a new task due one day later."""
    owner = Owner("R")
    pet = owner.add_pet(Pet("Dog"))
    task = pet.add_task(Task("Walk", time="08:00", frequency="daily",
                             due_date=date(2026, 7, 7)))
    scheduler = Scheduler(owner)

    follow_up = scheduler.mark_task_complete(task)
    assert follow_up is not None
    assert follow_up.completed is False
    assert follow_up.due_date == date(2026, 7, 8)
    assert pet.task_count == 2   # original + the new occurrence


def test_weekly_recurrence_advances_seven_days():
    """A weekly task's next occurrence is seven days out."""
    task = Task("Bath", time="10:00", frequency="weekly",
                due_date=date(2026, 7, 7))
    nxt = task.next_occurrence()
    assert nxt.due_date == date(2026, 7, 14)


def test_one_off_task_has_no_next_occurrence():
    """A 'once' task should not spawn a follow-up."""
    task = Task("Vet visit", time="10:00", frequency="once")
    assert task.next_occurrence() is None


# --------------------------------------------------------------------------- #
# Conflict detection
# --------------------------------------------------------------------------- #

def test_conflict_detection_flags_duplicate_times():
    """Two tasks at the same time produce exactly one warning."""
    owner = Owner("C")
    dog = owner.add_pet(Pet("Dog"))
    cat = owner.add_pet(Pet("Cat"))
    dog.add_task(Task("Walk", time="08:00"))
    cat.add_task(Task("Feed", time="08:00"))
    scheduler = Scheduler(owner)
    conflicts = scheduler.detect_conflicts()
    assert len(conflicts) == 1
    assert "08:00" in conflicts[0]


def test_no_conflict_when_times_differ():
    """Distinct times should produce no warnings."""
    scheduler = Scheduler(build_owner())
    assert scheduler.detect_conflicts() == []


# --------------------------------------------------------------------------- #
# Advanced algorithm + edge cases
# --------------------------------------------------------------------------- #

def test_next_available_slot_finds_gap():
    """next_available_slot() returns the earliest opening that fits."""
    owner = Owner("S")
    pet = owner.add_pet(Pet("Dog"))
    pet.add_task(Task("Walk", time="06:00", duration_minutes=30))  # 06:00-06:30
    scheduler = Scheduler(owner)
    # Day starts 06:00; first task ends 06:30, so a 45-min slot starts there.
    assert scheduler.next_available_slot(45) == "06:30"


def test_empty_pet_has_no_tasks():
    """A pet with no tasks yields an empty, non-crashing schedule."""
    owner = Owner("E")
    owner.add_pet(Pet("Lonely"))
    scheduler = Scheduler(owner)
    assert scheduler.get_all_tasks() == []
    assert scheduler.detect_conflicts() == []
    assert "no tasks" in scheduler.todays_schedule().lower()


# --------------------------------------------------------------------------- #
# Persistence
# --------------------------------------------------------------------------- #

def test_json_round_trip(tmp_path):
    """Saving then loading reproduces the same pets and tasks."""
    owner = build_owner()
    path = tmp_path / "data.json"
    save_to_json(owner, str(path))
    reloaded = load_from_json(str(path))
    assert reloaded is not None
    assert reloaded.name == owner.name
    assert len(reloaded.pets) == len(owner.pets)
    assert len(reloaded.all_tasks()) == len(owner.all_tasks())


def test_load_missing_file_returns_none():
    """Loading a non-existent file returns None instead of raising."""
    assert load_from_json("definitely_not_here_123.json") is None
