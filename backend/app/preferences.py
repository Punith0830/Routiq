"""Device-local preferences and rewards; no remote account or scheduling worker."""
import json
from datetime import time
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path
from typing import Literal
import tomllib
import base64
import binascii

from fastapi import HTTPException
from pydantic import Field, field_validator, model_validator
from app.schemas import StrictModel

try:
    VERSION = version("routiq-tracker")
except PackageNotFoundError:
    VERSION = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text())["project"]["version"]

class Reminder(StrictModel):
    enabled: bool = Field(default=False, strict=True)
    time: str = "09:00"

    @field_validator("time")
    @classmethod
    def valid_time(cls, value):
        if len(value) != 5 or value[2] != ":" or not value.replace(":", "").isascii() or not value.replace(":", "").isdigit():
            raise ValueError("Use HH:MM.")
        time.fromisoformat(value)
        return value

class Preferences(StrictModel):
    display_name: str = Field(default="", max_length=80)
    avatar: Literal["initial", "leaf", "sun", "spark"] = "initial"
    avatar_image: str = Field(default="", max_length=200000)
    theme: Literal["system", "light", "dark"] = "system"
    reduced_motion: bool = Field(default=False, strict=True)
    celebrations: bool = Field(default=True, strict=True)
    gamification: bool = Field(default=True, strict=True)
    notifications: bool = Field(default=False, strict=True)
    quiet_hours: bool = Field(default=False, strict=True)
    quiet_start: str = "22:00"
    quiet_end: str = "08:00"
    reminders: dict[str, Reminder] = Field(default_factory=dict, max_length=100)

    @field_validator("avatar_image")
    @classmethod
    def valid_photo(cls, value):
        if not value:
            return value
        prefix = "data:image/jpeg;base64,"
        if not value.startswith(prefix):
            raise ValueError("Choose a JPEG profile photo.")
        try:
            image = base64.b64decode(value[len(prefix):], validate=True)
        except (ValueError, binascii.Error):
            raise ValueError("Invalid profile photo.")
        if len(image) < 4 or not image.startswith(b"\xff\xd8\xff") or not image.endswith(b"\xff\xd9"):
            raise ValueError("Invalid JPEG profile photo.")
        return value

    @field_validator("display_name", mode="before")
    @classmethod
    def trim_name(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("quiet_start", "quiet_end")
    @classmethod
    def validate_time(cls, value):
        return Reminder.valid_time(value)

    @model_validator(mode="after")
    def quiet_bounds(self):
        if self.quiet_hours and self.quiet_start == self.quiet_end:
            raise ValueError("Choose different quiet-hours start and end times.")
        return self

def read_preferences(service):
    with service.connection() as db:
        row = db.execute("SELECT value FROM app_metadata WHERE key='preferences'").fetchone()
    return Preferences.model_validate_json(row["value"]) if row else Preferences()

def save_preferences(service, body):
    with service.connection() as db:
        habit_ids = {row["id"] for row in db.execute("SELECT id FROM habits")}
        if set(body.reminders) - habit_ids:
            raise HTTPException(422, "Select an existing habit for reminders.")
        db.execute("INSERT INTO app_metadata(key,value) VALUES ('preferences',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                   (body.model_dump_json(),))
    return body

def rewards(service, zone):
    today = service.today(zone).isoformat()
    with service.connection() as db:
        count = db.execute("SELECT count(*) FROM completions c JOIN habits h ON h.id=c.habit_id WHERE c.day>=h.start_date AND c.day<=?", (today,)).fetchone()[0]
    return {"recorded": count, "points": count * 10, "milestones": [
        {"target": target, "progress": min(count, target), "earned": count >= target}
        for target in (1, 5, 20)
    ]}

def feature_help(message):
    """Describe only implemented features, never claim background delivery or live AI."""
    from app.coach import normalize
    text = normalize(message)
    if any(word in text.split() for word in ("points", "point", "rewards", "reward", "milestones", "gamification", "badges")):
        return "Each eligible recorded habit earns 10 points per day. Undo recalculates points and milestone progress. Milestones are at 1, 5 and 20 check-ins. Rewards are optional in Settings; no leaderboard or streak penalty."
    if 'quiet hours' in text or any(word in text.split() for word in ("reminder", "reminders", "notification", "notifications", "snooze")):
        return "Open Settings → Notifications to enable in-app reminders and choose a time for a habit. Reminders work while Routiq is open; closed or suspended tabs cannot promise delivery. You can set quiet hours, dismiss a reminder for today or snooze it for 10 minutes. Completed habits are suppressed."
    if any(word in text.split() for word in ("theme", "themes", "settings", "profile", "version", "animations", "synced")):
        return "Settings contains your device-local display name and uploaded profile photo, System/Light/Dark appearance, reduced motion, optional rewards, in-app reminders and the application version. There is no account or cross-device sync."
    return None

