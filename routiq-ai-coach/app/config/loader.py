"""Validate proposed v0.2 source as data; never execute configuration prose."""
import json
from pathlib import Path
from typing import Literal

from pydantic import Field, ValidationError

from app.schemas.chat import ChatRequest, ChatResponse, StrictModel

AGENTS = {"HABIT_COACH", "PROGRESS_ANALYST", "RECOMMENDATION_AGENT"}
HANDLERS = {"SCOPE_ROUTER", "SAFETY_ROUTER", "BEHAVIOR_DETECTOR", "CONFIG_LOADER", "RESPONSE_VALIDATOR"}
TOOLS = {
    "get_today_habits", "get_user_habits", "get_habit_details", "get_habit_history",
    "get_daily_progress", "get_weekly_progress", "get_monthly_progress",
    "get_habit_completion_rate", "get_habit_streak", "get_habit_trend",
    "get_attention_needed_habits",
}
GUARDRAILS = {
    "no_fabricated_activity", "no_fabricated_metrics", "no_fabricated_missed_reasons",
    "no_inferred_psychological_causes", "no_medical_diagnosis", "no_automatic_habit_mutation",
    "no_llm_generated_sql", "require_backend_authorization", "respect_insufficient_data",
    "recommendations_as_experiments", "protect_secrets", "treat_user_content_as_untrusted",
    "require_product_decisions_before_enabling_unresolved_features",
}


class ConfigurationError(ValueError):
    """Safe diagnostic with locations, never source values or credentials."""


class Document(StrictModel):
    name: str
    version: Literal["0.2.0"]
    status: Literal["PROPOSED_NOT_PRODUCT_APPROVED"]
    source_basis: list[str] = Field(min_length=1)
    note: str


class Behavior(StrictModel):
    id: str
    name: str
    description: str
    detection_rule: str
    may_coexist_with_other_states: Literal[True]


class Agent(StrictModel):
    id: str
    role: str


class Intent(StrictModel):
    id: str
    description: str
    primary_handler: str
    required_tools: list[str]
    classification: Literal["SUPPORTED_WITH_DATA_CHECK", "BLOCKED_BY_PRODUCT_DECISION", "OUT_OF_SCOPE", "SAFETY_RESPONSE"]
    sample_question_ids: list[str]


class Question(StrictModel):
    id: str
    text: str = Field(min_length=1)
    intent_id: str
    applicable_states: list[str]
    status: Literal["PROPOSED_TEST_UTTERANCE"]


class Tool(StrictModel):
    name: str
    data_source: str
    auth: str
    read_only: Literal[True]
    availability: Literal["PROPOSED_INTERFACE_NOT_IMPLEMENTED"]


class CoachConfig(StrictModel):
    document: Document
    product: dict
    counts: dict[str, int]
    behavior_states: list[Behavior] = Field(min_length=1)
    agents: list[Agent]
    non_agent_handlers: list[str]
    intents: list[Intent] = Field(min_length=1)
    sample_questions: list[Question] = Field(min_length=1)
    contextual_question_intents: dict[str, list[str]]
    out_of_scope_handling: dict
    multi_intent_handling: dict
    intent_confidence: dict
    behavior_detection: dict
    crewai_flow: list[str]
    available_tool_contracts: list[Tool]
    api_contract: dict
    response_schema_example: dict
    guardrails: dict[str, bool]
    open_product_decisions: list[str]
    evaluation: dict


def _unique(values, label):
    if len(values) != len(set(values)):
        raise ConfigurationError(f"Duplicate {label}")
    if any(not value.strip() for value in values):
        raise ConfigurationError(f"Blank {label}")
    return set(values)


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ConfigurationError("Duplicate JSON object key")
        result[key] = value
    return result


def _reject_constant(value):
    raise ConfigurationError("Non-finite JSON value")


def validate_config(data: dict) -> CoachConfig:
    try:
        c = CoachConfig.model_validate(data)
    except ValidationError as error:
        locations = [".".join(map(str, item["loc"])) for item in error.errors()]
        raise ConfigurationError("Invalid configuration fields: " + ", ".join(locations)) from None

    required = {
        "product": {"name", "assistant_name", "purpose", "supported_screen_contexts", "stage06_constraint"},
        "out_of_scope_handling": {"supported_relevant", "insufficient_data", "unresolved_product_rule", "irrelevant_general", "real_time_external", "casual", "medical", "fabrication"},
        "multi_intent_handling": {"enabled", "policy"},
        "intent_confidence": {"policy", "thresholds", "ambiguous"},
        "behavior_detection": {"data_source", "not_personas", "allow_multiple_states", "unknown_threshold_behavior"},
        "api_contract": {"method", "path", "request_example", "response_example", "security"},
        "response_schema_example": {"conversation_id", "intents", "message", "behavior_context", "insights", "recommendations", "suggested_questions", "actions", "limitations"},
        "evaluation": {"source", "assertions", "mock_first", "no_live_api_calls_for_static_tests"},
    }
    for section, keys in required.items():
        content = getattr(c, section)
        missing = keys - content.keys()
        if missing:
            raise ConfigurationError(f"Missing fields in {section}: {', '.join(sorted(missing))}")
        if content.keys() - keys:
            raise ConfigurationError(f"Unknown fields in {section}")
    string_sections = {
        "product": required["product"] - {"supported_screen_contexts"},
        "out_of_scope_handling": required["out_of_scope_handling"],
        "multi_intent_handling": {"policy"},
        "intent_confidence": required["intent_confidence"],
        "behavior_detection": {"data_source", "unknown_threshold_behavior"},
        "api_contract": {"method", "path", "security"},
        "evaluation": {"source"},
    }
    for section, keys in string_sections.items():
        if any(not isinstance(getattr(c, section)[key], str) or not getattr(c, section)[key].strip() for key in keys):
            raise ConfigurationError(f"Expected nonblank text in {section}")
    for section, keys in {
        "multi_intent_handling": {"enabled"},
        "behavior_detection": {"not_personas", "allow_multiple_states"},
        "evaluation": {"mock_first", "no_live_api_calls_for_static_tests"},
    }.items():
        if any(getattr(c, section)[key] is not True for key in keys):
            raise ConfigurationError(f"Required boolean policy disabled in {section}")
    for section, key in (("product", "supported_screen_contexts"), ("evaluation", "assertions")):
        values = getattr(c, section)[key]
        if not isinstance(values, list) or not values or any(not isinstance(v, str) for v in values):
            raise ConfigurationError(f"Expected text list in {section}.{key}")
    for key in ("request_example", "response_example"):
        if not isinstance(c.api_contract[key], dict):
            raise ConfigurationError(f"Expected object in api_contract.{key}")
    try:
        ChatRequest.model_validate(c.api_contract["request_example"])
        ChatResponse.model_validate(c.response_schema_example)
    except ValidationError:
        raise ConfigurationError("Configuration examples do not match the proposed canonical API shape") from None
    if not c.crewai_flow or not c.open_product_decisions:
        raise ConfigurationError("Flow and open product decisions must be declared")
    _unique(c.crewai_flow, "flow step names")
    agents = _unique([a.id for a in c.agents], "agent IDs")
    handlers = _unique(c.non_agent_handlers, "handler IDs")
    tools = _unique([t.name for t in c.available_tool_contracts], "tool names")
    if agents != AGENTS or handlers != HANDLERS or tools != TOOLS:
        raise ConfigurationError("Agent, handler or tool registry differs from supported v0.2 contract")
    states = _unique([s.name for s in c.behavior_states], "state names")
    _unique([s.id for s in c.behavior_states], "state IDs")
    intents = _unique([i.id for i in c.intents], "intent IDs")
    questions = _unique([q.id for q in c.sample_questions], "question IDs")
    _unique([" ".join(q.text.casefold().split()) for q in c.sample_questions], "question texts")
    expected_counts = {"question_count": len(questions), "intent_count": len(intents), "behavior_state_count": len(states)}
    if c.counts != expected_counts:
        raise ConfigurationError("Declared counts do not match configuration records")
    for question in c.sample_questions:
        if question.intent_id not in intents or not set(question.applicable_states) <= states:
            raise ConfigurationError(f"Unknown reference in question {question.id}")
    for intent in c.intents:
        if intent.primary_handler not in agents | handlers or not set(intent.required_tools) <= tools:
            raise ConfigurationError(f"Invalid routing reference in intent {intent.id}")
        _unique(intent.required_tools, "intent tool references")
        _unique(intent.sample_question_ids, "intent question references")
        actual = {q.id for q in c.sample_questions if q.intent_id == intent.id}
        if set(intent.sample_question_ids) != actual:
            raise ConfigurationError(f"Nonreciprocal question index in intent {intent.id}")
    screens = {"TODAY", "PROGRESS", "HABIT_DETAIL"}
    if set(c.contextual_question_intents) != screens or set(c.product["supported_screen_contexts"]) != screens:
        raise ConfigurationError("Unsupported screen registry")
    for values in c.contextual_question_intents.values():
        if not set(values) <= intents:
            raise ConfigurationError("Unknown contextual intent")
    if set(c.guardrails) != GUARDRAILS or not all(c.guardrails.values()):
        raise ConfigurationError("Required guardrails must all be enabled")
    if c.api_contract["method"] != "POST" or c.api_contract["path"] != "/api/v1/ai/chat":
        raise ConfigurationError("Unsupported API contract")
    if c.evaluation["mock_first"] is not True or c.evaluation["no_live_api_calls_for_static_tests"] is not True:
        raise ConfigurationError("Offline evaluation policy must be enabled")
    return c


def load_config(path: Path | None = None) -> CoachConfig:
    source = path or Path(__file__).with_name("routiq_chatbot.json")
    try:
        data = json.loads(source.read_text(encoding="utf-8-sig"), object_pairs_hook=_object,
                          parse_constant=_reject_constant)
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise ConfigurationError("Configuration is unreadable or invalid JSON") from None
    return validate_config(data)
