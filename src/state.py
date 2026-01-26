"""State management for the agent.

This module defines the structure for maintaining the state of
messages exchanged during the data extraction and processing workflow.
"""

from collections.abc import Sequence
from typing import Annotated, TypedDict

from langgraph.graph.message import BaseMessage, add_messages


class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
