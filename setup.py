#!/usr/bin/env python3
"""
Jenny Assistant - Automated Setup Script (Python version)
Cross-platform setup script for Windows, macOS, and Linux
"""

import os
import subprocess
import sys
import time
import platform
from pathlib import Path

# Colors for terminal output
class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

    @staticmethod
    def is_windows():
        return platform.system() == 'Windows'

    @classmethod
    def print_status(cls, message):
        if cls.is_windows():
            print(f"✓ {message}")
        else:
            print(f"{cls.GREEN}✓{cls.NC} {message}")

    @classmethod
    def print_warning(cls, message):
        if cls.is_windows():
            print(f"⚠ {message}")
        else:
            print(f"{cls.YELLOW}⚠{cls.NC} {message}")

    @classmethod
    def print_error(cls, message):
        if cls.is_windows():
            print(f"✗ {message}")
        else:
            print(f"{cls.RED}✗{cls.NC} {message}")

    @classmethod
    def print_header(cls, message):
        if cls.is_windows():
            print(f"\n{message}")
        else:
            print(f"\n{cls.BLUE}{message}{cls.NC}")


def run_command(cmd, check=True, capture_output=False):
    """Run a shell command"""
    try:
        if capture_output:
            result = subprocess.run(cmd, shell=True, check=check,
                                   capture_output=True, text=True)
            return result.stdout.strip()
        else:
            subprocess.run(cmd, shell=True, check=check)
            return True
    except subprocess.CalledProcessError:
        return False


def check_python_version():
    """Check if Python version is >= 3.11"""
    Colors.print_header("Step 1: Checking Python version...")

    version = sys.version_info
    if version.major >= 3 and version.minor >= 11:
        Colors.print_status(f"Python {version.major}.{version.minor}.{version.micro} detected (>= 3.11 required)")
        return True
    else:
        Colors.print_error(f"Python 3.11 or higher required. Found: {version.major}.{version.minor}.{version.micro}")
        print("Install Python 3.11+: https://www.python.org/downloads/")
        return False


def check_docker():
    """Check if Docker is installed and running"""
    Colors.print_header("Step 2: Checking Docker...")

    # Check Docker
    docker_version = run_command("docker --version", capture_output=True)
    if not docker_version:
        Colors.print_error("Docker not found")
        print("Install Docker: https://docs.docker.com/get-docker/")
        return False

    Colors.print_status(f"Docker detected: {docker_version}")

    # Check if Docker daemon is running
    if not run_command("docker info", check=False):
        Colors.print_error("Docker is installed but not running")
        print("Please start Docker Desktop or Docker daemon")
        return False

    Colors.print_status("Docker daemon is running")

    # Check Docker Compose
    compose_version = run_command("docker compose version", capture_output=True)
    if not compose_version:
        compose_version = run_command("docker-compose --version", capture_output=True)
        if not compose_version:
            Colors.print_error("Docker Compose not found")
            return False

    Colors.print_status(f"Docker Compose detected: {compose_version}")
    return True


def install_dependencies():
    """Install Python dependencies"""
    Colors.print_header("Step 3: Installing Python dependencies...")

    if not Path("requirements.txt").exists():
        Colors.print_error("requirements.txt not found")
        return False

    print("Installing packages (this may take a minute)...")
    if run_command(f"{sys.executable} -m pip install -r requirements.txt --quiet"):
        Colors.print_status("Python dependencies installed")
        return True
    else:
        Colors.print_error("Failed to install Python dependencies")
        return False


def configure_environment():
    """Set up .env file"""
    Colors.print_header("Step 4: Configuring environment...")

    env_file = Path(".env")
    env_example = Path(".env.example")

    if env_file.exists():
        Colors.print_warning(".env file already exists")
        response = input("Do you want to overwrite it? (y/N): ").lower()
        if response != 'y':
            Colors.print_status("Keeping existing .env file")
            return True

    # Copy .env.example to .env
    if not env_example.exists():
        Colors.print_error(".env.example not found")
        return False

    with open(env_example, 'r') as src, open(env_file, 'w') as dst:
        dst.write(src.read())

    Colors.print_status("Created .env file from template")

    # Check OpenAI API key
    with open(env_file, 'r') as f:
        content = f.read()

    if 'OPENAI_API_KEY=your-openai-api-key-here' in content or 'OPENAI_API_KEY=' in content:
        Colors.print_warning("OpenAI API key not configured")
        print("\nYou need to add your OpenAI API key to .env file")
        print("Get your API key from: https://platform.openai.com/api-keys\n")

        api_key = input("Enter your OpenAI API key (or press Enter to skip): ").strip()

        if api_key:
            # Replace placeholder with actual key
            content = content.replace('OPENAI_API_KEY=your-openai-api-key-here', f'OPENAI_API_KEY={api_key}')
            with open(env_file, 'w') as f:
                f.write(content)
            Colors.print_status("OpenAI API key configured")
        else:
            Colors.print_warning("You'll need to manually add your API key to .env before running Jenny")
    else:
        Colors.print_status("OpenAI API key already configured")

    return True


def start_docker_services():
    """Start Docker containers"""
    Colors.print_header("Step 5: Starting Docker services (PostgreSQL, Redis, Neo4j)...")
    print("This may take 30-60 seconds for first-time setup...\n")

    # Determine compose command
    compose_cmd = "docker compose"
    if not run_command(f"{compose_cmd} version", check=False):
        compose_cmd = "docker-compose"

    # Start services
    if not run_command(f"{compose_cmd} up -d"):
        Colors.print_error("Failed to start Docker services")
        return False

    Colors.print_status("Docker services started")

    # Wait for services
    print("\nWaiting for services to be ready...")
    time.sleep(5)

    # Check PostgreSQL
    print("  Checking PostgreSQL... ", end='', flush=True)
    for _ in range(30):
        if run_command("docker exec jenny-postgres pg_isready -U jenny", check=False):
            Colors.print_status("")
            break
        time.sleep(1)
    else:
        Colors.print_warning("(timeout - might still be starting)")

    # Check Redis
    print("  Checking Redis... ", end='', flush=True)
    for _ in range(30):
        if run_command("docker exec jenny-redis redis-cli ping", check=False):
            Colors.print_status("")
            break
        time.sleep(1)
    else:
        Colors.print_warning("(timeout - might still be starting)")

    # Check Neo4j
    print("  Checking Neo4j... ", end='', flush=True)
    for _ in range(60):
        if run_command("docker exec jenny-neo4j wget -q --spider http://localhost:7474", check=False):
            Colors.print_status("")
            break
        time.sleep(1)
    else:
        Colors.print_warning("(timeout - Neo4j can take up to 2 minutes)")

    return True


def print_final_instructions():
    """Print final setup instructions"""
    print("\n" + "=" * 50)
    Colors.print_status("Installation Complete!")
    print("=" * 50)
    print("\nNext steps:\n")
    print("1. Start Mem0 service (Terminal 1):")
    print("   python -m uvicorn app.mem0.server.main:app --port 8081\n")
    print("2. Start Jenny main app (Terminal 2):")
    print("   python -m uvicorn app.main:app --port 8044\n")
    print("3. Test the installation:")
    print("   curl http://localhost:8044/health\n")
    print("Database access:")
    print("  - PostgreSQL: localhost:5432 (user: jenny, password: jenny123)")
    print("  - Redis:      localhost:6379")
    print("  - Neo4j:      http://localhost:7474 (user: neo4j, password: jenny123)\n")
    print("Documentation:")
    print("  - Quick Start: README.md")
    print("  - Full Guide:  SETUP.md\n")
    print("Useful commands:")
    compose_cmd = "docker compose" if run_command("docker compose version", check=False) else "docker-compose"
    print(f"  - Stop services:   {compose_cmd} down")
    print(f"  - View logs:       {compose_cmd} logs -f")
    print(f"  - Restart service: {compose_cmd} restart postgres\n")


def main():
    """Main setup function"""
    print("=" * 50)
    print("  Jenny AI Assistant - Automated Setup")
    print("=" * 50)

    # Check if in Jenny directory
    if not Path("requirements.txt").exists():
        Colors.print_error("Please run this script from the Jenny directory")
        sys.exit(1)

    Colors.print_status("Found Jenny directory")

    # Run setup steps
    if not check_python_version():
        sys.exit(1)

    if not check_docker():
        sys.exit(1)

    if not install_dependencies():
        sys.exit(1)

    if not configure_environment():
        sys.exit(1)

    if not start_docker_services():
        sys.exit(1)

    # Print final instructions
    print_final_instructions()

    # Ask if user wants to start services
    response = input("Do you want to start Jenny services now? (y/N): ").lower()
    if response == 'y':
        print("\nStarting services...")
        print("Press Ctrl+C to stop\n")

        # Start services (simplified version - just show commands)
        print("Run these commands in separate terminals:")
        print("\nTerminal 1:")
        print("  python -m uvicorn app.mem0.server.main:app --port 8081")
        print("\nTerminal 2:")
        print("  python -m uvicorn app.main:app --port 8044")
        print("\nOr use the start.py launcher script:")
        print("  python start.py")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup interrupted by user")
        sys.exit(0)
    except Exception as e:
        Colors.print_error(f"An error occurred: {e}")
        sys.exit(1)
