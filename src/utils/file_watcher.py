"""
File Watcher utility for monitoring directories for new Supernote files
"""

import logging
import time
from pathlib import Path
from typing import Callable, Set, List
from threading import Thread, Event

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)


class NoteFileHandler(FileSystemEventHandler):
    """Handler for file system events targeting note files"""
    
    SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".note", ".pdf"}
    
    def __init__(self, callback: Callable[[Path], None]):
        super().__init__()
        self.callback = callback
        self.processed_files: Set[str] = set()
    
    def on_created(self, event):
        """Handle new file creation"""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        
        # Check if it's a supported file type
        if file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
            # Avoid duplicate processing
            if str(file_path) not in self.processed_files:
                self.processed_files.add(str(file_path))
                logger.info(f"New file detected: {file_path}")
                
                # Give the file a moment to finish being written
                time.sleep(1)
                
                try:
                    self.callback(file_path)
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
    
    def on_moved(self, event):
        """Handle file moves (e.g., from .tmp to final name)"""
        if event.is_directory:
            return
            
        dest_path = Path(event.dest_path)
        
        if dest_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
            if str(dest_path) not in self.processed_files:
                self.processed_files.add(str(dest_path))
                logger.info(f"File moved to: {dest_path}")
                
                time.sleep(1)
                
                try:
                    self.callback(dest_path)
                except Exception as e:
                    logger.error(f"Error processing {dest_path}: {e}")


class FileWatcher:
    """File watcher for monitoring directories for new note files"""
    
    def __init__(self, 
                 watch_directory: Path,
                 file_callback: Callable[[Path], None],
                 poll_interval: int = 5):
        self.watch_directory = Path(watch_directory)
        self.file_callback = file_callback
        self.poll_interval = poll_interval
        
        self.observer = Observer()
        self.handler = NoteFileHandler(self.file_callback)
        self.stop_event = Event()
        
        # For polling mode fallback
        self.poll_thread = None
        self.last_seen_files: Set[str] = set()
        
        logger.info(f"FileWatcher initialized for: {self.watch_directory}")
    
    def start(self):
        """Start watching the directory"""
        if not self.watch_directory.exists():
            raise ValueError(f"Watch directory does not exist: {self.watch_directory}")
        
        try:
            # Try to use native file system events first
            self.observer.schedule(
                self.handler, 
                str(self.watch_directory), 
                recursive=True
            )
            self.observer.start()
            logger.info(f"Started file system watcher for: {self.watch_directory}")
            
            # Keep the main thread alive
            while not self.stop_event.is_set():
                time.sleep(1)
                
        except Exception as e:
            logger.warning(f"File system watcher failed: {e}")
            logger.info("Falling back to polling mode...")
            self._start_polling()
    
    def _start_polling(self):
        """Fallback to polling mode if file system events don't work"""
        self.poll_thread = Thread(target=self._poll_directory, daemon=True)
        self.poll_thread.start()
        
        # Initialize with current files
        self._scan_for_new_files()
        
        # Keep polling until stopped
        while not self.stop_event.is_set():
            time.sleep(self.poll_interval)
            self._scan_for_new_files()
    
    def _poll_directory(self):
        """Poll directory for new files"""
        while not self.stop_event.is_set():
            try:
                self._scan_for_new_files()
            except Exception as e:
                logger.error(f"Error polling directory: {e}")
            
            time.sleep(self.poll_interval)
    
    def _scan_for_new_files(self):
        """Scan directory for new files"""
        try:
            current_files = set()
            
            for ext in NoteFileHandler.SUPPORTED_EXTENSIONS:
                for file_path in self.watch_directory.rglob(f"*{ext}"):
                    if file_path.is_file():
                        current_files.add(str(file_path))
            
            # Find new files
            new_files = current_files - self.last_seen_files
            
            for file_path_str in new_files:
                file_path = Path(file_path_str)
                logger.info(f"New file found: {file_path}")
                
                try:
                    self.file_callback(file_path)
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
            
            self.last_seen_files = current_files
            
        except Exception as e:
            logger.error(f"Error scanning directory: {e}")
    
    def stop(self):
        """Stop watching the directory"""
        logger.info("Stopping file watcher...")
        self.stop_event.set()
        
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
        
        if self.poll_thread and self.poll_thread.is_alive():
            self.poll_thread.join()
        
        logger.info("File watcher stopped")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()


class SupernoteCloudSync:
    """Future implementation for Supernote Cloud API integration"""
    
    def __init__(self, credentials: dict):
        self.credentials = credentials
        # TODO: Initialize Supernote API client
        logger.info("SupernoteCloudSync initialized (placeholder)")
    
    def sync_notes(self, local_directory: Path) -> List[Path]:
        """Sync notes from Supernote Cloud to local directory"""
        # TODO: Implement actual API calls
        logger.info("Cloud sync not yet implemented")
        return []
    
    def get_recent_notes(self, since: str) -> List[dict]:
        """Get notes modified since a specific timestamp"""
        # TODO: Implement API call
        logger.info("Recent notes fetch not yet implemented")
        return []