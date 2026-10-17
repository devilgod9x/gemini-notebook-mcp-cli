from unittest.mock import patch

from notebooklm_tools.mcp.tools import pipeline as pipeline_tool
from notebooklm_tools.services.errors import ValidationError

RUN = "notebooklm_tools.services.pipeline.pipeline_run"
GET_CLIENT = "notebooklm_tools.mcp.tools.pipeline.get_client"


def _step(n: int, ok: bool) -> dict:
    return {
        "step": n,
        "action": "notebook_query",
        "success": ok,
        "result": {} if ok else None,
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


def test_run_all_steps_succeed():
    with patch(GET_CLIENT), patch(RUN, return_value=_result([_step(1, True)])):
        out = pipeline_tool(action="run", notebook_id="nb-1", pipeline_name="p")
    assert out["status"] == "success"


def test_run_failed_step_is_not_reported_as_success():
    with patch(GET_CLIENT), patch(RUN, return_value=_result([_step(1, False)])):
        out = pipeline_tool(action="run", notebook_id="nb-1", pipeline_name="p")
    assert out["status"] == "error"
    assert "API error" in out["error"]
    assert out["failed"] == 1


def test_run_partial_when_some_steps_succeeded():
    steps = [_step(1, True), _step(2, False)]
    with patch(GET_CLIENT), patch(RUN, return_value=_result(steps)):
        out = pipeline_tool(action="run", notebook_id="nb-1", pipeline_name="p")
    assert out["status"] == "partial"
    assert "Step 2" in out["error"]


def test_run_passes_confirm_to_service():
    with patch(GET_CLIENT), patch(RUN, return_value=_result([_step(1, True)])) as run:
        pipeline_tool(action="run", notebook_id="nb-1", pipeline_name="p", confirm=True)
    assert run.call_args.kwargs["confirm"] is True


def test_run_unconfirmed_destructive_pipeline_is_an_error():
    err = ValidationError("needs confirm", user_message="needs confirm=True")
    with patch(GET_CLIENT), patch(RUN, side_effect=err):
        out = pipeline_tool(action="run", notebook_id="nb-1", pipeline_name="p")
    assert out["status"] == "error"
    assert "confirm" in out["error"]
