# Guide: Python for Java/JavaScript-Udviklere

**Niveau:** Java/JS-erfaren -> Python-kompetent | **Kontekst:** ai-automation-agent + AI-udvikling

---

## HVORFOR PYTHON?

Hvis du kommer fra Java eller JavaScript, er Python det tredje ben i den moderne udviklers trekant. Java giver dig enterprise-arkitektur og typesikkerhed. JavaScript giver dig web og asynkron I/O. Python giver dig AI/ML-oekosystemet, hurtig prototyping og scripts der bare virker. Med 2+ aars erfaring i Java/JS har du allerede de mentale modeller der skal til -- denne guide mapper dem direkte over til Python.

---

## 1. SYNTAX-MAPPING: Java/JS -> Python

### 1.1 Variabler og typer

```java
// Java
String name = "Simon";
int age = 25;
final double PI = 3.14;
List<String> skills = List.of("Java", "JS", "Python");
```

```javascript
// JavaScript
const name = "Simon";
let age = 25;
const PI = 3.14;
const skills = ["Java", "JS", "Python"];
```

```python
# Python
name = "Simon"            # Ingen typeangivelse paakraevet
age = 25                  # Ingen semikolon
PI = 3.14                 # Konvention: UPPERCASE = konstant (men ikke enforced)
skills = ["Java", "JS", "Python"]

# Med type hints (anbefalet i stoerre projekter):
name: str = "Simon"
age: int = 25
skills: list[str] = ["Java", "JS", "Python"]
```

**Noegleforskelle:**
- Ingen semikolon, ingen krølleparenteser -- indentation er syntaks
- Variabler har ingen typedekleration (men kan faa type hints)
- `const`/`final` findes ikke -- brug UPPERCASE-konvention

### 1.2 Funktioner

```java
// Java
public static String greet(String name, int times) {
    return name.repeat(times);
}
```

```javascript
// JavaScript
function greet(name, times = 1) {
    return name.repeat(times);
}
// Eller arrow function:
const greet = (name, times = 1) => name.repeat(times);
```

```python
# Python
def greet(name: str, times: int = 1) -> str:
    return name * times

# Lambda (svarende til arrow function, men kun et udtryk):
greet = lambda name, times=1: name * times
```

**FRA ai-automation-agent -- reel funktionssignatur:**
```python
# Fra agent/tools/analyze.py
def handle_analyze(text: str, focus: str = "general") -> dict:
    """Analyze document structure and extract key points.

    Args:
        text: The document text to analyze.
        focus: Optional focus area for the analysis.

    Returns:
        Dictionary with sections, key_points, and word_count.
    """
    lines = text.strip().split("\n")
    sections = [line.strip() for line in lines if line.strip().startswith("#")]
    return {"sections": sections, "word_count": len(text.split()), "focus": focus}
```

Laeg maerke til:
- Type hints (`str`, `dict`) er valgfrie men anbefalet
- Docstring (tredobbelt anfoerselstegn) erstatter Javadoc/JSDoc
- Default parametre fungerer ligesom i JS

### 1.3 Klasser

```java
// Java
public class Agent {
    private final String apiKey;
    private final String model;

    public Agent(String apiKey, String model) {
        this.apiKey = apiKey;
        this.model = model;
    }

    public String run(String task) {
        // ...
        return result;
    }
}
```

```javascript
// JavaScript
class Agent {
    #apiKey;  // private field
    #model;

    constructor(apiKey, model) {
        this.#apiKey = apiKey;
        this.#model = model;
    }

    run(task) {
        // ...
        return result;
    }
}
```

```python
# Python
class Agent:
    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key    # Konvention: _ = "privat"
        self._model = model

    def run(self, task: str) -> str:
        # ...
        return result
```

**Noegleforskelle:**
- `__init__` er Pythons constructor (svarende til `constructor`/public-constructor)
- `self` er eksplicit foerste parameter i alle instansmetoder (i Java/JS er `this` implicit)
- Ingen access modifiers (`public`/`private`) -- brug `_`-prefix som konvention
- `__double_underscore__` = "dunder methods" (magiske metoder som `__init__`, `__str__`, `__repr__`)

### 1.4 Conditionals og loops

```java
// Java
for (String skill : skills) {
    if (skill.length() > 3) {
        System.out.println(skill.toUpperCase());
    }
}
```

```javascript
// JavaScript
for (const skill of skills) {
    if (skill.length > 3) {
        console.log(skill.toUpperCase());
    }
}
// Eller: skills.filter(s => s.length > 3).forEach(s => console.log(s.toUpperCase()));
```

```python
# Python
for skill in skills:
    if len(skill) > 3:
        print(skill.upper())

# Pythonisk (list comprehension):
[print(skill.upper()) for skill in skills if len(skill) > 3]
```

**Vigtigt:** Python bruger `elif` (ikke `else if`), `and`/`or`/`not` (ikke `&&`/`||`/`!`).

```python
if age >= 18 and not is_banned:
    print("Velkommen")
elif age >= 16:
    print("Begroenset adgang")
else:
    print("Ingen adgang")
```

### 1.5 Fejlhaandtering

```java
// Java
try {
    result = riskyOperation();
} catch (IOException e) {
    logger.error("IO fejl: " + e.getMessage());
} catch (Exception e) {
    logger.error("Generel fejl: " + e.getMessage());
} finally {
    cleanup();
}
```

```javascript
// JavaScript
try {
    result = await riskyOperation();
} catch (error) {
    if (error instanceof TypeError) {
        console.error("Type fejl:", error.message);
    }
} finally {
    cleanup();
}
```

```python
# Python
try:
    result = risky_operation()
except IOError as e:
    logger.error(f"IO fejl: {e}")
except Exception as e:
    logger.error(f"Generel fejl: {e}")
else:
    # Koerer KUN hvis ingen exception (unik for Python!)
    process(result)
finally:
    cleanup()
```

**Python-specifikt:** `else`-blokken i try/except koerer kun hvis ingen exception blev rejst. Det har hverken Java eller JS.

---

## 2. TYPE-SYSTEMET: Tre filosofier

### Java: Statisk og streng
```java
// Kompileringsfejl hvis typer ikke matcher
String name = 42;  // FEJL ved kompilering
```

### JavaScript: Dynamisk og "fleksibel"
```javascript
// Ingen fejl -- implicit type coercion
let name = 42;     // Fine
name = "Simon";    // Ogsaa fine
"5" + 3;           // "53" (string concatenation)
"5" - 3;           // 2 (number subtraction)
```

### Python: Dynamisk men konsistent
```python
# Dynamisk typing -- ingen kompileringsfejl
name = 42         # Fine
name = "Simon"    # Ogsaa fine

# Men INGEN implicit coercion (modsat JS):
"5" + 3           # TypeError! Python tvinger dig til at vaere eksplicit
"5" + str(3)      # "53"
int("5") + 3      # 8
```

### Type Hints i Python (PEP 484)

Type hints er Pythons svar paa Javas typesystem -- men de er frivillige og haandhaeves kun af vaerktoej, ikke af runtime:

```python
# Grundlaeggende type hints
def process_article(title: str, word_count: int) -> dict[str, any]:
    return {"title": title, "words": word_count}

# Komplekse typer
from typing import Optional

def find_user(user_id: int) -> Optional[dict]:
    """Returnerer user dict eller None."""
    ...

# Union types (Python 3.10+)
def parse_input(data: str | dict) -> list[str]:
    ...

# Generics
def first_item(items: list[T]) -> T:
    return items[0]
```

**FRA ai-automation-agent -- type hints i praksis:**
```python
# Fra agent/tools/extract.py
def handle_extract(text: str, fields: list[str]) -> dict:
    extracted: dict[str, str | None] = {}
    for field in fields:
        pattern = rf"(?i){re.escape(field)}[\s:=]+(.+?)(?:\n|$)"
        match = re.search(pattern, text)
        extracted[field] = match.group(1).strip() if match else None
    return {
        "extracted": extracted,
        "fields_found": sum(1 for v in extracted.values() if v is not None),
        "fields_missing": sum(1 for v in extracted.values() if v is None),
    }
```

Laeg maerke til `dict[str, str | None]` -- dette fortaeller mypy at values enten er `str` eller `None`.

**Saadan haandhaeves type hints:**
```bash
# mypy checker typer statisk (som Javas compiler, men optional)
mypy agent/
# Output: agent/tools/extract.py:31: error: Incompatible return type
```

---

## 3. PYTHONISKE IDIOMER

Dette er det der adskiller en "Python-skriver der taenker i Java" fra en reel Python-udvikler.

### 3.1 List Comprehensions

Erstatning for `map`/`filter` i JS og streams i Java:

```java
// Java
List<String> upper = skills.stream()
    .filter(s -> s.length() > 2)
    .map(String::toUpperCase)
    .collect(Collectors.toList());
```

```javascript
// JavaScript
const upper = skills.filter(s => s.length > 2).map(s => s.toUpperCase());
```

```python
# Python -- list comprehension
upper = [s.upper() for s in skills if len(s) > 2]

# Dict comprehension
tool_names = {tool["name"]: tool for tool in TOOLS}

# Set comprehension
unique_lengths = {len(s) for s in skills}
```

**FRA ai-automation-agent:**
```python
# Fra agent/tools/analyze.py -- list comprehensions i reel kode
sections = [line.strip() for line in lines if line.strip().startswith("#")]
paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
key_points = [p[:100] + "..." if len(p) > 100 else p for p in paragraphs[:5]]
```

### 3.2 Generators

Generatorer er "dovne" iteratorer -- de beregner vaerdier on-demand i stedet for at allokere hele listen:

```python
# List comprehension: allokerer HELE listen i hukommelsen
all_words = [word for doc in documents for word in doc.split()]

# Generator expression: beregner en ad gangen (memory-efficient)
all_words = (word for doc in documents for word in doc.split())

# Generator function med yield
def read_large_file(path: str):
    with open(path) as f:
        for line in f:
            yield line.strip()

# Brug det som en iterator
for line in read_large_file("data.csv"):
    process(line)  # Kun en linje i hukommelsen ad gangen
```

**FRA ai-automation-agent -- generator expression:**
```python
# Fra agent/tools/extract.py
"fields_found": sum(1 for v in extracted.values() if v is not None),
"fields_missing": sum(1 for v in extracted.values() if v is None),
```

`sum(1 for v in ...)` er en generator expression -- den taeller uden at lave en midlertidig liste.

### 3.3 Context Managers (with-statement)

Pythons svar paa Javas try-with-resources og JS's... intet direkte equivalent:

```java
// Java (try-with-resources)
try (var reader = new BufferedReader(new FileReader("data.txt"))) {
    String line = reader.readLine();
}  // reader lukkes automatisk
```

```python
# Python (context manager)
with open("data.txt") as reader:
    line = reader.readline()
# reader lukkes automatisk

# Du kan lave dine egne:
from contextlib import contextmanager

@contextmanager
def timer(label: str):
    import time
    start = time.time()
    yield  # Her koerer koden inde i "with"-blokken
    elapsed = time.time() - start
    print(f"{label}: {elapsed:.2f}s")

with timer("API call"):
    response = call_api()
```

### 3.4 Decorators

Dekoratorer er Pythons svar paa Java-annotationer + AOP, og JS-dekoratorer (Stage 3):

```python
# En dekorator er bare en funktion der wrapper en anden funktion
def log_call(func):
    def wrapper(*args, **kwargs):
        print(f"Kalder {func.__name__} med {args}, {kwargs}")
        result = func(*args, **kwargs)
        print(f"{func.__name__} returnerede {result}")
        return result
    return wrapper

@log_call
def handle_analyze(text: str, focus: str = "general") -> dict:
    ...

# Svarer til:
# handle_analyze = log_call(handle_analyze)
```

Almindelige built-in dekoratorer:
```python
class ArticleService:
    @staticmethod            # Javas static method
    def validate(text: str) -> bool:
        return len(text) > 0

    @classmethod             # Factory methods
    def from_config(cls, config: dict) -> "ArticleService":
        return cls(**config)

    @property                # Javas getter
    def word_count(self) -> int:
        return len(self._text.split())
```

### 3.5 F-strings (formatterede strenge)

```java
// Java
String msg = String.format("Hej %s, du er %d aar", name, age);
// Eller: "Hej " + name + ", du er " + age + " aar"
```

```javascript
// JavaScript
const msg = `Hej ${name}, du er ${age} aar`;
```

```python
# Python f-string (bedste maade)
msg = f"Hej {name}, du er {age} aar"

# Med udtryk:
msg = f"Opgaven har {len(tasks)} elementer"

# Med formattering:
msg = f"Pris: {price:.2f} kr"

# Debug-mode (Python 3.8+):
print(f"{name=}")  # Output: name='Simon'
```

**FRA ai-automation-agent:**
```python
# Fra agent/main.py
print(f"Task: {task}\n")
```

---

## 4. PAKKEHAANDTERING: pip vs npm vs Maven

### Sammenligning

| Koncept          | Java (Maven)           | JavaScript (npm)      | Python (pip)              |
|-----------------|------------------------|----------------------|---------------------------|
| Package manager | `mvn`                  | `npm` / `yarn`       | `pip`                     |
| Manifest        | `pom.xml`              | `package.json`       | `requirements.txt` / `pyproject.toml` |
| Lock file       | (implicit i pom)       | `package-lock.json`  | `requirements.txt` (pinned) |
| Install deps    | `mvn install`          | `npm install`        | `pip install -r requirements.txt` |
| Add dep         | Edit `pom.xml`         | `npm install pkg`    | `pip install pkg`         |
| Local env       | (global .m2 cache)     | `node_modules/`      | `venv/` (virtual environment) |
| Run scripts     | `mvn exec:java`        | `npm run start`      | `python -m module.name`   |

### Virtual Environments (venv)

Python har IKKE `node_modules`-style isolation som default. Uden venv installerer `pip` pakker globalt. Brug ALTID venv:

```bash
# Opret virtual environment (som npm init + node_modules)
python -m venv .venv

# Aktiver det (vigtigt! -- ellers installerer pip globalt)
source .venv/bin/activate       # macOS/Linux
# .venv\Scripts\activate        # Windows

# Nu er pip isoleret til dette projekt
pip install anthropic python-dotenv

# Gem dependencies (som npm package-lock.json)
pip freeze > requirements.txt

# En anden udvikler installerer:
pip install -r requirements.txt

# Deaktiver naar du er faerdig
deactivate
```

**FRA ai-automation-agent -- requirements.txt:**
```
# AI Agent dependencies
anthropic>=0.42.0
python-dotenv>=1.0.0

# Development & testing
pytest>=8.0.0
ruff>=0.8.0
mypy>=1.13.0
```

`>=0.42.0` er version pinning -- svarende til `"anthropic": "^0.42.0"` i package.json.

---

## 5. PROJEKTSTRUKTUR: Moduler og Pakker

### Java-tankegang -> Python-mapping

```
// Java
src/main/java/com/example/agent/
    Agent.java
    tools/
        AnalyzeTool.java
        ExtractTool.java
```

```
# Python (ai-automation-agent)
agent/
    __init__.py          # Goer mappen til en "pakke" (som package-info.java)
    main.py              # Entry point
    agent.py             # Agent-klassen
    prompts/
        __init__.py      # Goer prompts/ til en subpakke
        system.py
    tools/
        __init__.py      # Eksporterer TOOLS og TOOL_HANDLERS
        analyze.py
        extract.py
        summarize.py
tests/
    __init__.py
    agent/
        __init__.py
        test_tools.py
        test_agent.py
requirements.txt
```

### Hvad er `__init__.py`?

Det er filen der goer en mappe til en Python-pakke. Den koerer naar du importerer pakken:

```python
# agent/tools/__init__.py fra ai-automation-agent:
"""Agent tools -- functions the AI agent can call to accomplish tasks."""

from agent.tools.analyze import ANALYZE_TOOL, handle_analyze
from agent.tools.extract import EXTRACT_TOOL, handle_extract
from agent.tools.summarize import SUMMARIZE_TOOL, handle_summarize

# Registry of all available tools
TOOLS = [ANALYZE_TOOL, EXTRACT_TOOL, SUMMARIZE_TOOL]

TOOL_HANDLERS = {
    "analyze_document": handle_analyze,
    "extract_data": handle_extract,
    "summarize": handle_summarize,
}

__all__ = ["TOOLS", "TOOL_HANDLERS"]
```

**Hvad sker der her:**
- Imports samler sub-modulernes exports i et centralt sted
- `TOOLS` og `TOOL_HANDLERS` er registries (et common Python-pattern)
- `__all__` definerer hvad `from agent.tools import *` eksporterer (som `module.exports` i JS)

### Import-systemet

```python
# Absolut import (anbefalet)
from agent.tools import TOOLS, TOOL_HANDLERS
from agent.tools.analyze import handle_analyze

# Relativ import (inden for samme pakke)
from .analyze import handle_analyze        # Fra samme pakke
from ..prompts import AGENT_SYSTEM_PROMPT  # Fra foraelder-pakke

# Svarende til i JS:
# import { TOOLS } from './tools/index.js';
# import { handleAnalyze } from './tools/analyze.js';
```

### Koere et modul

```bash
# I stedet for: node index.js
python -m agent.main "Analyze this document"

# -m flaget fortaeller Python: "kig i agent/main.py og koer det"
# Det svarer til at Maven/Gradle koerer main-klassen
```

---

## 6. ALMINDELIGE GOTCHAS

### 6.1 Mutable Default Arguments (FARLIGT!)

```python
# FEJL -- listen deles mellem alle kald!
def add_item(item: str, items: list = []) -> list:
    items.append(item)
    return items

print(add_item("a"))  # ['a']
print(add_item("b"))  # ['a', 'b'] -- HVAD?! Listen husker!

# KORREKT -- brug None som default
def add_item(item: str, items: list | None = None) -> list:
    if items is None:
        items = []
    items.append(item)
    return items
```

**Forklaring:** Default-vaerdier evalueres EN gang naar funktionen defineres, ikke ved hvert kald. Mutable objekter (lister, dicts) genbruges, saa de akkumulerer data. I Java og JS evalueres defaults ved hvert kald, saa dette problem findes ikke.

### 6.2 Indentation er syntaks

```python
# FEJL -- blander tabs og spaces
def my_func():
    x = 1       # 4 spaces
	y = 2       # 1 tab -- IndentationError!

# Python enforcer konsistent indentation. Brug ALTID 4 spaces.
# Konfigurer din editor til at konvertere tabs -> spaces.
```

I Java/JS er indentation kun kosmetisk. I Python er det lovpligtigt. Dit program koerer simpelthen ikke med forkert indentation.

### 6.3 GIL (Global Interpreter Lock)

```python
# Python (CPython) har en GIL der begraenser threads til en ad gangen
# Det betyder at CPU-tunge opgaver IKKE faar speedup fra threading

# FORKERT tilgang for CPU-arbejde:
import threading
# Threads hjaelper IKKE med parallel beregning i Python

# KORREKT for CPU-arbejde: multiprocessing
from multiprocessing import Pool
with Pool(4) as p:
    results = p.map(heavy_computation, data)

# Threads er fine til I/O (netvaerkskald, filer):
import asyncio
async def fetch_all(urls: list[str]):
    async with aiohttp.ClientSession() as session:
        tasks = [session.get(url) for url in urls]
        return await asyncio.gather(*tasks)
```

**Java-sammenligning:** Java har aekte multi-threading. Python fakes det for CPU-arbejde men er fine til I/O.
**JS-sammenligning:** JS er single-threaded som Python, men bruger event loop (async/await) -- Python har det samme via `asyncio`.

### 6.4 Equality: `==` vs `is`

```python
# == sammenligner vaerdi (som Java's .equals())
# is sammenligner identitet (som Java's ==)

a = [1, 2, 3]
b = [1, 2, 3]
a == b   # True  (samme vaerdi)
a is b   # False (forskellige objekter i hukommelsen)

# Brug altid "is" med None:
if result is None:     # KORREKT
    ...
if result == None:     # Fungerer, men er anti-pattern
    ...
```

### 6.5 Slicing (findes ikke i Java/JS paa denne maade)

```python
skills = ["Java", "JS", "Python", "SQL", "React"]

skills[1:3]     # ["JS", "Python"]     -- index 1 til 3 (eksklusiv)
skills[:2]      # ["Java", "JS"]       -- fra start til index 2
skills[-2:]     # ["SQL", "React"]     -- de sidste 2
skills[::2]     # ["Java", "Python", "React"]  -- hvert 2. element
skills[::-1]    # ["React", "SQL", "Python", "JS", "Java"]  -- reversed

# Ogsaa paa strings:
"Hello World"[6:]   # "World"
```

### 6.6 Truthy/Falsy

```python
# Falsy i Python (anderledes end JS!):
# None, False, 0, 0.0, "", [], {}, set()

# I JS er [] og {} truthy -- i Python er de falsy!
if []:
    print("Aldrig")   # Tom liste er falsy

# Pythonisk check for tom collection:
if skills:              # Bedre end: if len(skills) > 0
    process(skills)

if not errors:          # Bedre end: if len(errors) == 0
    print("Ingen fejl")
```

---

## 7. DEV TOOLS

### 7.1 Ruff (Linting + Formattering)

Ruff erstatter baaede ESLint/Prettier (JS) og Checkstyle (Java):

```bash
# Installer
pip install ruff

# Lint (finder fejl og style-problemer)
ruff check .

# Auto-fix
ruff check --fix .

# Formatering (som Prettier)
ruff format .
```

Ruff er skrevet i Rust og er 10-100x hurtigere end aeldrePython-linters (flake8, black, isort). Det er den anbefalede standard i 2025+.

### 7.2 Mypy (Statisk Typecheck)

Mypy goer Python mere som Java -- det checker dine type hints:

```bash
# Koer typecheck
mypy agent/

# Eksempel output:
# agent/tools/extract.py:31: error: Incompatible types in assignment
```

```python
# mypy fanger denne fejl:
def process(items: list[str]) -> int:
    return items  # error: Incompatible return value type (got "list[str]", expected "int")
```

**Tip:** Start med `mypy --strict` paa nye projekter. Paa eksisterende kode, brug gradvis adoption med `# type: ignore` kommentarer.

### 7.3 Pytest (Testing)

Pytest er Pythons JUnit/Jest -- men simplere:

```java
// Java (JUnit)
@Test
public void testWordCount() {
    Result result = handleAnalyze("Hello world");
    assertEquals(2, result.getWordCount());
}
```

```javascript
// JavaScript (Jest)
test('counts words', () => {
    const result = handleAnalyze("Hello world");
    expect(result.wordCount).toBe(2);
});
```

```python
# Python (pytest) -- ingen klasse paakraevet, ingen boilerplate
def test_counts_words():
    result = handle_analyze("Hello world")
    assert result["word_count"] == 2
```

**FRA ai-automation-agent -- reelle tests:**
```python
# Fra tests/agent/test_tools.py
class TestAnalyzeTool:
    def test_counts_words(self) -> None:
        result = handle_analyze("Hello world this is a test")
        assert result["word_count"] == 6

    def test_finds_sections(self) -> None:
        text = "# Header 1\nSome text\n# Header 2\nMore text"
        result = handle_analyze(text)
        assert len(result["sections"]) == 2
        assert result["sections"][0] == "# Header 1"

    def test_respects_focus(self) -> None:
        result = handle_analyze("Some text", focus="financial")
        assert result["focus"] == "financial"

class TestExtractTool:
    def test_extracts_field(self) -> None:
        text = "Company: Columbus Global\nLocation: Aarhus"
        result = handle_extract(text, fields=["Company", "Location"])
        assert result["extracted"]["Company"] == "Columbus Global"
        assert result["extracted"]["Location"] == "Aarhus"

    def test_reports_missing_fields(self) -> None:
        text = "Company: Columbus Global"
        result = handle_extract(text, fields=["Company", "Revenue"])
        assert result["fields_found"] == 1
        assert result["fields_missing"] == 1
        assert result["extracted"]["Revenue"] is None
```

**Koer tests:**
```bash
# Alle tests
pytest

# Med verbose output
pytest -v

# Specifik testfil
pytest tests/agent/test_tools.py

# Specifik testklasse/-funktion
pytest tests/agent/test_tools.py::TestAnalyzeTool::test_counts_words

# Med coverage
pytest --cov=agent
```

**Noegleforskelle fra JUnit/Jest:**
- Bare `assert` -- ingen `assertEquals`, `expect().toBe()` osv.
- Pytest opdager automatisk filer der hedder `test_*.py` og funktioner der hedder `test_*`
- Fixtures erstatter `@Before`/`beforeEach`:

```python
import pytest

@pytest.fixture
def sample_text():
    return "# Title\nFirst paragraph.\n\nSecond paragraph."

def test_analyze_with_fixture(sample_text):
    result = handle_analyze(sample_text)
    assert result["paragraph_count"] == 2
```

---

## 8. PATTERNS FRA AI-AUTOMATION-AGENT

### 8.1 Tool Registry Pattern

```python
# agent/tools/__init__.py
TOOLS = [ANALYZE_TOOL, EXTRACT_TOOL, SUMMARIZE_TOOL]

TOOL_HANDLERS = {
    "analyze_document": handle_analyze,
    "extract_data": handle_extract,
    "summarize": handle_summarize,
}
```

I Java ville dette vaere et `Map<String, Function>` eller et Strategy-pattern med interfaces. I Python er funktioner foersteklasses-objekter, saa du kan bare putte dem i en dict:

```python
# Kald en tool handler dynamisk
tool_name = "analyze_document"
handler = TOOL_HANDLERS[tool_name]
result = handler(text="some text", focus="technical")
```

**JS-equivalent:**
```javascript
const TOOL_HANDLERS = {
    analyze_document: handleAnalyze,
    extract_data: handleExtract,
};
const result = TOOL_HANDLERS[toolName](text, focus);
```

### 8.2 Dict som "struct" / lightweight objekt

Python bruger ofte dicts hvor Java bruger klasser og JS bruger plain objects:

```python
# Fra agent/tools/analyze.py
ANALYZE_TOOL = {
    "name": "analyze_document",
    "description": "Analyze a document to extract its structure...",
    "input_schema": {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "The document text to analyze"},
            "focus": {"type": "string", "default": "general"},
        },
        "required": ["text"],
    },
}
```

**Alternativ med dataclass (mere Java-agtigt):**
```python
from dataclasses import dataclass

@dataclass
class ToolResult:
    sections: list[str]
    paragraph_count: int
    word_count: int
    focus: str
    key_points: list[str]
```

### 8.3 Environment Variables med python-dotenv

```python
# Fra agent/main.py
from dotenv import load_dotenv

load_dotenv()  # Loader .env fil (som dotenv i Node.js)

api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    print("Error: ANTHROPIC_API_KEY not set.")
    sys.exit(1)

model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")  # Default vaerdi
```

### 8.4 `if __name__ == "__main__"` idiom

```python
# Fra agent/main.py
if __name__ == "__main__":
    main()
```

Denne linje sikrer at `main()` KUN koerer naar filen eksekveres direkte (`python main.py`), ikke naar den importeres (`from agent.main import main`). Det er Pythons svar paa:

```java
// Java
public static void main(String[] args) { ... }
```

```javascript
// Node.js (CommonJS)
if (require.main === module) { main(); }
// ES Modules har ingen direkte equivalent
```

---

## 9. QUICK REFERENCE: Java/JS -> Python

| Koncept           | Java                        | JavaScript             | Python                        |
|-------------------|-----------------------------|------------------------|-------------------------------|
| Print             | `System.out.println(x)`     | `console.log(x)`      | `print(x)`                   |
| String format     | `String.format("%s", x)`    | `` `${x}` ``          | `f"{x}"`                     |
| Null/None         | `null`                      | `null` / `undefined`  | `None`                       |
| Array/List        | `ArrayList<T>`              | `[]`                  | `[]` (list)                  |
| Map/Object/Dict   | `HashMap<K,V>`              | `{}`                  | `{}` (dict)                  |
| Set               | `HashSet<T>`                | `new Set()`           | `set()` / `{1, 2, 3}`       |
| Tuple             | (ingen built-in)            | (ingen built-in)      | `(1, 2, 3)` (immutable)     |
| Ternary           | `x ? a : b`                 | `x ? a : b`           | `a if x else b`             |
| For-each          | `for (var x : list)`        | `for (const x of list)` | `for x in list:`           |
| Enumerate         | Manual counter              | `list.forEach((x,i))` | `for i, x in enumerate(list):` |
| Range loop        | `for (int i=0; i<n; i++)`   | `for (let i=0; i<n; i++)` | `for i in range(n):`    |
| String multiply   | `"x".repeat(3)`             | `"x".repeat(3)`       | `"x" * 3`                   |
| Check contains    | `list.contains(x)`          | `list.includes(x)`    | `x in list`                 |
| Lambda            | `(x) -> x * 2`              | `(x) => x * 2`        | `lambda x: x * 2`           |
| Interface         | `interface Runnable`         | (ingen)               | `ABC` (abstract base class) |
| Enum              | `enum Color { RED }`         | Ingen native          | `from enum import Enum`     |
| Package/Module    | `package com.example`        | `import/export`       | `__init__.py` + `import`    |

---

## 10. PRAKTISKE OEVELSER

### Oevelse 1: Refaktorer fra Java-stil til Pythonisk

Omskriv denne Java-inspirerede kode til idiomatisk Python:

```python
# Java-stil (FOER)
def get_long_skills(skills_list):
    result = []
    for i in range(len(skills_list)):
        skill = skills_list[i]
        if len(skill) > 3:
            result.append(skill.upper())
    return result
```

<details>
<summary>Loesning</summary>

```python
# Pythonisk (EFTER)
def get_long_skills(skills: list[str]) -> list[str]:
    return [skill.upper() for skill in skills if len(skill) > 3]
```
</details>

### Oevelse 2: Byg en tool handler

Lav en ny tool handler til ai-automation-agent der taeller ord per sektion:

```python
# Udfyld denne funktion
def handle_word_count(text: str, per_section: bool = False) -> dict:
    """Count words in text, optionally per section.

    Args:
        text: The text to count words in.
        per_section: If True, count words per markdown section.

    Returns:
        Dictionary with total and optional per-section counts.
    """
    # Din kode her
    pass
```

<details>
<summary>Loesning</summary>

```python
def handle_word_count(text: str, per_section: bool = False) -> dict:
    total = len(text.split())
    result: dict = {"total_words": total}

    if per_section:
        sections: dict[str, int] = {}
        current_section = "intro"
        current_words: list[str] = []

        for line in text.split("\n"):
            if line.strip().startswith("#"):
                if current_words:
                    sections[current_section] = len(current_words)
                current_section = line.strip().lstrip("# ").strip()
                current_words = []
            else:
                current_words.extend(line.split())

        if current_words:
            sections[current_section] = len(current_words)

        result["per_section"] = sections

    return result
```
</details>

### Oevelse 3: Skriv pytest-tests

Skriv tests til din `handle_word_count` funktion:

```python
# Skriv mindst 4 tests:
# 1. Test simpel ordtaelling
# 2. Test per-section taelling
# 3. Test tom string
# 4. Test tekst uden sektioner med per_section=True
```

<details>
<summary>Loesning</summary>

```python
class TestWordCount:
    def test_simple_count(self) -> None:
        result = handle_word_count("Hello world foo bar")
        assert result["total_words"] == 4

    def test_per_section(self) -> None:
        text = "# Intro\nHello world\n# Details\nFoo bar baz"
        result = handle_word_count(text, per_section=True)
        assert result["per_section"]["Intro"] == 2
        assert result["per_section"]["Details"] == 3

    def test_empty_string(self) -> None:
        result = handle_word_count("")
        assert result["total_words"] == 0

    def test_no_sections_with_per_section(self) -> None:
        result = handle_word_count("Just plain text", per_section=True)
        assert "intro" in result["per_section"]
        assert result["per_section"]["intro"] == 3
```
</details>

### Oevelse 4: Opsaet et Python-projekt fra scratch

```bash
# 1. Opret projektstruktur
mkdir my-ai-tool && cd my-ai-tool
python -m venv .venv
source .venv/bin/activate

# 2. Installer dependencies
pip install anthropic python-dotenv pytest ruff mypy

# 3. Gem dependencies
pip freeze > requirements.txt

# 4. Opret pakkestruktur
mkdir -p my_tool/utils tests
touch my_tool/__init__.py my_tool/main.py my_tool/utils/__init__.py
touch tests/__init__.py tests/test_main.py

# 5. Tilfoej .gitignore
echo ".venv/\n__pycache__/\n*.pyc\n.env\n.mypy_cache/" > .gitignore

# 6. Koer vaerktoej
ruff check .
mypy my_tool/
pytest
```

### Oevelse 5: Konverter en JS async-funktion til Python

```javascript
// JavaScript
async function fetchArticles(urls) {
    const results = [];
    for (const url of urls) {
        try {
            const response = await fetch(url);
            const data = await response.json();
            results.push({ url, title: data.title, status: 'ok' });
        } catch (error) {
            results.push({ url, title: null, status: 'error' });
        }
    }
    return results;
}
```

<details>
<summary>Loesning</summary>

```python
import aiohttp
import asyncio

async def fetch_articles(urls: list[str]) -> list[dict]:
    results = []
    async with aiohttp.ClientSession() as session:
        for url in urls:
            try:
                async with session.get(url) as response:
                    data = await response.json()
                    results.append({"url": url, "title": data["title"], "status": "ok"})
            except Exception:
                results.append({"url": url, "title": None, "status": "error"})
    return results

# Koer det:
articles = asyncio.run(fetch_articles(["https://api.example.com/1"]))
```
</details>

---

## NAESTE SKRIDT

1. **Koer ai-automation-agent lokalt:** `cd ai-automation-agent && source .venv/bin/activate && pytest -v`
2. **Lav en ny tool:** Tilfoj en ny tool handler og registrer den i `agent/tools/__init__.py`
3. **Tilfoej type hints:** Koer `mypy --strict agent/` og fix alle fejl
4. **Laes reelle Python-kode:** FastAPI, httpx, Pydantic -- de viser moderne Python-patterns
5. **Oev list comprehensions:** Omskriv alle dine for-loops til comprehensions i en uge

---

*Genereret: 2026-04-16 | Kontekst: ai-automation-agent projekt | Maalsgruppe: Java/JS-udvikler -> Python for AI*
