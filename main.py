#!/usr/bin/env python3
"""
merge_with_filename_titles.py (GUI Version)
-------------------------------------------
Select a directory containing PDFs, choose an output file, and merge all PDFs
lexicographically. Each original PDF is preceded by an automatically generated
title page bearing its own filename.
"""

import io
import os
import re
import sys
from pathlib import Path

from pypdf import PdfWriter, PdfReader
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

try:
    from PyQt6.QtWidgets import (
        QApplication, QWidget, QVBoxLayout, QPushButton, QLabel,
        QFileDialog, QMessageBox, QLineEdit
    )
    from PyQt6.QtCore import Qt
except ImportError:
    print("PyQt6 not found. Please install it: pip install PyQt6")
    sys.exit(1)

# ----------------- helpers -------------------------------------------------- #

def natural_key(name: str):
    """Sort so that 'file10.pdf' is after 'file2.pdf'."""
    return [int(s) if s.isdigit() else s.lower()
            for s in re.split(r"(\d+)", name)]

def iter_pdfs(folder: Path):
    """Yield PDFs in natural‑sort order."""
    pdf_files = list(folder.glob("*.pdf"))
    pdf_files.sort(key=lambda p: natural_key(p.name))
    for p in pdf_files:
        yield p

def make_title_page(text: str) -> PdfReader | None:
    """
    Build a 1‑page PDF in memory with the given `text` centered,
    return it as a PdfReader object ready for merging.
    Returns None if text is empty or generation fails.
    """
    if not text:
        return None
    buf = io.BytesIO()
    try:
        c = canvas.Canvas(buf, pagesize=LETTER)
        width, height = LETTER
        # Use a larger font size for a heading style
        font_size = 32 # Increased back to 32 for emphasis
        c.setFont("Helvetica-Bold", font_size)
        # Simple wrap attempt if name is too long
        max_width = width * 0.8
        text_width = c.stringWidth(text, "Helvetica-Bold", font_size)

        if text_width > max_width:
             # Very basic split, might break words awkwardly
            parts = text.split()
            lines = []
            current_line = ""
            for part in parts:
                test_line = f"{current_line} {part}".strip()
                if c.stringWidth(test_line, "Helvetica-Bold", font_size) <= max_width:
                    current_line = test_line
                else:
                    if current_line: # Avoid adding empty lines if a single part is too long
                        lines.append(current_line)
                    current_line = part
                    # Handle case where a single part itself is too long (rare for filenames)
                    if c.stringWidth(current_line, "Helvetica-Bold", font_size) > max_width:
                         # Truncate or handle differently? For now, just add it.
                         lines.append(current_line)
                         current_line = "" # Reset line after adding oversized part

            if current_line:
                lines.append(current_line)

            line_height = font_size * 1.2 # Basic line spacing
            start_y = height / 2 + (len(lines) -1) * line_height / 2
            for i, line in enumerate(lines):
                 c.drawCentredString(width / 2, start_y - i * line_height, line)
        else:
            c.drawCentredString(width / 2, height / 2, text)

        c.save()
        buf.seek(0)
        return PdfReader(buf)
    except Exception as e:
        print(f"Error creating title page for '{text}': {e}")
        return None
    finally:
        # Do not close buf here; PdfReader needs it open.
        # buf.close()
        pass # Keep the finally block for structure if needed, or remove.


def merge(dir_path: Path, out_file: Path, status_callback=None):
    """Merges PDFs with title pages, using callback for status updates."""
    writer = PdfWriter()
    pdf_paths = list(iter_pdfs(dir_path)) # Get list upfront for count
    count = len(pdf_paths)
    merged_count = 0

    if not count:
        if status_callback:
            status_callback(f"No PDF files found in {dir_path}")
        return 0 # Indicate no files were merged

    if status_callback:
        status_callback(f"Starting merge of {count} PDF(s)...")

    for i, pdf_path in enumerate(pdf_paths):
        title_text = pdf_path.stem # filename without .pdf
        if status_callback:
            status_callback(f"Processing ({i+1}/{count}): {pdf_path.name}")

        title_pdf = make_title_page(title_text)
        if title_pdf:
            try:
                writer.append(fileobj=title_pdf)
            except Exception as e:
                 print(f"Error appending title page for {title_text}: {e}")
                 if status_callback:
                     status_callback(f"❌ Error adding title for {pdf_path.name}")
                 continue # Skip this file? Or just the title? Let's skip title.
                 # Alternative: Raise error? Depends on desired behavior.

        try:
            writer.append(str(pdf_path))
            merged_count += 1
        except Exception as e:
            print(f"Error appending PDF {pdf_path.name}: {e}")
            # Potentially corrupted PDF, could be PyPDF issue too
            if hasattr(e, 'strict') and e.strict: # Check if it's a PdfReadError related to strictness
                 print(f"Trying to append {pdf_path.name} in non-strict mode.")
                 try:
                     # Need to open reader explicitly for non-strict append
                     reader = PdfReader(str(pdf_path), strict=False)
                     writer.append(fileobj=reader)
                     merged_count += 1
                 except Exception as e_nonstrict:
                      print(f"Error appending {pdf_path.name} even in non-strict mode: {e_nonstrict}")
                      if status_callback:
                        status_callback(f"❌ Error adding {pdf_path.name}")
            else:
                 if status_callback:
                     status_callback(f"❌ Error adding {pdf_path.name}")


    if merged_count > 0:
        try:
            out_file.parent.mkdir(parents=True, exist_ok=True)
            with open(str(out_file), "wb") as fp:
                writer.write(fp)
            if status_callback:
                status_callback(f"✅ Merged {merged_count} PDF(s) into {out_file.name}")
        except Exception as e:
            print(f"Error writing final PDF {out_file}: {e}")
            if status_callback:
                status_callback(f"❌ Error saving merged file: {e}")
            merged_count = -1 # Indicate save error
        # No writer.close() needed when using write with a file path/context manager
    elif count > 0 : # If we had files but merged none (due to errors)
         if status_callback:
             status_callback(f"⚠️ No PDFs were successfully merged due to errors.")
         merged_count = -2 # Indicate merge errors
    # else: # No files found case handled earlier

    # Explicitly close the writer object if an error occurred before writing
    # or if no files were merged successfully. This prevents potential resource leaks.
    if merged_count <= 0:
        try:
            writer.close()
        except Exception as e_close:
            print(f"Error closing PdfWriter: {e_close}")

    return merged_count


# ----------------- GUI ------------------------------------------------------ #

class PdfMergerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.input_dir = None
        self.output_file = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('PDF Title Merger')
        self.setGeometry(300, 300, 450, 250) # x, y, width, height

        layout = QVBoxLayout()

        self.dir_label = QLabel('Select Input Directory:')
        layout.addWidget(self.dir_label)

        self.dir_button = QPushButton('Browse Directory...')
        self.dir_button.clicked.connect(self.select_directory)
        layout.addWidget(self.dir_button)

        self.selected_dir_label = QLabel('No directory selected')
        self.selected_dir_label.setStyleSheet("font-style: italic; color: grey;")
        layout.addWidget(self.selected_dir_label)

        self.out_label = QLabel('Select Output File:')
        layout.addWidget(self.out_label)

        self.out_button = QPushButton('Browse Output Location...')
        self.out_button.clicked.connect(self.select_output)
        layout.addWidget(self.out_button)

        self.selected_out_label = QLabel('No output file selected')
        self.selected_out_label.setStyleSheet("font-style: italic; color: grey;")
        layout.addWidget(self.selected_out_label)

        self.merge_button = QPushButton('Merge PDFs')
        self.merge_button.clicked.connect(self.run_merge)
        self.merge_button.setEnabled(False) # Disabled until paths are set
        layout.addWidget(self.merge_button)

        self.status_label = QLabel('Status: Waiting for input...')
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        layout.addStretch(1) # Add space at the bottom

        self.setLayout(layout)

    def select_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select PDF Directory")
        if dir_path:
            self.input_dir = Path(dir_path)
            self.selected_dir_label.setText(f"Input: {self.input_dir}")
            self.selected_dir_label.setStyleSheet("") # Reset style
            self.update_merge_button_state()
            # Suggest default output in the parent of the selected dir
            suggested_out = self.input_dir.parent / f"{self.input_dir.name}-merged.pdf"
            self.output_file = suggested_out # Pre-fill suggestion
            self.selected_out_label.setText(f"Output: {self.output_file}")
            self.selected_out_label.setStyleSheet("") # Reset style


    def select_output(self):
        # Default to input dir's parent if input_dir is known, otherwise CWD
        start_dir = str(self.input_dir.parent) if self.input_dir else os.getcwd()
        default_name = f"{self.input_dir.name}-merged.pdf" if self.input_dir else "combined.pdf"
        suggested_path = os.path.join(start_dir, default_name)

        file_path, _ = QFileDialog.getSaveFileName(self, "Save Merged PDF As...", suggested_path, "PDF Files (*.pdf)")
        if file_path:
            self.output_file = Path(file_path)
            self.selected_out_label.setText(f"Output: {self.output_file}")
            self.selected_out_label.setStyleSheet("") # Reset style
            self.update_merge_button_state()

    def update_merge_button_state(self):
        if self.input_dir and self.output_file:
            self.merge_button.setEnabled(True)
        else:
            self.merge_button.setEnabled(False)

    def update_status(self, message):
        """Callback function to update the status label."""
        self.status_label.setText(f"Status: {message}")
        QApplication.processEvents() # Allow GUI to update

    def run_merge(self):
        if not self.input_dir or not self.output_file:
            QMessageBox.warning(self, "Missing Input", "Please select both an input directory and an output file.")
            return

        if self.output_file.exists():
             reply = QMessageBox.question(self, 'File Exists',
                                         f"The file '{self.output_file.name}' already exists. Overwrite?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
             if reply == QMessageBox.StandardButton.No:
                 self.update_status("Merge cancelled by user (file exists).")
                 return

        # Disable buttons during merge
        self.dir_button.setEnabled(False)
        self.out_button.setEnabled(False)
        self.merge_button.setEnabled(False)

        try:
            result = merge(self.input_dir, self.output_file, self.update_status)
            # Final status update already handled by merge via callback
            if result > 0:
                 QMessageBox.information(self, "Success", f"Successfully merged {result} PDF(s) into {self.output_file}")
            elif result == 0:
                 QMessageBox.warning(self, "No Files", f"No PDF files were found in the selected directory: {self.input_dir}")
            elif result == -1:
                 QMessageBox.critical(self, "Error", f"An error occurred while saving the merged PDF to: {self.output_file}")
            elif result == -2:
                  QMessageBox.warning(self, "Merge Issues", f"Some PDFs could not be merged. Please check the console output for details.")
            else: # Should not happen, but cover base case
                  QMessageBox.warning(self, "Warning", f"Merge operation completed with an unexpected result code: {result}")

        except Exception as e:
            self.update_status(f"❌ An unexpected error occurred: {e}")
            QMessageBox.critical(self, "Error", f"An unexpected error occurred during the merge process: {e}")
            print(f"Critical error during merge: {e}") # Also print to console
        finally:
            # Re-enable buttons
             self.dir_button.setEnabled(True)
             self.out_button.setEnabled(True)
             self.update_merge_button_state() # Re-enable merge button if paths still valid


# ----------------- Entry Point ---------------------------------------------- #

def main_gui():
    app = QApplication(sys.argv)
    ex = PdfMergerApp()
    ex.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main_gui()

