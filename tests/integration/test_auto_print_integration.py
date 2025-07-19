import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
class TestAutoPrintIntegration:
    """Integration tests for auto-print functionality"""
    
    async def test_auto_print_simple_expression(self):
        """Test auto-print with simple expression"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/run", json={
                "code": "2 + 3"
            })
            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "success"
            assert result["stdout"].strip() == "5"
    
    async def test_auto_print_with_sympy(self):
        """Test auto-print with sympy expressions"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/run", json={
                "code": """from sympy import symbols, Eq, solve
x = symbols('x')
equation = Eq(x**2 + 4*x + 6, 0)
solutions = solve(equation, x)
solutions"""
            })
            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "success"
            assert "[-2 - sqrt(2)*I, -2 + sqrt(2)*I]" in result["stdout"]
    
    async def test_auto_print_disabled(self):
        """Test with auto_print disabled"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/run", json={
                "code": "2 + 3",
                "auto_print": False
            })
            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "success"
            assert result["stdout"] == ""  # No output when disabled
    
    async def test_auto_print_with_explicit_print(self):
        """Test that explicit print statements still work"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/run", json={
                "code": "x = 5\nprint(f'The value is {x}')\nx + 10"
            })
            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "success"
            assert "The value is 5" in result["stdout"]
            assert "15" in result["stdout"]
    
    async def test_auto_print_none_value(self):
        """Test that None values are not printed"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/run", json={
                "code": "x = print('Hello')\nx"  # print returns None
            })
            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "success"
            assert "Hello" in result["stdout"]
            assert result["stdout"].strip() == "Hello"  # None should not be printed
    
    async def test_auto_print_with_numpy(self):
        """Test auto-print with numpy arrays"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/run", json={
                "code": """import numpy as np
arr = np.array([1, 2, 3, 4, 5])
arr * 2"""
            })
            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "success"
            assert "[ 2  4  6  8 10]" in result["stdout"]
    
    async def test_auto_print_with_pandas(self):
        """Test auto-print with pandas DataFrames"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/run", json={
                "code": """import pandas as pd
df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
df"""
            })
            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "success"
            assert "A  B" in result["stdout"]
            assert "1  4" in result["stdout"]
    
    async def test_auto_print_complex_calculation(self):
        """Test auto-print with complex mathematical calculations"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/run", json={
                "code": """import math
radius = 5
area = math.pi * radius ** 2
area"""
            })
            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "success"
            assert "78.539" in result["stdout"]  # Approximate value of 25π
    
    async def test_auto_print_multiline_expression(self):
        """Test auto-print with multiline expression"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/run", json={
                "code": """values = [1, 2, 3, 4, 5]
sum(values) + \
len(values) * \
2"""
            })
            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "success"
            assert "25" in result["stdout"]  # 15 + 5*2 = 25
    
    async def test_auto_print_dict_output(self):
        """Test auto-print with dictionary output"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/run", json={
                "code": """data = {'name': 'Alice', 'age': 30, 'city': 'NYC'}
{k: v for k, v in data.items() if k != 'age'}"""
            })
            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "success"
            assert "'name': 'Alice'" in result["stdout"]
            assert "'city': 'NYC'" in result["stdout"]
    
    async def test_no_auto_print_for_assignment(self):
        """Test that assignments don't trigger auto-print"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/run", json={
                "code": "x = 10\ny = x * 2"
            })
            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "success"
            assert result["stdout"] == ""  # No output for assignments
    
    async def test_no_auto_print_for_function_def(self):
        """Test that function definitions don't trigger auto-print"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/run", json={
                "code": """def calculate(x, y):
    return x + y"""
            })
            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "success"
            assert result["stdout"] == ""  # No output for function definitions
    
    async def test_auto_print_with_error_code(self):
        """Test auto-print behavior with code that raises an error"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/run", json={
                "code": "1 / 0"  # This will raise ZeroDivisionError
            })
            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "error"
            assert "ZeroDivisionError" in result["stderr"]
    
    async def test_auto_print_preserves_security(self):
        """Test that auto-print doesn't bypass security checks"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/run", json={
                "code": "__import__('os').listdir('.')"
            })
            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "error"
            assert "Security validation failed" in result["stderr"]