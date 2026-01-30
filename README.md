# clawdbot_plugin

Clawdbot plugin for ncatbot.

## Features
- Group chat support
- Private chat support (configurable)
- Per-group/user session context
- New session command
- Async handling

## Quick Start
See `QUICKSTART.md` for setup and usage details.

## Commands
- `/clawd <message>`: chat with Clawdbot
- `/clawdtest`: test connection
- `/clawdnew`: start a new session (clear context)

## Notes
To change allowed private user ID, edit:
`clawdbot_plugin.py` and update `ALLOWED_PRIVATE_USER_ID`.

## License
TBD
