#!/usr/bin/env python3
"""
Comprehensive security validation test suite for PyRunner
"""
import requests
import json

def test_allowed_modules():
    """Test all allowed modules from the whitelist"""
    print("Testing allowed modules...")
    
    allowed_tests = [
        {
            "name": "math",
            "code": "import math\nprint(f'π = {math.pi}')",
            "expected_output": "π = 3.141592653589793"
        },
        {
            "name": "numpy",
            "code": "import numpy as np\narr = np.array([1, 2, 3])\nprint(f'Array: {arr}')",
            "expected_output": "Array: [1 2 3]"
        },
        {
            "name": "sympy",
            "code": "import sympy as sp\nx = sp.Symbol('x')\nprint(f'Symbol: {x}')",
            "expected_output": "Symbol: x"
        },
        {
            "name": "pandas",
            "code": "import pandas as pd\ndf = pd.DataFrame({'A': [1, 2]})\nprint(f'DataFrame:\\n{df}')",
            "expected_output": "DataFrame:"
        },
        {
            "name": "matplotlib",
            "code": "import matplotlib\nprint(f'Matplotlib version: {matplotlib.__version__}')",
            "expected_output": "Matplotlib version:"
        },
        {
            "name": "scipy",
            "code": "import scipy\nprint(f'SciPy version: {scipy.__version__}')",
            "expected_output": "SciPy version:"
        },
        {
            "name": "sklearn",
            "code": "import sklearn\nprint(f'Scikit-learn version: {sklearn.__version__}')",
            "expected_output": "Scikit-learn version:"
        },
        {
            "name": "collections",
            "code": "from collections import Counter\nc = Counter([1, 2, 2, 3])\nprint(f'Counter: {c}')",
            "expected_output": "Counter: Counter({2: 2, 1: 1, 3: 1})"
        },
        {
            "name": "itertools",
            "code": "import itertools\nresult = list(itertools.combinations([1, 2, 3], 2))\nprint(f'Combinations: {result}')",
            "expected_output": "Combinations: [(1, 2), (1, 3), (2, 3)]"
        },
        {
            "name": "functools",
            "code": "from functools import reduce\nresult = reduce(lambda x, y: x + y, [1, 2, 3, 4])\nprint(f'Sum: {result}')",
            "expected_output": "Sum: 10"
        }
    ]
    
    passed = 0
    total = len(allowed_tests)
    
    for test in allowed_tests:
        print(f"\n  Testing {test['name']}...")
        
        try:
            payload = {"code": test["code"]}
            response = requests.post("http://localhost:8000/run", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if (data.get("status") == "success" and 
                    test["expected_output"] in data.get("stdout", "")):
                    print(f"    ✓ {test['name']} PASSED")
                    passed += 1
                else:
                    print(f"    ✗ {test['name']} FAILED - unexpected output")
                    print(f"      Expected: {test['expected_output']}")
                    print(f"      Got: {data.get('stdout', '')}")
            else:
                print(f"    ✗ {test['name']} FAILED - status {response.status_code}")
                
        except Exception as e:
            print(f"    ✗ {test['name']} FAILED - {e}")
    
    print(f"\nAllowed modules test: {passed}/{total} passed")
    return passed == total

def test_blocked_modules():
    """Test blocked modules"""
    print("\nTesting blocked modules...")
    
    blocked_tests = [
        {
            "name": "os",
            "code": "import os\nprint(os.getcwd())",
            "expected_error": "os"
        },
        {
            "name": "subprocess",
            "code": "import subprocess\nresult = subprocess.run(['echo', 'test'])\nprint(result)",
            "expected_error": "subprocess"
        },
        {
            "name": "sys",
            "code": "import sys\nprint(sys.path)",
            "expected_error": "sys"
        },
        {
            "name": "socket",
            "code": "import socket\ns = socket.socket()\nprint(s)",
            "expected_error": "socket"
        },
        {
            "name": "urllib",
            "code": "import urllib.request\nprint(urllib.request)",
            "expected_error": "urllib"
        },
        {
            "name": "requests",
            "code": "import requests\nprint(requests)",
            "expected_error": "requests"
        },
        {
            "name": "time",
            "code": "import time\nprint(time.sleep)",
            "expected_error": "time"
        },
        {
            "name": "threading",
            "code": "import threading\nprint(threading.Thread)",
            "expected_error": "threading"
        },
        {
            "name": "multiprocessing",
            "code": "import multiprocessing\nprint(multiprocessing.Process)",
            "expected_error": "multiprocessing"
        },
        {
            "name": "pickle",
            "code": "import pickle\nprint(pickle.dumps)",
            "expected_error": "pickle"
        }
    ]
    
    passed = 0
    total = len(blocked_tests)
    
    for test in blocked_tests:
        print(f"\n  Testing {test['name']} (should be blocked)...")
        
        try:
            payload = {"code": test["code"]}
            response = requests.post("http://localhost:8000/run", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if (data.get("status") == "error" and 
                    test["expected_error"] in data.get("error", "").lower()):
                    print(f"    ✓ {test['name']} correctly blocked")
                    passed += 1
                else:
                    print(f"    ✗ {test['name']} NOT blocked - security issue!")
                    print(f"      Response: {data}")
            else:
                print(f"    ✗ {test['name']} - unexpected status {response.status_code}")
                
        except Exception as e:
            print(f"    ✗ {test['name']} test failed - {e}")
    
    print(f"\nBlocked modules test: {passed}/{total} passed")
    return passed == total

def test_security_edge_cases():
    """Test security edge cases and bypass attempts"""
    print("\nTesting security edge cases...")
    
    edge_cases = [
        {
            "name": "dynamic_import",
            "code": "__import__('os').getcwd()",
            "should_block": True
        },
        {
            "name": "getattr_bypass",
            "code": "import builtins\ngetattr(builtins, '__import__')('os')",
            "should_block": True
        },
        {
            "name": "exec_bypass",
            "code": "exec('import os')",
            "should_block": True
        },
        {
            "name": "eval_bypass",
            "code": "eval('__import__(\"os\").getcwd()')",
            "should_block": True
        },
        {
            "name": "nested_import",
            "code": "from os import path\nprint(path)",
            "should_block": True
        },
        {
            "name": "aliased_import",
            "code": "import os as operating_system\nprint(operating_system)",
            "should_block": True
        },
        {
            "name": "valid_nested_import",
            "code": "from collections import defaultdict\ndd = defaultdict(int)\nprint(dd)",
            "should_block": False
        },
        {
            "name": "valid_math_usage",
            "code": "import math\nfrom math import sqrt\nprint(sqrt(16))",
            "should_block": False
        }
    ]
    
    passed = 0
    total = len(edge_cases)
    
    for test in edge_cases:
        print(f"\n  Testing {test['name']}...")
        
        try:
            payload = {"code": test["code"]}
            response = requests.post("http://localhost:8000/run", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                
                if test["should_block"]:
                    if data.get("status") == "error":
                        print(f"    ✓ {test['name']} correctly blocked")
                        passed += 1
                    else:
                        print(f"    ✗ {test['name']} should have been blocked!")
                        print(f"      Response: {data}")
                else:
                    if data.get("status") == "success":
                        print(f"    ✓ {test['name']} correctly allowed")
                        passed += 1
                    else:
                        print(f"    ✗ {test['name']} should have been allowed!")
                        print(f"      Response: {data}")
            else:
                print(f"    ✗ {test['name']} - unexpected status {response.status_code}")
                
        except Exception as e:
            print(f"    ✗ {test['name']} test failed - {e}")
    
    print(f"\nEdge cases test: {passed}/{total} passed")
    return passed == total

def run_security_tests():
    """Run all security tests"""
    print("PyRunner Security Validation Test Suite")
    print("=" * 60)
    
    tests = [
        ("Allowed Modules", test_allowed_modules),
        ("Blocked Modules", test_blocked_modules),
        ("Security Edge Cases", test_security_edge_cases)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}")
        print("-" * len(test_name))
        
        if test_func():
            passed_tests += 1
            print(f"✓ {test_name} PASSED")
        else:
            print(f"✗ {test_name} FAILED")
    
    print(f"\n{'='*60}")
    print(f"Security Test Results: {passed_tests}/{total_tests} test suites passed")
    
    if passed_tests == total_tests:
        print("✓ ALL SECURITY TESTS PASSED!")
        return True
    else:
        print("✗ SOME SECURITY TESTS FAILED!")
        return False

if __name__ == "__main__":
    success = run_security_tests()
    exit(0 if success else 1)