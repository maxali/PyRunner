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
        "name": "Error Handling",
        "code": """
# This will cause an error
print(1 / 0)
"""
    },
    {
        "name": "Timeout Test",
        "code": """
import time
print("Starting long computation...")
time.sleep(35)  # This will timeout
print("This won't be printed")
""",
        "timeout": 2
    },
    {
        "name": "Memory Test",
        "code": """
# Try to allocate large array
import numpy as np
print("Allocating memory...")
arr = np.zeros((1000, 1000, 100))  # ~800MB
print(f"Array shape: {arr.shape}")
""",
        "memory_limit": 256
    }
]

def test_api():
    """Test the PyRunner API with various code examples"""
    
    for test in test_cases:
        print(f"\n{'='*50}")
        print(f"Test: {test['name']}")
        print(f"{'='*50}")
        
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
            else:
                print(f"Error: HTTP {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"Request failed: {str(e)}")

if __name__ == "__main__":
    print("Testing PyRunner API...")
    print("Make sure the service is running on http://localhost:8000")
    input("Press Enter to start tests...")
    test_api()