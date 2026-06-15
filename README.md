# Agent Desk

Agent Desk is a local daemon prototype for a desktop hardware controller that can
monitor and control Claude Code and Codex CLI sessions.

The first milestone is intentionally small:

- query Claude and OpenAI/Codex service status from public status APIs
- start local CLI sessions
- read recent session output
- send input to a session
- provide a simple `continue` command for a hardware button

## Reference Projects

These two repositories are the primary references for this prototype:

- `graykode/abtop` - https://github.com/graykode/abtop
  - Reference for discovering and monitoring AI coding agent sessions, including
    Claude Code and Codex CLI.
  - Useful ideas: session list, token/context/rate-limit visibility, process and
    port monitoring.
- `alexei-led/ccgram` - https://github.com/alexei-led/ccgram
  - Reference for controlling Claude Code and Codex CLI through terminal
    sessions.
  - Useful ideas: bridge to terminal sessions, monitor output, send replies,
    manage multiple sessions.

## Prototype API

Run the daemon:

```powershell
python .\daemon\server.py
```

Default URL:

```text
http://127.0.0.1:8765
```

Endpoints:

```text
GET  /api/providers/status
GET  /api/agents
GET  /api/agents/{id}
POST /api/agents/{id}/start
POST /api/agents/{id}/send
POST /api/agents/{id}/continue
POST /api/agents/{id}/stop
GET  /api/sessions
POST /api/sessions/start
GET  /api/sessions/{id}
POST /api/sessions/{id}/send
POST /api/sessions/{id}/continue
POST /api/sessions/{id}/stop
```

Example:

```powershell
Invoke-RestMethod http://127.0.0.1:8765/api/providers/status
```

List configured agents:

```powershell
Invoke-RestMethod http://127.0.0.1:8765/api/agents
```

Start Codex from `config.json`:

```powershell
Invoke-RestMethod http://127.0.0.1:8765/api/agents/codex/start -Method Post
```

Continue Claude:

```powershell
Invoke-RestMethod http://127.0.0.1:8765/api/agents/claude/continue -Method Post
```

Start a session:

```powershell
Invoke-RestMethod http://127.0.0.1:8765/api/sessions/start `
  -Method Post `
  -ContentType application/json `
  -Body '{"name":"shell","command":["powershell","-NoProfile"]}'
```

## Configured Agents

Edit `config.json` to point agents at the projects and commands you actually
use:

```json
{
  "agents": [
    {
      "id": "claude",
      "name": "Claude Code",
      "command": ["claude"],
      "cwd": "C:\\Users\\100448405\\your-project"
    },
    {
      "id": "codex",
      "name": "Codex CLI",
      "command": ["codex"],
      "cwd": "C:\\Users\\100448405\\your-project"
    }
  ]
}
```

Send input:

```powershell
Invoke-RestMethod http://127.0.0.1:8765/api/sessions/1/send `
  -Method Post `
  -ContentType application/json `
  -Body '{"text":"Write-Host hello\n"}'
```

## Hardware Direction

The daemon should expose a stable local API. The hardware side can then be any
small device that speaks USB serial, WebSocket, or HTTP through a companion
bridge.

Initial controls:

- agent switch button
- continue/confirm button
- cancel/stop button
- small screen for provider status and active session output
