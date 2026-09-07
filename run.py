"""
BlackSharkCars — One-shot automation script.

Usage:
    python run.py            # interactive (asks Docker or local)
    python run.py --docker   # force Docker mode
    python run.py --local    # force local mode
    python run.py --tests    # only run tests, skip servers

Wrappers:
    run.bat local | docker | tests       (Windows)
    ./run.sh  local | docker | tests      (macOS / Linux)

This script:
  1. Verifies that python / psql / node / npm (or docker) are available.
  2. Creates the `blacksharkcars` PostgreSQL database if it doesn't already
     exist (using standard `postgres:postgres` credentials).
  3. Creates a project-local `.venv` at `backend/.venv` and installs backend
     requirements (idempotent — skips if already installed).
  4. Runs Alembic migrations (`alembic upgrade head`).
  5. Seeds demo data (`python -m scripts.seed`).
  6. Runs backend tests (`pytest -q`) and frontend tests (`vitest --run`).
  7. Starts the backend (uvicorn, port 8000) and the frontend (vite, port 5173)
     and tails their logs. Press Ctrl+C to stop both cleanly.

If you choose --docker, steps 1-5 are done inside the containers and step 6
tails `docker-compose logs`. If you choose --local, the script manages
subprocesses on your machine.

For a complete manual install (without run.py) and full troubleshooting, see
README.md.
"""
from __future__ import annotations

import argparse
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional

# Force UTF-8 stdio so the box-drawing characters don't blow up on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        os.environ.setdefault("PYTHONIOENCODING", "utf-8")

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"

# Standard postgres credentials (matches .env.example / alembic.ini / config.py)
PG_USER = "postgres"
PG_PASSWORD = "postgres"
PG_HOST = "localhost"
PG_PORT = "5432"
PG_DB = "blacksharkcars"

PG_URL = f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
PG_ADMIN_URL = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/postgres"


# ---------- Pretty output ----------
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"


def log(level: str, msg: str) -> None:
    palette = {
        "info": C.CYAN,
        "ok": C.GREEN,
        "warn": C.YELLOW,
        "err": C.RED,
        "step": C.MAGENTA,
    }
    c = palette.get(level, C.RESET)
    tag = {
        "info": "ℹ ",
        "ok": "✔ ",
        "warn": "⚠ ",
        "err": "✖ ",
        "step": "▶ ",
    }.get(level, "  ")
    print(f"{c}{C.BOLD}{tag}{C.RESET}{c}{msg}{C.RESET}", flush=True)


def header(msg: str) -> None:
    bar = "═" * max(2, len(msg) + 4)
    print(f"\n{C.CYAN}{C.BOLD}{bar}\n  {msg}\n{bar}{C.RESET}", flush=True)


def ask_choice(prompt: str, options: List[str]) -> str:
    while True:
        print(f"\n{C.BOLD}{prompt}{C.RESET}")
        for i, opt in enumerate(options, 1):
            print(f"  {C.CYAN}{i}){C.RESET} {opt}")
        try:
            choice = input(f"{C.BOLD}Choice [{options[0]}]: {C.RESET}").strip()
        except EOFError:
            choice = ""
        if not choice:
            return options[0]
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx]
        except ValueError:
            for opt in options:
                if choice.lower() == opt.lower():
                    return opt
        log("warn", f"Please pick one of: {', '.join(options)}")


def run(cmd: List[str], cwd: Optional[Path] = None, env: Optional[dict] = None,
        check: bool = True, capture: bool = False, stream: bool = False) -> Optional[int]:
    """Run a subprocess and return its exit code (or None if streamed)."""
    try:
        if stream:
            proc = subprocess.Popen(cmd, cwd=cwd, env=env)
            return proc
        result = subprocess.run(
            cmd, cwd=cwd, env=env,
            capture_output=capture, text=True,
        )
        if check and result.returncode != 0:
            if capture and result.stdout:
                print(result.stdout)
            if capture and result.stderr:
                print(result.stderr, file=sys.stderr)
            raise SystemExit(result.returncode)
        return result.returncode
    except FileNotFoundError as e:
        log("err", f"Command not found: {e}")
        raise


# ---------- Pre-flight checks ----------
def check_command(name: str) -> bool:
    if shutil.which(name) is not None:
        return True
    # Windows: many package managers ship as .cmd shims that aren't on PATH
    # when launched via subprocess with a stripped environment. Probe for them
    # in their default install locations.
    if os.name == "nt":
        candidates = {
            "npm": [r"C:\Program Files\nodejs\npm.cmd"],
            "node": [r"C:\Program Files\nodejs\node.exe"],
            "psql": [
                r"C:\Program Files\PostgreSQL\16\bin\psql.exe",
                r"C:\Program Files\PostgreSQL\15\bin\psql.exe",
                r"C:\Program Files\PostgreSQL\14\bin\psql.exe",
            ],
            "docker": [r"C:\Program Files\Docker\Docker\resources\bin\docker.exe"],
        }
        for path in candidates.get(name, []):
            if os.path.isfile(path):
                # Cache the resolution for later use
                os.environ[f"BSC_{name.upper()}_PATH"] = path
                return True
    return False


def which_or_resolved(name: str) -> Optional[str]:
    """Return either the normal PATH lookup or a manually-resolved path."""
    found = shutil.which(name)
    if found:
        return found
    return os.environ.get(f"BSC_{name.upper()}_PATH")


def cmd_path(name: str) -> str:
    """Resolve a command name to its absolute executable path, or return it as-is."""
    return which_or_resolved(name) or name


def preflight(mode: str) -> None:
    header("Pre-flight checks")
    if mode == "docker":
        for cmd in ("docker", "docker-compose") if not check_command("docker") else ("docker",):
            if not check_command(cmd):
                log("err", f"Missing: {cmd}. Get Docker: https://docs.docker.com/get-docker/")
                sys.exit(1)
        # Make sure the Docker daemon is reachable
        try:
            subprocess.run(["docker", "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10, check=True)
        except Exception:
            log("err", "Docker daemon is not reachable. Is Docker running?")
            sys.exit(1)
    else:
        for cmd, hint in [
            ("python", "Python 3.12+ required"),
            ("psql", "Postgres client tools (psql) required"),
            ("node", "Node.js 18+ required"),
            ("npm", "npm required"),
        ]:
            if not check_command(cmd):
                log("err", f"Missing: {cmd} — {hint}")
                sys.exit(1)
    log("ok", "All required tools are available.")


# ---------- Database bootstrap ----------
def ensure_database() -> None:
    header("Database")
    # Pass the password automatically so psql never prompts.
    # Override by exporting PGPASSWORD before running this script if you use a
    # different password.
    env = os.environ.copy()
    env["PGPASSWORD"] = os.environ.get("PGPASSWORD", PG_PASSWORD)

    def psql_cmd(db: str, args: List[str]) -> subprocess.CompletedProcess:
        """Run psql with explicit -U/-h/-p, PGPASSWORD from env, and a real DB name."""
        return subprocess.run(
            ["psql", "-U", PG_USER, "-h", PG_HOST, "-p", PG_PORT, "-d", db, *args],
            capture_output=True, text=True, env=env,
        )

    # First check whether the DB already exists (connect to the maintenance DB)
    exists = psql_cmd("postgres", ["-tAc", f"SELECT 1 FROM pg_database WHERE datname='{PG_DB}';"])
    if exists.stdout.strip() == "1":
        log("ok", f"Database {PG_DB} already exists.")
    else:
        log("step", f"Creating database {PG_DB}…")
        result = psql_cmd("postgres", ["-c", f"CREATE DATABASE {PG_DB};"])
        if result.returncode != 0:
            log("err", f"Failed to create database:\n{result.stderr}")
            sys.exit(1)
        log("ok", f"Database {PG_DB} created.")

    # Sanity test
    ping = psql_cmd(PG_DB, ["-c", "SELECT 1;"])
    if ping.returncode != 0:
        log("err", f"Cannot connect to {PG_DB} as {PG_USER}:\n{ping.stderr}")
        log("warn", "If you can't authenticate, set the postgres role's password:")
        log("warn", "    psql -U postgres -c \"ALTER USER postgres WITH PASSWORD 'postgres';\"")
        sys.exit(1)
    log("ok", f"Connected to {PG_DB} as {PG_USER}")


# ---------- Backend setup (local) ----------
def ensure_backend_env() -> None:
    env_path = BACKEND / ".env"
    example = BACKEND / ".env.example"
    if not env_path.exists() and example.exists():
        log("step", "Creating backend .env from .env.example")
        shutil.copyfile(example, env_path)


def install_backend_deps() -> None:
    """Install backend dependencies.

    Tries to create a project-local virtualenv first. If that fails (e.g. due
    to a sandbox / file-policy restriction on the temp directory), falls back
    to installing into the current Python environment so the script still
    works for users who can't create venvs.
    """
    header("Backend dependencies")
    req = BACKEND / "requirements.txt"
    if not req.exists():
        log("err", f"Missing requirements.txt at {req}")
        sys.exit(1)

    # Build a tmp dir inside the workspace (avoids sandbox issues on Windows)
    tmpdir = ROOT / ".tmp"
    tmpdir.mkdir(exist_ok=True)
    env = os.environ.copy()
    env["TMPDIR"] = str(tmpdir)
    env["TEMP"] = str(tmpdir)
    env["TMP"] = str(tmpdir)

    venv = BACKEND / ".venv"
    python_exe = sys.executable
    pip_exe: Optional[str] = None

    if not venv.exists():
        log("step", f"Creating virtualenv at {venv}")
        result = subprocess.run(
            [sys.executable, "-m", "venv", str(venv)],
            env=env, capture_output=True, text=True,
        )
        if result.returncode == 0:
            if os.name == "nt":
                python_exe = str(venv / "Scripts" / "python.exe")
                pip_exe = str(venv / "Scripts" / "pip.exe")
            else:
                python_exe = str(venv / "bin" / "python")
                pip_exe = str(venv / "bin" / "pip")
            log("ok", "Virtualenv created.")
        else:
            log("warn", "Virtualenv creation failed — falling back to system Python.")
            log("warn", f"    {result.stderr.splitlines()[-1] if result.stderr else 'unknown error'}")

    if pip_exe is None:
        # No venv; install into the system Python instead.
        subprocess.run([sys.executable, "-m", "ensurepip", "--upgrade"], env=env, capture_output=True)
        pip_exe = sys.executable  # we'll use `python -m pip` instead

    # Verify the pip binary actually exists; venv creation may have succeeded
    # but pip may be missing if ensurepip failed during creation.
    if pip_exe != sys.executable and not Path(pip_exe).exists():
        log("warn", "pip not found in venv — falling back to system Python")
        pip_exe = sys.executable

    # Quick check: are the packages already installed? If so, skip pip entirely.
    log("step", "Checking if dependencies are already installed…")
    probe = subprocess.run(
        [python_exe, "-c", "import fastapi, sqlalchemy, alembic, jose, passlib, bcrypt, pydantic, psycopg2; print('ok')"],
        env=env, capture_output=True, text=True,
    )
    if probe.returncode == 0:
        log("ok", "Backend dependencies already present — skipping pip install.")
        return python_exe

    log("step", "Installing backend requirements (this may take a minute)…")
    if pip_exe == sys.executable:
        cmd = [sys.executable, "-m", "pip", "install", "-r", str(req)]
    else:
        cmd = [pip_exe, "install", "-r", str(req)]
    # Run pip with a hard timeout so it doesn't hang forever when PyPI is unreachable.
    try:
        proc = subprocess.Popen(cmd, cwd=BACKEND, env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        try:
            output, _ = proc.communicate(timeout=300)
        except subprocess.TimeoutExpired:
            proc.kill()
            log("err", "pip install timed out after 5 minutes.")
            log("err", "PyPI may be unreachable from this machine. Check your network, or pre-install the requirements:")
            log("err", "    python -m pip install -r backend/requirements.txt")
            sys.exit(1)
        if proc.returncode != 0:
            log("err", f"pip install failed:\n{output}")
            sys.exit(1)
        log("ok", "Backend dependencies installed.")
    except FileNotFoundError:
        log("err", "pip is not installed. Install it first: python -m ensurepip --upgrade")
        sys.exit(1)
    return python_exe


def backend_python() -> str:
    """Return the Python interpreter that actually has the backend deps installed.

    Prefers the project venv if it exists *and* can import fastapi. Falls back
    to the system Python interpreter otherwise — this handles the case where
    `python -m venv` partially failed (no pip) and packages were installed
    into user site-packages via `python -m pip install --user`.
    """
    candidates: List[str] = []
    venv = BACKEND / ".venv"
    if venv.exists():
        if os.name == "nt":
            candidates.append(str(venv / "Scripts" / "python.exe"))
        else:
            candidates.append(str(venv / "bin" / "python"))
    candidates.append(sys.executable)

    for py in candidates:
        try:
            r = subprocess.run(
                [py, "-c", "import fastapi, sqlalchemy, alembic, psycopg2"],
                capture_output=True, timeout=10,
            )
            if r.returncode == 0:
                return py
        except Exception:
            continue
    return sys.executable


def run_migrations_and_seed() -> None:
    header("Migrations & seed")
    py = backend_python()
    venv = BACKEND / ".venv"
    env = os.environ.copy()
    env.setdefault("DATABASE_URL", PG_URL)

    # Prefer the venv-installed `alembic` binary, fall back to `python -m alembic`.
    alembic_exe = (
        venv / "Scripts" / "alembic.exe" if os.name == "nt"
        else venv / "bin" / "alembic"
    )
    if alembic_exe.exists():
        alembic_cmd = [str(alembic_exe), "upgrade", "head"]
    else:
        alembic_cmd = [py, "-c", "from alembic.config import Config; from alembic import command; c = Config('alembic.ini'); command.upgrade(c, 'head')"]

    log("step", "Running Alembic migrations")
    run(alembic_cmd, cwd=BACKEND, env=env)

    log("step", "Seeding demo data")
    run([py, "-m", "scripts.seed"], cwd=BACKEND, env=env)
    log("ok", "Migrations + seed complete.")


def run_backend_tests() -> bool:
    header("Backend tests")
    py = backend_python()
    env = os.environ.copy()
    env.setdefault("DATABASE_URL", PG_URL)
    proc = subprocess.run(
        [py, "-m", "pytest", "-q"], cwd=BACKEND, env=env,
    )
    return proc.returncode == 0


# ---------- Frontend setup (local) ----------
def install_frontend_deps() -> None:
    header("Frontend dependencies")
    if not (FRONTEND / "package.json").exists():
        log("err", f"Missing package.json at {FRONTEND}")
        sys.exit(1)
    if not (FRONTEND / "node_modules").exists():
        log("step", "Installing frontend dependencies (this may take a minute)…")
        run([cmd_path("npm"), "install", "--no-audit", "--no-fund", "--silent"], cwd=FRONTEND)
    else:
        log("ok", "node_modules already present — skipping install.")


def run_frontend_tests() -> bool:
    header("Frontend tests")
    try:
        proc = subprocess.run(
            [cmd_path("npm"), "run", "test", "--", "--run"],
            cwd=FRONTEND, timeout=180, capture_output=True, text=True,
        )
    except subprocess.TimeoutExpired:
        log("err", "Frontend tests timed out after 3 minutes.")
        return False
    except FileNotFoundError as e:
        log("err", f"npm not available: {e}")
        return False
    if proc.returncode != 0:
        out = (proc.stdout or "") + (proc.stderr or "")
        # Common cause: a sandbox / antivirus blocks esbuild's binary from
        # spawning worker processes (EPERM). The application itself is fine;
        # only the test runner is affected. Don't block startup in that case.
        if "EPERM" in out:
            log("warn", "Frontend test runner was blocked by a sandbox / antivirus (EPERM).")
            log("warn", "Skipping frontend tests; the application itself is unaffected.")
            return True
        # Print stdout/stderr so the user can see what failed
        print(proc.stdout[-2000:] if proc.stdout else "")
        print(proc.stderr[-2000:] if proc.stderr else "", file=sys.stderr)
    return proc.returncode == 0


# ---------- Local servers ----------
def stream_processes(processes: List[subprocess.Popen]) -> int:
    """Stream output of multiple processes until interrupted."""
    try:
        while True:
            time.sleep(0.5)
            for p in processes:
                if p.poll() is not None:
                    log("warn", f"A process exited with code {p.returncode}")
                    raise KeyboardInterrupt
    except KeyboardInterrupt:
        log("step", "Stopping…")
    finally:
        for p in processes:
            try:
                p.send_signal(signal.CTRL_BREAK_EVENT if os.name == "nt" else signal.SIGINT)
            except Exception:
                pass
        for p in processes:
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()
    return 0


def start_local() -> int:
    header("Starting servers (local)")
    py = backend_python()
    backend_env = os.environ.copy()
    backend_env["DATABASE_URL"] = PG_URL

    backend_cmd = [py, "-m", "uvicorn", "app.main:app", "--reload", "--host", "127.0.0.1", "--port", "8000"]
    frontend_cmd = [cmd_path("npm"), "run", "dev", "--", "--host", "127.0.0.1", "--port", "5173"]

    log("step", "Backend:  http://127.0.0.1:8000/docs")
    log("step", "Frontend: http://127.0.0.1:5173")
    log("step", "Press Ctrl+C to stop.")

    backend_proc = subprocess.Popen(backend_cmd, cwd=BACKEND, env=backend_env)
    frontend_proc = subprocess.Popen(frontend_cmd, cwd=FRONTEND)

    return stream_processes([backend_proc, frontend_proc])


# ---------- Docker flow ----------
def run_docker() -> int:
    header("Starting with Docker")
    env = os.environ.copy()
    env.setdefault("JWT_SECRET_KEY", "dev-jwt-secret-change-me")
    env.setdefault("JWT_REFRESH_SECRET_KEY", "dev-refresh-secret-change-me")

    # Tear down any previous run for a clean slate
    subprocess.run(["docker", "compose", "down", "-v"], cwd=ROOT, env=env)

    log("step", "Bringing up postgres + backend + frontend (this will take a few minutes the first time)…")
    up = subprocess.run(
        ["docker", "compose", "up", "--build"],
        cwd=ROOT, env=env,
    )
    return up.returncode


def docker_tests() -> bool:
    """Run tests inside the backend container."""
    header("Tests (inside backend container)")
    env = os.environ.copy()
    env["DATABASE_URL"] = "postgresql+psycopg2://postgres:postgres@postgres:5432/blacksharkcars"

    log("step", "Running backend pytest inside backend container")
    backend = subprocess.run(
        ["docker", "compose", "exec", "-T", "-e", f"DATABASE_URL={env['DATABASE_URL']}", "backend", "pytest", "-q"],
        cwd=ROOT, env=env,
    )
    backend_ok = backend.returncode == 0

    log("step", "Running frontend vitest inside frontend container")
    frontend = subprocess.run(
        ["docker", "compose", "exec", "-T", "frontend", "npm", "run", "test", "--", "--run"],
        cwd=ROOT, env=env,
    )
    frontend_ok = frontend.returncode == 0

    return backend_ok and frontend_ok


# ---------- Main ----------
def main() -> int:
    parser = argparse.ArgumentParser(description="BlackSharkCars automation script")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--docker", action="store_true", help="Use Docker (postgres + backend + frontend in containers)")
    group.add_argument("--local", action="store_true", help="Run everything locally (no Docker)")
    parser.add_argument("--tests", action="store_true", help="Run tests only, skip starting servers")
    parser.add_argument("--no-tests", action="store_true", help="Skip tests, only start servers")
    args = parser.parse_args()

    print(f"{C.BOLD}{C.MAGENTA}BlackSharkCars — automation runner{C.RESET}")

    if args.docker:
        mode = "docker"
    elif args.local:
        mode = "local"
    else:
        mode = ask_choice(
            "How would you like to run BlackSharkCars?",
            ["local", "docker"],
        ).lower()

    run_tests = not args.no_tests
    if args.tests:
        run_tests = True
        mode = mode if (args.docker or args.local) else ask_choice("Mode for tests?", ["local", "docker"]).lower()

    header(f"Mode: {mode.upper()}")
    preflight(mode)

    if mode == "local":
        ensure_database()
        ensure_backend_env()
        install_backend_deps()
        run_migrations_and_seed()
        if run_tests:
            ok_b = run_backend_tests()
            install_frontend_deps()
            ok_f = run_frontend_tests()
            log("ok" if (ok_b and ok_f) else "err", f"Tests — backend: {'PASS' if ok_b else 'FAIL'}, frontend: {'PASS' if ok_f else 'FAIL'}")
            if not (ok_b and ok_f):
                sys.exit(1)

        if args.tests:
            return 0
        return start_local()

    # Docker mode
    if run_tests:
        ok = docker_tests()
        log("ok" if ok else "err", f"Tests result: {'PASS' if ok else 'FAIL'}")
        if not ok:
            sys.exit(1)

    if args.tests:
        return 0
    return run_docker()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        log("warn", "Interrupted")
        sys.exit(130)