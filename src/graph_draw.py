"""Module to build and display a graph in Mermaid format."""

from graph import build_graph

if __name__ == "__main__":
    graph = build_graph()
    print(graph.get_graph().draw_mermaid())
