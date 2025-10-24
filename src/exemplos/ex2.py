from pathlib import Path

import pdfplumber

pdf_path = Path(__file__).parent.parent.parent / "pdfs" / "exemplo.pdf"


text = ""
with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages[1:3]:
        text += page.extract_text()


print(text)
