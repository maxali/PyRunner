"""Unit tests for code executor"""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock, AsyncMock
import subprocess
import signal
import psutil
import asyncio

from app.executor import CodeExecutor
from app.models import ExecutionStatus


class TestCodeExecutor:
    """Test cases for CodeExecutor class"""
    
    def test_class_exists(self):
        """Test CodeExecutor class exists"""
        assert CodeExecutor is not None
        assert hasattr(CodeExecutor, 'execute')
    
    @pytest.mark.unit
    def test_set_limits(self):
        """Test resource limit setting"""
        with patch('resource.setrlimit') as mock_setrlimit:
            CodeExecutor._set_limits(512)
            
            # Check that setrlimit was called for memory, CPU, and file limits
            assert mock_setrlimit.call_count >= 3
    
    @pytest.mark.unit
    @patch('resource.setrlimit')
    def test_set_limits_with_values(self, mock_setrlimit):
        """Test resource limit setting with specific values"""
        import resource
        
        CodeExecutor._set_limits(1024)
        
        # Should set memory limit (RLIMIT_AS) to 1024MB
        calls = mock_setrlimit.call_args_list
        assert any(call[0][0] == resource.RLIMIT_AS for call in calls)
        assert any(call[0][0] == resource.RLIMIT_CPU for call in calls)
        assert any(call[0][0] == resource.RLIMIT_NOFILE for call in calls)
    
    @pytest.mark.unit
    @patch('resource.setrlimit')
    def test_set_limits_exception_handling(self, mock_setrlimit):
        """Test resource limit setting with exceptions"""
        mock_setrlimit.side_effect = OSError("Permission denied")
        
        # Should not raise exception even if setrlimit fails
        CodeExecutor._set_limits(512)
        assert mock_setrlimit.called
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_monitor_memory_normal(self):
        """Test memory monitoring for normal process"""
        with patch('psutil.Process') as mock_process_class:
            mock_process = MagicMock()
            mock_process.memory_info.return_value.rss = 100 * 1024 * 1024  # 100MB
            mock_process_class.return_value = mock_process
            
            # Mock the process to raise NoSuchProcess after first call
            call_count = 0
            def mock_memory_info():
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return MagicMock(rss=100 * 1024 * 1024)
                else:
                    raise psutil.NoSuchProcess(12345)
            
            mock_process.memory_info.side_effect = mock_memory_info
            
            with patch('asyncio.sleep', return_value=None):
                result = await CodeExecutor._monitor_memory(12345, 512)
                
                assert result == 100.0  # 100MB converted to MB
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_monitor_memory_exceeded(self):
        """Test memory monitoring when limit is exceeded"""
        with patch('psutil.Process') as mock_process_class:
            mock_process = MagicMock()
            mock_process.memory_info.return_value.rss = 600 * 1024 * 1024  # 600MB
            mock_process_class.return_value = mock_process
            
            with patch('asyncio.sleep', return_value=None):
                result = await CodeExecutor._monitor_memory(12345, 512)
                
                # Should kill process when memory exceeds limit
                mock_process.kill.assert_called_once()
                assert result == 600.0  # 600MB converted to MB
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_monitor_memory_process_not_found(self):
        """Test memory monitoring when process is not found"""
        with patch('psutil.Process') as mock_process_class:
            mock_process_class.side_effect = psutil.NoSuchProcess(12345)
            
            result = await CodeExecutor._monitor_memory(12345, 512)
            
            assert result is None
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_monitor_memory_access_denied(self):
        """Test memory monitoring when access is denied"""
        with patch('psutil.Process') as mock_process_class:
            mock_process_class.side_effect = psutil.AccessDenied(12345)
            
            result = await CodeExecutor._monitor_memory(12345, 512)
            
            assert result is None
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test successful code execution"""
        with patch('tempfile.NamedTemporaryFile') as mock_temp:
            mock_file = MagicMock()
            mock_file.name = '/tmp/test_file.py'
            mock_temp.return_value.__enter__.return_value = mock_file
            
            with patch('asyncio.create_subprocess_exec') as mock_subprocess:
                mock_process = AsyncMock()
                mock_process.pid = 12345
                mock_process.communicate.return_value = (b'Hello World\n', b'')
                mock_process.returncode = 0
                mock_subprocess.return_value = mock_process
                
                with patch.object(CodeExecutor, '_monitor_memory') as mock_monitor:
                    # Mock the memory monitor to raise CancelledError when cancelled
                    mock_monitor.side_effect = asyncio.CancelledError()
                    with patch('os.unlink'):
                        status, stdout, stderr, exec_time, memory_used = await CodeExecutor.execute("print('Hello World')")
                        
                        assert status == ExecutionStatus.SUCCESS
                        assert stdout == 'Hello World\n'
                        assert stderr == ''
                        assert exec_time > 0
                        # Memory monitoring task gets cancelled, so memory_used is None
                        assert memory_used is None
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_with_error(self):
        """Test code execution with Python error"""
        with patch('tempfile.NamedTemporaryFile') as mock_temp:
            mock_file = MagicMock()
            mock_file.name = '/tmp/test_file.py'
            mock_temp.return_value.__enter__.return_value = mock_file
            
            with patch('asyncio.create_subprocess_exec') as mock_subprocess:
                mock_process = AsyncMock()
                mock_process.pid = 12345
                mock_process.communicate.return_value = (b'', b'ValueError: Test error\n')
                mock_process.returncode = 1
                mock_subprocess.return_value = mock_process
                
                with patch.object(CodeExecutor, '_monitor_memory') as mock_monitor:
                    # Mock the memory monitor to raise CancelledError when cancelled
                    mock_monitor.side_effect = asyncio.CancelledError()
                    with patch('os.unlink'):
                        status, stdout, stderr, exec_time, memory_used = await CodeExecutor.execute("raise ValueError('Test error')")
                        
                        assert status == ExecutionStatus.ERROR
                        assert stdout == ''
                        assert stderr == 'ValueError: Test error\n'
                        assert exec_time > 0
                        # Memory monitoring task gets cancelled, so memory_used is None
                        assert memory_used is None
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_timeout(self):
        """Test code execution with timeout"""
        with patch('tempfile.NamedTemporaryFile') as mock_temp:
            mock_file = MagicMock()
            mock_file.name = '/tmp/test_file.py'
            mock_temp.return_value.__enter__.return_value = mock_file
            
            with patch('asyncio.create_subprocess_exec') as mock_subprocess:
                mock_process = AsyncMock()
                mock_process.pid = 12345
                mock_process.communicate.side_effect = asyncio.TimeoutError()
                mock_subprocess.return_value = mock_process
                
                with patch.object(CodeExecutor, '_monitor_memory', return_value=15.0):
                    with patch('os.killpg') as mock_killpg:
                        with patch('os.getpgid', return_value=12345):
                            with patch('os.unlink'):
                                status, stdout, stderr, exec_time, memory_used = await CodeExecutor.execute("import time; time.sleep(10)", timeout=1)
                                
                                assert status == ExecutionStatus.TIMEOUT
                                assert exec_time >= 1.0
                                # Memory monitoring task gets cancelled, so memory_used is None
                                assert memory_used is None
                                mock_killpg.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_memory_exceeded(self):
        """Test code execution with memory limit exceeded"""
        with patch('tempfile.NamedTemporaryFile') as mock_temp:
            mock_file = MagicMock()
            mock_file.name = '/tmp/test_file.py'
            mock_temp.return_value.__enter__.return_value = mock_file
            
            with patch('asyncio.create_subprocess_exec') as mock_subprocess:
                mock_process = AsyncMock()
                mock_process.pid = 12345
                mock_process.communicate.return_value = (b'', b'')
                mock_process.returncode = -9  # SIGKILL
                mock_subprocess.return_value = mock_process
                
                # Mock memory monitor to exceed limit
                async def mock_monitor(pid, limit):
                    await asyncio.sleep(0.1)
                    # Simulate killing process due to memory
                    return 600.0  # 600MB > 512MB limit
                
                with patch.object(CodeExecutor, '_monitor_memory', side_effect=mock_monitor):
                    with patch('os.unlink'):
                        status, stdout, stderr, exec_time, memory_used = await CodeExecutor.execute("data = [0] * (600 * 1024 * 1024)", memory_limit=512)
                        
                        assert status == ExecutionStatus.MEMORY_EXCEEDED
                        # In the actual code when returncode is -SIGKILL, memory_used would be None
                        # because the task gets cancelled and the memory is set to None
                        assert memory_used is None
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_subprocess_error(self):
        """Test code execution with subprocess error"""
        with patch('tempfile.NamedTemporaryFile') as mock_temp:
            mock_file = MagicMock()
            mock_file.name = '/tmp/test_file.py'
            mock_temp.return_value.__enter__.return_value = mock_file
            
            with patch('asyncio.create_subprocess_exec') as mock_subprocess:
                mock_subprocess.side_effect = OSError("Failed to start subprocess")
                
                with patch('os.unlink'):
                    # The current implementation doesn't handle subprocess creation errors
                    # so this will raise an exception
                    with pytest.raises(OSError):
                        await CodeExecutor.execute("print('Hello World')")
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_cleanup_on_exception(self):
        """Test that temporary files are cleaned up on exceptions"""
        with patch('tempfile.NamedTemporaryFile') as mock_temp:
            mock_file = MagicMock()
            mock_file.name = '/tmp/test_file.py'
            mock_temp.return_value.__enter__.return_value = mock_file
            
            with patch('asyncio.create_subprocess_exec') as mock_subprocess:
                mock_subprocess.side_effect = Exception("Unexpected error")
                
                with patch('os.unlink') as mock_unlink:
                    # The current implementation doesn't handle subprocess creation errors
                    # but the finally block should still clean up the temp file
                    with pytest.raises(Exception):
                        await CodeExecutor.execute("print('Hello World')")
                    
                    # Should still clean up temp file
                    mock_unlink.assert_called_once_with('/tmp/test_file.py')
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_with_custom_parameters(self):
        """Test code execution with custom timeout and memory limits"""
        with patch('tempfile.NamedTemporaryFile') as mock_temp:
            mock_file = MagicMock()
            mock_file.name = '/tmp/test_file.py'
            mock_temp.return_value.__enter__.return_value = mock_file
            
            with patch('asyncio.create_subprocess_exec') as mock_subprocess:
                mock_process = AsyncMock()
                mock_process.pid = 12345
                mock_process.communicate.return_value = (b'Test output\n', b'')
                mock_process.returncode = 0
                mock_subprocess.return_value = mock_process
                
                with patch.object(CodeExecutor, '_monitor_memory') as mock_monitor:
                    # Mock the memory monitor to raise CancelledError when cancelled
                    mock_monitor.side_effect = asyncio.CancelledError()
                    with patch('os.unlink'):
                        status, stdout, stderr, exec_time, memory_used = await CodeExecutor.execute(
                            "print('Test output')", 
                            timeout=60, 
                            memory_limit=1024
                        )
                        
                        assert status == ExecutionStatus.SUCCESS
                        assert stdout == 'Test output\n'
                        assert stderr == ''
                        assert exec_time > 0
                        # Memory monitoring task gets cancelled, so memory_used is None
                        assert memory_used is None
                        
                        # Verify memory limit was passed to monitor
                        mock_monitor.assert_called_once_with(12345, 1024)