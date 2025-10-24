import json
import time
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pypdf import PdfReader

load_dotenv()

pdf_path = Path(__file__).parent.parent.parent / "pdfs" / "exemplo.pdf"

start = time.perf_counter()

text = ""
pages_text = {}

with pdf_path.open("rb") as pdf:
    reader = PdfReader(pdf)
    for page in reader.pages[1:3]:
        page_no = reader.pages.index(page) + 1
        page_text = page.extract_text()
        pages_text[page_no] = page_text
        text += f"\n\n --- Page {page_no} --- \n\n{page_text}"

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

template = """
Extraia e retorne as seguintes informações do texto fornecido:
- Número da página
- Questão e número da questão
- Enunciado
- Fontes, caso tenha (utilize a formatação [texto](link))
- Alternativas (A, B, C, D, E)

Retorne os dados no seguinte formato JSON:
{{
    "page": int,
    "questao": str,
    "enunciado": str,
    "fontes": [str],
    "alternativas": {{
        "A": str,
        "B": str,
        "C": str,
        "D": str,
        "E": str
    }}
}}
{text}
"""

prompt = PromptTemplate(input_variables=["text"], template=template)

chain = prompt | llm | JsonOutputParser()

response = chain.invoke({"text": text})

JSON_PATH = Path(__file__).parent / "output_ex4.json"
with JSON_PATH.open("w", encoding="utf-8") as file:
    json.dump(response, file, indent=4, ensure_ascii=False)


end = time.perf_counter()
# print_json(data=response)

print(f"\nTempo de execução: {end - start} segundos")
