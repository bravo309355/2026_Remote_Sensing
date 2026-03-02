import pytest

from debug_api import extract_records_and_type, mask_api_key_in_url


def test_mask_api_key_in_url():
    masked = mask_api_key_in_url(
        "https://example.com/api?api_key=secret123&format=json&x=1"
    )
    assert "secret123" not in masked
    assert "api_key=%2A%2A%2AREDACTED%2A%2A%2A" in masked
    assert "format=json" in masked


def test_extract_records_for_list_payload():
    payload = [{"sitename": "A"}]
    records, response_type = extract_records_and_type(payload)
    assert response_type == "list"
    assert len(records) == 1


def test_extract_records_for_dict_payload():
    payload = {"records": [{"sitename": "A"}, {"sitename": "B"}]}
    records, response_type = extract_records_and_type(payload)
    assert response_type == "dict.records"
    assert len(records) == 2


def test_extract_records_invalid_payload_raises():
    with pytest.raises(ValueError):
        extract_records_and_type({"unexpected": []})
