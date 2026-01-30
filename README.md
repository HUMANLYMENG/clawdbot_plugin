# clawdbot_plugin

Clawdbot plugin for ncatbot.

## Features
- Group chat support
- Private chat support (configurable)
- Per-group/user session context
- New session command
- Async handling

## Quick Start
Place this directory under `ncatbot/plugins/`.
See `QUICKSTART.md` for setup and usage details.

## Configuration
Set these environment variables before starting ncatbot:
- `CLAWDBOT_TOKEN` (required)
- `CLAWDBOT_GATEWAY_URL` (optional, default `http://127.0.0.1:18789`)
- `CLAWDBOT_ALLOWED_PRIVATE_USER_ID` (optional, restrict private access to a single user)

## Commands
- `/clawd <message>`: chat with Clawdbot
- `/clawdtest`: test connection
- `/clawdnew`: start a new session (clear context)

## Notes
To restrict private access to a single user, set:
`CLAWDBOT_ALLOWED_PRIVATE_USER_ID`.

## License
TBD
