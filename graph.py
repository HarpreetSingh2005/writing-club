from langgraph.graph import StateGraph, START, END
from nodes.summarizer import summarize
from state import State

def build_graph():
    builder = StateGraph(State)
    builder.add_node("summarizer", summarize)

    builder.add_edge(START, "summarizer")
    builder.add_edge("summarizer", END)

    graph = builder.compile()

    return graph