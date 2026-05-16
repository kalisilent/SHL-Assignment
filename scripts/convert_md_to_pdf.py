#!/usr/bin/env python3
"""Convert Markdown to PDF using reportlab."""

import os
import sys
from pathlib import Path
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY


def markdown_to_pdf(md_file, output_file, page_size=letter):
    """Convert markdown file to PDF."""
    
    # Read markdown content
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create PDF
    doc = SimpleDocTemplate(output_file, pagesize=page_size,
                           rightMargin=0.75*inch,
                           leftMargin=0.75*inch,
                           topMargin=0.75*inch,
                           bottomMargin=0.75*inch)
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor='#1f4788',
        spaceAfter=12,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor='#1f4788',
        spaceAfter=6,
        spaceBefore=6
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        spaceAfter=6,
        alignment=TA_JUSTIFY
    )
    
    # Parse markdown and build story
    story = []
    lines = content.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines
        if not line:
            story.append(Spacer(1, 0.1*inch))
            i += 1
            continue
        
        # Handle headings
        if line.startswith('# '):
            text = line[2:].strip()
            story.append(Paragraph(text, title_style))
            story.append(Spacer(1, 0.2*inch))
        elif line.startswith('## '):
            text = line[3:].strip()
            story.append(Paragraph(text, heading_style))
        elif line.startswith('### '):
            text = line[4:].strip()
            story.append(Paragraph(text, heading_style))
        elif line.startswith('- '):
            # Bullet point
            text = '• ' + line[2:].strip()
            story.append(Paragraph(text, body_style))
        else:
            # Regular text
            if line:
                story.append(Paragraph(line, body_style))
        
        i += 1
    
    # Build PDF
    try:
        doc.build(story)
        print(f"✓ PDF created: {output_file}")
        return True
    except Exception as e:
        print(f"✗ Error creating PDF: {e}", file=sys.stderr)
        return False


if __name__ == '__main__':
    # Get repo root
    repo_root = Path(__file__).parent.parent
    md_file = repo_root / 'Approach_Document.md'
    pdf_file = repo_root / 'Approach_Document.pdf'
    
    if not md_file.exists():
        print(f"✗ File not found: {md_file}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Converting {md_file.name} to PDF...")
    if markdown_to_pdf(str(md_file), str(pdf_file)):
        sys.exit(0)
    else:
        sys.exit(1)
