# Examples — a real React app the engine heals

A runnable **React + Vite** demo app plus a set of **scenarios** that reproduce the
situation the engine is built for: a component changes, a selector breaks, a Playwright
test fails, and the healer repairs it — end to end, against a real running app.

Unlike a hand-written static page, editing a component here produces a **real `git diff`**,
that diff **actually breaks** a test, and the healer patches the spec's selector while
leaving assertions untouched.

## Layout

```
examples/
  demo-app/                 # the React + Vite app under test
    index.html
    src/
      main.tsx
      App.tsx
      components/           # actually-rendered components
        SubmitButton.tsx
  scenarios/
    id-rename/              # one scenario = component + breaking change + failing spec
      spec.ts              # the test for this scenario
      change.patch         # the real component change that breaks it
      README.md            # reproduce + heal steps
  vite.config.ts           # serves demo-app on :4173 (dev and preview)
  playwright.config.ts      # webServer = `pnpm build && pnpm preview`
  package.json
```

Each scenario is a **set of three**: a working component → a breaking change (a real
`git diff`) → a failing spec. The demo app is committed **green** — every spec passes on
a clean checkout — and a scenario is triggered by applying its `change.patch`.

## Setup

Requires Node and [pnpm](https://pnpm.io). From this folder:

```bash
pnpm install
pnpm exec playwright install chromium
```

## Run the tests against the real app

```bash
pnpm exec playwright test          # builds the app, serves it via vite preview, runs specs
```

Playwright's `webServer` runs `pnpm build && pnpm preview`, so the specs always run
against the freshly built app. On a clean checkout everything is green.

To develop the app interactively:

```bash
pnpm dev                            # http://localhost:4173
```

## Scenarios

| Scenario                          | Breakage                          | Status |
| --------------------------------- | --------------------------------- | ------ |
| [`id-rename/`](scenarios/id-rename/) | button `id` renamed (`submit-btn` → `submit`) | ✅ live |
| className change                  | CSS class renamed                 | planned |
| text / label change               | breaks `getByText` locators       | planned |
| DOM restructuring                 | wrapper added/removed             | planned |
| role / aria change                | breaks `getByRole` locators       | planned |

> The legacy static-HTML [`classname-scenario/`](classname-scenario/) predates this demo
> app and is pending migration onto it.

## Heal a scenario

Each scenario's README documents the full reproduce-and-heal flow. In short, from
`examples/`:

```bash
git apply scenarios/id-rename/change.patch                     # break the app for real
pnpm exec playwright test scenarios/id-rename 2>&1 | tee scenarios/id-rename/playwright.log
e2e-healer scenarios/id-rename/spec.ts --log scenarios/id-rename/playwright.log --dry-run
```

The healer defaults to `git diff`, so the applied change is picked up automatically; pass
`--diff scenarios/<name>/change.patch` to be explicit. See
[`scenarios/id-rename/README.md`](scenarios/id-rename/README.md) for the detailed walkthrough.

## Reset after experimenting

```bash
git checkout -- demo-app scenarios      # undo applied patches and any written fixes
```
