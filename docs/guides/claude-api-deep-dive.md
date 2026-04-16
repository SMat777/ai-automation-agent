# Claude API & Anthropic SDK Deep-Dive

> **Studyguide** til udviklere der kender Python og vil bygge med Claude API.
> Baseret paa det rigtige projekt `ai-automation-agent` med konkrete kodeeksempler.

---

## Indholdsfortegnelse

1. [Opsaetning: SDK, API-noegle og klient](#1-opsaetning-sdk-api-noegle-og-klient)
2. [Messages API: Roller, content blocks og system prompts](#2-messages-api-roller-content-blocks-og-system-prompts)
3. [Tool Use: Definer tools, haandter tool_use, returner tool_result](#3-tool-use-definer-tools-haandter-tool_use-returner-tool_result)
4. [Type Safety med Anthropic-typer](#4-type-safety-med-anthropic-typer)
5. [Streaming Responses](#5-streaming-responses)
6. [Token Management og omkostningsstyring](#6-token-management-og-omkostningsstyring)
7. [Error Handling: Rate limits, API-fejl og retries](#7-error-handling-rate-limits-api-fejl-og-retries)
8. [Best Practices: Prompt caching, batching, modelvalg](#8-best-practices-prompt-caching-batching-modelvalg)
9. [Kodegennemgang: Agent-klassen i ai-automation-agent](#9-kodegennemgang-agent-klassen-i-ai-automation-agent)
10. [Oevelser](#10-oevelser)

---

## 1. Opsaetning: SDK, API-noegle og klient

### Installation

```bash
# Opret virtuelt miljoe og installer
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
pip install anthropic python-dotenv
```

**requirements.txt** (fra ai-automation-agent):
```
anthropic>=0.42.0
python-dotenv>=1.0.0
```

### API-noegle

Gaa til [console.anthropic.com](https://console.anthropic.com/) og opret en noegle.
Gem den i `.env` (ALDRIG i koden):

```env
ANTHROPIC_API_KEY=sk-ant-api03-...
ANTHROPIC_MODEL=claude-sonnet-4-20250514
```

### Klient-initialisering

```python
import os
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError("ANTHROPIC_API_KEY mangler i .env")

client = Anthropic(api_key=api_key)
```

> **Tip:** Anthropic SDK'et laeser automatisk `ANTHROPIC_API_KEY` fra miljoevariabler,
> saa `Anthropic()` uden argumenter virker ogsaa -- men eksplicit er bedre i produktionskode.

### Saadan goer ai-automation-agent det

Fra `agent/main.py`:
```python
from dotenv import load_dotenv
from agent.agent import Agent

load_dotenv()
api_key = os.getenv("ANTHROPIC_API_KEY")
model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

agent = Agent(api_key=api_key, model=model)
result = agent.run("Analyser denne tekst...")
```

---

## 2. Messages API: Roller, content blocks og system prompts

### Grundstruktur

```
POST https://api.anthropic.com/v1/messages

{
  "model": "claude-sonnet-4-20250514",
  "max_tokens": 1024,
  "system": "Du er en hjaelpsom assistent.",
  "messages": [
    {"role": "user", "content": "Hvad er Python?"}
  ]
}
```

### Python SDK-kald

```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    system="Du er en hjaelpsom assistent der svarer paa dansk.",
    messages=[
        {"role": "user", "content": "Forklar list comprehensions i Python."}
    ],
)

print(response.content[0].text)
```

### Roller

| Rolle | Beskrivelse |
|-------|-------------|
| `system` | Separat parameter -- saetter kontekst og adfaerd for modellen |
| `user` | Brugerens besked (altid foerste besked i listen) |
| `assistant` | Modellens svar (bruges til multi-turn samtaler) |

### Content Blocks

Et `response.content` er en **liste af blokke**, ikke bare tekst:

```python
for block in response.content:
    if block.type == "text":
        print(block.text)
    elif block.type == "tool_use":
        print(f"Tool: {block.name}, Input: {block.input}")
```

### Multi-turn samtale

```python
messages = [
    {"role": "user", "content": "Hvad er en dekorator i Python?"},
    {"role": "assistant", "content": "En dekorator er en funktion der..."},
    {"role": "user", "content": "Giv mig et eksempel med @property."},
]

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=2048,
    messages=messages,
)
```

### System prompt -- saadan goer ai-automation-agent det

Fra `agent/prompts/system.py`:
```python
AGENT_SYSTEM_PROMPT = """You are an AI automation agent that helps with
document analysis and data extraction tasks.

You have access to tools that let you:
- Analyze documents to extract structure and key points
- Extract specific data points from text
- Summarize content into concise reports

When given a task:
1. Think about which tool(s) would best accomplish it
2. Call the appropriate tool(s) with the right parameters
3. Use the results to build your final answer
4. If a tool result is insufficient, try a different approach

Always explain your reasoning before calling a tool. Be precise with tool parameters.
Return structured, actionable results."""
```

> **Vigtig indsigt:** System prompten forklarer modellen hvilke tools den har,
> og giver den en beslutningsramme (think -> act -> observe).

---

## 3. Tool Use: Definer tools, haandter tool_use, returner tool_result

Tool Use er hjertet i en AI-agent. Modellen beslutter SELV om den skal kalde et tool.

### Diagram: Tool Use Flow

```
    Bruger                     Claude API                    Din kode
      |                            |                            |
      |--- "Analyser teksten" ---->|                            |
      |                            |-- stop_reason: tool_use -->|
      |                            |   content: [{              |
      |                            |     type: "tool_use",      |
      |                            |     name: "analyze_doc",   |
      |                            |     input: {text: "..."}   |
      |                            |   }]                       |
      |                            |                            |
      |                            |<-- tool_result ------------|
      |                            |    {sections: [...],       |
      |                            |     word_count: 142}       |
      |                            |                            |
      |<-- stop_reason: end_turn --|                            |
      |    "Dokumentet indeholder  |                            |
      |     3 sektioner..."        |                            |
```

### Trin 1: Definer et tool (JSON Schema)

Hvert tool er et dictionary med `name`, `description` og `input_schema`:

```python
ANALYZE_TOOL = {
    "name": "analyze_document",
    "description": (
        "Analyze a document to extract its structure, key points, and main topics. "
        "Use this when you need to understand what a document contains."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "The document text to analyze",
            },
            "focus": {
                "type": "string",
                "description": "Optional focus area (e.g., 'financial', 'technical')",
                "default": "general",
            },
        },
        "required": ["text"],
    },
}
```

> **Vigtig:** `description` er afgoerende -- det er det modellen bruger til at beslutte
> om toolen skal bruges. Skriv klare, praecise beskrivelser.

### Trin 2: Registrer tools og handlers

Fra `agent/tools/__init__.py`:
```python
TOOLS = [ANALYZE_TOOL, EXTRACT_TOOL, SUMMARIZE_TOOL]

TOOL_HANDLERS = {
    "analyze_document": handle_analyze,
    "extract_data": handle_extract,
    "summarize": handle_summarize,
}
```

### Trin 3: Send tools med API-kaldet

```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=4096,
    system=AGENT_SYSTEM_PROMPT,
    tools=tools,           # <-- Listen af tool-definitioner
    messages=messages,
)
```

### Trin 4: Haandter stop_reason

```python
if response.stop_reason == "end_turn":
    # Modellen er faerdig -- ekstraher tekst-svar
    final_answer = response.content[0].text

elif response.stop_reason == "tool_use":
    # Modellen vil kalde et tool -- vi skal koere det og sende resultatet
    for block in response.content:
        if block.type == "tool_use":
            tool_name = block.name       # f.eks. "analyze_document"
            tool_input = block.input     # f.eks. {"text": "...", "focus": "technical"}
            tool_id = block.id           # unikt ID til at matche resultatet
```

### Trin 5: Koer toolen og send tool_result tilbage

```python
# Koer handler-funktionen
result = handler(**tool_input)

# Byg tool_result besked
tool_result = {
    "type": "tool_result",
    "tool_use_id": block.id,         # SKAL matche tool_use blokkens ID
    "content": json.dumps(result),   # Resultatet som string
}

# Tilfoej til samtalen og kald API igen
messages.append({"role": "assistant", "content": response.content})
messages.append({"role": "user", "content": [tool_result]})
```

> **Kritisk detalje:** `tool_result` sendes med `role: "user"` selvom det ikke er
> brugeren der skriver. Det er API'ets konvention -- tool-resultater er altid "user"-beskeder.

### Fejlhaandtering i tools

```python
def _execute_tool(self, name: str, params: dict) -> dict:
    handler = self.tool_handlers.get(name)
    if handler is None:
        return {"error": f"Unknown tool: {name}"}
    try:
        return handler(**params)
    except Exception as e:
        return {"error": f"Tool '{name}' failed: {str(e)}"}
```

---

## 4. Type Safety med Anthropic-typer

Anthropic SDK'et kommer med strinke Python-typer. Brug dem til at undgaa runtime-fejl.

### Centrale typer

```python
from anthropic import Anthropic
from anthropic.types import (
    Message,                  # Hele response-objektet
    MessageParam,             # En besked i messages-listen
    ToolParam,                # En tool-definition
    ToolResultBlockParam,     # Et tool-resultat
    ContentBlock,             # En blok i response.content
    TextBlock,                # Specifik tekstblok
    ToolUseBlock,             # Specifik tool_use blok
)
```

### Saadan bruges de i ai-automation-agent

```python
from typing import Any, Callable, cast
from anthropic.types import Message, MessageParam, ToolParam, ToolResultBlockParam

class Agent:
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514") -> None:
        self.client = Anthropic(api_key=api_key)
        self.model = model
        # cast() fortaeller mypy at vores tool-dicts matcher ToolParam
        self.tools = [cast(ToolParam, tool) for tool in TOOLS]

    def run(self, task: str, max_iterations: int = 10) -> str:
        # MessageParam sikrer korrekt type i messages-listen
        messages: list[MessageParam] = [{"role": "user", "content": task}]

        for _ in range(max_iterations):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=AGENT_SYSTEM_PROMPT,
                tools=self.tools,
                messages=messages,
            )

            if response.stop_reason == "tool_use":
                # ToolResultBlockParam sikrer korrekt struktur
                tool_results: list[ToolResultBlockParam] = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = self._execute_tool(
                            block.name,
                            cast(dict[str, Any], block.input)
                        )
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result),
                        })
                messages.append({"role": "user", "content": tool_results})
```

### Typehierarki-diagram

```
Message
  |-- id: str
  |-- model: str
  |-- role: "assistant"
  |-- content: list[ContentBlock]
  |     |-- TextBlock        (type="text", text="...")
  |     |-- ToolUseBlock     (type="tool_use", name="...", input={...}, id="...")
  |-- stop_reason: "end_turn" | "tool_use" | "max_tokens" | "stop_sequence"
  |-- usage: Usage
        |-- input_tokens: int
        |-- output_tokens: int
```

### mypy-integration

Koer mypy for at fange type-fejl:
```bash
mypy agent/ --strict
```

> **Pro-tip:** Brug `cast()` naar du konverterer fra dine egne tool-dicts til SDK-typer.
> Det er bedre end `# type: ignore` fordi det dokumenterer intentionen.

---

## 5. Streaming Responses

### Hvornaar skal du streame?

| Scenario | Brug streaming? |
|----------|----------------|
| CLI-tool der viser tekst loebende | Ja |
| Agent-loop der venter paa tool calls | Nej (normalt) |
| Chat-UI der viser svar real-time | Ja |
| Batch-job der processer mange tasks | Nej |
| Lange svar (>1000 tokens) | Ja (bedre UX) |

### Grundlaeggende streaming

```python
with client.messages.stream(
    model="claude-sonnet-4-20250514",
    max_tokens=2048,
    messages=[{"role": "user", "content": "Forklar Python generators."}],
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
print()  # Ny linje til sidst
```

### Streaming med events

```python
with client.messages.stream(
    model="claude-sonnet-4-20250514",
    max_tokens=2048,
    messages=[{"role": "user", "content": "Analyser denne kode."}],
    tools=tools,
) as stream:
    for event in stream:
        if event.type == "content_block_start":
            if event.content_block.type == "tool_use":
                print(f"\n[Kalder tool: {event.content_block.name}]")
        elif event.type == "text":
            print(event.text, end="", flush=True)

# Hent det endelige Message-objekt
final_message = stream.get_final_message()
print(f"\nTokens brugt: {final_message.usage.input_tokens + final_message.usage.output_tokens}")
```

### Streaming med tool use

Naar du streamer og modellen kalder et tool, skal du stadig vente paa hele tool_use-blokken
foer du kan koere toolen:

```python
with client.messages.stream(
    model="claude-sonnet-4-20250514",
    max_tokens=4096,
    tools=tools,
    messages=messages,
) as stream:
    # stream.get_final_message() venter paa hele svaret
    response = stream.get_final_message()

# Herefter kan du tjekke stop_reason og haandtere tool calls normalt
if response.stop_reason == "tool_use":
    # ... samme logik som uden streaming
```

---

## 6. Token Management og omkostningsstyring

### Token-taelling

Hvert API-svar inkluderer token-forbrug:

```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hej"}],
)

print(f"Input tokens:  {response.usage.input_tokens}")
print(f"Output tokens: {response.usage.output_tokens}")
print(f"Total:         {response.usage.input_tokens + response.usage.output_tokens}")
```

### Token-taelling FOER du sender (beta)

```python
# Tael tokens uden at lave et kald
count = client.beta.messages.count_tokens(
    model="claude-sonnet-4-20250514",
    messages=[{"role": "user", "content": "En lang tekst her..."}],
    system="System prompt her...",
    tools=tools,
)
print(f"Estimerede input tokens: {count.input_tokens}")
```

### Priser (pr. april 2025)

| Model | Input (pr. 1M tokens) | Output (pr. 1M tokens) |
|-------|----------------------|------------------------|
| Claude Opus 4 | $15.00 | $75.00 |
| Claude Sonnet 4 | $3.00 | $15.00 |
| Claude Haiku 3.5 | $0.80 | $4.00 |

### max_tokens-strategi

```python
# FORKERT: For hoej max_tokens koster ikke ekstra INPUT, men kan give lange svar
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=100_000,   # Unodvendigt hoej
    messages=messages,
)

# KORREKT: Saet en rimelig graense baseret paa forventet output
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=4096,      # Nok til de fleste svar
    messages=messages,
)
```

> **Vigtig:** `max_tokens` er OBLIGATORISK. Hvis svaret overstiger graensen,
> faar du `stop_reason: "max_tokens"` og et afkortet svar.

### Cost tracker

```python
class CostTracker:
    """Spoer token-forbrug og estimerede omkostninger."""

    # Priser pr. token (Sonnet 4)
    INPUT_COST = 3.00 / 1_000_000     # $3 pr. 1M input tokens
    OUTPUT_COST = 15.00 / 1_000_000   # $15 pr. 1M output tokens

    def __init__(self):
        self.total_input = 0
        self.total_output = 0
        self.call_count = 0

    def track(self, response):
        self.total_input += response.usage.input_tokens
        self.total_output += response.usage.output_tokens
        self.call_count += 1

    @property
    def total_cost(self) -> float:
        return (
            self.total_input * self.INPUT_COST
            + self.total_output * self.OUTPUT_COST
        )

    def report(self) -> str:
        return (
            f"API-kald: {self.call_count}\n"
            f"Input tokens: {self.total_input:,}\n"
            f"Output tokens: {self.total_output:,}\n"
            f"Estimeret pris: ${self.total_cost:.4f}"
        )
```

### Token-besparelse i agent-loops

I ai-automation-agent loebes agent-loopen potentielt mange gange.
Hvert kald sender HELE samtalehistorikken, saa input-tokens vokser:

```
Iteration 1:  system + user task                         ~500 tokens
Iteration 2:  system + user task + assistant + tool_result ~1500 tokens
Iteration 3:  system + alt ovenstaaende + mere            ~3000 tokens
...
```

**Strategier:**
- Saet `max_iterations` lavt (10 er godt)
- Komprimér tool-resultater (send kun det relevante, ikke raa data)
- Brug `json.dumps(result)` frem for at stringify hele objekter

---

## 7. Error Handling: Rate limits, API-fejl og retries

### Fejltyper

```python
from anthropic import (
    APIError,              # Basis for alle API-fejl
    APIConnectionError,    # Netvaerksfejl
    RateLimitError,        # 429 Too Many Requests
    APIStatusError,        # Alle HTTP-fejl med status kode
    AuthenticationError,   # 401 Ugyldig API-noegle
    BadRequestError,       # 400 Fejl i request (f.eks. for mange tokens)
    PermissionDeniedError, # 403 Ingen adgang
    NotFoundError,         # 404
    InternalServerError,   # 500+ Anthropics serverfejl
)
```

### Grundlaeggende fejlhaandtering

```python
from anthropic import Anthropic, RateLimitError, APIError

client = Anthropic()

try:
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Hej!"}],
    )
except RateLimitError as e:
    print(f"Rate limit naaet. Vent og proev igen. Headers: {e.response.headers}")
except APIError as e:
    print(f"API-fejl: {e.status_code} - {e.message}")
```

### Retry med exponential backoff

SDK'et har **automatisk retry** indbygget for forbigaaende fejl (429, 500, 502, 503, 504):

```python
# Standard: 2 retries med exponential backoff
client = Anthropic()

# Justér antal retries
client = Anthropic(max_retries=5)

# Deaktivér retries
client = Anthropic(max_retries=0)
```

### Manuel retry-logik (naar du har brug for mere kontrol)

```python
import time
from anthropic import RateLimitError

def call_with_retry(client, max_retries=3, **kwargs):
    """Kald API med eksponentiel backoff."""
    for attempt in range(max_retries + 1):
        try:
            return client.messages.create(**kwargs)
        except RateLimitError as e:
            if attempt == max_retries:
                raise
            # Brug Retry-After header hvis den findes
            retry_after = e.response.headers.get("retry-after")
            wait = float(retry_after) if retry_after else (2 ** attempt)
            print(f"Rate limited. Venter {wait}s (forsoeg {attempt + 1}/{max_retries})")
            time.sleep(wait)
```

### Haandter max_tokens afbrydelse

```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=100,  # Bevidst lavt for eksemplet
    messages=[{"role": "user", "content": "Skriv en lang historie."}],
)

if response.stop_reason == "max_tokens":
    print("ADVARSEL: Svaret blev afkortet!")
    # Du kan fortsaette samtalen for at faa resten
    messages.append({"role": "assistant", "content": response.content})
    messages.append({"role": "user", "content": "Fortsaet."})
```

---

## 8. Best Practices: Prompt caching, batching, modelvalg

### Prompt Caching

Prompt caching reducerer latency og omkostninger naar du sender det samme system prompt
eller store kontekster gentagne gange:

```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    system=[
        {
            "type": "text",
            "text": "Et meget langt system prompt med regler, eksempler...",
            "cache_control": {"type": "ephemeral"},  # <-- Aktivér caching
        }
    ],
    messages=[{"role": "user", "content": "Sporgsmaal..."}],
)

# Tjek cache-brug i response
print(f"Cache creation input tokens: {response.usage.cache_creation_input_tokens}")
print(f"Cache read input tokens:     {response.usage.cache_read_input_tokens}")
```

**Hvornaar er caching vaerd at bruge?**
- System prompt > 1024 tokens
- Samme kontekst sendes i mange kald (f.eks. agent-loops)
- Store dokumenter der analyseres med flere spoergsmaal

### Message Batches API

Til store maengder uafhaengige kald (50% rabat, resultat inden 24 timer):

```python
batch = client.messages.batches.create(
    requests=[
        {
            "custom_id": f"task-{i}",
            "params": {
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": text}],
            },
        }
        for i, text in enumerate(many_texts)
    ]
)

# Tjek status
status = client.messages.batches.retrieve(batch.id)
print(f"Status: {status.processing_status}")

# Hent resultater naar batch er faerdig
for result in client.messages.batches.results(batch.id):
    print(f"{result.custom_id}: {result.result.message.content[0].text[:100]}")
```

### Modelvalg

| Brug | Anbefalet model | Hvorfor |
|------|----------------|---------|
| Agent med tool use | Claude Sonnet 4 | God balance mellem pris og intelligens |
| Simpel klassificering | Claude Haiku 3.5 | Hurtig og billig |
| Kompleks raesonnering | Claude Opus 4 | Bedste kvalitet, hoejeste pris |
| Kode-generering | Claude Sonnet 4 | Staerk til kode, rimelig pris |

ai-automation-agent bruger `claude-sonnet-4-20250514` som standard med mulighed for override:
```python
model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
```

### Andre best practices

1. **Hold tool-beskrivelser praecise** -- modellen vaelger tool baseret paa `description`
2. **Brug `required` i input_schema** -- undgaa at modellen sender tomme parametre
3. **Komprimér tool-resultater** -- send kun det modellen har brug for, ikke hele datasaet
4. **Saet rimelig max_tokens** -- 4096 er en god standard for de fleste agent-svar
5. **Log token-forbrug** -- spoer omkostninger fra dag 1

---

## 9. Kodegennemgang: Agent-klassen i ai-automation-agent

Her gennemgaar vi `agent/agent.py` linje for linje for at forstaa et komplet eksempel.

### Oversigt: Agent-arkitektur

```
agent/
  agent.py           # Agent-klasse med agentic loop
  main.py            # Entry point (CLI)
  prompts/
    system.py        # System prompt
  tools/
    __init__.py      # Tool registry (TOOLS + TOOL_HANDLERS)
    analyze.py       # analyze_document tool
    extract.py       # extract_data tool
    summarize.py     # summarize tool
```

### Agent.__init__ -- Opsaetning

```python
class Agent:
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514") -> None:
        self.client = Anthropic(api_key=api_key)    # SDK-klienten
        self.model = model                           # Model-ID
        self.tools = [cast(ToolParam, tool) for tool in TOOLS]  # Type-safe tools
        self.tool_handlers = TOOL_HANDLERS           # Mapping: tool_name -> funktion
```

**Vigtige designvalg:**
- `cast(ToolParam, tool)` -- konverterer vores tool-dicts til SDK-typer for mypy
- Tool-definitioner og handlers er adskilt i `tools/`-mappen for overskuelighed
- Model kan overrides via miljoe-variabel

### Agent.run -- Agentic Loop

```python
def run(self, task: str, max_iterations: int = 10) -> str:
    messages: list[MessageParam] = [{"role": "user", "content": task}]

    for _ in range(max_iterations):
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=AGENT_SYSTEM_PROMPT,
            tools=self.tools,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            return self._extract_text(response)    # Faerdigt svar

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})

            tool_results: list[ToolResultBlockParam] = []
            for block in response.content:
                if block.type == "tool_use":
                    result = self._execute_tool(block.name, cast(dict[str, Any], block.input))
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    })

            messages.append({"role": "user", "content": tool_results})

    return "Agent reached maximum iterations without completing the task."
```

**Loopens flow:**

```
START
  |
  v
[Send messages til Claude] -------> stop_reason == "end_turn"? --> RETURN tekst
  |                                        |
  | stop_reason == "tool_use"              |
  v                                        |
[Tilfoej assistant-besked]                 |
[Koer alle tool calls]                     |
[Tilfoej tool_results som user-besked]     |
  |                                        |
  +--- loop igen --------------------------+
  |
  v (max_iterations naaet)
RETURN fejlbesked
```

**Kritiske detaljer:**

1. **Samtalehistorik vokser:** Hvert loop-iteration tilfojer 2 beskeder
   (assistant + user/tool_result), saa input-tokens stiger.

2. **Flere tool calls i ét svar:** Claude kan kalde flere tools paa én gang.
   Loopet itererer over ALLE content blocks og samler resultaterne.

3. **Safety limit:** `max_iterations=10` forhindrer uendelige loops.

### _execute_tool -- Koer en tool sikkert

```python
def _execute_tool(self, name: str, params: dict[str, Any]) -> dict[str, Any]:
    handler = cast(Callable[..., dict[str, Any]] | None, self.tool_handlers.get(name))
    if handler is None:
        return {"error": f"Unknown tool: {name}"}
    try:
        return handler(**params)
    except Exception as e:
        return {"error": f"Tool '{name}' failed: {str(e)}"}
```

**Design-moenster:**
- Returnerer altid et dict (aldrig en exception) -- saa Claude kan laese fejlen og proeve igen
- Bruger `**params` til at unpacke tool-input direkte som keyword arguments
- Handler-funktionerne er rene Python-funktioner -- nemt at teste uafhaengigt

### _extract_text -- Hent tekst fra response

```python
def _extract_text(self, response: Message) -> str:
    text_blocks = [block.text for block in response.content if block.type == "text"]
    return "\n".join(text_blocks)
```

---

## 10. Oevelser

### Oevelse 1: Dit foerste API-kald

Opret en fil `hello_claude.py` og lav et simpelt kald:

```python
# hello_claude.py
from anthropic import Anthropic

client = Anthropic()  # Laeser ANTHROPIC_API_KEY fra miljoet

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=256,
    messages=[{"role": "user", "content": "Sig hej paa dansk og forklar hvad du er."}],
)

print(response.content[0].text)
print(f"\nTokens: {response.usage.input_tokens} in / {response.usage.output_tokens} out")
```

**Maal:** Faa et svar og forstaa token-forbrug.

---

### Oevelse 2: Tilfoej et nyt tool til ai-automation-agent

Opret `agent/tools/translate.py`:

```python
TRANSLATE_TOOL = {
    "name": "translate_text",
    "description": "Translate text between languages. Use this for translation tasks.",
    "input_schema": {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Text to translate"},
            "target_language": {"type": "string", "description": "Target language (e.g., 'Danish', 'English')"},
        },
        "required": ["text", "target_language"],
    },
}

def handle_translate(text: str, target_language: str) -> dict:
    # Simpel placeholder -- i virkeligheden ville du kalde en oversaettelses-API
    return {
        "original": text,
        "target_language": target_language,
        "note": "Translation would happen here",
        "word_count": len(text.split()),
    }
```

**Opgaver:**
1. Tilfoej toolen til `TOOLS` og `TOOL_HANDLERS` i `agent/tools/__init__.py`
2. Koer testene: `pytest tests/` -- de skal fejle (test_tool_count forventer 3)
3. Ret testen og verficer at alt passer

---

### Oevelse 3: Byg en cost tracker ind i Agent-klassen

Tilfoej `CostTracker` fra sektion 6 til `Agent` klassen:

```python
class Agent:
    def __init__(self, ...):
        ...
        self.cost_tracker = CostTracker()

    def run(self, task: str, max_iterations: int = 10) -> str:
        ...
        for _ in range(max_iterations):
            response = self.client.messages.create(...)
            self.cost_tracker.track(response)   # <-- Tilfoej denne linje
            ...
        print(self.cost_tracker.report())
```

**Maal:** Spoer omkostninger per agent-koersel.

---

### Oevelse 4: Implementer streaming i en chat-loop

```python
# chat.py
from anthropic import Anthropic

client = Anthropic()
messages = []

while True:
    user_input = input("\nDig: ")
    if user_input.lower() in ("quit", "exit"):
        break

    messages.append({"role": "user", "content": user_input})

    print("\nClaude: ", end="")
    with client.messages.stream(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        messages=messages,
    ) as stream:
        full_response = ""
        for text in stream.text_stream:
            print(text, end="", flush=True)
            full_response += text

    print()
    messages.append({"role": "assistant", "content": full_response})
```

**Maal:** Forstaa streaming og multi-turn samtaler.

---

### Oevelse 5: Error handling challenge

Skriv en funktion der haandterer alle disse scenarier:
1. Ugyldigt API-noegle (AuthenticationError)
2. For mange tokens i input (BadRequestError)
3. Rate limiting (RateLimitError) med retry
4. Afkortet svar (stop_reason == "max_tokens") med auto-fortsaettelse

```python
def robust_call(client, messages, max_retries=3):
    """Implementer robust API-kald med fejlhaandtering.

    TODO:
    - Haandter AuthenticationError med en klar besked
    - Haandter BadRequestError (tjek om det er token overflow)
    - Haandter RateLimitError med exponential backoff
    - Tjek stop_reason og fortsaet hvis afkortet
    """
    pass  # Din kode her
```

---

## Hurtig-reference

### Minimalt kald
```python
from anthropic import Anthropic
r = Anthropic().messages.create(
    model="claude-sonnet-4-20250514", max_tokens=1024,
    messages=[{"role": "user", "content": "Hej!"}]
)
print(r.content[0].text)
```

### Minimalt tool use
```python
tools = [{"name": "get_weather", "description": "Hent vejret",
          "input_schema": {"type": "object", "properties": {
              "city": {"type": "string"}}, "required": ["city"]}}]
r = client.messages.create(model="claude-sonnet-4-20250514", max_tokens=1024,
    tools=tools, messages=[{"role": "user", "content": "Hvad er vejret i Koebenhavn?"}])
# r.stop_reason == "tool_use"
# r.content[1].name == "get_weather", r.content[1].input == {"city": "Koebenhavn"}
```

### Vigtige links
- [Anthropic Python SDK (GitHub)](https://github.com/anthropics/anthropic-sdk-python)
- [API Reference](https://docs.anthropic.com/en/api/messages)
- [Tool Use Guide](https://docs.anthropic.com/en/docs/build-with-claude/tool-use)
- [Prompt Caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)
- [Message Batches](https://docs.anthropic.com/en/docs/build-with-claude/message-batches)

---

*Genereret 2026-04-16 -- baseret paa Anthropic Python SDK >=0.42.0 og ai-automation-agent projektet.*
