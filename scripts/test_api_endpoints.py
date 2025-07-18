#!/usr/bin/env python3
"""
Test PyRunner API endpoints
"""
import requests
import json

def test_health_endpoint():
    """Test health check endpoint"""
    print("Testing health endpoint...")
    
    try:
        response = requests.get("http://localhost:8000/")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✓ Health endpoint test PASSED")
            return True
        else:
            print("✗ Health endpoint test FAILED")
            return False
    except Exception as e:
        print(f"✗ Health endpoint test FAILED: {e}")
        return False

def test_basic_code_execution():
    """Test basic code execution"""
    print("\nTesting basic code execution...")
    
    payload = {
        "code": "print('Hello from PyRunner!')"
    }
    
    try:
        response = requests.post("http://localhost:8000/run", json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success" and "Hello from PyRunner!" in data.get("stdout", ""):
                print("✓ Basic code execution test PASSED")
                return True
        
        print("✗ Basic code execution test FAILED")
        return False
    except Exception as e:
        print(f"✗ Basic code execution test FAILED: {e}")
        return False

def test_math_execution():
    """Test mathematical operations"""
    print("\nTesting mathematical operations...")
    
    payload = {
        "code": "import math\nresult = math.sqrt(16) + math.pi\nprint(f'Result: {result}')"
    }
    
    try:
        response = requests.post("http://localhost:8000/run", json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success" and "Result:" in data.get("stdout", ""):
                print("✓ Math execution test PASSED")
                return True
        
        print("✗ Math execution test FAILED")
        return False
    except Exception as e:
        print(f"✗ Math execution test FAILED: {e}")
        return False

def test_error_handling():
    """Test error handling"""
    print("\nTesting error handling...")
    
    payload = {
        "code": "print('Before error')\nraise ValueError('Test error')\nprint('After error')"
    }
    
    try:
        response = requests.post("http://localhost:8000/run", json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            if (data.get("status") == "error" and 
                "Before error" in data.get("stdout", "") and
                "ValueError" in data.get("stderr", "")):
                print("✓ Error handling test PASSED")
                return True
        
        print("✗ Error handling test FAILED")
        return False
    except Exception as e:
        print(f"✗ Error handling test FAILED: {e}")
        return False

def test_security_validation():
    """Test security validation"""
    print("\nTesting security validation...")
    
    payload = {
        "code": "import os\nprint(os.getcwd())"
    }
    
    try:
        response = requests.post("http://localhost:8000/run", json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            if (data.get("status") == "error" and 
                "security" in data.get("stderr", "").lower() and
                "os" in data.get("error", "")):
                print("✓ Security validation test PASSED")
                return True
        
        print("✗ Security validation test FAILED")
        return False
    except Exception as e:
        print(f"✗ Security validation test FAILED: {e}")
        return False

def test_numpy_execution():
    """Test NumPy execution"""
    print("\nTesting NumPy execution...")
    
    payload = {
        "code": "import numpy as np\narr = np.array([1, 2, 3, 4])\nprint(f'Array: {arr}')\nprint(f'Sum: {np.sum(arr)}')"
    }
    
    try:
        response = requests.post("http://localhost:8000/run", json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            if (data.get("status") == "success" and 
                "Array:" in data.get("stdout", "") and
                "Sum: 10" in data.get("stdout", "")):
                print("✓ NumPy execution test PASSED")
                return True
        
        print("✗ NumPy execution test FAILED")
        return False
    except Exception as e:
        print(f"✗ NumPy execution test FAILED: {e}")
        return False

def run_all_tests():
    """Run all API tests"""
    print("PyRunner API Test Suite")
    print("=" * 50)
    
    tests = [
        test_health_endpoint,
        test_basic_code_execution,
        test_math_execution,
        test_error_handling,
        test_security_validation,
        test_numpy_execution
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All API tests PASSED!")
        return True
    else:
        print("✗ Some API tests FAILED.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)