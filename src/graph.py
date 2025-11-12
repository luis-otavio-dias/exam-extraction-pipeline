from typing import Literal

from langchain_core.messages import AIMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import END, START
from langgraph.graph.state import CompiledStateGraph, StateGraph
from pydantic import ValidationError
from rich import print

from state import State
from tools import TOOLS, TOOLS_BY_NAME
from utils import load_google_generative_ai_model


async def call_llm(state: State) -> State:
    llm = load_google_generative_ai_model().bind_tools(TOOLS)
    result = await llm.ainvoke(state["messages"])

    return {"messages": [result]}


async def tool_node(state: State) -> State:
    llm_response = state["messages"][-1]

    if not isinstance(llm_response, AIMessage) or not getattr(
        llm_response, "tool_calls", None
    ):
        return state

    tool_messages: list[ToolMessage] = []

    for tool_call in llm_response.tool_calls:
        name = tool_call["name"]
        args = tool_call.get("args", {}) or {}
        id_ = tool_call.get("id", None)

        print(f"Invoking tool '{name}' with args: {args}")
        try:
            content = await TOOLS_BY_NAME[name].ainvoke(args)
            status = "success"

        except (
            KeyError,
            IndexError,
            TypeError,
            ValidationError,
            ValueError,
        ) as error:
            content = f"Erro ao chamar a ferramenta '{name}': {error!s}"
            status = "error"

        tool_messages.append(
            ToolMessage(
                content=content,
                tool_call_id=id_,
                status=status,
            )
        )

    return {"messages": tool_messages}


def router(state: State) -> Literal["tool_node", "__end__"]:
    llm_response = state["messages"][-1]

    if (
        isinstance(llm_response, ToolMessage)
        and getattr(llm_response, "name", None) == "structure_questions"
    ):
        return "__end__"

    if isinstance(llm_response, AIMessage) and getattr(
        llm_response, "tool_calls", None
    ):
        return "tool_node"
    return "__end__"


def build_graph() -> CompiledStateGraph[State, None, State, State]:
    builder = StateGraph(State)

    builder.add_node("call_llm", call_llm)
    builder.add_node("tool_node", tool_node)

    builder.add_edge(START, "call_llm")
    builder.add_conditional_edges("call_llm", router, ["tool_node", "__end__"])
    builder.add_edge("tool_node", "call_llm")
    builder.add_edge("call_llm", END)

    return builder.compile(checkpointer=InMemorySaver())
