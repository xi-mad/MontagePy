from pathlib import Path
from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView,
    QStyledItemDelegate, QStyleOptionViewItem, QStyle, QApplication, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QRect, QSize
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPainter, QColor, QBrush, QPen

class StatusDelegate(QStyledItemDelegate):
    """Delegate for the Status column (Checkbox/Icon)."""
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        # Draw the default checkbox logic or custom icon
        # For now, let's use the default check state behavior but centered
        # We can customize this further to match the specific green checkmark design later
        
        # Ensure we don't draw the default focus rect
        option.state &= ~QStyle.State_HasFocus
        
        # Get data
        checked = index.data(Qt.CheckStateRole) == Qt.Checked
        
        # Draw background (alternating colors handled by table)
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        
        # Draw Checkbox (centered)
        style = option.widget.style()
        checkbox_rect = style.subElementRect(QStyle.SE_ItemViewItemCheckIndicator, option, option.widget)
        
        # Center the checkbox in the cell
        checkbox_rect.moveCenter(option.rect.center())
        
        opt = QStyleOptionViewItem(option)
        opt.rect = checkbox_rect
        opt.state = opt.state & ~QStyle.State_HasFocus
        
        if checked:
            opt.state |= QStyle.State_On
        else:
            opt.state |= QStyle.State_Off
            
        style.drawPrimitive(QStyle.PE_IndicatorItemViewItemCheck, opt, painter, option.widget)

    def editorEvent(self, event, model, option, index):
        # Handle clicks to toggle check state
        if event.type() == event.MouseButtonRelease:
             # Calculate checkbox rect to see if click was inside
            style = option.widget.style()
            checkbox_rect = style.subElementRect(QStyle.SE_ItemViewItemCheckIndicator, option, option.widget)
            checkbox_rect.moveCenter(option.rect.center())
            
            if checkbox_rect.contains(event.pos()):
                current_state = index.data(Qt.CheckStateRole)
                new_state = Qt.Unchecked if current_state == Qt.Checked else Qt.Checked
                model.setData(index, new_state, Qt.CheckStateRole)
                return True
        return False

class InfoDelegate(QStyledItemDelegate):
    """Delegate for the Info column (Progress Bar + Text)."""
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        painter.save()
        
        # Draw background
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
            
        # Get data
        progress = index.data(Qt.UserRole + 1) # Progress 0-100
        status_text = index.data(Qt.DisplayRole) # Text like "准备处理" or "30%"
        
        rect = option.rect
        
        if isinstance(progress, int) and progress >= 0:
            # Draw Progress Bar
            # Define progress bar rect (e.g., bottom part of the cell or full background)
            # Let's match the design: Text centered, maybe progress bar behind or small?
            # The design shows "30%" text and a purple bar filling the cell partially?
            # Or just text "准备处理"
            
            # If progress is active (e.g. > 0 and < 100, or specific state), draw bar
            # For now, let's draw a simple progress bar at the bottom if progress > 0
            
            if progress > 0:
                bar_height = rect.height() 
                bar_width = int(rect.width() * (progress / 100.0))
                bar_rect = QRect(rect.x(), rect.y(), bar_width, bar_height)
                
                # Use a light purple color for progress background
                painter.fillRect(bar_rect, QColor(200, 180, 255, 100)) # Semi-transparent purple
                
        # Draw Text
        painter.setPen(option.palette.text().color())
        if option.state & QStyle.State_Selected:
             painter.setPen(option.palette.highlightedText().color())
             
        painter.drawText(rect, Qt.AlignCenter, status_text)
        
        painter.restore()

class FileListWidget(QTableWidget):
    """Custom TableWidget that supports file drag and drop with specific columns."""
    
    files_dropped = Signal(list)  # Signal emitted when files are dropped

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setAlternatingRowColors(True)
        self.setShowGrid(True) # Design shows grid lines
        self.verticalHeader().setVisible(False) # Hide row numbers
        
        # Setup Columns
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(["", "状态", "文件路径"])
        
        # Column Resizing
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed) # Status column fixed width
        header.setSectionResizeMode(1, QHeaderView.Fixed) # Info column fixed width
        header.setSectionResizeMode(2, QHeaderView.Stretch) # Path column stretches
        
        self.setColumnWidth(0, 30) # Small width for checkbox
        self.setColumnWidth(1, 100) # Width for status/progress
        
        # Set Delegates
        self.setItemDelegateForColumn(0, StatusDelegate(self))
        self.setItemDelegateForColumn(1, InfoDelegate(self))

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        files = []
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.exists():
                files.append(str(path))
        
        if files:
            self.files_dropped.emit(files)
            event.acceptProposedAction()
            
    def add_files(self, file_paths):
        """Add files to the list, avoiding duplicates."""
        # Get existing paths
        existing_paths = set()
        for row in range(self.rowCount()):
            item = self.item(row, 2)
            if item:
                existing_paths.add(item.text())
        
        for path in file_paths:
            if path not in existing_paths:
                row = self.rowCount()
                self.insertRow(row)
                
                # Column 0: Status (Checkbox)
                status_item = QTableWidgetItem()
                status_item.setData(Qt.CheckStateRole, Qt.Unchecked) # Default unchecked
                status_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable) # Not user checkable via standard way, handled by delegate? 
                # Actually, let's make it user checkable for selection
                status_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable)
                self.setItem(row, 0, status_item)
                
                # Column 1: Info (Progress/Status)
                info_item = QTableWidgetItem("准备处理")
                info_item.setData(Qt.UserRole + 1, 0) # Progress 0
                self.setItem(row, 1, info_item)
                
                # Column 2: File Path
                path_item = QTableWidgetItem(str(path))
                self.setItem(row, 2, path_item)

    def set_row_status(self, row, status_text, progress=None):
        """Update the status text and progress for a specific row."""
        if row < 0 or row >= self.rowCount():
            return
            
        item = self.item(row, 1)
        if item:
            item.setText(status_text)
            if progress is not None:
                item.setData(Qt.UserRole + 1, progress)
            # Force update
            self.viewport().update(self.visualItemRect(item))

    def set_row_checked(self, row, checked):
        """Set the checked state of a row."""
        if row < 0 or row >= self.rowCount():
            return
            
        item = self.item(row, 0)
        if item:
            state = Qt.Checked if checked else Qt.Unchecked
            item.setData(Qt.CheckStateRole, state)
