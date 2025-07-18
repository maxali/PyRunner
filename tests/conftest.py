"""Pytest configuration and fixtures for PyRunner tests"""

import asyncio
import subprocess
import time
import signal
import os
import sys
from pathlib import Path
import pytest
import httpx
from typing import AsyncGenerator, Generator


# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from tests.fixtures.test_data import VALID_CODE_SAMPLES, INVALID_CODE_SAMPLES, EXPECTED_OUTPUTS, EXPECTED_ERRORS


class PyRunnerService:
    """Service manager for PyRunner during tests"""
    
    def __init__(self, host: str = "localhost", port: int = 8000):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.process = None
        self.startup_timeout = 30
        
    async def start(self):
        """Start the PyRunner service"""
        if self.process is not None:
            return
            
        # Start the service using uvicorn
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "app.main:app",
            "--host", self.host,
            "--port", str(self.port),
            "--log-level", "warning"
        ]
        
        # Change to the project root directory
        project_root = Path(__file__).parent.parent
        self.process = subprocess.Popen(
            cmd,
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid  # Create process group for cleanup
        )
        
        # Wait for service to be ready
        await self._wait_for_service()
        
    async def stop(self):
        """Stop the PyRunner service"""
        if self.process is None:
            return
            
        try:
            # Send SIGTERM to process group
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            
            # Wait for graceful shutdown
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if not stopped gracefully
                os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                self.process.wait()
                
        except (ProcessLookupError, OSError):
            # Process already dead
            pass
        finally:
            self.process = None
            
    async def _wait_for_service(self):
        """Wait for service to be ready"""
        start_time = time.time()
        
        while time.time() - start_time < self.startup_timeout:
            try:
                async with httpx.AsyncClient(timeout=1.0) as client:
                    response = await client.get(f"{self.base_url}/")
                    if response.status_code == 200:
                        return
            except (httpx.RequestError, httpx.TimeoutException):
                pass
            
            await asyncio.sleep(0.5)
            
        raise TimeoutError(f"Service did not start within {self.startup_timeout} seconds")
        
    async def health_check(self):
        """Check if service is healthy"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/")
                return response.status_code == 200
        except (httpx.RequestError, httpx.TimeoutException):
            return False
            
    def is_running(self):
        """Check if service process is running"""
        return self.process is not None and self.process.poll() is None


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def pyrunner_service() -> AsyncGenerator[PyRunnerService, None]:
    """Start PyRunner service for integration tests"""
    service = PyRunnerService()
    await service.start()
    
    try:
        yield service
    finally:
        await service.stop()


@pytest.fixture
async def api_client(pyrunner_service: PyRunnerService) -> AsyncGenerator[httpx.AsyncClient, None]:
    """HTTP client for API tests"""
    async with httpx.AsyncClient(
        base_url=pyrunner_service.base_url,
        timeout=30.0
    ) as client:
        yield client


@pytest.fixture
def valid_code_samples():
    """Valid code samples for testing"""
    return VALID_CODE_SAMPLES


@pytest.fixture
def invalid_code_samples():
    """Invalid code samples for testing"""
    return INVALID_CODE_SAMPLES


@pytest.fixture
def expected_outputs():
    """Expected outputs for valid code samples"""
    return EXPECTED_OUTPUTS


@pytest.fixture
def expected_errors():
    """Expected errors for invalid code samples"""
    return EXPECTED_ERRORS


@pytest.fixture
def sample_code_request():
    """Sample code request payload"""
    return {
        "code": "print('Hello from PyRunner!')",
        "timeout": 30,
        "memory_limit": 512
    }


@pytest.fixture
def math_code_request():
    """Math code request payload"""
    return {
        "code": "import math\nresult = math.sqrt(16) + math.pi\nprint(f'Result: {result}')",
        "timeout": 30,
        "memory_limit": 512
    }


@pytest.fixture
def numpy_code_request():
    """NumPy code request payload"""
    return {
        "code": "import numpy as np\narr = np.array([1, 2, 3, 4])\nprint(f'Array: {arr}')\nprint(f'Sum: {np.sum(arr)}')",
        "timeout": 30,
        "memory_limit": 512
    }


@pytest.fixture
def security_violation_request():
    """Security violation request payload"""
    return {
        "code": "import os\nprint(os.getcwd())",
        "timeout": 30,
        "memory_limit": 512
    }


@pytest.fixture
def timeout_request():
    """Request that should timeout"""
    return {
        "code": "import time\ntime.sleep(5)",
        "timeout": 1,
        "memory_limit": 512
    }


@pytest.fixture
def memory_limit_request():
    """Request that should exceed memory limit"""
    return {
        "code": "data = [0] * (1024 * 1024 * 100)  # 100MB of zeros",
        "timeout": 30,
        "memory_limit": 64
    }


@pytest.fixture
def error_code_request():
    """Request with code that raises an error"""
    return {
        "code": "print('Before error')\nraise ValueError('Test error')\nprint('After error')",
        "timeout": 30,
        "memory_limit": 512
    }


# Utility functions for tests
def assert_success_response(response_data: dict, expected_output: str = None):
    """Assert that response indicates successful execution"""
    assert response_data["status"] == "success"
    assert "stdout" in response_data
    assert "stderr" in response_data
    assert "execution_time" in response_data
    assert "memory_used" in response_data
    
    if expected_output:
        assert expected_output in response_data["stdout"]


def assert_error_response(response_data: dict, expected_error: str = None):
    """Assert that response indicates an error"""
    assert response_data["status"] == "error"
    assert "error" in response_data
    
    if expected_error:
        assert expected_error.lower() in response_data["error"].lower()


def assert_timeout_response(response_data: dict):
    """Assert that response indicates a timeout"""
    assert response_data["status"] == "timeout"
    assert "execution_time" in response_data


def assert_memory_exceeded_response(response_data: dict):
    """Assert that response indicates memory limit exceeded"""
    assert response_data["status"] == "memory_exceeded"
    assert "memory_used" in response_data


# Test markers for pytest
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.security = pytest.mark.security
pytest.mark.performance = pytest.mark.performance
pytest.mark.slow = pytest.mark.slow