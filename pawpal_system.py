"""PawPal+ core logic layer.

This module is the "brain" of PawPal+. It defines the data model
(``Task``, ``Pet``, ``Owner``) and the scheduling engine (``Scheduler``).
Everything here is UI-agnostic so it can be driven from a CLI demo
(``main.py``), the automated test suite, or the Streamlit app (``app.py``).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import date, timedelta

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

# Lower number == higher urgency, so tasks sort naturally with sorted().
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

VALID_FREQUENCIES = {"once", "daily", "weekly"}

# Emoji used purely for friendlier CLI/UI output (see Challenge 4).
PRIORITY_EMOJI = {"high": "🔴", "medium": "🟡", "low": "🟢"}
_TYPE_EMOJI = {
    "walk": "🐕",
    "feed": "🍽️",
    "food": "🍽️",
    "meal": "🍽️",
    "med": "💊",
    "pill": "💊",
    "vet": "🏥",
    "appointment": "🏥",
    "groom": "🛁",
    "bath": "🛁",
    "play": "🎾",
    "enrich": "🎾",
    "train": "🎓",
}


# --------------------------------------------------------------------------- #
# Task
# --------------------------------------------------------------------------- #

@dataclass
class Task:
    """A single pet-care activity (a walk, feeding, medication, etc.)."""

    description: str
    time: str = "09:00"                 # 24-hour "HH:MM"
    duration_minutes: int = 30
    priority: str = "medium"            # "low" | "medium" | "high"
    frequency: str = "once"             # "once" | "daily" | "weekly"
    completed: bool = False
    pet_name: str = ""                  # filled in when attached to a Pet
    due_date: date = field(default_factory=date.today)

    def mark_complete(self) -> None:
        """Flip this task's completion status to done."""
        self.completed = True

    @property
    def priority_rank(self) -> int:
        """Numeric urgency (0 = high) used as a sort key."""
        return PRIORITY_ORDER.get(self.priority.lower(), 1)

    def time_in_minutes(self) -> int:
        """Convert the ``HH:MM`` time string into minutes past midnight."""
        hours, minutes = self.time.split(":")
        return int(hours) * 60 + int(minutes)

    def end_in_minutes(self) -> int:
        """Minutes past midnight when this task finishes."""
        return self.time_in_minutes() + self.duration_minutes

    def next_occurrence(self) -> "Task | None":
        """Return the next instance of a recurring task, or None if one-off."""
        if self.frequency == "daily":
            step = timedelta(days=1)
        elif self.frequency == "weekly":
            step = timedelta(days=7)
        else:
            return None
        return Task(
            description=self.description,
            time=self.time,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            frequency=self.frequency,
            completed=False,
            pet_name=self.pet_name,
            due_date=self.due_date + step,
        )

    # -- presentation helpers ------------------------------------------------ #
    def type_emoji(self) -> str:
        """Guess a friendly emoji from keywords in the description."""
        text = self.description.lower()
        for keyword, emoji in _TYPE_EMOJI.items():
            if keyword in text:
                return emoji
        return "📋"

    def status_emoji(self) -> str:
        """✅ when done, ⬜ when still pending."""
        return "✅" if self.completed else "⬜"

    def __str__(self) -> str:
        status = "done" if self.completed else "pending"
        return (
            f"{self.time} — {self.description} ({self.duration_minutes} min) "
            f"[{self.priority}] for {self.pet_name or 'unassigned'} · {status}"
        )

    # -- serialization (Challenge 2: persistence) ---------------------------- #
    def to_dict(self) -> dict:
        """Return a JSON-safe dict (dates become ISO strings)."""
        data = asdict(self)
        data["due_date"] = self.due_date.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Rebuild a Task from a dict produced by ``to_dict``."""
        data = dict(data)
        if isinstance(data.get("due_date"), str):
            data["due_date"] = date.fromisoformat(data["due_date"])
        return cls(**data)


# --------------------------------------------------------------------------- #
# Pet
# --------------------------------------------------------------------------- #

@dataclass
class Pet:
    """A pet, holding its own list of care tasks."""

    name: str
    species: str = "dog"
    breed: str = ""
    tasks: list = field(default_factory=list)

    def add_task(self, task: Task) -> Task:
        """Attach a task to this pet and stamp it with the pet's name."""
        task.pet_name = self.name
        self.tasks.append(task)
        return task

    @property
    def task_count(self) -> int:
        """How many tasks this pet currently has."""
        return len(self.tasks)

    def get_tasks(self) -> list:
        """Return this pet's task list."""
        return self.tasks

    def to_dict(self) -> dict:
        """Serialize this pet and its tasks to a JSON-safe dict."""
        return {
            "name": self.name,
            "species": self.species,
            "breed": self.breed,
            "tasks": [t.to_dict() for t in self.tasks],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Pet":
        """Rebuild a Pet (and its tasks) from a dict."""
        pet = cls(name=data["name"], species=data.get("species", "dog"),
                  breed=data.get("breed", ""))
        pet.tasks = [Task.from_dict(t) for t in data.get("tasks", [])]
        return pet


# --------------------------------------------------------------------------- #
# Owner
# --------------------------------------------------------------------------- #

@dataclass
class Owner:
    """A pet owner who manages one or more pets."""

    name: str
    pets: list = field(default_factory=list)

    def add_pet(self, pet: Pet) -> Pet:
        """Register a new pet with this owner."""
        self.pets.append(pet)
        return pet

    def get_pet(self, name: str) -> "Pet | None":
        """Look up a pet by name (case-insensitive)."""
        for pet in self.pets:
            if pet.name.lower() == name.lower():
                return pet
        return None

    def all_tasks(self) -> list:
        """Flatten every task across every pet into one list."""
        tasks: list = []
        for pet in self.pets:
            tasks.extend(pet.tasks)
        return tasks

    def to_dict(self) -> dict:
        """Serialize the owner and all pets to a JSON-safe dict."""
        return {"name": self.name, "pets": [p.to_dict() for p in self.pets]}

    @classmethod
    def from_dict(cls, data: dict) -> "Owner":
        """Rebuild an Owner (and all pets/tasks) from a dict."""
        owner = cls(name=data["name"])
        owner.pets = [Pet.from_dict(p) for p in data.get("pets", [])]
        return owner


# --------------------------------------------------------------------------- #
# Scheduler — the "brain"
# --------------------------------------------------------------------------- #

class Scheduler:
    """Retrieves, organizes, and analyzes tasks across an owner's pets."""

    def __init__(self, owner: Owner):
        """Bind the scheduler to a single owner."""
        self.owner = owner

    # -- retrieval ----------------------------------------------------------- #
    def get_all_tasks(self) -> list:
        """Return every task belonging to the owner's pets."""
        return self.owner.all_tasks()

    # -- sorting ------------------------------------------------------------- #
    def sort_by_time(self, tasks: "list | None" = None) -> list:
        """Return tasks in chronological order (earliest ``HH:MM`` first)."""
        tasks = self.get_all_tasks() if tasks is None else tasks
        return sorted(tasks, key=lambda t: t.time)

    def sort_by_priority(self, tasks: "list | None" = None) -> list:
        """Sort by priority first (high->low), then by time (Challenge 3)."""
        tasks = self.get_all_tasks() if tasks is None else tasks
        return sorted(tasks, key=lambda t: (t.priority_rank, t.time))

    # -- filtering ----------------------------------------------------------- #
    def filter_by_status(self, completed: bool,
                         tasks: "list | None" = None) -> list:
        """Return only tasks whose completion matches ``completed``."""
        tasks = self.get_all_tasks() if tasks is None else tasks
        return [t for t in tasks if t.completed == completed]

    def filter_by_pet(self, pet_name: str,
                      tasks: "list | None" = None) -> list:
        """Return only the tasks belonging to a named pet."""
        tasks = self.get_all_tasks() if tasks is None else tasks
        return [t for t in tasks if t.pet_name.lower() == pet_name.lower()]

    # -- conflict detection -------------------------------------------------- #
    def detect_conflicts(self, tasks: "list | None" = None) -> list:
        """Return warning strings for any two tasks sharing a start time.

        Lightweight by design: it flags exact ``HH:MM`` collisions and returns
        messages instead of raising, so callers can warn without crashing.
        """
        tasks = self.get_all_tasks() if tasks is None else tasks
        by_time: dict = {}
        for task in tasks:
            by_time.setdefault(task.time, []).append(task)

        warnings: list = []
        for time_slot, group in sorted(by_time.items()):
            if len(group) > 1:
                who = ", ".join(f"{t.description} ({t.pet_name})" for t in group)
                warnings.append(f"⚠️ Conflict at {time_slot}: {who}")
        return warnings

    # -- recurrence ---------------------------------------------------------- #
    def mark_task_complete(self, task: Task) -> "Task | None":
        """Mark a task done; auto-create the next instance if it recurs.

        Returns the newly created follow-up task (added to the same pet) for
        daily/weekly tasks, or ``None`` for one-off tasks.
        """
        task.mark_complete()
        follow_up = task.next_occurrence()
        if follow_up is not None:
            pet = self.owner.get_pet(task.pet_name)
            if pet is not None:
                pet.add_task(follow_up)
        return follow_up

    # -- advanced: next available slot (Challenge 1) ------------------------- #
    def next_available_slot(self, duration_minutes: int,
                            day_start: str = "06:00",
                            day_end: str = "22:00",
                            tasks: "list | None" = None) -> "str | None":
        """Find the earliest gap that fits ``duration_minutes``.

        Scans the day between ``day_start`` and ``day_end`` around already
        scheduled (incomplete) tasks and returns the start time as ``HH:MM``,
        or ``None`` if nothing fits.
        """
        tasks = self.get_all_tasks() if tasks is None else tasks
        busy = sorted(
            (t for t in tasks if not t.completed),
            key=lambda t: t.time_in_minutes(),
        )
        start = self._to_minutes(day_start)
        end = self._to_minutes(day_end)

        cursor = start
        for task in busy:
            if task.time_in_minutes() - cursor >= duration_minutes:
                return self._to_hhmm(cursor)
            cursor = max(cursor, task.end_in_minutes())
        if end - cursor >= duration_minutes:
            return self._to_hhmm(cursor)
        return None

    # -- presentation -------------------------------------------------------- #
    def todays_schedule(self, sort_by: str = "time",
                        pet_name: "str | None" = None) -> str:
        """Build a formatted, human-readable schedule string for the terminal."""
        tasks = self.get_all_tasks()
        if pet_name:
            tasks = self.filter_by_pet(pet_name, tasks)

        if sort_by == "priority":
            tasks = self.sort_by_priority(tasks)
        else:
            tasks = self.sort_by_time(tasks)

        header = f"Today's Schedule for {self.owner.name}"
        if not tasks:
            return f"{header}\n{'-' * len(header)}\n  (no tasks scheduled)"

        lines = [header, "-" * len(header)]
        for t in tasks:
            lines.append(
                f"  {t.status_emoji()} {t.time}  {t.type_emoji()} "
                f"{t.description:<22} {t.duration_minutes:>3} min  "
                f"{PRIORITY_EMOJI.get(t.priority, '')} {t.priority:<6} "
                f"· {t.pet_name}"
            )

        for warning in self.detect_conflicts(tasks):
            lines.append(f"  {warning}")
        return "\n".join(lines)

    def format_table(self, tasks: "list | None" = None) -> str:
        """Render tasks as an aligned table (uses ``tabulate`` if available)."""
        tasks = self.sort_by_time() if tasks is None else tasks
        rows = [
            [t.status_emoji(), t.time, t.description,
             f"{t.duration_minutes} min", t.priority, t.pet_name]
            for t in tasks
        ]
        headers = ["", "Time", "Task", "Duration", "Priority", "Pet"]
        try:
            from tabulate import tabulate
            return tabulate(rows, headers=headers, tablefmt="github")
        except ImportError:  # graceful fallback, no hard dependency
            out = ["  ".join(headers)]
            out += ["  ".join(str(c) for c in row) for row in rows]
            return "\n".join(out)

    # -- helpers ------------------------------------------------------------- #
    @staticmethod
    def _to_minutes(hhmm: str) -> int:
        """Parse ``HH:MM`` into minutes past midnight."""
        h, m = hhmm.split(":")
        return int(h) * 60 + int(m)

    @staticmethod
    def _to_hhmm(minutes: int) -> str:
        """Format minutes past midnight back into an ``HH:MM`` string."""
        return f"{minutes // 60:02d}:{minutes % 60:02d}"


# --------------------------------------------------------------------------- #
# Persistence (Challenge 2)
# --------------------------------------------------------------------------- #

def save_to_json(owner: Owner, path: str = "data.json") -> None:
    """Serialize an owner (and all pets/tasks) to a JSON file."""
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(owner.to_dict(), fh, indent=2)


def load_from_json(path: str = "data.json") -> "Owner | None":
    """Rebuild an owner from a JSON file, or return None if it doesn't exist."""
    try:
        with open(path, encoding="utf-8") as fh:
            return Owner.from_dict(json.load(fh))
    except FileNotFoundError:
        return None
