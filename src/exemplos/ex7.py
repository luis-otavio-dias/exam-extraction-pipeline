from pathlib import Path

from pypdf import PdfReader

pdf_path = Path(__file__).parent.parent.parent / "pdfs" / "exemplo.pdf"
MEDIA_DIR = Path("media_images")
MEDIA_DIR.mkdir(parents=True, exist_ok=True)


def pdf_extract_text(
    pdf_path: Path = pdf_path, start_page: int = 0, end_page: int = 3
) -> str:
    """
    Extrai o texto de um arquivo PDF entre as páginas start_page e end_page.
    Retorna texto extraído como uma string contendo o texto de cada página
    separada por quebras de linha e identificada pelo número da página.
    Args:
        pdf_path (Path): Caminho para o arquivo PDF.
        start_page (int): Página inicial (inclusiva).
        end_page (int): Página final (exclusiva).
    Returns:
        str: Texto extraído do PDF.
    """
    text = ""
    pages_text = {}

    with pdf_path.open("rb") as pdf:
        reader = PdfReader(pdf)
        for page in reader.pages[start_page:end_page]:
            page_no = reader.pages.index(page) + 1
            page_text = page.extract_text()
            pages_text[page_no] = page_text
            text += f"\n\n --- Page {page_no} --- \n\n{page_text}"

    return text

with pdf_path.open("rb") as pdf:
    reader = PdfReader(pdf)
    pages_text = {}
    text = ""
    for page_index in range(1, 3):
        page = reader.pages[page_index]
        page_no = reader.pages.index(page) + 1
        # page_text = page.extract_text()
        # pages_text[page_no] = page_text
        # text += f"\n\n --- Page {page_no} --- \n\n{page_text}"

        for image_file_object in page.images:
            # print(page.images)
            page_no = reader.pages.index(page) + 1
            if image_file_object.name.find(".jpg") != -1:
                print(page_no)
                img_name = f"page_{page_index + 1}_{image_file_object.name}"

                out_path = MEDIA_DIR / img_name
                with out_path.open("wb") as fp:
                    fp.write(image_file_object.data)

