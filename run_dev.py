#!/usr/bin/env python3
"""
Enterprise Hybrid RAG - 1-Click Unified Development Launcher
Launches FastAPI Backend (127.0.0.1:8000) and Vite React Frontend (5173) concurrently.
Guarantees virtual environment python resolution, stale lock cleanup, health wait,
and graceful tree termination.
"""

import sys
import os
import signal
import subprocess
import time
import socket
import urllib.request
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"

def get_venv_python():
    """Resolve Python executable in .venv or fallback to sys.executable."""
    if os.name == "nt":
        venv_py = ROOT_DIR / ".venv" / "Scripts" / "python.exe"
    else:
        venv_py = ROOT_DIR / ".venv" / "bin" / "python"
    
    if venv_py.exists():
        return str(venv_py)
    return sys.executable

def ensure_port_clean(port=8000):
    """Ensure no stale processes are occupying the port or holding locks on qdrant_db."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        is_busy = s.connect_ex(("127.0.0.1", port)) == 0
    if is_busy:
        print(f"⚠ Warning: Port {port} is occupied. Attempting to release stale process...")
        if os.name == "nt":
            try:
                res = subprocess.run(
                    f'netstat -ano | findstr :{port}',
                    shell=True,
                    capture_output=True,
                    text=True
                )
                for line in res.stdout.strip().splitlines():
                    parts = line.split()
                    if len(parts) >= 5 and "LISTENING" in parts:
                        pid = parts[-1]
                        print(f"  Terminating stale process PID {pid} holding port {port}...")
                        subprocess.run(f"taskkill /F /PID {pid}", shell=True, capture_output=True)
                time.sleep(1.5)
            except Exception as e:
                print(f"  Could not release port automatically: {e}")

def check_ollama():
    """Verify Ollama local daemon is responding."""
    try:
        req = urllib.request.Request("http://127.0.0.1:11434/api/tags", headers={"User-Agent": "run_dev"})
        with urllib.request.urlopen(req, timeout=2) as resp:
            if resp.status == 200:
                print("✓ Ollama daemon is active at http://127.0.0.1:11434.")
                return True
    except Exception:
        print("⚠ Warning: Ollama daemon not responding at http://127.0.0.1:11434.")
        print("  Please ensure 'ollama serve' is active.")
    return False

def wait_for_backend(url="http://127.0.0.1:8000/api/health", timeout=45):
    """Poll backend health check until 200 OK or timeout."""
    print("  Waiting for FastAPI to initialize models and Qdrant DB ...", end="", flush=True)
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "run_dev_health"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                if resp.status == 200:
                    print(f" [ONLINE in {time.time() - start:.1f}s]")
                    return True
        except Exception:
            pass
        print(".", end="", flush=True)
        time.sleep(1.0)
    print(" [TIMEOUT]")
    return False

def kill_proc_tree(proc):
    """Reliably kill a process and all its children across OS platforms."""
    if proc is None:
        return
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
        else:
            proc.terminate()
            proc.wait(timeout=3)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass

def main():
    print("=" * 70)
    print("  ENTERPRISE HYBRID RAG ENGINE - LOCAL UNIFIED LAUNCHER")
    print("=" * 70)
    
    check_ollama()
    ensure_port_clean(8000)
    
    venv_python = get_venv_python()
    print(f"✓ Python Interpreter: {venv_python}")
    
    # 1. Start FastAPI Backend on 127.0.0.1:8000
    print("\n[1/2] Starting FastAPI Backend on http://127.0.0.1:8000 ...")
    backend_env = os.environ.copy()
    backend_env["CUDA_VISIBLE_DEVICES"] = ""
    backend_env["PYTHONPATH"] = f"{ROOT_DIR}{os.pathsep}{BACKEND_DIR}"
    
    backend_cmd = [
        venv_python, "-m", "uvicorn", "backend.api:app",
        "--host", "127.0.0.1",
        "--port", "8000"
    ]
    
    backend_proc = subprocess.Popen(
        backend_cmd,
        cwd=str(ROOT_DIR),
        env=backend_env
    )

    # Health check wait: block until FastAPI loads Qdrant and Cross-Encoder weights
    is_healthy = wait_for_backend("http://127.0.0.1:8000/api/health", timeout=45)
    if not is_healthy:
        print("❌ Backend failed to become healthy within timeout. Shutting down...")
        kill_proc_tree(backend_proc)
        sys.exit(1)

    # 2. Start Vite React Frontend
    print("\n[2/2] Starting Vite React Frontend on http://localhost:5173 ...")
    shell_mode = (os.name == "nt")
    frontend_cmd = "npm run dev" if shell_mode else ["npm", "run", "dev"]
    frontend_proc = subprocess.Popen(
        frontend_cmd,
        cwd=str(FRONTEND_DIR),
        shell=shell_mode
    )

    print("\n" + "=" * 70)
    print("  ALL SERVICES ONLINE & FULLY GROUNDED:")
    print("  → Frontend React UI:  http://localhost:5173  (Proxy: /api → 127.0.0.1:8000)")
    print("  → Backend API & Docs: http://127.0.0.1:8000/docs")
    print("  → API Health Check:   http://127.0.0.1:8000/api/health")
    print("  Press Ctrl+C to terminate both servers.")
    print("=" * 70 + "\n")

    def signal_handler(sig, frame):
        print("\nGracefully shutting down Enterprise Hybrid RAG services...")
        kill_proc_tree(frontend_proc)
        kill_proc_tree(backend_proc)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        while True:
            time.sleep(1)
            if backend_proc.poll() is not None:
                print("Backend process terminated unexpectedly.")
                break
            if frontend_proc.poll() is not None:
                print("Frontend process terminated unexpectedly.")
                break
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()
