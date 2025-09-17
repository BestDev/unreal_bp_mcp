#!/usr/bin/env python3
"""
Development Environment Setup Script

Automatically sets up the development environment for UnrealBlueprintMCP.
This script handles Python virtual environment, dependency installation,
and basic configuration.
"""

import os
import sys
import subprocess
import platform
import venv
from pathlib import Path

class Colors:
    """ANSI color codes for terminal output"""
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_status(message, color=Colors.BLUE):
    """Print colored status message"""
    print(f"{color}{Colors.BOLD}[INFO]{Colors.ENDC} {message}")

def print_success(message):
    """Print success message"""
    print(f"{Colors.GREEN}{Colors.BOLD}[SUCCESS]{Colors.ENDC} {message}")

def print_warning(message):
    """Print warning message"""
    print(f"{Colors.YELLOW}{Colors.BOLD}[WARNING]{Colors.ENDC} {message}")

def print_error(message):
    """Print error message"""
    print(f"{Colors.RED}{Colors.BOLD}[ERROR]{Colors.ENDC} {message}")

def run_command(command, cwd=None, check=True):
    """Run command and return result"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=check
        )
        return result
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {command}")
        print_error(f"Error: {e.stderr}")
        if check:
            raise
        return e

def check_python_version():
    """Check if Python version is compatible"""
    print_status("Checking Python version...")

    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error(f"Python 3.8+ required, found {version.major}.{version.minor}")
        return False

    print_success(f"Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def check_git():
    """Check if git is available"""
    print_status("Checking Git availability...")

    try:
        result = run_command("git --version")
        print_success(f"Git is available: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError:
        print_warning("Git not found - some features may not work")
        return False

def create_virtual_environment(project_root):
    """Create Python virtual environment"""
    print_status("Creating Python virtual environment...")

    venv_path = project_root / "mcp_server_env"

    if venv_path.exists():
        print_warning(f"Virtual environment already exists at {venv_path}")
        return venv_path

    # Create virtual environment
    venv.create(venv_path, with_pip=True)
    print_success(f"Virtual environment created at {venv_path}")

    return venv_path

def get_activation_command(venv_path):
    """Get the appropriate activation command for the platform"""
    if platform.system() == "Windows":
        return str(venv_path / "Scripts" / "activate.bat")
    else:
        return f"source {venv_path / 'bin' / 'activate'}"

def install_dependencies(project_root, venv_path):
    """Install Python dependencies"""
    print_status("Installing Python dependencies...")

    requirements_file = project_root / "requirements.txt"
    if not requirements_file.exists():
        print_error(f"Requirements file not found: {requirements_file}")
        return False

    # Get Python executable in virtual environment
    if platform.system() == "Windows":
        python_exe = venv_path / "Scripts" / "python.exe"
        pip_exe = venv_path / "Scripts" / "pip.exe"
    else:
        python_exe = venv_path / "bin" / "python"
        pip_exe = venv_path / "bin" / "pip"

    # Upgrade pip first
    print_status("Upgrading pip...")
    run_command(f'"{python_exe}" -m pip install --upgrade pip')

    # Install requirements
    print_status("Installing project dependencies...")
    run_command(f'"{pip_exe}" install -r "{requirements_file}"')

    # Install development dependencies
    dev_packages = [
        "pytest",
        "pytest-asyncio",
        "pytest-cov",
        "black",
        "flake8",
        "mypy"
    ]

    print_status("Installing development dependencies...")
    for package in dev_packages:
        print_status(f"Installing {package}...")
        run_command(f'"{pip_exe}" install {package}')

    print_success("All dependencies installed successfully")
    return True

def setup_git_hooks(project_root):
    """Setup Git pre-commit hooks"""
    print_status("Setting up Git pre-commit hooks...")

    hooks_dir = project_root / ".git" / "hooks"
    if not hooks_dir.exists():
        print_warning("Not a Git repository - skipping Git hooks setup")
        return False

    # Create pre-commit hook
    pre_commit_hook = hooks_dir / "pre-commit"
    hook_content = """#!/bin/bash
# Pre-commit hook for UnrealBlueprintMCP

echo "Running pre-commit checks..."

# Activate virtual environment
source mcp_server_env/bin/activate 2>/dev/null || source mcp_server_env/Scripts/activate 2>/dev/null

# Run black formatter
echo "Checking code formatting with black..."
black --check . || {
    echo "Code formatting issues found. Run 'black .' to fix."
    exit 1
}

# Run flake8 linter
echo "Running flake8 linter..."
flake8 . || {
    echo "Linting issues found. Please fix them."
    exit 1
}

# Run tests
echo "Running tests..."
pytest tests/ -x || {
    echo "Tests failed. Please fix them."
    exit 1
}

echo "All pre-commit checks passed!"
"""

    with open(pre_commit_hook, 'w') as f:
        f.write(hook_content)

    # Make executable
    pre_commit_hook.chmod(0o755)

    print_success("Git pre-commit hooks set up successfully")
    return True

def create_development_config(project_root):
    """Create development configuration files"""
    print_status("Creating development configuration files...")

    # Create .gitignore if it doesn't exist
    gitignore_path = project_root / ".gitignore"
    if not gitignore_path.exists():
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
mcp_server_env/
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Coverage
.coverage
htmlcov/
.pytest_cache/

# Unreal Engine
Binaries/
Intermediate/
Saved/
*.tmp
*.temp

# Temporary files
.tmp/
temp/
"""

        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)

        print_success(".gitignore created")

    # Create .markdownlint.json for documentation
    markdownlint_config = project_root / ".markdownlint.json"
    if not markdownlint_config.exists():
        config_content = """{
  "MD013": { "line_length": 120 },
  "MD033": false,
  "MD041": false
}"""

        with open(markdownlint_config, 'w') as f:
            f.write(config_content)

        print_success(".markdownlint.json created")

def verify_installation(project_root, venv_path):
    """Verify that the installation was successful"""
    print_status("Verifying installation...")

    # Get Python executable
    if platform.system() == "Windows":
        python_exe = venv_path / "Scripts" / "python.exe"
    else:
        python_exe = venv_path / "bin" / "python"

    # Test importing main modules
    test_imports = [
        "fastmcp",
        "pydantic",
        "websockets",
        "pytest",
        "black"
    ]

    for module in test_imports:
        try:
            result = run_command(f'"{python_exe}" -c "import {module}; print(f\'{module} imported successfully\')"')
            print_success(f"{module} import test passed")
        except subprocess.CalledProcessError:
            print_error(f"Failed to import {module}")
            return False

    # Test MCP server syntax
    server_file = project_root / "unreal_blueprint_mcp_server.py"
    if server_file.exists():
        try:
            result = run_command(f'"{python_exe}" -m py_compile "{server_file}"')
            print_success("MCP server syntax check passed")
        except subprocess.CalledProcessError:
            print_error("MCP server has syntax errors")
            return False

    print_success("Installation verification completed successfully")
    return True

def print_next_steps(project_root, venv_path):
    """Print next steps for the developer"""
    activation_cmd = get_activation_command(venv_path)

    print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 Development environment setup complete!{Colors.ENDC}\n")

    print(f"{Colors.BOLD}Next steps:{Colors.ENDC}")
    print(f"1. Activate the virtual environment:")
    print(f"   {Colors.BLUE}{activation_cmd}{Colors.ENDC}")
    print()
    print(f"2. Start the MCP server:")
    print(f"   {Colors.BLUE}fastmcp dev unreal_blueprint_mcp_server.py{Colors.ENDC}")
    print()
    print(f"3. Run tests:")
    print(f"   {Colors.BLUE}pytest tests/ -v{Colors.ENDC}")
    print()
    print(f"4. Format code:")
    print(f"   {Colors.BLUE}black .{Colors.ENDC}")
    print()
    print(f"5. Lint code:")
    print(f"   {Colors.BLUE}flake8 .{Colors.ENDC}")
    print()
    print(f"{Colors.BOLD}Documentation:{Colors.ENDC}")
    print(f"- README.md - Project overview and quick start")
    print(f"- INSTALLATION_GUIDE.md - Detailed installation instructions")
    print(f"- docs/API_REFERENCE.md - Complete API documentation")
    print(f"- docs/MCP_CLIENT_SETUP.md - AI client integration guide")
    print()
    print(f"{Colors.BOLD}Happy coding! 🚀{Colors.ENDC}")

def main():
    """Main setup function"""
    print(f"{Colors.BOLD}🔧 UnrealBlueprintMCP Development Environment Setup{Colors.ENDC}")
    print("=" * 60)

    # Get project root
    project_root = Path(__file__).parent.parent
    print_status(f"Project root: {project_root}")

    try:
        # Check prerequisites
        if not check_python_version():
            sys.exit(1)

        check_git()

        # Setup virtual environment
        venv_path = create_virtual_environment(project_root)

        # Install dependencies
        if not install_dependencies(project_root, venv_path):
            sys.exit(1)

        # Setup development tools
        setup_git_hooks(project_root)
        create_development_config(project_root)

        # Verify installation
        if not verify_installation(project_root, venv_path):
            sys.exit(1)

        # Print next steps
        print_next_steps(project_root, venv_path)

    except KeyboardInterrupt:
        print_error("\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()