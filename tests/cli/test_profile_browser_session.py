"""`nlm login profile delete` / `forget-browser` and the saved browser login."""

from typer.testing import CliRunner

from notebooklm_tools.cli.main import app
from notebooklm_tools.services.auth import AuthManager
from notebooklm_tools.utils.config import get_storage_dir

runner = CliRunner()


def _browser_dir(kind: str, name: str, lock: str | None = None):
    path = get_storage_dir() / kind / name
    path.mkdir(parents=True)
    (path / "Cookies").write_text("secret")
    if lock:
        (path / lock).write_text("")
    return path


def _save(name: str) -> None:
    AuthManager(name).save_profile(cookies={"SID": "x"}, csrf_token="c", email=f"{name}@x.com")


def test_profile_delete_also_removes_browser_login():
    _save("gone")
    chrome = _browser_dir("chrome-profiles", "gone")
    firefox = _browser_dir("firefox-profiles", "gone")

    out = runner.invoke(app, ["login", "profile", "delete", "gone", "-y"])

    assert out.exit_code == 0, out.output
    assert not chrome.exists() and not firefox.exists()
    assert "Removed saved browser login" in out.output


def test_profile_delete_keeps_browser_login_that_is_in_use():
    _save("busy")
    chrome = _browser_dir("chrome-profiles", "busy", lock="SingletonLock")

    out = runner.invoke(app, ["login", "profile", "delete", "busy", "-y"])

    assert out.exit_code == 0, out.output  # credentials are still deleted
    assert chrome.exists()
    assert "forget-browser busy" in out.output


def test_forget_browser_keeps_credentials():
    _save("keep")
    chrome = _browser_dir("chrome-profiles", "keep")

    out = runner.invoke(app, ["login", "profile", "forget-browser", "keep", "-y"])

    assert out.exit_code == 0, out.output
    assert not chrome.exists()
    assert "keep" in AuthManager.list_profiles()


def test_forget_browser_in_use_needs_force():
    _save("busy2")
    chrome = _browser_dir("chrome-profiles", "busy2", lock="SingletonLock")

    refused = runner.invoke(app, ["login", "profile", "forget-browser", "busy2", "-y"])
    assert refused.exit_code == 1
    assert chrome.exists()

    forced = runner.invoke(app, ["login", "profile", "forget-browser", "busy2", "-y", "--force"])
    assert forced.exit_code == 0
    assert not chrome.exists()


def test_forget_browser_nothing_to_remove():
    out = runner.invoke(app, ["login", "profile", "forget-browser", "nobody", "-y"])
    assert out.exit_code == 0
    assert "No saved browser login" in out.output


def test_forget_browser_aborts_without_confirmation():
    chrome = _browser_dir("chrome-profiles", "ask")
    out = runner.invoke(app, ["login", "profile", "forget-browser", "ask"], input="n\n")
    assert out.exit_code != 0
    assert chrome.exists()
