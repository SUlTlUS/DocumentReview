from __future__ import annotations

import argparse
import atexit
import ctypes
import json
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import threading
import time
from urllib.error import URLError
from urllib.request import urlopen
import webbrowser


ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"
OUTPUT_DIR = ROOT / "output"
PYTHON = BACKEND_DIR / ".venv" / "Scripts" / "python.exe"
FRONTEND_URL = "http://127.0.0.1:5173"
HEALTH_URL = "http://127.0.0.1:8000/api/health"
CREATE_NO_WINDOW = 0x08000000

_children: list[subprocess.Popen[bytes]] = []
_log_files = []
_cleaned = False
_cleanup_lock = threading.Lock()


def port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connection:
        connection.settimeout(0.3)
        return connection.connect_ex(("127.0.0.1", port)) == 0


def http_ready(url: str) -> bool:
    try:
        with urlopen(url, timeout=2) as response:
            return 200 <= response.status < 400
    except (OSError, URLError):
        return False


def start_process(
    command: list[str],
    cwd: Path,
    stdout_name: str,
    stderr_name: str,
) -> subprocess.Popen[bytes]:
    stdout = (OUTPUT_DIR / stdout_name).open("wb")
    stderr = (OUTPUT_DIR / stderr_name).open("wb")
    _log_files.extend((stdout, stderr))
    process = subprocess.Popen(
        command,
        cwd=cwd,
        stdout=stdout,
        stderr=stderr,
        creationflags=CREATE_NO_WINDOW,
    )
    _children.append(process)
    return process


def stop_process_tree(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    subprocess.run(
        ["taskkill", "/PID", str(process.pid), "/T", "/F"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=CREATE_NO_WINDOW,
        check=False,
    )


def cleanup() -> None:
    global _cleaned
    with _cleanup_lock:
        if _cleaned:
            return
        _cleaned = True
        if _children:
            print("\n正在关闭本次启动的前后端服务...", flush=True)
        for child in reversed(_children):
            stop_process_tree(child)
        for log_file in _log_files:
            log_file.close()


def install_console_close_handler() -> None:
    if sys.platform != "win32":
        return
    handler_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_uint)

    @handler_type
    def handler(_event: int) -> bool:
        cleanup()
        return False

    install_console_close_handler.callback = handler
    ctypes.windll.kernel32.SetConsoleCtrlHandler(handler, True)


def wait_until_ready(timeout_seconds: int) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if http_ready(HEALTH_URL) and http_ready(FRONTEND_URL):
            return
        if any(child.poll() is not None for child in _children):
            raise RuntimeError("服务进程提前退出，请检查 output 目录中的启动日志。")
        time.sleep(0.4)
    raise TimeoutError("等待服务就绪超时，请检查 output 目录中的启动日志。")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--exit-after-ready", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--timeout", type=int, default=45)
    args = parser.parse_args()

    if not PYTHON.is_file():
        raise RuntimeError("Backend virtual environment is missing.")
    npm = shutil.which("npm.cmd")
    if npm is None:
        raise RuntimeError("npm.cmd was not found. Install Node.js and add npm to PATH.")
    if not (FRONTEND_DIR / "node_modules").is_dir():
        raise RuntimeError("Frontend dependencies are missing. Run: cd frontend && npm install")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    atexit.register(cleanup)
    install_console_close_handler()

    if port_open(8000):
        print("[1/3] 后端已在 127.0.0.1:8000 运行，本次不接管该进程。")
    else:
        print("[1/3] 启动后端 127.0.0.1:8000...")
        start_process(
            [str(PYTHON), "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
            BACKEND_DIR,
            "backend-live.stdout.log",
            "backend-live.stderr.log",
        )

    if port_open(5173):
        print("[2/3] 前端已在 127.0.0.1:5173 运行，本次不接管该进程。")
    else:
        print("[2/3] 启动前端 127.0.0.1:5173...")
        start_process(
            [npm, "run", "dev", "--", "--host", "127.0.0.1", "--port", "5173"],
            FRONTEND_DIR,
            "frontend-live.stdout.log",
            "frontend-live.stderr.log",
        )

    print("[3/3] 等待服务就绪...")
    wait_until_ready(args.timeout)
    health = json.loads(urlopen(HEALTH_URL, timeout=2).read().decode("utf-8"))
    print(f"已就绪：{FRONTEND_URL}（{health['llm_provider']}）", flush=True)
    if not args.no_browser:
        webbrowser.open(FRONTEND_URL)
    if args.exit_after_ready:
        return 0

    print("关闭此窗口或按 Ctrl+C，将停止本次启动的前后端服务。", flush=True)
    try:
        while True:
            if any(child.poll() is not None for child in _children):
                raise RuntimeError("服务进程意外退出，请检查 output 目录中的日志。")
            time.sleep(1)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"[ERROR] {error}", file=sys.stderr, flush=True)
        raise SystemExit(1)
