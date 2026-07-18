# launch_hermes.py
"""
Windows -> WSL argument bridge for hermes.

Log files:
  logs/hermes_launch_debug.txt — accumulated log of every run (append, capped at 1 MB)
  logs/last_run.txt            — raw hermes stdout from Linux, current run only (overwrite)

Project files:
  dist/hermes.exe              — compiled executable (Paperclip calls this)
  temp/heartbeat_paperclip.txt — raw argv of heartbeat calls
  temp/task_from_paperclip.txt — raw argv of task calls
"""
import subprocess
import sys
import os
import datetime
import threading
import json

# ── Resolve the project root (PyInstaller-aware) ──────────────────────────────
if getattr(sys, 'frozen', False):
    _project_dir = os.path.dirname(os.path.dirname(os.path.abspath(sys.executable)))
else:
    _project_dir = os.path.dirname(os.path.abspath(__file__))

_logs_dir = os.path.join(_project_dir, 'logs')
_temp_dir = os.path.join(_project_dir, 'temp')
os.makedirs(_logs_dir, exist_ok=True)
os.makedirs(_temp_dir, exist_ok=True)

_debug_log   = os.path.join(_logs_dir, 'hermes_launch_debug.txt')
_session_log = os.path.join(_logs_dir, 'last_run.txt')

_DEBUG_LOG_LIMIT = 1 * 1024 * 1024  # 1 MB

# ── Logging helpers ───────────────────────────────────────────────────────────

def log(msg):
    """Write to the accumulated debug log with a timestamp. Truncate if > 1 MB."""
    try:
        if os.path.exists(_debug_log) and os.path.getsize(_debug_log) > _DEBUG_LOG_LIMIT:
            mode = 'w'
        else:
            mode = 'a'
        with open(_debug_log, mode, encoding='utf-8') as f:
            f.write(f'{datetime.datetime.now().isoformat()} {msg}\n')
    except Exception:
        pass

def _session_write_raw(data: bytes):
    """Write raw bytes from hermes into the current-run log."""
    try:
        with open(_session_log, 'ab') as f:
            f.write(data)
    except Exception:
        pass

# ── Session start ─────────────────────────────────────────────────────────────
args = sys.argv[1:]
_start_time = datetime.datetime.now().isoformat()

# Clear the current-run log
open(_session_log, 'w').close()

log(f'\n=== NEW RUN {_start_time} ===')
log(f'argv: {sys.argv}')
for k in ['PAPERCLIP_TASK_ID', 'PAPERCLIP_AGENT_ID', 'PAPERCLIP_COMPANY_ID', 'PAPERCLIP_API_URL']:
    log(f'{k}={os.environ.get(k, "<NOT SET>")}')

# ── Version check ─────────────────────────────────────────────────────────────
if not args or args[0] == '--version':
    result = subprocess.run(
        ['wsl', 'bash', '-lc', 'hermes --version'],
        capture_output=True, text=True, timeout=15
    )
    print(result.stdout, end='')
    sys.exit(result.returncode)

# ── Save the raw Paperclip call into temp/ ────────────────────────────────────
_task_id_raw = os.environ.get('PAPERCLIP_TASK_ID', '')
_raw_path = os.path.join(_temp_dir, 'task_from_paperclip.txt' if _task_id_raw else 'heartbeat_paperclip.txt')
with open(_raw_path, 'w', encoding='utf-8') as _f:
    _f.write('\n'.join(sys.argv))

# ── Pin the model in the WSL config ───────────────────────────────────────────
# Provider-agnostic: set HERMES_MODEL (e.g. in the Paperclip agent env) to use a
# different provider such as MiniMax. Defaults to ZAI's free glm-4.6. The chosen
# model's provider must be configured/authed in your ~/.hermes setup.
_model = os.environ.get('HERMES_MODEL', 'zai/glm-4.6')
log(f'model: {_model}')
subprocess.run(
    ['wsl', 'bash', '-lc',
     f"sed -i 's|^model:.*|model: {_model}|' ~/.hermes/config.yaml"]
)

# ── Extract the prompt from argv ──────────────────────────────────────────────
prompt = None
if '-q' in args:
    _q_idx = args.index('-q')
    if _q_idx + 1 < len(args):
        prompt = args[_q_idx + 1]
        log(f'prompt taken from -q ({len(prompt)} chars)')
else:
    log('no -q argument')

if prompt is None:
    log('prompt=None → no task, exiting')
    sys.exit(0)

# ═════════════════════════════════════════════════════════════════════════════
# STEP 1: Check that hermes is available
# ═════════════════════════════════════════════════════════════════════════════
log('STEP 1: hermes --version')
try:
    check = subprocess.run(
        ['wsl', 'bash', '-lc', 'hermes --version'],
        capture_output=True, text=True
    )
    if check.returncode != 0:
        log(f'STEP 1 ERROR: returncode={check.returncode} stderr={check.stderr.strip()!r}')
        sys.exit(1)
    log(f'STEP 1 OK: {check.stdout.strip()!r}')
except subprocess.TimeoutExpired:
    log('STEP 1 ERROR: timeout')
    sys.exit(1)
except FileNotFoundError:
    log('STEP 1 ERROR: wsl.exe not found')
    sys.exit(1)
except Exception as e:
    log(f'STEP 1 ERROR: {type(e).__name__}: {e}')
    sys.exit(1)

# ═════════════════════════════════════════════════════════════════════════════
# STEP 2: Write the prompt to /tmp/hermes_prompt.txt in WSL
# ═════════════════════════════════════════════════════════════════════════════
log('STEP 2: write the prompt to WSL /tmp/hermes_prompt.txt')
try:
    subprocess.run(
        ['wsl', 'bash', '-c', 'cat > /tmp/hermes_prompt.txt'],
        input=prompt.encode('utf-8')
    )
    log(f'STEP 2 OK: prompt written ({len(prompt)} chars)')
except Exception as e:
    log(f'STEP 2 ERROR: {type(e).__name__}: {e}')
    sys.exit(1)

# ═════════════════════════════════════════════════════════════════════════════
# STEP 3: Run hermes with -q, capturing all output to the log
# ═════════════════════════════════════════════════════════════════════════════
log('STEP 3: build the runner script and launch hermes in WSL')
# Forward Paperclip flags except: -q (prompt comes from the file), -m and --provider
# (the model comes from the WSL ~/.hermes/config.yaml pinned by sed above)
_SKIP_FLAGS = {'-q', '-m', '--provider'}
_forward_args = []
_skip_val = False
for _a in args:
    if _skip_val:
        _skip_val = False
        continue
    if _a in _SKIP_FLAGS:
        _skip_val = True
        continue
    _forward_args.append(_a)

_hermes_cmd = ['hermes'] + _forward_args
_runner_lines = [
    'import subprocess, sys',
    f'cmd = {json.dumps(_hermes_cmd)}',
    'p = open("/tmp/hermes_prompt.txt").read()',
    'try:',
    '    idx = cmd.index("chat") + 1',
    'except ValueError:',
    '    idx = 1',
    'cmd = cmd[:idx] + ["-q", p] + cmd[idx:]',
    'r = subprocess.run(cmd)',
    'sys.exit(r.returncode)',
]
_runner_script = '\n'.join(_runner_lines) + '\n'

try:
    subprocess.run(
        ['wsl', 'bash', '-c', 'cat > /tmp/run_hermes.py'],
        input=_runner_script.encode('utf-8'),
        check=True
    )
    log('STEP 3a OK: /tmp/run_hermes.py written')
except Exception as e:
    log(f'STEP 3 ERROR (write runner): {type(e).__name__}: {e}')
    sys.exit(1)

try:
    proc = subprocess.Popen(
        ['wsl', 'bash', '-lc', 'python3 /tmp/run_hermes.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    log(f'STEP 3b OK: process started (pid={proc.pid}), cmd={_hermes_cmd!r}')
except FileNotFoundError:
    log('STEP 3b ERROR: wsl.exe not found')
    sys.exit(1)
except Exception as e:
    log(f'STEP 3b ERROR: {type(e).__name__}: {e}')
    sys.exit(1)

def _stdout_reader(proc):
    """Read hermes stdout: write raw bytes to last_run.txt and pass them through."""
    try:
        for raw_line in iter(proc.stdout.readline, b''):
            _session_write_raw(raw_line)
            sys.stdout.buffer.write(raw_line)
            sys.stdout.buffer.flush()
    except Exception as e:
        log(f'_stdout_reader ERROR: {type(e).__name__}: {e}')

reader_thread = threading.Thread(target=_stdout_reader, args=(proc,), daemon=True)
reader_thread.start()

# ═════════════════════════════════════════════════════════════════════════════
# STEP 4: Wait for hermes to finish
# ═════════════════════════════════════════════════════════════════════════════
log('STEP 4: wait for hermes to finish')
try:
    reader_thread.join()
    returncode = proc.wait()
    log(f'STEP 4 OK: hermes exited with code {returncode}')
    sys.exit(returncode)
except Exception as e:
    log(f'STEP 4 ERROR: {type(e).__name__}: {e}')
    sys.exit(1)
