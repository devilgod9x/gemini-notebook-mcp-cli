"""Windows ACL hardening of the login storage folder (icacls is mocked)."""

import subprocess
import sys
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from notebooklm_tools.cli.main import app
from notebooklm_tools.services import auth_storage
from notebooklm_tools.services.errors import ServiceError

SID = "S-1-5-21-1111-2222-3333-1001"
WHOAMI_OK = SimpleNamespace(returncode=0, stdout=f'"PC\\me","{SID}"\n', stderr="")


@pytest.fixture
def fake_windows(monkeypatch):
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        if cmd[0] == "whoami":
            return WHOAMI_OK
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(subprocess, "run", fake_run)
    return calls


def test_noop_on_non_windows(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    result = auth_storage.harden_storage_permissions()
    assert result["supported"] is False and result["applied"] is False


def test_dry_run_builds_command_without_running_icacls(fake_windows):
    result = auth_storage.harden_storage_permissions(dry_run=True)
    assert result["applied"] is False
    assert result["command"][0] == "icacls"
    assert "/inheritance:r" in result["command"]
    assert f"*{SID}:(OI)(CI)F" in result["command"]
    assert "*S-1-5-18:(OI)(CI)F" in result["command"]
    assert all(c[0] != "icacls" for c in fake_windows)


def test_apply_runs_icacls(fake_windows):
    result = auth_storage.harden_storage_permissions()
    assert result["applied"] is True
    assert [c[0] for c in fake_windows] == ["whoami", "icacls"]


def test_icacls_failure_is_a_service_error(monkeypatch, fake_windows):
    def failing(cmd, **kwargs):
        if cmd[0] == "whoami":
            return WHOAMI_OK
        return SimpleNamespace(returncode=5, stdout="", stderr="Access is denied.")

    monkeypatch.setattr(subprocess, "run", failing)
    with pytest.raises(ServiceError, match="Access is denied"):
        auth_storage.harden_storage_permissions()


def test_bad_whoami_output_is_rejected(monkeypatch, fake_windows):
    bad = SimpleNamespace(returncode=0, stdout='"PC\\me","not-a-sid"\n', stderr="")
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: bad)
    with pytest.raises(ServiceError):
        auth_storage.harden_storage_permissions()


def test_cli_dry_run_changes_nothing(fake_windows):
    out = CliRunner().invoke(app, ["auth", "storage", "harden", "--dry-run"])
    assert out.exit_code == 0, out.output
    assert "icacls" in out.output
    assert all(c[0] != "icacls" for c in fake_windows)


def test_cli_aborts_without_confirmation(fake_windows):
    out = CliRunner().invoke(app, ["auth", "storage", "harden"], input="n\n")
    assert out.exit_code != 0
    assert all(c[0] != "icacls" for c in fake_windows)


def test_cli_confirm_applies(fake_windows):
    out = CliRunner().invoke(app, ["auth", "storage", "harden", "-y"])
    assert out.exit_code == 0, out.output
    assert any(c[0] == "icacls" for c in fake_windows)
