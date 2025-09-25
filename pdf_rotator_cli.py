#!/usr/bin/env python3
"""
PDF Rotator and Layout Tool (Command Line Version)
-------------------------------------------------
Reads a PDF, rotates each page 90 degrees left, and arranges 2 pages per A4 sheet
with gaps for optimal printing.

Usage:
    python pdf_rotator_cli.py input.pdf output.pdf [gap_size]
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

from pypdf import PdfWriter, PdfReader
from pypdf import Transformation
from reportlab.lib.pagesizes import A4

# Define A4 dimensions
A4_WIDTH, A4_HEIGHT = A4

def rotate_page_left(page):
    """Rotate a page 90 degrees to the left (counter-clockwise)."""
    # Get original dimensions
    original_width = float(page.mediabox.width)
    original_height = float(page.mediabox.height)
    
    # Create transformation for 90-degree left rotation
    # For left rotation: rotate 90 degrees and translate to maintain position
    transformation = Transformation().rotate(90).translate(ty=original_width)
    
    return transformation

def arrange_pages_on_a4_rotated(page1, page2=None, gap=20, orientation: str = "side-by-side", size_factor: float = 1.0):
    """Place one or two original pages rotated 90° left onto a single A4 page."""
    writer = PdfWriter()
    a4_page = writer.add_blank_page(width=A4_WIDTH, height=A4_HEIGHT)

    def place_rotated(src_page, slot_index: int):
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
        rot_w, rot_h = h, w
        max_scale = min(slot_width / rot_w if rot_w else 1, slot_height / rot_h if rot_h else 1)
        scale = max(0.1, min(1.0, size_factor)) * max_scale

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

        transform = (
            Transformation()
            .rotate(90)
            .translate(h, 0)
            .scale(scale)
            .translate(tx, ty)
        )
        a4_page.merge_transformed_page(src_page, transform, expand=False)

    place_rotated(page1, 0)
    if page2 is not None:
        place_rotated(page2, 1)

    return a4_page

def arrange_pages_on_a4_rotated_three(pages, gap=20, size_factor: float = 1.0):
    """Place up to three original pages rotated 90° left onto a single A4 page (stacked top-bottom)."""
    writer = PdfWriter()
    a4_page = writer.add_blank_page(width=A4_WIDTH, height=A4_HEIGHT)

    rows, cols = 3, 1
    available_width = A4_WIDTH
    available_height = A4_HEIGHT - (rows - 1) * gap
    slot_width = available_width / cols
    slot_height = available_height / rows

    def place_at(src_page, row_index: int):
        base_x = 0
        base_y = A4_HEIGHT - ((row_index + 1) * slot_height) - (row_index * gap)

        w = float(src_page.mediabox.width)
        h = float(src_page.mediabox.height)
        rot_w, rot_h = h, w
        max_scale = min(slot_width / rot_w if rot_w else 1, slot_height / rot_h if rot_h else 1)
        scale = max(0.1, min(1.0, size_factor)) * max_scale
        content_w = rot_w * scale
        content_h = rot_h * scale
        tx = base_x + (slot_width - content_w) / 2
        ty = base_y + (slot_height - content_h) / 2

        transform = (
            Transformation()
            .rotate(90)
            .translate(h, 0)
            .scale(scale)
            .translate(tx, ty)
        )
        a4_page.merge_transformed_page(src_page, transform, expand=False)

    for idx, p in enumerate(pages[:3]):
        place_at(p, idx)

    return a4_page

def process_pdf(input_file: Path, output_file: Path, gap_size: int = 20, layout: str = "side-by-side", size_factor: float = 1.0):
    """
    Process PDF: rotate pages 90° left and arrange 2 per A4 sheet.
    
    Args:
        input_file: Path to input PDF
        output_file: Path to output PDF
        gap_size: Gap between pages in points
    
    Returns:
        Number of pages processed, or -1 on error
    """
    try:
        print(f"📖 Reading input PDF: {input_file}")
        
        # Read the input PDF
        reader = PdfReader(str(input_file))
        total_pages = len(reader.pages)
        
        if total_pages == 0:
            print("❌ Input PDF has no pages")
            return -1
        
        print(f"📄 Found {total_pages} pages to process...")
        
        # Create output writer
        writer = PdfWriter()
        
    # Process pages according to layout (2-up or 3-up)
    step = 3 if layout == "top-bottom-3" else 2
    for i in range(0, total_pages, step):
            print(f"🔄 Processing pages {i+1}-{min(i+2, total_pages)}...")
            
            # Get the first page
            page1 = reader.pages[i]
            
        # We'll place the original pages with rotation during layout
        if layout == "top-bottom-3":
            pages = [page1]
            if i + 1 < total_pages:
                pages.append(reader.pages[i + 1])
            if i + 2 < total_pages:
                pages.append(reader.pages[i + 2])
            a4_page = arrange_pages_on_a4_rotated_three(pages, gap_size, size_factor)  # function defined below
            writer.add_page(a4_page)
        else:
            if i + 1 < total_pages:
                # Get the second page
                page2 = reader.pages[i + 1]
                # Create A4 page with both rotated pages directly from originals
                a4_page = arrange_pages_on_a4_rotated(page1, page2, gap_size, layout, size_factor)
                writer.add_page(a4_page)
            else:
                # Only one page left, create A4 with just that page
                a4_page = arrange_pages_on_a4_rotated(page1, None, gap_size, layout, size_factor)
                writer.add_page(a4_page)
        
        # Save the output PDF
        print("💾 Saving output PDF...")
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(str(output_file), "wb") as fp:
            writer.write(fp)
        
        output_pages = (total_pages + 1) // 2  # Calculate output pages (2 input pages per output page)
        print(f"✅ Successfully processed {total_pages} pages into {output_pages} A4 sheets")
        
        return total_pages
        
    except Exception as e:
        print(f"❌ Error processing PDF: {str(e)}")
        return -1

def main():
    """Main entry point for command line interface."""
    parser = argparse.ArgumentParser(
        description="Rotate PDF pages 90° left and arrange 2 pages per A4 sheet with gaps for printing."
    )
    parser.add_argument("input_file", help="Input PDF file path")
    parser.add_argument("output_file", help="Output PDF file path")
    parser.add_argument("--gap", type=int, default=20, help="Gap between pages in points (default: 20)")
    parser.add_argument("--layout", choices=["side-by-side", "top-bottom", "top-bottom-3"], default="side-by-side", help="Layout orientation: side-by-side, top-bottom, or top-bottom-3 (default: side-by-side)")
    parser.add_argument("--size", type=float, default=1.0, help="Size factor 0.1-1.0 applied on top of fit-to-slot (default: 1.0)")
    
    args = parser.parse_args()
    
    input_path = Path(args.input_file)
    output_path = Path(args.output_file)
    
    # Validate input file
    if not input_path.exists():
        print(f"❌ Error: Input file not found: {input_path}")
        sys.exit(1)
    
    if not input_path.suffix.lower() == '.pdf':
        print(f"❌ Error: Input file must be a PDF: {input_path}")
        sys.exit(1)
    
    # Check if output file already exists
    if output_path.exists():
        response = input(f"Output file '{output_path}' already exists. Overwrite? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("Operation cancelled.")
            sys.exit(0)
    
    # Process the PDF
    result = process_pdf(input_path, output_path, args.gap, args.layout, args.size)
    
    if result > 0:
        print(f"🎉 Processing completed successfully!")
        print(f"📁 Output saved to: {output_path}")
    else:
        print("❌ Processing failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()