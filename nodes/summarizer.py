from typing import TypedDict
from langgraph.graph import START, END, StateGraph

class State(TypedDict):
    count: int

def router(state: State):
    if(state["count"] >= 5):
        return "end"
    return "continue"

def increment(state: State):
    print("Current :", state["count"])
    return {
        "count": state["count"]+1
    }

graph_builder = StateGraph(State)

graph_builder.add_node("increment", increment)

graph_builder.add_edge(START, "increment")
graph_builder.add_conditional_edges("increment", router, {"end": END, "continue":"increment" })
graph = graph_builder.compile()

result = graph.invoke({"count": 1})