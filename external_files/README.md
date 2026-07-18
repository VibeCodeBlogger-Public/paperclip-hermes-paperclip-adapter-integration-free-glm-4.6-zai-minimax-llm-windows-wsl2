# External files — installation guide

This folder holds files that **live outside the repo** but are required for the
Paperclip → Hermes Agent → ZAI integration to work.

---

## Layout

```
external_files/
  windows/
    .wslconfig        → C:\Users\%USERNAME%\.wslconfig
    hermes.cmd        → C:\Users\%USERNAME%\bin\hermes.cmd
  wsl/
    hermes_config.yaml → ~/.hermes/config.yaml  (inside WSL)
```

---

## Step 1 — Install Hermes Agent manually (WSL)

> ⚠️ **Install Hermes by hand — not through an AI CLI, not through a script.**
>
> Why: the hermes installer asks interactive questions in the terminal
> (choose a provider, enter an API key, etc.). If you run the install through an
> AI agent (Claude Code, Codex, etc.), the agent just hangs, because it has
> nowhere to type the answers. So **open a WSL terminal yourself and install it**.

Open a WSL terminal (not via an AI!) and install hermes per the official
NousResearch hermes-agent documentation. Then verify:

```bash
hermes --version
```

It should print something like: `Hermes Agent v0.10.0`

---

## Step 2 — Configure ZAI in the Hermes config (WSL)

Copy `wsl/hermes_config.yaml` into WSL:

```bash
cp /mnt/c/path/to/project/external_files/wsl/hermes_config.yaml ~/.hermes/config.yaml
```

Or create `~/.hermes/config.yaml` by hand with:

```yaml
model: zai/glm-4.6
provider: zai
base_url: https://api.z.ai/api/paas/v4
```

Then authenticate with ZAI:

```bash
hermes auth zai
```

Check that ZAI responds:

```bash
hermes chat -q "say hello"
```

---

## Step 3 — Enable mirrored networking for WSL2 (Windows)

Copy `windows/.wslconfig` into your Windows home folder:

```
C:\Users\%USERNAME%\.wslconfig
```

Contents:

```ini
[wsl2]
networkingMode=mirrored
```

**Why:** without this, WSL cannot see `127.0.0.1:3100` (the Paperclip API),
because WSL2 uses a separate network stack by default. Mirrored mode proxies the
Windows loopback into WSL.

After creating the file, restart WSL:

```cmd
wsl --shutdown
```

---

## Step 4 — Add hermes.cmd to the Windows PATH (optional)

> Only needed to call `hermes` from a Windows command line directly.
> Paperclip calls `dist\hermes.exe` directly and does not need this file.

1. Create `C:\Users\%USERNAME%\bin\` (if it doesn't exist)
2. Copy `windows/hermes.cmd` there
3. Open the file and set the path to your actual project folder
4. Add `C:\Users\%USERNAME%\bin` to the system PATH variable

---

## Step 5 — Build hermes.exe

At the project root (Windows, Python 3.x + pyinstaller):

```cmd
pip install pyinstaller
pyinstaller --clean hermes.spec
```

Result: `dist\hermes.exe` — the executable Paperclip calls as `hermesCommand`.

---

## Final picture

```
Paperclip (Node.js :3100)
    ↓  calls hermesCommand = dist\hermes.exe
dist\hermes.exe  (= compiled launch_hermes.py)
    ↓  stdin-pipe → /tmp/hermes_prompt.txt  (prompt, no bash quoting)
    ↓  stdin-pipe → /tmp/run_hermes.py      (runner script)
    ↓  runs: wsl bash -lc 'python3 /tmp/run_hermes.py'
Hermes Agent (WSL, ~/.hermes/config.yaml → model: zai/glm-4.6)
    ↓  sends the request
ZAI API (https://api.z.ai, model: glm-4.6)
    ↓  runs the task, curls back to the Paperclip API
    ↓  curl http://127.0.0.1:3100/api/...  ← works thanks to .wslconfig mirrored
Paperclip API  ✓
```
