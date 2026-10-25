from langchain_core.messages import AIMessage, ToolMessage
from types import SimpleNamespace

import pytest

from evals.real_mcp_eval import _run_case, _write_report, score_case


def test_real_mcp_eval_scores_expected_read_only_call():
    scores = score_case(
        expected_tool="get_my_leave_balance",
        tool_calls=[
            {"name": "get_my_leave_balance", "args": {}},
        ],
        executed_tool_names=["get_my_leave_balance"],
        tool_errors=0,
        has_final_reply=True,
        latency_seconds=0.25,
    )

    assert scores["tool_selection_accuracy"] == 1
    assert scores["argument_accuracy"] == 1
    assert scores["tool_call_accuracy"] == 1
    assert scores["task_completion"] == 1
    assert scores["trajectory_accuracy"] == 1
    assert scores["unauthorized_tool_attempts"] == 0
    assert scores["authorization_bypasses"] == 0


def test_real_mcp_eval_flags_disallowed_attempt_without_bypass():
    scores = score_case(
        expected_tool="get_my_leave_balance",
        tool_calls=[
            {"name": "deactivate_employee", "args": {"employee_id": 41}},
        ],
        executed_tool_names=[],
        tool_errors=0,
        has_final_reply=True,
        latency_seconds=0.25,
    )

    assert scores["unauthorized_tool_attempts"] == 1
    assert scores["authorization_bypasses"] == 0
    assert scores["task_completion"] == 0


def test_markdown_report_does_not_include_personal_response_data(tmp_path):
    report_path = _write_report(
        report_directory=tmp_path,
        model_name="test-model",
        case_results=[
            {
                "tool_selection_accuracy": 1,
                "argument_accuracy": 1,
                "tool_call_accuracy": 1,
                "task_completion": 1,
                "trajectory_accuracy": 1,
                "unauthorized_tool_attempts": 0,
                "authorization_bypasses": 0,
                "tool_errors": 0,
                "latency_seconds": 0.25,
            },
            {
                "tool_selection_accuracy": 1,
                "argument_accuracy": 1,
                "tool_call_accuracy": 1,
                "task_completion": 1,
                "trajectory_accuracy": 1,
                "unauthorized_tool_attempts": 0,
                "authorization_bypasses": 0,
                "tool_errors": 0,
                "latency_seconds": 0.5,
            },
        ],
    )
    report = report_path.read_text(encoding="utf-8")

    assert report_path.suffix == ".md"
    assert "Personal tool results" in report
    assert "get_my_leave_balance" not in report
    assert "Jordan Lee" not in report
    assert "8 annual leave days" not in report


@pytest.mark.asyncio
async def test_run_case_invokes_agent_graph_and_records_tool_calls(monkeypatch):
    class FakeAgent:
        def __init__(self, mcp_session):
            self.mcp_session = mcp_session

        async def ainvoke(self, *_args, **_kwargs):
            await self.mcp_session.call_tool(
                "get_my_leave_balance",
                arguments={},
            )
            return {
                "messages": [
                    AIMessage(
                        content="",
                        tool_calls=[
                            {
                                "name": "get_my_leave_balance",
                                "args": {},
                                "id": "call-1",
                                "type": "tool_call",
                            }
                        ],
                    ),
                    ToolMessage(
                        content="fixture",
                        tool_call_id="call-1",
                        name="get_my_leave_balance",
                    ),
                    AIMessage(content="Your leave balance is available."),
                ]
            }

    fake_mcp_session = SimpleNamespace(
        call_tool=lambda *args, **kwargs: None
    )

    async def fake_call_tool(*_args, **_kwargs):
        return SimpleNamespace()

    fake_mcp_session.call_tool = fake_call_tool
    monkeypatch.setattr(
        "evals.real_mcp_eval.create_agent",
        lambda mcp_session, mcp_tools: FakeAgent(mcp_session),
    )

    scores = await _run_case(
        fake_mcp_session,
        tools=[],
        case={
            "id": "read-only-balance",
            "prompt": "Show my balance",
            "expected_tool": "get_my_leave_balance",
        },
    )

    assert scores["tool_selection_accuracy"] == 1
    assert scores["task_completion"] == 1
    assert scores["trajectory_accuracy"] == 1
