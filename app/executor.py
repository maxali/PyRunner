import asyncio
import subprocess
import tempfile
import time
import psutil
import os
import signal
from typing import Tuple, Optional
from app.models import ExecutionStatus


class CodeExecutor:
    """Executes Python code in an isolated subprocess with resource limits"""
    
    @staticmethod
    async def execute(code: str, timeout: int = 30, memory_limit: int = 512) -> Tuple[ExecutionStatus, str, str, float, Optional[float]]:
        """
        Execute Python code with timeout and memory limits.
        Returns (status, stdout, stderr, execution_time, memory_used)
        """
        start_time = time.time()
        
        # Create temporary file for code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
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