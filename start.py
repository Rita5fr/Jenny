#!/usr/bin/env python3
"""
Jenny Assistant - Service Launcher
Starts both Mem0 and main Jenny services
"""

import subprocess
import sys
import time
import signal
import requests
from pathlib import Path

# Process IDs for cleanup
processes = []


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\nShutting down services...")
    for p in processes:
        if p.poll() is None:  # Process still running
            p.terminate()
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()
    print("All services stopped")
    sys.exit(0)


def check_port_available(port):
    """Check if a port is available"""
    try:
        response = requests.get(f"http://localhost:{port}/health", timeout=1)
        return False  # Port in use
    except:
        return True  # Port available


def wait_for_service(port, service_name, max_wait=30):
    """Wait for a service to be ready"""
    print(f"Waiting for {service_name} to start...", end='', flush=True)
    for i in range(max_wait):
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=1)
            if response.status_code == 200:
                print(" ✓")
                return True
        except:
            pass
        time.sleep(1)
        if i % 5 == 0:
            print(".", end='', flush=True)
    print(" ✗ (timeout)")
    return False


def main():
    global processes

    # Register signal handler for clean shutdown
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signal_handler)

    print("=" * 50)
    print("  Jenny AI Assistant - Service Launcher")
    print("=" * 50)
    print()

    # Check if in Jenny directory
    if not Path("requirements.txt").exists():
        print("✗ Please run this script from the Jenny directory")
        sys.exit(1)

    # Check if .env exists
    if not Path(".env").exists():
        print("✗ .env file not found. Run setup first:")
        print("  python setup.py")
        sys.exit(1)

    # Check if ports are available
    if not check_port_available(8081):
        print("⚠ Port 8081 is already in use (Mem0 service)")
        print("  Stop existing service or use a different port")
        sys.exit(1)

    if not check_port_available(8044):
        print("⚠ Port 8044 is already in use (Jenny main app)")
        print("  Stop existing service or use a different port")
        sys.exit(1)

    print("✓ Ports available")
    print()

    # Start Mem0 service
    print("Starting Mem0 microservice on port 8081...")
    mem0_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.mem0.server.main:app",
         "--host", "0.0.0.0", "--port", "8081"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    processes.append(mem0_process)

    # Wait for Mem0 to start
    if not wait_for_service(8081, "Mem0", max_wait=30):
        print("✗ Failed to start Mem0 service")
        signal_handler(None, None)
        sys.exit(1)

    print()

    # Start main Jenny app
    print("Starting Jenny main application on port 8044...")
    main_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app",
         "--host", "0.0.0.0", "--port", "8044"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    processes.append(main_process)

    # Wait for main app to start
    if not wait_for_service(8044, "Jenny", max_wait=30):
        print("✗ Failed to start Jenny main service")
        signal_handler(None, None)
        sys.exit(1)

    print()
    print("=" * 50)
    print("✓ All services started successfully!")
    print("=" * 50)
    print()
    print("Service URLs:")
    print("  - Mem0:  http://localhost:8081")
    print("  - Jenny: http://localhost:8044")
    print()
    print("Try it out:")
    print('  curl http://localhost:8044/health')
    print('  curl -X POST http://localhost:8044/ask \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"user_id":"test","text":"Hello Jenny!"}\'')
    print()
    print("Database interfaces:")
    print("  - Neo4j Browser: http://localhost:7474 (neo4j/jenny123)")
    print("  - PostgreSQL:    localhost:5432 (jenny/jenny123)")
    print("  - Redis:         localhost:6379")
    print()
    print("Press Ctrl+C to stop all services")
    print()

    # Keep services running and monitor them
    try:
        while True:
            # Check if processes are still running
            for i, p in enumerate(processes):
                if p.poll() is not None:
                    service = "Mem0" if i == 0 else "Jenny"
                    print(f"\n✗ {service} service stopped unexpectedly")
                    print("Check logs for errors")
                    signal_handler(None, None)
                    sys.exit(1)
            time.sleep(1)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        signal_handler(None, None)
        sys.exit(1)
