from pathlib import Path

import pypdf
from rich import print

pdf_path = Path(__file__).parent.parent.parent / "pdfs" / "exemplo.pdf"

text = ""

with pdf_path.open("rb") as pdf:
    reader = pypdf.PdfReader(pdf)
    for page_index in range(1, 3):
        page_no = page_index + 1
        page = reader.pages[page_index]

        page_text = page.extract_text() or ""

        # Colete imagens da página (sem se preocupar com a ordem no fluxo)
        markers = []
        for i, img in enumerate(page.images, start=1):
            name = getattr(img, "name", f"img_{i}")
            w = getattr(img, "width", "?")
            h = getattr(img, "height", "?")

            # Se quiser apenas JPG/JPEG, descomente:
            # if not str(name).lower().endswith((".jpg", ".jpeg")):
            #     continue

            markers.append(f"[IMAGEM {i} na página {page_no}: name={name}, {w}x{h}]")
            print(f"Página {page_no} → imagem {i}: {name} ({w}x{h})")

        text += f"\n\n --- Página {page_no} --- \n\n{page_text}"
        if markers:
            text += "\n" + "\n".join(markers)

print(text)