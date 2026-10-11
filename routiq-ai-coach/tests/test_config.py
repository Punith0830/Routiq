import hashlib
import json
from pathlib import Path

import pytest

from app.config.loader import ConfigurationError, load_config, validate_config


def test_original_config_is_preserved():
    path = Path(__file__).parents[1] / "app/config/routiq_chatbot.json"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == "9ba2027729a85e1821f806e3fb6cfc74fef1ab95427cbfab402c6fc288fe0f15"
    c = load_config()
    assert (len(c.sample_questions), len(c.intents), len(c.behavior_states)) == (255, 28, 8)
    assert c.document.status == "PROPOSED_NOT_PRODUCT_APPROVED"


@pytest.mark.parametrize("section", [
    "document", "product", "counts", "behavior_states", "agents", "non_agent_handlers",
    "intents", "sample_questions", "contextual_question_intents", "out_of_scope_handling",
    "multi_intent_handling", "intent_confidence", "behavior_detection", "crewai_flow",
    "available_tool_contracts", "api_contract", "response_schema_example", "guardrails",
    "open_product_decisions", "evaluation",
])
def test_missing_sections_fail(config_data, section):
    del config_data[section]
    with pytest.raises(ConfigurationError):
        validate_config(config_data)


@pytest.mark.parametrize("defect", ["count", "intent", "state", "agent", "tool", "duplicate_id", "duplicate_text", "routing", "guardrail", "nested", "context", "write_tool", "extra", "offline"])
def test_corruptions_fail(config_data, defect):
    c = config_data
    if defect == "count": c["counts"]["question_count"] = 1
    if defect == "intent": c["sample_questions"][0]["intent_id"] = "UNKNOWN"
    if defect == "state": c["sample_questions"][0]["applicable_states"] = ["BEH-001"]
    if defect == "agent": c["intents"][0]["primary_handler"] = "EXECUTE_CODE"
    if defect == "tool": c["intents"][0]["required_tools"] = ["run_sql"]
    if defect == "duplicate_id": c["behavior_states"][1]["id"] = c["behavior_states"][0]["id"]
    if defect == "duplicate_text": c["sample_questions"][1]["text"] = "  " + c["sample_questions"][0]["text"].upper()
    if defect == "routing": c["intents"][0]["sample_question_ids"] = []
    if defect == "guardrail": c["guardrails"]["protect_secrets"] = False
    if defect == "nested": del c["api_contract"]["security"]
    if defect == "context": c["contextual_question_intents"]["TODAY"] = ["UNKNOWN"]
    if defect == "write_tool": c["available_tool_contracts"][0]["read_only"] = False
    if defect == "extra": c["arbitrary_code"] = "exec(...)"
    if defect == "offline": c["evaluation"]["mock_first"] = False
    with pytest.raises(ConfigurationError): validate_config(c)


@pytest.mark.parametrize("text", ['{"a":1,"a":2}', '{', '{"a":NaN}'])
def test_bad_json(tmp_path, text):
    path = tmp_path / "invalid.json"
    path.write_text(text)
    with pytest.raises(ConfigurationError): load_config(path)


def test_diagnostics_do_not_echo_source_values(config_data):
    config_data["document"]["version"] = "SECRET_SENTINEL"
    with pytest.raises(ConfigurationError) as error: validate_config(config_data)
    assert "SECRET_SENTINEL" not in str(error.value)


def test_source_prose_is_not_executed(config_data):
    config_data["behavior_states"][0]["detection_rule"] = "raise RuntimeError('never execute me')"
    assert validate_config(config_data).behavior_states[0].detection_rule.startswith("raise")


@pytest.mark.parametrize("section,key,value", [
    ("product", "supported_screen_contexts", "TODAY"),
    ("intent_confidence", "thresholds", 0.8),
    ("behavior_detection", "allow_multiple_states", "true"),
    ("evaluation", "assertions", {}),
    ("api_contract", "request_example", []),
])
def test_nested_types_fail(config_data, section, key, value):
    config_data[section][key] = value
    with pytest.raises(ConfigurationError): validate_config(config_data)


def test_all_question_library_references_resolve(config_data):
    c = validate_config(config_data)
    indexed = {question_id for intent in c.intents for question_id in intent.sample_question_ids}
    assert indexed == {q.id for q in c.sample_questions}
    assert len(indexed) == 255  # Structural audit, not classifier accuracy.
