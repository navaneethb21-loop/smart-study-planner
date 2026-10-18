import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import datetime, date, timedelta
import csv


# ============================================================
# DATABASE
# ============================================================

DB_NAME = "study_planner.db"

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    difficulty TEXT NOT NULL,
    priority TEXT NOT NULL,
    score INTEGER NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS study_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER,
    subject_name TEXT NOT NULL,
    study_date TEXT NOT NULL,
    planned_minutes INTEGER NOT NULL,
    completed INTEGER DEFAULT 0
)
""")

conn.commit()


# ============================================================
# MAIN WINDOW
# ============================================================

root = tk.Tk()
root.title("Smart Study Planner V5")
root.geometry("1100x750")
root.minsize(950, 650)

# Main style
style = ttk.Style()

try:
    style.theme_use("clam")
except:
    pass

style.configure("Title.TLabel", font=("Arial", 24, "bold"))
style.configure("Subtitle.TLabel", font=("Arial", 11))
style.configure("Card.TLabel", font=("Arial", 20, "bold"))
style.configure("CardTitle.TLabel", font=("Arial", 10))
style.configure("Heading.TLabel", font=("Arial", 15, "bold"))
style.configure("BigTimer.TLabel", font=("Arial", 42, "bold"))


# ============================================================
# VARIABLES
# ============================================================

name_var = tk.StringVar()
study_time_var = tk.StringVar()
mood_var = tk.StringVar(value="Good")

subject_name_var = tk.StringVar()
difficulty_var = tk.StringVar(value="Medium")
priority_var = tk.StringVar(value="Medium")

timer_subject_var = tk.StringVar(value="No session selected")
timer_display_var = tk.StringVar(value="00:00")

timer_seconds = 0
timer_running = False
timer_job = None
current_timer_session_id = None


# ============================================================
# SUBJECT STORAGE
# ============================================================

subjects = []


def load_subjects():
    """Load subjects from SQLite into memory."""
    subjects.clear()

    cursor.execute("""
        SELECT id, name, difficulty, priority, score
        FROM subjects
        ORDER BY id
    """)

    rows = cursor.fetchall()

    for row in rows:
        subjects.append({
            "id": row[0],
            "name": row[1],
            "difficulty": row[2],
            "priority": row[3],
            "score": row[4]
        })


load_subjects()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def difficulty_weight(difficulty):
    weights = {
        "Hard": 3,
        "Medium": 2,
        "Easy": 1
    }

    return weights.get(difficulty, 1)


def priority_weight(priority):
    weights = {
        "High": 3,
        "Medium": 2,
        "Low": 1
    }

    return weights.get(priority, 1)


def calculate_score(difficulty, priority):
    return difficulty_weight(difficulty) + priority_weight(priority)


def refresh_subject_list():
    subject_tree.delete(*subject_tree.get_children())

    for subject in subjects:
        subject_tree.insert(
            "",
            "end",
            iid=str(subject["id"]),
            values=(
                subject["name"],
                subject["difficulty"],
                subject["priority"],
                subject["score"]
            )
        )


def get_today():
    return date.today().strftime("%Y-%m-%d")


# ============================================================
# ADD SUBJECT
# ============================================================

def add_subject():

    subject_name = subject_name_var.get().strip()
    difficulty = difficulty_var.get()
    priority = priority_var.get()

    if not subject_name:
        messagebox.showwarning(
            "Missing Subject",
            "Please enter a subject name."
        )
        return

    # Duplicate check
    for subject in subjects:
        if subject["name"].lower() == subject_name.lower():
            messagebox.showwarning(
                "Duplicate Subject",
                "This subject already exists."
            )
            return

    score = calculate_score(difficulty, priority)

    # Save to database
    cursor.execute("""
        INSERT INTO subjects
        (name, difficulty, priority, score)
        VALUES (?, ?, ?, ?)
    """, (
        subject_name,
        difficulty,
        priority,
        score
    ))

    conn.commit()

    subject_id = cursor.lastrowid

    subjects.append({
        "id": subject_id,
        "name": subject_name,
        "difficulty": difficulty,
        "priority": priority,
        "score": score
    })

    refresh_subject_list()

    subject_name_var.set("")
    difficulty_var.set("Medium")
    priority_var.set("Medium")


# ============================================================
# REMOVE SUBJECT
# ============================================================

def remove_subject():

    selected = subject_tree.selection()

    if not selected:
        messagebox.showwarning(
            "No Selection",
            "Please select a subject to remove."
        )
        return

    subject_id = int(selected[0])

    selected_subject = None

    for subject in subjects:
        if subject["id"] == subject_id:
            selected_subject = subject
            break

    if selected_subject is None:
        return

    confirm = messagebox.askyesno(
        "Remove Subject",
        f"Remove '{selected_subject['name']}'?"
    )

    if not confirm:
        return

    cursor.execute(
        "DELETE FROM subjects WHERE id = ?",
        (subject_id,)
    )

    conn.commit()

    subjects.remove(selected_subject)

    refresh_subject_list()


# ============================================================
# RESET SUBJECTS
# ============================================================

def reset_subjects():

    if not subjects:
        messagebox.showinfo(
            "Reset Subjects",
            "There are no subjects to reset."
        )
        return

    confirm = messagebox.askyesno(
        "Reset Subjects",
        "Remove all current subjects?"
    )

    if not confirm:
        return

    cursor.execute("DELETE FROM subjects")
    conn.commit()

    subjects.clear()

    refresh_subject_list()


# ============================================================
# TIME ALLOCATION
# ============================================================

def allocate_time(total_minutes, subject_list):

    """
    Allocate available study time according to subject scores.

    Handles small time values so that total allocated time
    never exceeds the available study time.
    """

    if total_minutes <= 0 or not subject_list:
        return []

    number_of_subjects = len(subject_list)

    # If there isn't enough time to give one minute to everyone,
    # only schedule as many subjects as there are minutes.
    if total_minutes < number_of_subjects:

        sorted_subjects = sorted(
            subject_list,
            key=lambda x: x["score"],
            reverse=True
        )

        selected = sorted_subjects[:total_minutes]

        return [
            {
                "subject": s,
                "minutes": 1
            }
            for s in selected
        ]

    total_score = sum(s["score"] for s in subject_list)

    allocations = []

    # First give everyone one minute
    remaining_time = total_minutes - number_of_subjects

    for subject in subject_list:

        extra = 0

        if total_score > 0:
            extra = int(
                remaining_time *
                subject["score"] /
                total_score
            )

        allocations.append({
            "subject": subject,
            "minutes": 1 + extra
        })

    # Handle rounding differences
    allocated = sum(item["minutes"] for item in allocations)

    difference = total_minutes - allocated

    index = 0

    while difference > 0:
        allocations[index]["minutes"] += 1
        difference -= 1
        index = (index + 1) % len(allocations)

    while difference < 0:

        if allocations[index]["minutes"] > 1:
            allocations[index]["minutes"] -= 1
            difference += 1

        index = (index + 1) % len(allocations)

    return allocations


# ============================================================
# GENERATE STUDY PLAN
# ============================================================

def generate_plan():

    name = name_var.get().strip()
    time_text = study_time_var.get().strip()
    mood = mood_var.get()

    if not name:
        messagebox.showwarning(
            "Missing Name",
            "Please enter your name."
        )
        return

    if not time_text:
        messagebox.showwarning(
            "Missing Time",
            "Please enter your available study time."
        )
        return

    try:
        total_time = int(time_text)
    except ValueError:
        messagebox.showwarning(
            "Invalid Time",
            "Study time must be a number."
        )
        return

    if total_time <= 0:
        messagebox.showwarning(
            "Invalid Time",
            "Study time must be greater than 0."
        )
        return

    if not subjects:
        messagebox.showwarning(
            "No Subjects",
            "Please add at least one subject."
        )
        return

    # Break handling
    break_time = 0

    if total_time > 60:
        study_minutes = total_time - 10
        break_time = 10
    else:
        study_minutes = total_time

    # Mood-based ordering
    planning_subjects = subjects.copy()

    if mood == "Good":

        planning_subjects.sort(
            key=lambda x: x["score"],
            reverse=True
        )

    elif mood == "Tired":

        planning_subjects.sort(
            key=lambda x: x["score"]
        )

    elif mood == "Stressed":

        # Start with easier subjects
        planning_subjects.sort(
            key=lambda x: (
                difficulty_weight(x["difficulty"]),
                -x["score"]
            )
        )

    allocations = allocate_time(
        study_minutes,
        planning_subjects
    )

    if not allocations:
        messagebox.showwarning(
            "Unable to Plan",
            "There isn't enough time to create a study plan."
        )
        return

    # Create plan window
    plan_window = tk.Toplevel(root)
    plan_window.title("Today's Study Plan")
    plan_window.geometry("850x600")

    ttk.Label(
        plan_window,
        text=f"{name}'s Study Plan",
        style="Title.TLabel"
    ).pack(pady=15)

    ttk.Label(
        plan_window,
        text=f"Mood: {mood}    |    Available Time: {total_time} minutes"
    ).pack(pady=5)

    # Plan table
    columns = (
        "order",
        "subject",
        "difficulty",
        "priority",
        "minutes"
    )

    plan_tree = ttk.Treeview(
        plan_window,
        columns=columns,
        show="headings",
        height=12
    )

    headings = {
        "order": "#",
        "subject": "Subject",
        "difficulty": "Difficulty",
        "priority": "Priority",
        "minutes": "Minutes"
    }

    for column in columns:
        plan_tree.heading(
            column,
            text=headings[column]
        )

    plan_tree.column("order", width=50, anchor="center")
    plan_tree.column("subject", width=250)
    plan_tree.column("difficulty", width=110, anchor="center")
    plan_tree.column("priority", width=110, anchor="center")
    plan_tree.column("minutes", width=100, anchor="center")

    plan_tree.pack(
        fill="both",
        expand=True,
        padx=20,
        pady=15
    )

    # Save generated sessions
    session_ids = []

    for index, item in enumerate(allocations, start=1):

        subject = item["subject"]
        minutes = item["minutes"]

        plan_tree.insert(
            "",
            "end",
            values=(
                index,
                subject["name"],
                subject["difficulty"],
                subject["priority"],
                minutes
            )
        )

        cursor.execute("""
            INSERT INTO study_sessions
            (subject_id, subject_name, study_date, planned_minutes, completed)
            VALUES (?, ?, ?, ?, 0)
        """, (
            subject["id"],
            subject["name"],
            get_today(),
            minutes
        ))

        session_ids.append(cursor.lastrowid)

    conn.commit()

    if break_time > 0:

        ttk.Label(
            plan_window,
            text="☕ 10-minute break included after the study plan.",
            font=("Arial", 11, "bold")
        ).pack(pady=5)

    # Button area
    button_frame = ttk.Frame(plan_window)
    button_frame.pack(pady=15)

    def start_selected_session():

        selected = plan_tree.selection()

        if not selected:
            messagebox.showwarning(
                "Select Session",
                "Select a study session first."
            )
            return

        item = plan_tree.item(selected[0])
        values = item["values"]

        subject_name = values[1]
        minutes = int(values[4])

        # Find corresponding session
        row_index = plan_tree.index(selected[0])

        if row_index >= len(session_ids):
            return

        session_id = session_ids[row_index]

        open_timer(
            subject_name,
            minutes,
            session_id
        )

    ttk.Button(
        button_frame,
        text="START SELECTED SESSION",
        command=start_selected_session
    ).pack(side="left", padx=5)

    ttk.Button(
        button_frame,
        text="CLOSE",
        command=plan_window.destroy
    ).pack(side="left", padx=5)


# ============================================================
# TIMER
# ============================================================

def open_timer(subject_name, minutes, session_id=None):

    global timer_seconds
    global timer_running
    global current_timer_session_id

    timer_subject_var.set(subject_name)

    timer_seconds = minutes * 60
    timer_running = False
    current_timer_session_id = session_id

    update_timer_display()

    # Switch notebook to timer tab
    notebook.select(timer_tab)


def update_timer_display():

    minutes = timer_seconds // 60
    seconds = timer_seconds % 60

    timer_display_var.set(
        f"{minutes:02d}:{seconds:02d}"
    )


def timer_tick():

    global timer_seconds
    global timer_running
    global timer_job

    if not timer_running:
        return

    if timer_seconds > 0:

        timer_seconds -= 1
        update_timer_display()

        timer_job = root.after(
            1000,
            timer_tick
        )

    else:

        timer_running = False

        messagebox.showinfo(
            "Timer Complete",
            "Study session completed! 🎉"
        )

        complete_current_timer_session()


def start_timer():

    global timer_running

    if timer_seconds <= 0:
        messagebox.showwarning(
            "Timer",
            "Please select a study session first."
        )
        return

    if timer_running:
        return

    timer_running = True

    timer_tick()


def pause_timer():

    global timer_running
    global timer_job

    timer_running = False

    if timer_job is not None:

        try:
            root.after_cancel(timer_job)
        except:
            pass

        timer_job = None


def reset_timer():

    global timer_running
    global timer_job
    global timer_seconds

    pause_timer()

    timer_seconds = 0

    update_timer_display()

    timer_subject_var.set(
        "No session selected"
    )


def complete_current_timer_session():

    global current_timer_session_id

    if current_timer_session_id is None:
        return

    cursor.execute("""
        UPDATE study_sessions
        SET completed = 1
        WHERE id = ?
    """, (
        current_timer_session_id,
    ))

    conn.commit()

    current_timer_session_id = None

    update_dashboard()


def manually_complete_timer():

    if current_timer_session_id is None:
        messagebox.showwarning(
            "No Session",
            "Select a study session first."
        )
        return

    confirm = messagebox.askyesno(
        "Complete Session",
        "Mark this session as completed?"
    )

    if not confirm:
        return

    pause_timer()

    complete_current_timer_session()

    messagebox.showinfo(
        "Completed",
        "Study session marked as completed."
    )


# ============================================================
# DASHBOARD DATA
# ============================================================

def get_completed_sessions():

    cursor.execute("""
        SELECT COUNT(*)
        FROM study_sessions
        WHERE completed = 1
    """)

    return cursor.fetchone()[0]


def get_completed_minutes():

    cursor.execute("""
        SELECT COALESCE(SUM(planned_minutes), 0)
        FROM study_sessions
        WHERE completed = 1
    """)

    return cursor.fetchone()[0]


def get_total_sessions():

    cursor.execute("""
        SELECT COUNT(*)
        FROM study_sessions
    """)

    return cursor.fetchone()[0]


def get_completion_percentage():

    total = get_total_sessions()
    completed = get_completed_sessions()

    if total == 0:
        return 0

    return round(
        (completed / total) * 100
    )


# ============================================================
# STUDY STREAK
# ============================================================

def get_study_streak():

    cursor.execute("""
        SELECT DISTINCT study_date
        FROM study_sessions
        WHERE completed = 1
        ORDER BY study_date DESC
    """)

    rows = cursor.fetchall()

    if not rows:
        return 0

    dates = set(
        datetime.strptime(
            row[0],
            "%Y-%m-%d"
        ).date()
        for row in rows
    )

    current_date = date.today()

    # If there was no study today, check yesterday.
    if current_date not in dates:

        current_date -= timedelta(days=1)

        if current_date not in dates:
            return 0

    streak = 0

    while current_date in dates:

        streak += 1
        current_date -= timedelta(days=1)

    return streak


# ============================================================
# WEEKLY STATS
# ============================================================

def get_weekly_minutes():

    today = date.today()

    week_start = today - timedelta(
        days=today.weekday()
    )

    week_start_text = week_start.strftime(
        "%Y-%m-%d"
    )

    cursor.execute("""
        SELECT COALESCE(SUM(planned_minutes), 0)
        FROM study_sessions
        WHERE completed = 1
        AND study_date >= ?
    """, (
        week_start_text,
    ))

    return cursor.fetchone()[0]


def get_today_minutes():

    cursor.execute("""
        SELECT COALESCE(SUM(planned_minutes), 0)
        FROM study_sessions
        WHERE completed = 1
        AND study_date = ?
    """, (
        get_today(),
    ))

    return cursor.fetchone()[0]


# ============================================================
# DASHBOARD UPDATE
# ============================================================

def update_dashboard():

    completed = get_completed_sessions()
    minutes = get_completed_minutes()
    streak = get_study_streak()
    weekly = get_weekly_minutes()
    percentage = get_completion_percentage()
    today_minutes = get_today_minutes()

    completed_value_label.config(
        text=str(completed)
    )

    minutes_value_label.config(
        text=str(minutes)
    )

    streak_value_label.config(
        text=str(streak)
    )

    weekly_value_label.config(
        text=f"{weekly} min"
    )

    today_value_label.config(
        text=f"{today_minutes} min"
    )

    completion_value_label.config(
        text=f"{percentage}%"
    )

    progress_bar["value"] = percentage


# ============================================================
# HISTORY WINDOW
# ============================================================

def show_history():

    history_window = tk.Toplevel(root)

    history_window.title(
        "Study History"
    )

    history_window.geometry(
        "900x550"
    )

    ttk.Label(
        history_window,
        text="Study History",
        style="Title.TLabel"
    ).pack(pady=15)

    columns = (
        "date",
        "subject",
        "minutes",
        "status"
    )

    tree = ttk.Treeview(
        history_window,
        columns=columns,
        show="headings"
    )

    tree.heading(
        "date",
        text="Date"
    )

    tree.heading(
        "subject",
        text="Subject"
    )

    tree.heading(
        "minutes",
        text="Minutes"
    )

    tree.heading(
        "status",
        text="Status"
    )

    tree.column(
        "date",
        width=150
    )

    tree.column(
        "subject",
        width=350
    )

    tree.column(
        "minutes",
        width=120,
        anchor="center"
    )

    tree.column(
        "status",
        width=150,
        anchor="center"
    )

    tree.pack(
        fill="both",
        expand=True,
        padx=20,
        pady=10
    )

    cursor.execute("""
        SELECT study_date,
               subject_name,
               planned_minutes,
               completed
        FROM study_sessions
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    for row in rows:

        status = (
            "Completed"
            if row[3] == 1
            else "Pending"
        )

        tree.insert(
            "",
            "end",
            values=(
                row[0],
                row[1],
                row[2],
                status
            )
        )


# ============================================================
# PROGRESS WINDOW
# ============================================================

def show_progress():

    progress_window = tk.Toplevel(root)

    progress_window.title(
        "Progress Statistics"
    )

    progress_window.geometry(
        "650x550"
    )

    ttk.Label(
        progress_window,
        text="Progress Statistics",
        style="Title.TLabel"
    ).pack(pady=20)

    completed = get_completed_sessions()
    total = get_total_sessions()
    minutes = get_completed_minutes()
    percentage = get_completion_percentage()
    streak = get_study_streak()
    weekly = get_weekly_minutes()

    stats_frame = ttk.Frame(
        progress_window
    )

    stats_frame.pack(
        fill="x",
        padx=30,
        pady=10
    )

    stats = [
        ("Completed Sessions", completed),
        ("Total Sessions", total),
        ("Study Minutes", minutes),
        ("Completion", f"{percentage}%"),
        ("Current Streak", f"{streak} days"),
        ("This Week", f"{weekly} min")
    ]

    for index, (title, value) in enumerate(stats):

        frame = ttk.LabelFrame(
            stats_frame,
            text=title
        )

        frame.grid(
            row=index // 2,
            column=index % 2,
            padx=10,
            pady=10,
            sticky="nsew"
        )

        ttk.Label(
            frame,
            text=str(value),
            style="Card.TLabel"
        ).pack(
            padx=30,
            pady=20
        )

    stats_frame.columnconfigure(
        0,
        weight=1
    )

    stats_frame.columnconfigure(
        1,
        weight=1
    )

    ttk.Label(
        progress_window,
        text="Overall Completion"
    ).pack(
        pady=(20, 5)
    )

    progress = ttk.Progressbar(
        progress_window,
        length=450,
        mode="determinate",
        maximum=100
    )

    progress["value"] = percentage

    progress.pack(
        pady=10
    )


# ============================================================
# WEEKLY STATISTICS WINDOW
# ============================================================

def show_weekly_stats():

    weekly_window = tk.Toplevel(root)

    weekly_window.title(
        "Weekly Statistics"
    )

    weekly_window.geometry(
        "800x500"
    )

    ttk.Label(
        weekly_window,
        text="Weekly Study Statistics",
        style="Title.TLabel"
    ).pack(pady=15)

    columns = (
        "day",
        "date",
        "minutes",
        "sessions"
    )

    tree = ttk.Treeview(
        weekly_window,
        columns=columns,
        show="headings"
    )

    tree.heading(
        "day",
        text="Day"
    )

    tree.heading(
        "date",
        text="Date"
    )

    tree.heading(
        "minutes",
        text="Minutes"
    )

    tree.heading(
        "sessions",
        text="Sessions"
    )

    tree.column(
        "day",
        width=150
    )

    tree.column(
        "date",
        width=180
    )

    tree.column(
        "minutes",
        width=150,
        anchor="center"
    )

    tree.column(
        "sessions",
        width=150,
        anchor="center"
    )

    tree.pack(
        fill="both",
        expand=True,
        padx=25,
        pady=15
    )

    today = date.today()

    week_start = today - timedelta(
        days=today.weekday()
    )

    for i in range(7):

        current_day = week_start + timedelta(
            days=i
        )

        current_text = current_day.strftime(
            "%Y-%m-%d"
        )

        cursor.execute("""
            SELECT
                COALESCE(SUM(planned_minutes), 0),
                COUNT(*)
            FROM study_sessions
            WHERE study_date = ?
            AND completed = 1
        """, (
            current_text,
        ))

        minutes, sessions = cursor.fetchone()

        tree.insert(
            "",
            "end",
            values=(
                current_day.strftime("%A"),
                current_text,
                minutes,
                sessions
            )
        )


# ============================================================
# CSV EXPORT
# ============================================================

def export_history():

    cursor.execute("""
        SELECT study_date,
               subject_name,
               planned_minutes,
               completed
        FROM study_sessions
        ORDER BY study_date DESC
    """)

    rows = cursor.fetchall()

    if not rows:
        messagebox.showinfo(
            "Export",
            "There is no study history to export."
        )
        return

    file_path = filedialog.asksaveasfilename(
        title="Export Study History",
        defaultextension=".csv",
        filetypes=[
            ("CSV files", "*.csv")
        ]
    )

    if not file_path:
        return

    try:

        with open(
            file_path,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                "Date",
                "Subject",
                "Planned Minutes",
                "Completed"
            ])

            for row in rows:

                writer.writerow([
                    row[0],
                    row[1],
                    row[2],
                    "Yes" if row[3] else "No"
                ])

        messagebox.showinfo(
            "Export Successful",
            "Study history exported successfully."
        )

    except Exception as error:

        messagebox.showerror(
            "Export Error",
            f"Could not export the file.\n\n{error}"
        )


# ============================================================
# NOTEBOOK
# ============================================================

notebook = ttk.Notebook(root)

dashboard_tab = ttk.Frame(notebook)
planner_tab = ttk.Frame(notebook)
timer_tab = ttk.Frame(notebook)

notebook.add(
    dashboard_tab,
    text="📊 Dashboard"
)

notebook.add(
    planner_tab,
    text="📚 Planner"
)

notebook.add(
    timer_tab,
    text="⏱ Timer"
)

notebook.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)


# ============================================================
# DASHBOARD TAB
# ============================================================

ttk.Label(
    dashboard_tab,
    text="Smart Study Planner V5",
    style="Title.TLabel"
).pack(pady=(20, 5))

ttk.Label(
    dashboard_tab,
    text="Your personal study dashboard",
    style="Subtitle.TLabel"
).pack(pady=(0, 20))


# Dashboard cards
cards_frame = ttk.Frame(
    dashboard_tab
)

cards_frame.pack(
    fill="x",
    padx=30
)


def create_card(parent, title):

    frame = ttk.LabelFrame(
        parent,
        text=title
    )

    frame.pack(
        side="left",
        fill="both",
        expand=True,
        padx=8
    )

    value = ttk.Label(
        frame,
        text="0",
        style="Card.TLabel"
    )

    value.pack(
        pady=25
    )

    return value


completed_value_label = create_card(
    cards_frame,
    "Completed Sessions"
)

minutes_value_label = create_card(
    cards_frame,
    "Total Minutes"
)

streak_value_label = create_card(
    cards_frame,
    "🔥 Study Streak"
)


# Second row
second_cards = ttk.Frame(
    dashboard_tab
)

second_cards.pack(
    fill="x",
    padx=30,
    pady=20
)

weekly_value_label = create_card(
    second_cards,
    "This Week"
)

today_value_label = create_card(
    second_cards,
    "Today"
)

completion_value_label = create_card(
    second_cards,
    "Completion"
)


# Progress
ttk.Label(
    dashboard_tab,
    text="Overall Progress",
    style="Heading.TLabel"
).pack(pady=(15, 5))

progress_bar = ttk.Progressbar(
    dashboard_tab,
    length=600,
    maximum=100,
    mode="determinate"
)

progress_bar.pack(
    pady=10
)


# Dashboard buttons
dashboard_buttons = ttk.Frame(
    dashboard_tab
)

dashboard_buttons.pack(
    pady=20
)

ttk.Button(
    dashboard_buttons,
    text="VIEW PROGRESS",
    command=show_progress
).pack(
    side="left",
    padx=5
)

ttk.Button(
    dashboard_buttons,
    text="WEEKLY STATS",
    command=show_weekly_stats
).pack(
    side="left",
    padx=5
)

ttk.Button(
    dashboard_buttons,
    text="VIEW HISTORY",
    command=show_history
).pack(
    side="left",
    padx=5
)

ttk.Button(
    dashboard_buttons,
    text="EXPORT CSV",
    command=export_history
).pack(
    side="left",
    padx=5
)


# ============================================================
# PLANNER TAB
# ============================================================

ttk.Label(
    planner_tab,
    text="Create Your Study Plan",
    style="Title.TLabel"
).pack(pady=15)


# User information
user_frame = ttk.LabelFrame(
    planner_tab,
    text="Study Information"
)

user_frame.pack(
    fill="x",
    padx=25,
    pady=5
)

ttk.Label(
    user_frame,
    text="Name:"
).grid(
    row=0,
    column=0,
    padx=10,
    pady=12
)

ttk.Entry(
    user_frame,
    textvariable=name_var,
    width=25
).grid(
    row=0,
    column=1,
    padx=10
)

ttk.Label(
    user_frame,
    text="Available Minutes:"
).grid(
    row=0,
    column=2,
    padx=10
)

ttk.Entry(
    user_frame,
    textvariable=study_time_var,
    width=15
).grid(
    row=0,
    column=3,
    padx=10
)

ttk.Label(
    user_frame,
    text="Mood:"
).grid(
    row=0,
    column=4,
    padx=10
)

mood_combo = ttk.Combobox(
    user_frame,
    textvariable=mood_var,
    values=[
        "Good",
        "Tired",
        "Stressed"
    ],
    state="readonly",
    width=12
)

mood_combo.grid(
    row=0,
    column=5,
    padx=10
)


# Subject input
subject_frame = ttk.LabelFrame(
    planner_tab,
    text="Add Subject"
)

subject_frame.pack(
    fill="x",
    padx=25,
    pady=10
)

ttk.Label(
    subject_frame,
    text="Subject:"
).grid(
    row=0,
    column=0,
    padx=10,
    pady=12
)

ttk.Entry(
    subject_frame,
    textvariable=subject_name_var,
    width=25
).grid(
    row=0,
    column=1,
    padx=10
)

ttk.Label(
    subject_frame,
    text="Difficulty:"
).grid(
    row=0,
    column=2,
    padx=10
)

difficulty_combo = ttk.Combobox(
    subject_frame,
    textvariable=difficulty_var,
    values=[
        "Easy",
        "Medium",
        "Hard"
    ],
    state="readonly",
    width=12
)

difficulty_combo.grid(
    row=0,
    column=3,
    padx=10
)

ttk.Label(
    subject_frame,
    text="Priority:"
).grid(
    row=0,
    column=4,
    padx=10
)

priority_combo = ttk.Combobox(
    subject_frame,
    textvariable=priority_var,
    values=[
        "Low",
        "Medium",
        "High"
    ],
    state="readonly",
    width=12
)

priority_combo.grid(
    row=0,
    column=5,
    padx=10
)

ttk.Button(
    subject_frame,
    text="ADD SUBJECT",
    command=add_subject
).grid(
    row=0,
    column=6,
    padx=15
)


# Subject table
subject_tree_frame = ttk.Frame(
    planner_tab
)

subject_tree_frame.pack(
    fill="both",
    expand=True,
    padx=25,
    pady=5
)

columns = (
    "name",
    "difficulty",
    "priority",
    "score"
)

subject_tree = ttk.Treeview(
    subject_tree_frame,
    columns=columns,
    show="headings",
    height=8
)

subject_tree.heading(
    "name",
    text="Subject"
)

subject_tree.heading(
    "difficulty",
    text="Difficulty"
)

subject_tree.heading(
    "priority",
    text="Priority"
)

subject_tree.heading(
    "score",
    text="Score"
)

subject_tree.column(
    "name",
    width=350
)

subject_tree.column(
    "difficulty",
    width=150,
    anchor="center"
)

subject_tree.column(
    "priority",
    width=150,
    anchor="center"
)

subject_tree.column(
    "score",
    width=100,
    anchor="center"
)

subject_tree.pack(
    side="left",
    fill="both",
    expand=True
)


subject_scrollbar = ttk.Scrollbar(
    subject_tree_frame,
    orient="vertical",
    command=subject_tree.yview
)

subject_scrollbar.pack(
    side="right",
    fill="y"
)

subject_tree.configure(
    yscrollcommand=subject_scrollbar.set
)


# Planner buttons
planner_buttons = ttk.Frame(
    planner_tab
)

planner_buttons.pack(
    pady=15
)

ttk.Button(
    planner_buttons,
    text="GENERATE STUDY PLAN",
    command=generate_plan
).pack(
    side="left",
    padx=5
)

ttk.Button(
    planner_buttons,
    text="REMOVE SUBJECT",
    command=remove_subject
).pack(
    side="left",
    padx=5
)

ttk.Button(
    planner_buttons,
    text="RESET SUBJECTS",
    command=reset_subjects
).pack(
    side="left",
    padx=5
)


# ============================================================
# TIMER TAB
# ============================================================

ttk.Label(
    timer_tab,
    text="Study Timer",
    style="Title.TLabel"
).pack(pady=25)

ttk.Label(
    timer_tab,
    textvariable=timer_subject_var,
    style="Heading.TLabel"
).pack(pady=10)

ttk.Label(
    timer_tab,
    textvariable=timer_display_var,
    style="BigTimer.TLabel"
).pack(pady=30)


timer_buttons = ttk.Frame(
    timer_tab
)

timer_buttons.pack(
    pady=10
)

ttk.Button(
    timer_buttons,
    text="▶ START",
    command=start_timer
).pack(
    side="left",
    padx=5
)

ttk.Button(
    timer_buttons,
    text="⏸ PAUSE",
    command=pause_timer
).pack(
    side="left",
    padx=5
)

ttk.Button(
    timer_buttons,
    text="🔄 RESET",
    command=reset_timer
).pack(
    side="left",
    padx=5
)

ttk.Button(
    timer_buttons,
    text="✓ COMPLETE",
    command=manually_complete_timer
).pack(
    side="left",
    padx=5
)


ttk.Label(
    timer_tab,
    text=(
        "Select a session from your generated study plan "
        "to start the timer."
    )
).pack(
    pady=25
)


# ============================================================
# INITIAL DATA
# ============================================================

refresh_subject_list()
update_dashboard()


# ============================================================
# WINDOW CLOSE
# ============================================================

def close_application():

    global timer_running
    global timer_job

    timer_running = False

    if timer_job is not None:

        try:
            root.after_cancel(timer_job)
        except:
            pass

    conn.commit()
    conn.close()

    root.destroy()


root.protocol(
    "WM_DELETE_WINDOW",
    close_application
)


# ============================================================
# START APPLICATION
# ============================================================

root.mainloop()
