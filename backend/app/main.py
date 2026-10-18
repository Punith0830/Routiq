from contextlib import asynccontextmanager
import os
from pathlib import Path
from datetime import date

from fastapi import FastAPI, Header, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.database import available, initialize
from app.services import HabitService
from app.coach import FAQCoach
from app.preferences import Preferences, VERSION, read_preferences, save_preferences, rewards
from app.schemas import HabitInput, Habit, Overview, Progress, ChatInput, ChatReply

MODULE_ROOT = Path(__file__).resolve().parents[1]


def create_app(database_path: Path | None = None, clock=None) -> FastAPI:
    selected = database_path or Path(os.environ.get("ROUTIQ_DATABASE_PATH", "data/routiq.sqlite3"))
    path = selected if selected.is_absolute() else MODULE_ROOT / selected
    service = HabitService(path, clock)
    coach = FAQCoach(MODULE_ROOT.parent / 'routiq-ai-coach/app/config/routiq_faq.json')

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        initialize(path)
        yield

    application = FastAPI(title="Routiq Tracker", version="0.1.0", lifespan=lifespan)
    application.add_middleware(TrustedHostMiddleware, allowed_hosts=['127.0.0.1','localhost','[::1]'])

    @application.middleware('http')
    async def local_origin(request: Request, call_next):
        origin = request.headers.get('origin')
        if origin and origin not in {'http://127.0.0.1:4200','http://localhost:4200','http://127.0.0.1:8001','http://localhost:8001'}:
            return JSONResponse(status_code=403, content={"detail":"Use the local Routiq application."})
        return await call_next(request)

    @application.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError):
        # Never return rejected chat/password content via Pydantic input fields.
        fields = ['.'.join(str(part) for part in e['loc']) for e in exc.errors()]
        return JSONResponse(status_code=422, content={"detail": "Check the submitted fields.", "fields": fields})

    @application.exception_handler(Exception)
    async def unexpected_error(_: Request, __: Exception):
        return JSONResponse(status_code=503, content={"detail": "The local service is unavailable. Try again.", "code": "SERVICE_UNAVAILABLE"})

    def local_zone(requested: str):
        return service.zone(requested)

    @application.get('/api/habits', response_model=Overview)
    def list_habits(x_routiq_timezone: str = Header()):
        return service.overview(local_zone(x_routiq_timezone))

    @application.post('/api/habits', response_model=Habit, status_code=201)
    def add_habit(body: HabitInput, x_routiq_timezone: str = Header()):
        return service.create(body, local_zone(x_routiq_timezone))

    @application.patch('/api/habits/{habit_id}', response_model=Habit)
    def edit_habit(habit_id: str, body: HabitInput, x_routiq_timezone: str = Header()):
        return service.update(habit_id, body, local_zone(x_routiq_timezone))

    @application.put('/api/habits/{habit_id}/completions/{day}', response_model=Overview)
    def complete(habit_id: str, day: date, x_routiq_timezone: str = Header()):
        return service.complete(habit_id, day, True, local_zone(x_routiq_timezone))

    @application.delete('/api/habits/{habit_id}/completions/{day}', response_model=Overview)
    def undo(habit_id: str, day: date, x_routiq_timezone: str = Header()):
        return service.complete(habit_id, day, False, local_zone(x_routiq_timezone))

    @application.get('/api/progress', response_model=Progress)
    def progress(x_routiq_timezone: str = Header()):
        return service.progress(local_zone(x_routiq_timezone))

    @application.get('/api/settings', response_model=Preferences)
    def settings():
        return read_preferences(service)

    @application.put('/api/settings', response_model=Preferences)
    def update_settings(body: Preferences):
        return save_preferences(service, body)

    @application.get('/api/rewards')
    def achievements(x_routiq_timezone: str = Header()):
        return rewards(service, local_zone(x_routiq_timezone))

    @application.get('/api/version')
    def application_version():
        return {'version': VERSION, 'reminder_delivery': 'in_app_while_open', 'live_ai': False}

    @application.post('/api/assist/chat', response_model=ChatReply)
    @application.post('/api/coach/chat', response_model=ChatReply)
    def chat(body: ChatInput, x_routiq_timezone: str = Header()):
        return coach.respond(body.message, service, local_zone(x_routiq_timezone))

    @application.get("/health")
    def health():
        return {"status": "ok"}

    @application.get("/api/ready")
    def ready():
        if not available(path):
            return JSONResponse(status_code=503, content={"status": "unavailable", "code": "STORAGE_UNAVAILABLE"})
        return {"status": "ready", "phase": "initial_tracker", "tracking_available": True, "coach_mode": "local_faq"}

    return application


app = create_app()
