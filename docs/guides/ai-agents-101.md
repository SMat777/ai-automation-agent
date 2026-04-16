# AI Agents 101 -- Arkitektur & Tool Calling

> **Studyguide** | Dato: 2026-04-16  
> **Malgruppe:** Datamatikerstuderende med programmeringserfaring, men nye inden for AI-agenter  
> **Projekt-reference:** `ai-automation-agent` -- Simons eget agentprojekt

---

## Indholdsfortegnelse

1. [Hvad er en AI-agent?](#1-hvad-er-en-ai-agent)
2. [ReAct-monsteret: Reasoning + Acting](#2-react-monsteret-reasoning--acting)
3. [Tool Calling: Hvordan Claude vaelger vaerktojer](#3-tool-calling-hvordan-claude-vaelger-vaerktojer)
4. [Tool Design: name, description, input_schema](#4-tool-design-name-description-input_schema)
5. [Agent-arkitektur-moenstre](#5-agent-arkitektur-moenstre)
6. [Agent-loopet i detaljer](#6-agent-loopet-i-detaljer)
7. [Praktisk gennemgang: agent.py](#7-praktisk-gennemgang-agentpy)
8. [Prompt Engineering for agenter](#8-prompt-engineering-for-agenter)
9. [Fejlhaandtering i agent-loops](#9-fejlhaandtering-i-agent-loops)
10. [Virkelige anvendelser](#10-virkelige-anvendelser)
11. [Columbus-relevans: AI-agenter i enterprise consulting](#11-columbus-relevans-ai-agenter-i-enterprise-consulting)
12. [Forstaelsessporgsmaal](#12-forstaelsessporgsmaal)

---

## 1. Hvad er en AI-agent?

En AI-agent er et program, der **selvstaendigt** kan raesonnere over en opgave, vaelge handlinger, udfore dem og bruge resultaterne til at traeffe nye beslutninger -- alt sammen uden at en bruger manuelt styrer hvert skridt.

### Tre niveauer af AI-systemer

```
┌─────────────────────────────────────────────────────────────────┐
│                        AUTONOMI-SPEKTRET                        │
├──────────────┬──────────────────────┬───────────────────────────┤
│   Chatbot    │  Automations-script  │       AI-Agent            │
├──────────────┼──────────────────────┼───────────────────────────┤
│ Svar paa     │ Udforer faste        │ Raesonnerer, vaelger      │
│ spoergsmaal  │ trin i raekkefoelge  │ vaerktojer, tilpasser     │
│ et ad gangen │                      │ sig dynamisk              │
│              │                      │                           │
│ Ingen        │ Ingen beslutninger   │ Beslutter SELV hvad       │
│ handling     │ -- alt er hardcoded  │ der skal goeres           │
│              │                      │                           │
│ Eksempel:    │ Eksempel:            │ Eksempel:                 │
│ ChatGPT-     │ Cron-job der         │ "Analyseer dette          │
│ samtale      │ henter data          │ dokument og find          │
│              │ kl. 08:00            │ noegletal"                │
└──────────────┴──────────────────────┴───────────────────────────┘
```

### Kerneforskelle

| Egenskab | Chatbot | Script | AI-Agent |
|----------|---------|--------|----------|
| Beslutningstagning | Ingen | Ingen (hardcoded) | Dynamisk |
| Vaerktojsbrug | Ingen | Fast pipeline | Vaelger selv |
| Tilpasningsevne | Lav | Ingen | Hoej |
| Feedback-loop | Ingen | Ingen | Ja (observe -> think -> act) |
| Kontekstbevidsthed | Samtalehistorik | Konfiguration | Opgave + resultater + resonnement |

**Noegleprincip:** En agent er ikke bare en LLM der svarer -- den er en LLM der **handler**, **observerer resultaterne** og **justerer sin plan**.

---

## 2. ReAct-monsteret: Reasoning + Acting

ReAct (Reason + Act) er det mest udbredte moenstre for AI-agenter. Det kombinerer LLM'ens evne til at taenke (reasoning) med evnen til at goere ting (acting).

### ReAct-loopet visualiseret

```
    ┌──────────────────────────────────────────────────┐
    │                    BRUGER-OPGAVE                  │
    │   "Analyseer dette dokument og opsummer det"      │
    └──────────────────────┬───────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │    THINK (Reasoning)   │◄─────────────┐
              │                        │              │
              │  "Jeg skal foerst      │              │
              │   analysere dokumentet │              │
              │   for at forstaa       │              │
              │   strukturen..."       │              │
              └───────────┬────────────┘              │
                          │                           │
                          ▼                           │
              ┌────────────────────────┐              │
              │     ACT (Tool Call)    │              │
              │                        │              │
              │  analyze_document(     │              │
              │    text="...",         │              │
              │    focus="general"     │              │
              │  )                     │              │
              └───────────┬────────────┘              │
                          │                           │
                          ▼                           │
              ┌────────────────────────┐              │
              │   OBSERVE (Resultat)   │              │
              │                        │              │
              │  { sections: [...],    │──────────────┘
              │    key_points: [...],  │   Flere trin
              │    word_count: 342 }   │   nødvendige?
              └───────────┬────────────┘
                          │
                          ▼  Nej, faerdig
              ┌────────────────────────┐
              │     ENDELIGT SVAR      │
              │                        │
              │  "Dokumentet handler   │
              │   om..."               │
              └────────────────────────┘
```

### Hvad ReAct loser

Uden ReAct: En LLM kan kun generere tekst baseret paa sin traening. Den kan ikke hente live data, beregne praecise tal eller interagere med systemer.

Med ReAct: LLM'en kan **planlaegge**, **bruge vaerktojer** til at faa reel information og **bygge svar baseret paa faktiske resultater** i stedet for at gaette.

### ReAct vs. Chain-of-Thought

| Aspekt | Chain-of-Thought | ReAct |
|--------|-----------------|-------|
| Metode | Taenk trin-for-trin | Taenk + handl + observer |
| Handling | Ingen -- kun tekst | Kalder vaerktojer |
| Datakilde | Kun traening | Traening + vaerktojresultater |
| Fejlrettelse | Begreanset | Kan proeve en anden tilgang |

---

## 3. Tool Calling: Hvordan Claude vaelger vaerktojer

Tool calling er den mekanisme, der goer det muligt for en LLM at "goere ting" i den virkelige verden. I stedet for kun at generere tekst, kan modellen signalere: **"Jeg vil gerne kalde dette vaerktoj med disse parametre."**

### Flowet fra API-perspektiv

```
┌─────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│  DIN KODE   │────>│    CLAUDE API         │────>│  DIN KODE       │
│             │     │                      │     │                 │
│ Sender:     │     │ Modellen ser:        │     │ Modtager:       │
│ - system    │     │ - Opgaven            │     │ - stop_reason:  │
│   prompt    │     │ - Tilgaengelige      │     │   "tool_use"    │
│ - tools[]   │     │   vaerktojer         │     │ - tool_name     │
│ - messages  │     │ - Historik           │     │ - tool_input    │
│             │     │                      │     │                 │
│             │     │ Beslutter:           │     │ Du udforer      │
│             │     │ "analyze_document    │     │ vaerktojet og   │
│             │     │  passer bedst her"   │     │ sender resultat │
│             │     │                      │     │ tilbage         │
└─────────────┘     └──────────────────────┘     └─────────────────┘
```

### Hvad modellen ser

Naar du sender et API-kald med vaerktojer, ser Claude noget i retning af:

```json
{
  "system": "Du er en AI automation agent...",
  "tools": [
    {
      "name": "analyze_document",
      "description": "Analyze a document to extract its structure...",
      "input_schema": {
        "type": "object",
        "properties": {
          "text": { "type": "string", "description": "The document text..." },
          "focus": { "type": "string", "description": "Optional focus area..." }
        },
        "required": ["text"]
      }
    }
  ],
  "messages": [
    { "role": "user", "content": "Analyseer denne rapport..." }
  ]
}
```

### Beslutningsprocessen (forenklet)

Claude overvejer: **"Givet denne opgave, hvilken kombination af tilgaengelige vaerktojer vil bedst lose den?"**

Modellen bruger:
1. **Tool-beskrivelsen** -- "Analyze a document to extract its structure" matcher opgaven
2. **Input-skemaet** -- Forstaar hvilke parametre der skal udfyldes
3. **Konteksten** -- Hvad brugeren har bedt om, og hvad der allerede er sket
4. **System-prompten** -- Instruktioner om hvornaar man bruger vaerktojer

### stop_reason -- Noeglebegrebet

Claudes svar har altid en `stop_reason`:

| stop_reason | Betydning | Din kode skal |
|-------------|-----------|---------------|
| `"end_turn"` | Claude er faerdig, her er svaret | Returnere teksten |
| `"tool_use"` | Claude vil kalde et vaerktoj | Udfore vaerktojet, sende resultatet tilbage |
| `"max_tokens"` | Svaret blev afkortet | Haandtere ufuldstaendigt svar |

---

## 4. Tool Design: name, description, input_schema

Saadan dit vaerktoj er designet har **direkte indflydelse** paa hvor godt agenten bruger det. Taenk paa det som en API-kontrakt mellem dig og AI-modellen.

### De tre byggeklodser

```python
# Fra ai-automation-agent/agent/tools/analyze.py

ANALYZE_TOOL = {
    "name": "analyze_document",        # (1) Unikt navn
    "description": (                    # (2) Beskrivelse -- KRITISK
        "Analyze a document to extract its structure, key points, "
        "and main topics. Use this when you need to understand what "
        "a document contains before extracting specific data from it."
    ),
    "input_schema": {                   # (3) JSON Schema for input
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "The document text to analyze",
            },
            "focus": {
                "type": "string",
                "description": "Optional focus area (e.g., 'financial', "
                               "'technical', 'organizational')",
                "default": "general",
            },
        },
        "required": ["text"],
    },
}
```

### (1) name -- Vaerktojets identitet

- Skal vaere unikt paa tvaers af alle vaerktojer
- Brug `snake_case` (f.eks. `analyze_document`, ikke `analyzeDocument`)
- Vaer beskrivende: `extract_data` er bedre end `extract`

### (2) description -- Det vigtigste felt

Beskrivelsen er **det primaere signal** Claude bruger til at vaelge vaerktojer. En daarlig beskrivelse = forkerte vaerktojsvalg.

**Best practices:**
- Forklar **hvad** vaerktojet goer
- Forklar **hvornaar** det skal bruges (vs. andre vaerktojer)
- Giv eksempler paa typiske use cases
- Hold det koncist men praecist

```
GODT:
"Extract specific data points from text based on a list of fields
 to look for. Use this when you need to pull structured information
 like names, dates, numbers, or categories from a document."

DAARLIGT:
"Extracts data."
```

### (3) input_schema -- Kontrakten

JSON Schema der definerer hvad vaerktojet forventer:

| Felt | Formaal | Eksempel |
|------|---------|----------|
| `type` | Altid "object" for vaerktojer | `"object"` |
| `properties` | De parametre vaerktojet accepterer | `{"text": {...}, "focus": {...}}` |
| `required` | Parametre der SKAL vaere med | `["text"]` |
| `description` (pr. felt) | Forklarer hvad feltet er | `"The document text to analyze"` |
| `enum` | Begreanser til specificke vaerdier | `["bullets", "paragraph"]` |
| `default` | Standardvaerdi hvis ikke angivet | `"general"` |

### Sammenligining: Tre vaerktojer fra projektet

```
┌──────────────────┬──────────────────┬──────────────────┐
│ analyze_document │   extract_data   │    summarize     │
├──────────────────┼──────────────────┼──────────────────┤
│ Input:           │ Input:           │ Input:           │
│ - text (req)     │ - text (req)     │ - text (req)     │
│ - focus (opt)    │ - fields (req)   │ - format (opt)   │
│                  │                  │ - max_points     │
│                  │                  │   (opt)          │
├──────────────────┼──────────────────┼──────────────────┤
│ Bruges naar:     │ Bruges naar:     │ Bruges naar:     │
│ Du vil forstaa   │ Du vil traekke   │ Du vil have en   │
│ dokumentets      │ specifikke       │ kort opsummering │
│ struktur         │ datapunkter ud   │                  │
├──────────────────┼──────────────────┼──────────────────┤
│ Output:          │ Output:          │ Output:          │
│ sections,        │ extracted,       │ summary,         │
│ key_points,      │ fields_found,    │ format,          │
│ word_count       │ fields_missing   │ word_count       │
└──────────────────┴──────────────────┴──────────────────┘
```

---

## 5. Agent-arkitektur-moenstre

### Moenstre 1: Single-Agent

Den simpleste arkitektur -- en agent med adgang til vaerktojer.

```
                    ┌───────────────────┐
                    │   SINGLE AGENT    │
                    │                   │
                    │  System Prompt    │
                    │  + LLM           │
                    │  + Tools[]       │
                    └────────┬──────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
        ┌─────┴─────┐ ┌─────┴─────┐ ┌─────┴─────┐
        │  Tool A   │ │  Tool B   │ │  Tool C   │
        │ (analyze) │ │ (extract) │ │(summarize)│
        └───────────┘ └───────────┘ └───────────┘
```

**Fordele:** Simpelt, nemt at debugge, lavere latency  
**Ulemper:** Begreanset af en enkelt prompt og kontekstvindue  
**Bruges i:** `ai-automation-agent` (vores projekt!)

### Moenstre 2: Multi-Agent

Flere agenter med forskellige specialer, der samarbejder.

```
        ┌──────────────┐         ┌──────────────┐
        │  AGENT A     │         │  AGENT B     │
        │  (Forsker)   │────────>│  (Skribent)  │
        │              │ output  │              │
        │ Soeger info, │ bliver  │ Skriver      │
        │ analyserer   │ input   │ rapport      │
        └──────────────┘         └──────────────┘
```

**Fordele:** Hver agent er specialist, bedre til komplekse opgaver  
**Ulemper:** Koordineringslogik, hoejere latency, svaerere at debugge

### Moenstre 3: Hierarkisk (Orchestrator)

En overordnet agent styrer underordnede agenter.

```
                    ┌───────────────────┐
                    │   ORCHESTRATOR    │
                    │                   │
                    │  "Hvem skal       │
                    │   loese hvad?"    │
                    └────────┬──────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
        ┌─────┴─────┐ ┌─────┴─────┐ ┌─────┴─────┐
        │  Agent 1  │ │  Agent 2  │ │  Agent 3  │
        │ (Analyse) │ │ (Kode)    │ │ (Test)    │
        │           │ │           │ │           │
        │ tools:    │ │ tools:    │ │ tools:    │
        │ [read,    │ │ [write,   │ │ [run,     │
        │  search]  │ │  edit]    │ │  assert]  │
        └───────────┘ └───────────┘ └───────────┘
```

**Fordele:** Skalerbart, klar ansvarsfordeling, parallelle opgaver  
**Ulemper:** Mest komplekst, hoejtforbrug af tokens, fejlpropagering  
**Eksempel:** Claude Code (bruger hierarkisk agent-arkitektur med sub-agents)

### Oversigt

| Moenstre | Kompleksitet | Bedst til |
|----------|-------------|-----------|
| Single-Agent | Lav | Specifikke, velafgraensede opgaver |
| Multi-Agent | Mellem | Workflows med klare faser |
| Hierarkisk | Hoej | Komplekse, multi-domaine opgaver |

---

## 6. Agent-loopet i detaljer

Her er det **praecise flow** for hvordan en agent-iteration fungerer, med kodeeksempler fra `ai-automation-agent`.

### Trin-for-trin

```
TRIN 1: Bruger giver opgave
───────────────────────────
  "Analyseer denne rapport og opsummer de vigtigste punkter"
         │
         ▼
TRIN 2: Byg messages-array
───────────────────────────
  messages = [
    {"role": "user", "content": "Analyseer denne rapport..."}
  ]
         │
         ▼
TRIN 3: Send til Claude API
───────────────────────────
  response = client.messages.create(
    model="claude-sonnet-4-20250514",
    system=AGENT_SYSTEM_PROMPT,
    tools=TOOLS,
    messages=messages,
  )
         │
         ▼
TRIN 4: Tjek stop_reason
───────────────────────────
  if response.stop_reason == "end_turn":
      return tekst-svar          ──> FAERDIG
  elif response.stop_reason == "tool_use":
      gaa til trin 5             ──> FORTSAET
         │
         ▼
TRIN 5: Udfør vaerktoj lokalt
───────────────────────────
  handler = TOOL_HANDLERS["analyze_document"]
  result = handler(text="...", focus="general")
  # => {"sections": [...], "key_points": [...]}
         │
         ▼
TRIN 6: Send resultat tilbage
───────────────────────────
  messages.append({"role": "assistant", "content": response.content})
  messages.append({"role": "user", "content": [
    {"type": "tool_result", "tool_use_id": "...", "content": "..."}
  ]})
         │
         ▼
  GÅ TILBAGE TIL TRIN 3 (ny iteration)
```

### Conversation-historikken vokser

```
Iteration 1:
  messages = [
    user: "Analyseer denne rapport..."
  ]

Iteration 2 (efter tool call):
  messages = [
    user: "Analyseer denne rapport...",
    assistant: [thinking + tool_use(analyze_document)],
    user: [tool_result: {sections: [...], ...}]
  ]

Iteration 3 (efter endnu et tool call):
  messages = [
    user: "Analyseer denne rapport...",
    assistant: [thinking + tool_use(analyze_document)],
    user: [tool_result: {sections: [...], ...}],
    assistant: [thinking + tool_use(summarize)],
    user: [tool_result: {summary: "...", ...}]
  ]

Iteration 4 (endeligt svar):
  messages = [
    ...alt ovenfor...,
    assistant: "Rapporten handler om..."   <-- stop_reason: "end_turn"
  ]
```

---

## 7. Praktisk gennemgang: agent.py

Lad os laese den faktiske kode fra projektet og forstaa den linje for linje.

### Filstruktur

```
ai-automation-agent/
├── agent/
│   ├── __init__.py
│   ├── agent.py            <-- KERNEN: Agent-klassen med loopet
│   ├── main.py             <-- Entry point (CLI)
│   ├── prompts/
│   │   ├── __init__.py
│   │   └── system.py       <-- System prompt
│   └── tools/
│       ├── __init__.py     <-- Tool registry (TOOLS + TOOL_HANDLERS)
│       ├── analyze.py      <-- analyze_document tool
│       ├── extract.py      <-- extract_data tool
│       └── summarize.py    <-- summarize tool
├── tests/
│   └── agent/
│       ├── test_agent.py   <-- Tests for tool registry
│       └── test_tools.py   <-- Tests for individual tools
└── docs/
    └── ARCHITECTURE.md
```

### Agent-klassen (komplet kode med kommentarer)

```python
class Agent:
    """AI agent der raesonnerer over opgaver og kalder vaerktojer."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        # Opret Anthropic-klient med API-noegle
        self.client = Anthropic(api_key=api_key)
        self.model = model
        # Indlaes alle vaerktojs-definitioner (name + description + schema)
        self.tools = [cast(ToolParam, tool) for tool in TOOLS]
        # Indlaes alle handler-funktioner (den faktiske kode)
        self.tool_handlers = TOOL_HANDLERS

    def run(self, task: str, max_iterations: int = 10) -> str:
        """Koer agenten paa en opgave. Returnerer endeligt svar."""

        # Start med brugerens opgave som foerste besked
        messages = [{"role": "user", "content": task}]

        # AGENT-LOOPET: max 10 iterationer (sikkerhedsgraense)
        for _ in range(max_iterations):
            # TRIN 1: Send alt til Claude
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=AGENT_SYSTEM_PROMPT,
                tools=self.tools,
                messages=messages,
            )

            # TRIN 2: Er Claude faerdig?
            if response.stop_reason == "end_turn":
                return self._extract_text(response)

            # TRIN 3: Claude vil kalde vaerktojer
            if response.stop_reason == "tool_use":
                # Gem Claudes svar (inkl. reasoning + tool_use blokke)
                messages.append({
                    "role": "assistant",
                    "content": response.content
                })

                # Udfør HVERT vaerktoj Claude bad om
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = self._execute_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result),
                        })

                # Send resultaterne tilbage som "user"-besked
                messages.append({"role": "user", "content": tool_results})

        # Sikkerhedsgraense naaet
        return "Agent reached maximum iterations without completing the task."

    def _execute_tool(self, name: str, params: dict) -> dict:
        """Udfør et vaerktoj. Haandterer ukendte vaerktojer og fejl."""
        handler = self.tool_handlers.get(name)
        if handler is None:
            return {"error": f"Unknown tool: {name}"}
        try:
            return handler(**params)
        except Exception as e:
            return {"error": f"Tool '{name}' failed: {str(e)}"}
```

### Tool Registry (tools/__init__.py)

```python
# Alle vaerktojer samlet eet sted
TOOLS = [ANALYZE_TOOL, EXTRACT_TOOL, SUMMARIZE_TOOL]

# Mapping: vaerktojnavn -> handler-funktion
TOOL_HANDLERS = {
    "analyze_document": handle_analyze,
    "extract_data": handle_extract,
    "summarize": handle_summarize,
}
```

Dette design goer det nemt at tilfoeje nye vaerktojer:
1. Opret en ny fil i `tools/` med `TOOL_DEFINITION` + `handler`
2. Importeer og tilfoej i `tools/__init__.py`
3. Agenten kan nu bruge det -- **ingen aendringer i agent.py!**

---

## 8. Prompt Engineering for agenter

System-prompten er agentens "instruktionsbog". Den definerer **hvem agenten er**, **hvad den kan** og **hvordan den skal opfoere sig**.

### System-prompten fra projektet

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

Always explain your reasoning before calling a tool. Be precise with
tool parameters. Return structured, actionable results."""
```

### Anatomien af en god agent-prompt

```
┌─────────────────────────────────────────────────┐
│              SYSTEM PROMPT STRUKTUR              │
├─────────────────────────────────────────────────┤
│                                                 │
│  1. ROLLE                                       │
│     "Du er en AI automation agent der..."       │
│                                                 │
│  2. KAPABILITETER                               │
│     "Du har adgang til vaerktojer der kan..."   │
│                                                 │
│  3. ADFAERDSINSTRUKTIONER                       │
│     "Naar du faar en opgave:"                   │
│     "1. Taenk over hvilke vaerktojer..."        │
│     "2. Kald de relevante vaerktojer..."        │
│                                                 │
│  4. FEJLHAANDTERING                             │
│     "Hvis et resultat er utilstraekkeligt,      │
│      proev en anden tilgang"                    │
│                                                 │
│  5. OUTPUT-FORMAT                               │
│     "Returner strukturerede, handlingsoriente-  │
│      rede resultater"                           │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Noegleelementer der paavirker agent-adfaerd

**1. Tool-beskrivelser (vigtigst)**
Disse bestemmer hvornaar agenten vaelger et vaerktoj. Sammenlign:

```python
# GODT -- giver Claude kontekst for HVORNAAR vaerktojet bruges
"Analyze a document to extract its structure, key points, and main topics.
 Use this when you need to understand what a document contains BEFORE
 extracting specific data from it."

# DAARLIGT -- ingen vejledning om hvornaar
"Analyzes documents."
```

Bemaerk "before extracting specific data" -- dette hjaelper Claude med at
forstaa **raekkefoelgen** af vaerktojer.

**2. Few-shot eksempler i system-prompten**

```python
# Avanceret: Vis agenten et eksempel paa korrekt adfaerd
SYSTEM_PROMPT = """...
Example workflow:
Task: "Find all dates in this contract"
1. First, I'll analyze the document to understand its structure
   -> analyze_document(text="...", focus="legal")
2. Then I'll extract the specific date fields
   -> extract_data(text="...", fields=["effective_date", "expiration_date"])
3. Finally, I'll summarize the findings
..."""
```

**3. Toneangivelse og graenser**

```python
# Definer hvad agenten IKKE maa goere
"Never make up data that wasn't in the original document.
 If you can't find the requested information, say so explicitly."
```

---

## 9. Fejlhaandtering i agent-loops

Robuste agenter skal haandtere tre typer fejl:

### 1. Max iterations (uendelig loop-beskyttelse)

```python
def run(self, task: str, max_iterations: int = 10) -> str:
    for _ in range(max_iterations):
        # ... agent loop ...
        pass

    # Sikkerhedsgraense naaet -- agenten gik i ring
    return "Agent reached maximum iterations without completing the task."
```

**Hvorfor:** Uden denne graense kunne agenten kalde vaerktojer i det uendelige, bruge tokens og koste penge.

**Typisk vaerdi:** 5-20 iterationer afhaengig af opgavens kompleksitet.

### 2. Vaerktojfejl (tool execution failures)

```python
def _execute_tool(self, name: str, params: dict) -> dict:
    handler = self.tool_handlers.get(name)

    # Fejl 1: Ukendt vaerktoj (Claude hallucinerede et vaerktojnavn)
    if handler is None:
        return {"error": f"Unknown tool: {name}"}

    try:
        return handler(**params)
    except Exception as e:
        # Fejl 2: Vaerktojet crashede (forkerte parametre, runtime-fejl)
        return {"error": f"Tool '{name}' failed: {str(e)}"}
```

**Noegle-design:** Fejl returneres som **data** (en dict med `"error"`-noegle), ikke som exceptions. Dette giver Claude mulighed for at **se fejlen og proeve en anden tilgang**.

### 3. API-fejl (netvaerksproblemer, rate limits)

```
┌─────────────────────────────────────────────────────┐
│              FEJLHAANDTERINGS-HIERARKI               │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Niveau 1: Tool-fejl (handler returnerer error)     │
│  -> Claude ser fejlen og justerer                   │
│  -> Eksempel: "Unknown tool: spell_check"           │
│                                                     │
│  Niveau 2: Max iterations (loop-graense)            │
│  -> Tvunget stop, returnerer besked                 │
│  -> Eksempel: Agenten gik i ring                    │
│                                                     │
│  Niveau 3: API-fejl (HTTP/netvaerk)                 │
│  -> Retry med exponential backoff                   │
│  -> Eksempel: Rate limit (429), timeout             │
│                                                     │
│  Niveau 4: Uventet stop_reason                      │
│  -> Returnerer hvad vi har                          │
│  -> Eksempel: "max_tokens" stop                     │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Best Practices for fejlhaandtering

| Problem | Loesning | Implementeret i projektet? |
|---------|----------|---------------------------|
| Uendelig loop | `max_iterations` parameter | Ja (default: 10) |
| Ukendt vaerktoj | Return error dict | Ja |
| Tool-crash | try/except med error dict | Ja |
| API rate limit | Exponential backoff retry | Naeste fase |
| Timeout | Request timeout + fallback | Naeste fase |
| Token-overloeb | Truncate/summarize historik | Naeste fase |

---

## 10. Virkelige anvendelser

### Dokumentanalyse (som vores projekt)

```
Bruger: "Analyseer denne kontrakt og find alle deadlines"

Agent:
  1. analyze_document(text=kontrakt, focus="legal")
  2. extract_data(text=kontrakt, fields=["deadline", "due_date", "expiration"])
  3. summarize(text=resultater, format="bullets")

Resultat: Struktureret liste af deadlines med kontekst
```

### Data Pipelines

```
Agent orkesterer:
  1. Hent data fra API
  2. Valideer mod skema
  3. Transformer til output-format
  4. Skriv rapport

Fordel vs. script: Agenten kan haandtere uventede dataformater
```

### Kundesupport

```
Agent med vaerktojer:
  - search_knowledge_base(query)
  - lookup_customer(id)
  - create_ticket(details)
  - escalate(reason)

Agenten beslutter SELV hvornaar der skal eskaleres baseret paa
kundens problem og tilgaengelig information.
```

### Kodegenerering

```
Agent med vaerktojer:
  - read_file(path)
  - write_file(path, content)
  - run_tests()
  - search_codebase(query)

Eksempel: Claude Code er en hierarkisk agent der kan laese,
skrive, soege og koere kode.
```

---

## 11. Columbus-relevans: AI-agenter i enterprise consulting

Columbus er et nordisk konsulenthus specialiseret i digital transformation med Microsoft Dynamics 365, dataplatforme og AI-loesninger. Her er hvordan AI-agenter passer ind:

### Use Cases for Columbus-kunder

| Omraade | Agent-anvendelse | Vaerdi |
|---------|-----------------|-------|
| **ERP-integration** | Agent der analyserer data mellem Dynamics 365 og externe systemer | Automatisk datafejlsoegning |
| **Dataplatforme** | Agent der orkestrerer ETL-pipelines og haandterer data-kvalitet | Intelligent databehandling |
| **Kundeservice** | Agent med adgang til CRM, vidensbase og eskaleringsvaerktojer | Hurtigere sagsbehandling |
| **Supply chain** | Agent der analyserer leverandoerdata og forudsiger forsinkelser | Proaktiv risikostyring |
| **Rapportering** | Agent der genererer Power BI-dashboards fra naturligt sprog | Demokratiseret dataindsigt |

### Hvordan en Columbus-konsulent bruger denne viden

```
┌──────────────────────────────────────────────────────┐
│         FRA AI-AGENT-VIDEN TIL KONSULENTVAERDI       │
├──────────────────────────────────────────────────────┤
│                                                      │
│  1. FORSTAA KLIENTENS PROBLEM                        │
│     "Vi bruger for meget tid paa manual data-        │
│      validering mellem systemer"                     │
│                                                      │
│  2. DESIGNEER AGENT-LOESNING                         │
│     - Hvilke vaerktojer skal agenten have?            │
│     - Hvilken arkitektur (single/multi/hierarkisk)?  │
│     - Hvad er fejlscenarierme?                       │
│                                                      │
│  3. IMPLEMENTEER MED KENDTE MOENESTRE                │
│     - ReAct-loop for beslutningstagning              │
│     - Tool calling for systemintegration             │
│     - Prompt engineering for domaene-viden           │
│                                                      │
│  4. LEVER VAERDI                                     │
│     - Reduceret manuelt arbejde                      │
│     - Hoejere datakvalitet                           │
│     - Skalerbar loesning                             │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### Copilot Studio vs. Custom Agents

Microsoft investerer massivt i Copilot Studio, som lader virksomheder bygge agenter med lav-kode-vaerktojer. Som Columbus-konsulent med dyb agent-forstaaelse kan du:

1. **Raadgive** om hvornaar Copilot Studio er nok vs. custom agent
2. **Designe** tool-skemaer der integrerer med Dynamics 365
3. **Fejlsoege** agent-adfaerd (fordi du forstaar loopet, tool selection, prompts)
4. **Optimere** performance (faerre iterationer, bedre tool-beskrivelser)

---

## 12. Forstaelsessporgsmaal

### Grundlaeggende (Niveau 1)

1. Hvad er den primaere forskel mellem en chatbot og en AI-agent?

2. Forklar med dine egne ord hvad ReAct-monsteret er, og hvorfor det er nyttigt.

3. Hvad er de tre obligatoriske felter i en tool-definition, og hvad bruges de til?

4. Hvad sker der naar `stop_reason` er `"tool_use"` vs. `"end_turn"`?

### Mellemliggende (Niveau 2)

5. I `agent.py`, hvorfor sender vi tool-resultater som `"role": "user"` i stedet for `"role": "assistant"`? (Hint: taenk paa Claude API'ets beskedformat)

6. Forklar hvorfor tool-beskrivelsen er vigtigere end tool-navnet for agentens adfaerd. Giv et eksempel paa en daarlig vs. god beskrivelse.

7. Hvad ville der ske hvis vi fjernede `max_iterations`-parameteren fra `run()`-metoden? Beskriv et scenarie hvor dette ville vaere problematisk.

8. Sammenlign single-agent og hierarkisk arkitektur. Hvornaar ville du vaelge den ene over den anden?

### Avancerede (Niveau 3)

9. Du skal designe en agent der kan haandtere kundesupport for en webshop. Beskriv:
   - Hvilke vaerktojer agenten skal have (min. 4)
   - System-prompten (skitseer hovedpunkterne)
   - Fejlscenarier og hvordan de haandteres

10. I projektet returnerer `_execute_tool()` fejl som dictionaries i stedet for at raise exceptions. Hvad er fordelen ved dette design, og hvad er den potentielle ulempe?

11. Forestil dig at du skal tilfoeje et nyt vaerktoj `translate_text` til projektet. Beskriv praecist hvilke filer du skal aendre, og vis pseudo-kode for tool-definitionen og handleren.

12. En Columbus-kunde vil automatisere kvalitetskontrol af produktdata i Dynamics 365. Design en agent-arkitektur (vaelg moenstre, definer vaerktojer, beskriv loopet) der loser dette problem.

---

## Opsummering

```
┌──────────────────────────────────────────────────────────┐
│                    NOEGLE-TAKEAWAYS                       │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  1. En AI-agent = LLM + vaerktojer + beslutningsloop     │
│                                                          │
│  2. ReAct = Think -> Act -> Observe -> Repeat            │
│                                                          │
│  3. Tool calling: Claude laeer tool-beskrivelser og      │
│     vaelger det rette vaerktoj baseret paa opgaven       │
│                                                          │
│  4. God tool-design (klar description, praecis schema)   │
│     = bedre agent-adfaerd                                │
│                                                          │
│  5. Agent-loopet: messages vokser for hver iteration     │
│     med assistant + tool_result par                      │
│                                                          │
│  6. Fejlhaandtering er kritisk: max_iterations,          │
│     error dicts, API retry                               │
│                                                          │
│  7. Arkitektur-valg (single/multi/hierarkisk) afhaenger  │
│     af opgavens kompleksitet                             │
│                                                          │
│  8. Enterprise-vaerdi: Konsulenter der forstaar agenter  │
│     kan designe bedre AI-loesninger for kunder           │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

> **Naeste skridt:** Proev at koere `python -m agent.main "Analyze this text and extract key metrics"` i `ai-automation-agent` projektet og observer agent-loopet i praksis.
