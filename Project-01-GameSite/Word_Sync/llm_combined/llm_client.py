"""Lightweight LLM integration for the game chat (now via a single-node LangGraph graph).

Assumptions:
- OPENAI_API_KEY is available in environment (user provides via .env)
- Uses langchain's init_chat_model (same pattern as previous implementation)
- Keeps dependency surface minimal; graceful fallback if model import fails or key missing.

Function `generate_llm_reply(messages)` expects a list of chat dicts like:
[{"player": "Alice", "text": "..."}, ...]
It returns a Persian casual reply string.

Implementation notes:
- We use a StateGraph with a single node ("chat") that formats the history and invokes the model.
- No checkpoint / memory store: caller supplies full history each call (on-demand response only when user presses bot button).
- History truncation: last 15 messages (same as earlier) to control token size.
"""
from __future__ import annotations
import os
from typing import List, Dict, Annotated
from llm_combined.prompts_chat import prompts


# LangChain / LangGraph imports
try:
    from langchain.chat_models import init_chat_model
    from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
    from langgraph.graph import StateGraph, START, END
    from typing_extensions import TypedDict
    from langgraph.graph.message import add_messages
    from langchain_core.messages import AIMessage
    _IMPORT_ERROR = None
except Exception as e:  # pragma: no cover - import guard
    _IMPORT_ERROR = e

# Singleton graph + callable
_graph = None  # type: ignore
_chain_callable = None  # type: ignore  # fallback or graph wrapper

# State definition for LangGraph
class ChatState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]

def _build_graph():
    """Create and compile a single-node LangGraph for chat responses."""
    # Model init
    llm = init_chat_model(
        model=os.getenv("OPENAI_MODEL", "openai:gpt-4.1-nano"),
        temperature=float(os.getenv("OPENAI_TEMPERATURE", 0.7)),
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    def chat_node(state: ChatState):  # type: ignore
        # The incoming state already contains the HumanMessage built from history
        # Just run LLM on state.messages (system + single human) and append answer.
        response = llm.invoke(state["messages"])  # returns AIMessage
        return {"messages": [response]}

    builder = StateGraph(ChatState)
    builder.add_node("chat", chat_node)
    builder.add_edge(START, "chat")
    builder.add_edge("chat", END)
    graph = builder.compile()
    return graph

def _ensure_callable():
    """Lazily prepare the graph or a fallback function.

    Returns a function(messages: List[Dict[str,str]]) -> str
    """
    global _graph, _chain_callable
    if _chain_callable is not None:
        return _chain_callable

    # Fallback cases: import problem or missing API key
    api_key = os.getenv("OPENAI_API_KEY")
    if _IMPORT_ERROR is not None:
        def _no_import(_msgs: List[Dict[str,str]]) -> str:  # type: ignore
            return f"(LLM غیرفعال است: خطا در بارگذاری کتابخانه‌ها: {_IMPORT_ERROR})"
        _chain_callable = _no_import  # type: ignore
        return _chain_callable
    if not api_key:
        def _no_key(*_args, **_kwargs) -> str:  # type: ignore
            return "(LLM غیرفعال است: کلید OPENAI_API_KEY تنظیم نشده است)"
        _chain_callable = _no_key  # type: ignore
        return _chain_callable

    # Build graph
    _graph = _build_graph()

    def _invoke(messages: List[Dict[str,str]], persona: str) -> str:
        # Prepare truncated history (last 15 entries)
        last_msgs = messages[-15:]
        state_messages: List[BaseMessage] = [SystemMessage(content=prompts[persona])]
        llm_name = persona  # assuming persona is the LLM's name

        for m in last_msgs:
            name = m.get("player", "?")
            text = m.get("text", "")
            if name == llm_name:
                # Message from assistant
                state_messages.append(AIMessage(content=f"{name}: {text}"))
            else:
                state_messages.append(HumanMessage(content=f"{name}: {text}"))
        try:
            # Invoke graph with provided state; we don't keep memory/checkpoints.
            state_out = _graph.invoke({"messages": state_messages})  # type: ignore
            ai_msg = state_out["messages"][-1]
            return getattr(ai_msg, "content", "") or ""
        except Exception as e:  # graceful failure
            return f"(problem while generating: {e})"

    _chain_callable = _invoke  # type: ignore
    return _chain_callable


def generate_llm_reply(messages: List[Dict[str,str]], persona: str) -> str:
    """Generate a Persian casual reply given raw chat history message dicts.

    Parameters
    ----------
    messages : list of dicts with keys at least ('player','text')
        Full chat history or subset (last 15 are used internally).
    """
    callable_fn = _ensure_callable()
    return callable_fn(messages, persona)

__all__ = ["generate_llm_reply"]
