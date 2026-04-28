"""Tests for the log_run service."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Run, User
from app.services.runs import _hash_payload, _truncate_payload, log_run


class TestLogRun:
    def test_creates_a_run_row(self, db_session: Session) -> None:
        run = log_run(
            db_session,
            tool_name="analyze",
            input_payload={"text": "hello"},
            output_payload={"document_type": "email"},
            duration_ms=127,
        )

        assert run is not None
        assert run.id is not None
        assert run.tool_name == "analyze"
        assert run.duration_ms == 127
        assert run.status == "success"
        assert run.input_hash  # non-empty
        assert run.input_json == {"text": "hello"}
        assert run.output_json == {"document_type": "email"}

    def test_records_failure_with_error_message(self, db_session: Session) -> None:
        run = log_run(
            db_session,
            tool_name="extract",
            input_payload={"text": "…"},
            output_payload=None,
            duration_ms=12,
            status="error",
            error_message="Unknown strategy: weird",
        )

        assert run is not None
        assert run.status == "error"
        assert run.error_message == "Unknown strategy: weird"
        assert run.output_json is None

    def test_truncates_very_long_error_messages(self, db_session: Session) -> None:
        long_msg = "x" * 5000
        run = log_run(
            db_session,
            tool_name="extract",
            input_payload=None,
            output_payload=None,
            duration_ms=0,
            status="error",
            error_message=long_msg,
        )

        assert run is not None
        assert run.error_message is not None
        assert len(run.error_message) == 2000  # clipped to column width

    def test_attributes_to_guest_user_when_present(self, db_session: Session) -> None:
        guest = User(display_name="Guest", role="guest")
        db_session.add(guest)
        db_session.commit()

        run = log_run(
            db_session,
            tool_name="analyze",
            input_payload={"text": "hi"},
            output_payload={"ok": True},
            duration_ms=5,
        )

        assert run is not None
        assert run.user_id == guest.id

    def test_leaves_user_id_null_when_no_guest(self, db_session: Session) -> None:
        run = log_run(
            db_session,
            tool_name="analyze",
            input_payload={"text": "hi"},
            output_payload={"ok": True},
            duration_ms=5,
        )

        assert run is not None
        assert run.user_id is None

    def test_explicit_user_id_wins_over_guest_fallback(self, db_session: Session) -> None:
        guest = User(display_name="Guest", role="guest")
        alice = User(email="alice@test.dk", role="user")
        db_session.add_all([guest, alice])
        db_session.commit()

        run = log_run(
            db_session,
            tool_name="analyze",
            input_payload={"text": "hi"},
            output_payload={"ok": True},
            duration_ms=5,
            user_id=alice.id,
        )

        assert run is not None
        assert run.user_id == alice.id  # not guest.id

    def test_multiple_runs_appear_in_insertion_order(self, db_session: Session) -> None:
        for i in range(3):
            log_run(
                db_session,
                tool_name=f"tool_{i}",
                input_payload={"i": i},
                output_payload={"i": i},
                duration_ms=i * 10,
            )

        runs = db_session.scalars(select(Run).order_by(Run.id)).all()
        assert [r.tool_name for r in runs] == ["tool_0", "tool_1", "tool_2"]


class TestHashPayload:
    def test_hashes_are_stable_across_dict_ordering(self) -> None:
        a = {"x": 1, "y": 2, "z": 3}
        b = {"z": 3, "y": 2, "x": 1}
        assert _hash_payload(a) == _hash_payload(b)

    def test_hashes_differ_for_different_content(self) -> None:
        assert _hash_payload({"x": 1}) != _hash_payload({"x": 2})

    def test_returns_empty_string_for_none(self) -> None:
        assert _hash_payload(None) == ""

    def test_hash_length_is_64_chars(self) -> None:
        """SHA-256 hex digest is always 64 chars."""
        assert len(_hash_payload({"x": "hello"})) == 64


class TestTruncatePayload:
    def test_small_payload_passes_through(self) -> None:
        payload = {"text": "short"}
        assert _truncate_payload(payload) == payload

    def test_none_returns_none(self) -> None:
        assert _truncate_payload(None) is None

    def test_large_payload_is_truncated_with_marker(self) -> None:
        payload = {"text": "x" * 100_000}
        result = _truncate_payload(payload)

        assert result is not None
        assert result["_truncated"] is True
        assert "_original_size_bytes" in result
        assert "_preview" in result
        assert len(result["_preview"]) == 500

    def test_non_serialisable_returns_error_marker(self) -> None:
        class Opaque:
            pass

        result = _truncate_payload({"thing": Opaque()})
        assert result is not None
        # Either the default=str path handled it, or we got an error marker.
        # Both are acceptable — we just must not crash.
        assert isinstance(result, dict)
