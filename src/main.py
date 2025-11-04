import json
import time
from pathlib import Path
from tracemalloc import start

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langgraph.graph.state import RunnableConfig
from pydantic import ValidationError
from rich import print

from graph import build_graph
from prompts import SYSTEM_PROMPT


def main() -> None:
    config = RunnableConfig(configurable={"thread_id": 1})
    graph = build_graph()

    messages = [
        SystemMessage(SYSTEM_PROMPT),
        HumanMessage(
            "Extraia o texto do PDF no caminho 'pdfs/exemplo.pdf'"
            "entre as páginas 1 e 3."
            "E extraia as imagens JPEG dessas páginas e salve-as"
            " no diretório 'media_images'."
            "Depois, extraia os dados estruturados conforme as instruções."
        ),
    ]

    result = graph.invoke({"messages": messages}, config=config)

    content = result["messages"][-1].content

    try:
        parsed = JsonOutputParser().invoke(content[-1]["text"])

        json_path = Path(__file__).parent / "final_output.json"

        with json_path.open("w", encoding="utf-8") as file:
            json.dump(parsed, file, indent=4, ensure_ascii=False)

    except ValidationError as e:
        print(f"Errro ao parsear a resposta JSON: {e}")
        print(f"Conteúdo bruto da resposta: {content}")


if __name__ == "__main__":
    start = time.perf_counter()
    main()
    end = time.perf_counter()
    print(f"Execution time: {end - start:.2f} seconds")
