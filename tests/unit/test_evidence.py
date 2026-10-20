from __future__ import annotations

from coachme.domain.evidence import EvidenceRecord, is_valid, validate


def _record(**patch):
    data = {
        "id": "ev_0001",
        "run_id": "20261018T090000Z-abc12345",
        "tool": "look",
        "window": (2.0, 3.0),
        "times": [2.2, 2.8],
        "summary": "contact near 2.8s",
        "confidence": "medium",
    }
    data.update(patch)
    return EvidenceRecord(**data)


def test_valid_record_round_trips() -> None:
    record = _record()
    assert is_valid(record)
    cloned = EvidenceRecord.from_dict(record.to_dict())
    assert cloned == record
    assert cloned.envelope()["evidence_id"] == "ev_0001"


def test_invalid_confidence_and_window_are_reported() -> None:
    assert "bad confidence: certain" in validate(_record(confidence="certain"))
    assert any("bad window" in item for item in validate(_record(window=(3.0, 2.0))))


def test_envelope_is_compact_and_has_no_payload() -> None:
    envelope = _record(details="compact detail").envelope()
    assert envelope["details"] == "compact detail"
    assert "payload" not in envelope
