"""Integration tests for security validation"""

import pytest
import httpx
from tests.conftest import assert_success_response, assert_error_response


class TestAllowedModules:
    """Test cases for allowed modules"""
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_math_module(self, api_client: httpx.AsyncClient):
        """Test math module is allowed"""
        payload = {"code": "import math\nprint(f'π = {math.pi}')"}
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data, "π = 3.141592653589793")
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_numpy_module(self, api_client: httpx.AsyncClient):
        """Test numpy module is allowed"""
        payload = {"code": "import numpy as np\narr = np.array([1, 2, 3])\nprint(f'Array: {arr}')"}
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data, "Array: [1 2 3]")
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_sympy_module(self, api_client: httpx.AsyncClient):
        """Test sympy module is allowed"""
        payload = {"code": "import sympy as sp\nx = sp.Symbol('x')\nprint(f'Symbol: {x}')"}
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data, "Symbol: x")
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_pandas_module(self, api_client: httpx.AsyncClient):
        """Test pandas module is allowed"""
        payload = {"code": "import pandas as pd\ndf = pd.DataFrame({'A': [1, 2]})\nprint(f'DataFrame:\\n{df}')"}
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data, "DataFrame:")
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_matplotlib_module(self, api_client: httpx.AsyncClient):
        """Test matplotlib module is allowed"""
        payload = {"code": "import matplotlib\nprint(f'Matplotlib version: {matplotlib.__version__}')"}
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data, "Matplotlib version:")
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_scipy_module(self, api_client: httpx.AsyncClient):
        """Test scipy module is allowed"""
        payload = {"code": "import scipy\nprint(f'SciPy version: {scipy.__version__}')"}
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data, "SciPy version:")
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_sklearn_module(self, api_client: httpx.AsyncClient):
        """Test sklearn module is allowed"""
        payload = {"code": "import sklearn\nprint(f'Scikit-learn version: {sklearn.__version__}')"}
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data, "Scikit-learn version:")
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_collections_module(self, api_client: httpx.AsyncClient):
        """Test collections module is allowed"""
        payload = {"code": "from collections import Counter\nc = Counter([1, 2, 2, 3])\nprint(f'Counter: {c}')"}
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data, "Counter: Counter({2: 2, 1: 1, 3: 1})")
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_itertools_module(self, api_client: httpx.AsyncClient):
        """Test itertools module is allowed"""
        payload = {"code": "import itertools\nresult = list(itertools.combinations([1, 2, 3], 2))\nprint(f'Combinations: {result}')"}
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data, "Combinations: [(1, 2), (1, 3), (2, 3)]")
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_functools_module(self, api_client: httpx.AsyncClient):
        """Test functools module is allowed"""
        payload = {"code": "from functools import reduce\nresult = reduce(lambda x, y: x + y, [1, 2, 3, 4])\nprint(f'Sum: {result}')"}
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data, "Sum: 10")


class TestBlockedModules:
    """Test cases for blocked modules"""
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_os_module_blocked(self, api_client: httpx.AsyncClient):
        """Test os module is blocked"""
        payload = {"code": "import os\nprint(os.getcwd())"}
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_error_response(data, "os")
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_subprocess_module_blocked(self, api_client: httpx.AsyncClient):
        """Test subprocess module is blocked"""
        payload = {"code": "import subprocess\nresult = subprocess.run(['echo', 'test'])\nprint(result)"}
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_error_response(data, "subprocess")
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_sys_module_blocked(self, api_client: httpx.AsyncClient):
        """Test sys module is blocked"""
        payload = {"code": "import sys\nprint(sys.path)"}
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_error_response(data, "sys")
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_socket_module_blocked(self, api_client: httpx.AsyncClient):
        """Test socket module is blocked"""
        payload = {"code": "import socket\ns = socket.socket()\nprint(s)"}
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_error_response(data, "socket")
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_urllib_module_blocked(self, api_client: httpx.AsyncClient):
        """Test urllib module is blocked"""
        payload = {"code": "import urllib.request\nprint(urllib.request)"}
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_error_response(data, "urllib")
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_requests_module_blocked(self, api_client: httpx.AsyncClient):
        """Test requests module is blocked"""
        payload = {"code": "import requests\nprint(requests)"}
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_error_response(data, "requests")
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_time_module_blocked(self, api_client: httpx.AsyncClient):
        """Test time module is blocked"""
        payload = {"code": "import time\nprint(time.sleep)"}
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_error_response(data, "time")
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_threading_module_blocked(self, api_client: httpx.AsyncClient):
        """Test threading module is blocked"""
        payload = {"code": "import threading\nprint(threading.Thread)"}
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_error_response(data, "threading")
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_multiprocessing_module_blocked(self, api_client: httpx.AsyncClient):
        """Test multiprocessing module is blocked"""
        payload = {"code": "import multiprocessing\nprint(multiprocessing.Process)"}
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_error_response(data, "multiprocessing")
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_pickle_module_blocked(self, api_client: httpx.AsyncClient):
        """Test pickle module is blocked"""
        payload = {"code": "import pickle\nprint(pickle.dumps)"}
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_error_response(data, "pickle")


class TestSecurityBypassAttempts:
    """Test cases for security bypass attempts"""
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_dynamic_import_blocked(self, api_client: httpx.AsyncClient):
        """Test dynamic import is blocked"""
        payload = {"code": "__import__('os').getcwd()"}
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_error_response(data, "__import__")
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_getattr_bypass_blocked(self, api_client: httpx.AsyncClient):
        """Test getattr bypass is blocked"""
        payload = {"code": "import builtins\ngetattr(builtins, '__import__')('os')"}
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_error_response(data, "builtins")
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_exec_bypass_blocked(self, api_client: httpx.AsyncClient):
        """Test exec bypass is blocked"""
        payload = {"code": "exec('import os')"}
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_error_response(data, "exec")
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_eval_bypass_blocked(self, api_client: httpx.AsyncClient):
        """Test eval bypass is blocked"""
        payload = {"code": "eval('__import__(\"os\").getcwd()')"}
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_error_response(data, "eval")
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_nested_import_blocked(self, api_client: httpx.AsyncClient):
        """Test nested import is blocked"""
        payload = {"code": "from os import path\nprint(path)"}
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_error_response(data, "os")
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_aliased_import_blocked(self, api_client: httpx.AsyncClient):
        """Test aliased import is blocked"""
        payload = {"code": "import os as operating_system\nprint(operating_system)"}
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_error_response(data, "os")
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_function_level_import_blocked(self, api_client: httpx.AsyncClient):
        """Test function-level import is blocked"""
        payload = {
            "code": """
def malicious_function():
    import os
    return os.getcwd()

result = malicious_function()
print(result)
"""
        }
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_error_response(data, "os")
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_class_level_import_blocked(self, api_client: httpx.AsyncClient):
        """Test class-level import is blocked"""
        payload = {
            "code": """
class MaliciousClass:
    def __init__(self):
        import subprocess
        self.subprocess = subprocess
    
    def execute(self):
        return self.subprocess.run(['echo', 'test'])

obj = MaliciousClass()
result = obj.execute()
print(result)
"""
        }
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_error_response(data, "subprocess")
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_complex_bypass_blocked(self, api_client: httpx.AsyncClient):
        """Test complex bypass attempt is blocked"""
        payload = {
            "code": """
def get_module(name):
    return __import__(name)

def execute_command(cmd):
    os_module = get_module('os')
    return os_module.system(cmd)

result = execute_command('echo test')
print(result)
"""
        }
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_error_response(data, "__import__")


class TestValidSecurityCases:
    """Test cases for valid security scenarios"""
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_valid_nested_import(self, api_client: httpx.AsyncClient):
        """Test valid nested import from allowed module"""
        payload = {"code": "from collections import defaultdict\ndd = defaultdict(int)\ndd['test'] = 1\nprint(dict(dd))"}
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data, "{'test': 1}")
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_valid_math_usage(self, api_client: httpx.AsyncClient):
        """Test valid math module usage"""
        payload = {"code": "import math\nfrom math import sqrt\nprint(f'Square root of 16: {sqrt(16)}')\nprint(f'π: {math.pi}')"}
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data, "Square root of 16: 4.0")
        assert "π: 3.141592653589793" in data["stdout"]
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_valid_scientific_computation(self, api_client: httpx.AsyncClient):
        """Test valid scientific computation"""
        payload = {
            "code": """
import numpy as np
import sympy as sp
from scipy import integrate

# NumPy array operations
arr = np.array([1, 2, 3, 4, 5])
mean = np.mean(arr)
std = np.std(arr)

# SymPy symbolic computation
x = sp.Symbol('x')
expr = x**2 + 2*x + 1
derivative = sp.diff(expr, x)

# SciPy integration
result, error = integrate.quad(lambda x: x**2, 0, 1)

print(f'Array mean: {mean}')
print(f'Array std: {std:.4f}')
print(f'Derivative: {derivative}')
print(f'Integration result: {result:.4f}')
"""
        }
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data)
        assert "Array mean: 3.0" in data["stdout"]
        assert "Derivative: 2*x + 2" in data["stdout"]
        assert "Integration result: 0.3333" in data["stdout"]
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_valid_data_processing(self, api_client: httpx.AsyncClient):
        """Test valid data processing with pandas"""
        payload = {
            "code": """
import pandas as pd
import numpy as np

# Create sample data
data = {
    'name': ['Alice', 'Bob', 'Charlie'],
    'age': [25, 30, 35],
    'score': [85.5, 92.3, 78.9]
}

df = pd.DataFrame(data)
print("Original DataFrame:")
print(df)

# Basic operations
mean_age = df['age'].mean()
max_score = df['score'].max()

print(f"\\nMean age: {mean_age}")
print(f"Max score: {max_score}")
"""
        }
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data)
        assert "Alice" in data["stdout"]
        assert "Mean age: 30.0" in data["stdout"]
        assert "Max score: 92.3" in data["stdout"]