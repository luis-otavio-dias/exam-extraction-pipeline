from pathlib import Path

from pypdf import PdfReader

pdf_path = Path(__file__).parent.parent.parent / "pdfs" / "exemplo.pdf"
MEDIA_DIR = Path("media_images")
MEDIA_DIR.mkdir(parents=True, exist_ok=True)



with pdf_path.open("rb") as pdf:
    reader = PdfReader(pdf)
    for page_index in range(1, 3):
        page = reader.pages[page_index]
        for image_file_object in page.images:
            if image_file_object.name.find(".jpg") != -1:
                img_name = f"page_{page_index + 1}_{image_file_object.name}"

                out_path = MEDIA_DIR / img_name
                with out_path.open("wb") as fp:
                    fp.write(image_file_object.data)

