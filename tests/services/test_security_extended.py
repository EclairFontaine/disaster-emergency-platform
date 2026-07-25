"""安全功能单元测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.unit
class TestPasswordStrength:

    def test_too_short(self):
        from app.core.security import validate_password_strength
        valid, msg = validate_password_strength("12345")
        assert not valid
        assert "至少" in msg

    def test_digits_only(self):
        from app.core.security import validate_password_strength
        valid, msg = validate_password_strength("12345678")
        assert not valid
        assert "字母" in msg

    def test_alpha_only(self):
        from app.core.security import validate_password_strength
        valid, msg = validate_password_strength("abcdefg")
        assert not valid
        assert "数字" in msg

    def test_valid_password(self):
        from app.core.security import validate_password_strength
        valid, msg = validate_password_strength("abc123")
        assert valid
        assert msg == ""

    def test_valid_complex_password(self):
        from app.core.security import validate_password_strength
        valid, msg = validate_password_strength("admin123")
        assert valid
        assert msg == ""


@pytest.mark.unit
class TestRateLimiter:

    def test_limiter_initialized(self):
        from app.main import limiter
        assert limiter is not None

    def test_limiter_default_limits(self):
        from app.main import limiter
        limits = limiter._default_limits
        assert len(limits) >= 1

    def test_auth_rate_limit_decorated(self):
        from app.api.auth import login
        assert "__wrapped__" in dir(login) or hasattr(login, "__wrapped__")
