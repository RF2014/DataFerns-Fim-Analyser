"""
Test script to verify clickable links in PDF footer with full-width clickable area
"""
import os
import sys
import tempfile

from PyPDF2 import PdfWriter, PdfReader
from PyPDF2.generic import DictionaryObject, ArrayObject, NumberObject, NameObject, TextStringObject
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

print("Creating test PDF with full-width clickable link...")

# Create a simple PDF with text and footer
fig = plt.figure(figsize=(8.27, 11.69), dpi=100)

# Main content
ax = fig.add_axes([0.1, 0.2, 0.8, 0.7])
ax.text(0.5, 0.5, 'Test Content\n\nClick at the bottom to visit website', 
        ha='center', va='center', fontsize=14, color='black', transform=ax.transAxes)
ax.axis('off')

# Add footer text at bottom
fig.text(0.2, 0.03, 'Logo here | Nord Comptage Routier - Click me!', 
        fontsize=10, color='blue', fontweight='bold')

# Save to temporary file
temp_pdf = os.path.join(tempfile.gettempdir(), 'test_link_fullwidth.pdf')

with PdfPages(temp_pdf) as pdf:
    pdf.savefig(fig, bbox_inches=None, pad_inches=0)

plt.close(fig)

print(f"Initial PDF created: {temp_pdf}")

# Now add the link annotation with full-width clickable area
try:
    reader = PdfReader(temp_pdf)
    writer = PdfWriter()
    
    # Add all pages
    for page in reader.pages:
        writer.add_page(page)
    
    # Add link to first page with full-width bottom area
    page = writer.pages[0]
    
    pdf_width = 595.276
    pdf_height = 841.890
    
    # Full-width clickable area at bottom
    rect_x1 = 0
    rect_x2 = pdf_width
    rect_y1 = 0
    rect_y2 = 80  # About 9.5% from bottom
    
    print(f"Creating link annotation with coordinates:")
    print(f"  X: {rect_x1} to {rect_x2}")
    print(f"  Y: {rect_y1} to {rect_y2}")
    
    # Create URI action
    uri_action = DictionaryObject()
    uri_action[NameObject("/S")] = NameObject("/URI")
    uri_action[NameObject("/URI")] = TextStringObject("http://nordcomptageroutier.fr/")
    
    # Create link annotation
    link_annotation = DictionaryObject()
    link_annotation[NameObject("/Type")] = NameObject("/Annot")
    link_annotation[NameObject("/Subtype")] = NameObject("/Link")
    link_annotation[NameObject("/Rect")] = ArrayObject([
        NumberObject(rect_x1),
        NumberObject(rect_y1),
        NumberObject(rect_x2),
        NumberObject(rect_y2)
    ])
    link_annotation[NameObject("/Border")] = ArrayObject([NumberObject(0), NumberObject(0), NumberObject(0)])
    link_annotation[NameObject("/A")] = uri_action
    link_annotation[NameObject("/F")] = NumberObject(4)
    
    if "/Annots" not in page:
        page[NameObject("/Annots")] = ArrayObject()
    
    annots = page["/Annots"]
    if annots is None:
        annots = ArrayObject()
        page[NameObject("/Annots")] = annots
    
    annot_ref = writer._add_object(link_annotation)
    annots.append(annot_ref)
    
    print(f"Link annotation object added: {annot_ref}")
    
    # Save modified PDF
    with open(temp_pdf, 'wb') as f:
        writer.write(f)
    
    print(f"\nLink annotation added successfully!")
    print(f"Test PDF with clickable link created at: {temp_pdf}")
    print(f"PDF size: {os.path.getsize(temp_pdf)} bytes")
    print("\nTo test: Open the PDF in your PDF reader and click anywhere at the bottom of the page.")
    print("It should open: http://nordcomptageroutier.fr/")
    
except Exception as e:
    print(f"ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
