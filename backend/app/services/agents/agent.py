"""
Supply Chain AI Agent orchestration (section 22-24).

Implements a tool-calling loop against the LLM provider abstraction. This
plays the role LangGraph would in a larger deployment; the loop itself
(call model -> execute requested tools -> feed results back -> repeat
until the model stops calling tools) is the same mechanism LangGraph
wraps, kept dependency-light here for portability.
"""
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.services.agents.llm_provider import get_llm_provider
from app.services.agents.tools import TOOL_REGISTRY, TOOL_SPECS

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are the AI Supply Chain Assistant for an enterprise supply-chain
disruption prediction and inventory optimization platform.

Rules you MUST follow:
- Never invent inventory numbers, supplier data, disruption events, or financial figures.
- For any factual/numerical question, call the appropriate tool and base your answer only
  on its output.
- For questions about policies, contracts, or historical incident reports, call
  search_knowledge_base or search_news and cite the sources returned.
- If a tool returns an error or insufficient data, tell the user you don't have enough
  data to determine the answer - do not guess.
- Prefer structured, concise answers: state the risk/recommendation, the key contributing
  factors, and cite evidence.
"""


def run_agent_turn(db: Session, user_message: str, history: list[dict] | None = None, max_steps: int = 5) -> dict:
    """
    Provider-agnostic tool-calling loop. `messages` is kept in the normalized
    format documented in llm_provider.py; each provider converts it to its
    own wire format internally, so this loop works unchanged across
    Anthropic, Gemini, and OpenRouter.
    """
    provider = get_llm_provider()
    messages = list(history or [])
    messages.append({"role": "user", "content": user_message})

    tool_trace = []
    for _ in range(max_steps):
        response = provider.complete(messages, system=SYSTEM_PROMPT, tools=TOOL_SPECS, max_tokens=1024)

        if not response["tool_calls"]:
            return {"content": response["content"], "tool_trace": tool_trace, "messages": messages + [{"role": "assistant", "content": response["content"]}]}

        # Record the assistant's turn (text + requested tool calls), execute
        # each tool against the real DB, and feed results back as one "tool"
        # message per call.
        messages.append({"role": "assistant", "content": response["content"], "tool_calls": response["tool_calls"]})

        for call in response["tool_calls"]:
            fn = TOOL_REGISTRY.get(call["name"])
            if not fn:
                result = {"error": f"Unknown tool {call['name']}"}
            else:
                try:
                    result = fn(db, **call["input"])
                except Exception as exc:
                    logger.error("agent.tool_error", tool=call["name"], error=str(exc))
                    result = {"error": str(exc)}
            tool_trace.append({"tool": call["name"], "input": call["input"], "output": result})
            messages.append({"role": "tool", "tool_call_id": call["id"], "name": call["name"], "content": str(result)})

    return {"content": "Reached tool-call step limit without a final answer.", "tool_trace": tool_trace, "messages": messages}
