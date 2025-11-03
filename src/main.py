from langchain_core.messages import HumanMessage
from langgraph.graph.state import RunnableConfig
from rich import print

from graph import build_graph


def main() -> None:
    config = RunnableConfig(configurable={"thread_id": 1})
    graph = build_graph()

    human_message = HumanMessage(
        "Extraia o texto do PDF no caminho padrão entre as páginas 1 e 3."
    )
    current_message = [human_message]
    result = graph.invoke({"messages": current_message}, config=config)

    print(result)


if __name__ == "__main__":
    main()
