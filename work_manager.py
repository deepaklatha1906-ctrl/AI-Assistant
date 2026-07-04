# work_manager.py - 100% local work management module
import json
import os
import time
from pathlib import Path
from datetime import datetime, timedelta

DATA_DIR = Path("data")
TASKS_FILE = DATA_DIR / "tasks.json"
TIMER_FILE = DATA_DIR / "focus_timer.json"
NOTES_DIR = DATA_DIR / "notes"

def _ensure_dirs():
    DATA_DIR.mkdir(exist_ok=True)
    NOTES_DIR.mkdir(exist_ok=True)

def _load_json(filepath):
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return [] if "tasks" in str(filepath) else {}

def _save_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)

# 📋 TASK MANAGER
def add_task(task_text, priority="medium"):
    _ensure_dirs()
    tasks = _load_json(TASKS_FILE)
    tasks.append({
        "id": len(tasks) + 1,
        "text": task_text.strip(),
        "priority": priority.lower(),
        "created": datetime.now().isoformat(),
        "completed": False
    })
    _save_json(TASKS_FILE, tasks)
    return f"✅ Task added: '{task_text}' ({priority} priority)"

def list_tasks(status="pending"):
    tasks = _load_json(TASKS_FILE)
    filtered = [t for t in tasks if (status == "completed") == t["completed"]]
    if not filtered:
        return "📋 No tasks found."
    lines = [f"{'✅' if t['completed'] else '⏳'} [#{t['id']}] [{t['priority'].upper()}] {t['text']}" for t in filtered]
    return "📋 Your tasks:\n" + "\n".join(lines)

def complete_task(task_id):
    tasks = _load_json(TASKS_FILE)
    for t in tasks:
        if str(t["id"]) == str(task_id):
            t["completed"] = True
            _save_json(TASKS_FILE, tasks)
            return f"✅ Marked task #{task_id} as complete."
    return f"❌ Task #{task_id} not found."

# 📝 QUICK NOTES
def capture_note(content, tags=None):
    _ensure_dirs()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tags_str = "_".join(tags or ["untagged"])
    filename = NOTES_DIR / f"note_{timestamp}_{tags_str}.md"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"# {content}\n\n_Captured: {datetime.now().isoformat()}_\n_Tags: {', '.join(tags or [])}_\n")
    return f"📝 Note saved."

def search_notes(query):
    _ensure_dirs()
    matches = []
    for file in NOTES_DIR.glob("*.md"):
        if query.lower() in file.read_text(encoding='utf-8').lower():
            matches.append(file.stem)
    return f"🔍 Found {len(matches)} note(s): {', '.join(matches[:5])}" if matches else "📭 No matching notes."

# ⏱️ FOCUS TIMER
def start_focus(minutes=25):
    _ensure_dirs()
    end_time = datetime.now() + timedelta(minutes=minutes)
    _save_json(TIMER_FILE, {"start": datetime.now().isoformat(), "end": end_time.isoformat(), "minutes": minutes})
    return f"⏱️ Focus timer started for {minutes} mins."

def check_timer():
    _ensure_dirs()
    data = _load_json(TIMER_FILE)
    if not data:
        return "⏱️ No active timer."
    end = datetime.fromisoformat(data["end"])
    remaining = (end - datetime.now()).total_seconds() / 60
    if remaining <= 0:
        return "🎉 Focus session complete! Time for a break."
    return f"⏱️ {int(remaining)} minutes remaining."

# 🔍 FILE FINDER (Safe & Fast)
def find_files(query, file_type=None):
    results = []
    search_paths = [Path.home() / "Desktop", Path.home() / "Documents", Path.home() / "Downloads"]
    query = query.lower().strip()
    
    for base in search_paths:
        if not base.exists(): continue
        try:
            for file in base.rglob(f"*{query}*"):
                if file.is_file():
                    if not file_type or file.suffix.lower() == f".{file_type.lower()}":
                        results.append(str(file))
                        if len(results) >= 8: break  # Performance limit
            if len(results) >= 8: break
        except PermissionError:
            continue
            
    if not results:
        return "📭 No files found in Desktop/Documents/Downloads."
    return f"📁 Found {len(results)} file(s):\n" + "\n".join(results[:5])

# 📊 DAILY BRIEFING
def generate_briefing():
    tasks = list_tasks("pending")
    timer_status = check_timer()
    notes_count = len(list(NOTES_DIR.glob("*.md"))) if NOTES_DIR.exists() else 0
    return f"📊 DAILY BRIEFING\n{'='*20}\n📋 {tasks}\n\n⏱️ {timer_status}\n📝 {notes_count} notes captured."