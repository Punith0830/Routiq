"""Conservative local-demo scope and output checks; not comprehensive NLU."""
import re
from dataclasses import dataclass

from app.schemas.chat import ChatRequest


class UnsafeCoachOutput(ValueError):
    """Safe type marker; never includes generated text."""


@dataclass(frozen=True)
class Route:
    intent: str
    message: str | None = None
    supported_message: str = ""
    limitation: str = ""


def classify(request: ChatRequest, config) -> Route:
    text = request.message.strip()
    lowered = text.lower()
    if request.conversation_id or request.context.habit_id:
        return Route("UNAVAILABLE_CONTEXT", "Habit ownership and saved conversations are not connected yet. Please ask a general habit question.")
    if re.search(r"sk-[\w-]{8,}|api.?key|system prompt|developer prompt|ignore.{0,35}instructions|invent.{0,30}(data|records|progress)", lowered):
        return Route("SAFETY_RESPONSE", "Please ask about habits or routines without credentials or requests to invent records or reveal private instructions.")
    if re.search(r"suicid|kill myself|self.harm", lowered):
        return Route("SAFETY_RESPONSE", "If you might hurt yourself or are in immediate danger, contact local emergency services or a trusted person now. Routiq cannot provide crisis care.")
    if re.search(r"diagnos|medicat|medical|depress|adhd|therap|symptom|dosage|disease", lowered):
        return Route("SAFETY_RESPONSE", "I can help with general routines, but cannot diagnose conditions or advise on treatment. Please consult a qualified health professional.")
    if re.search(r"skip|pause|denominator|timezone|time zone|day.boundary|archiv|delet|streak", lowered):
        return Route("UNRESOLVED_PRODUCT_RULE", "That Routiq product rule is still TBD_PRODUCT_DECISION. I cannot assume how it works.")
    if re.search(r"\b(create|edit|change|set|update|remove|complete|mark)\b.{0,25}\b(my|habit|reminder)\b", lowered) and not re.search(r"how|help|suggest|idea", lowered):
        return Route("ACTION_UNAVAILABLE", "I can discuss an optional habit experiment, but cannot change or complete habits or reminders.")
    # Honor supplied exact question-to-intent examples where data/tools are required.
    for question in config.sample_questions:
        if question.text.casefold().rstrip("?.!") == lowered.rstrip("?.!"):
            intent = next(i for i in config.intents if i.id == question.intent_id)
            if intent.required_tools:
                return Route(intent.id, "Your habit records are not connected, so I cannot calculate or explain your personal progress yet.")
    if re.search(r"my (progress|habits|week|month|consistency)|how (am i|was my)|completion|percent|missed|remaining|compare|better than|today.s habits", lowered) and not re.search(r"how (can|do|should) i|help me|tips|suggest|start", lowered):
        return Route("INSUFFICIENT_DATA", "Your habit records are not connected, so I cannot calculate your progress, explain misses or compare periods yet.")
    if lowered.rstrip("!?.") in {"hi", "hello", "hey", "thanks", "thank you"}:
        return Route("CASUAL_CONVERSATION", "Hi! I can help you explore habits and routines. What would you like to work on?")
    if re.search(r"how (is it going|am i doing)|how.s it going", lowered):
        return Route("CLARIFICATION", "Would you like general habit advice, help using Routiq, or a progress summary? Personal progress data is not connected yet.")
    parts = re.split(r"\s+and\s+|[?;]", text, flags=re.I)
    supported = [p.strip() for p in parts if re.search(r"habit|routine|routiq|reminder", p, re.I)]
    external = bool(re.search(r"weather|bitcoin|cricket|stock price|news|president", lowered))
    if not supported:
        return Route("OUT_OF_SCOPE", "I’m your Routiq AI Coach. I can help with habits, routines and Routiq, but this question is outside that scope.")
    return Route("GENERAL_HABIT_COACHING", supported_message=". ".join(supported),
                 limitation="I cannot provide real-time external information." if external else "")


def validate_message(message: str, secret: str = "") -> str:
    if not isinstance(message, str) or not message.strip() or len(message) > 3000:
        raise UnsafeCoachOutput("Invalid coach output")
    # No verified records exist in this extension. Reject personal metric/action
    # claims and numerical output conservatively, including numeric suggestions.
    if (secret and secret in message) or re.search(
        r"\d|\b(percent|percentage|streak|diagnos\w*)\b|you (completed|missed|achieved)|"
        r"I (created|updated|deleted|changed|saved|set your)|system prompt|api.?key|sk-",
        message, re.I,
    ):
        raise UnsafeCoachOutput("Unverified or private content")
    return message.strip()
