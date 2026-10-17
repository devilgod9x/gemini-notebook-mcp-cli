"""CLI behaviour of `nlm pipeline run`: confirmation prompt and exit code."""

from unittest.mock import patch

from typer.testing import CliRunner

from notebooklm_tools.cli.commands.pipeline import app

runner = CliRunner()

SVC = "notebooklm_tools.cli.commands.pipeline.pipeline_service"
GET_CLIENT = "notebooklm_tools.cli.utils.get_client"


def _step(n: int, ok: bool) -> dict:
    return {
        "step": n,
        "action": "notebook_query",
        "success": ok,
        "result": None,
        "error": None if ok else "API error",
        "duration_ms": 1,
    }


def _result(steps: list[dict]) -> dict:
    succeeded = sum(1 for s in steps if s["success"])
    return {
        "pipeline_name": "p",
        "notebook_id": "nb-1",
        "steps": steps,
        "total_steps": 3,
        "succeeded": succeeded,
        "failed": len(steps) - succeeded,
        "total_duration_ms": 1,
    }


def test_failed_step_exits_nonzero_and_prints_all_steps():
    steps = [_step(1, True), _step(2, False)]
    with patch(GET_CLIENT), patch(SVC) as svc:
        svc.get_confirmation_actions.return_value = []
        svc.pipeline_run.return_value = _result(steps)
        out = runner.invoke(app, ["run", "p", "--notebook", "nb-1"])

    assert out.exit_code == 1
    assert "Step 1" in out.output
    assert "Step 2" in out.output
    assert "API error" in out.output


def test_successful_pipeline_exits_zero():
    with patch(GET_CLIENT), patch(SVC) as svc:
        svc.get_confirmation_actions.return_value = []
        svc.pipeline_run.return_value = _result([_step(1, True)])
        out = runner.invoke(app, ["run", "p", "--notebook", "nb-1"])

    assert out.exit_code == 0


def test_studio_pipeline_aborts_without_confirmation():
    with patch(GET_CLIENT), patch(SVC) as svc:
        svc.get_confirmation_actions.return_value = ["studio_create"]
        out = runner.invoke(app, ["run", "p", "--notebook", "nb-1"], input="\n")

    assert out.exit_code != 0
    svc.pipeline_run.assert_not_called()


def test_confirm_flag_skips_prompt_and_is_forwarded():
    with patch(GET_CLIENT), patch(SVC) as svc:
        svc.get_confirmation_actions.return_value = ["studio_create"]
        svc.pipeline_run.return_value = _result([_step(1, True)])
        out = runner.invoke(app, ["run", "p", "--notebook", "nb-1", "-y"])

    assert out.exit_code == 0
    assert svc.pipeline_run.call_args.kwargs["confirm"] is True


def test_interactive_yes_is_forwarded_as_confirm():
    with patch(GET_CLIENT), patch(SVC) as svc:
        svc.get_confirmation_actions.return_value = ["notebook_delete"]
        svc.pipeline_run.return_value = _result([_step(1, True)])
        out = runner.invoke(app, ["run", "p", "--notebook", "nb-1"], input="y\n")

    assert out.exit_code == 0
    assert svc.pipeline_run.call_args.kwargs["confirm"] is True
