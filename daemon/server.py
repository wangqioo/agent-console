from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from agents import AgentManager
from sessions import SessionManager
from status import get_provider_status


HOST = "127.0.0.1"
PORT = 8765

sessions = SessionManager()
agents = AgentManager(sessions)


class ApiError(Exception):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self._dispatch("GET")

    def do_POST(self) -> None:
        self._dispatch("POST")

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _dispatch(self, method: str) -> None:
        try:
            result = self._handle(method, urlparse(self.path).path)
            self._send_json(200, result)
        except ApiError as exc:
            self._send_json(exc.status, {"error": exc.message})
        except Exception as exc:
            self._send_json(500, {"error": str(exc)})

    def _handle(self, method: str, path: str) -> dict[str, Any] | list[Any]:
        if method == "GET" and path == "/api/providers/status":
            return get_provider_status()

        if method == "GET" and path == "/api/sessions":
            return {"sessions": sessions.list()}

        if method == "GET" and path == "/api/agents":
            return {"agents": agents.list()}

        if method == "POST" and path == "/api/sessions/start":
            body = self._read_json()
            command = body.get("command")
            if not isinstance(command, list) or not all(isinstance(x, str) for x in command):
                raise ApiError(400, "command must be a list of strings")
            name = body.get("name") or command[0]
            if not isinstance(name, str):
                raise ApiError(400, "name must be a string")
            cwd = body.get("cwd")
            if cwd is not None and not isinstance(cwd, str):
                raise ApiError(400, "cwd must be a string")
            return sessions.start(name, command, cwd)

        parts = path.strip("/").split("/")
        if len(parts) == 3 and parts[:2] == ["api", "sessions"] and method == "GET":
            session_id = self._parse_id(parts[2])
            snapshot = sessions.get(session_id)
            if snapshot is None:
                raise ApiError(404, "session not found")
            return snapshot

        if len(parts) == 4 and parts[:2] == ["api", "sessions"] and method == "POST":
            session_id = self._parse_id(parts[2])
            action = parts[3]
            try:
                if action == "send":
                    body = self._read_json()
                    text = body.get("text")
                    if not isinstance(text, str):
                        raise ApiError(400, "text must be a string")
                    return sessions.send(session_id, text)
                if action == "continue":
                    return sessions.continue_session(session_id)
                if action == "stop":
                    return sessions.stop(session_id)
            except KeyError:
                raise ApiError(404, "session not found")
            except RuntimeError as exc:
                raise ApiError(409, str(exc))

        if len(parts) == 3 and parts[:2] == ["api", "agents"] and method == "GET":
            agent_id = parts[2]
            try:
                return agents.get(agent_id)
            except KeyError:
                raise ApiError(404, "agent not found")

        if len(parts) == 4 and parts[:2] == ["api", "agents"] and method == "POST":
            agent_id = parts[2]
            action = parts[3]
            try:
                if action == "start":
                    return agents.start(agent_id)
                if action == "send":
                    body = self._read_json()
                    text = body.get("text")
                    if not isinstance(text, str):
                        raise ApiError(400, "text must be a string")
                    return agents.send(agent_id, text)
                if action == "continue":
                    return agents.continue_agent(agent_id)
                if action == "stop":
                    return agents.stop(agent_id)
            except KeyError:
                raise ApiError(404, "agent not found")
            except RuntimeError as exc:
                raise ApiError(409, str(exc))

        raise ApiError(404, "not found")

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ApiError(400, f"invalid json: {exc}")
        if not isinstance(data, dict):
            raise ApiError(400, "json body must be an object")
        return data

    def _send_json(self, status: int, body: dict[str, Any] | list[Any]) -> None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _parse_id(self, value: str) -> int:
        try:
            return int(value)
        except ValueError:
            raise ApiError(400, "session id must be an integer")


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Agent Console daemon listening on http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
