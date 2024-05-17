import fitz  # PyMuPDF

# Open the PDF file
filename = 'data/fwil_dhi_me_results_tt.pdf'
doc = fitz.open(filename)

# Extract text from the first few pages to inspect the format
for page_num in range(min(3, len(doc))):  # Check up to the first 3 pages
    page = doc[page_num]
    text = page.get_text("text")
    lines = text.split('\n')
    print(f"---- Page {page_num + 1} ----")
    for line in lines[:30]:  # Print the first 30 lines of each page
        print(line)

# Close the document
doc.close()
