# AI Automation Agent

En AI-drevet automationsagent der demonstrerer **agentarkitektur**, **tool calling** og **workflow-automatisering** med Python og TypeScript.

Projektet viser hvordan en AI-agent kan automatisere forretningsopgaver – fra dokumentanalyse og dataudtræk til rapportering via en automationspipeline.

## Hvad gør programmet?

Programmet består af to dele der arbejder sammen:

1. **AI-agenten** (Python) modtager en opgave i naturligt sprog, ræsonnerer om hvilke tools der skal bruges, kalder dem og sammenfatter resultaterne
2. **Automationspipelinen** (TypeScript) henter data fra API'er, transformerer det i flere trin og producerer struktureret output

Agenten kan trigge pipelinen, og pipelinen kan føde resultater tilbage til agenten – en komplet feedback-loop fra opgave til rapport.

### Eksempel

```bash
# Kør AI-agenten med en opgave
python -m agent.main "Analysér dette dokument og udtræk nøgletal"
```

Agenten vil:
1. Analysere dokumentet (type, struktur, entiteter)
2. Trække strukturerede data ud (nøgle-værdi, tabeller, lister)
3. Sammenfatte resultaterne i en rapport

```bash
# Kør automationspipelinen direkte
cd automation && npm start
```

Pipelinen vil:
1. Hente data fra en REST API
2. Rense og transformere data (fjern null-værdier, dedupliker, filtrer)
3. Aggregere resultater grupperet efter bruger
4. Formatere output som markdown-tabel

## Arkitektur

```
┌──────────────────────────────────────────────────────────────┐
│                      Bruger / Trigger                        │
└─────────────────────────────┬────────────────────────────────┘
                              │
                              v
┌──────────────────────────────────────────────────────────────┐
│                     AI Agent (Python)                         │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐ │
│  │ Agentkerne   │  │ Tool Router  │  │ Prompt-skabeloner   │ │
│  │ (ReAct-loop) │──│ (Vælger og   │  │ (Systemprompts,     │ │
│  │              │  │  eksekverer  │  │  few-shot examples) │ │
│  └─────────────┘  │  tools)      │  └─────────────────────┘ │
│                    └──────┬───────┘                           │
│                           │                                   │
│  ┌────────────┐  ┌───────┴──────┐  ┌───────────────────┐    │
│  │ Analysér   │  │ Udtræk       │  │ Opsummér          │    │
│  │ dokument   │  │ data         │  │ rapport           │    │
│  └────────────┘  └──────────────┘  └───────────────────┘    │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               v
┌──────────────────────────────────────────────────────────────┐
│                Automationspipeline (TypeScript)                │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐ │
│  │ Connectors  │──│ Transforms   │──│ Output              │ │
│  │ (API/Fil)   │  │ (Rens/Map)   │  │ (Rapport/Notif.)    │ │
│  └─────────────┘  └──────────────┘  └─────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

**Agent** (Python): Modtager en opgave, ræsonnerer om hvilke tools der skal bruges, kalder dem og sammenfatter resultaterne. Bruger ReAct-mønsteret (Reasoning + Acting) med iterativ beslutningslogik.

**Automationspipeline** (TypeScript): Orkestrerer datatransformationer i flere trin – henter fra API'er, renser og transformerer data, og producerer struktureret output med fuld typesikkerhed via Zod.

**Integration**: Agenten kan trigge automationspipelines via `run_pipeline`-toolet, og pipelineresultater fødes tilbage til agenten for videre analyse.

## Hvad projektet demonstrerer

| Kompetence | Teknologi | Placering |
|------------|-----------|-----------|
| AI-agentarkitektur (ReAct-loop) | Python, Claude API | `agent/` |
| Tool calling og beslutningslogik | Anthropic SDK, function tools | `agent/tools/` |
| Automationsworkflows | TypeScript, Node.js | `automation/` |
| API-integration med retry og fejlhåndtering | REST, Zod-validering | `automation/connectors/` |
| Test (79 tests) | pytest, vitest | `tests/` |
| CI/CD | GitHub Actions | `.github/workflows/` |

## Kom i gang

### Forudsætninger

- Python 3.11+
- Node.js 20+
- En Anthropic API-nøgle ([hent her](https://console.anthropic.com/))

### Opsætning

```bash
# Klon repoet
git clone https://github.com/SMat777/ai-automation-agent.git
cd ai-automation-agent

# Python-opsætning
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# TypeScript-opsætning
cd automation
npm install
cd ..

# Miljøvariabler
cp .env.example .env
# Tilføj din ANTHROPIC_API_KEY i .env
```

### Kør

```bash
# Kør AI-agenten
python -m agent.main "Analyze this document and extract key metrics"

# Kør automationspipelinen
cd automation && npm start

# Kør end-to-end demo (agent + pipeline)
python demo.py
```

### Test

```bash
# Python-tests
pytest tests/agent/ -v

# TypeScript-tests
cd automation && npm test
```

## Projektstruktur

```
ai-automation-agent/
├── agent/                  # Python – AI Agent
│   ├── main.py             # Indgangspunkt og agentloop
│   ├── agent.py            # Agentkerne med beslutningslogik
│   ├── tools/              # Tool-implementeringer
│   │   ├── analyze.py      # Dokumentanalyse (type, entiteter, nøglepunkter)
│   │   ├── extract.py      # Dataudtræk (nøgle-værdi, tabel, liste)
│   │   ├── summarize.py    # Rapportopsummering
│   │   └── pipeline.py     # Pipeline-trigger tool
│   └── prompts/
│       └── system.py       # Systemprompts
├── automation/             # TypeScript – Automationspipeline
│   ├── src/
│   │   ├── index.ts        # Pipeline-indgangspunkt og demo
│   │   ├── pipeline.ts     # Workflow-orkestrering
│   │   ├── connectors/
│   │   │   └── api.ts      # REST API-connector med retry
│   │   └── transforms/     # Datatransformationer
│   │       ├── clean.ts    # Datarensning og deduplikering
│   │       ├── filter.ts   # Filtrering (range-baseret)
│   │       ├── map.ts      # Feltudvælgelse og berigelse
│   │       ├── aggregate.ts # Gruppering og aggregering
│   │       └── format.ts   # Markdown-formatering
├── docs/
│   ├── ARCHITECTURE.md     # Teknisk arkitekturdokumentation
│   └── LEARNING.md         # Læringsjournal
├── tests/                  # Testsuites
│   ├── agent/              # Python-agenttests (43 tests)
│   └── automation/         # TypeScript-pipelinetests (36 tests)
├── demo.py                 # End-to-end integrationsdemo
├── .github/workflows/
│   └── ci.yml              # CI/CD-pipeline (lint, test, typecheck)
├── requirements.txt        # Python-afhængigheder
├── CONTRIBUTING.md         # Udviklingsworkflow
└── LICENSE                 # MIT
```

## Udviklingsfaser

Projektet er udviklet iterativt i fire faser:

| Fase | Indhold | Tests |
|------|---------|-------|
| **Fase 0** | Projektopsætning, CI/CD, dokumentationsstruktur | — |
| **Fase 1** | Python AI-agentkerne: ReAct-loop, tool calling, retry-logik, dokumentanalyse, dataudtræk | 38 |
| **Fase 2** | TypeScript automationspipeline: REST-connector med retry, 5 composable transforms, pipeline-orkestrering | 36 |
| **Fase 3** | Integration: agent triggerer pipeline, pipeline føder agent, end-to-end demo | 79 total |

## Tech-stack

**Agent (Python)**
- [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python) — Claude API med tool use
- [python-dotenv](https://github.com/theskumar/python-dotenv) — Miljøvariabler
- [pytest](https://docs.pytest.org/) — Test

**Automationspipeline (TypeScript)**
- [TypeScript](https://www.typescriptlang.org/) — Typesikker automatisering
- [tsx](https://github.com/privatenumber/tsx) — TypeScript-eksekvering
- [vitest](https://vitest.dev/) — Hurtig test
- [zod](https://zod.dev/) — Runtime-validering

## Licens

MIT — se [LICENSE](LICENSE) for detaljer.

---

Bygget af [Simon Mathiasen](https://github.com/SMat777) som portfolioprojekt der demonstrerer AI-agentarkitektur og workflow-automatisering.
