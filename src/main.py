import asyncio
import time
from typing import Any

from langchain_core.caches import InMemoryCache
from langchain_core.globals import set_llm_cache
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph.state import RunnableConfig
from rich import print

from graph import build_graph
from prompts import HUMAN_PROMPT, SYSTEM_PROMPT


def _content_to_text(content: str | list[str | dict[str, Any]]) -> str:
    text = ""

    if isinstance(content, str):
        text = content

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
        text = "\n".join(parts)

    else:
        text = str(content)

    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]

    text = text.removesuffix("```")

    return text.strip()


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
        content_text = _content_to_text(final_message.content)
        print(content_text)
        print()

    else:
        print("Final message is not from AI.")
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
    # after switching to gemini-2.5-flash-lite: ~ 300-500 seconds
    # after further prompt optimizations: ~150-250 seconds
    # after adding concurrency with semaphore limit 30: ~ 30-50 seconds
