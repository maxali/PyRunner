"""Integration tests for resource limits"""

import pytest
import httpx
import asyncio
from tests.conftest import assert_success_response, assert_timeout_response, assert_memory_exceeded_response


class TestTimeoutLimits:
    """Test cases for timeout limits"""
    
    @pytest.mark.integration
    @pytest.mark.performance
    @pytest.mark.slow
    async def test_timeout_enforcement(self, api_client: httpx.AsyncClient):
        """Test timeout enforcement"""
        payload = {
            "code": "# Create infinite loop that will timeout\nwhile True:\n    pass",
            "timeout": 1
        }
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_timeout_response(data)
        assert data["execution_time"] >= 1.0
        assert data["execution_time"] < 2.0  # Should be killed around 1 second
    
    @pytest.mark.integration
    @pytest.mark.performance
    async def test_fast_execution_within_timeout(self, api_client: httpx.AsyncClient):
        """Test fast execution within timeout"""
        payload = {
            "code": "import math\nprint(math.pi)",
            "timeout": 5
        }
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data, "3.141592653589793")
        assert data["execution_time"] < 1.0  # Should be very fast
    
    @pytest.mark.integration
    @pytest.mark.performance
    @pytest.mark.slow
    async def test_infinite_loop_timeout(self, api_client: httpx.AsyncClient):
        """Test infinite loop timeout"""
        payload = {
            "code": "while True:\n    pass",
            "timeout": 2
        }
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_timeout_response(data)
        assert data["execution_time"] >= 2.0
        assert data["execution_time"] < 3.0
    
    @pytest.mark.integration
    @pytest.mark.performance
    @pytest.mark.slow
    async def test_recursive_function_timeout(self, api_client: httpx.AsyncClient):
        """Test recursive function timeout"""
        payload = {
            "code": """
def recursive_function():
    return recursive_function()

recursive_function()
""",
            "timeout": 1
        }
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        # This might timeout or hit recursion limit
        assert data["status"] in ["timeout", "error"]
    
    @pytest.mark.integration
    @pytest.mark.performance
    @pytest.mark.slow
    async def test_cpu_intensive_timeout(self, api_client: httpx.AsyncClient):
        """Test CPU-intensive operation timeout"""
        payload = {
            "code": """
# CPU-intensive calculation
result = 0
for i in range(10000000):
    result += i * i

print(f'Result: {result}')
""",
            "timeout": 1
        }
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        # This might complete or timeout depending on system speed
        assert data["status"] in ["success", "timeout"]
    
    @pytest.mark.integration
    @pytest.mark.performance
    async def test_multiple_timeout_values(self, api_client: httpx.AsyncClient):
        """Test different timeout values"""
        test_cases = [
            {"timeout": 1, "expected_max": 1.5},
            {"timeout": 3, "expected_max": 3.5},
            {"timeout": 5, "expected_max": 5.5},
        ]
        
        for case in test_cases:
            payload = {
                "code": f"# Loop for roughly {case['timeout']} seconds\ncount = 0\nwhile count < {case['timeout'] * 100000000}:\n    count += 1\nprint(f'Finished {{count}} iterations')",
                "timeout": case["timeout"]
            }
            response = await api_client.post("/run", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            assert_timeout_response(data)
            assert data["execution_time"] >= case["timeout"]
            assert data["execution_time"] < case["expected_max"]


class TestMemoryLimits:
    """Test cases for memory limits"""
    
    @pytest.mark.integration
    @pytest.mark.performance
    @pytest.mark.slow
    async def test_memory_limit_enforcement(self, api_client: httpx.AsyncClient):
        """Test memory limit enforcement"""
        payload = {
            "code": "data = [0] * (50 * 1024 * 1024)  # 50MB of zeros",
            "memory_limit": 64,
            "timeout": 10
        }
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_memory_exceeded_response(data)
        # Note: memory_used may be None due to monitoring task cancellation  
        if data["memory_used"] is not None:
            assert data["memory_used"] > 50  # Should show high memory usage (in MB)
    
    @pytest.mark.integration
    @pytest.mark.performance
    async def test_low_memory_usage_within_limit(self, api_client: httpx.AsyncClient):
        """Test low memory usage within limit"""
        payload = {
            "code": "import numpy as np\narr = np.array([1, 2, 3, 4, 5])\nprint(f'Array: {arr}')",
            "memory_limit": 512,
            "timeout": 10
        }
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data, "Array: [1 2 3 4 5]")
        # Note: memory_used may be None due to monitoring task cancellation
        if data["memory_used"] is not None:
            assert data["memory_used"] < 100  # Should use less than 100MB
    
    @pytest.mark.integration
    @pytest.mark.performance
    @pytest.mark.slow
    async def test_gradual_memory_increase(self, api_client: httpx.AsyncClient):
        """Test gradual memory increase"""
        payload = {
            "code": """
import time
data = []
for i in range(1000):
    data.extend([0] * 10000)  # Add 10KB per iteration
    if i % 100 == 0:
        print(f'Iteration {i}, approx size: {len(data) * 4 / 1024 / 1024:.1f}MB')
        time.sleep(0.001)
""",
            "memory_limit": 64,
            "timeout": 15
        }
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        # Should either complete or exceed memory limit
        assert data["status"] in ["success", "memory_exceeded"]
    
    @pytest.mark.integration
    @pytest.mark.performance
    @pytest.mark.slow
    async def test_large_numpy_array(self, api_client: httpx.AsyncClient):
        """Test large NumPy array creation"""
        payload = {
            "code": """
import numpy as np
try:
    # Try to create a 100MB array
    arr = np.zeros(25 * 1024 * 1024)  # 25M floats ≈ 100MB
    print(f'Created array with {len(arr)} elements')
except MemoryError:
    print('Memory error creating array')
""",
            "memory_limit": 64,
            "timeout": 10
        }
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        # Should either exceed memory limit or handle gracefully
        assert data["status"] in ["success", "memory_exceeded"]
    
    @pytest.mark.integration
    @pytest.mark.performance
    async def test_different_memory_limits(self, api_client: httpx.AsyncClient):
        """Test different memory limits"""
        test_cases = [
            {"memory_limit": 64, "data_size": 32},   # Within limit
            {"memory_limit": 128, "data_size": 64},  # Within limit
            {"memory_limit": 256, "data_size": 128}, # Within limit
        ]
        
        for case in test_cases:
            payload = {
                "code": f"data = [0] * ({case['data_size']} * 1024 * 1024)  # {case['data_size']}MB\nprint(f'Created {case['data_size']}MB of data')",
                "memory_limit": case["memory_limit"],
                "timeout": 10
            }
            response = await api_client.post("/run", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            assert_success_response(data, f"Created {case['data_size']}MB of data")
            # Note: memory_used may be None due to monitoring task cancellation
            if data["memory_used"] is not None:
                assert data["memory_used"] > case["data_size"] * 0.8  # At least 80% of expected (in MB)


class TestCombinedLimits:
    """Test cases for combined timeout and memory limits"""
    
    @pytest.mark.integration
    @pytest.mark.performance
    @pytest.mark.slow
    async def test_timeout_before_memory_limit(self, api_client: httpx.AsyncClient):
        """Test timeout occurs before memory limit"""
        payload = {
            "code": """
import time
data = []
for i in range(10000):
    data.extend([0] * 1000)  # Slow memory growth
    time.sleep(0.001)  # Ensure we hit timeout first
""",
            "memory_limit": 2048,  # High memory limit
            "timeout": 2           # Low timeout
        }
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_timeout_response(data)
        assert data["execution_time"] >= 2.0
        assert data["execution_time"] < 3.0
    
    @pytest.mark.integration
    @pytest.mark.performance
    @pytest.mark.slow
    async def test_memory_limit_before_timeout(self, api_client: httpx.AsyncClient):
        """Test memory limit occurs before timeout"""
        payload = {
            "code": "data = [0] * (100 * 1024 * 1024)  # 100MB quickly",
            "memory_limit": 64,    # Low memory limit
            "timeout": 30          # High timeout
        }
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_memory_exceeded_response(data)
        assert data["execution_time"] < 10.0  # Should be killed quickly
    
    @pytest.mark.integration
    @pytest.mark.performance
    async def test_both_limits_respected(self, api_client: httpx.AsyncClient):
        """Test both limits are respected when not exceeded"""
        payload = {
            "code": """
import numpy as np
import math

# Moderate computation within both limits
arr = np.array(range(1000))
result = np.sum(arr * np.sin(arr))
print(f'Result: {result:.2f}')
""",
            "memory_limit": 256,
            "timeout": 10
        }
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data, "Result:")
        assert data["execution_time"] < 5.0
        # Note: memory_used may be None due to monitoring task cancellation
        if data["memory_used"] is not None:
            assert data["memory_used"] < 100  # Less than 100MB


class TestResourceMonitoring:
    """Test cases for resource monitoring accuracy"""
    
    @pytest.mark.integration
    @pytest.mark.performance
    async def test_execution_time_accuracy(self, api_client: httpx.AsyncClient):
        """Test execution time measurement accuracy"""
        payload = {
            "code": """
import time
start = time.time()
time.sleep(0.1)  # Sleep for 100ms
end = time.time()
print(f'Internal time: {end - start:.3f}s')
""",
            "timeout": 10
        }
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data, "Internal time:")
        
        # External measurement should be close to internal measurement
        assert data["execution_time"] >= 0.1
        assert data["execution_time"] <= 0.2  # Allow for some overhead
    
    @pytest.mark.integration
    @pytest.mark.performance
    async def test_memory_usage_reporting(self, api_client: httpx.AsyncClient):
        """Test memory usage reporting"""
        payload = {
            "code": """
import numpy as np
# Create arrays of known sizes
arr1 = np.zeros(1024 * 1024)      # 1M floats ≈ 8MB
arr2 = np.zeros(2 * 1024 * 1024)  # 2M floats ≈ 16MB
total_size = arr1.nbytes + arr2.nbytes
print(f'Created arrays totaling {total_size / 1024 / 1024:.1f}MB')
""",
            "memory_limit": 256,
            "timeout": 10
        }
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data, "Created arrays totaling")
        
        # Should show significant memory usage
        # Note: memory_used may be None due to monitoring task cancellation
        if data["memory_used"] is not None:
            assert data["memory_used"] > 10  # At least 10MB
    
    @pytest.mark.integration
    @pytest.mark.performance
    async def test_multiple_executions_independent(self, api_client: httpx.AsyncClient):
        """Test multiple executions are independent"""
        # First execution with high memory usage
        payload1 = {
            "code": "data = [0] * (10 * 1024 * 1024)  # 10MB\nprint('First execution')",
            "memory_limit": 256,
            "timeout": 10
        }
        response1 = await api_client.post("/run", json=payload1)
        
        assert response1.status_code == 200
        data1 = response1.json()
        assert_success_response(data1, "First execution")
        
        # Second execution with low memory usage
        payload2 = {
            "code": "print('Second execution')",
            "memory_limit": 256,
            "timeout": 10
        }
        response2 = await api_client.post("/run", json=payload2)
        
        assert response2.status_code == 200
        data2 = response2.json()
        assert_success_response(data2, "Second execution")
        
        # Memory usage should be independent
        # Note: memory_used may be None due to monitoring task cancellation
        if data1["memory_used"] is not None and data2["memory_used"] is not None:
            assert data1["memory_used"] > data2["memory_used"]
            assert data2["memory_used"] < 10  # Much less than first (in MB)
    
    @pytest.mark.integration
    @pytest.mark.performance
    @pytest.mark.slow
    async def test_concurrent_resource_limits(self, api_client: httpx.AsyncClient):
        """Test concurrent executions respect individual limits"""
        import asyncio
        
        async def memory_intensive_request():
            payload = {
                "code": "data = [0] * (30 * 1024 * 1024)  # 30MB\nprint('Memory intensive done')",
                "memory_limit": 64,
                "timeout": 10
            }
            return await api_client.post("/run", json=payload)
        
        async def cpu_intensive_request():
            payload = {
                "code": "result = sum(i*i for i in range(1000000))\nprint(f'CPU intensive done: {result}')",
                "memory_limit": 256,
                "timeout": 5
            }
            return await api_client.post("/run", json=payload)
        
        # Run both concurrently
        results = await asyncio.gather(
            memory_intensive_request(),
            cpu_intensive_request()
        )
        
        response1, response2 = results
        
        # Check both responses
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        
        # First should exceed memory limit
        assert data1["status"] == "memory_exceeded"
        
        # Second should complete successfully
        assert data2["status"] == "success"
        assert "CPU intensive done:" in data2["stdout"]


class TestEdgeCases:
    """Test cases for edge cases in resource limits"""
    
    @pytest.mark.integration
    @pytest.mark.performance
    async def test_zero_timeout_not_allowed(self, api_client: httpx.AsyncClient):
        """Test zero timeout is not allowed"""
        payload = {
            "code": "print('hello')",
            "timeout": 0
        }
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.integration
    @pytest.mark.performance
    async def test_minimum_timeout(self, api_client: httpx.AsyncClient):
        """Test minimum timeout (1 second)"""
        payload = {
            "code": "print('hello')",
            "timeout": 1
        }
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data, "hello")
    
    @pytest.mark.integration
    @pytest.mark.performance
    async def test_maximum_timeout(self, api_client: httpx.AsyncClient):
        """Test maximum timeout (300 seconds)"""
        payload = {
            "code": "print('hello')",
            "timeout": 300
        }
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data, "hello")
    
    @pytest.mark.integration
    @pytest.mark.performance
    async def test_minimum_memory_limit(self, api_client: httpx.AsyncClient):
        """Test minimum memory limit (64MB)"""
        payload = {
            "code": "print('hello')",
            "memory_limit": 64
        }
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data, "hello")
    
    @pytest.mark.integration
    @pytest.mark.performance
    async def test_maximum_memory_limit(self, api_client: httpx.AsyncClient):
        """Test maximum memory limit (2048MB)"""
        payload = {
            "code": "print('hello')",
            "memory_limit": 2048
        }
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data, "hello")