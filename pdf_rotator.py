#!/usr/bin/env python3
"""
PDF Rotator and Layout Tool
---------------------------
Reads a PDF, rotates each page 90 degrees left, and arranges 2 pages per A4 sheet
with gaps for optimal printing.
"""

import io
import os
import sys
from pathlib import Path
from typing import Optional

from pypdf import PdfWriter, PdfReader
from pypdf import Transformation
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

try:
    from PyQt6.QtWidgets import (
        QApplication, QWidget, QVBoxLayout, QPushButton, QLabel,
        QFileDialog, QMessageBox, QLineEdit, QProgressBar
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal
except ImportError:
    print("PyQt6 not found. Please install it: pip install PyQt6")
    sys.exit(1)

# Define A4 dimensions
A4_WIDTH, A4_HEIGHT = A4

class PDFProcessor(QThread):
    """Worker thread for PDF processing to keep GUI responsive."""
    progress_updated = pyqtSignal(str)
    processing_complete = pyqtSignal(int)  # Returns number of pages processed
    
    def __init__(self, input_file, output_file, gap_points: int, layout: str):
        super().__init__()
        self.input_file = input_file
        self.output_file = output_file
        self.gap_points = gap_points
        self.layout = layout
    
    def run(self):
        try:
            result = process_pdf(self.input_file, self.output_file, self.gap_points, self.progress_updated.emit, self.layout)
            self.processing_complete.emit(result)
        except Exception as e:
            self.progress_updated.emit(f"❌ Error: {str(e)}")
            self.processing_complete.emit(-1)

def rotate_page_left(page):
    """Rotate a page 90 degrees to the left (counter-clockwise)."""
    # Get original dimensions
    original_width = float(page.mediabox.width)
    original_height = float(page.mediabox.height)
    
    # Create transformation for 90-degree left rotation
    # For left rotation: rotate 90 degrees and translate to maintain position
    transformation = Transformation().rotate(90).translate(ty=original_width)
    
    return transformation

def create_blank_a4_page():
    """Create a blank A4 page."""
    return PdfWriter().add_blank_page(width=A4_WIDTH, height=A4_HEIGHT)

def arrange_pages_on_a4_rotated(page1, page2=None, gap=20, orientation: str = "side-by-side"):
    """Place one or two original pages rotated 90° left onto a single A4 page.

    If page2 is None, only page1 is placed centered in the left slot.
    """
    writer = PdfWriter()
    a4_page = writer.add_blank_page(width=A4_WIDTH, height=A4_HEIGHT)

    def place_rotated(src_page, slot_index: int):
        # side-by-side: slot_index 0 => left, 1 => right
        # top-bottom: slot_index 0 => top, 1 => bottom
        if orientation == "top-bottom":
            available_height = A4_HEIGHT - gap
            slot_height = available_height / 2
            slot_width = A4_WIDTH
        else:
            available_width = A4_WIDTH - gap
            slot_width = available_width / 2
            slot_height = A4_HEIGHT

        w = float(src_page.mediabox.width)
        h = float(src_page.mediabox.height)

        # After 90° CCW rotation, dimensions swap
        rot_w, rot_h = h, w

        scale = min(slot_width / rot_w if rot_w else 1, slot_height / rot_h if rot_h else 1)

        # Center within slot
        if orientation == "top-bottom":
            base_y = slot_height + gap if slot_index == 0 else 0
            content_w = rot_w * scale
            content_h = rot_h * scale
            tx = (A4_WIDTH - content_w) / 2
            ty = base_y + (slot_height - content_h) / 2
        else:
            base_x = 0 if slot_index == 0 else slot_width + gap
            content_w = rot_w * scale
            content_h = rot_h * scale
            tx = base_x + (slot_width - content_w) / 2
            ty = (A4_HEIGHT - content_h) / 2

        # Build transformation: rotate -> translate to positive -> scale -> place
        # Correct composition: rotate CCW 90°, shift into +X by original height,
        # scale to slot, then place at (tx, ty).
        transform = (
            Transformation()
            .rotate(90)
            .translate(h, 0)
            .scale(scale)
            .translate(tx, ty)
        )
        a4_page.merge_transformed_page(src_page, transform, expand=False)

    # Always place first page
    place_rotated(page1, 0)
    # Optionally place second page
    if page2 is not None:
        place_rotated(page2, 1)

    return a4_page

def process_pdf(input_file: Path, output_file: Path, gap_points: int = 20, status_callback=None, layout: str = "side-by-side"):
    """
    Process PDF: rotate pages 90° left and arrange 2 per A4 sheet.
    
    Args:
        input_file: Path to input PDF
        output_file: Path to output PDF
        status_callback: Function to call with status updates
    
    Returns:
        Number of pages processed, or -1 on error
    """
    try:
        if status_callback:
            status_callback("📖 Reading input PDF...")
        
        # Read the input PDF
        reader = PdfReader(str(input_file))
        total_pages = len(reader.pages)
        
        if total_pages == 0:
            if status_callback:
                status_callback("❌ Input PDF has no pages")
            return -1
        
        if status_callback:
            status_callback(f"📄 Found {total_pages} pages to process...")
        
        # Create output writer
        writer = PdfWriter()
        
        # Process pages in pairs
        for i in range(0, total_pages, 2):
            if status_callback:
                status_callback(f"🔄 Processing pages {i+1}-{min(i+2, total_pages)}...")
            
            # Get the first page
            page1 = reader.pages[i]
            
            if i + 1 < total_pages:
                # Get the second page
                page2 = reader.pages[i + 1]
                # Create A4 page with both rotated pages directly from originals
                a4_page = arrange_pages_on_a4_rotated(page1, page2, gap_points, layout)
                writer.add_page(a4_page)
            else:
                # Only one page left, create A4 with just that page
                a4_page = arrange_pages_on_a4_rotated(page1, None, gap_points, layout)
                writer.add_page(a4_page)
        
        # Save the output PDF
        if status_callback:
            status_callback("💾 Saving output PDF...")
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(str(output_file), "wb") as fp:
            writer.write(fp)
        
        output_pages = (total_pages + 1) // 2  # Calculate output pages (2 input pages per output page)
        if status_callback:
            status_callback(f"✅ Successfully processed {total_pages} pages into {output_pages} A4 sheets")
        
        return total_pages
        
    except Exception as e:
        if status_callback:
            status_callback(f"❌ Error processing PDF: {str(e)}")
        return -1

class PDFRotatorApp(QWidget):
    """GUI application for PDF rotation and layout."""
    
    def __init__(self):
        super().__init__()
        self.input_file = None
        self.output_file = None
        self.processor = None
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle('PDF Rotator & Layout Tool')
        self.setGeometry(300, 300, 500, 400)
        
        layout = QVBoxLayout()
        
        # Input file selection
        self.input_label = QLabel('Select Input PDF:')
        layout.addWidget(self.input_label)
        
        self.input_button = QPushButton('Browse Input PDF...')
        self.input_button.clicked.connect(self.select_input_file)
        layout.addWidget(self.input_button)
        
        self.selected_input_label = QLabel('No input file selected')
        self.selected_input_label.setStyleSheet("font-style: italic; color: grey;")
        layout.addWidget(self.selected_input_label)
        
        # Output file selection
        self.output_label = QLabel('Select Output PDF:')
        layout.addWidget(self.output_label)
        
        self.output_button = QPushButton('Browse Output Location...')
        self.output_button.clicked.connect(self.select_output_file)
        layout.addWidget(self.output_button)
        
        self.selected_output_label = QLabel('No output file selected')
        self.selected_output_label.setStyleSheet("font-style: italic; color: grey;")
        layout.addWidget(self.selected_output_label)
        
        # Gap setting
        self.gap_label = QLabel('Gap between pages (points):')
        layout.addWidget(self.gap_label)
        
        self.gap_input = QLineEdit('20')
        self.gap_input.setPlaceholderText('Enter gap size in points (default: 20)')
        layout.addWidget(self.gap_input)

        # Layout selection
        self.layout_label = QLabel('Layout:')
        layout.addWidget(self.layout_label)
        from PyQt6.QtWidgets import QComboBox
        self.layout_combo = QComboBox()
        self.layout_combo.addItems(["side-by-side", "top-bottom"])  # default side-by-side
        layout.addWidget(self.layout_combo)
        
        # Process button
        self.process_button = QPushButton('Process PDF')
        self.process_button.clicked.connect(self.run_processing)
        self.process_button.setEnabled(False)
        layout.addWidget(self.process_button)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel('Status: Ready to process PDF...')
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        layout.addStretch(1)
        self.setLayout(layout)
    
    def select_input_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Input PDF", "", "PDF Files (*.pdf)"
        )
        if file_path:
            self.input_file = Path(file_path)
            self.selected_input_label.setText(f"Input: {self.input_file.name}")
            self.selected_input_label.setStyleSheet("")
            self.suggest_output_file()
            self.update_process_button_state()
    
    def select_output_file(self):
        if not self.input_file:
            QMessageBox.warning(self, "No Input", "Please select an input file first.")
            return
        
        # Suggest output filename based on input
        suggested_name = f"{self.input_file.stem}-rotated-layout.pdf"
        suggested_path = self.input_file.parent / suggested_name
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Output PDF As...", str(suggested_path), "PDF Files (*.pdf)"
        )
        if file_path:
            self.output_file = Path(file_path)
            self.selected_output_label.setText(f"Output: {self.output_file.name}")
            self.selected_output_label.setStyleSheet("")
            self.update_process_button_state()
    
    def suggest_output_file(self):
        if self.input_file:
            suggested_name = f"{self.input_file.stem}-rotated-layout.pdf"
            suggested_path = self.input_file.parent / suggested_name
            self.output_file = suggested_path
            self.selected_output_label.setText(f"Output: {self.output_file.name}")
            self.selected_output_label.setStyleSheet("")
    
    def update_process_button_state(self):
        if self.input_file and self.output_file:
            self.process_button.setEnabled(True)
        else:
            self.process_button.setEnabled(False)
    
    def update_status(self, message):
        """Update status label and process events."""
        self.status_label.setText(f"Status: {message}")
        QApplication.processEvents()
    
    def run_processing(self):
        if not self.input_file or not self.output_file:
            QMessageBox.warning(self, "Missing Files", "Please select both input and output files.")
            return
        
        if not self.input_file.exists():
            QMessageBox.critical(self, "File Not Found", f"Input file not found: {self.input_file}")
            return
        
        if self.output_file.exists():
            reply = QMessageBox.question(
                self, 'File Exists',
                f"The file '{self.output_file.name}' already exists. Overwrite?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                self.update_status("Processing cancelled by user (file exists).")
                return
        
        # Disable buttons during processing
        self.input_button.setEnabled(False)
        self.output_button.setEnabled(False)
        self.process_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Parse gap value
        try:
            gap_points = int(self.gap_input.text().strip()) if self.gap_input.text().strip() else 20
        except ValueError:
            gap_points = 20
            self.update_status("Invalid gap value. Using default 20 points.")

        # Start processing in a separate thread
        chosen_layout = self.layout_combo.currentText()
        self.processor = PDFProcessor(self.input_file, self.output_file, gap_points, chosen_layout)
        self.processor.progress_updated.connect(self.update_status)
        self.processor.processing_complete.connect(self.processing_finished)
        self.processor.start()
    
    def processing_finished(self, result):
        """Handle completion of PDF processing."""
        self.progress_bar.setVisible(False)
        
        # Re-enable buttons
        self.input_button.setEnabled(True)
        self.output_button.setEnabled(True)
        self.update_process_button_state()
        
        if result > 0:
            QMessageBox.information(
                self, "Success", 
                f"Successfully processed {result} pages!\nOutput saved to: {self.output_file.name}"
            )
        elif result == -1:
            QMessageBox.critical(
                self, "Error", 
                f"An error occurred while processing the PDF. Please check the status for details."
            )

def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    window = PDFRotatorApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()