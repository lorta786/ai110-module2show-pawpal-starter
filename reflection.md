# PawPal+ Project Reflection

## System Design (natural-language actions)

Three core actions a user should be able to perform:

1. **Add a pet** and register basic details (name, species, breed).
2. **Schedule a task** for a pet (a walk, feeding, medication, or appointment)
   with a time, duration, priority, and how often it repeats.
3. **See today's plan** — a single sorted schedule across all pets, with
   conflicts flagged and recurring tasks rolling forward automatically.

---

## 1. System Design

**a. Initial design**

I chose four classes with clearly separated responsibilities:

- **`Task`** — one activity. Holds description, time, duration, priority,
  frequency, completion status, and a due date. It owns the small bits of logic
  that belong to a single task (marking itself complete, producing its next
  occurrence).
- **`Pet`** — a container for one animal's details and its own list of tasks.
- **`Owner`** — manages multiple pets and can flatten every task across them.
- **`Scheduler`** — the "brain." It never stores data itself; it reads from the
  `Owner` and does all the organizing: sorting, filtering, conflict detection,
  and recurrence.

The relationships are simple aggregations: an `Owner` *has* `Pet`s, a `Pet`
*has* `Task`s, and the `Scheduler` *reads* an `Owner`. Keeping the `Scheduler`
separate from the data classes was deliberate — it means I can change scheduling
behavior without touching the model.

**b. Design changes**

Two changes came out of implementation:

1. **Tasks needed to know their pet.** My first skeleton had the `Scheduler`
   pass `(pet, task)` pairs around. That got clumsy fast, so I added a
   `pet_name` field to `Task` that `Pet.add_task()` stamps automatically. Now a
   flat list of tasks still knows which pet each belongs to, which made
   filtering and conflict messages much cleaner.
2. **Recurrence needed real dates.** I originally tracked frequency as just a
   string. To make "the next daily task is tomorrow" actually correct, I added a
   `due_date` and used `datetime.timedelta` (+1 day for daily, +7 for weekly).

---

## 2. Scheduling Logic and Tradeoffs

a. Constraints and priorities

The scheduler considers **time** (for chronological ordering and conflict
detection), **priority** (High/Medium/Low, for the priority sort), and
**duration** (used by the next-available-slot search). I treated time as the
primary constraint because a daily pet routine is fundamentally clock-driven —
you feed and walk at set times — and layered priority on top for when an owner
wants to triage rather than read the day in order.

b. Tradeoffs

My conflict detection only flags **exact start-time matches**, not overlapping
durations. A 30-minute 08:00 walk and an 08:15 feeding technically overlap but
won't be flagged. I accepted this because it keeps the logic to a single
dictionary grouping (fast and easy to read), and for a home pet-care routine an
exact-collision warning catches the most common real mistake — double-booking
the same slot — without the complexity of interval math. It's the first thing
I'd upgrade with more time.

---

## 3. AI Collaboration

a. How you used AI
I used AI coding assistant to explain to me complex problems such as creating the UML
Diagram as well as selecting which classes I should use. As well as creating pytest
test cases The most useful prompts were specific and grounded in my own code.

b. Judgment and verification

I verified the pytest suite and I didn't accept AI output blindly as it would produce some weird test cases

---

## 4. Testing and Verification

a. What you tested

I tested task completion, task addition (task counts), chronological sorting,
priority sorting, filtering by pet and by status, daily and weekly recurrence,
one-off tasks not recurring, conflict detection, the next-available-slot
search, an empty-pet edge case, and a JSON save/load round-trip.These matter 
because they're the behaviors the UI depends on — if sorting or 
recurrence silently breaks, the whole daily plan is wrong.

b. Confidence

All 16 tests pass and cover the happy paths plus several edge
cases. However, with more time I'd test overlapping durations, invalid time strings, 
and tasks that cross midnight.

---

## 5. Reflection

a. What went well

The CLI-first workflow. Because the logic layer was fully working and tested
before I opened `app.py`, wiring the Streamlit UI was almost mechanical — I just
called methods that I already trusted. Separating the `Scheduler` from the data
also paid off: adding priority sorting and the next-available-slot feature
didn't require touching `Task`, `Pet`, or `Owner`.

b. What you would improve

I'd replace exact-time conflict detection with true interval-overlap checking,
and I'd move persistence from a single `data.json` to something that supports
multiple saved profiles. I'd also add input validation on the `HH:MM` field in
the UI.

c. Key takeaway

The most important thing I learned is that **the human sets the structure and
the AI fills it in.** When I gave the assistant a clear class design and asked
narrow, code-grounded questions, it accelerated me enormously; when I asked it
to "design the app," it produced plausible-looking code that didn't match my
mental model. Owning the architecture — and verifying every suggestion against a
demo and a test — is what kept the system coherent.
