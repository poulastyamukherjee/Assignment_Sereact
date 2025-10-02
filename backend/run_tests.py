#!/usr/bin/env python3
"""
Test runner script for the robot backend application.
This script provides various options for running tests.
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(backend_dir))


def run_command(command, description=""):
    """Run a shell command and return the result."""
    if description:
        print(f"\n{'='*60}")
        print(f"Running: {description}")
        print(f"{'='*60}")
    
    print(f"Command: {' '.join(command)}")
    result = subprocess.run(command, cwd=backend_dir, capture_output=False)
    return result.returncode == 0


def install_dependencies():
    """Install test dependencies."""
    print("Installing test dependencies...")
    return run_command([
        sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
    ], "Installing dependencies")


def run_all_tests():
    """Run all tests with verbose output."""
    return run_command([
        sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"
    ], "Running all tests")


def run_specific_test(test_file):
    """Run a specific test file."""
    # Ensure the test file path includes the tests directory
    if not test_file.startswith("tests/"):
        test_file = f"tests/{test_file}"
    
    return run_command([
        sys.executable, "-m", "pytest", test_file, "-v"
    ], f"Running {test_file}")


def run_tests_with_coverage():
    """Run tests with coverage reporting."""
    # First install coverage if not available
    subprocess.run([sys.executable, "-m", "pip", "install", "pytest-cov"], 
                  cwd=backend_dir, capture_output=True)
    
    return run_command([
        sys.executable, "-m", "pytest", "tests/",
        "--cov=app", 
        "--cov=robot_controller",
        "--cov-report=html",
        "--cov-report=term-missing",
        "-v"
    ], "Running tests with coverage")


def run_unit_tests():
    """Run only unit tests."""
    return run_command([
        sys.executable, "-m", "pytest", "tests/", "-m", "unit", "-v"
    ], "Running unit tests")


def run_integration_tests():
    """Run only integration tests."""
    return run_command([
        sys.executable, "-m", "pytest", "tests/", "-m", "integration", "-v"
    ], "Running integration tests")


def run_flask_tests():
    """Run only Flask endpoint tests."""
    return run_command([
        sys.executable, "-m", "pytest", "tests/", "-m", "flask", "-v"
    ], "Running Flask endpoint tests")


def run_websocket_tests():
    """Run only WebSocket tests."""
    return run_command([
        sys.executable, "-m", "pytest", "tests/", "-m", "websocket", "-v"
    ], "Running WebSocket tests")


def lint_code():
    """Run code linting."""
    # Install flake8 if not available
    subprocess.run([sys.executable, "-m", "pip", "install", "flake8"], 
                  cwd=backend_dir, capture_output=True)
    
    return run_command([
        sys.executable, "-m", "flake8", "app.py", "robot_controller.py", 
        "--max-line-length=100", "--ignore=E501,W503"
    ], "Running code linting")


def check_test_files():
    """Check which test files exist."""
    test_files = [
        "tests/test_app.py",
        "tests/test_websocket.py",
        "tests/conftest.py",
        "tests/pytest.ini"
    ]
    
    print("\nTest file status:")
    print("-" * 40)
    
    for test_file in test_files:
        file_path = backend_dir / test_file
        status = "EXISTS" if file_path.exists() else "MISSING"
        print(f"{test_file:<25} {status}")


def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(description="Robot Backend Test Runner")
    parser.add_argument("--install", action="store_true", 
                       help="Install test dependencies")
    parser.add_argument("--all", action="store_true", 
                       help="Run all tests")
    parser.add_argument("--coverage", action="store_true", 
                       help="Run tests with coverage reporting")
    parser.add_argument("--unit", action="store_true", 
                       help="Run only unit tests")
    parser.add_argument("--integration", action="store_true", 
                       help="Run only integration tests")
    parser.add_argument("--flask", action="store_true", 
                       help="Run only Flask endpoint tests")
    parser.add_argument("--websocket", action="store_true", 
                       help="Run only WebSocket tests")
    parser.add_argument("--lint", action="store_true", 
                       help="Run code linting")
    parser.add_argument("--file", type=str, 
                       help="Run specific test file")
    parser.add_argument("--check", action="store_true", 
                       help="Check test file status")
    
    args = parser.parse_args()
    
    # If no arguments provided, show help
    if not any(vars(args).values()):
        parser.print_help()
        print("\nAvailable test files:")
        check_test_files()
        return
    
    success = True
    
    try:
        if args.check:
            check_test_files()
        
        if args.install:
            success &= install_dependencies()
        
        if args.lint:
            success &= lint_code()
        
        if args.file:
            success &= run_specific_test(args.file)
        
        if args.unit:
            success &= run_unit_tests()
        
        if args.integration:
            success &= run_integration_tests()
        
        if args.flask:
            success &= run_flask_tests()
        
        if args.websocket:
            success &= run_websocket_tests()
        
        if args.coverage:
            success &= run_tests_with_coverage()
        
        if args.all:
            success &= run_all_tests()
        
        # Print final result
        print(f"\n{'='*60}")
        if success:
            print("All operations completed successfully!")
        else:
            print("Some operations failed. Check the output above.")
        print(f"{'='*60}")
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\nTest run interrupted by user.")
        return 1
    except Exception as e:
        print(f"\nError running tests: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)