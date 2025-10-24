from pathlib import Path

import pypdf
from rich import print

pdf_path = Path(__file__).parent.parent.parent / "pdfs" / "exemplo.pdf"

# reader = pypdf.PdfReader(pdf_path)
# number_of_pages = len(reader.pages)
# page = reader.pages[1]
# text = page.extract_text()
# print(text)

text = ""
pages_text = {}

with pdf_path.open("rb") as pdf:
    reader = pypdf.PdfReader(pdf)
    for page in reader.pages[1:3]:
        page_no = reader.pages.index(page) + 1

        page_text = page.extract_text()

        pages_text[page_no] = page_text

        text += f"\n\n --- Página {page_no} --- \n\n{page_text}"


print(text)
