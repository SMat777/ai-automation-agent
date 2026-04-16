# Automation & Workflow Orchestration

> En praktisk guide til automatiseringsmønstre: pipelines, connectors, transforms og fejlhåndtering.

---

## Hvad er workflow automation?

Workflow automation handler om at lade maskiner udføre gentagne, regelbaserede opgaver i en bestemt rækkefølge. I stedet for at en person manuelt henter data, renser det, og laver en rapport, bygger man en **pipeline** der gør det automatisk.

```
┌──────────┐    ┌───────────┐    ┌──────────┐    ┌──────────┐
│  Kilde   │───→│ Connector │───→│Transform │───→│  Output  │
│ (API/fil)│    │ (hent)    │    │(rens/map)│    │(rapport) │
└──────────┘    └───────────┘    └──────────┘    └──────────┘
```

## Pipe-and-Filter mønsteret

Det klassiske mønster for datapipelines. Hvert trin (filter) tager input, bearbejder det, og sender output videre til næste trin.

**Styrker:**
- Hvert trin er uafhængigt og testbart
- Trin kan genbruges i andre pipelines
- Let at tilføje/fjerne trin uden at ændre resten

**Sammenligning med kendte koncepter:**

| Koncept | Java | JavaScript | Python |
|---------|------|-----------|--------|
| Pipeline | Stream API | Array.map().filter() | Generators |
| Transform | Function<T, R> | (data) => newData | def transform(data) |
| Connector | JDBC/HttpClient | fetch/axios | requests/httpx |

## Pipeline-klassen i dette projekt

```typescript
// automation/src/pipeline.ts
const pipeline = new Pipeline("Min Pipeline");

const result = await pipeline
  .step("Hent data", () => fetchJSON(url))      // Connector
  .step("Rens data", (data) => cleanData(data))  // Transform
  .step("Lav rapport", (data) => formatReport(data)) // Output
  .execute();
```

**Nøgleprincipper:**
1. **Chaining** — `.step().step().execute()` gør det læsbart
2. **Navngivne trin** — Hvert trin har et navn til logging
3. **Timing** — Hvert trin rapporterer sin udførselstid
4. **Async support** — Trin kan være synkrone eller asynkrone

## Connectors — Datahentning

Connectors er ansvarlige for at hente data fra eksterne kilder:

```typescript
// Simpel API connector med validering
export async function fetchJSON(url: string): Promise<unknown> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`API fejl: ${response.status}`);
  }
  const data = await response.json();
  return ApiResponseSchema.parse(data); // Zod validering
}
```

**Best practices for connectors:**
- Validér altid svar med Zod/schema
- Håndtér HTTP fejlkoder eksplicit
- Implementér retry med exponential backoff
- Log requests og responses til debugging

### Retry-mønster

```typescript
async function fetchWithRetry(url: string, maxRetries = 3): Promise<unknown> {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fetchJSON(url);
    } catch (error) {
      if (attempt === maxRetries - 1) throw error;
      const delay = Math.pow(2, attempt) * 1000; // 1s, 2s, 4s
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
}
```

## Transforms — Databearbejdning

Transforms ændrer data uden at hente eller gemme noget:

```typescript
// Rensning: fjern null-værdier, trim strenge
export function cleanData(records: Record<string, unknown>[]) {
  return records.map(record => {
    const cleaned = {};
    for (const [key, value] of Object.entries(record)) {
      if (value === null || value === undefined) continue;
      cleaned[key] = typeof value === "string" ? value.trim() : value;
    }
    return cleaned;
  });
}
```

**Typiske transforms:**
| Transform | Formål | Eksempel |
|-----------|--------|---------|
| Filter | Fjern poster der ikke matcher | `records.filter(r => r.active)` |
| Map | Omdøb/omform felter | `records.map(r => ({ name: r.title }))` |
| Aggregate | Gruppér og beregn | Summer salg per kategori |
| Sort | Sortér poster | `records.sort((a, b) => a.date - b.date)` |
| Enrich | Tilføj data fra anden kilde | Slå adresser op fra CVR |

## Fejlhåndtering i pipelines

Fejl i ét trin kan stoppe hele pipelinen. Strategier:

### 1. Fail Fast (standard)
```typescript
// Pipelinen stopper ved første fejl
try {
  await pipeline.execute();
} catch (error) {
  console.error(`Pipeline fejlede: ${error.message}`);
}
```

### 2. Skip & Continue
```typescript
// Spring fejlede poster over
const results = data.map(item => {
  try {
    return processItem(item);
  } catch {
    console.warn(`Sprang over: ${item.id}`);
    return null;
  }
}).filter(Boolean);
```

### 3. Dead Letter Queue
Gem fejlede items til senere genbehandling — bruges i enterprise-systemer.

## Automation vs RPA vs Low-Code

| Tilgang | Hvad | Hvornår | Eksempel |
|---------|------|---------|----------|
| **Code automation** | Skriv pipelines i kode | Kompleks logik, API-integrationer | Dette projekt |
| **RPA** (Robotic Process Automation) | Automatisér UI-handlinger | Legacy systemer uden API | UiPath, Power Automate |
| **Low-code** | Visuel workflow-builder | Hurtige prototyper, ikke-tekniske brugere | Make, n8n, Zapier |
| **AI Agents** | AI bestemmer hvad der skal ske | Uforudsigelige opgaver, naturligt sprog | Claude + tools |

**Columbus-relevans:** Columbus arbejder med alle fire tilgange — fra Dynamics 365 integrationer (code) til Power Automate (low-code) til AI Copilots (agents).

## Zod — Runtime validering i TypeScript

TypeScript checker typer på compile-tid, men data fra API'er er `unknown` at runtime. Zod løser dette:

```typescript
import { z } from "zod";

// Definer schema
const UserSchema = z.object({
  name: z.string(),
  email: z.string().email(),
  age: z.number().min(0),
});

// Validér ukendt data
const user = UserSchema.parse(apiResponse); // Kaster fejl hvis ugyldig
type User = z.infer<typeof UserSchema>; // Genererer TypeScript type
```

**Hvorfor Zod er vigtigt:**
- API'er kan ændre sig uden varsel
- `JSON.parse()` returnerer `any` — ingen sikkerhed
- Zod fanger fejl tidligt med klare beskeder

## Øvelser

1. **Byg en connector** der henter vejrdata fra et offentligt API og validerer svaret med Zod
2. **Skriv en transform** der konverterer en liste af objekter til en Markdown-tabel
3. **Kombiner dem** i en pipeline: hent → rens → formater → gem som fil
4. **Tilføj retry** til din connector med exponential backoff
5. **Sammenlign** din kode-pipeline med at gøre det samme i et low-code tool (fx Make.com)

---

*Guide genereret som del af ai-automation-agent projektet — se [CONTRIBUTING.md](../../CONTRIBUTING.md) for workflow.*
