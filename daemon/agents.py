from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sessions import SessionManager


CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"


@dataclass(frozen=True)
class AgentConfig:
    id: str
    name: str
    command: list[str]
    cwd: str | None = None

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "command": self.command,
            "cwd": self.cwd,
        }


class AgentManager:
    def __init__(self, sessions: SessionManager, config_path: Path = CONFIG_PATH) -> None:
        self._sessions = sessions
        self._config_path = config_path
        self._agents = self._load_config(config_path)
        self._agent_sessions: dict[str, int] = {}

    def list(self) -> list[dict[str, Any]]:
        return [self._snapshot(agent) for agent in self._agents.values()]

    def get(self, agent_id: str) -> dict[str, Any]:
        agent = self._require_agent(agent_id)
        return self._snapshot(agent)

    def start(self, agent_id: str) -> dict[str, Any]:
        agent = self._require_agent(agent_id)
        existing_id = self._agent_sessions.get(agent_id)
        if existing_id is not None:
            existing = self._sessions.get(existing_id)
            if existing is not None and existing["running"]:
                return self._snapshot(agent)

        session = self._sessions.start(agent.name, agent.command, agent.cwd)
        self._agent_sessions[agent_id] = session["id"]
        return self._snapshot(agent)

    def send(self, agent_id: str, text: str) -> dict[str, Any]:
        session_id = self._require_running_session(agent_id)
        self._sessions.send(session_id, text)
        return self.get(agent_id)

    def continue_agent(self, agent_id: str) -> dict[str, Any]:
        session_id = self._require_running_session(agent_id)
        self._sessions.continue_session(session_id)
        return self.get(agent_id)

    def stop(self, agent_id: str) -> dict[str, Any]:
        session_id = self._require_running_session(agent_id)
        self._sessions.stop(session_id)
        return self.get(agent_id)

    def _snapshot(self, agent: AgentConfig) -> dict[str, Any]:
        session_id = self._agent_sessions.get(agent.id)
        session = self._sessions.get(session_id) if session_id is not None else None
        return {
            **agent.public(),
            "session_id": session_id,
            "session": session,
            "running": bool(session and session["running"]),
        }

    def _require_agent(self, agent_id: str) -> AgentConfig:
        agent = self._agents.get(agent_id)
        if agent is None:
            raise KeyError(f"unknown agent id: {agent_id}")
        return agent

    def _require_running_session(self, agent_id: str) -> int:
        self._require_agent(agent_id)
        session_id = self._agent_sessions.get(agent_id)
        if session_id is None:
            raise RuntimeError("agent is not started")
        session = self._sessions.get(session_id)
        if session is None or not session["running"]:
            raise RuntimeError("agent session is not running")
        return session_id

    def _load_config(self, path: Path) -> dict[str, AgentConfig]:
        if not path.exists():
            return {}

        data = json.loads(path.read_text(encoding="utf-8"))
        raw_agents = data.get("agents", [])
        if not isinstance(raw_agents, list):
            raise ValueError("config agents must be a list")

        agents: dict[str, AgentConfig] = {}
        for item in raw_agents:
            if not isinstance(item, dict):
                raise ValueError("agent config entries must be objects")
            agent_id = item.get("id")
            name = item.get("name")
            command = item.get("command")
            cwd = item.get("cwd")
            if not isinstance(agent_id, str) or not agent_id:
                raise ValueError("agent id must be a non-empty string")
            if not isinstance(name, str) or not name:
                raise ValueError(f"agent {agent_id} name must be a non-empty string")
            if not isinstance(command, list) or not all(isinstance(x, str) for x in command):
                raise ValueError(f"agent {agent_id} command must be a list of strings")
            if cwd is not None and not isinstance(cwd, str):
                raise ValueError(f"agent {agent_id} cwd must be a string or null")
            agents[agent_id] = AgentConfig(agent_id, name, command, cwd)
        return agents

