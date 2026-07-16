#!/usr/bin/env python3
"""Run Armada agent instructions with sliding-window OpenCode workers on macOS."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import signal
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


ARMADA_DIR = Path(os.environ.get("ARMADA_DIR", "~/armada")).expanduser()
RESULTS_DIR = ARMADA_DIR / "run-results"
DEFAULT_MCP_URL = "https://custodian.lamannalogistics.com/mcp"
DEFAULT_MCP_AUTH_PATH = Path("~/.local/share/opencode/mcp-auth.json").expanduser()
DEFAULT_OPENCODE_BIN = Path.home() / ".opencode" / "bin" / "opencode"
TERMINAL_STATUSES = {"executed", "failed"}
PENDING_STATUSES = {"submitted", "open"}
TIME_SCALE = 0.001
SUCCESS_RATE = 1.0
RANDOM_SEED = 188


@dataclass
class Instruction:
    id: str
    agent_name: str
    status: str = "open"
    duration: float | None = None
    success: bool = True
    model_override: str | None = None


@dataclass
class WorkerState:
    instruction: Instruction
    worker_id: int
    started_at: float
    process: asyncio.subprocess.Process | None = None
    log_path: Path | None = None


@dataclass
class RunStats:
    started_at: float = field(default_factory=time.perf_counter)
    events: list[dict[str, Any]] = field(default_factory=list)
    completed: int = 0
    failed: int = 0


class CustodianMcpClient:
    def __init__(self, url: str, auth_path: Path, timeout: float) -> None:
        self.url = url
        self.auth_path = auth_path
        self.timeout = timeout
        self.session_id: str | None = None
        self._access_token: str | None = None

    def _load_access_token(self) -> str:
        if os.environ.get("CUSTODIAN_MCP_TOKEN"):
            return str(os.environ["CUSTODIAN_MCP_TOKEN"])
        if self._access_token:
            return self._access_token
        data = json.loads(self.auth_path.read_text(encoding="utf-8"))
        for entry in data.values():
            token = entry.get("tokens", {}).get("accessToken")
            if token:
                self._access_token = str(token)
                return self._access_token
        raise RuntimeError(f"No Custodian MCP access token found in {self.auth_path}")

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._load_access_token()}",
            "User-Agent": "armada-orchestrator/1.0",
        }
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        return headers

    @staticmethod
    def _parse_response(text: str) -> dict[str, Any] | None:
        if not text.strip():
            return None

        messages: list[dict[str, Any]] = []
        data_lines: list[str] = []
        for line in text.splitlines():
            if line.startswith("data:"):
                data_lines.append(line[5:].strip())
            elif not line.strip() and data_lines:
                messages.append(json.loads("\n".join(data_lines)))
                data_lines = []
        if data_lines:
            messages.append(json.loads("\n".join(data_lines)))
        if messages:
            return messages[-1]

        return json.loads(text)

    def _post(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        for attempt in range(2):
            request = urllib.request.Request(
                self.url,
                data=json.dumps(payload).encode("utf-8"),
                headers=self._headers(),
                method="POST",
            )
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    session_id = response.headers.get("Mcp-Session-Id")
                    if session_id:
                        self.session_id = session_id
                    return self._parse_response(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                if exc.code == 401 and attempt == 0:
                    # Token expired: clear cached auth/session state and retry once.
                    self._access_token = None
                    self.session_id = None
                    continue
                detail = exc.read().decode("utf-8", errors="replace")[:1000]
                raise RuntimeError(f"Custodian MCP HTTP {exc.code}: {detail}") from exc
        return None

    def initialize(self) -> None:
        if self.session_id:
            return
        response = self._post(
            {
                "jsonrpc": "2.0",
                "id": "armada-orchestrator-init",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "armada-orchestrator", "version": "1.0"},
                },
            }
        )
        if response and response.get("error"):
            raise RuntimeError(f"Custodian MCP initialize failed: {response['error']}")
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})

    def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        self.initialize()
        response = self._post(
            {
                "jsonrpc": "2.0",
                "id": f"armada-orchestrator-{int(time.time() * 1000)}",
                "method": "tools/call",
                "params": {"name": name, "arguments": arguments},
            }
        )
        if not response:
            return None
        if response.get("error"):
            raise RuntimeError(f"Custodian MCP tool {name} failed: {response['error']}")

        result = response.get("result")
        if isinstance(result, dict) and "content" in result:
            content = result.get("content") or []
            if content and content[0].get("type") == "text":
                text = str(content[0].get("text") or "")
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return text
        return result


def read_node_name() -> str:
    node_file = Path("~/.armada-node").expanduser()
    if node_file.exists():
        value = node_file.read_text(encoding="utf-8").strip()
        if value:
            return value
    return os.environ.get("ARMADA_NODE_NAME", "macbook")


def make_client(args: argparse.Namespace) -> CustodianMcpClient:
    return CustodianMcpClient(args.mcp_url, args.mcp_auth_path, args.mcp_timeout)


def load_dispatch_instructions(client: CustodianMcpClient, node: str, dispatch_id: str) -> list[Instruction]:
    data = client.call_tool(
        "armada_get_node_instructions",
        {"node": node, "dispatch_id": dispatch_id, "override_governance": False},
    )
    rows = data.get("instructions", []) if isinstance(data, dict) else []
    instructions: list[Instruction] = []
    for row in rows:
        status = str(row.get("status") or "open")
        if status not in PENDING_STATUSES:
            continue
        agent_name = row.get("agent_name") or row.get("agent") or row.get("agentName")
        if not agent_name:
            raise RuntimeError(f"Instruction {row.get('id')} did not include an agent name")
        model_override = row.get("model_override") or row.get("model") or None
        instructions.append(
            Instruction(
                id=str(row["id"]),
                agent_name=str(agent_name),
                status=status,
                model_override=str(model_override) if model_override else None,
            )
        )
    return instructions


def make_test_workload(count: int) -> list[Instruction]:
    rng = random.Random(RANDOM_SEED)
    instructions = []
    for index in range(1, count + 1):
        if index == 1:
            duration = 10.0
        elif index == 2:
            duration = 30.0
        else:
            duration = rng.uniform(10, 25)
        instructions.append(
            Instruction(
                id=f"AI-TEST-{index:03d}",
                agent_name="mock-worker",
                duration=duration,
                success=rng.random() < SUCCESS_RATE,
            )
        )
    return instructions


def get_instruction_status(client: CustodianMcpClient, ai_id: str) -> str | None:
    data = client.call_tool("get_agent_instruction", {"ai_id": ai_id, "override_governance": False})
    if isinstance(data, dict):
        status = data.get("status")
        return str(status) if status else None
    return None


async def run_mock_worker(instruction: Instruction, run_started_at: float) -> dict[str, Any]:
    start_offset = (time.perf_counter() - run_started_at) / TIME_SCALE
    duration = float(instruction.duration or 0)
    await asyncio.sleep(duration * TIME_SCALE)
    end_offset = (time.perf_counter() - run_started_at) / TIME_SCALE
    return {
        "instruction_id": instruction.id,
        "agent_name": instruction.agent_name,
        "pid": None,
        "started_at": start_offset,
        "ended_at": end_offset,
        "duration": duration,
        "result": "executed" if instruction.success else "failed",
        "source": "mock",
    }


async def spawn_opencode_worker(
    instruction: Instruction,
    opencode_bin: str,
    log_path: Path,
) -> asyncio.subprocess.Process:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = log_path.open("wb")

    cmd = [
        opencode_bin,
        "run",
        f"execute {instruction.id}",
        "--agent",
        "brand-outreach-worker-cli",
        "--dangerously-skip-permissions",
    ]
    if instruction.model_override:
        cmd.extend(["--model", instruction.model_override])

    env = os.environ.copy()
    env["BROWSER_USE_HEADLESS"] = "true"

    try:
        return await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(Path.home()),
            stdout=log_file,
            stderr=asyncio.subprocess.STDOUT,
            env=env,
        )
    finally:
        log_file.close()


async def stop_process(process: asyncio.subprocess.Process) -> None:
    if process.returncode is not None:
        return
    try:
        process.send_signal(signal.SIGTERM)
        await asyncio.wait_for(process.wait(), timeout=5)
    except ProcessLookupError:
        return
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()


async def wait_for_real_completion(
    client: CustodianMcpClient,
    state: WorkerState,
    poll_interval: float,
    timeout: float,
    opencode_bin: str,
    consecutive_mcp_failures: list[int],
) -> dict[str, Any]:
    instruction = state.instruction
    safe_ai_id = instruction.id.replace("/", "_")
    state.log_path = RESULTS_DIR / f"{safe_ai_id}.worker.log"
    process = await spawn_opencode_worker(instruction, opencode_bin, state.log_path)
    state.process = process
    start_time = state.started_at
    deadline = start_time + timeout

    while True:
        now = time.perf_counter()
        if now >= deadline:
            await stop_process(process)
            return build_event(instruction, process, start_time, "failed", "timeout", state.log_path)

        if process.returncode is not None:
            await process.wait()
            status = get_instruction_status(client, instruction.id)
            if status not in TERMINAL_STATUSES:
                status = "failed"
            return build_event(instruction, process, start_time, status, "process_exit", state.log_path)

        try:
            status = get_instruction_status(client, instruction.id)
            consecutive_mcp_failures[0] = 0
        except Exception as exc:
            consecutive_mcp_failures[0] += 1
            if consecutive_mcp_failures[0] >= 5:
                await stop_process(process)
                raise RuntimeError("Custodian MCP polling failed 5 consecutive times") from exc
            await asyncio.sleep(min(poll_interval * consecutive_mcp_failures[0], 60))
            continue

        if status in TERMINAL_STATUSES:
            if process.returncode is None:
                await stop_process(process)
            return build_event(instruction, process, start_time, status, "mcp_status", state.log_path)

        await asyncio.sleep(poll_interval)


def build_event(
    instruction: Instruction,
    process: asyncio.subprocess.Process | None,
    started_at: float,
    result: str,
    source: str,
    log_path: Path | None = None,
) -> dict[str, Any]:
    ended_at = time.perf_counter()
    event = {
        "instruction_id": instruction.id,
        "agent_name": instruction.agent_name,
        "pid": process.pid if process else None,
        "started_at": started_at,
        "ended_at": ended_at,
        "duration": ended_at - started_at,
        "result": result,
        "source": source,
    }
    if process:
        event["returncode"] = process.returncode
    if log_path:
        event["log_path"] = str(log_path)
    return event


async def run_instruction(
    client: CustodianMcpClient | None,
    instruction: Instruction,
    worker_id: int,
    args: argparse.Namespace,
    stats: RunStats,
    mcp_failures: list[int],
) -> dict[str, Any]:
    print(f"[{worker_id}] dispatch {instruction.id} ({instruction.agent_name})", flush=True)
    state = WorkerState(instruction=instruction, worker_id=worker_id, started_at=time.perf_counter())
    if args.test:
        event = await run_mock_worker(instruction, stats.started_at)
    else:
        if client is None:
            raise RuntimeError("Custodian client is required outside --test mode")
        event = await wait_for_real_completion(
            client,
            state,
            args.poll_interval,
            args.timeout,
            args.opencode_bin,
            mcp_failures,
        )

    if event["result"] == "executed":
        stats.completed += 1
    else:
        stats.failed += 1
    stats.events.append(event)
    print(f"[{worker_id}] complete {instruction.id}: {event['result']} in {event['duration']:.1f}s", flush=True)
    return event


async def run_sliding(
    client: CustodianMcpClient | None,
    instructions: list[Instruction],
    args: argparse.Namespace,
) -> RunStats:
    stats = RunStats()
    mcp_failures = [0]
    pending = list(instructions)
    active: set[asyncio.Task[dict[str, Any]]] = set()
    worker_ids = list(range(1, args.concurrency + 1))
    task_workers: dict[asyncio.Task[dict[str, Any]], int] = {}

    while pending or active:
        while pending and len(active) < args.concurrency:
            worker_id = worker_ids.pop(0) if worker_ids else len(active) + 1
            task = asyncio.create_task(run_instruction(client, pending.pop(0), worker_id, args, stats, mcp_failures))
            active.add(task)
            task_workers[task] = worker_id

        done, active = await asyncio.wait(active, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            worker_ids.append(task_workers.pop(task))
            task.result()

    return stats


async def run_batch(
    client: CustodianMcpClient | None,
    instructions: list[Instruction],
    args: argparse.Namespace,
) -> RunStats:
    stats = RunStats()
    mcp_failures = [0]
    for start in range(0, len(instructions), args.concurrency):
        chunk = instructions[start : start + args.concurrency]
        tasks = [
            asyncio.create_task(run_instruction(client, instruction, worker_id, args, stats, mcp_failures))
            for worker_id, instruction in enumerate(chunk, start=1)
        ]
        await asyncio.gather(*tasks)
    return stats


def summarize(mode: str, concurrency: int, instructions: list[Instruction], stats: RunStats) -> dict[str, Any]:
    elapsed = time.perf_counter() - stats.started_at
    if instructions and all(instruction.duration is not None for instruction in instructions):
        total_work = sum(float(instruction.duration or 0) for instruction in instructions)
        reported_elapsed = elapsed / TIME_SCALE
        utilization = total_work / (concurrency * reported_elapsed) * 100 if reported_elapsed else 0.0
        throughput = len(stats.events) / (reported_elapsed / 60) if reported_elapsed else 0.0
    else:
        reported_elapsed = elapsed
        utilization = None
        throughput = len(stats.events) / (elapsed / 60) if elapsed else 0.0

    return {
        "mode": mode,
        "concurrency": concurrency,
        "instruction_count": len(instructions),
        "total_elapsed": reported_elapsed,
        "throughput_per_min": throughput,
        "utilization_pct": utilization,
        "completed": stats.completed,
        "failed": stats.failed,
        "events": sorted(stats.events, key=lambda event: str(event["instruction_id"])),
    }


def write_results(summary: dict[str, Any], dispatch_id: str | None) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    name = dispatch_id or "test"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = RESULTS_DIR / f"{name}-{summary['mode']}-{timestamp}.json"
    path.write_text(json.dumps(summary, indent=2, default=str) + "\n", encoding="utf-8")
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dispatch-id", help="Armada dispatch ID to run")
    parser.add_argument("--node", default=read_node_name(), help="Armada node name")
    parser.add_argument("--concurrency", type=int, default=8, help="worker slots to keep full")
    parser.add_argument("--timeout", type=float, default=600, help="per-worker timeout in seconds")
    parser.add_argument("--poll-interval", type=float, default=10, help="Custodian MCP poll interval in seconds")
    parser.add_argument("--mode", choices=("sliding", "batch"), default="sliding")
    parser.add_argument("--test", action="store_true", help="run mock workers instead of OpenCode")
    parser.add_argument("--count", type=int, default=10, help="mock instruction count")
    parser.add_argument("--mcp-url", default=os.environ.get("CUSTODIAN_MCP_URL", DEFAULT_MCP_URL))
    parser.add_argument("--mcp-auth-path", type=Path, default=DEFAULT_MCP_AUTH_PATH)
    parser.add_argument("--mcp-timeout", type=float, default=30)
    parser.add_argument("--opencode-bin", default=os.environ.get("OPENCODE_BIN", str(DEFAULT_OPENCODE_BIN)))
    args = parser.parse_args()
    if args.concurrency < 1:
        parser.error("--concurrency must be >= 1")
    if not args.test and not args.dispatch_id:
        parser.error("--dispatch-id is required unless --test is set")
    return args


async def async_main() -> int:
    args = parse_args()
    client: CustodianMcpClient | None = None
    if args.test:
        instructions = make_test_workload(args.count)
    else:
        if not Path(args.opencode_bin).exists():
            print(f"OpenCode CLI not found: {args.opencode_bin}", file=sys.stderr)
            return 1
        client = make_client(args)
        instructions = load_dispatch_instructions(client, args.node, args.dispatch_id)

    if not instructions:
        print("No pending instructions found.", file=sys.stderr)
        return 1

    runner = run_sliding if args.mode == "sliding" else run_batch
    stats = await runner(client, instructions, args)
    summary = summarize(args.mode, args.concurrency, instructions, stats)
    results_path = write_results(summary, args.dispatch_id)

    print("\nRun summary")
    print(f"  mode: {summary['mode']}")
    print(f"  instructions: {summary['instruction_count']}")
    print(f"  completed: {summary['completed']}")
    print(f"  failed: {summary['failed']}")
    print(f"  elapsed: {summary['total_elapsed']:.1f}s")
    print(f"  throughput: {summary['throughput_per_min']:.2f}/m")
    print(f"  results: {results_path}")
    return 0 if summary["failed"] == 0 else 2


def main() -> None:
    raise SystemExit(asyncio.run(async_main()))


if __name__ == "__main__":
    main()
