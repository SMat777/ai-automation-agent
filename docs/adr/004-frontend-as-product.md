# ADR 004: Frontend is the product, not a demo shell

- **Status:** Accepted
- **Date:** 2026-04-18
- **Deciders:** Simon Mathiasen

## Context

This project is both a functional tool and a portfolio piece. The first impression
for anyone evaluating it — a recruiter, a tech lead, a potential teammate — is
almost always the web UI. They rarely read code before deciding if something is
worth a second look.

The current frontend is competent but reads as *"well-styled demo"* rather than
*"polished product"*. It has:

- Good information architecture (tabs per tool)
- Functional interactions (keyboard shortcuts, toast notifications, streaming chat)
- Basic accessibility pass (focus states, aria labels)

It lacks:

- A visual system with consistent spacing, elevation, typography scale
- Empty states that feel designed, not default
- Error states that look intentional, not thrown
- Responsive behaviour below tablet width
- A sense that every pixel has been considered

The risk of leaving this gap is that the sophisticated backend work (persistence,
MCP integration, prompt workbench, observability) will not be *perceived* as
sophisticated — because the front door says otherwise.

## Decision

**The frontend is treated as the product surface from Fase 1 onward**, not as a
demo shell around the real work. This means:

1. **Every backend feature gets a matching frontend pass.** When Fase 1 adds
   run history, the UI gets a sidebar with filterable history — not a JSON blob.
   When Fase 2 adds auth, the UI gets sign-in, account dropdown, session indicator
   — not just a form.

2. **Design quality is measured against a reference bar.** The target is
   "indistinguishable from a Linear / Stripe / Vercel dashboard at a glance".
   That bar is high on purpose — it filters out the kind of UI that kills
   portfolio impact.

3. **Every phase ends with a UI review pass.** Before merging, the new surface
   is checked against this checklist:
   - [ ] Spacing is on an 8px grid (or documented exception)
   - [ ] All interactive states designed: hover, focus, active, disabled, loading
   - [ ] Empty state is designed, not default
   - [ ] Error state is designed, not a toast
   - [ ] Works at 375px width (mobile) and 1440px (desktop)
   - [ ] Keyboard-only navigation works end-to-end
   - [ ] Colour contrast meets WCAG AA
   - [ ] Screen-reader labels present on icons and interactive elements
   - [ ] No layout shift when content loads
   - [ ] Page has a designed scroll experience (not just default)

4. **No build step yet.** Vanilla HTML/CSS/JS continues until a frontend concern
   actually justifies tooling (the Prompt Workbench in Fase 4 may cross that line).
   Adding a bundler before it is needed adds deployment complexity and slows
   iteration.

5. **Design tokens are documented as code.** CSS custom properties
   (`--bg-0`, `--accent`, `--r`, `--t`) serve as the design system. Changes go
   through git like any other code — no Figma-as-separate-source-of-truth.

## Consequences

### Positive

- **The project reads as mature at first contact.** Someone opening the deployed
  URL understands this is a product, not an experiment.
- **Portfolio leverage.** A showcase URL that looks production-grade is more
  valuable in a conversation than a GitHub repo alone.
- **Forces us to think in user flows, not endpoints.** Every API decision is
  pressure-tested against "how does this feel to use?".

### Negative

- **Each phase takes longer.** 20-40% of phase time now goes to frontend polish
  that would otherwise be deferred or skipped. Accepted cost.
- **Design work is a skill we must level up in.** Copy-pasting SaaS aesthetics
  is not enough; we have to understand spacing, type scale, motion timing well
  enough to apply them intentionally.
- **The "no build step" rule will eventually bite.** Prompt Workbench (Fase 4)
  may require richer interactions that vanilla JS cannot ergonomically deliver.
  When it does, we revisit this decision in a new ADR.

### Neutral

- Some UX patterns (drag-and-drop upload, split-view editor, live-preview panels)
  are more complex in vanilla JS than in a framework. Where they appear, we
  document the pattern well so it can survive a future migration.

## Alternatives considered

- **Ship backend first, polish frontend at the end.** Rejected because the
  portfolio impact is lost if the frontend reveal happens last — every phase
  demo along the way will undersell the work.

- **Pick a component library (shadcn, Radix) now.** Rejected for the current
  phase because a component library locks us into a React/Vite setup that is
  overkill for the current feature set. Revisited when/if build step arrives.

- **Hire or commission a designer.** Rejected because this is a learning
  project — the author needs to level up design sensibility, not delegate it.

## References

- [ADR 001 — persistence strategy](./001-persistence-strategy.md)
- Reference bar examples: [Linear](https://linear.app), [Stripe Dashboard](https://dashboard.stripe.com),
  [Vercel Dashboard](https://vercel.com/dashboard)
- Design tokens currently in: `frontend/style.css` (`:root` block)
