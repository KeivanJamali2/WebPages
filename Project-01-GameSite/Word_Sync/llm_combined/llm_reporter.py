"""LLM reporter module

Generates short Persian commentary lines from *reporter personas* about the
players' submitted words each round. Two reporter personas can be called in
sequence by the backend once BOTH players have submitted their words for the
round (transition collecting -> deciding). Their comments are displayed in the
left box (players/room panel) – backend will extend the state payload.

Design goals:
 - Mirror the lightweight pattern used in `llm_client.generate_llm_reply`.
 - Stateless: caller passes round history + current submitted words; we build
   a concise prompt (system + alternating human/assistant messages based on
   name matching) and ask for exactly ONE short comment (<= ~60 Persian words).
 - Fallback gracefully if imports missing or API key absent.

Public function
----------------
generate_reporter_reply(messages: list[dict], persona: str) -> str
    messages: list of objects with at least {'player': str, 'text': str}
              representing prior reporter dialogue turns (if any) plus any
              structured meta lines the backend wishes to include. The logic
              treats entries whose player == persona as assistant turns; all
              others become human turns.
    persona: reporter persona key (must exist in prompts_reporter.prompts)

The resulting LLM call order:
  [ SystemMessage(persona prompt), <converted prior messages...>, HumanMessage(latest context) ]

For initial integration we keep it *very* small: caller may simply pass prior
reporter comments to let persona build continuity.
"""
from __future__ import annotations
import os
from typing import List, Dict, Annotated

from .prompts_reporter import prompts as reporter_prompts

try:  # Import guards identical style to llm_client
    from langchain.chat_models import init_chat_model
    from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage, AIMessage
    from langgraph.graph import StateGraph, START, END
    from typing_extensions import TypedDict
    from langgraph.graph.message import add_messages
    _IMPORT_ERROR = None
except Exception as e:  # pragma: no cover
    _IMPORT_ERROR = e

_graph = None  # compiled graph singleton
_callable = None  # resolved callable returning string


class ReporterState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]


def _build_graph():
    llm = init_chat_model(
        model=os.getenv("OPENAI_MODEL", "openai:gpt-4.1-nano"),
        temperature=float(os.getenv("OPENAI_TEMPERATURE", 0.6)),  # slightly lower for commentary steadiness
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    def node(state: ReporterState):  # type: ignore
        resp = llm.invoke(state["messages"])  # returns AIMessage
        return {"messages": [resp]}

    builder = StateGraph(ReporterState)
    builder.add_node("report", node)
    builder.add_edge(START, "report")
    builder.add_edge("report", END)
    return builder.compile()


def _ensure():
    global _graph, _callable
    if _callable is not None:
        return _callable

    api_key = os.getenv("OPENAI_API_KEY")
    if _IMPORT_ERROR is not None:
        def _disabled(_messages: List[Dict[str, str]], _persona: str) -> str:  # type: ignore
            return f"(گزارشگر غیرفعال: {_IMPORT_ERROR})"
        _callable = _disabled  # type: ignore
        return _callable
    if not api_key:
        def _nokey(_messages: List[Dict[str, str]], _persona: str) -> str:  # type: ignore
            return "(گزارشگر غیرفعال: کلید OPENAI_API_KEY تنظیم نشده است)"
        _callable = _nokey  # type: ignore
        return _callable

    _graph = _build_graph()

    def _invoke(messages: List[Dict[str, str]], persona: str) -> str:
        # Pick persona prompt (fallback generic)
        system_prompt = reporter_prompts.get(persona)

        # Convert prior messages (limit last 20 to cap tokens)
        history = messages[-20:]
        chain_messages: List[BaseMessage] = [SystemMessage(content=system_prompt + "\n\n Do not write more than 60 words. Avoid excessive emoji use.")]
        for m in history:
            name = m.get("player", "?")
            text = m.get("text", "")
            if name == persona:
                chain_messages.append(AIMessage(content=f"{name}: {text}"))
            else:
                chain_messages.append(HumanMessage(content=f"{name}: {text}"))
        try:
            out = _graph.invoke({"messages": chain_messages})  # type: ignore
            ai_msg = out["messages"][-1]
            return getattr(ai_msg, "content", "") or ""
        except Exception as e:  # pragma: no cover
            return f"(اشکال در تولید گزارش: {e})"

    _callable = _invoke  # type: ignore
    return _callable


def generate_reporter_reply(messages: List[Dict[str, str]], persona: str) -> str:
    """Return a short Persian commentary for the given reporter persona.

    Parameters
    ----------
    messages: list[dict]
        Prior reporter dialogue & context lines. Each dict must have 'player' & 'text'.
    persona: str
        Reporter persona key (must map to prompts_reporter.prompts)
    """
    fn = _ensure()
    return fn(messages, persona)


__all__ = ["generate_reporter_reply"]
