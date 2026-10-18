# 📚 Smart Study Planner

A Python desktop application that creates personalized study schedules based on available study time, subject difficulty, priority, and user mood.

The project evolved from a simple command-line study planner into a GUI-based application with database storage, study tracking, a timer, dashboard, and analytics.

## ✨ Features

- Personalized study-plan generation
- Add and manage multiple subjects
- Subject difficulty levels
- Subject priority levels
- Mood-based study ordering
- Weighted study-time allocation
- Automatic break scheduling
- SQLite database for persistent data
- Built-in study countdown timer
- Start, pause, reset, and complete timer
- Study progress tracking
- Study streak tracking
- Daily and weekly statistics
- Study history
- Completion percentage
- CSV data export
- Input validation and error handling
- Handles limited study time and multiple subjects

## 🖥️ Application

The planner provides a graphical interface built with Tkinter.

### Dashboard
Shows study progress, completed sessions, study time, streaks, and weekly statistics.

### Study Planner
Creates a personalized schedule based on available time, subject difficulty, priority, and mood.

### Study Timer
Provides a countdown timer for planned study sessions and records completed sessions.

## 🛠️ Technologies Used

- Python
- Tkinter
- SQLite
- CSV
- Git / GitHub

No external Python packages are required.

## ⚙️ How the Planner Works

Subjects are given weights based on difficulty and priority.

### Difficulty

- Easy = 1
- Medium = 2
- Hard = 3

### Priority

- Low = 1
- Medium = 2
- High = 3

The subject score is calculated from its difficulty and priority.

Subjects with higher scores receive a larger share of the available study time.

The user's mood can also influence the order of the generated study plan.

## 🗄️ Database

SQLite is used to store:

- Subjects
- Difficulty
- Priority
- Subject scores
- Planned study sessions
- Completed sessions
- Study dates
- Planned study time

This allows study progress and history to remain available after restarting the application.

## ⏱️ Study Timer

The built-in timer supports:

- Start
- Pause
- Reset
- Complete session

Completed sessions are stored in the SQLite database.

## 📊 Progress Tracking

The application tracks:

- Completed study sessions
- Total completed study minutes
- Today's study time
- Weekly study time
- Completion percentage
- Current study streak
- Study history

## 📤 Data Export

Study data can be exported to CSV for further analysis or record keeping.

## ▶️ How to Run

Make sure Python is installed.

Run the application with:

```bash
python smart_study_planner.py
The project was developed progressively:
V1 → V2 → V3 → V4 → V5
The early version focused on basic study-plan generation.
Later versions introduced:
- Dynamic scheduling
- Graphical user interface
- SQLite database
- Progress tracking
- Study timer
- Dashboard
- Study streaks
- Weekly statistics
- CSV export
🔮 Future Improvements
- User accounts
- Custom study goals
- Subject-specific notes
- Notifications
- Dark mode
- Cloud synchronization
- More advanced scheduling algorithms
- Improved analytics

### Then do this

1. **Select** the existing text `Enter file contents here`.
2. **Paste** the README above.
3. Click **Commit changes...** in the top-right.
4. In the commit message, write:

```text
Add project README
