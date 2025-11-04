from pathlib import Path
import fitz  # PyMuPDF

pdf_path = Path(__file__).parent.parent.parent / "pdfs" / "exemplo.pdf"

doc = fitz.open(pdf_path)

def block_to_text(block):
    parts = []
    for line in block.get("lines", []):
        for span in line.get("spans", []):
            parts.append(span.get("text") or "")
    return "".join(parts)

for page_index in range(1, 2):
    page = doc[page_index]
    blocks = page.get_text("rawdict").get("blocks", [])

    out_lines = [f"\n\n --- Página {page_index + 1} --- \n"]
    for b in blocks:
        btype = b.get("type")
        if btype == 0:  # texto
            txt = block_to_text(b).strip()
            if txt:
                out_lines.append(txt)
        # elif btype == 1:  # imagem
        #     bbox = b.get("bbox", [0, 0, 0, 0])
        #     xref = b.get("image")
        #     out_lines.append(
        #         f"[IMAGEM xref={xref} bbox=({bbox[0]:.1f},{bbox[1]:.1f},{bbox[2]:.1f},{bbox[3]:.1f})]"
        #     )

    print("\n".join(out_lines))