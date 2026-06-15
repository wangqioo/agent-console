from __future__ import annotations

import subprocess
import threading
from collections import deque
from dataclasses import dataclass, field
from itertools import count
from typing import Any


MAX_OUTPUT_LINES = 200


@dataclass
class Session:
    id: int
    name: str
    command: list[str]
    cwd: str | None
    process: subprocess.Popen[str]
    output: deque[str] = field(default_factory=lambda: deque(maxlen=MAX_OUTPUT_LINES))

    def snapshot(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "command": self.command,
            "cwd": self.cwd,
            "running": self.process.poll() is None,
            "returncode": self.process.poll(),
            "recent_output": list(self.output),
        }


class SessionManager:
    def __init__(self) -> None:
        self._ids = count(1)
        self._lock = threading.Lock()
        self._sessions: dict[int, Session] = {}

    def list(self) -> list[dict[str, Any]]:
        with self._lock:
            return [session.snapshot() for session in self._sessions.values()]

    def get(self, session_id: int) -> dict[str, Any] | None:
        with self._lock:
            session = self._sessions.get(session_id)
            return session.snapshot() if session else None

    def start(self, name: str, command: list[str], cwd: str | None = None) -> dict[str, Any]:
        if not command:
            raise ValueError("command must not be empty")

        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        session = Session(next(self._ids), name, command, cwd, process)

        with self._lock:
            self._sessions[session.id] = session

        thread = threading.Thread(target=self._read_output, args=(session,), daemon=True)
        thread.start()
        return session.snapshot()

    def send(self, session_id: int, text: str) -> dict[str, Any]:
        session = self._require_session(session_id)
        if session.process.poll() is not None:
            raise RuntimeError("session is not running")
        if session.process.stdin is None:
            raise RuntimeError("session stdin is unavailable")
        session.process.stdin.write(text)
        session.process.stdin.flush()
        return session.snapshot()

    def continue_session(self, session_id: int) -> dict[str, Any]:
        return self.send(session_id, "\n")

    def stop(self, session_id: int) -> dict[str, Any]:
        session = self._require_session(session_id)
        if session.process.poll() is None:
            session.process.terminate()
        return session.snapshot()

    def _require_session(self, session_id: int) -> Session:
        with self._lock:
            session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(f"unknown session id: {session_id}")
        return session

    def _read_output(self, session: Session) -> None:
        if session.process.stdout is None:
            return
        for line in session.process.stdout:
            session.output.append(line.rstrip("\n"))
