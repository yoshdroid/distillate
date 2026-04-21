# pyxel_mcp Setup Memo

## Date

- 2026-04-20

## Goal

- Register `pyxel_mcp` as an MCP server so Codex can see it directly.

## What I checked first

- `pyxel-mcp` package was already installed in Python.
- `pyxel-mcp` command was exposed as a console script.
- Codex CLI had MCP management commands:
  - `codex mcp list`
  - `codex mcp add`
  - `codex mcp get`

## Commands I ran

```powershell
codex mcp add pyxel_mcp -- pyxel-mcp
codex mcp list
codex mcp get pyxel_mcp
Get-Content $HOME\.codex\config.toml
```

## Result

- MCP server registration succeeded.
- `codex mcp list` showed:
  - name: `pyxel_mcp`
  - command: `pyxel-mcp`
  - status: `enabled`
- `codex mcp get pyxel_mcp` showed:
  - transport: `stdio`
  - command: `pyxel-mcp`

## Config written by Codex CLI

`~/.codex/config.toml`

```toml
[windows]
sandbox = "unelevated"

[mcp_servers.pyxel_mcp]
command = "pyxel-mcp"
```

## Important note

- Inside the current Codex session, `list_mcp_resources` still returned empty.
- That means the MCP server was added to Codex configuration successfully, but this running session did not hot-reload the new MCP server.
- Most likely, a new Codex session or IDE restart is needed before the tool becomes visible to the agent.

## Current conclusion

- `pyxel_mcp` registration: success
- Visible to current live session immediately: not yet confirmed
- Likely next step: restart Codex / reopen the IDE session, then check MCP resources again
