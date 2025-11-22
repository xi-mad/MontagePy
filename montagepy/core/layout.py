"""Grid layout logic for irregular grids."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class GridCell:
    """A single cell in the grid."""
    
    row: int
    col: int
    row_span: int = 1
    col_span: int = 1
    index: int = -1  # Optional: index of the image to place here (if not sequential)


class GridLayout:
    """Defines the layout of the montage grid."""

    def __init__(self, rows: int, cols: int):
        self.rows = rows
        self.cols = cols
        self.cells: List[GridCell] = []

    @property
    def count(self) -> int:
        """Get the number of cells in the layout."""
        return len(self.cells)

    def add_cell(self, row: int, col: int, row_span: int = 1, col_span: int = 1, index: int = -1) -> None:
        """Add a cell to the layout.
        
        Args:
            row: Row index (0-based)
            col: Column index (0-based)
            row_span: Number of rows this cell spans
            col_span: Number of columns this cell spans
            index: Optional explicit index for the image
        """
        # Basic validation
        if row < 0 or row >= self.rows:
            raise ValueError(f"Row {row} is out of bounds (0-{self.rows-1})")
        if col < 0 or col >= self.cols:
            raise ValueError(f"Column {col} is out of bounds (0-{self.cols-1})")
        if row + row_span > self.rows:
            raise ValueError(f"Cell extends beyond bottom edge (row {row} + span {row_span} > {self.rows})")
        if col + col_span > self.cols:
            raise ValueError(f"Cell extends beyond right edge (col {col} + span {col_span} > {self.cols})")
            
        self.cells.append(GridCell(row, col, row_span, col_span, index))

    def get_cell(self, index: int) -> Optional[GridCell]:
        """Get cell for a specific image index.
        
        If cells have explicit indices, use those.
        Otherwise, return the cell at the given list index.
        """
        # First check for explicit index match
        for cell in self.cells:
            if cell.index == index:
                return cell
                
        # Fallback to sequential index if within bounds
        if 0 <= index < len(self.cells):
            # If the cell at this position has no explicit index (or -1), use it
            if self.cells[index].index == -1:
                return self.cells[index]
                
        return None
