# pyxel_mcp 設定メモ

## 日付

- 2026-04-20

## 目的

- `pyxel_mcp` を MCP サーバとして登録し、Codex から直接見える状態にする。

## 最初に確認したこと

- Python 環境に `pyxel-mcp` パッケージがすでにインストールされていた。
- `pyxel-mcp` コマンドがコンソールスクリプトとして公開されていた。
- Codex CLI に MCP 管理コマンドが用意されていた。
  - `codex mcp list`
  - `codex mcp add`
  - `codex mcp get`

## 実行したコマンド

```powershell
codex mcp add pyxel_mcp -- pyxel-mcp
codex mcp list
codex mcp get pyxel_mcp
Get-Content $HOME\.codex\config.toml
```

## 結果

- MCP サーバの登録は成功した。
- `codex mcp list` では次の内容を確認できた。
  - name: `pyxel_mcp`
  - command: `pyxel-mcp`
  - status: `enabled`
- `codex mcp get pyxel_mcp` では次の内容を確認できた。
  - transport: `stdio`
  - command: `pyxel-mcp`

## Codex CLI により書き込まれた設定

`~/.codex/config.toml`

```toml
[windows]
sandbox = "unelevated"

[mcp_servers.pyxel_mcp]
command = "pyxel-mcp"
```

## 重要なメモ

- 現在の Codex セッション内では、`list_mcp_resources` は空のままだった。
- つまり、Codex の設定ファイルへの追加自体は成功したが、この実行中セッションでは新しい MCP サーバがホットリロードされていない。
- エージェントから見えるようにするには、Codex セッションの再起動や IDE の再起動が必要である可能性が高い。

## 現時点の結論

- `pyxel_mcp` の登録: 成功
- 現在のライブセッションから即時に見えるか: 未確認
- 次の有力な手順: Codex / IDE を再起動し、その後に MCP リソースが見えるか再確認する
