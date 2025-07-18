#!/usr/bin/env python3
"""
Test resource limits and timeouts for PyRunner
"""
import requests
import time

def test_timeout_handling():
    """Test timeout handling"""
    print("Testing timeout handling...")
    
    # Test with a short timeout using CPU-intensive busy loop
    payload = {
        "code": """
import math
print('Starting CPU-intensive loop...')
result = 0
for i in range(100000000):  # Much larger range
    result += math.sqrt(i)
print('Should not reach here')
""",
        "timeout": 2
    }
    
    start_time = time.time()
    
    try:
        response = requests.post("http://localhost:8000/run", json=payload)
        elapsed = time.time() - start_time
        
        print(f"Request took {elapsed:.2f} seconds")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            if (data.get("status") == "timeout" and 
                elapsed >= 2.0 and elapsed < 3.0 and
                "timed out" in data.get("stderr", "")):
                print("✓ Timeout handling test PASSED")
                return True
        
        print("✗ Timeout handling test FAILED")
        return False
    except Exception as e:
        print(f"✗ Timeout handling test FAILED: {e}")
        return False

def test_memory_monitoring():
    """Test memory monitoring (psutil-based)"""
    print("\nTesting memory monitoring...")
    
    # Test with memory-intensive operation
    payload = {
        "code": """
import numpy as np
print('Creating large array...')
# Create a reasonably large array (not too large to avoid system issues)
arr = np.zeros((1000, 1000))
print(f'Array shape: {arr.shape}')
print(f'Array size: {arr.nbytes} bytes')
""",
        "memory_limit": 128
    }
    
    try:
        response = requests.post("http://localhost:8000/run", json=payload)
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            if (data.get("status") == "success" and 
                "Array shape" in data.get("stdout", "")):
                print("✓ Memory monitoring test PASSED")
                return True
        
        print("✗ Memory monitoring test FAILED")
        return False
    except Exception as e:
        print(f"✗ Memory monitoring test FAILED: {e}")
        return False

def test_infinite_loop_timeout():
    """Test timeout with infinite loop"""
    print("\nTesting infinite loop timeout...")
    
    payload = {
        "code": """
print('Starting infinite loop...')
i = 0
while True:
    i += 1
    if i % 1000000 == 0:
        pass  # Just to keep the loop busy
""",
        "timeout": 3
    }
    
    start_time = time.time()
    
    try:
        response = requests.post("http://localhost:8000/run", json=payload)
        elapsed = time.time() - start_time
        
        print(f"Request took {elapsed:.2f} seconds")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            if (data.get("status") == "timeout" and 
                elapsed >= 3.0 and elapsed < 4.0):
                print("✓ Infinite loop timeout test PASSED")
                return True
        
        print("✗ Infinite loop timeout test FAILED")
        return False
    except Exception as e:
        print(f"✗ Infinite loop timeout test FAILED: {e}")
        return False

def test_cpu_intensive_operation():
    """Test CPU-intensive operation"""
    print("\nTesting CPU-intensive operation...")
    
    payload = {
        "code": """
import math
print('Starting CPU-intensive calculation...')
result = 0
for i in range(1000000):
    result += math.sqrt(i)
print(f'Calculation complete: {result:.2f}')
""",
        "timeout": 10
    }
    
    try:
        response = requests.post("http://localhost:8000/run", json=payload)
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            if (data.get("status") == "success" and 
                "Calculation complete" in data.get("stdout", "")):
                print("✓ CPU-intensive operation test PASSED")
                return True
        
        print("✗ CPU-intensive operation test FAILED")
        return False
    except Exception as e:
        print(f"✗ CPU-intensive operation test FAILED: {e}")
        return False

def test_concurrent_requests():
    """Test concurrent request handling"""
    print("\nTesting concurrent requests...")
    
    import threading
    import queue
    
    results = queue.Queue()
    
    def make_request(request_id):
        payload = {
            "code": f"""
import math
print('Request {request_id} starting')
# Do some mathematical work
result = sum(math.sqrt(i) for i in range(10000))
print(f'Request {request_id} complete: {{result:.2f}}')
""",
            "timeout": 5
        }
        
        try:
            response = requests.post("http://localhost:8000/run", json=payload)
            results.put(("success", request_id, response.status_code, response.json()))
        except Exception as e:
            results.put(("error", request_id, str(e)))
    
    # Start 3 concurrent requests
    threads = []
    for i in range(3):
        thread = threading.Thread(target=make_request, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Check results
    successful = 0
    total = 3
    
    while not results.empty():
        result = results.get()
        if result[0] == "success":
            status, req_id, status_code, response_data = result
            if status_code == 200 and response_data.get("status") == "success":
                successful += 1
                print(f"  ✓ Request {req_id} succeeded")
            else:
                print(f"  ✗ Request {req_id} failed: {response_data}")
        else:
            _, req_id, error = result
            print(f"  ✗ Request {req_id} error: {error}")
    
    if successful == total:
        print("✓ Concurrent requests test PASSED")
        return True
    else:
        print(f"✗ Concurrent requests test FAILED ({successful}/{total} succeeded)")
        return False

def test_parameter_validation():
    """Test parameter validation"""
    print("\nTesting parameter validation...")
    
    test_cases = [
        {
            "name": "invalid_timeout_low",
            "payload": {"code": "print('test')", "timeout": 0},
            "should_fail": True
        },
        {
            "name": "invalid_timeout_high",
            "payload": {"code": "print('test')", "timeout": 400},
            "should_fail": True
        },
        {
            "name": "invalid_memory_low",
            "payload": {"code": "print('test')", "memory_limit": 32},
            "should_fail": True
        },
        {
            "name": "invalid_memory_high",
            "payload": {"code": "print('test')", "memory_limit": 3000},
            "should_fail": True
        },
        {
            "name": "valid_parameters",
            "payload": {"code": "print('test')", "timeout": 10, "memory_limit": 256},
            "should_fail": False
        }
    ]
    
    passed = 0
    total = len(test_cases)
    
    for test in test_cases:
        print(f"  Testing {test['name']}...")
        
        try:
            response = requests.post("http://localhost:8000/run", json=test["payload"])
            
            if test["should_fail"]:
                if response.status_code == 422:  # Validation error
                    print(f"    ✓ {test['name']} correctly rejected")
                    passed += 1
                else:
                    print(f"    ✗ {test['name']} should have been rejected (status: {response.status_code})")
            else:
                if response.status_code == 200:
                    print(f"    ✓ {test['name']} correctly accepted")
                    passed += 1
                else:
                    print(f"    ✗ {test['name']} should have been accepted (status: {response.status_code})")
                    
        except Exception as e:
            print(f"    ✗ {test['name']} test failed: {e}")
    
    if passed == total:
        print("✓ Parameter validation test PASSED")
        return True
    else:
        print(f"✗ Parameter validation test FAILED ({passed}/{total} passed)")
        return False

def run_resource_tests():
    """Run all resource limit tests"""
    print("PyRunner Resource Limits Test Suite")
    print("=" * 50)
    
    tests = [
        ("Timeout Handling", test_timeout_handling),
        ("Memory Monitoring", test_memory_monitoring),
        ("Infinite Loop Timeout", test_infinite_loop_timeout),
        ("CPU-Intensive Operation", test_cpu_intensive_operation),
        ("Concurrent Requests", test_concurrent_requests),
        ("Parameter Validation", test_parameter_validation)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}")
        print("-" * len(test_name))
        
        try:
            if test_func():
                passed_tests += 1
                print(f"✓ {test_name} PASSED")
            else:
                print(f"✗ {test_name} FAILED")
        except Exception as e:
            print(f"✗ {test_name} FAILED with exception: {e}")
    
    print(f"\n{'='*50}")
    print(f"Resource Test Results: {passed_tests}/{total_tests} test suites passed")
    
    if passed_tests == total_tests:
        print("✓ ALL RESOURCE TESTS PASSED!")
        return True
    else:
        print("✗ SOME RESOURCE TESTS FAILED!")
        return False

if __name__ == "__main__":
    success = run_resource_tests()
    exit(0 if success else 1)