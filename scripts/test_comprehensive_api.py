#!/usr/bin/env python3
"""
Comprehensive API test for PyRunner service
This is a working version that respects the security constraints
"""
import requests
import json
import time

# API endpoint
API_URL = "http://localhost:8000/run"

# Test cases
test_cases = [
    {
        "name": "Basic Math",
        "code": """
import math
print(f"Pi: {math.pi}")
print(f"Square root of 16: {math.sqrt(16)}")
print(f"2^10: {2**10}")
"""
    },
    {
        "name": "SymPy Example",
        "code": """
from sympy import symbols, expand, factor
x, y = symbols('x y')
expr = (x + y)**3
print(f"Expression: {expr}")
print(f"Expanded: {expand(expr)}")
print(f"Factored: {factor(x**3 - y**3)}")
"""
    },
    {
        "name": "NumPy Array Operations",
        "code": """
import numpy as np
arr = np.array([1, 2, 3, 4, 5])
print(f"Array: {arr}")
print(f"Mean: {arr.mean()}")
print(f"Standard deviation: {arr.std()}")
print(f"Cumulative sum: {arr.cumsum()}")
"""
    },
    {
        "name": "Pandas DataFrame",
        "code": """
import pandas as pd
import numpy as np

# Create sample data
data = {
    'A': [1, 2, 3, 4, 5],
    'B': [10, 20, 30, 40, 50],
    'C': ['a', 'b', 'c', 'd', 'e']
}

df = pd.DataFrame(data)
print("DataFrame:")
print(df)
print(f"\\nDataFrame shape: {df.shape}")
print(f"Column A mean: {df['A'].mean()}")
"""
    },
    {
        "name": "SciPy Statistics",
        "code": """
import scipy.stats as stats
import numpy as np

# Generate sample data
data = np.random.normal(0, 1, 100)
print(f"Sample size: {len(data)}")
print(f"Mean: {np.mean(data):.4f}")
print(f"Standard deviation: {np.std(data):.4f}")

# Perform t-test
t_stat, p_value = stats.ttest_1samp(data, 0)
print(f"T-statistic: {t_stat:.4f}")
print(f"P-value: {p_value:.4f}")
"""
    },
    {
        "name": "Error Handling",
        "code": """
# This will cause an error
print("Before error")
print(1 / 0)
print("After error")
"""
    },
    {
        "name": "Timeout Test (CPU-intensive)",
        "code": """
import math
print("Starting CPU-intensive computation...")
result = 0
for i in range(100000000):
    result += math.sqrt(i)
print(f"This won't be printed: {result}")
""",
        "timeout": 2
    },
    {
        "name": "Memory Test",
        "code": """
# Try to allocate large array
import numpy as np
print("Allocating memory...")
arr = np.zeros((1000, 1000))  # ~8MB
print(f"Array shape: {arr.shape}")
print(f"Array size: {arr.nbytes} bytes")
""",
        "memory_limit": 256
    },
    {
        "name": "Collections and Itertools",
        "code": """
from collections import Counter, defaultdict
import itertools

# Counter example
text = "hello world"
counter = Counter(text)
print(f"Character counts: {counter}")

# defaultdict example
dd = defaultdict(list)
for char in text:
    dd[char].append(char)
print(f"Default dict: {dict(dd)}")

# itertools example
combinations = list(itertools.combinations([1, 2, 3], 2))
print(f"Combinations: {combinations}")
"""
    },
    {
        "name": "Security Test (should fail)",
        "code": """
# This should be blocked by security validation
import os
print(os.getcwd())
"""
    }
]

def test_api():
    """Test the PyRunner API with various code examples"""
    
    successful_tests = 0
    total_tests = len(test_cases)
    
    for test in test_cases:
        print(f"\n{'='*60}")
        print(f"Test: {test['name']}")
        print(f"{'='*60}")
        
        payload = {
            "code": test["code"],
            "timeout": test.get("timeout", 30),
            "memory_limit": test.get("memory_limit", 512)
        }
        
        start_time = time.time()
        
        try:
            response = requests.post(API_URL, json=payload)
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"Status: {result['status']}")
                print(f"Execution time: {result['execution_time']}s")
                print(f"API call time: {elapsed_time:.3f}s")
                
                if result.get('memory_used'):
                    print(f"Memory used: {result['memory_used']}MB")
                
                if result['stdout']:
                    print(f"\nOutput:\n{result['stdout']}")
                
                if result['stderr']:
                    print(f"\nErrors:\n{result['stderr']}")
                
                # Determine if test passed based on expectations
                if test['name'] == "Security Test (should fail)":
                    if result['status'] == 'error' and 'security' in result.get('stderr', '').lower():
                        print("✓ Security test correctly blocked")
                        successful_tests += 1
                    else:
                        print("✗ Security test should have been blocked")
                elif test['name'] == "Timeout Test (CPU-intensive)":
                    if result['status'] == 'timeout':
                        print("✓ Timeout test correctly timed out")
                        successful_tests += 1
                    else:
                        print("✗ Timeout test should have timed out")
                elif test['name'] == "Error Handling":
                    if result['status'] == 'error' and 'ZeroDivisionError' in result.get('stderr', ''):
                        print("✓ Error handling test correctly caught error")
                        successful_tests += 1
                    else:
                        print("✗ Error handling test should have caught error")
                else:
                    if result['status'] == 'success':
                        print("✓ Test passed successfully")
                        successful_tests += 1
                    else:
                        print("✗ Test failed unexpectedly")
                        
            else:
                print(f"Error: HTTP {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"Request failed: {str(e)}")
    
    print(f"\n{'='*60}")
    print(f"COMPREHENSIVE API TEST RESULTS")
    print(f"{'='*60}")
    print(f"Passed: {successful_tests}/{total_tests} tests")
    
    if successful_tests == total_tests:
        print("✓ ALL TESTS PASSED! PyRunner is working correctly.")
        return True
    else:
        print("✗ Some tests failed. Check the output above.")
        return False

def test_health_endpoint():
    """Test the health endpoint"""
    print("Testing health endpoint...")
    try:
        response = requests.get("http://localhost:8000/")
        if response.status_code == 200:
            health_data = response.json()
            print(f"✓ Health check passed: {health_data}")
            return True
        else:
            print(f"✗ Health check failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False

if __name__ == "__main__":
    print("PyRunner Comprehensive API Test Suite")
    print("=" * 60)
    print("Testing PyRunner API...")
    print("Make sure the service is running on http://localhost:8000")
    print()
    
    # Test health endpoint first
    if not test_health_endpoint():
        print("Service is not running. Please start the service first.")
        exit(1)
    
    print("\nStarting comprehensive tests...")
    success = test_api()
    
    if success:
        print("\n🎉 All tests passed! PyRunner is fully functional.")
    else:
        print("\n❌ Some tests failed. Check the service implementation.")
    
    exit(0 if success else 1)