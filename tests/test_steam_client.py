"""Tests for Steam client helpers."""

from src.steam_client import parse_appid


def test_parse_appid_numeric() -> None:
    """Numeric input should be treated as AppID."""
    assert parse_appid("1942280") == "1942280"


def test_parse_appid_url() -> None:
    """Steam store URLs should yield the AppID."""
    assert parse_appid("https://store.steampowered.com/app/1942280/Brotato/") == "1942280"


def test_parse_appid_name_returns_none() -> None:
    """Plain names should not be parsed as AppID."""
    assert parse_appid("Brotato") is None
