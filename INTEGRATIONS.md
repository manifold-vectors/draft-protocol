# Integrations: 5-Minute Quickstarts

DRAFT Protocol works with any AI framework that makes tool calls. Each quickstart below is self-contained, copy-paste ready, and shows the difference between ungoverned and governed execution.

**Prerequisites:** `pip install draft-protocol` and a running DRAFT server (`draft-protocol serve`).

---

## LangChain (5 min)

### Before DRAFT

```python
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI

# Agent executes based on its own interpretation of user intent
agent = create_openai_tools_agent(ChatOpenAI(), tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools)

# What could go wrong: agent assumes "clean up the database"
# means DROP TABLE instead of DELETE FROM ... WHERE expired = true
result = executor.invoke({"input": "clean up the database"})
```

### After DRAFT

```python
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from draft_protocol.client import DRAFTClient

draft = DRAFTClient(base_url="http://localhost:8080")

user_input = "clean up the database"

# DRAFT forces intent clarification before any tool executes
session = draft.intake(user_input, tier="STANDARD")

# session.fields now contains:
# D1 (goal): "Remove expired records from user_sessions table"
# D3 (why_now): "Storage alert triggered at 85% capacity"
# A2 (constraints): "Preserve all records < 90 days old"
# T1 (success): "Storage below 70%, zero active session loss"
# T2 (failure): "Any deletion of non-expired records"

# Only after all dimensions confirmed does execution begin
if session.status == "CONFIRMED":
    result = executor.invoke({"input": session.refined_intent})
```

**What changed:** The agent now knows exactly what "clean up" means before touching the database. DRAFT surfaced 5 assumptions that would have been silent failures.

---

## CrewAI (5 min)

### Before DRAFT

```python
from crewai import Agent, Task, Crew

researcher = Agent(role="Researcher", goal="Find information")
task = Task(description="Research our competitors", agent=researcher)
crew = Crew(agents=[researcher], tasks=[task])

# What could go wrong: "competitors" is ambiguous — which market?
# which timeframe? direct vs indirect? The agent guesses.
result = crew.kickoff()
```

### After DRAFT

```python
from crewai import Agent, Task, Crew
from draft_protocol.client import DRAFTClient

draft = DRAFTClient(base_url="http://localhost:8080")

session = draft.intake(
    "Research our competitors",
    tier="STANDARD",
    context={"domain": "AI governance middleware", "market": "enterprise"}
)

# DRAFT surfaces: which competitors? what dimensions to compare?
# what's the deliverable format? who's the audience?
if session.status == "CONFIRMED":
    task = Task(
        description=session.refined_intent,
        expected_output=session.fields.get("A3", "Research report"),
        agent=researcher
    )
    crew = Crew(agents=[researcher], tasks=[task])
    result = crew.kickoff()
```

---

## AutoGen (5 min)

### Before DRAFT

```python
import autogen

assistant = autogen.AssistantAgent("assistant", llm_config=llm_config)
user_proxy = autogen.UserProxyAgent("user", human_input_mode="NEVER")

# What could go wrong: multi-agent conversation diverges from
# original intent with no mechanism to check alignment
user_proxy.initiate_chat(assistant, message="Refactor the auth module")
```

### After DRAFT

```python
import autogen
from draft_protocol.client import DRAFTClient

draft = DRAFTClient(base_url="http://localhost:8080")

session = draft.intake("Refactor the auth module", tier="STANDARD")

# DRAFT clarifies: which auth module? what's broken? what should
# change vs stay the same? what's the test criteria?
if session.status == "CONFIRMED":
    user_proxy.initiate_chat(
        assistant,
        message=f"{session.refined_intent}\n\n"
                f"Constraints: {session.fields.get('A2', 'None stated')}\n"
                f"Success criteria: {session.fields.get('T1', 'Tests pass')}\n"
                f"Failure criteria: {session.fields.get('T2', 'Breaking changes')}"
    )
```

---

## OpenAI Function Calling (5 min)

### Before DRAFT

```python
from openai import OpenAI

client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Update the pricing page"}],
    tools=tools
)
# The model decides what "update" means on its own
```

### After DRAFT

```python
from openai import OpenAI
from draft_protocol.client import DRAFTClient

draft = DRAFTClient(base_url="http://localhost:8080")
client = OpenAI()

session = draft.intake("Update the pricing page", tier="STANDARD")

# Now the model has explicit scope, constraints, and success criteria
if session.status == "CONFIRMED":
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{
            "role": "user",
            "content": session.refined_intent
        }],
        tools=tools
    )
```

---

## Anthropic Tool Use (5 min)

### Before DRAFT

```python
import anthropic

client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-sonnet-4-5-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Deploy to production"}],
    tools=tools
)
# "Deploy to production" — which service? which version?
# rollback plan? health checks? The model assumes.
```

### After DRAFT

```python
import anthropic
from draft_protocol.client import DRAFTClient

draft = DRAFTClient(base_url="http://localhost:8080")
client = anthropic.Anthropic()

# "Deploy to production" auto-escalates to CONSEQUENTIAL tier
session = draft.intake("Deploy to production", tier="CONSEQUENTIAL")

# DRAFT requires: which service, which version, rollback criteria,
# health check endpoints, notification list, maintenance window
if session.status == "CONFIRMED":
    response = client.messages.create(
        model="claude-sonnet-4-5-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": session.refined_intent}],
        tools=tools
    )
```

---

## Raw REST API (5 min)

For any framework not listed above, DRAFT exposes a standard REST API:

```bash
# Start a session
curl -X POST http://localhost:8080/sessions \
  -H "Content-Type: application/json" \
  -d '{"message": "Migrate user data to new schema", "tier": "CONSEQUENTIAL"}'

# Response includes session_id and elicitation questions
# Answer them:
curl -X POST http://localhost:8080/sessions/{session_id}/respond \
  -H "Content-Type: application/json" \
  -d '{"field": "D1", "value": "Migrate users table from v2 to v3 schema"}'

# Continue until all required fields are confirmed
# Check status:
curl http://localhost:8080/sessions/{session_id}/status

# When status is "CONFIRMED", proceed with execution
```

---

## MCP Native (Built-in)

If your AI client supports MCP (Model Context Protocol), DRAFT runs as a native MCP server — no REST calls needed:

```bash
# stdio transport
draft-protocol serve --transport stdio

# SSE transport
draft-protocol serve --transport sse --port 8080

# Streamable HTTP transport
draft-protocol serve --transport streamable-http --port 8080
```

The 15 MCP tools are available directly to any MCP-compatible client (Claude Desktop, Cursor, Windsurf, etc.). See the [full tool reference](docs/api.md) for details.

---

## Chrome Extension

For browser-based AI chat interfaces (Claude, ChatGPT, Gemini, etc.), DRAFT includes a Chrome Extension that intercepts tool calls at the UI layer:

```
extension/
├── manifest.json
├── content.js      # Intercepts AI responses
├── background.js   # Manages DRAFT sessions
└── popup.html      # Configuration UI
```

See the [extension directory](extension/) for installation instructions.

---

## Which Integration Should I Use?

| Your Setup | Recommended Integration |
|---|---|
| MCP-compatible client (Claude Desktop, Cursor) | MCP Native — zero code needed |
| Python framework (LangChain, CrewAI, AutoGen) | Python client + REST |
| Direct API calls (OpenAI, Anthropic) | Python client wrapping your calls |
| Browser-based AI chat | Chrome Extension |
| Custom/other language | Raw REST API |
| Multiple of the above | MCP Native + REST for non-MCP tools |

---

## What DRAFT Doesn't Replace

DRAFT governs **intake** — making sure AI understands what you want before acting. It does not replace:

- **Output guardrails** (Guardrails AI, NeMo Guardrails) — these validate what the AI produces
- **Observability** (Langfuse, Helicone) — these monitor what happened after the fact
- **Agent frameworks** (LangChain, CrewAI) — these orchestrate execution

DRAFT is complementary to all of these. Use DRAFT *before* your agent framework, and output guardrails *after*. Defense in depth.

---

*DRAFT Protocol is Gate 1 (intake) in the [Vector Gate](https://github.com/manifold-vectors) pipeline. These integrations cover the open-source DRAFT component. For the full three-gate pipeline, see Vector Gate.*
