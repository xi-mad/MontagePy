from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QFrame, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MontagePy UI")
        self.resize(1000, 800)
        
        # Main Layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setSpacing(24)
        self.main_layout.setContentsMargins(24, 24, 24, 24)
        
        # Header
        self.setup_header()
        
        # Progress Section
        self.setup_progress()
        
        # File List Section
        self.setup_file_list()
        
        # Bottom Panel (Quick Settings)
        self.setup_bottom_panel()

    def setup_header(self):
        header_layout = QHBoxLayout()
        
        # Left Actions
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(16)
        
        self.btn_add_folder = QPushButton("添加文件夹")
        self.btn_add_folder.setIcon(QIcon.fromTheme("folder-new")) # Placeholder icon
        
        self.btn_add_file = QPushButton("添加文件")
        self.btn_add_file.setIcon(QIcon.fromTheme("video")) # Placeholder icon
        
        actions_layout.addWidget(self.btn_add_folder)
        actions_layout.addWidget(self.btn_add_file)
        
        # Right Actions (Toolbar)
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(8)
        
        # Container for toolbar
        toolbar_container = QFrame()
        container_layout = QHBoxLayout(toolbar_container)
        container_layout.setContentsMargins(4, 4, 4, 4)
        container_layout.setSpacing(4)
        
        self.btn_start = QPushButton()
        self.btn_start.setIcon(QIcon.fromTheme("media-playback-start"))
        self.btn_start.setToolTip("开始处理")
        self.btn_start.setFixedSize(32, 32)
        
        container_layout.addWidget(self.btn_start)
        
        header_layout.addLayout(actions_layout)
        header_layout.addStretch()
        header_layout.addWidget(toolbar_container)
        
        self.main_layout.addLayout(header_layout)

    def setup_progress(self):
        progress_frame = QFrame()
        layout = QVBoxLayout(progress_frame)
        layout.setContentsMargins(16, 16, 16, 16)
        
        header = QHBoxLayout()
        title = QLabel("处理进度")
        self.lbl_percent = QLabel("0%")
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.lbl_percent)
        
        # Progress Bar
        from PySide6.QtWidgets import QProgressBar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        
        layout.addLayout(header)
        layout.addWidget(self.progress_bar)
        
        self.main_layout.addWidget(progress_frame)

    def setup_file_list(self):
        file_list_frame = QFrame() 
        
        layout = QVBoxLayout(file_list_frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 16, 24, 16)
        
        title = QLabel("文件列表")
        self.count_badge = QLabel("0")
        
        header_layout.addWidget(title)
        header_layout.addWidget(self.count_badge)
        header_layout.addStretch()
        
        # List Area
        from montagepy.gui.widgets.file_list import FileListWidget
        self.file_list = FileListWidget()
        self.file_list.files_dropped.connect(self.add_files)
        
        layout.addWidget(header)
        layout.addWidget(self.file_list, 1) # 1 stretch factor
        
        self.main_layout.addWidget(file_list_frame, 1)

    def setup_bottom_panel(self):
        panel_layout = QHBoxLayout()
        panel_layout.setSpacing(24)
        
        # Quick Settings Card
        settings_frame = QFrame()
        settings_frame.setFixedHeight(176) # h-44 approx
        
        layout = QVBoxLayout(settings_frame)
        layout.setContentsMargins(24, 24, 24, 24)
        
        title = QLabel("快速设置")
        layout.addWidget(title)
        
        # Settings Content
        content_layout = QVBoxLayout()
        content_layout.setSpacing(12)
        
        # Output Folder Row
        folder_row = QHBoxLayout()
        folder_bg = QFrame()
        folder_layout = QHBoxLayout(folder_bg)
        folder_layout.setContentsMargins(8, 8, 8, 8)
        
        from PySide6.QtWidgets import QCheckBox, QRadioButton, QButtonGroup
        
        self.check_output = QCheckBox()
        self.check_output.setChecked(True)
        
        folder_label = QLabel("输出文件夹")
        
        self.lbl_output_path = QLabel("./output")
        
        self.btn_select_folder = QPushButton()
        self.btn_select_folder.setIcon(QIcon.fromTheme("folder"))
        self.btn_select_folder.setFixedSize(24, 24)
        self.btn_select_folder.clicked.connect(self.select_output_folder)
        
        folder_layout.addWidget(self.check_output)
        folder_layout.addWidget(folder_label)
        folder_layout.addWidget(self.lbl_output_path, 1)
        folder_layout.addWidget(self.btn_select_folder)
        
        content_layout.addWidget(folder_bg)
        
        # Options Row
        options_row = QHBoxLayout()
        options_row.setSpacing(24)
        
        # Format Selection
        format_layout = QHBoxLayout()
        format_layout.setSpacing(12)
        format_label = QLabel("输出格式:")
        
        self.radio_jpg = QRadioButton("JPG")
        self.radio_jpg.setChecked(True)
        self.radio_gif = QRadioButton("GIF")
        
        self.format_group = QButtonGroup(self)
        self.format_group.addButton(self.radio_jpg)
        self.format_group.addButton(self.radio_gif)
        
        format_layout.addWidget(format_label)
        format_layout.addWidget(self.radio_jpg)
        format_layout.addWidget(self.radio_gif)
        
        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setFixedHeight(16)
        
        # Checkboxes
        self.check_keep_structure = QCheckBox("保留文件夹结构")
        self.check_overwrite = QCheckBox("覆盖已存在文件 (Overwrite)")
        
        options_row.addLayout(format_layout)
        options_row.addWidget(sep)
        options_row.addWidget(self.check_keep_structure)
        options_row.addWidget(self.check_overwrite)
        options_row.addStretch()
        
        content_layout.addLayout(options_row)
        
        layout.addLayout(content_layout)
        layout.addStretch()
        
        panel_layout.addWidget(settings_frame, 1)
        
        self.main_layout.addLayout(panel_layout)
        
        # Connect signals
        self.btn_add_folder.clicked.connect(self.add_folder)
        self.btn_add_file.clicked.connect(self.add_file)
        self.btn_start.clicked.connect(self.start_processing)

    def add_files(self, files):
        """Add files to the list."""
        self.file_list.add_files(files)
        self.update_count()

    def add_folder(self):
        """Open dialog to select folder."""
        from PySide6.QtWidgets import QFileDialog
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            # Scan folder for video files
            from montagepy.utils.file_utils import scan_video_files
            files = scan_video_files(folder)
            self.add_files(files)

    def add_file(self):
        """Open dialog to select files."""
        from PySide6.QtWidgets import QFileDialog
        files, _ = QFileDialog.getOpenFileNames(self, "选择文件", "", "Video Files (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm)")
        if files:
            self.add_files(files)

    def select_output_folder(self):
        """Open dialog to select output folder."""
        from PySide6.QtWidgets import QFileDialog
        folder = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if folder:
            self.lbl_output_path.setText(folder)

    def update_count(self):
        """Update the file count badge."""
        count = self.file_list.rowCount()
        self.count_badge.setText(str(count))

    def start_processing(self):
        """Start the montage generation process."""
        files = []
        for i in range(self.file_list.rowCount()):
            files.append(self.file_list.item(i, 2).text())
            
        if not files:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "提示", "请先添加视频文件")
            return

        # Create Config
        from montagepy.core.config import Config
        cfg = Config()
        
        # Output settings
        if self.check_output.isChecked():
            cfg.output_path = self.lbl_output_path.text()
        else:
            cfg.output_path = "" # Default to source folder
            
        # Format
        if self.radio_gif.isChecked():
            cfg.output_format = "gif"
        else:
            cfg.output_format = "jpg"
            
        # Other settings
        cfg.overwrite = self.check_overwrite.isChecked()
        # cfg.keep_structure = self.check_keep_structure.isChecked() # Not yet in Config?
        
        # Disable UI
        self.set_ui_enabled(False)
        self.progress_bar.setValue(0)
        self.lbl_percent.setText("0%")
        
        # Start Thread
        from montagepy.gui.workers import ProcessingThread
        self.worker = ProcessingThread(files, cfg)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.log_message.connect(self.log_message)
        self.worker.finished_processing.connect(self.processing_finished)
        
        # Connect file-specific signals
        self.worker.file_started.connect(self.on_file_started)
        self.worker.file_finished.connect(self.on_file_finished)
        self.worker.file_error.connect(self.on_file_error)
        
        self.worker.start()
        
    def update_progress(self, current, total):
        if total > 0:
            percent = int((current / total) * 100)
            self.progress_bar.setValue(percent)
            self.lbl_percent.setText(f"{percent}%")
            
    def on_file_started(self, row, file_path):
        """Handle file processing started."""
        self.file_list.set_row_status(row, "处理中...", 0)
        
    def on_file_finished(self, row, file_path, success):
        """Handle file processing finished."""
        if success:
            self.file_list.set_row_status(row, "完成", 100)
            self.file_list.set_row_checked(row, True)
        else:
            # Error state is handled by on_file_error usually, but ensure status is set
            pass

    def on_file_error(self, row, file_path, error_msg):
        """Handle file processing error."""
        self.file_list.set_row_status(row, "失败", 0)
        # Optional: Add tooltip or log error
        item = self.file_list.item(row, 1)
        if item:
            item.setToolTip(error_msg)
            
    def log_message(self, msg):
        print(msg) # For now just print to console, could add a log widget later
        
    def processing_finished(self):
        self.set_ui_enabled(True)
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "完成", "处理完成！")
        
    def set_ui_enabled(self, enabled):
        self.btn_add_folder.setEnabled(enabled)
        self.btn_add_file.setEnabled(enabled)
        self.btn_start.setEnabled(enabled)
        self.file_list.setEnabled(enabled)
