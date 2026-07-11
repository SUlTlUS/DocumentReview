from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"
VENV_DIR = BACKEND_DIR / ".venv"
VENV_PYTHON = VENV_DIR / "Scripts" / "python.exe"


def run(command: list[str], cwd: Path = ROOT) -> None:
    print(f"\n> {' '.join(command)}", flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def require_tool(name: str, install_hint: str) -> str:
    executable = shutil.which(name)
    if executable is None:
        raise RuntimeError(f"{name} was not found. {install_hint}")
    return executable


def validate_host() -> str:
    if sys.version_info < (3, 11):
        raise RuntimeError(
            f"Python 3.11 or newer is required; current version is {sys.version.split()[0]}."
        )
    npm = require_tool("npm.cmd", "Install the current Node.js LTS and add npm to PATH.")
    require_tool("node.exe", "Install the current Node.js LTS and add node to PATH.")
    return npm


def create_environment_file() -> None:
    target = BACKEND_DIR / ".env"
    example = BACKEND_DIR / ".env.example"
    if target.exists():
        print("[config] Existing backend/.env preserved.")
        return
    if not example.is_file():
        raise RuntimeError("backend/.env.example is missing.")
    shutil.copy2(example, target)
    print("[config] Created backend/.env from .env.example.")


def install_backend(with_ocr: bool) -> None:
    if not VENV_PYTHON.is_file():
        print("[backend] Creating virtual environment...")
        run([sys.executable, "-m", "venv", str(VENV_DIR)])
    else:
        print("[backend] Reusing backend/.venv.")
    run([str(VENV_PYTHON), "-m", "pip", "install", "--upgrade", "pip"])
    run([str(VENV_PYTHON), "-m", "pip", "install", "-r", "requirements.txt"], BACKEND_DIR)
    run([str(VENV_PYTHON), "-m", "pip", "install", "-r", "requirements-dev.txt"], BACKEND_DIR)
    if with_ocr:
        print("[backend] Installing optional PaddleOCR runtime; this may take several minutes...")
        run([str(VENV_PYTHON), "-m", "pip", "install", "-r", "requirements-ocr.txt"], BACKEND_DIR)


def install_frontend(npm: str) -> None:
    print("[frontend] Installing locked npm dependencies...")
    run([npm, "ci"], FRONTEND_DIR)


def verify(npm: str) -> None:
    print("[verify] Checking backend imports...")
    run(
        [
            str(VENV_PYTHON),
            "-c",
            "import fastapi, sqlalchemy, langchain_core; from app.main import app; print(app.version)",
        ],
        BACKEND_DIR,
    )
    print("[verify] Checking frontend types...")
    run([npm, "run", "typecheck"], FRONTEND_DIR)


def check_only(npm: str) -> None:
    missing: list[str] = []
    if not VENV_PYTHON.is_file():
        missing.append("backend/.venv")
    if not (FRONTEND_DIR / "node_modules").is_dir():
        missing.append("frontend/node_modules")
    if missing:
        raise RuntimeError(f"Environment is incomplete: {', '.join(missing)}")
    verify(npm)


def main() -> int:
    parser = argparse.ArgumentParser(description="Install the DocumentReview local environment.")
    parser.add_argument(
        "--with-ocr",
        action="store_true",
        help="Also install the large optional PaddleOCR/PaddlePaddle runtime.",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Verify the existing environment without installing packages.",
    )
    args = parser.parse_args()

    print(f"DocumentReview environment setup\nWorkspace: {ROOT}")
    npm = validate_host()
    if args.check_only:
        check_only(npm)
    else:
        create_environment_file()
        install_backend(args.with_ocr)
        install_frontend(npm)
        verify(npm)
    print("\n[SUCCESS] Backend and frontend environments are ready.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, subprocess.CalledProcessError) as error:
        print(f"\n[ERROR] {error}", file=sys.stderr)
        raise SystemExit(1)
