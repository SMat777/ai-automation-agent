# GitHub Project Management — Best Practices

> En guide til at bruge GitHubs fulde toolset professionelt: issues, projects, milestones, actions, releases og branch protection.

---

## Hvorfor GitHub Project Management?

GitHub er ikke bare til kode — det er et komplet projektstyringsværktøj. For en praktikant eller junior-udvikler er det et stærkt signal at vise at du forstår hele workflowet, ikke bare `git push`.

## Issues — Alt arbejde starter her

### Grundprincip
Ingen kode skrives uden et issue. Issues er:
- **Dokumentation** af hvad der skal laves og hvorfor
- **Kommunikation** med teamet
- **Tracking** af hvad der er færdigt

### God issue-struktur

```markdown
## Description
Hvad skal laves og hvorfor.

## Acceptance Criteria
- [ ] Konkret krav 1
- [ ] Konkret krav 2
- [ ] Tests skrevet og bestået

## Technical Notes
Implementation-detaljer, constraints, afhængigheder.
```

### Issue Templates
Gem templates i `.github/ISSUE_TEMPLATE/`:
- `feature.md` — Ny funktionalitet
- `bug.md` — Fejl der skal fixes
- `learning.md` — Læringsopgaver (brugt i dette projekt)

### Labels — Organisér visuelt

| Label | Farve | Formål |
|-------|-------|--------|
| `feature` | Grøn | Ny funktionalitet |
| `bug` | Rød | Fejl |
| `docs` | Blå | Dokumentation |
| `learning` | Lilla | Læringsopgave |
| `python` | Python-blå | Sprog-specifik |
| `typescript` | TS-blå | Sprog-specifik |
| `phase-0` til `phase-4` | Gul | Udviklingsfase |

```bash
# Opret label via CLI
gh label create feature --color 0E8A16 --description "New functionality"
```

## Milestones — Gruppér issues i faser

Milestones samler relaterede issues og giver overblik over fremdrift:

```bash
# Opret milestone via API
gh api repos/OWNER/REPO/milestones \
  -f title="Phase 1: Agent Core" \
  -f description="Python AI agent med tool calling" \
  -f due_on="2026-05-15T00:00:00Z"
```

**Best practice:**
- Én milestone per udviklingsfase
- Sæt realistiske deadlines
- Luk milestone når alle issues er done

## Branches — Feature Branch Workflow

### Navngivning
```
feature/agent-core        # Ny funktionalitet
fix/api-timeout           # Bug fix
docs/learning-guides      # Dokumentation
refactor/tool-registry    # Restructuring
```

### Workflow
```bash
# 1. Start fra opdateret main
git checkout main && git pull

# 2. Opret feature branch
git checkout -b feature/agent-core

# 3. Arbejd, commit, push
git add agent/agent.py
git commit -m "feat: implement agent decision loop"
git push -u origin feature/agent-core

# 4. Opret PR
gh pr create --title "feat: implement agent decision loop" \
  --body "Closes #1"
```

## Pull Requests — Code Review Process

### PR Template
Gem i `.github/PULL_REQUEST_TEMPLATE/pull_request.md`:

```markdown
## Summary
Kort beskrivelse af hvad og hvorfor.

## Changes
- Ændring 1
- Ændring 2

## Related Issue
Closes #XX

## Test Results
(indsæt test output)

## Checklist
- [ ] Tests tilføjet/opdateret
- [ ] Dokumentation opdateret
- [ ] CI passer
```

### Linking Issues
Brug nøgleord i PR-beskrivelsen:
- `Closes #1` — Lukker issue automatisk ved merge
- `Fixes #3` — Samme effekt
- `Relates to #5` — Link uden auto-close

## Conventional Commits

### Format
```
<type>: <beskrivelse>
```

### Typer
| Type | Hvornår |
|------|---------|
| `feat` | Ny funktionalitet |
| `fix` | Bug fix |
| `docs` | Kun dokumentation |
| `test` | Kun tests |
| `refactor` | Kode-ændring uden adfærdsændring |
| `chore` | Build, CI, dependencies |
| `ci` | CI/CD pipeline ændringer |

### Eksempler
```
feat: add document analysis tool with entity extraction
fix: handle empty API response in connector
docs: add AI agents learning guide
test: add agent tool routing tests
refactor: extract prompt templates to separate module
ci: add TypeScript type checking to CI pipeline
```

## GitHub Actions — CI/CD

### Grundlæggende CI workflow

```yaml
# .github/workflows/ci.yml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: ruff check .
      - run: pytest -v
```

### Hvad CI skal checke
- **Lint** — Kode følger style guide (ruff, eslint)
- **Types** — Type-check passer (mypy, tsc)
- **Tests** — Alle tests passer (pytest, vitest)
- **Build** — Projektet kan bygges

### Secrets
Gem API-nøgler som repository secrets:
```
Settings → Secrets and variables → Actions → New repository secret
```
Brug i workflow: `${{ secrets.ANTHROPIC_API_KEY }}`

## Releases — Versionering

### Semantic Versioning (SemVer)
```
MAJOR.MINOR.PATCH
  1.0.0  — Første stabile release
  1.1.0  — Ny feature tilføjet (bagudkompatibel)
  1.1.1  — Bug fix
  2.0.0  — Breaking change
```

### Opret release
```bash
# Tag version
git tag -a v1.0.0 -m "v1.0.0: Initial release with agent + pipeline"
git push origin v1.0.0

# Opret GitHub release
gh release create v1.0.0 --title "v1.0.0" --notes "First stable release"
```

## GitHub Projects (Kanban)

### Opsætning
```bash
# Opret via GitHub UI: github.com/OWNER/REPO/projects → New project
# Vælg "Board" layout
# Kolonner: Backlog → In Progress → Review → Done
```

### Best practice
- Flyt issues til "In Progress" når du starter
- Flyt til "Review" når PR er oprettet
- Auto-close moves to "Done" ved merge

## Komplet workflow — Fra idé til merge

```
1. Opret Issue (#5: "feat: add data extraction tool")
     ↓
2. Opret branch (feature/data-extraction)
     ↓
3. Skriv kode + tests + docs
     ↓
4. Commit (feat: add data extraction with pattern matching)
     ↓
5. Push + opret PR ("Closes #5")
     ↓
6. CI kører automatisk (lint, type, test)
     ↓
7. Review + godkendelse
     ↓
8. Merge til main → Issue #5 lukkes automatisk
     ↓
9. Når milestone er komplet → tag release
```

## Øvelser

1. **Opret et issue** med template, labels og milestone
2. **Lav et feature branch** workflow: branch → commit → push → PR
3. **Skriv 5 commits** der følger conventional commit-formatet
4. **Opsæt en GitHub Action** der kører `pytest` på push
5. **Tag og udgiv** en v0.1.0 release med release notes

---

*Guide genereret som del af ai-automation-agent projektet — se [CONTRIBUTING.md](../../CONTRIBUTING.md) for workflow.*
