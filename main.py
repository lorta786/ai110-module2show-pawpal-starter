"""PawPal+ CLI demo / testing ground.

Run with:  python main.py

This script exercises the backend logic in ``pawpal_system.py`` end-to-end so
we can verify behavior in the terminal before wiring it into Streamlit. It
demonstrates: building owners/pets/tasks, sorting, filtering, conflict
detection, recurring tasks, the "next available slot" algorithm, and JSON
persistence.
"""

from pawpal_system import (
    Owner,
    Pet,
    Task,
    Scheduler,
    save_to_json,
    load_from_json,
)


def divider(title: str) -> None:
    """Print a titled section divider to keep the demo output readable."""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def main() -> None:
    """Run the full PawPal+ demonstration."""
    # --- Build the world: one owner, two pets ------------------------------ #
    owner = Owner("Leo")
    biscuit = owner.add_pet(Pet("Biscuit", species="dog", breed="Golden Retriever"))
    mochi = owner.add_pet(Pet("Mochi", species="cat", breed="Tabby"))

    # --- Add tasks OUT OF ORDER (to prove sorting works) ------------------- #
    biscuit.add_task(Task("Evening walk", time="18:00", duration_minutes=30,
                          priority="high", frequency="daily"))
    biscuit.add_task(Task("Morning walk", time="08:00", duration_minutes=30,
                          priority="high", frequency="daily"))
    mochi.add_task(Task("Feed breakfast", time="08:00", duration_minutes=10,
                        priority="high", frequency="daily"))   # conflict @ 08:00
    mochi.add_task(Task("Vet appointment", time="14:30", duration_minutes=60,
                        priority="medium", frequency="once"))
    biscuit.add_task(Task("Give medication", time="12:00", duration_minutes=5,
                          priority="high", frequency="daily"))

    scheduler = Scheduler(owner)

    # --- Today's schedule (sorted chronologically) ------------------------- #
    divider("TODAY'S SCHEDULE (sorted by time)")
    print(scheduler.todays_schedule())

    # --- Same schedule, sorted by priority (Challenge 3) ------------------- #
    divider("TODAY'S SCHEDULE (sorted by priority, then time)")
    print(scheduler.todays_schedule(sort_by="priority"))

    # --- Filtering --------------------------------------------------------- #
    divider("FILTER: only Biscuit's tasks")
    for t in scheduler.filter_by_pet("Biscuit"):
        print(f"  {t}")

    divider("FILTER: only pending (incomplete) tasks")
    for t in scheduler.filter_by_status(completed=False):
        print(f"  {t}")

    # --- Conflict detection ------------------------------------------------ #
    divider("CONFLICT DETECTION")
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        for warning in conflicts:
            print(f"  {warning}")
    else:
        print("  No conflicts found.")

    # --- Recurring tasks --------------------------------------------------- #
    divider("RECURRING TASKS: complete the daily morning walk")
    morning = next(t for t in scheduler.filter_by_pet("Biscuit")
                   if t.description == "Morning walk")
    print(f"  Before: {morning}")
    follow_up = scheduler.mark_task_complete(morning)
    print(f"  After:  {morning}")
    print(f"  Auto-created next occurrence: {follow_up}")
    print(f"  Biscuit now has {biscuit.task_count} tasks.")

    # --- Next available slot (Challenge 1) --------------------------------- #
    divider("NEXT AVAILABLE SLOT: find 45 free minutes")
    slot = scheduler.next_available_slot(45)
    print(f"  Earliest 45-minute opening today: {slot}")

    # --- Persistence (Challenge 2) ----------------------------------------- #
    divider("PERSISTENCE: save + reload from data.json")
    save_to_json(owner, "data.json")
    reloaded = load_from_json("data.json")
    print(f"  Reloaded owner '{reloaded.name}' with "
          f"{len(reloaded.pets)} pets and "
          f"{len(reloaded.all_tasks())} total tasks from disk.")

    # --- Clean tabular view (Challenge 4) ---------------------------------- #
    divider("TABLE VIEW")
    print(scheduler.format_table())


if __name__ == "__main__":
    main()
