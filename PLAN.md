# Development Plan

## Goal

Build a desktop hardware controller for Claude Code and Codex CLI that can show
agent status and continue execution without returning to the keyboard.

## Phase 1: Local Daemon MVP

Status: in progress.

Scope:

- expose a local HTTP API
- query official Claude and OpenAI status APIs
- launch and track local CLI processes
- load configured agents from `config.json`
- send text to a running process
- implement `continue` as a newline send
- return recent output for display

Success criteria:

- `GET /api/providers/status` returns Claude and OpenAI status
- `GET /api/agents` returns configured Claude and Codex entries
- `POST /api/agents/{id}/start` starts the configured command
- `POST /api/sessions/start` starts a local command
- `POST /api/sessions/{id}/continue` sends Enter
- `GET /api/sessions/{id}` returns running state and recent output

## Phase 2: Agent-Specific Session Detection

References:

- `graykode/abtop`
- `alexei-led/ccgram`

Scope:

- detect existing Claude Code and Codex CLI sessions
- identify active workspace/repo
- distinguish running, idle, waiting-for-input, and exited states
- parse useful token/rate-limit/context signals when available

## Phase 3: Reliable Terminal Control

Scope:

- replace naive subprocess handling with tmux/pty/ConPTY-backed sessions
- support Windows and WSL separately
- preserve scrollback
- send special keys such as Enter, Ctrl+C, Escape, arrow keys
- attach to existing sessions

## Phase 4: Hardware Bridge

Scope:

- add USB serial protocol or WebSocket bridge
- define compact status payload for ESP32 screen
- map hardware buttons to daemon commands
- add debouncing and reconnect behavior

## Phase 5: Hardware Firmware

Scope:

- ESP32-S3 firmware
- display provider status, active agent, and recent output
- buttons: switch agent, continue, stop, custom prompt
- optional rotary encoder for session selection

## Phase 6: Productization

Scope:

- config file for commands and sessions
- authentication for local network access
- packaged Windows/macOS daemon
- logs, crash recovery, and auto-start
