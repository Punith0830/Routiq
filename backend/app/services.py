from datetime import datetime, timezone, date, timedelta
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from contextlib import contextmanager
import sqlite3

from fastapi import HTTPException

from app.schemas import HabitInput


class HabitService:
    def __init__(self, path: Path, clock=None):
        self.path = path
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    @contextmanager
    def connection(self):
        with sqlite3.connect(self.path) as db:
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA foreign_keys = ON")
            yield db

    def zone(self, requested: str) -> str:
        try:
            ZoneInfo(requested)
        except (ZoneInfoNotFoundError, ValueError):
            raise HTTPException(422, "Choose a valid local timezone.") from None
        with self.connection() as db:
            db.execute("INSERT OR IGNORE INTO app_metadata VALUES ('timezone', ?)", (requested,))
            stored = db.execute("SELECT value FROM app_metadata WHERE key='timezone'").fetchone()[0]
        # Travel does not silently reinterpret saved activity dates.
        return stored

    def today(self, zone: str) -> date:
        return self.clock().astimezone(ZoneInfo(zone)).date()

    def overview(self, zone: str):
        today = self.today(zone)
        with self.connection() as db:
            rows = db.execute("SELECT h.*, EXISTS(SELECT 1 FROM completions c WHERE c.habit_id=h.id AND c.day=?) AS completed FROM habits h WHERE h.start_date <= ? ORDER BY h.created_at, h.id", (today.isoformat(), today.isoformat())).fetchall()
            activity = db.execute("SELECT c.day, COUNT(*) AS completed FROM completions c JOIN habits h ON h.id=c.habit_id WHERE c.day BETWEEN ? AND ? AND c.day >= h.start_date GROUP BY c.day", ((today - timedelta(days=6)).isoformat(), today.isoformat())).fetchall()
        habits = [dict(row) for row in rows]
        completed = sum(bool(h['completed']) for h in habits)
        total = len(habits)
        counts = {row['day']: row['completed'] for row in activity}
        days = [today - timedelta(days=offset) for offset in range(6, -1, -1)]
        return {"today": today, "timezone": zone, "habits": habits,
                "completed": completed, "total": total, "remaining": total - completed,
                "completion_percentage": round(completed / total * 100, 1) if total else None,
                "recent_days": [{"day": day, "completed": counts.get(day.isoformat(), 0)} for day in days]}

    def create(self, payload: HabitInput, zone: str):
        now = self.clock().isoformat()
        habit_id = str(uuid4())
        today = self.today(zone).isoformat()
        with self.connection() as db:
            db.execute("INSERT INTO habits (id,name,description,created_at,start_date,reason,small_action,cue) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (habit_id, payload.name, payload.description, now, today,payload.reason,payload.small_action,payload.cue))
        return {**payload.model_dump(), "id": habit_id, "created_at": now, "start_date": today, "completed": False}

    def update(self, habit_id: str, payload: HabitInput, zone: str):
        with self.connection() as db:
            if not db.execute("SELECT 1 FROM habits WHERE id=?", (habit_id,)).fetchone():
                raise HTTPException(404, "Habit not found.")
            db.execute("UPDATE habits SET name=?, description=?,reason=?,small_action=?,cue=? WHERE id=?", (payload.name, payload.description,payload.reason,payload.small_action,payload.cue, habit_id))
        return next(h for h in self.overview(zone)['habits'] if h['id'] == habit_id)

    def complete(self, habit_id: str, day: date, completed: bool, zone: str):
        with self.connection() as db:
            habit = db.execute("SELECT start_date FROM habits WHERE id=?", (habit_id,)).fetchone()
            if not habit:
                raise HTTPException(404, "Habit not found.")
            if day != self.today(zone) or day.isoformat() < habit['start_date']:
                raise HTTPException(422, "This initial version supports completion changes for today only. Refresh Today and try again.")
            if completed:
                db.execute("INSERT OR IGNORE INTO completions VALUES (?, ?)", (habit_id, day.isoformat()))
            else:
                db.execute("DELETE FROM completions WHERE habit_id=? AND day=?", (habit_id, day.isoformat()))
        return self.overview(zone)

    def progress(self, zone: str):
        today = self.today(zone)
        start = (today - timedelta(days=29)).isoformat()
        with self.connection() as db:
            rows = db.execute("SELECT c.habit_id, h.name AS habit_name, c.day FROM completions c JOIN habits h ON h.id=c.habit_id WHERE c.day BETWEEN ? AND ? ORDER BY c.day DESC, h.name", (start, today.isoformat())).fetchall()
        return {"today": today, "recorded_completions": len(rows), "history": [dict(row) for row in rows]}
