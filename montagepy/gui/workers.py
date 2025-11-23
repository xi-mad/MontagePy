from PySide6.QtCore import QThread, Signal
from montagepy.core.config import Config
from montagepy.core.logger import Logger
from montagepy.core.handlers import process_single_file
import traceback

class GuiLogger(Logger):
    """Logger that emits signals for GUI updates."""
    
    def __init__(self, signal: Signal):
        self.signal = signal
        self.verbose_enabled = False

    def info(self, msg, *args):
        formatted_msg = msg % args if args else msg
        self.signal.emit(f"INFO: {formatted_msg}")

    def error(self, msg, *args):
        formatted_msg = msg % args if args else msg
        self.signal.emit(f"ERROR: {formatted_msg}")

    def warning(self, msg, *args):
        formatted_msg = msg % args if args else msg
        self.signal.emit(f"WARNING: {formatted_msg}")
        
    def verbose(self, msg, *args):
        if self.verbose_enabled:
            formatted_msg = msg % args if args else msg
            self.signal.emit(f"DEBUG: {formatted_msg}")

class ProcessingThread(QThread):
    """Thread for processing video files."""
    
    progress_updated = Signal(int, int) # current, total
    log_message = Signal(str)
    finished_processing = Signal()
    
    # New signals for per-file progress
    file_started = Signal(int, str) # row_index, file_path
    file_finished = Signal(int, str, bool) # row_index, file_path, success
    file_error = Signal(int, str, str) # row_index, file_path, error_message
    
    def __init__(self, files, config: Config):
        super().__init__()
        self.files = files
        self.config = config
        self.is_running = True

    def run(self):
        logger = GuiLogger(self.log_message)
        total = len(self.files)
        
        for i, file_path in enumerate(self.files):
            if not self.is_running:
                break
                
            self.progress_updated.emit(i, total)
            self.file_started.emit(i, file_path)
            
            try:
                # Create a copy of config for this file
                file_config = Config()
                file_config.__dict__.update(self.config.__dict__)
                file_config.input_path = file_path
                
                # Process
                process_single_file(file_config, logger)
                self.file_finished.emit(i, file_path, True)
                
            except BaseException as e:
                logger.error(f"Failed to process {file_path}: {e}")
                self.file_error.emit(i, file_path, str(e))
                self.file_finished.emit(i, file_path, False)
                traceback.print_exc()
                
        self.progress_updated.emit(total, total)
        self.finished_processing.emit()

    def stop(self):
        self.is_running = False
