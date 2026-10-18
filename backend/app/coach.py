"""Deterministic local Coach. No provider calls, chat writes or arbitrary tools."""
import json
import re
from pathlib import Path
from app.schemas import ChatReply, Choice


def normalize(text):
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", text.lower().replace('’', "'")).split())


class FAQCoach:
    def __init__(self, path: Path):
        data = json.loads(path.read_text(encoding="utf-8"))
        self.questions = data['questions']
        if len(self.questions) != data['total_questions'] or len({q['id'] for q in self.questions}) != len(self.questions):
            raise ValueError("Invalid FAQ coverage")
        if any(not q['question'].strip() or not q['answer'].strip() for q in self.questions):
            raise ValueError("Blank FAQ entry")
        self.by_text = {normalize(q['question']): q for q in self.questions}
        self.stop = set('a an the i my me you your can could would should do does how what which is are am was were it this that to for of on in and with please show tell about'.split())

    def respond(self, message: str, habits, zone: str):
        return self.with_suggestions(message, self._respond(message, habits, zone))

    def with_suggestions(self, message: str, reply: ChatReply):
        from app.coach_suggestions import related_questions
        return reply.model_copy(update={'suggestions': related_questions(message, reply, self.questions)})

    def _respond(self, message: str, habits, zone: str):
        # Do not retain or echo user input in service logs or persistent storage.
        if re.search(r"sk-[\w-]{8,}|api.?key|password|ignore.{0,35}instructions|reveal.{0,35}prompt", message, re.I):
            return ChatReply(message="Please keep credentials private. I cannot reveal private instructions or invent activity, but I’m happy to help with a Routiq habit question.", source="scope_limit")
        text = normalize(message)
        q = self.by_text.get(text)
        from app.preferences import feature_help
        help_text = feature_help(message)
        if help_text:
            return ChatReply(message=help_text, source='application_help', question_id=q['id'] if q else None)
        aliases = {'how am i doing today', 'today progress', 'what habits are left today', 'remaining habits', 'show today habits'}
        today_ids = {'Q-011','Q-012','Q-013','Q-014','Q-015','Q-016','Q-017','Q-021','Q-055','Q-075','Q-077','Q-078','Q-081','Q-082','Q-083','Q-084'}
        if text in aliases or q and q['id'] in today_ids:
            overview = habits.overview(zone)
            if not overview['habits']:
                reply = "Happy to help you get started! You have no habits yet. Choose Add habit on Today and begin with a manageable daily action."
            else:
                pending = [h['name'] for h in overview['habits'] if not h['completed']]
                done = [h['name'] for h in overview['habits'] if h['completed']]
                reply = f"Happy to help! For {overview['today'].isoformat()}, you have recorded {overview['completed']} of {overview['total']} daily habits complete."
                if q and q['id'] in {'Q-014','Q-055'}:
                    reply += " Completed: " + (', '.join(done) if done else 'none yet') + "."
                else:
                    reply += " Remaining: " + (', '.join(pending) if pending else 'none') + "."
            return ChatReply(message=reply, source="verified_local_data", question_id=q['id'] if q else None)
        help_map = {
            'how do i create a habit': 'Happy to help! On Today, choose Add habit. Enter a name and optional description, then Save habit. Habits in this initial version repeat daily.',
            'can i add a reading habit': 'Of course—you can add one from Today. Choose Add habit and name it Reading. Add an optional description and save. Chat itself does not create habits.',
            'where do i see my habits': 'Open Today to see your daily habits. Progress shows your saved completion history.',
            'how do i check off a habit': 'Use the Mark complete button beside a habit on Today. Use Undo completion to reverse today’s check-in.',
            'how does routiq work': 'Add a daily habit, record completion on Today and review saved activity in Progress. I can answer prepared habit questions and summarize your saved Today records.',
            'what can i ask you': 'Ask about today’s habits, remaining habits or daily progress. I also offer prepared habit-building answers. I cannot calculate streaks, change habits from chat or call live AI in this version.',
            'can i mark this complete': 'Use Mark complete beside the habit on Today. Chat does not change habit records.',
            'can i undo completion': 'Use Undo completion beside the completed habit on Today.',
            'how do i edit a habit': 'Choose Edit beside a habit on Today. Update its name or description and save. Its recorded activity stays attached to the same habit.',
            'where is the progress dashboard': 'Happy to guide you! Open Today for daily metrics and a seven-day check-in chart. Open Progress to see saved completion activity for the last 30 days.',
            'what habit data can the ai see': 'Thank you for checking how your data is used. This local AI Assist reads today’s habit names and saved completion states when answering a supported Today question. It does not send them to OpenAI. Live AI is off.',
            'does routiq store my conversations': 'Thank you for asking about your privacy. Chat messages stay temporarily in this browser tab. They are not written to the backend database and clear on reload.',
            'can i delete my chat history': 'Reload the page to clear the displayed conversation. Chat is not persisted by this initial application.',
            'who can access my habit records': 'This is a single-user local application. Records are in its SQLite file on this computer. Anyone with access to that file or the running local service may access them; account isolation is not implemented.',
            'can i opt out of ai recommendations': 'Live AI is off in this initial application. You can use habit tracking without opening AI Assist.',
            'can i export my habit history': 'Thank you for asking. Export is not included in this initial release, but you can review saved completion activity in Progress.'
        }
        if text in help_map:
            return ChatReply(message=help_map[text], source="application_help", question_id=q['id'] if q else None)
        if q:
            if q['id'] != 'Q-031' and q['intent_id'] in {'APP_HELP','HABIT_CREATION_HELP','HABIT_MANAGEMENT','REMINDERS','HABIT_SCHEDULING'}:
                return ChatReply(message="Happy to explain what’s available. This version has Today, Add/Edit habit, Progress, Achievements, Settings and AI Assist. Foreground reminders are available in Settings. Custom schedules, archive and accounts are not included. You can use Add habit or Edit on Today to manage a name and description.", source="application_help", question_id=q['id'])
            if 'notebook' in q['answer'].lower() or '/live' in q['answer']:
                return ChatReply(message="Thank you for asking. This local application uses prepared FAQ answers and can summarize saved Today records. Live AI and saved conversations are off. You’re welcome to ask about today’s habits or explore a small habit idea.", source="scope_limit", question_id=q['id'])
            if q['intent_id'] in {'DAILY_PROGRESS','WEEKLY_PROGRESS','MONTHLY_PROGRESS','PERIOD_COMPARISON','STREAKS','PATTERN_ANALYSIS','COMPLETION_STATUS','TODAY_OVERVIEW','MISSED_HABITS','HIGH_CONSISTENCY','RETURNING_USER','RECOMMENDATION_EXPLANATION'}:
                return ChatReply(message="Thank you for asking. That analysis isn’t available in this initial version yet. I can summarize today’s saved habits, or you can review recorded completion activity in Progress. Today’s completion percentage is available on Today; historical rates, streaks and missed-day interpretations still require approved rules.", source="scope_limit", question_id=q['id'])
            return ChatReply(message=q['answer'], source="prepared_faq", question_id=q['id'])
        tokens = set(text.split()) - self.stop
        ranked = []
        for item in self.questions:
            qt = set(normalize(item['question']).split()) - self.stop
            shared = len(tokens & qt)
            score = 2 * shared / (len(tokens) + len(qt)) if tokens or qt else 0
            if shared >= min(2, len(tokens)) and shared and score >= .35:
                ranked.append((score, item))
        ranked.sort(key=lambda x: (-x[0], x[1]['id']))
        choices = [Choice(id=item['id'], question=item['question']) for _, item in ranked[:3]]
        return ChatReply(message="Happy to help you find the right answer. Which related question did you mean?" if choices else "I’m happy to help with Routiq and habits. You’re welcome to ask about today’s progress or choose a sample question. This version uses prepared answers rather than live AI.", source="clarification" if choices else "scope_limit", choices=choices)
