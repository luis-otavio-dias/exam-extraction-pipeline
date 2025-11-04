from pathlib import Path

from langchain.tools import BaseTool, tool
from pypdf import PdfReader

pdf_path = Path(__file__).parent.parent / "pdfs" / "exemplo.pdf"


@tool
def pdf_extract_text(
    pdf_path: Path = pdf_path,
    start_page: int = 0,
    end_page: int | None = None,
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
        total_pages = len(reader.pages)

        if start_page is None or start_page < 0:
            start_page = 0
        if end_page is None or end_page > total_pages:
            end_page = total_pages
        if start_page >= end_page:
            return ""

        for page in reader.pages[start_page:end_page]:
            page_no = reader.pages.index(page) + 1
            page_text = page.extract_text()
            pages_text[page_no] = page_text
            text += f"\n\n --- Page {page_no} --- \n\n{page_text}"

    return text


@tool
def pdf_extract_jpegs(
    pdf_path: Path = pdf_path,
    output_dir: Path = Path("media_images"),
    start_page: int | None = None,
    end_page: int | None = None,
) -> None:
    """
    Extrai imagens JPEG de um arquivo PDF e as salva em um diretório
    especificado.

    Args:
        pdf_path (Path): Caminho para o arquivo PDF.
        output_dir (Path): Diretório onde as imagens extraídas serão salvas.
        start_page (int): Página inicial (inclusiva).
        end_page (int): Página final (exclusiva).
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    with pdf_path.open("rb") as pdf:
        reader = PdfReader(pdf)
        total_pages = len(reader.pages)

        if start_page is None or start_page < 0:
            start_page = 0
        if end_page is None or end_page > total_pages:
            end_page = total_pages
        if start_page >= end_page:
            return

        for page_index in range(start_page, end_page):
            page = reader.pages[page_index]
            for image_file_object in page.images:
                if image_file_object.name.find(".jpg") != -1:
                    img_name = f"page_{page_index+1}_{image_file_object.name}"

                    out_path = output_dir / img_name
                    with out_path.open("wb") as fp:
                        fp.write(image_file_object.data)


TOOLS: list[BaseTool] = [pdf_extract_text, pdf_extract_jpegs]
TOOLS_BY_NAME: dict[str, BaseTool] = {tool.name: tool for tool in TOOLS}
