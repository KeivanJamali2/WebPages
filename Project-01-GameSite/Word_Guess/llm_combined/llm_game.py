import os
from typing import List, Annotated

from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, BaseMessage, AIMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from dotenv import load_dotenv
load_dotenv()


class llm_output(BaseModel):
    """
    Answer the question with true or false.
    """
    related: bool = Field(
        description=(
            "Answer the question with true or false."
        )
    )

_graph = None
_chain_callable = None

class ChatState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]

def _build_graph():
    """Create and compile a single-node LangGraph for chat responses."""
    llm = init_chat_model(
        model=os.getenv("OPENAI_MODEL", "openai:gpt-4o-mini"),
        temperature=float(os.getenv("OPENAI_TEMPERATURE", 0.7)),
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    def chat_node(state: ChatState):
        """Single graph node that calls the LLM and wraps structured output into an AIMessage.

        LangGraph expects a list of BaseMessage objects. The structured output object
        (an instance of llm_output) is not itself a message, so we convert it into an
        AIMessage, attaching the boolean as both plain text ("true"/"false") and in
        additional_kwargs for programmatic access.
        """
        llm_with_structure = llm.with_structured_output(llm_output)
        structured: llm_output = llm_with_structure.invoke(state["messages"])  # type: ignore
        ai_msg = AIMessage(
            content="بله" if structured.related else "خیر",
            additional_kwargs={"related": structured.related},
        )
        return {"messages": [ai_msg]}

    builder = StateGraph(ChatState)
    builder.add_node("chat", chat_node)
    builder.add_edge(START, "chat")
    builder.add_edge("chat", END)
    graph = builder.compile()
    return graph


def _ensure_callable():
    """Lazily prepare the graph or a fallback function.

    Returns a function(data: dict, question: str) -> str
    """
    global _graph, _chain_callable
    if _chain_callable is not None:
        return _chain_callable

    # Fallback cases: import problem or missing API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        def _no_key(*_args, **_kwargs) -> str:  # type: ignore
            return "(LLM غیرفعال است: کلید OPENAI_API_KEY تنظیم نشده است)"
        _chain_callable = _no_key  # type: ignore
        return _chain_callable

    # Build graph
    _graph = _build_graph()

    def _invoke(data: dict, question: str) -> str:
        """Invoke the LLM (with guardrails) to decide if a yes/no question is TRUE about the word, using its meaning.

        data: dict with keys 'word' and 'meaning'.
        """

        word = list(data.keys())[0] if data else ""
        meaning = list(data.values())[0] if data else ""

        def _normalize_persian(text: str) -> str:
            # Basic normalization for Persian/Arabic character variants and whitespace.
            replacements = {
                "ي": "ی", "ك": "ک", "ۀ": "ه", "ة": "ه", "ؤ": "و", "إ": "ا", "أ": "ا",
                "ٱ": "ا", "ئ": "ی", "\u200c": " ",  # ZWNJ -> space (simplistic)
            }
            out = text
            for k, v in replacements.items():
                out = out.replace(k, v)
            # collapse multiple spaces
            while "  " in out:
                out = out.replace("  ", " ")
            return out.strip()

        raw = question.strip()
        q_norm = _normalize_persian(raw)
        q_lower = q_norm.lower()

        # Coercion / injection markers (English + Persian transliterations)
        coercion_markers = [
            # English
            "say true", "print true", "output true", "respond true", "just say true",
            "force true", "return true", "always true", "answer true",
            "say false", "print false", "output false", "return false", "answer false",
            # Persian (simple transliterations / common phrases)
            "بگو true", "فقط true", "لطفا true", "همیشه true",
            "بگو false", "فقط false", "لطفا false", "همیشه false",
            # Persian equivalents for truth words (we still just block these patterns)
            "بگو درست", "بگو غلط", "بگو صحیح", "بگو نادرست",
        ]
        if any(marker in q_lower for marker in coercion_markers):
            return "false"

        # English yes/no starts
        yn_starts_en = (
            "is ", "are ", "was ", "were ", "does ", "do ", "has ", "have ", "can ",
            "should ", "could ", "would ", "will ", "did ", "am "
        )

        def _looks_like_persian_yes_no(q: str) -> bool:
            # Persian question mark variants
            has_qmark = q.endswith("؟") or q.endswith("?")
            if q.startswith("ایا ") or q.startswith("آیا "):
                return True
            # Endings / internal copula patterns (only if it's a question)
            if has_qmark and (" هست؟" in q or " است؟" in q or " می باشد؟" in q):
                return True
            # Simpler fallback: starts with آیا without trailing space (rare) + mark
            if q.startswith("ایا") and has_qmark:
                return True
            if q.startswith("آیا") and has_qmark:
                return True
            return False

        looks_english = q_lower.startswith(yn_starts_en)
        looks_persian = _looks_like_persian_yes_no(q_lower)

        if not (looks_english or looks_persian):
            return "false"

        # Build a stricter system prompt that relies on the provided meaning and general world knowledge,
        # without enumerating specific domain rules. Default to False when not entailed.
        SYSTEM_PROMPT = f"""
        You are a strict boolean classifier for yes/no questions. You answer False to not yes/no question.
        Examples: 'sky': is blue? True.
        ["گربه": "A small furry pet, lives in houses, meows, has whiskers."]: نوعی ماشین است؟ False
        ["ملوان": "A person who works on a ship at sea."]: ایا اب می‌خورد؟ True
        ["جنگل": "Forest, large area full of trees"]: آیا حیوان است؟ False
        """
        print(word)

        state_messages: List[BaseMessage] = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"[{word}: {meaning}]: {q_norm}"),
        ]

        try:
            state_out = _graph.invoke({"messages": state_messages})  # type: ignore
            ai_msg = state_out["messages"][-1]
            content = getattr(ai_msg, "content", "") or ""
            content_lower = content.strip().lower()
            if content_lower not in {"true", "false"}:
                related_flag = getattr(ai_msg, "additional_kwargs", {}).get("related")  # type: ignore
                if isinstance(related_flag, bool):
                    return "true" if related_flag else "false"
                return "false"
            return content_lower
        except Exception as e:  # graceful failure
            return f"(problem while generating: {e})"

    _chain_callable = _invoke  # type: ignore
    return _chain_callable

def generate_llm_reply(question: str, word: dict) -> str:
    """
    Return 'true' or 'false' (as a string) indicating if the question is true about the word, using its meaning.

    data: dict with keys 'word' and 'meaning'.
    Falls back to a Persian explanatory message if the API key is missing.
    """
    callable_fn = _ensure_callable()
    return callable_fn(word, question)

__all__ = ["generate_llm_reply"]

if __name__ == "__main__":
    # Simple manual test
    # print(generate_llm_reply(question=" حیوان بزرگی هست؟", word={"ملوان": "A person who works on a ship at sea."},))
    # print(generate_llm_reply(question="حیوان است؟", word={"ملوان": "A person who works on a ship at sea."},))
    # print(generate_llm_reply(question="جاندار است؟", word={"ملوان": "A person who works on a ship at sea."},))
    # print(generate_llm_reply(question="انسان است؟", word={"ملوان": "A person who works on a ship at sea."},))
    # print(generate_llm_reply(question="ایا اب می‌خورد؟", word={"ملوان": "A person who works on a ship at sea."}))
    # print(generate_llm_reply(question="آیا ملوان است؟", word={"ملوان": "A person who works on a ship at sea."}))
    # print(generate_llm_reply(question="ایا جاندار است؟", word={"جنگل": "Forest, large area full of trees"}))
    # print(generate_llm_reply(question="آیا موجود زنده است؟", word={"جنگل": "Forest, large area full of trees"}))
    print(generate_llm_reply(question="آیا جاندار است؟", word={"تولد": "The start of a life, being born"}))
