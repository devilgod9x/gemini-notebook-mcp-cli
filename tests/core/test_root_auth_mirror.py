"""Root auth.json mirror opt-out and the Windows plain-text storage warning."""

import sys

import pytest

from notebooklm_tools.core.auth import (
    DISABLE_ROOT_AUTH_MIRROR_ENV,
    AuthTokens,
    get_cache_path,
    save_tokens_to_cache,
)
from notebooklm_tools.services import auth_storage


def _tokens() -> AuthTokens:
    return AuthTokens(cookies={"SID": "x"}, csrf_token="c", session_id="s")


def test_root_mirror_written_by_default():
    save_tokens_to_cache(_tokens(), silent=True)
    assert get_cache_path().exists()


def test_root_mirror_can_be_disabled(monkeypatch):
    monkeypatch.setenv(DISABLE_ROOT_AUTH_MIRROR_ENV, "1")
    save_tokens_to_cache(_tokens(), silent=True)
    assert not get_cache_path().exists()


def test_disabling_mirror_keeps_profile_files(monkeypatch):
    monkeypatch.setenv(DISABLE_ROOT_AUTH_MIRROR_ENV, "1")
    save_tokens_to_cache(_tokens(), silent=True)
    status = auth_storage.get_storage_status()
    assert status["has_legacy"] is True  # the profile's own cookies.json still exists


@pytest.mark.parametrize("platform", ["win32", "linux", "darwin"])
def test_plaintext_warning_only_for_file_mode_on_windows(monkeypatch, platform):
    monkeypatch.setattr(sys, "platform", platform)
    warning = auth_storage.get_plaintext_warning("file")
    if platform == "win32":
        assert warning and "nlm auth storage set protected" in warning
    else:
        assert warning is None
    assert auth_storage.get_plaintext_warning("protected") is None


def test_storage_status_includes_warning_on_windows(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    status = auth_storage.get_storage_status()
    assert status["mode"] == "file"
    assert status["plaintext_warning"] == auth_storage.WINDOWS_FILE_MODE_WARNING
