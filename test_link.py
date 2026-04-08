"""
Test script to verify clickable links in PDF footer
"""
import os
import sys
import tempfile

# Add paths
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'dcr_python/src'))

# Test PyPDF2 link creation
from PyPDF2 import PdfWriter, PdfReader
from PyPDF2.generic import DictionaryObject, ArrayObject, NumberObject, NameObject, TextStringObject
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

print("Creating test PDF with clickable link...")

# Create a simple PDF with text
fig = plt.figure(figsize=(8.27, 11.69))
ax = fig.add_axes([0.1, 0.1, 0.8, 0.8])
ax.text(0.5, 0.5, 'Nord Comptage Routier\n\nClick the text above to visit the website', 
        ha='center', va='center', fontsize=16, color='blue', transform=ax.transAxes)
ax.axis('off')

# Save to temporary file
temp_pdf = os.path.join(tempfile.gettempdir(), 'test_link.pdf')

with PdfPages(temp_pdf) as pdf:
    pdf.savefig(fig, bbox_inches=None, pad_inches=0)

plt.close(fig)

print(f"Initial PDF created: {temp_pdf}")

# Now add the link annotation
try:
    reader = PdfReader(temp_pdf)
    writer = PdfWriter()
    
    # Add all pages
    for page in reader.pages:
        writer.add_page(page)
    
    # Add link to first page
    page = writer.pages[0]
    
    # Create link annotation
    pdf_width = 595.276
    pdf_height = 841.890
    
    rect_x1 = pdf_width * 0.10
    rect_x2 = pdf_width * 0.90
    rect_y1 = pdf_height * 0.40  # Middle of page for test
    rect_y2 = pdf_height * 0.60
    
    link_annotation = DictionaryObject()
    link_annotation[NameObject("/Type")] = NameObject("/Annot")
    link_annotation[NameObject("/Subtype")] = NameObject("/Link")
    link_annotation[NameObject("/Rect")] = ArrayObject([
        NumberObject(float(rect_x1)),
        NumberObject(float(rect_y1)),
        NumberObject(float(rect_x2)),
        NumberObject(float(rect_y2))
    ])
    link_annotation[NameObject("/Border")] = ArrayObject([NumberObject(0), NumberObject(0), NumberObject(0)])
    
    action = DictionaryObject()
    action[NameObject("/S")] = NameObject("/URI")
    action[NameObject("/URI")] = TextStringObject("http://nordcomptageroutier.fr/")
    link_annotation[NameObject("/A")] = action
    
    if "/Annots" not in page:
        page[NameObject("/Annots")] = ArrayObject()
    
    page["/Annots"].append(writer._add_object(link_annotation))
    
    # Save modified PDF
    with open(temp_pdf, 'wb') as f:
        writer.write(f)
    
    print(f"Link annotation added successfully!")
    print(f"Test PDF with clickable link created at: {temp_pdf}")
    print(f"PDF size: {os.path.getsize(temp_pdf)} bytes")
    print("\nTo test: Open the PDF in your PDF reader and click on the blue text.")
    
except Exception as e:
    print(f"ERROR adding link: {str(e)}")
    import traceback
    traceback.print_exc()
