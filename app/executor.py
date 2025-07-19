import asyncio
import subprocess
import tempfile
import time
import psutil
import os
import signal
import ast
from typing import Tuple, Optional
from app.models import ExecutionStatus


class CodeExecutor:
    """Executes Python code in an isolated subprocess with resource limits"""
    
    @staticmethod
    def wrap_code_with_auto_print(code: str, auto_print: bool = True) -> str:
        """
        Wrap code to automatically print the last expression if auto_print is True.
        This mimics Python's interactive mode behavior.
        """
        if not auto_print or not code.strip():
            return code
        
        try:
            # Parse the code into an AST
            tree = ast.parse(code)
            
            # If the tree is empty or has no body, return original code
            if not tree.body:
                return code
            
            # Get the last statement
            last_stmt = tree.body[-1]
            
            # Check if the last statement is an expression
            if isinstance(last_stmt, ast.Expr):
                # Check if it's already a print statement
                if isinstance(last_stmt.value, ast.Call):
                    if isinstance(last_stmt.value.func, ast.Name) and last_stmt.value.func.id == 'print':
                        # Already a print statement, don't modify
                        return code
                
                # Get the line number info for proper code reconstruction
                last_line_start = last_stmt.lineno - 1
                code_lines = code.splitlines()
                
                # Find the actual expression text (handling multi-line expressions)
                expr_lines = []
                for i in range(last_line_start, len(code_lines)):
                    expr_lines.append(code_lines[i])
                    # Try to parse just this expression to see if it's complete
                    try:
                        ast.parse('\n'.join(expr_lines), mode='eval')
                        break
                    except SyntaxError:
                        # Expression continues on next line
                        continue
                
                # Reconstruct the code with the wrapped expression
                new_lines = code_lines[:last_line_start]
                
                # Create the print wrapper
                expr_text = '\n'.join(expr_lines)
                # Handle proper indentation
                indent = len(expr_lines[0]) - len(expr_lines[0].lstrip())
                indent_str = ' ' * indent
                
                # Add the wrapped expression
                new_lines.append(f"{indent_str}__auto_print_result = {expr_text}")
                new_lines.append(f"{indent_str}if __auto_print_result is not None:")
                new_lines.append(f"{indent_str}    print(__auto_print_result)")
                
                return '\n'.join(new_lines)
            
        except SyntaxError:
            # If there's a syntax error, return the original code
            # The error will be caught during execution
            pass
        except Exception:
            # For any other parsing errors, return original code
            pass
        
        return code
    
    @staticmethod
    async def execute(code: str, timeout: int = 30, memory_limit: int = 512, auto_print: bool = True) -> Tuple[ExecutionStatus, str, str, float, Optional[float]]:
        """
        Execute Python code with timeout and memory limits.
        Returns (status, stdout, stderr, execution_time, memory_used)
        """
        start_time = time.time()
        
        # Wrap code with auto-print if enabled
        wrapped_code = CodeExecutor.wrap_code_with_auto_print(code, auto_print)
        
        # Create temporary file for code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(wrapped_code)
            temp_file = f.name
        
        try:
            # Prepare subprocess with resource limits
            process = await asyncio.create_subprocess_exec(
                'python', '-u', temp_file,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=lambda: CodeExecutor._set_limits(memory_limit),
                start_new_session=True  # Create new process group for cleanup
            )
            
            # Monitor memory usage
            memory_monitor_task = asyncio.create_task(
                CodeExecutor._monitor_memory(process.pid, memory_limit)
            )
            
            try:
                # Wait for completion with timeout
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                
                execution_time = time.time() - start_time
                
                # Cancel memory monitor
                memory_monitor_task.cancel()
                try:
                    max_memory = await memory_monitor_task
                except asyncio.CancelledError:
                    max_memory = None
                
                # Determine status
                if process.returncode == 0:
                    status = ExecutionStatus.SUCCESS
                elif process.returncode == -signal.SIGKILL:
                    status = ExecutionStatus.MEMORY_EXCEEDED
                    stderr = b"Memory limit exceeded"
                else:
                    status = ExecutionStatus.ERROR
                
                return (
                    status,
                    stdout.decode('utf-8', errors='replace'),
                    stderr.decode('utf-8', errors='replace'),
                    execution_time,
                    max_memory
                )
                
            except asyncio.TimeoutError:
                # Kill the process group
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    await asyncio.sleep(0.5)  # Give it time to terminate
                    if process.returncode is None:
                        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                except ProcessLookupError:
                    pass
                
                memory_monitor_task.cancel()
                
                return (
                    ExecutionStatus.TIMEOUT,
                    "",
                    f"Execution timed out after {timeout} seconds",
                    timeout,
                    None
                )
                
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file)
            except:
                pass
    
    @staticmethod
    def _set_limits(memory_limit_mb: int):
        """Set resource limits for the subprocess"""
        import resource
        
        try:
            # Set process group for proper cleanup
            os.setpgrp()
        except Exception:
            pass  # Some systems don't support this
        
        # Set memory limit (RLIMIT_AS)
        try:
            memory_bytes = memory_limit_mb * 1024 * 1024
            _, current_hard = resource.getrlimit(resource.RLIMIT_AS)
            
            # Only set if we can actually lower the limit
            if current_hard == resource.RLIM_INFINITY or memory_bytes <= current_hard:
                resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
        except (ValueError, OSError):
            # Memory limit setting failed - continue without it
            # Memory monitoring will still work via psutil
            pass
        
        # Set CPU time limit
        try:
            _, current_hard = resource.getrlimit(resource.RLIMIT_CPU)
            cpu_limit = 300
            
            if current_hard == resource.RLIM_INFINITY or cpu_limit <= current_hard:
                resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, cpu_limit))
        except (ValueError, OSError):
            pass  # Continue without CPU limit
        
        # Limit file descriptors
        try:
            _, current_hard = resource.getrlimit(resource.RLIMIT_NOFILE)
            fd_limit = 50
            
            if current_hard == resource.RLIM_INFINITY or fd_limit <= current_hard:
                resource.setrlimit(resource.RLIMIT_NOFILE, (fd_limit, fd_limit))
        except (ValueError, OSError):
            pass  # Continue without FD limit
        
        # Disable core dumps
        try:
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        except (ValueError, OSError):
            pass  # Continue without core dump limit
    
    @staticmethod
    async def _monitor_memory(pid: int, limit_mb: int) -> Optional[float]:
        """Monitor memory usage of a process"""
        max_memory = 0
        limit_bytes = limit_mb * 1024 * 1024
        
        try:
            process = psutil.Process(pid)
            while True:
                try:
                    memory_info = process.memory_info()
                    memory_mb = memory_info.rss / 1024 / 1024
                    max_memory = max(max_memory, memory_mb)
                    
                    # Kill if exceeds limit
                    if memory_info.rss > limit_bytes:
                        process.kill()
                        break
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    break
                
                await asyncio.sleep(0.1)
                
        except Exception:
            pass
        
        return max_memory if max_memory > 0 else None