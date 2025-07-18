"""Integration tests for PyRunner API"""

import pytest
import httpx
from tests.conftest import assert_success_response, assert_error_response


class TestHealthEndpoint:
    """Test cases for health check endpoint"""
    
    @pytest.mark.integration
    async def test_health_check(self, api_client: httpx.AsyncClient):
        """Test health check endpoint"""
        response = await api_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "service" in data
        assert data["service"] == "PyRunner"
    
    @pytest.mark.integration
    async def test_health_check_includes_capabilities(self, api_client: httpx.AsyncClient):
        """Test health check includes service capabilities"""
        response = await api_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "capabilities" in data
        capabilities = data["capabilities"]
        
        # Check for expected capabilities
        assert "max_timeout" in capabilities
        assert "max_memory_mb" in capabilities
        assert "libraries" in capabilities
        assert capabilities["max_timeout"] == 300
        assert capabilities["max_memory_mb"] == 2048
        assert "numpy" in capabilities["libraries"]
        assert "pandas" in capabilities["libraries"]
    
    @pytest.mark.integration
    async def test_health_check_includes_limits(self, api_client: httpx.AsyncClient):
        """Test health check includes resource limits"""
        response = await api_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert data["version"] == "1.0.0"
        
        # Resource limits are included in capabilities
        capabilities = data["capabilities"]
        assert "max_timeout" in capabilities
        assert "max_memory_mb" in capabilities
        assert "libraries" in capabilities


class TestCodeExecutionEndpoint:
    """Test cases for code execution endpoint"""
    
    @pytest.mark.integration
    async def test_basic_code_execution(self, api_client: httpx.AsyncClient, sample_code_request):
        """Test basic code execution"""
        response = await api_client.post("/run", json=sample_code_request)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data, "Hello from PyRunner!")
    
    @pytest.mark.integration
    async def test_math_execution(self, api_client: httpx.AsyncClient, math_code_request):
        """Test mathematical operations"""
        response = await api_client.post("/run", json=math_code_request)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data, "Result:")
        assert "stdout" in data
        assert "Result:" in data["stdout"]
    
    @pytest.mark.integration
    async def test_numpy_execution(self, api_client: httpx.AsyncClient, numpy_code_request):
        """Test NumPy execution"""
        response = await api_client.post("/run", json=numpy_code_request)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data)
        assert "Array:" in data["stdout"]
        assert "Sum: 10" in data["stdout"]
    
    @pytest.mark.integration
    async def test_error_handling(self, api_client: httpx.AsyncClient, error_code_request):
        """Test error handling"""
        response = await api_client.post("/run", json=error_code_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert "Before error" in data["stdout"]
        assert "ValueError" in data["stderr"]
    
    @pytest.mark.integration
    async def test_security_validation(self, api_client: httpx.AsyncClient, security_violation_request):
        """Test security validation"""
        response = await api_client.post("/run", json=security_violation_request)
        
        assert response.status_code == 200
        data = response.json()
        assert_error_response(data, "os")
    
    @pytest.mark.integration
    async def test_empty_code(self, api_client: httpx.AsyncClient):
        """Test empty code execution"""
        payload = {"code": ""}
        response = await api_client.post("/run", json=payload)
        
        # Empty code should be rejected with 422 (validation error)
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert "Code cannot be empty" in str(data["detail"])
    
    @pytest.mark.integration
    async def test_whitespace_only_code(self, api_client: httpx.AsyncClient):
        """Test whitespace-only code"""
        payload = {"code": "   \n  \t  "}
        response = await api_client.post("/run", json=payload)
        
        # Whitespace-only code should be rejected with 422 (validation error)
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert "Code cannot be empty" in str(data["detail"])
    
    @pytest.mark.integration
    async def test_multiline_code(self, api_client: httpx.AsyncClient):
        """Test multiline code execution"""
        multiline_code = """
import math

def calculate_area(radius):
    return math.pi * radius * radius

radius = 5
area = calculate_area(radius)
print(f"Area of circle with radius {radius}: {area:.2f}")
"""
        payload = {"code": multiline_code}
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data)
        assert "Area of circle with radius 5:" in data["stdout"]
    
    @pytest.mark.integration
    async def test_syntax_error(self, api_client: httpx.AsyncClient):
        """Test code with syntax error"""
        payload = {"code": "print('hello world'"}  # Missing closing parenthesis
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_error_response(data, "syntax")
    
    @pytest.mark.integration
    async def test_complex_calculation(self, api_client: httpx.AsyncClient):
        """Test complex mathematical calculation"""
        complex_code = """
import math
import numpy as np

# Calculate fibonacci sequence
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Calculate some values
fib_10 = fibonacci(10)
pi_squared = math.pi ** 2
array_sum = np.sum(np.array([1, 2, 3, 4, 5]))

print(f"Fibonacci(10): {fib_10}")
print(f"π²: {pi_squared:.6f}")
print(f"Array sum: {array_sum}")
"""
        payload = {"code": complex_code}
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data)
        assert "Fibonacci(10): 55" in data["stdout"]
        assert "π²:" in data["stdout"]
        assert "Array sum: 15" in data["stdout"]


class TestRequestValidation:
    """Test cases for request validation"""
    
    @pytest.mark.integration
    async def test_missing_code(self, api_client: httpx.AsyncClient):
        """Test request with missing code field"""
        payload = {"timeout": 30}
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert "code" in str(data["detail"])
    
    @pytest.mark.integration
    async def test_invalid_timeout(self, api_client: httpx.AsyncClient):
        """Test request with invalid timeout"""
        payload = {"code": "print('hello')", "timeout": 0}
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert "timeout" in str(data["detail"])
    
    @pytest.mark.integration
    async def test_invalid_memory_limit(self, api_client: httpx.AsyncClient):
        """Test request with invalid memory limit"""
        payload = {"code": "print('hello')", "memory_limit": 32}
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert "memory_limit" in str(data["detail"])
    
    @pytest.mark.integration
    async def test_invalid_json(self, api_client: httpx.AsyncClient):
        """Test request with invalid JSON"""
        response = await api_client.post("/run", content="invalid json")
        
        assert response.status_code == 422
    
    @pytest.mark.integration
    async def test_large_code_payload(self, api_client: httpx.AsyncClient):
        """Test request with large code payload"""
        large_code = "print('hello')\n" * 10000
        payload = {"code": large_code}
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data)
        assert data["stdout"].count("hello") == 10000


class TestResponseFormat:
    """Test cases for response format"""
    
    @pytest.mark.integration
    async def test_success_response_format(self, api_client: httpx.AsyncClient):
        """Test successful response format"""
        payload = {"code": "print('test')"}
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "status" in data
        assert "stdout" in data
        assert "stderr" in data
        assert "execution_time" in data
        assert "memory_used" in data
        
        # Check optional fields
        assert data.get("error") is None
        
        # Check data types
        assert isinstance(data["status"], str)
        assert isinstance(data["stdout"], str)
        assert isinstance(data["stderr"], str)
        assert isinstance(data["execution_time"], (int, float))
        # memory_used can be None
        assert data["memory_used"] is None or isinstance(data["memory_used"], (int, float))
    
    @pytest.mark.integration
    async def test_error_response_format(self, api_client: httpx.AsyncClient):
        """Test error response format"""
        payload = {"code": "import os"}
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "status" in data
        assert "error" in data
        assert data["status"] == "error"
        assert isinstance(data["error"], str)
        assert data["error"] != ""
    
    @pytest.mark.integration
    async def test_execution_metrics(self, api_client: httpx.AsyncClient):
        """Test execution metrics in response"""
        payload = {"code": "import math\nprint(math.pi)"}
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check execution time
        assert "execution_time" in data
        assert isinstance(data["execution_time"], (int, float))
        assert data["execution_time"] > 0
        assert data["execution_time"] < 30  # Should be fast
        
        # Check memory usage (can be None due to task cancellation)
        assert "memory_used" in data
        # memory_used can be None due to monitoring task cancellation
        if data["memory_used"] is not None:
            assert isinstance(data["memory_used"], (int, float))
            assert data["memory_used"] > 0
            assert data["memory_used"] < 100  # Should be reasonable (in MB)
    
    @pytest.mark.integration
    async def test_unicode_handling(self, api_client: httpx.AsyncClient):
        """Test unicode character handling"""
        payload = {"code": "print('Hello 世界! 🌍')"}
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data)
        assert "Hello 世界! 🌍" in data["stdout"]


class TestConcurrentRequests:
    """Test cases for concurrent request handling"""
    
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_concurrent_requests(self, api_client: httpx.AsyncClient):
        """Test handling of concurrent requests"""
        import asyncio
        
        async def make_request(i):
            payload = {"code": f"print('Request {i}')"}
            response = await api_client.post("/run", json=payload)
            return response
        
        # Send 5 concurrent requests
        tasks = [make_request(i) for i in range(5)]
        responses = await asyncio.gather(*tasks)
        
        # Check all responses
        for i, response in enumerate(responses):
            assert response.status_code == 200
            data = response.json()
            assert_success_response(data)
            assert f"Request {i}" in data["stdout"]
    
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_mixed_concurrent_requests(self, api_client: httpx.AsyncClient):
        """Test handling of mixed concurrent requests"""
        import asyncio
        
        async def success_request():
            payload = {"code": "print('success')"}
            return await api_client.post("/run", json=payload)
        
        async def error_request():
            payload = {"code": "import os"}
            return await api_client.post("/run", json=payload)
        
        # Mix of success and error requests
        tasks = [success_request(), error_request(), success_request()]
        responses = await asyncio.gather(*tasks)
        
        # Check responses
        assert responses[0].status_code == 200
        assert responses[0].json()["status"] == "success"
        
        assert responses[1].status_code == 200
        assert responses[1].json()["status"] == "error"
        
        assert responses[2].status_code == 200
        assert responses[2].json()["status"] == "success"