# src/tests/unit/shared/test_validators.py
import pytest
from datetime import datetime, date
from my_bot.shared.utils.text_validators import (
    validate_email,
    validate_phone,
    validate_username,
    validate_password,
    validate_url,
    sanitize_text,
    validate_length,
    validate_positive_number,
    validate_date_format,
    validate_time_format,
)


class TestTextValidators:
    """Unit tests for text validation utilities."""

    def test_validate_email_valid(self):
        """Test validating valid email addresses."""
        valid_emails = [
            "user@example.com",
            "user.name@domain.com",
            "user+label@domain.com",
            "user@sub.domain.com",
            "user@domain.co.uk",
            "user_name@domain.com",
            "user123@domain.com",
        ]
        for email in valid_emails:
            assert validate_email(email) is True

    def test_validate_email_invalid(self):
        """Test validating invalid email addresses."""
        invalid_emails = [
            "user",
            "user@",
            "@domain.com",
            "user@domain.",
            "user@domain..com",
            "user name@domain.com",
            "user@domain.c",
            "",
            None,
        ]
        for email in invalid_emails:
            assert validate_email(email) is False

    def test_validate_phone_valid(self):
        """Test validating valid phone numbers."""
        valid_phones = [
            "+989123456789",
            "09123456789",
            "+1-555-555-5555",
            "+44-20-7946-0958",
            "021-12345678",
            "0912-345-6789",
        ]
        for phone in valid_phones:
            assert validate_phone(phone) is True

    def test_validate_phone_invalid(self):
        """Test validating invalid phone numbers."""
        invalid_phones = [
            "123",
            "+",
            "abc",
            "0912345678901",
            "++989123456789",
            "",
            None,
        ]
        for phone in invalid_phones:
            assert validate_phone(phone) is False

    def test_validate_username_valid(self):
        """Test validating valid usernames."""
        valid_usernames = [
            "user",
            "user123",
            "user_name",
            "username",
            "user_123",
            "u",
            "user123456789",
        ]
        for username in valid_usernames:
            assert validate_username(username) is True

    def test_validate_username_invalid(self):
        """Test validating invalid usernames."""
        invalid_usernames = [
            "",
            "!user",
            "user@name",
            " user",
            "user ",
            "user name",
            None,
        ]
        for username in invalid_usernames:
            assert validate_username(username) is False

    def test_validate_username_length(self):
        """Test username length validation."""
        # Too short
        assert validate_username("a", min_length=2) is False
        # Too long
        long_name = "a" * 31
        assert validate_username(long_name, max_length=30) is False
        # Valid length
        assert validate_username("ab", min_length=2, max_length=30) is True

    def test_validate_password_valid(self):
        """Test validating valid passwords."""
        valid_passwords = [
            "Password123",
            "P@ssw0rd",
            "MyPassword2024",
            "Secure_Password_123",
            "A1b2C3d4E5",
        ]
        for password in valid_passwords:
            assert validate_password(password) is True

    def test_validate_password_invalid(self):
        """Test validating invalid passwords."""
        invalid_passwords = [
            "",
            "pass",
            "password",
            "123456",
            "PASSWORD",
            "Passw0rd",
            "Pass@",
            None,
        ]
        for password in invalid_passwords:
            assert validate_password(password) is False

    def test_validate_password_with_custom_rules(self):
        """Test password validation with custom rules."""
        # Minimum length 8
        assert validate_password("A1b2c3d4", min_length=8) is True
        assert validate_password("A1b2c3", min_length=8) is False

        # Must contain uppercase
        assert validate_password("password123", require_uppercase=True) is False
        assert validate_password("Password123", require_uppercase=True) is True

        # Must contain number
        assert validate_password("Password", require_number=True) is False
        assert validate_password("Password123", require_number=True) is True

        # Must contain special character
        assert validate_password("Password123", require_special=True) is False
        assert validate_password("P@ssword123", require_special=True) is True

    def test_validate_url_valid(self):
        """Test validating valid URLs."""
        valid_urls = [
            "https://example.com",
            "http://example.com",
            "https://www.example.com",
            "https://example.com/path",
            "https://example.com?query=1",
            "https://example.com#anchor",
            "https://sub.example.com",
            "https://example.co.uk",
        ]
        for url in valid_urls:
            assert validate_url(url) is True

    def test_validate_url_invalid(self):
        """Test validating invalid URLs."""
        invalid_urls = [
            "example.com",
            "http://",
            "https://",
            "ftp://example.com",
            "",
            "not a url",
            None,
        ]
        for url in invalid_urls:
            assert validate_url(url) is False

    def test_sanitize_text(self):
        """Test text sanitization."""
        # Remove special characters
        assert sanitize_text("Hello @World!") == "Hello World!"
        assert sanitize_text("<script>alert('xss')</script>") == "scriptalertxssscript"
        assert sanitize_text("Hello   World") == "Hello World"
        assert sanitize_text(" Hello World ") == "Hello World"
        assert sanitize_text("") == ""

        # With preserve option
        assert sanitize_text("Hello! World.", preserve_chars="!.") == "Hello! World."

    def test_validate_length(self):
        """Test length validation."""
        assert validate_length("Hello", min_len=1, max_len=10) is True
        assert validate_length("Hello", min_len=6, max_len=10) is False
        assert validate_length("Hello World", min_len=1, max_len=10) is False
        assert validate_length("", min_len=0, max_len=10) is True
        assert validate_length(None, min_len=0, max_len=10) is False

    def test_validate_positive_number(self):
        """Test positive number validation."""
        assert validate_positive_number(1) is True
        assert validate_positive_number(100) is True
        assert validate_positive_number(0) is False
        assert validate_positive_number(-1) is False
        assert validate_positive_number(0.5) is True
        assert validate_positive_number(1.0) is True
        assert validate_positive_number(-0.5) is False
        assert validate_positive_number("10") is True
        assert validate_positive_number("abc") is False
        assert validate_positive_number(None) is False

    def test_validate_positive_number_with_max(self):
        """Test positive number validation with max value."""
        assert validate_positive_number(5, max_value=10) is True
        assert validate_positive_number(15, max_value=10) is False
        assert validate_positive_number(5, max_value=5) is True
        assert validate_positive_number(6, max_value=5) is False

    def test_validate_date_format_valid(self):
        """Test validating valid date formats."""
        valid_dates = [
            "2024-01-01",
            "2024-12-31",
            "2024-02-29",
            "2023-01-15",
            "2000-01-01",
        ]
        for date_str in valid_dates:
            assert validate_date_format(date_str) is True

    def test_validate_date_format_invalid(self):
        """Test validating invalid date formats."""
        invalid_dates = [
            "2024-13-01",
            "2024-01-32",
            "2024-02-30",
            "2024-1-1",
            "01-01-2024",
            "2024/01/01",
            "2024-01",
            "",
            None,
        ]
        for date_str in invalid_dates:
            assert validate_date_format(date_str) is False

    def test_validate_date_format_with_format(self):
        """Test validating date formats with custom format."""
        assert validate_date_format("01/01/2024", format_str="%d/%m/%Y") is True
        assert validate_date_format("2024/01/01", format_str="%Y/%m/%d") is True
        assert validate_date_format("01-01-2024", format_str="%d-%m-%Y") is True
        assert validate_date_format("invalid", format_str="%Y-%m-%d") is False

    def test_validate_time_format_valid(self):
        """Test validating valid time formats."""
        valid_times = [
            "12:00:00",
            "00:00:00",
            "23:59:59",
            "12:30",
            "01:01:01",
            "06:00:00",
        ]
        for time_str in valid_times:
            assert validate_time_format(time_str) is True

    def test_validate_time_format_invalid(self):
        """Test validating invalid time formats."""
        invalid_times = [
            "24:00:00",
            "12:60:00",
            "12:00:60",
            "12:00",
            "12-00-00",
            "abc",
            "",
            None,
        ]
        for time_str in invalid_times:
            assert validate_time_format(time_str) is False

    def test_validate_time_format_with_format(self):
        """Test validating time formats with custom format."""
        assert validate_time_format("12:30 PM", format_str="%I:%M %p") is True
        assert validate_time_format("12:30", format_str="%H:%M") is True
        assert validate_time_format("invalid", format_str="%H:%M:%S") is False


class TestValidationEdgeCases:
    """Test edge cases for validation utilities."""

    def test_empty_inputs(self):
        """Test validation with empty inputs."""
        assert validate_email("") is False
        assert validate_phone("") is False
        assert validate_username("") is False
        assert validate_password("") is False
        assert validate_url("") is False
        assert validate_length("", min_len=0) is True
        assert validate_length("", min_len=1) is False

    def test_none_inputs(self):
        """Test validation with None inputs."""
        assert validate_email(None) is False
        assert validate_phone(None) is False
        assert validate_username(None) is False
        assert validate_password(None) is False
        assert validate_url(None) is False
        assert validate_length(None) is False
        assert validate_positive_number(None) is False

    def test_whitespace_inputs(self):
        """Test validation with whitespace inputs."""
        assert validate_email(" user@example.com ") is True
        assert validate_phone(" 09123456789 ") is True
        assert validate_username(" user ") is True
        assert sanitize_text("  Hello  World  ") == "Hello World"

    def test_unicode_inputs(self):
        """Test validation with Unicode inputs."""
        assert validate_email("user@example.com") is True
        assert validate_username("کاربر") is True
        assert sanitize_text("سلام دنیا!") == "سلام دنیا!"
        assert validate_length("درود", min_len=1, max_len=10) is True