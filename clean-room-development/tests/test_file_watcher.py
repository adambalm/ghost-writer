"""
Tests for file watching functionality
"""

import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch
from threading import Event

from src.utils.file_watcher import FileWatcher, NoteFileHandler


class TestNoteFileHandler:
    """Test the file system event handler"""
    
    def setup_method(self):
        """Setup for each test"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.callback = Mock()
        self.handler = NoteFileHandler(self.callback)
    
    def teardown_method(self):
        """Cleanup after each test"""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_handler_initialization(self):
        """Test handler initializes correctly"""
        assert self.handler.callback == self.callback
        assert self.handler.processed_files == set()
        assert ".note" in self.handler.SUPPORTED_EXTENSIONS
        assert ".png" in self.handler.SUPPORTED_EXTENSIONS
    
    def test_on_created_supported_file(self):
        """Test handling creation of supported file"""
        from watchdog.events import FileCreatedEvent
        
        test_file = self.temp_dir / "test.note"
        event = FileCreatedEvent(str(test_file))
        
        # Mock sleep to speed up test
        with patch('time.sleep'):
            self.handler.on_created(event)
        
        self.callback.assert_called_once_with(test_file)
        assert str(test_file) in self.handler.processed_files
    
    def test_on_created_unsupported_file(self):
        """Test handling creation of unsupported file"""
        from watchdog.events import FileCreatedEvent
        
        test_file = self.temp_dir / "test.txt"
        event = FileCreatedEvent(str(test_file))
        
        self.handler.on_created(event)
        
        self.callback.assert_not_called()
        assert str(test_file) not in self.handler.processed_files
    
    def test_on_created_directory(self):
        """Test handling directory creation (should be ignored)"""
        from watchdog.events import DirCreatedEvent
        
        test_dir = self.temp_dir / "new_folder"
        event = DirCreatedEvent(str(test_dir))
        
        self.handler.on_created(event)
        
        self.callback.assert_not_called()
    
    def test_on_created_duplicate_file(self):
        """Test handling duplicate file creation"""
        from watchdog.events import FileCreatedEvent
        
        test_file = self.temp_dir / "test.png"
        event = FileCreatedEvent(str(test_file))
        
        # Add file to processed set first
        self.handler.processed_files.add(str(test_file))
        
        with patch('time.sleep'):
            self.handler.on_created(event)
        
        # Should not call callback for already processed file
        self.callback.assert_not_called()
    
    def test_on_moved_supported_file(self):
        """Test handling file move to supported extension"""
        from watchdog.events import FileMovedEvent
        
        src_file = self.temp_dir / "temp.tmp"
        dest_file = self.temp_dir / "final.note"
        event = FileMovedEvent(str(src_file), str(dest_file))
        
        with patch('time.sleep'):
            self.handler.on_moved(event)
        
        self.callback.assert_called_once_with(dest_file)
        assert str(dest_file) in self.handler.processed_files
    
    def test_on_created_callback_exception(self):
        """Test handling callback exception"""
        from watchdog.events import FileCreatedEvent
        
        test_file = self.temp_dir / "test.jpg"
        event = FileCreatedEvent(str(test_file))
        
        # Make callback raise exception
        self.callback.side_effect = Exception("Callback failed")
        
        with patch('time.sleep'):
            # Should not raise exception
            self.handler.on_created(event)
        
        self.callback.assert_called_once()


class TestFileWatcher:
    """Test the main file watcher class"""
    
    def setup_method(self):
        """Setup for each test"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.callback = Mock()
    
    def teardown_method(self):
        """Cleanup after each test"""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_watcher_initialization(self):
        """Test watcher initializes correctly"""
        watcher = FileWatcher(self.temp_dir, self.callback)
        
        assert watcher.watch_directory == self.temp_dir
        assert watcher.file_callback == self.callback
        assert watcher.poll_interval == 5  # default
        assert watcher.last_seen_files == set()
    
    def test_watcher_custom_poll_interval(self):
        """Test watcher with custom poll interval"""
        watcher = FileWatcher(self.temp_dir, self.callback, poll_interval=10)
        assert watcher.poll_interval == 10
    
    def test_start_nonexistent_directory(self):
        """Test starting watcher on nonexistent directory"""
        nonexistent_dir = self.temp_dir / "missing"
        watcher = FileWatcher(nonexistent_dir, self.callback)
        
        with pytest.raises(ValueError, match="does not exist"):
            watcher.start()
    
    @patch('src.utils.file_watcher.Observer')
    def test_start_file_system_watcher(self, mock_observer_class):
        """Test starting file system watcher"""
        mock_observer = Mock()
        mock_observer_class.return_value = mock_observer
        
        watcher = FileWatcher(self.temp_dir, self.callback)
        watcher.stop_event.set()  # Stop immediately
        
        watcher.start()
        
        # Verify observer was configured and started
        mock_observer.schedule.assert_called_once()
        mock_observer.start.assert_called_once()
    
    @patch('src.utils.file_watcher.Observer')
    def test_start_fallback_to_polling(self, mock_observer_class):
        """Test fallback to polling when file system events fail"""
        mock_observer = Mock()
        mock_observer.schedule.side_effect = Exception("FS events failed")
        mock_observer_class.return_value = mock_observer
        
        watcher = FileWatcher(self.temp_dir, self.callback, poll_interval=1)
        
        # Create a test file before starting
        test_file = self.temp_dir / "existing.png"
        test_file.touch()
        
        # Use a thread to stop the watcher after short delay
        import threading
        def stop_watcher():
            time.sleep(0.1)
            watcher.stop()
        
        stop_thread = threading.Thread(target=stop_watcher, daemon=True)
        stop_thread.start()
        
        watcher.start()
        
        # Should have fallen back to polling mode
        assert len(watcher.last_seen_files) > 0
    
    def test_scan_for_new_files(self):
        """Test scanning directory for new files"""
        watcher = FileWatcher(self.temp_dir, self.callback)
        
        # Create some test files
        (self.temp_dir / "test1.note").touch()
        (self.temp_dir / "test2.png").touch()
        (self.temp_dir / "ignore.txt").touch()
        
        watcher._scan_for_new_files()
        
        # Should detect supported files
        assert len(watcher.last_seen_files) == 2
        supported_files = [f for f in watcher.last_seen_files 
                          if any(f.endswith(ext) for ext in [".note", ".png"])]
        assert len(supported_files) == 2
    
    def test_scan_for_new_files_with_callback(self):
        """Test scanning with callback for new files"""
        watcher = FileWatcher(self.temp_dir, self.callback)
        
        # Initial scan
        watcher._scan_for_new_files()
        initial_count = len(watcher.last_seen_files)
        
        # Add new file
        new_file = self.temp_dir / "new.jpg"
        new_file.touch()
        
        # Scan again
        watcher._scan_for_new_files()
        
        # Callback should be called for new file
        self.callback.assert_called_once()
        args = self.callback.call_args[0]
        assert args[0] == new_file
    
    def test_scan_ignores_unchanged_files(self):
        """Test that scanning ignores files that haven't changed"""
        watcher = FileWatcher(self.temp_dir, self.callback)
        
        # Create file and do initial scan
        test_file = self.temp_dir / "unchanged.pdf"
        test_file.touch()
        watcher._scan_for_new_files()
        
        # Clear callback mock
        self.callback.reset_mock()
        
        # Scan again - should not trigger callback
        watcher._scan_for_new_files()
        self.callback.assert_not_called()
    
    def test_stop_watcher(self):
        """Test stopping the watcher"""
        with patch('src.utils.file_watcher.Observer') as mock_observer_class:
            mock_observer = Mock()
            mock_observer_class.return_value = mock_observer
            
            watcher = FileWatcher(self.temp_dir, self.callback)
            watcher.stop()
            
            assert watcher.stop_event.is_set()
    
    def test_context_manager(self):
        """Test using watcher as context manager"""
        with patch('src.utils.file_watcher.Observer'):
            with FileWatcher(self.temp_dir, self.callback) as watcher:
                assert isinstance(watcher, FileWatcher)
            
            # Should be stopped after context exit
            assert watcher.stop_event.is_set()
    
    def test_scan_error_handling(self):
        """Test error handling in scan method"""
        watcher = FileWatcher(self.temp_dir, self.callback)
        
        # Make glob method raise exception
        with patch('pathlib.Path.rglob', side_effect=Exception("Scan failed")):
            # Should not raise exception
            watcher._scan_for_new_files()
        
        # Should still have empty file set
        assert watcher.last_seen_files == set()
    
    def test_callback_exception_in_scan(self):
        """Test handling callback exception during scan"""
        watcher = FileWatcher(self.temp_dir, self.callback)
        
        # Make callback raise exception
        self.callback.side_effect = Exception("Callback error")
        
        # Create test file
        test_file = self.temp_dir / "test.note"
        test_file.touch()
        
        # Should not raise exception
        watcher._scan_for_new_files()
        
        # File should still be tracked
        assert str(test_file) in watcher.last_seen_files