import time
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pypdf import PdfReader
from rich import print_json

load_dotenv()

pdf_path = Path(__file__).parent.parent.parent / "pdfs" / "exemplo.pdf"

start = time.perf_counter()
text = ""
with pdf_path.open("rb") as pdf:
    reader = PdfReader(pdf)
    for page in reader.pages[1:3]:
        text += page.extract_text()

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

template = """
Extraia e retorne as seguintes informações do texto fornecido:
- Questão e número da questão
- Texto do enunciado, (algumas questões podem ter um texto antes do enunciado
que deve ser incluído, caso nao tenha retorne apenas o enunciado e uma string
vazia para esse campo)
- Enunciado
- Fontes, caso tenha (utilize a formatação [texto](link))
- Alternativas (A, B, C, D, E)

Retorne os dados no seguinte formato JSON:
{{
    "questao": str,
    "texto_do_enunciado": str,
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
# print(text)

prompt = PromptTemplate(input_variables=["text"], template=template)

chain = prompt | llm | JsonOutputParser()

response = chain.invoke({"text": text})

end = time.perf_counter()
print_json(data=response)

print(f"\nTempo de execução: {end - start} segundos")
