"""
Debug script to check actual footer coordinates in matplotlib-generated PDF
"""
import os
import sys
import tempfile
from pathlib import Path

from PyPDF2 import PdfReader
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

print("Creating test PDF with text at specific coordinates...")

# Create a simple PDF with text at known positions
fig = plt.figure(figsize=(8.27, 11.69), dpi=100)  # A4 size

# Main content
ax = fig.add_axes([0.1, 0.2, 0.8, 0.7])
ax.text(0.5, 0.5, 'Test Content', ha='center', va='center', fontsize=14)
ax.axis('off')

# Add text at EXACT footer location where we'll put the link
# Normalized coordinates: x=0.2, y=0.025 (which should be ~131 points X, ~21 points Y)
fig.text(0.2, 0.025, 'Nord Comptage Routier', fontsize=10, color='blue', fontweight='bold')

# Save to temporary file
temp_pdf = os.path.join(tempfile.gettempdir(), 'test_footer_coords.pdf')

with PdfPages(temp_pdf) as pdf:
    pdf.savefig(fig, bbox_inches=None, pad_inches=0)

plt.close(fig)

print(f"Test PDF created: {temp_pdf}")

# Read the PDF to check actual content stream
try:
    reader = PdfReader(temp_pdf)
    page = reader.pages[0]
    
    print(f"\nPage dimensions:")
    print(f"  /MediaBox: {page.mediabox}")
    
    # Try to extract text to see coordinates
    if "/Contents" in page:
        print(f"\nPage has content stream")
        
        # Get the content stream
        content = page["/Contents"]
        print(f"  Content stream object: {content}")
    
    # Check for annotations (links)
    if "/Annots" in page:
        print(f"\nPage has {len(page['/Annots'])} annotations")
        for annot in page["/Annots"]:
            print(f"  Annotation: {annot}")
    else:
        print(f"\nPage has NO annotations")
    
    print(f"\nPDF file size: {os.path.getsize(temp_pdf)} bytes")
    
except Exception as e:
    print(f"ERROR reading PDF: {str(e)}")
    import traceback
    traceback.print_exc()

print("\nNOTE: The text 'Nord Comptage Routier' is placed at normalized coordinates (0.2, 0.025)")
print("In PDF points (595.276 x 841.890):")
print(f"  X = 0.2 * 595.276 = {0.2 * 595.276:.1f} points")
print(f"  Y = 0.025 * 841.890 = {0.025 * 841.890:.1f} points")
print("\nThis means the footer text is only ~21 points from the bottom!")
print("The link annotation with rect_y2=80 SHOULD cover this area.")
