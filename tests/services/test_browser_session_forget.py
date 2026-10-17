"""Removing saved browser logins (the unencrypted long-lived Google session)."""

import pytest

from notebooklm_tools.services.auth_storage import (
    forget_browser_session,
    get_browser_profile_dirs,
)
from notebooklm_tools.utils.config import get_storage_dir


def _make(path, lock=None):
    path.mkdir(parents=True)
    (path / "Cookies").write_text("secret")
    if lock:
        (path / lock).write_text("")
    return path


def test_lists_only_existing_dirs():
    storage = get_storage_dir()
    chrome = _make(storage / "chrome-profiles" / "work")
    assert get_browser_profile_dirs("work") == [chrome]
    assert get_browser_profile_dirs("nobody") == []


def test_removes_chrome_and_firefox_but_not_other_profiles():
    storage = get_storage_dir()
    _make(storage / "chrome-profiles" / "work")
    _make(storage / "firefox-profiles" / "work")
    keep = _make(storage / "chrome-profiles" / "other")

    result = forget_browser_session("work")

    assert len(result["removed"]) == 2
    assert result["skipped_in_use"] == []
    assert get_browser_profile_dirs("work") == []
    assert keep.exists()


def test_legacy_default_chrome_profile_is_included():
    storage = get_storage_dir()
    legacy = _make(storage / "chrome-profile")
    assert get_browser_profile_dirs("default") == [legacy]
    forget_browser_session("default")
    assert not legacy.exists()


def test_skips_dir_in_use_unless_forced():
    storage = get_storage_dir()
    busy = _make(storage / "chrome-profiles" / "work", lock="SingletonLock")

    result = forget_browser_session("work")
    assert result["removed"] == []
    assert result["skipped_in_use"] == [str(busy)]
    assert busy.exists()

    forced = forget_browser_session("work", force=True)
    assert forced["removed"] == [str(busy)]
    assert not busy.exists()


def test_read_only_files_are_removed():
    import os
    import stat

    storage = get_storage_dir()
    d = _make(storage / "chrome-profiles" / "work")
    os.chmod(d / "Cookies", stat.S_IREAD)
    forget_browser_session("work")
    assert not d.exists()


def test_rejects_unsafe_profile_name():
    with pytest.raises(ValueError):
        get_browser_profile_dirs("../escape")
