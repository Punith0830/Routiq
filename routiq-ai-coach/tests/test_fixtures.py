import json
from pathlib import Path


def test_mock_records_are_explicitly_synthetic_and_isolated():
    fixture = json.loads((Path(__file__).parent / "fixtures/habits.json").read_text())
    assert fixture["classification"] == "SYNTHETIC_TEST_FIXTURE_NOT_USER_ACTIVITY"
    assert len({h["owner"] for h in fixture["habits"]}) == 2
    assert fixture["metric_rules"] == "TBD_PRODUCT_DECISION"
    assert fixture["events"] == []
