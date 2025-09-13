# Agents & Routing

This guide explains multi-agent query decomposition, agent configuration, and the LangGraph state graph.

## Agent Configuration
Agents are defined in `app/utils/agent_utils.py` using `AgentConfig`:

```python
from dataclasses import dataclass
from typing import Any, Literal
from langchain_core.prompts import ChatPromptTemplate

@dataclass(frozen=True)
class AgentConfig:
    name: str
    description: str
    model: str
    tools: list[Any]
    model_provider: Literal["openai","anthropic","deepseek","google","mistral","groq","ollama","huggingface"]
    temperature: float
    prompt: ChatPromptTemplate
```

Concrete configs: `MATH_AGENT`, `RESEARCH_AGENT`, `CODE_AGENT`.

Example usage:
```python
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent
from app.utils.agent_utils import CODE_AGENT

_llm = init_chat_model(
    model=CODE_AGENT.model,
    model_provider=CODE_AGENT.model_provider,
    temperature=CODE_AGENT.temperature,
)
code_agent = create_react_agent(
    model=_llm,
    tools=CODE_AGENT.tools,
    prompt=CODE_AGENT.prompt,
    name=CODE_AGENT.name,
)
```

## Query Decomposition & Routing
- `app/ai_core/agents/new_router.py`: structured output splitting and `routes` building
- `app/ai_core/agents/router.py`: utility functions (summarization, plan completion finalization)

State keys used by router/agents:
- `routes: dict[str, str]` — subquery → agent name
- `subquery_results: list[str]` — agent outputs
- `done_queries: list[str]` — processed subqueries
- `messages: list[BaseMessage]`

## State Graph
Defined in `app/ai_core/state_graph_object.py`:
- Nodes: `router`, `research`, `math`, `code`, `tools`, `format_results`
- Edges:
  - `START -> router`
  - conditional from `router` to `{research, math, code, __end__}` (→ `format_results`)
  - agents route back to `router`
  - `format_results -> END`

`format_results` collects `subquery_results` and emits the final `AIMessage`.

## Prompts
- `app/utils/prompt_utils.py` contains system prompts for agents and helper builders:
  - `RESEARCH_SYSTEM_PROMPT`, `CODE_SYSTEM_PROMPT`, `MATH_SYSTEM_PROMPT`
  - `build_final_response_prompt()`, `build_conversation_summary_prompt(...)`

## Logging
- `app/utils/loging_utils.py` sets a standard logging format.

## Tips
- Keep `LLM_*_MODEL` envs aligned with your provider.
- Use `MODEL_PROVIDER_MAP` in `app/utils/llm_utils.py` to resolve provider for `init_chat_model`.
