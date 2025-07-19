import re
import ast
from typing import Set, List


class SecurityValidator:
    """Basic security validation for Python code"""
    
    # Dangerous imports and functions
    DANGEROUS_IMPORTS = {
        'os', 'subprocess', 'sys', 'importlib', 'eval', 'exec',
        'compile', '__import__', 'open', 'file', 'input', 'raw_input',
        'socket', 'urllib', 'httplib', 'ftplib', 'telnetlib',
        'pickle', 'cPickle', 'marshal', 'shelve'
    }
    
    DANGEROUS_BUILTINS = {
        'eval', 'exec', 'compile', '__import__', 'open', 'file',
        'input', 'raw_input', 'execfile', 'reload'
    }
    
    # Allowed modules for scientific computing (fully safe modules)
    ALLOWED_MODULES = {
        'math', 'cmath', 'decimal', 'fractions', 'random', 'statistics',
        'itertools', 'functools', 'operator', 'collections', 'heapq',
        'bisect', 'array', 'datetime', 'calendar', 'copy', 'pprint',
        're', 'string', 'textwrap', 'unicodedata', 'json', 'csv',
        'numpy', 'sympy', 'pandas', 'matplotlib', 'scipy', 'sklearn'
    }
    
    # Allowed specific imports from partially-safe modules
    ALLOWED_MODULE_IMPORTS = {
        'io': {
            'StringIO', 'BytesIO', 'TextIOWrapper', 'BufferedReader', 
            'BufferedWriter', 'BufferedRWPair', 'BufferedRandom',
            'IOBase', 'RawIOBase', 'BufferedIOBase', 'TextIOBase',
            'DEFAULT_BUFFER_SIZE', 'SEEK_SET', 'SEEK_CUR', 'SEEK_END',
            'UnsupportedOperation', 'BlockingIOError', 'IncrementalNewlineDecoder'
        }
    }
    
    @classmethod
    def validate_code(cls, code: str) -> tuple[bool, str]:
        """
        Validate Python code for security issues.
        Returns (is_valid, error_message)
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, f"Syntax error: {str(e)}"
        
        validator = SecurityChecker(cls.DANGEROUS_IMPORTS, cls.DANGEROUS_BUILTINS, cls.ALLOWED_MODULES, cls.ALLOWED_MODULE_IMPORTS)
        try:
            validator.visit(tree)
        except SecurityError as e:
            return False, str(e)
        
        return True, ""


class SecurityError(Exception):
    """Raised when security violation is detected"""
    pass


class SecurityChecker(ast.NodeVisitor):
    """AST visitor to check for security issues"""
    
    def __init__(self, dangerous_imports: Set[str], dangerous_builtins: Set[str], allowed_modules: Set[str], allowed_module_imports: dict):
        self.dangerous_imports = dangerous_imports
        self.dangerous_builtins = dangerous_builtins
        self.allowed_modules = allowed_modules
        self.allowed_module_imports = allowed_module_imports
    
    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            module_name = alias.name.split('.')[0]
            if module_name in self.dangerous_imports:
                raise SecurityError(f"Import of '{module_name}' is not allowed")
            
            # For modules with granular controls, block direct import
            if module_name in self.allowed_module_imports:
                raise SecurityError(f"Direct import of '{module_name}' is not allowed. Use 'from {module_name} import specific_item' instead")
            
            if module_name not in self.allowed_modules and not module_name.startswith('_'):
                raise SecurityError(f"Import of '{module_name}' is not in the allowed list")
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            module_name = node.module.split('.')[0]
            if module_name in self.dangerous_imports:
                raise SecurityError(f"Import from '{module_name}' is not allowed")
            
            # Check if module is fully allowed
            if module_name in self.allowed_modules:
                self.generic_visit(node)
                return
            
            # Check if module has granular import controls
            if module_name in self.allowed_module_imports:
                # Check each specific import
                for alias in node.names:
                    import_name = alias.name
                    if import_name == '*':
                        raise SecurityError(f"Wildcard import from '{module_name}' is not allowed")
                    if import_name not in self.allowed_module_imports[module_name]:
                        raise SecurityError(f"Import of '{import_name}' from '{module_name}' is not allowed")
                self.generic_visit(node)
                return
            
            # Module not in either allowed list
            if not module_name.startswith('_'):
                raise SecurityError(f"Import from '{module_name}' is not in the allowed list")
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call):
        # Check for dangerous function calls
        if isinstance(node.func, ast.Name):
            if node.func.id in self.dangerous_builtins:
                raise SecurityError(f"Call to '{node.func.id}' is not allowed")
        
        # Check for getattr/setattr/delattr
        if isinstance(node.func, ast.Name) and node.func.id in {'getattr', 'setattr', 'delattr'}:
            raise SecurityError(f"Call to '{node.func.id}' is not allowed")
        
        self.generic_visit(node)
    
    def visit_Attribute(self, node: ast.Attribute):
        # Check for dangerous attribute access patterns
        dangerous_attrs = {'__globals__', '__code__', '__class__', '__bases__', '__subclasses__'}
        if node.attr in dangerous_attrs:
            raise SecurityError(f"Access to '{node.attr}' attribute is not allowed")
        self.generic_visit(node)