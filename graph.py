from langgraph.graph import StateGraph, START, END
from employees.intake.summarizer import summarize
from employees.planning import perspecitive_discovery
from state import State

def build_graph():
    builder = StateGraph(State)
    builder.add_node("summarizer", summarize)
    builder.add_node("perspective discovery", perspecitive_discovery.perspective_discovery)

    builder.add_edge(START, "summarizer")
    builder.add_edge("summarizer", "perspective discovery")
    builder.add_edge("perspective discovery", END)
    

    graph = builder.compile()

    return graph