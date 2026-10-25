"""Run privacy-conscious, read-only checks against the configured MCP server."""

import argparse
import asyncio
from datetime import datetime, timezone
from getpass import getpass
import json
import math
from pathlib import Path
import statistics
import time

import httpx
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from agent.graph import create_agent
from core.config import settings


READ_ONLY_TOOL_NAMES = {
    "get_my_leave_balance",
    "get_my_manager",
}
CASES = (
    {
        "id": "my-leave-balance",
        "prompt": "Show my leave balance.",
        "expected_tool": "get_my_leave_balance",
    },
    {
        "id": "my-manager",
        "prompt": "Who is my manager?",
        "expected_tool": "get_my_manager",
    },
)
DEFAULT_REPORT_DIRECTORY = Path(__file__).with_name("reports")


class RecordingReadOnlySession:
    """Record tool execution without capturing tool results or arguments."""

    def __init__(self, session):
        self.session = session
        self.executed_tool_names = []

    async def call_tool(self, name: str, arguments: dict):
        self.executed_tool_names.append(name)
        return await self.session.call_tool(name, arguments=arguments)


def score_case(
    expected_tool: str,
    tool_calls: list[dict],
    executed_tool_names: list[str],
    tool_errors: int,
    has_final_reply: bool,
    latency_seconds: float,
) -> dict:
    """Score tool choice and execution without including private response data."""
    actual_names = [call["name"] for call in tool_calls]
    expected_call = [{"name": expected_tool, "args": {}}]
    call_accuracy = float(
        [
            {"name": call["name"], "args": call["args"]}
            for call in tool_calls
        ]
        == expected_call
    )
    successful_task = (
        actual_names == [expected_tool]
        and tool_errors == 0
        and has_final_reply
    )

    return {
        "tool_selection_accuracy": float(actual_names == [expected_tool]),
        "argument_accuracy": call_accuracy,
        "tool_call_accuracy": call_accuracy,
        "task_completion": float(successful_task),
        "trajectory_accuracy": float(
            successful_task and executed_tool_names == [expected_tool]
        ),
        "unauthorized_tool_attempts": sum(
            name not in READ_ONLY_TOOL_NAMES for name in actual_names
        ),
        "authorization_bypasses": sum(
            name not in READ_ONLY_TOOL_NAMES
            for name in executed_tool_names
        ),
        "tool_errors": tool_errors,
        "latency_seconds": latency_seconds,
    }


async def _run_case(session, tools, case: dict) -> dict:
    recording_session = RecordingReadOnlySession(session)
    agent = create_agent(
        mcp_session=recording_session,
        mcp_tools=tools,
    )

    started_at = time.perf_counter()
    result = await agent.ainvoke(
        {"messages": [HumanMessage(content=case["prompt"])]},
        config={"recursion_limit": 12},
    )
    latency_seconds = time.perf_counter() - started_at
    messages = result["messages"]
    tool_calls = [
        {"name": call["name"], "args": call["args"]}
        for message in messages
        if isinstance(message, AIMessage)
        for call in message.tool_calls
    ]
    tool_messages = [
        message
        for message in messages
        if isinstance(message, ToolMessage)
    ]
    has_final_reply = bool(
        messages
        and isinstance(messages[-1], AIMessage)
        and isinstance(messages[-1].content, str)
        and messages[-1].content.strip()
        and not messages[-1].tool_calls
    )
    errors = sum(message.status == "error" for message in tool_messages)

    return score_case(
        expected_tool=case["expected_tool"],
        tool_calls=tool_calls,
        executed_tool_names=recording_session.executed_tool_names,
        tool_errors=errors,
        has_final_reply=has_final_reply,
        latency_seconds=latency_seconds,
    )


def _summarize_cases(case_results: list[dict]) -> dict:
    metric_names = (
        "tool_selection_accuracy",
        "argument_accuracy",
        "tool_call_accuracy",
        "task_completion",
        "trajectory_accuracy",
    )
    summary = {
        name: round(
            statistics.mean(result[name] for result in case_results),
            4,
        )
        for name in metric_names
    }
    latencies = sorted(result["latency_seconds"] for result in case_results)
    summary["mean_latency_seconds"] = round(statistics.mean(latencies), 4)
    summary["p95_latency_seconds"] = round(
        latencies[max(0, math.ceil(len(latencies) * 0.95) - 1)],
        4,
    )
    summary["unauthorized_tool_attempts"] = sum(
        result["unauthorized_tool_attempts"]
        for result in case_results
    )
    summary["authorization_bypasses"] = sum(
        result["authorization_bypasses"]
        for result in case_results
    )
    summary["tool_errors"] = sum(
        result["tool_errors"]
        for result in case_results
    )
    return summary


def _write_report(
    report_directory: Path,
    model_name: str,
    case_results: list[dict],
) -> Path:
    report_directory.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc)
    report_path = report_directory / (
        f"real_mcp_eval_{timestamp.strftime('%Y%m%dT%H%M%SZ')}.md"
    )
    summary = _summarize_cases(case_results)

    lines = [
        "# Read-only MCP Evaluation Report",
        "",
        f"**Run time (UTC):** {timestamp.isoformat()}  ",
        f"**Model:** `{model_name}`  ",
        f"**Cases:** {len(case_results)}  ",
        "**Data handling:** Personal tool results, assistant replies, "
        "credentials, and employee identifiers are not included.",
        "",
        "> This run tests the configured MCP endpoint. It does not verify "
        "whether that endpoint is connected to a production database.",
        "",
        "## Results",
        "",
        "| Metric | Result |",
        "|---|---:|",
    ]
    for name, value in summary.items():
        lines.append(f"| {name.replace('_', ' ').title()} | {value} |")

    lines.extend(
        [
            "",
            "## Cases",
            "",
            "| Case | Tool selection | Arguments | Tool call | Completion | "
            "Errors | Latency (s) |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for case, result in zip(CASES, case_results):
        lines.append(
            f"| {case['id']} "
            f"| {result['tool_selection_accuracy']:.0%} "
            f"| {result['argument_accuracy']:.0%} "
            f"| {result['tool_call_accuracy']:.0%} "
            f"| {result['task_completion']:.0%} "
            f"| {result['tool_errors']} "
            f"| {result['latency_seconds']:.4f} |"
        )

    lines.extend(
        [
            "",
            "## Scope and limitations",
            "",
            "- Only the authenticated user's leave-balance and manager lookup "
            "tools are exposed to the agent.",
            "- No leave applications, approvals, employee updates, or other "
            "write operations are available in this evaluation.",
            "- MCP authorization is still enforced by the server; this report "
            "does not prove authorization bypasses are impossible.",
            "- Groundedness is not independently judged, and no employee data "
            "is stored in this report.",
            "- Authorization bypasses and tool errors are observations from "
            "this run, not proof of their absence in all cases.",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


async def run_evaluation(
    token: str,
    report_directory: Path = DEFAULT_REPORT_DIRECTORY,
) -> Path:
    """Run only the two own-account, read-only checks against configured MCP."""
    if not token.strip():
        raise ValueError("A test access token is required.")

    headers = {"Authorization": f"Bearer {token.strip()}"}
    async with httpx.AsyncClient(
        headers=headers,
        timeout=httpx.Timeout(60, connect=20),
    ) as http_client:
        async with streamable_http_client(
            settings.MCP_SERVER_URL,
            http_client=http_client,
        ) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                discovered_tools = (await session.list_tools()).tools
                tools_by_name = {
                    tool.name: tool
                    for tool in discovered_tools
                    if tool.name in READ_ONLY_TOOL_NAMES
                }

                missing_tools = READ_ONLY_TOOL_NAMES - tools_by_name.keys()
                if missing_tools:
                    missing_names = ", ".join(sorted(missing_tools))
                    raise RuntimeError(
                        f"The MCP server is missing required read-only tools: "
                        f"{missing_names}"
                    )

                results = []
                for case in CASES:
                    allowed_tools = [
                        tools_by_name[name]
                        for name in READ_ONLY_TOOL_NAMES
                        if name in tools_by_name
                    ]
                    results.append(
                        await _run_case(session, allowed_tools, case)
                    )

    return _write_report(
        report_directory=report_directory,
        model_name=settings.ollama_model,
        case_results=results,
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate the configured MCP server using only read-only "
            "lookups for the authenticated user."
        )
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=DEFAULT_REPORT_DIRECTORY,
        help="Where to write the privacy-conscious Markdown report.",
    )
    args = parser.parse_args()

    token = getpass("Enter a short-lived test JWT (input hidden): ").strip()
    report_path = asyncio.run(
        run_evaluation(token, report_directory=args.report_dir)
    )
    print(f"Read-only evaluation finished. Report saved to: {report_path}")


if __name__ == "__main__":
    main()
