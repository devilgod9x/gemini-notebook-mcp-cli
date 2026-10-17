"""Pipeline tools — consolidated tool for multi-step notebook workflows."""

from ...services import pipeline as pipeline_service
from ...services.errors import ServiceError
from ._utils import ResultDict, error_result, get_client, logged_tool


@logged_tool()
def pipeline(
    action: str,
    notebook_id: str | None = None,
    pipeline_name: str | None = None,
    input_url: str = "",
    description: str = "",
    steps: list[dict] | None = None,
    confirm: bool = False,
) -> ResultDict:
    """Manage and execute multi-step notebook pipelines.

    Actions:
    - run: Execute a pipeline on a notebook. Pipelines with notebook_delete
      (IRREVERSIBLE) or studio_create (uses Studio quota) steps require
      confirm=True; show the user the steps first
    - list: List all available pipelines (builtin and user-defined)
    - create: Save a user-defined pipeline (pipeline_name + steps; each step is
      {"action": <tool name>, "params": {...}})

    Args:
        action: Operation to perform (run, list, create)
        notebook_id: Target notebook UUID (required for action=run)
        pipeline_name: Pipeline name (required for action=run, e.g. "ingest-and-podcast")
        input_url: URL variable for pipelines that need it (replaces $INPUT_URL)
        description: Pipeline description (for action=create)
        steps: Step definitions (required for action=create)
        confirm: Must be True for action=run when the pipeline deletes a notebook
            or creates Studio artifacts
    """
    try:
        if action == "run":
            if not notebook_id:
                return {"status": "error", "error": "notebook_id is required for action=run"}
            if not pipeline_name:
                return error_result("pipeline_name is required for action=run")
            client = get_client()
            variables: dict[str, str] = {}
            if input_url:
                variables["INPUT_URL"] = input_url
            result = pipeline_service.pipeline_run(
                client, notebook_id, pipeline_name, variables, confirm=confirm
            )
            # The service reports step failures in the result instead of raising,
            # so derive the overall status here: callers (agents, schedulers) must
            # not treat a half-finished pipeline as success.
            if result["failed"] == 0:
                status = "success"
            elif result["succeeded"] > 0:
                status = "partial"
            else:
                status = "error"
            if status == "success":
                return {"status": status, **result}
            failed_step = next(s for s in result["steps"] if not s["success"])
            return {
                "status": status,
                "error": f"Step {failed_step['step']} ({failed_step['action']}) failed: "
                f"{failed_step['error']}",
                **result,
            }

        elif action == "list":
            pipelines = pipeline_service.pipeline_list()
            return {
                "status": "success",
                "pipelines": pipelines,
                "count": len(pipelines),
            }

        elif action == "create":
            if not pipeline_name:
                return error_result("pipeline_name is required for action=create")
            if not steps:
                return error_result("steps is required for action=create")
            result = pipeline_service.pipeline_create(pipeline_name, description, steps)
            return {"status": "success", **result}

        else:
            return error_result(f"Unknown action: {action}. Use: run, list, create")

    except ServiceError as e:
        return error_result(e.user_message, hint=e.hint)
    except Exception as e:
        return error_result(str(e))
