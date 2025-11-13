import asyncio
import json
import time
from pathlib import Path
from typing import Any

from langchain_core.caches import InMemoryCache
from langchain_core.exceptions import OutputParserException
from langchain_core.globals import set_llm_cache
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langgraph.graph.state import RunnableConfig
from pydantic import ValidationError
from rich import print

from graph import build_graph
from prompts import HUMAN_PROMPT, SYSTEM_PROMPT


def _content_to_text(content: str | list[str | dict[str, Any]]) -> str:
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: list[str] = []

        for item in content:
            if isinstance(item, str) and item.strip():
                parts.append(item)

            elif isinstance(item, dict):
                txt = item.get("text", "")
                if txt and txt.strip():
                    parts.append(txt)

                elif (
                    isinstance(item.get("content", None), str)
                    and item["content"].strip()
                ):
                    parts.append(item["content"])
        return "\n".join(parts)
    return str(content)


async def main() -> None:
    set_llm_cache(InMemoryCache())
    config = RunnableConfig(configurable={"thread_id": 1})
    graph = build_graph()

    messages = [
        SystemMessage(SYSTEM_PROMPT),
        HumanMessage(HUMAN_PROMPT),
    ]

    result = await graph.ainvoke({"messages": messages}, config=config)

    final_message = result["messages"][-1]
    if isinstance(final_message, AIMessage):
        content = final_message.content
        raw_text: str = _content_to_text(content)
        try:

            parsed = JsonOutputParser().invoke(raw_text)

            json_path = Path(__file__).parent / "final_output.json"

            with json_path.open("w", encoding="utf-8") as file:
                json.dump(parsed, file, indent=4, ensure_ascii=False)

        except (ValidationError, OutputParserException) as e:
            print(f"Errro ao parsear a resposta JSON: {e}")
            print(f"Conteúdo bruto da resposta: {content}")

    else:
        print("content não foi parsable.")
        return


if __name__ == "__main__":
    print(f"Start execution at {time.strftime('%X')}")
    start = time.perf_counter()
    asyncio.run(main())
    end = time.perf_counter()
    print(f"Execution time: {end - start:.2f} seconds")
    # first time execution (before async functions and cache):  ~1165 seconds
    # subsequent executions (with cache): ~1054 seconds
    # after optimizations in tool 'structure_questions': ~ 525 seconds
    # after switching to gemini-2.5-flash-lite and
    # tweaks in 'structure_questions': ~ 342 seconds
