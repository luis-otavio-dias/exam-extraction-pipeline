from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import END, START
from langgraph.graph.state import CompiledStateGraph, StateGraph
from pydantic import ValidationError

from state import State
from tools import TOOLS, TOOLS_BY_NAME
from utils import load_google_generative_ai_model


def call_llm(state: State) -> State:
    llm = load_google_generative_ai_model().bind_tools(TOOLS)
    result = llm.invoke(state["messages"])
    return {"messages": [result]}


def tool_node(state: State) -> State:
    llm_response = state["messages"][-1]

    if isinstance(llm_response, AIMessage) and getattr(
        llm_response, "tool_calls", None
    ):
        tool_call = llm_response.tool_calls[-1]

        name, args, id_ = tool_call["name"], tool_call["args"], tool_call["id"]

        try:
            content = TOOLS_BY_NAME[name].invoke(**args)

        except (
            KeyError,
            IndexError,
            TypeError,
            ValidationError,
            ValueError,
        ) as error:
            content = f"Erro ao chamar a ferramenta '{name}': {error!s}"
            status = "error"

    return state


def build_graph() -> CompiledStateGraph[State, None, State, State]:
    builder = StateGraph(State)

    builder.add_node("call_llm", call_llm)
    builder.add_edge(START, "call_llm")
    builder.add_edge("call_llm", END)

    return builder.compile(checkpointer=InMemorySaver())
