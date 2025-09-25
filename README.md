# PDF Tools Collection

This repository contains multiple Python tools for PDF manipulation:

## 1. PDF Title Merger GUI (`main.py`)

This Python script provides a graphical user interface (GUI) to merge multiple PDF files from a selected directory into a single output PDF. It automatically inserts a title page before each original PDF, displaying the filename (without the `.pdf` extension) as a centered, bold heading.

The PDFs are sorted using a natural sort order, ensuring that filenames like `file2.pdf` appear before `file10.pdf`.

## 2. PDF Rotator & Layout Tool (`pdf_rotator.py`)

A GUI tool that reads a PDF, rotates each page 90 degrees left, and arranges 2 pages per A4 sheet with gaps for optimal printing. Perfect for creating print-friendly layouts from portrait documents.

### Features:
- **90° Left Rotation:** Rotates each page counter-clockwise
- **2-Pages-Per-Sheet Layout:** Arranges rotated pages side-by-side on A4 sheets
- **Configurable Gaps:** Adjustable spacing between pages for clean printing
- **GUI Interface:** Easy-to-use graphical interface
- **Progress Tracking:** Real-time status updates during processing

## 3. PDF Rotator CLI (`pdf_rotator_cli.py`)

Command-line version of the PDF rotator tool for batch processing and automation.

## Features

*   **GUI Interface:** Uses PyQt6 for a simple user interface.
*   **Directory Selection:** Browse and select the input directory containing the PDFs.
*   **Output File Selection:** Specify the name and location for the merged output PDF.
*   **Automatic Title Pages:** Generates a title page for each PDF using its filename.
*   **Natural Sorting:** Merges files in a human-friendly order (e.g., `doc1.pdf`, `doc2.pdf`, `doc10.pdf`).
*   **In-Memory Processing:** Title pages are generated in memory without creating temporary files.
*   **Status Updates:** Provides feedback during the merging process.

## Installation

1.  **Prerequisites:** Ensure you have Python 3 installed on your system.
2.  **Clone or Download:** Get the script (`main.py`) and the requirements file (`requirements.txt`).
3.  **Install Dependencies:** Open a terminal or command prompt in the project directory and run:
    ```bash
    pip install -r requirements.txt
    ```
    This will install the necessary libraries:
    *   `pypdf`: For reading and writing PDF files.
    *   `reportlab`: For generating the title page PDFs.
    *   `PyQt6`: For the graphical user interface.

## How to Run

### PDF Title Merger GUI

1.  Navigate to the directory containing `main.py` in your terminal or command prompt.
2.  Execute the script:
    ```bash
    python main.py
    ```
3.  The **PDF Title Merger** window will appear.
4.  Click "**Browse Directory...**" to select the folder containing your PDF files.
5.  Click "**Browse Output Location...**" to choose where to save the combined PDF and give it a name (e.g., `merged_documents.pdf`).
6.  Once both paths are selected, the "**Merge PDFs**" button will become active.
7.  Click "**Merge PDFs**" to start the process.
8.  The status label will provide updates. Upon completion, a message box will indicate success or report any errors.

### PDF Rotator & Layout Tool (GUI)

1. Run the GUI version:
   ```bash
   python pdf_rotator.py
   ```
2. Click "**Browse Input PDF...**" to select your source PDF file
3. The output file will be automatically suggested (you can change it if needed)
4. Adjust the gap size between pages if desired (default: 20 points)
5. Click "**Process PDF**" to start the rotation and layout process
6. The tool will rotate each page 90° left and arrange 2 pages per A4 sheet

### PDF Rotator CLI

For command-line usage:

```bash
# Basic usage
python pdf_rotator_cli.py input.pdf output.pdf

# With custom gap size
python pdf_rotator_cli.py input.pdf output.pdf --gap 30

# Help
python pdf_rotator_cli.py --help
```

**Example:**
```bash
python pdf_rotator_cli.py document.pdf document-rotated.pdf --gap 25
```

## Tools Used

*   **Python 3**
*   **pypdf:** Library for PDF manipulation.
*   **ReportLab:** Library for PDF generation (used for title pages).
*   **PyQt6:** Library for creating the GUI.
 
