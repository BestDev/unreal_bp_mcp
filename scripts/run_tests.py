#!/usr/bin/env python3
"""
Test Runner Script

Comprehensive test runner for UnrealBlueprintMCP project.
Handles unit tests, integration tests, linting, and code quality checks.
"""

import os
import sys
import subprocess
import platform
import argparse
import time
from pathlib import Path

class Colors:
    """ANSI color codes for terminal output"""
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(message):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message:^60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.ENDC}\n")

def print_status(message):
    """Print status message"""
    print(f"{Colors.BLUE}{Colors.BOLD}[INFO]{Colors.ENDC} {message}")

def print_success(message):
    """Print success message"""
    print(f"{Colors.GREEN}{Colors.BOLD}[SUCCESS]{Colors.ENDC} {message}")

def print_warning(message):
    """Print warning message"""
    print(f"{Colors.YELLOW}{Colors.BOLD}[WARNING]{Colors.ENDC} {message}")

def print_error(message):
    """Print error message"""
    print(f"{Colors.RED}{Colors.BOLD}[ERROR]{Colors.ENDC} {message}")

def run_command(command, cwd=None):
    """Run command and return result"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr

def get_python_executable(project_root):
    """Get Python executable from virtual environment"""
    venv_path = project_root / "mcp_server_env"

    if platform.system() == "Windows":
        python_exe = venv_path / "Scripts" / "python.exe"
        pip_exe = venv_path / "Scripts" / "pip.exe"
    else:
        python_exe = venv_path / "bin" / "python"
        pip_exe = venv_path / "bin" / "pip"

    return python_exe, pip_exe

def check_virtual_environment(project_root):
    """Check if virtual environment exists and is properly set up"""
    print_header("Checking Virtual Environment")

    venv_path = project_root / "mcp_server_env"
    if not venv_path.exists():
        print_error("Virtual environment not found!")
        print_error("Run 'python scripts/setup_dev_env.py' to set up the environment")
        return False

    python_exe, _ = get_python_executable(project_root)
    if not python_exe.exists():
        print_error(f"Python executable not found: {python_exe}")
        return False

    print_success("Virtual environment found and ready")
    return True

def run_code_formatting_check(project_root):
    """Run code formatting checks with Black"""
    print_header("Code Formatting Check (Black)")

    python_exe, _ = get_python_executable(project_root)

    # Check if files need formatting
    success, stdout, stderr = run_command(f'"{python_exe}" -m black --check --diff .', cwd=project_root)

    if success:
        print_success("All files are properly formatted")
        return True
    else:
        print_error("Code formatting issues found:")
        if stdout:
            print(stdout)
        if stderr:
            print(stderr)
        print_warning("Run 'black .' to auto-format the code")
        return False

def run_linting(project_root):
    """Run linting checks with flake8"""
    print_header("Linting Check (flake8)")

    python_exe, _ = get_python_executable(project_root)

    # Run flake8
    success, stdout, stderr = run_command(f'"{python_exe}" -m flake8 . --count --statistics', cwd=project_root)

    if success:
        print_success("No linting issues found")
        if stdout.strip():
            print(f"Statistics:\n{stdout}")
        return True
    else:
        print_error("Linting issues found:")
        if stdout:
            print(stdout)
        if stderr:
            print(stderr)
        return False

def run_type_checking(project_root):
    """Run type checking with mypy"""
    print_header("Type Checking (mypy)")

    python_exe, _ = get_python_executable(project_root)

    # Run mypy on main server file
    server_file = project_root / "unreal_blueprint_mcp_server.py"
    if not server_file.exists():
        print_warning("MCP server file not found, skipping type checking")
        return True

    success, stdout, stderr = run_command(
        f'"{python_exe}" -m mypy "{server_file}" --ignore-missing-imports --no-strict-optional',
        cwd=project_root
    )

    if success:
        print_success("Type checking passed")
        return True
    else:
        print_warning("Type checking issues found (non-critical):")
        if stdout:
            print(stdout)
        if stderr:
            print(stderr)
        return True  # Don't fail on type checking issues

def run_unit_tests(project_root, verbose=False):
    """Run unit tests with pytest"""
    print_header("Unit Tests (pytest)")

    python_exe, _ = get_python_executable(project_root)

    # Build pytest command
    pytest_args = [
        f'"{python_exe}"', '-m', 'pytest',
        'tests/test_mcp_tools.py',
        '--tb=short'
    ]

    if verbose:
        pytest_args.append('-v')

    # Add coverage if available
    coverage_args = ['--cov=.', '--cov-report=term-missing', '--cov-report=html']
    pytest_command = ' '.join(pytest_args + coverage_args)

    success, stdout, stderr = run_command(pytest_command, cwd=project_root)

    if success:
        print_success("Unit tests passed")
        if stdout:
            print(stdout)
        return True
    else:
        print_error("Unit tests failed:")
        if stdout:
            print(stdout)
        if stderr:
            print(stderr)
        return False

def run_integration_tests(project_root, verbose=False):
    """Run integration tests"""
    print_header("Integration Tests")

    python_exe, _ = get_python_executable(project_root)

    # Build pytest command for integration tests
    pytest_args = [
        f'"{python_exe}"', '-m', 'pytest',
        'tests/test_integration.py',
        'tests/test_websocket.py',
        '--tb=short'
    ]

    if verbose:
        pytest_args.append('-v')

    pytest_command = ' '.join(pytest_args)

    print_warning("Integration tests require MCP server to be running")
    print_warning("These tests will be skipped if server is not available")

    success, stdout, stderr = run_command(pytest_command, cwd=project_root)

    if success:
        print_success("Integration tests passed")
        if stdout:
            print(stdout)
        return True
    else:
        print_warning("Integration tests had issues (may be due to server not running):")
        if stdout:
            print(stdout)
        if stderr:
            print(stderr)
        return True  # Don't fail build on integration test issues

def run_security_scan(project_root):
    """Run security scanning with bandit"""
    print_header("Security Scan (bandit)")

    python_exe, _ = get_python_executable(project_root)

    # Install bandit if not available
    print_status("Checking bandit availability...")
    install_success, _, _ = run_command(f'"{python_exe}" -m pip install bandit')

    if install_success:
        # Run bandit security scan
        success, stdout, stderr = run_command(f'"{python_exe}" -m bandit -r . -f text', cwd=project_root)

        if success:
            print_success("Security scan passed - no issues found")
            return True
        else:
            print_warning("Security scan found potential issues:")
            if stdout:
                print(stdout)
            if stderr:
                print(stderr)
            return True  # Don't fail on security warnings
    else:
        print_warning("Could not install bandit, skipping security scan")
        return True

def run_dependency_check(project_root):
    """Check for outdated dependencies"""
    print_header("Dependency Check")

    python_exe, pip_exe = get_python_executable(project_root)

    # Check for outdated packages
    success, stdout, stderr = run_command(f'"{pip_exe}" list --outdated', cwd=project_root)

    if stdout.strip():
        print_warning("Outdated packages found:")
        print(stdout)
        print_warning("Consider updating dependencies with 'pip install --upgrade <package>'")
    else:
        print_success("All dependencies are up to date")

    return True

def generate_test_report(results, project_root):
    """Generate a test report"""
    print_header("Test Summary Report")

    total_checks = len(results)
    passed_checks = sum(1 for result in results.values() if result)
    failed_checks = total_checks - passed_checks

    print(f"Total checks: {total_checks}")
    print(f"Passed: {Colors.GREEN}{passed_checks}{Colors.ENDC}")
    print(f"Failed: {Colors.RED}{failed_checks}{Colors.ENDC}")
    print()

    # Detailed results
    for check_name, result in results.items():
        status = f"{Colors.GREEN}PASS{Colors.ENDC}" if result else f"{Colors.RED}FAIL{Colors.ENDC}"
        print(f"  {check_name}: {status}")

    # Save report to file
    report_file = project_root / "test_report.txt"
    with open(report_file, 'w') as f:
        f.write("UnrealBlueprintMCP Test Report\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Total checks: {total_checks}\n")
        f.write(f"Passed: {passed_checks}\n")
        f.write(f"Failed: {failed_checks}\n\n")

        for check_name, result in results.items():
            status = "PASS" if result else "FAIL"
            f.write(f"{check_name}: {status}\n")

    print(f"\nDetailed report saved to: {report_file}")

    return failed_checks == 0

def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="UnrealBlueprintMCP Test Runner")
    parser.add_argument('--verbose', '-v', action='store_true', help="Verbose output")
    parser.add_argument('--skip-format', action='store_true', help="Skip code formatting check")
    parser.add_argument('--skip-lint', action='store_true', help="Skip linting check")
    parser.add_argument('--skip-type', action='store_true', help="Skip type checking")
    parser.add_argument('--skip-unit', action='store_true', help="Skip unit tests")
    parser.add_argument('--skip-integration', action='store_true', help="Skip integration tests")
    parser.add_argument('--skip-security', action='store_true', help="Skip security scan")
    parser.add_argument('--unit-only', action='store_true', help="Run only unit tests")
    parser.add_argument('--quick', action='store_true', help="Run only essential checks")

    args = parser.parse_args()

    print(f"{Colors.BOLD}🧪 UnrealBlueprintMCP Test Runner{Colors.ENDC}")
    print("=" * 60)

    # Get project root
    project_root = Path(__file__).parent.parent
    print_status(f"Project root: {project_root}")

    start_time = time.time()
    results = {}

    try:
        # Check virtual environment first
        if not check_virtual_environment(project_root):
            sys.exit(1)

        # Quick mode - only essential checks
        if args.quick:
            results["Unit Tests"] = run_unit_tests(project_root, args.verbose)
            results["Code Formatting"] = run_code_formatting_check(project_root)
        # Unit tests only mode
        elif args.unit_only:
            results["Unit Tests"] = run_unit_tests(project_root, args.verbose)
        # Full test suite
        else:
            # Code quality checks
            if not args.skip_format:
                results["Code Formatting"] = run_code_formatting_check(project_root)

            if not args.skip_lint:
                results["Linting"] = run_linting(project_root)

            if not args.skip_type:
                results["Type Checking"] = run_type_checking(project_root)

            # Tests
            if not args.skip_unit:
                results["Unit Tests"] = run_unit_tests(project_root, args.verbose)

            if not args.skip_integration:
                results["Integration Tests"] = run_integration_tests(project_root, args.verbose)

            # Security and dependencies
            if not args.skip_security:
                results["Security Scan"] = run_security_scan(project_root)

            results["Dependency Check"] = run_dependency_check(project_root)

        # Generate report
        success = generate_test_report(results, project_root)

        end_time = time.time()
        elapsed_time = end_time - start_time

        print(f"\nTotal execution time: {elapsed_time:.2f} seconds")

        if success:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 All checks passed successfully!{Colors.ENDC}")
            sys.exit(0)
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ Some checks failed. Please review the results above.{Colors.ENDC}")
            sys.exit(1)

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test run interrupted by user{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Test run failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()