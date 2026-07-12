# Context & Role

You are an expert Technical Writer and Senior Developer Experience (DX) Engineer.
Your task is to refactor the official documentation (README and design documents) for `e2e-healer`, an AI-driven E2E test self-healing engine.

# Core Objective

The core engine is written in Python (using LangGraph), but our primary target audience, users, and buyers are Frontend (FE) and QA Engineers who live in the JavaScript/TypeScript and Playwright ecosystem.
You must rewrite and reposition the documentation so it feels completely native, intuitive, and appealing to a frontend developer, mimicking the polished documentation style of React or Playwright.

# Key Requirements & Positioning Strategy

1. Prioritize GitHub Action (CI/CD Integration)
    - Move the CI/CD integration section to the top or make it highly prominent.
    - Frontend and QA engineers love automated, PR-based healing workflows that run in the cloud without requiring local setup. Emphasize that they "don't have to run anything locally."

2. Use Tabbed/Parallel Structure for Examples
    - Whenever showcasing usage, contrast the Python CLI engine execution alongside the real JavaScript/TypeScript Playwright syntax it target-scans.
    - Format it clearly so JS/TS developers understand what the tool does to their codebase at a glance.

3. Keep Code Snippets JS/TS-Friendly
    - When showing before/after healing examples, use real, modern JS/TS Playwright test snippets (e.g., `await page.click(...)` changing to a robust locator). Do not use Python testing framework examples.

4. Scope Guardrail Emphasis
    - Clearly highlight that the engine ONLY patches broken locators and wait conditions. It never mutates test assertions (`expect()`) or control flow, ensuring 100% deterministic safety for enterprise pipelines.

# Input Content

-> More details are defined on README.md on root directory.

A **self-healing** engine that automatically repairs broken **Playwright** E2E tests with an
**AI agent** built on **LangGraph**. When a UI change renames or restructures
an element and a test's selector breaks, the engine diagnoses the failure, patches the
broken selector/wait, **verifies the new selector against the live DOM**, then re-runs the
test until it passes (or a retry cap is hit) and writes the fix back — as a local **CLI** or
a **CI GitHub Action** that opens a patch PR.

> **Scope guardrail:** the engine only fixes **failing locators and wait conditions**. It
> never touches assertions or test logic, and every patch stays human-reviewable.

### Two modes: **heal** and **review**

Auto-healing patches the _test_. That is fast, but on its own it can look like papering over
a real problem — the source that broke the selector. So the engine offers a second mode:

- **`heal`** (default) — patch the broken selector/wait and re-run until green. Best when the
  UI change is intentional and the test simply needs to catch up.
- **`review`** — diagnose _why_ the selector broke and post **source-level suggestions** as
  **inline PR comments** (e.g. "this `className` rename broke `#cta`; add a stable
  `data-testid` or use `getByRole`"). It **never edits the test** — it advises the fix at the
  source and pushes teams toward resilient, accessibility-first selectors.

Same diagnosis engine, two outputs: a patch, or a review. Pick per-project or per-PR.

## How it works

Four layers drive a LangGraph repair loop:

1. **CLI core** — the single entry point (`e2e-healer`); everything, including CI, calls it.
2. **Data Preprocessor** — abstracts the raw Playwright log and the `git diff` into compact,
   hallucination-resistant context (the failing selector + the DOM attribute that changed).
3. **LangGraph agent** — `Diagnoser → Patch Generator → Selector Verifier → Test Runner`,
   looping via a conditional Router until the test passes or `max_loops` is reached.
4. **Selector Verifier** — checks each patched selector against the real page DOM so it
   resolves to **exactly one** element (Node/Playwright helper). Hallucinated (0 matches) or
   ambiguous (>1) selectors are reverted and re-patched _before_ a full test run.
5. **Test Runner** — runs `npx playwright test` via subprocess to validate each attempt.

# Output Format

Provide the fully rewritten, production-ready Markdown documentation. Ensure the tone is professional, authoritative, and deeply aligned with modern frontend DX standards.
