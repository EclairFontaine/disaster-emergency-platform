"""核心模块单元测试 — 安全、配置、FSM"""
import pytest
from app.core.security import hash_password, verify_password, create_access_token, decode_token
from app.services.incident_fsm import validate_transition, STATES, TRANSITIONS


@pytest.mark.unit
class TestSecurity:
    """密码哈希与JWT Token"""

    def test_hash_and_verify_password(self):
        hashed = hash_password("test123")
        assert hashed != "test123"
        assert verify_password("test123", hashed)
        assert not verify_password("wrong", hashed)

    def test_create_and_decode_token(self):
        token = create_access_token({"sub": "1", "username": "admin"})
        assert isinstance(token, str)
        payload = decode_token(token)
        assert payload["sub"] == "1"
        assert payload["username"] == "admin"
        assert "exp" in payload

    def test_decode_invalid_token(self):
        with pytest.raises(Exception):
            decode_token("invalid.token.here")


@pytest.mark.unit
class TestIncidentFSM:
    """灾情状态机"""

    def test_valid_transitions(self):
        assert validate_transition("pending_review", "confirmed")
        assert validate_transition("confirmed", "in_progress")
        assert validate_transition("confirmed", "closed")
        assert validate_transition("in_progress", "closed")

    def test_invalid_transitions(self):
        assert not validate_transition("pending_review", "closed")
        assert not validate_transition("closed", "confirmed")
        assert not validate_transition("pending_review", "in_progress")

    def test_closed_no_transitions(self):
        assert validate_transition("closed", "") is False

    def test_all_states_defined(self):
        assert len(STATES) == 4
        for state in STATES:
            assert state in TRANSITIONS

    def test_happy_path(self):
        path = [("pending_review", "confirmed"), ("confirmed", "in_progress"), ("in_progress", "closed")]
        for current, target in path:
            assert validate_transition(current, target)

    def test_misreport_path(self):
        assert validate_transition("pending_review", "confirmed")
        assert validate_transition("confirmed", "closed")


@pytest.mark.unit
class TestHaversine:
    """Haversine距离计算"""

    def test_same_point(self):
        from app.api.incidents import haversine
        dist = haversine(25.0, 102.0, 25.0, 102.0)
        assert dist == 0.0

    def test_known_distance(self):
        from app.api.incidents import haversine
        dist = haversine(25.04, 102.68, 25.59, 100.23)
        assert 200000 < dist < 300000

    def test_engine_haversine(self):
        from app.services.ai_engine import haversine
        dist = haversine(25.0, 102.0, 25.0, 102.0)
        assert dist == 0.0
