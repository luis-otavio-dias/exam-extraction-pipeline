from pathlib import Path

from langchain.tools import BaseTool, tool
from pypdf import PdfReader

pdf_path = Path(__file__).parent.parent / "pdfs" / "exemplo.pdf"


@tool
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


TOOLS: list[BaseTool] = [pdf_extract_text]
TOOLS_BY_NAME: dict[str, BaseTool] = {tool.name: tool for tool in TOOLS}
