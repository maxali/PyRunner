#!/usr/bin/env python3
"""
Test runner script for PyRunner
Provides convenient test execution with proper service management
"""

import os
import sys
import time
import signal
import subprocess
import argparse
from pathlib import Path


class PyRunnerTestRunner:
    """Test runner for PyRunner with service management"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.service_process = None
        self.service_port = 8000
        self.service_host = "localhost"
        
    def start_service(self):
        """Start the PyRunner service"""
        print("Starting PyRunner service...")
        
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "app.main:app",
            "--host", self.service_host,
            "--port", str(self.service_port),
            "--log-level", "warning"
        ]
        
        self.service_process = subprocess.Popen(
            cmd,
            cwd=self.project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid
        )
        
        # Wait for service to be ready
        self._wait_for_service()
        print(f"✓ Service started on http://{self.service_host}:{self.service_port}")
        
    def stop_service(self):
        """Stop the PyRunner service"""
        if self.service_process is None:
            return
            
        print("Stopping PyRunner service...")
        try:
            # Send SIGTERM to process group
            os.killpg(os.getpgid(self.service_process.pid), signal.SIGTERM)
            
            # Wait for graceful shutdown
            try:
                self.service_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if not stopped gracefully
                os.killpg(os.getpgid(self.service_process.pid), signal.SIGKILL)
                self.service_process.wait()
                
        except (ProcessLookupError, OSError):
            # Process already dead
            pass
        finally:
            self.service_process = None
            print("✓ Service stopped")
    
    def _wait_for_service(self, timeout=30):
        """Wait for service to be ready"""
        import requests
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"http://{self.service_host}:{self.service_port}/", timeout=1)
                if response.status_code == 200:
                    return
            except requests.RequestException:
                pass
            time.sleep(0.5)
        
        raise TimeoutError(f"Service did not start within {timeout} seconds")
    
    def run_tests(self, test_args):
        """Run tests with pytest"""
        cmd = [sys.executable, "-m", "pytest"] + test_args
        
        print(f"Running tests: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=self.project_root)
        return result.returncode
    
    def run_unit_tests(self, verbose=False):
        """Run unit tests only"""
        args = ["tests/unit/", "-m", "unit"]
        if verbose:
            args.extend(["-v", "--tb=short"])
        
        return self.run_tests(args)
    
    def run_integration_tests(self, verbose=False):
        """Run integration tests with service"""
        args = ["tests/integration/", "-m", "integration"]
        if verbose:
            args.extend(["-v", "--tb=short"])
        
        try:
            self.start_service()
            return self.run_tests(args)
        finally:
            self.stop_service()
    
    def run_security_tests(self, verbose=False):
        """Run security tests"""
        args = ["tests/", "-m", "security"]
        if verbose:
            args.extend(["-v", "--tb=short"])
        
        try:
            self.start_service()
            return self.run_tests(args)
        finally:
            self.stop_service()
    
    def run_performance_tests(self, verbose=False):
        """Run performance tests"""
        args = ["tests/", "-m", "performance"]
        if verbose:
            args.extend(["-v", "--tb=short", "--timeout=120"])
        
        try:
            self.start_service()
            return self.run_tests(args)
        finally:
            self.stop_service()
    
    def run_all_tests(self, verbose=False, coverage=False):
        """Run all tests"""
        args = ["tests/"]
        if verbose:
            args.extend(["-v", "--tb=short"])
        if coverage:
            args.extend(["--cov=app", "--cov-report=term-missing", "--cov-report=html"])
        
        try:
            self.start_service()
            return self.run_tests(args)
        finally:
            self.stop_service()
    
    def run_specific_test(self, test_path, verbose=False):
        """Run a specific test file or function"""
        args = [test_path]
        if verbose:
            args.extend(["-v", "--tb=short"])
        
        # Check if test requires service
        if "integration" in test_path or "security" in test_path:
            try:
                self.start_service()
                return self.run_tests(args)
            finally:
                self.stop_service()
        else:
            return self.run_tests(args)


def main():
    parser = argparse.ArgumentParser(description="PyRunner Test Runner")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-c", "--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--security", action="store_true", help="Run security tests only")
    parser.add_argument("--performance", action="store_true", help="Run performance tests only")
    parser.add_argument("--test", help="Run specific test file or function")
    parser.add_argument("--list-tests", action="store_true", help="List available tests")
    
    args = parser.parse_args()
    
    runner = PyRunnerTestRunner()
    
    try:
        if args.list_tests:
            print("Available test categories:")
            print("  --unit          Unit tests (no service required)")
            print("  --integration   Integration tests (requires service)")
            print("  --security      Security validation tests")
            print("  --performance   Performance and resource limit tests")
            print("  --test PATH     Run specific test file or function")
            print("\nExample usage:")
            print("  python run_tests.py --unit -v")
            print("  python run_tests.py --integration --coverage")
            print("  python run_tests.py --test tests/unit/test_security.py")
            print("  python run_tests.py --test tests/integration/test_api.py::TestHealthEndpoint::test_health_check")
            return 0
        
        if args.test:
            return runner.run_specific_test(args.test, args.verbose)
        elif args.unit:
            return runner.run_unit_tests(args.verbose)
        elif args.integration:
            return runner.run_integration_tests(args.verbose)
        elif args.security:
            return runner.run_security_tests(args.verbose)
        elif args.performance:
            return runner.run_performance_tests(args.verbose)
        else:
            return runner.run_all_tests(args.verbose, args.coverage)
            
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1
    finally:
        runner.stop_service()


if __name__ == "__main__":
    sys.exit(main())