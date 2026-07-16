from __future__ import annotations

import os
import socket
from dataclasses import dataclass
from pathlib import Path


def _env_first(*names: str) -> str:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return ""


def _node_name() -> str:
    if os.environ.get("ARMADA_NODE_NAME"):
        return os.environ["ARMADA_NODE_NAME"]
    node_file = Path("~/.armada-node").expanduser()
    if node_file.exists():
        value = node_file.read_text(encoding="utf-8").strip()
        if value:
            return value
    return socket.gethostname()


@dataclass(frozen=True)
class Settings:
    base_dir: Path
    db_path: Path
    sqld_url: str
    searxng_search_url: str
    search_api_url: str
    search_api_key: str
    cdp_endpoint: str
    postgres_dsn: str
    custodian_mcp_url: str
    custodian_mark_tool: str
    request_timeout_seconds: float
    node_name: str


def get_settings() -> Settings:
    base_dir = Path(os.environ.get("ARMADA_DIR", "~/armada")).expanduser()
    db_path = Path(os.environ.get("ARMADA_NODE_DB_PATH", str(base_dir / "node.db"))).expanduser()
    return Settings(
        base_dir=base_dir,
        db_path=db_path,
        sqld_url=os.environ.get("SQLD_URL", "http://127.0.0.1:8400"),
        searxng_search_url=os.environ.get("SEARXNG_SEARCH_URL", "http://127.0.0.1:8888/search"),
        search_api_url=os.environ.get("SEARCH_API_URL", "https://google.serper.dev/search"),
        search_api_key=_env_first("SEARCH_API_KEY", "SERPER_API_KEY"),
        cdp_endpoint=os.environ.get("ARMADA_CDP_ENDPOINT", "http://127.0.0.1:9222"),
        postgres_dsn=_env_first("FBA_POSTGRES_DSN", "FBA_DATABASE_URL", "POSTGRES_DSN", "DATABASE_URL"),
        custodian_mcp_url=os.environ.get("CUSTODIAN_MCP_URL", "https://custodian.lamannalogistics.com/mcp"),
        custodian_mark_tool=os.environ.get("CUSTODIAN_MARK_TOOL", "mark_agent_instruction_executed"),
        request_timeout_seconds=float(os.environ.get("ARMADA_NODE_REQUEST_TIMEOUT", "30")),
        node_name=_node_name(),
    )
