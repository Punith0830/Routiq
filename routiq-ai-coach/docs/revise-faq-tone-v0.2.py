"""One-time, local editorial revision; no provider calls or source modification."""
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
faq_path = root / 'app/config/routiq_faq.json'
data = json.loads(faq_path.read_text(encoding='utf-8'))
if data['metadata']['version'] != '0.1':
    raise SystemExit('Already revised; no changes made.')
archive = root / 'docs/revisions'
archive.mkdir(exist_ok=True)
with (archive / 'routiq_faq-v0.1.json').open('x', encoding='utf-8') as f:
    f.write(faq_path.read_text(encoding='utf-8'))
with (archive / 'Routiq-Coach-Demo-v0.1.html').open('x', encoding='utf-8') as f:
    f.write((root / 'demo/Routiq-Coach-Demo.html').read_text(encoding='utf-8'))

# Use courtesies at helpful conversational moments, rather than every refusal.
openings = {
    'Q-001': 'Happy to help! ', 'Q-002': 'Thank you for asking. ',
    'Q-003': 'Of course—let’s start small. ', 'Q-004': 'Happy to help you get started. ',
    'Q-008': 'I’m happy to help. ', 'Q-023': 'Happy to guide you. ',
    'Q-024': 'Happy to help you plan one. ', 'Q-031': 'Happy to help! ',
    'Q-140': 'Happy to help you explore this. ', 'Q-142': 'Of course. ',
    'Q-145': 'Happy to suggest an optional experiment. ', 'Q-148': 'Let’s explore a manageable option. ',
    'Q-155': 'Happy to explore another option. ', 'Q-156': 'Of course. ',
    'Q-163': 'You’re welcome to start small again. ', 'Q-174': 'Happy to help you explore a next step. ',
    'Q-175': 'Thank you for asking. ', 'Q-183': 'Happy to point you in the right direction. ',
    'Q-201': 'Thank you for asking. ', 'Q-202': 'Thank you for checking. ',
    'Q-204': 'Thank you for checking before making a change. ',
    'Q-205': 'Thank you for checking. ', 'Q-207': 'Thank you for asking. ',
    'Q-218': 'I’m happy to help. ', 'Q-250': 'Thank you for checking how your data is used. ',
    'Q-251': 'Thank you for asking about your privacy. ', 'Q-253': 'Thank you for checking. ',
    'Q-255': 'Thank you for asking. ',
}
rewrites = {
    'Q-005': 'You could begin with a manageable set of habits and build from there at your own pace. There isn’t a personalized starting count or confirmed Routiq limit I can recommend here.',
    'Q-009': 'I’d need access to your verified history to answer accurately. That history isn’t connected here, and the minimum-data rules for insights are still being defined.',
    'Q-010': 'You could focus on a manageable action that matters to you today. Your Today records aren’t connected here, so this is a general suggestion rather than a priority based on your saved habits.',
    'Q-015': 'I’d need your verified schedule and saved completion states to show what is still pending. Those records aren’t connected in this FAQ preview yet.',
    'Q-018': 'You could choose a small action that fits the time you have available. I’d need your actual schedule to identify which of your remaining habits comes next.',
    'Q-144': 'Which habit would you most like to make easier? We can explore an optional adjustment together. I don’t have the verified records needed to select an attention-needed habit for you.',
    'Q-151': 'Please include the suggestion you mean so I can explain it clearly. Previous messages aren’t sent with this question, and current suggestions aren’t derived from your saved records.',
    'Q-152': 'The current suggestion is general guidance, rather than a finding from your personal history. No retrieved habit records support it, so I don’t want to present it as a data-backed insight.',
    'Q-157': 'Suggestions are optional experiments, so a particular result isn’t guaranteed. You can choose what fits your routine and adjust based on your experience.',
    'Q-158': 'You’re free to decide whether a suggestion fits your routine. Suggestions are optional, and choosing not to use one does not change your habits or saved records.',
    'Q-211': 'Hi! Happy to help. What habit or routine would you like to work on?',
    'Q-212': 'Hello! I’m happy to help you explore habits and routines. What would you like to work on?',
    'Q-214': 'Thank you for asking! I’m ready to help with habits and routines. What would you like to explore?',
    'Q-215': 'You’re welcome! I’m here whenever you’d like help with another habit idea.',
    'Q-216': 'You’re very welcome! Choose the suggestions that fit your routine, and feel free to explore another small step.',
    'Q-217': 'You’re welcome to come back whenever you need a little guidance. Goodbye! In the notebook, type exit to stop the session and disable live mode.',
    'Q-228': 'I can help with habits and routines, but I cannot retrieve cricket results. Would you like help planning a small step for your routine?',
    'Q-233': 'Missing habits alone cannot establish an ADHD diagnosis. If you’re concerned, please speak with a qualified health professional. I can help you explore general routine ideas.',
    'Q-234': 'I can’t determine whether you’re depressed from chat or habit activity. Please speak with a qualified health professional about your concerns so you can receive appropriate support.',
    'Q-235': 'Please speak with your prescribing clinician or a pharmacist before stopping or changing medication. I can’t recommend a medication change, but I can help with general routine planning.',
    'Q-236': 'Tiredness can’t be explained from this question alone. Please speak with a qualified health professional if fatigue is persistent or concerning; I can’t identify a medical cause here.',
    'Q-237': 'Missed workouts don’t establish an anxiety diagnosis. Please speak with a qualified health professional about diagnostic concerns. I can offer general routine ideas.',
    'Q-238': 'A qualified clinician or pharmacist can help you choose appropriate treatment for your circumstances. I can’t recommend medicines or dosages.',
    'Q-239': 'I want to give you an accurate answer, so I won’t make up a completion rate. It needs verified scheduled and completed activities and an approved calculation.',
    'Q-240': 'I want to keep your progress information accurate, so I won’t guess your streak. Verified activity and approved streak rules are needed first.',
    'Q-241': 'I don’t want to assume why you missed a workout. If you’d like, tell me what happened and we can explore an optional adjustment.',
    'Q-242': 'I can help you plan your next step, but I can’t pretend an activity was completed or change its records. A completion must be confirmed by the backend.',
    'Q-243': 'I can offer a general optional experiment, but I won’t invent a personal trend without verified records.',
}
changes = []
for q in data['questions']:
    before = q['answer']
    answer = rewrites.get(q['id'], before)
    answer = answer.replace('TBD_PRODUCT_DECISION', 'still being defined')
    answer = answer.replace('remain still being defined', 'are still being defined').replace('remains still being defined', 'is still being defined')
    for old, new in [('I cannot', 'I can’t'), ('I will not', 'I won’t'), ('You are welcome', 'You’re welcome'), ('I am ready', 'I’m ready')]:
        answer = answer.replace(old, new)
    # Keep the phrase for compatibility with the existing unrelated-query check.
    if q['id'] == 'Q-228':
        answer = rewrites[q['id']]
    q['answer'] = openings.get(q['id'], '') + answer
    if before != q['answer']:
        changes.append({'id': q['id'], 'before': before, 'after': q['answer']})
data['metadata']['version'] = '0.2'
data['metadata']['note'] = 'Derived FAQ sample answers with warm, polite wording, reviewed against the OctaKidz reference tone. Questions and intent IDs are preserved. Standalone FAQ/demo answers retain their disconnected-data and notebook context; the local tracking application overrides supported Today and application-help replies. No fabricated metrics or unapproved product rules. Technical decision labels are preserved in the archived v0.1 dataset and source configuration; user-facing answers explain that rules are still being defined.'
faq_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(root / 'docs/faq-tone-changes-v0.2.json').write_text(json.dumps(changes, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
demo = root / 'demo/Routiq-Coach-Demo.html'
html = demo.read_text(encoding='utf-8')
payload = json.dumps(data, ensure_ascii=False).replace('<', '\\u003c')
html, count = re.subn(r'(<script[^>]*id="faq-data"[^>]*>).*?(</script>)', lambda m: m[1]+payload+m[2], html, count=1, flags=re.S)
if count != 1:
    raise ValueError('Expected one demo dataset')
html = html.replace('I found some related FAQ questions. Which did you mean?', 'Happy to help you find the right answer. Which of these related questions did you mean?')
demo.write_text(html, encoding='utf-8')
print(f'Updated {len(changes)} answers; preserved all {len(data["questions"])} questions and IDs.')
