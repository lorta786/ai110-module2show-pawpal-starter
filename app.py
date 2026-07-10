"""PawPal+ Streamlit UI.

This is the *presentation layer*. All real logic lives in ``pawpal_system.py``;
this file just collects input, calls the backend methods, and displays results.

Run with:  streamlit run app.py
"""

import streamlit as st

from pawpal_system import (
    Owner,
    Pet,
    Task,
    Scheduler,
    save_to_json,
    load_from_json,
)

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

PRIORITY_BADGE = {"high": "🔴 high", "medium": "🟡 medium", "low": "🟢 low"}


# --------------------------------------------------------------------------- #
# Session state = the app's "memory"
# --------------------------------------------------------------------------- #
# Streamlit re-runs this whole script on every interaction, so we must keep the
# Owner object in st.session_state or it would be "reborn" empty each rerun.

def get_owner() -> Owner:
    """Return the persistent Owner, creating it once per session."""
    if "owner" not in st.session_state:
        st.session_state.owner = Owner("Leo")
    return st.session_state.owner


owner = get_owner()
scheduler = Scheduler(owner)   # cheap wrapper; always reflects current owner


# --------------------------------------------------------------------------- #
# Header
# --------------------------------------------------------------------------- #
st.title("🐾 PawPal+")
st.caption("A smart pet-care scheduler — sorts, filters, detects conflicts, "
           "and handles recurring tasks.")

owner.name = st.text_input("Owner name", value=owner.name)


# --------------------------------------------------------------------------- #
# Sidebar: add pets + persistence
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.header("🐶 Pets")
    with st.form("add_pet_form", clear_on_submit=True):
        pet_name = st.text_input("Pet name")
        species = st.selectbox("Species", ["dog", "cat", "other"])
        breed = st.text_input("Breed (optional)")
        if st.form_submit_button("Add pet") and pet_name.strip():
            owner.add_pet(Pet(pet_name.strip(), species=species, breed=breed.strip()))
            st.success(f"Added {pet_name}!")

    if owner.pets:
        st.write("Current pets:")
        for p in owner.pets:
            st.write(f"- {p.name} ({p.species}) — {p.task_count} tasks")

    st.divider()
    st.header("💾 Save / Load")
    if st.button("Save to data.json"):
        save_to_json(owner, "data.json")
        st.success("Saved!")
    if st.button("Load from data.json"):
        loaded = load_from_json("data.json")
        if loaded is None:
            st.warning("No data.json found yet.")
        else:
            st.session_state.owner = loaded
            st.success("Loaded! (Rerun to refresh)")


# --------------------------------------------------------------------------- #
# Add a task
# --------------------------------------------------------------------------- #
st.subheader("➕ Add a task")
if not owner.pets:
    st.info("Add a pet in the sidebar first.")
else:
    with st.form("add_task_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            which_pet = st.selectbox("Pet", [p.name for p in owner.pets])
            description = st.text_input("Task", value="Morning walk")
            priority = st.selectbox("Priority", ["high", "medium", "low"])
        with col2:
            time = st.text_input("Time (HH:MM)", value="08:00")
            duration = st.number_input("Duration (min)", 1, 240, 30)
            frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])

        if st.form_submit_button("Add task") and description.strip():
            pet = owner.get_pet(which_pet)
            pet.add_task(Task(description.strip(), time=time,
                              duration_minutes=int(duration),
                              priority=priority, frequency=frequency))
            st.success(f"Added '{description}' for {which_pet} at {time}.")


# --------------------------------------------------------------------------- #
# The schedule
# --------------------------------------------------------------------------- #
st.divider()
st.subheader("📅 Today's Schedule")

if not scheduler.get_all_tasks():
    st.info("No tasks yet. Add one above.")
else:
    c1, c2 = st.columns(2)
    sort_by = c1.radio("Sort by", ["time", "priority"], horizontal=True)
    pet_options = ["All pets"] + [p.name for p in owner.pets]
    pet_filter = c2.selectbox("Show", pet_options)

    tasks = scheduler.get_all_tasks()
    if pet_filter != "All pets":
        tasks = scheduler.filter_by_pet(pet_filter, tasks)
    tasks = (scheduler.sort_by_priority(tasks) if sort_by == "priority"
             else scheduler.sort_by_time(tasks))

    # Conflict warnings — surfaced clearly so a busy owner notices them.
    for warning in scheduler.detect_conflicts(tasks):
        st.warning(warning)

    # Render as a clean table.
    st.table([
        {
            "Done": t.status_emoji(),
            "Time": t.time,
            "Task": f"{t.type_emoji()} {t.description}",
            "Duration": f"{t.duration_minutes} min",
            "Priority": PRIORITY_BADGE.get(t.priority, t.priority),
            "Pet": t.pet_name,
            "Repeats": t.frequency,
        }
        for t in tasks
    ])

    done = len(scheduler.filter_by_status(True))
    total = len(scheduler.get_all_tasks())
    st.caption(f"{done}/{total} tasks completed.")

    # Mark a task complete (demonstrates recurrence in the UI).
    st.markdown("**✅ Mark a task complete**")
    pending = scheduler.filter_by_status(False)
    if pending:
        labels = {f"{t.time} · {t.description} ({t.pet_name})": t for t in pending}
        choice = st.selectbox("Pick a pending task", list(labels.keys()))
        if st.button("Mark complete"):
            follow_up = scheduler.mark_task_complete(labels[choice])
            if follow_up is not None:
                st.success(f"Done! Auto-scheduled the next '{follow_up.description}' "
                           f"for {follow_up.due_date}.")
            else:
                st.success("Marked complete.")
            st.rerun()
    else:
        st.caption("All tasks complete 🎉")


# --------------------------------------------------------------------------- #
# Find a free slot (Challenge 1)
# --------------------------------------------------------------------------- #
st.divider()
st.subheader("🔎 Find a free slot")
need = st.number_input("Minutes needed", 5, 240, 45, step=5)
if st.button("Find next opening"):
    slot = scheduler.next_available_slot(int(need))
    if slot:
        st.success(f"Earliest {need}-minute opening today: **{slot}**")
    else:
        st.warning("No opening that long left today.")
