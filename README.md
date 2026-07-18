# AI-agent setup instructions — Paperclip × Hermes Paperclip Adapter integration (ZAI GLM-4.6 / MiniMax, Windows/WSL2)

**Just paste this repo's link into your favorite AI coding agent (Claude Code, Codex, Cursor…) — and it sets up the whole
integration for you:** **[Paperclip](https://github.com/paperclipai/paperclip)** (the AI-agent orchestrator, Windows) →
**[Hermes Paperclip Adapter](https://github.com/NousResearch/hermes-paperclip-adapter)** (WSL2/Ubuntu) → a
**ZAI `glm-4.6`** (or **MiniMax**) LLM. This repo holds the **correct example files** and the **step-by-step instructions**
the AI follows to wire it all together. *(One step — installing Hermes itself — is interactive and flagged for a human;
the rest the AI does for you.)*

![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11%20%2B%20WSL2-0078D6?logo=windows&logoColor=white)
![Model](https://img.shields.io/badge/model-zai%2Fglm--4.6-8957e5)
![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-1f6feb)
[![Website](https://img.shields.io/badge/website-landing_page-34d17a)](https://vibecodeblogger-public.github.io/paperclip-hermes-paperclip-adapter-integration-glm-4.6-zai-minimax-llm-windows-wsl2/)

🌐 **New here? Start on the [landing page →](https://vibecodeblogger-public.github.io/paperclip-hermes-paperclip-adapter-integration-glm-4.6-zai-minimax-llm-windows-wsl2/)** — a clean, illustrated walkthrough of the whole setup.

> **What this solves:** the chain has several sharp edges (WSL prompt quoting, mirrored networking, a Paperclip config
> quirk) that each silently break it. This repo documents and automates the *working* setup so you don't have to
> rediscover them — after setup, point a Paperclip agent at one command and it drives Hermes on GLM-4.6 (or
> MiniMax) key, all locally on your machine.

---

## Why this exists

Paperclip orchestrates AI agents, but each agent needs an LLM backend. Wiring Paperclip (Windows, Node.js) to Hermes
Agent (Linux, in WSL2) hits two sharp edges that this bridge solves for you:

- **Quote-safe prompt passing.** Paperclip prompts contain `"` characters. Passing them straight through
  `wsl python3 -c "..."` makes bash choke with `unexpected EOF while looking for matching '"'`. The bridge writes the
  prompt to a file over a stdin pipe instead, so quoting can never break the call.
- **Mirrored networking.** By default WSL2 has its own network stack and cannot reach `127.0.0.1:3100` (the Paperclip
  API). A tiny `.wslconfig` switches WSL to mirrored mode so the agent can call back into Paperclip.

The result: a reliable, repeatable local setup that runs against **your own** ZAI (or MiniMax) API key, all on your machine.

## Architecture — the full call chain

```
Paperclip (Node.js, Windows, port 3100)
    │
    │  resolveSpawnTarget → calls hermes.cmd directly:
    │  cmd.exe /d /s /c "C:\Users\<USER>\...\hermes.cmd" chat -q "..."
    ▼
hermes.cmd            ← MAIN ENTRY POINT (delegates to the script beside it)
    │  python "%~dp0launch_hermes.py" %*
    ▼
launch_hermes.py      ← ALL THE LOGIC LIVES HERE
    │  1. Reads env vars: PAPERCLIP_TASK_ID, PAPERCLIP_API_URL, ...
    │  2. Pins the model in ~/.hermes/config.yaml (sed)
    │  3. Writes the prompt to /tmp/hermes_prompt.txt   (WSL stdin-pipe, no quoting)
    │  4. Writes a runner script to /tmp/run_hermes.py  (WSL stdin-pipe, no quoting)
    │  5. Runs: wsl bash -lc 'python3 /tmp/run_hermes.py'
    ▼
WSL2 Ubuntu — hermes chat
    │  ~/.hermes/config.yaml  (model: zai/glm-4.6, provider: zai)
    │  ~/.hermes/.env         (ZAI_API_KEY)
    ▼
ZAI API (https://api.z.ai/api/paas/v4) — model zai/glm-4.6
```

## Providers — ZAI, MiniMax, or any Hermes backend

The bridge is **provider-agnostic**. The default is ZAI's **`glm-4.6`**, but Hermes routes to whatever model you
configure — including popular options like **MiniMax**. To switch, either edit `model` / `provider` in
`~/.hermes/config.yaml`, or set the **`HERMES_MODEL`** environment variable on the Paperclip agent (it wins per run):

```
HERMES_MODEL = zai/glm-4.6      # default
HERMES_MODEL = <minimax-model>  # or any model whose provider you've configured in ~/.hermes
```

The only requirement is that the chosen model's provider is set up and authenticated in your WSL `~/.hermes` install.

## Requirements

- Windows 10/11 with **WSL2** (Ubuntu)
- **Node.js 20+** (for Paperclip)
- **Python 3.10+** on Windows (for `launch_hermes.py`) and in WSL Ubuntu (for hermes-agent)
- A **[z.ai](https://z.ai)** account for an API key

## Quick start

### 1. Get a ZAI API key

Sign in at **https://z.ai/manage-apikey/apikey-list**, create a key, and copy it.

### 2. Run the installer

```powershell
# In PowerShell, from this repo folder:
.\install_hermes_wsl.ps1
```

It installs `hermes-agent` in WSL, writes `~/.hermes/config.yaml` (model `zai/glm-4.6`) and `~/.hermes/.env` (your key),
adds a `hermes.bat` shim to your Windows `PATH`, and verifies the install.

### 3. Point a Paperclip agent at the bridge

1. Open **http://127.0.0.1:3100/MYA/agents/**
2. Create or edit an agent.
3. In **Hermes Command**, put the full path to `hermes.cmd` from this repo, e.g.
   `C:\Users\<USER>\paperclip-hermes-zai-integration\hermes.cmd`
4. In **Environment Variables**, add `ZAI_API_KEY` and `GLM_API_KEY` (both = your z.ai key).
5. Click **Test Environment** — it should report `Passed`.

That's it — assign a task to the agent and it runs on GLM-4.6.

## Manual install

Prefer to do it by hand? See **[external_files/README.md](external_files/README.md)** for the step-by-step version
(install Hermes in WSL, write the config, enable mirrored networking, build `hermes.exe`).

## Files in this repo

| File | What it does |
|------|-----------|
| `launch_hermes.py` | **The bridge.** Reads the Paperclip task, writes the prompt to a WSL file (quote-safe), runs hermes. |
| `hermes.cmd` | **Windows entry point** Paperclip calls. Delegates to `launch_hermes.py` beside it. |
| `install_hermes_wsl.ps1` | One-command installer for the whole chain. |
| `hermes.spec` | PyInstaller spec to build `dist\hermes.exe` from `launch_hermes.py`. |
| `hermes.bat` | Simple wrapper to call `hermes` from a Windows terminal (forwards into WSL). |
| `config.yaml` | Hermes config for WSL (`~/.hermes/config.yaml`): model `zai/glm-4.6`, provider `zai`. |
| `.env.template` | Template for the ZAI key — rename to `.env` inside `~/.hermes/`. |
| `external_files/` | Files that live **outside** the repo (`~/.wslconfig`, WSL config, PATH shim) + manual guide. |

## Build `hermes.exe` (optional)

Paperclip can call a compiled `dist\hermes.exe` instead of the `.cmd`:

```cmd
pip install pyinstaller
pyinstaller --clean hermes.spec
```

## Troubleshooting

**`hermes: command not found` in WSL** — install it: `wsl bash -lc "pip install --upgrade hermes-agent"`, then
`wsl bash -lc "which hermes"`.

**`bash: -c: line 1: unexpected EOF while looking for matching '"'`** — the classic WSL quoting bug. Make sure Paperclip
calls a build made from the current `launch_hermes.py` (rebuild with `pyinstaller --clean hermes.spec`); the bridge
passes prompts via a file specifically to avoid this.

**WSL can't reach the Paperclip API (`127.0.0.1:3100`)** — enable mirrored networking: put `[wsl2]` +
`networkingMode=mirrored` in `C:\Users\%USERNAME%\.wslconfig`, then `wsl --shutdown` and reopen.

**Test Environment passes but real runs fall back to PATH `hermes`** — a known Paperclip quirk: the UI saves the field as
`hermesCommand`, but agents created earlier may store the old `command` key, which the adapter ignores. Inspect the agent
config and, if `hermesCommand` is missing, `PATCH` it back via the Paperclip API. Full commands are in the manual guide.

**A task won't run a second time** — remove the assignee ("No assignee"), wait a couple of seconds, then reassign.

Debug logs are written next to the bridge under `logs/` (`hermes_launch_debug.txt` = every run, appended;
`last_run.txt` = raw stdout of the latest run).

## Links

- 🌐 Landing page (full illustrated guide) — https://vibecodeblogger-public.github.io/paperclip-hermes-paperclip-adapter-integration-glm-4.6-zai-minimax-llm-windows-wsl2/
- 📦 Paperclip — https://github.com/paperclipai/paperclip
- 🔌 Hermes Paperclip Adapter — https://github.com/NousResearch/hermes-paperclip-adapter
- 🔑 ZAI API keys — https://z.ai/manage-apikey/apikey-list
- 📺 Video walkthrough — https://www.youtube.com/playlist?list=PL6D9b9lf9gb2_0Wpg5HcYenthYSK9KznR

## License

MIT — see [LICENSE](LICENSE).
