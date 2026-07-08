from app.maas_client import _extract_json


def test_extract_json_from_code_block():
    text = 'Here:\n```json\n{"summary": "ok", "findings": []}\n```\nDone.'
    result = _extract_json(text)
    assert result["summary"] == "ok"
    assert result["findings"] == []


def test_extract_json_raw_object():
    text = 'blah {"risk_score": 42} trailing'
    result = _extract_json(text)
    assert result["risk_score"] == 42


def test_extract_json_fallback_wraps_text():
    text = "No JSON here, just prose."
    result = _extract_json(text)
    assert result["summary"] == text
    assert result["findings"] == []
    assert result["risks"] == []
