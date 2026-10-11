import pytest
from pydantic import ValidationError

from app.schemas.chat import ChatResponse


def test_canonical_response_handles_multiple_intents_and_optional_experiments():
    response = ChatResponse.model_validate({
        "conversation_id": None,
        "intents": ["WEEKLY_PROGRESS", "REAL_TIME_EXTERNAL_INFORMATION"],
        "message": "Synthetic schema fixture only.",
        "suggested_questions": [{"text": "How was my week?", "intent_id": "WEEKLY_PROGRESS"}],
        "recommendations": [{"title": "Test", "description": "Optional synthetic experiment"}],
    })
    assert response.recommendations[0].type == "OPTIONAL_EXPERIMENT"


@pytest.mark.parametrize("field,value", [
    ("suggested_questions", ["unsupported old string format"]),
    ("recommendations", [{"title": "test", "description": "test", "type": "GUARANTEED_RESULT"}]),
    ("behavior_context", [{"state": "NEW_USER", "evidence": [], "confidence": 0.99}]),
])
def test_invalid_response_shapes_fail(field, value):
    with pytest.raises(ValidationError):
        ChatResponse.model_validate({"conversation_id": None, "intents": [], "message": "test", field: value})
