"""Public assignment FAQ API; no database, habit writes or provider calls."""
import os
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.coach import FAQCoach, normalize
from app.schemas import ChatInput, ChatReply


def create_assignment_app(origins=None, hosts=None):
    origins = origins if origins is not None else [v.strip() for v in os.getenv('ALLOWED_ORIGINS', '').split(',') if v.strip()]
    for origin in origins:
        parsed = urlsplit(origin)
        if parsed.scheme not in {'http', 'https'} or not parsed.netloc or parsed.path or parsed.query or parsed.fragment or parsed.username:
            raise ValueError('ALLOWED_ORIGINS must contain exact origins without paths or trailing slashes.')
    hosts = hosts if hosts is not None else ['localhost', '127.0.0.1'] + ([os.environ['RENDER_EXTERNAL_HOSTNAME']] if os.getenv('RENDER_EXTERNAL_HOSTNAME') else [])
    coach = FAQCoach(Path(__file__).resolve().parents[2] / 'routiq-ai-coach/app/config/routiq_faq.json')
    app = FastAPI(title='Routiq Assignment FAQ', docs_url=None, redoc_url=None)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=hosts)

    @app.middleware('http')
    async def origin_boundary(request: Request, call_next):
        origin = request.headers.get('origin')
        if origin and origin not in origins:
            return JSONResponse(status_code=403, content={'detail': 'Origin is not allowed.'})
        return await call_next(request)

    # Outer CORS middleware handles OPTIONS and attaches headers to allowed errors.
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False,
                       allow_methods=['GET', 'POST'], allow_headers=['Content-Type'])

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        return JSONResponse(status_code=422, content={'detail': 'Enter a question of 1–4000 characters.'})

    @app.get('/health')
    def health():
        return {'status': 'ok', 'coach_mode': 'prepared_faq', 'habit_storage': 'browser_device', 'live_ai': False}

    @app.post('/api/assist/chat', response_model=ChatReply)
    @app.post('/api/coach/chat', response_model=ChatReply)
    def chat(body: ChatInput):
        def attach(reply):
            return coach.with_suggestions(body.message, reply)
        text = normalize(body.message)
        question = coach.by_text.get(text)
        today_ids = {'Q-011','Q-012','Q-013','Q-014','Q-015','Q-016','Q-017','Q-021','Q-055','Q-075','Q-077','Q-078','Q-081','Q-082','Q-083','Q-084'}
        if text in {'how am i doing today','today progress','what habits are left today','remaining habits','show today habits','what is still pending'} or question and question['id'] in today_ids:
            return attach(ChatReply(message='Your Today dashboard summarizes the test habits in this browser. This FAQ server cannot read your habit records.', source='scope_limit', question_id=question['id'] if question else None))
        privacy = {'what habit data can the ai see', 'who can access my habit records', 'does routiq store my conversations', 'can i delete my chat history'}
        if text in privacy:
            return attach(ChatReply(message='Habits and preferences stay in your browser on this device. Only unmatched custom questions may reach this prepared FAQ server; the application does not save conversations or call OpenAI. Reloading the page clears the displayed conversation. Please use sample information only.', source='application_help', question_id=question['id'] if question else None))
        if text in {'bye', 'goodbye', 'exit'}:
            return attach(ChatReply(message='Thank you for trying Routiq. You can return to Today or close this tab whenever you like.', source='application_help', question_id=question['id'] if question else None))
        return coach.respond(body.message, None, 'UTC')

    return app


app = create_assignment_app()
