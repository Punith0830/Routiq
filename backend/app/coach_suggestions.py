"""Stateless, curated follow-ups. Questions only; no history or habit access."""
import re
from app.schemas import ChatReply, Choice

GROUPS = {
    'today': ['Q-014','Q-015','Q-077','Q-083','Q-011','Q-017','Q-021','Q-055','Q-078','Q-082','Q-084','Q-012'],
    'reading': ['Q-140','Q-142','Q-145','Q-147','Q-024','Q-044','Q-148','Q-031','Q-028','Q-029'],
    'workout': ['Q-143','Q-142','Q-145','Q-147','Q-148','Q-031','Q-139','Q-141'],
    'setup': ['Q-023','Q-026','Q-028','Q-029','Q-043','Q-025','Q-046','Q-189','Q-188','Q-024','Q-044'],
    'privacy': ['Q-250','Q-251','Q-252','Q-253','Q-254','Q-188','Q-023','Q-031'],
    'general': ['Q-031','Q-142','Q-145','Q-147','Q-148','Q-139','Q-141','Q-140','Q-143','Q-023'],
}


def related_questions(message: str, reply: ChatReply, questions: list[dict]) -> list[Choice]:
    normalized = lambda s: ' '.join(re.sub(r'[^a-z0-9 ]', ' ', s.lower().replace('’', "'")).split())
    text = normalized(message)
    by_id = {q['id']: q for q in questions}
    matched = by_id.get(reply.question_id) or next((q for q in questions if normalized(q['question']) == text), None)
    sensitive = re.search(r'sk-[\w-]{8,}|api.?key|password|ignore.{0,35}instructions|reveal.{0,35}prompt', message, re.I)
    topic = 'general'
    if not sensitive:
        if reply.source == 'verified_local_data': topic = 'today'
        elif re.search(r'\b(read|reading|book|books)\b', text): topic = 'reading'
        elif re.search(r'\b(workout|exercise|fitness)\b', text): topic = 'workout'
        elif re.search(r'\b(privacy|data|conversation|conversations|chat history|export|access|opt out)\b', text): topic = 'privacy'
        elif re.search(r'\b(today|pending|complete|completed|remaining|left)\b', text): topic = 'today'
        elif (not matched or matched['id'] != 'Q-031') and re.search(r'\b(create|add|edit|rename|description|name|find)\b', text): topic = 'setup'
        elif reply.source == 'clarification':
            choice_ids = {q.id for q in reply.choices}
            topic = next((t for t in ['today','setup','privacy'] if choice_ids.intersection(GROUPS[t])), 'general')
    # Fixed eligible pools keep unsupported features from appearing as new promises.
    ids = [id for id in GROUPS[topic] if id != (matched['id'] if matched else None) and normalized(by_id[id]['question']) != text]
    preferred = {q.id for q in reply.choices} if not sensitive else set()
    ids.sort(key=lambda id: id not in preferred)
    return [Choice(id=id, question=by_id[id]['question']) for id in ids[:4]]
