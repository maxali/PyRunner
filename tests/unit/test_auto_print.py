import pytest
from app.executor import CodeExecutor


class TestAutoPrintWrapper:
    """Test the auto-print code wrapper functionality"""
    
    def test_simple_expression(self):
        """Test wrapping a simple expression"""
        code = "1 + 2"
        wrapped = CodeExecutor.wrap_code_with_auto_print(code, auto_print=True)
        expected = "__auto_print_result = 1 + 2\nif __auto_print_result is not None:\n    print(__auto_print_result)"
        assert wrapped == expected
    
    def test_expression_with_variables(self):
        """Test wrapping expression that uses variables"""
        code = "x = 5\nx + 10"
        wrapped = CodeExecutor.wrap_code_with_auto_print(code, auto_print=True)
        assert "x = 5" in wrapped
        assert "__auto_print_result = x + 10" in wrapped
        assert "print(__auto_print_result)" in wrapped
    
    def test_multiline_expression(self):
        """Test wrapping multiline expression"""
        code = """import math
math.pi * 2"""
        wrapped = CodeExecutor.wrap_code_with_auto_print(code, auto_print=True)
        assert "import math" in wrapped
        assert "__auto_print_result = math.pi * 2" in wrapped
    
    def test_already_has_print(self):
        """Test that code already ending with print is not modified"""
        code = "x = 5\nprint(x)"
        wrapped = CodeExecutor.wrap_code_with_auto_print(code, auto_print=True)
        assert wrapped == code  # Should remain unchanged
    
    def test_ends_with_assignment(self):
        """Test that code ending with assignment is not modified"""
        code = "x = 5\ny = x + 10"
        wrapped = CodeExecutor.wrap_code_with_auto_print(code, auto_print=True)
        assert wrapped == code  # Should remain unchanged
    
    def test_ends_with_function_def(self):
        """Test that code ending with function definition is not modified"""
        code = """def add(a, b):
    return a + b"""
        wrapped = CodeExecutor.wrap_code_with_auto_print(code, auto_print=True)
        assert wrapped == code  # Should remain unchanged
    
    def test_ends_with_class_def(self):
        """Test that code ending with class definition is not modified"""
        code = """class MyClass:
    pass"""
        wrapped = CodeExecutor.wrap_code_with_auto_print(code, auto_print=True)
        assert wrapped == code  # Should remain unchanged
    
    def test_auto_print_disabled(self):
        """Test that code is not modified when auto_print is False"""
        code = "1 + 2"
        wrapped = CodeExecutor.wrap_code_with_auto_print(code, auto_print=False)
        assert wrapped == code  # Should remain unchanged
    
    def test_empty_code(self):
        """Test handling of empty code"""
        code = ""
        wrapped = CodeExecutor.wrap_code_with_auto_print(code, auto_print=True)
        assert wrapped == code  # Should remain unchanged
    
    def test_whitespace_only(self):
        """Test handling of whitespace-only code"""
        code = "   \n  \t  "
        wrapped = CodeExecutor.wrap_code_with_auto_print(code, auto_print=True)
        assert wrapped == code  # Should remain unchanged
    
    def test_syntax_error(self):
        """Test handling of code with syntax errors"""
        code = "x = 5 +"  # Syntax error
        wrapped = CodeExecutor.wrap_code_with_auto_print(code, auto_print=True)
        assert wrapped == code  # Should return original code
    
    def test_indented_expression(self):
        """Test that expressions inside control structures are not wrapped"""
        code = """if True:
    x = 5
    x + 10"""
        wrapped = CodeExecutor.wrap_code_with_auto_print(code, auto_print=True)
        # Expressions inside control structures should not be wrapped
        assert wrapped == code
    
    def test_complex_expression(self):
        """Test wrapping complex expression"""
        code = """from sympy import symbols, solve
x = symbols('x')
equation = x**2 + 4*x + 6
solutions = solve(equation, x)
solutions"""
        wrapped = CodeExecutor.wrap_code_with_auto_print(code, auto_print=True)
        assert "__auto_print_result = solutions" in wrapped
        assert "print(__auto_print_result)" in wrapped
    
    def test_none_result_not_printed(self):
        """Test that None results are not printed"""
        code = "None"
        wrapped = CodeExecutor.wrap_code_with_auto_print(code, auto_print=True)
        assert "if __auto_print_result is not None:" in wrapped
    
    def test_multiline_last_expression(self):
        """Test handling of multiline last expression"""
        code = """x = 5
(x + 
 10 +
 20)"""
        wrapped = CodeExecutor.wrap_code_with_auto_print(code, auto_print=True)
        assert "__auto_print_result = (x + \n 10 +\n 20)" in wrapped
    
    def test_import_only(self):
        """Test code with only imports"""
        code = "import math"
        wrapped = CodeExecutor.wrap_code_with_auto_print(code, auto_print=True)
        assert wrapped == code  # Should remain unchanged
    
    def test_ends_with_if_statement(self):
        """Test code ending with if statement"""
        code = """x = 5
if x > 0:
    pass"""
        wrapped = CodeExecutor.wrap_code_with_auto_print(code, auto_print=True)
        assert wrapped == code  # Should remain unchanged
    
    def test_ends_with_for_loop(self):
        """Test code ending with for loop"""
        code = """for i in range(5):
    pass"""
        wrapped = CodeExecutor.wrap_code_with_auto_print(code, auto_print=True)
        assert wrapped == code  # Should remain unchanged
    
    def test_ends_with_while_loop(self):
        """Test code ending with while loop"""
        code = """i = 0
while i < 5:
    i += 1"""
        wrapped = CodeExecutor.wrap_code_with_auto_print(code, auto_print=True)
        assert wrapped == code  # Should remain unchanged