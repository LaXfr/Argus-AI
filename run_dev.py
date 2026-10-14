#!/usr/bin/env python3
"""
Enterprise Hybrid RAG - 1-Click Unified Development Launcher
Launches FastAPI Backend (port 8000) and Vite React Frontend (port 5173) concurrently.
Handles graceful multi-process termination upon Ctrl+C.
"""

import sys
import os
import signal
import subprocess
import time
import urllib.request
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"

def check_ollama():
    try:
        req = urllib.request.Request("http://127.0.0.1:11434/api/tags", headers={"User-Agent": "run_dev"})
        with urllib.request.urlopen(req, timeout=2) as resp:
            if resp.status == 200:
                print("✓ Ollama local daemon is active and responsive.")
                return True
    except Exception:
        print("⚠ Warning: Ollama daemon not responding at http://127.0.0.1:11434.")
        print("  Please ensure 'ollama serve' is running in another terminal.")
    return False

def main():
    print("=" * 70)
    print("  ENTERPRISE HYBRID RAG ENGINE - LOCAL UNIFIED LAUNCHER")
    print("=" * 70)
    
    check_ollama()
    
    # 1. Start FastAPI Backend
    print("\n[1/2] Starting FastAPI Backend on http://localhost:8000 ...")
    backend_env = os.environ.copy()
    backend_env["CUDA_VISIBLE_DEVICES"] = ""
    backend_env["PYTHONPATH"] = str(BACKEND_DIR)
    
    backend_cmd = ["uv", "run", "python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
    backend_proc = subprocess.Popen(
        backend_cmd,
        cwd=str(BACKEND_DIR),
        env=backend_env
    )

    # 2. Start Vite React Frontend
    print("[2/2] Starting Vite React Frontend on http://localhost:5173 ...")
    shell_mode = (os.name == "nt")
    frontend_cmd = "npm run dev" if shell_mode else ["npm", "run", "dev"]
    frontend_proc = subprocess.Popen(
        frontend_cmd,
        cwd=str(FRONTEND_DIR),
        shell=shell_mode
    )

    print("\n" + "=" * 70)
    print("  SERVICES RUNNING:")
    print("  → Backend API & Docs: http://localhost:8000/docs")
    print("  → Frontend React UI:  http://localhost:5173")
    print("  Press Ctrl+C to terminate both servers.")
    print("=" * 70 + "\n")

    def signal_handler(sig, frame):
        print("\nShutting down Enterprise Hybrid RAG services...")
        try:
            frontend_proc.terminate()
            backend_proc.terminate()
        except Exception:
            pass
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
