# AI-Driven E2E Test Self-Healing Engine

<!-- language: **English** · [한국어](README.ko.md) -->

**English** · [한국어](README.ko.md)

[![CI](https://github.com/Lee-Dongwook/E2E-Self-Heal/actions/workflows/ci.yml/badge.svg)](https://github.com/Lee-Dongwook/E2E-Self-Heal/actions/workflows/ci.yml)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Automatically repair broken Playwright E2E tests. When a UI change renames or restructures
an element and a test's selector breaks, the engine diagnoses the failure, patches the
broken selector/wait, **verifies the new selector against the live DOM**, then re-runs the
test until it passes (or a retry cap is hit) and writes the fix back — as a local **CLI** or
a **CI GitHub Action** that opens a patch PR.

> **Scope guardrail:** the engine only fixes **failing locators and wait conditions**. It
> never touches assertions or test logic, and every patch stays human-reviewable.

![e2e-healer demo — diagnose, verify against the live DOM, re-run, fixed](https://raw.githubusercontent.com/Lee-Dongwook/E2E-Self-Heal/main/docs/demo.gif)

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

```
   ┌──────────┐    ┌─────────────────┐    ┌───────────────────┐    ┌─────────────┐
──▶│ Diagnoser│──▶ │ Patch Generator │──▶ │ Selector Verifier │─┬─▶│ Test Runner │──┐
   └──────────┘    └─────────────────┘    └───────────────────┘ │  └─────────────┘  │
        ▲                   ▲  verify fail (0/2+ match) → repatch ┘                   │
        │                   └───────────────────────────────────────────────────────┘│
        │                          fail & loop_count < max                            │
        └───────────────────────────────  Router  ◀───────────────────────────────────┘
                                            │ pass or loop cap
                                            ▼
                                          [End]
```

> The Selector Verifier **skips** gracefully (loop proceeds unverified) when
> `E2E_HEALER_APP_URL` is empty or the page is unreachable (e.g. Node/Playwright not
> installed) — tooling problems never block a heal.

See [`docs/design.md`](docs/design.md) for the full design.

## Demo (verified end-to-end)

The [`examples/`](examples/) project reproduces a real break: the page's button id was
renamed `submit-btn` → `submit`, so `example.spec.ts` times out. Running the healer against
it (with a live NVIDIA key) produces:

```text
diagnoser_finished
patch_generator_finished        instruction_count=1
selector_verify_started         selector_count=1 url=http://localhost:4173
selector_verify_passed          counts={'#submit': 1}
test_runner_passed              loop_count=0
fixed after 0 loop(s)
```

```diff
- await page.click("#submit-btn");
+ await page.click("#submit");        # assertion on "Thanks!" left untouched
```

Reproduce it yourself: see [`examples/README.md`](examples/README.md).

## In practice

A real run against a landing-page CTA test. A UI refactor renamed the button id
`#enter-demo-btn` → `#demo-cta-btn`, so `demo-cta.spec.ts` started failing on
`locator.click`. Pointed at the file, the engine diagnosed the break against the `git diff`,
patched **only the broken selector** (leaving the `toHaveURL` assertion untouched), re-ran
the suite, and passed on the first attempt — end to end on NVIDIA NIM
(`integrate.api.nvidia.com`, `openai/gpt-oss-120b`):

![Real-world run: diagnose the renamed CTA selector, patch it, re-run, fixed after 0 loops](https://raw.githubusercontent.com/Lee-Dongwook/E2E-Self-Heal/main/docs/usecase-demo-cta.png)

```text
playwright_run_finished     passed=False                    # original selector times out
diagnoser_started           loop_count=0
diagnoser_finished
patch_generator_finished    instruction_count=1
test_runner_started
playwright_run_finished     passed=True
repair_run_finished         is_success=True loop_count=0
fixed after 0 loop(s)
```

```diff
  test('guest enters the demo workspace from the landing CTA', async ({ page }) => {
    await page.goto('/')
-   await page.click('#enter-demo-btn')
+   await page.click('#demo-cta-btn')
    await expect(page).toHaveURL(/\/w\//)   // assertion left untouched
  })
```

## Install

Requires Python 3.13+ and a Playwright project (Node) in your repo.

```bash
uv sync                 # or, once published: pipx install ai-driven-e2e
cp .env.example .env    # then set E2E_HEALER_NVIDIA_API_KEY
```

Get a free NVIDIA NIM API key at [build.nvidia.com](https://build.nvidia.com/) (the default
model is `openai/gpt-oss-120b`).

### Run it on your own project (global CLI)

Before publishing to PyPI, install the CLI globally straight from this repo — then `cd`
into **any** real Playwright project and run `e2e-healer` there:

```bash
uv tool install /path/to/this/repo     # installs a global `e2e-healer` (isolated env)

cd ~/work/your-real-web-app             # your actual Playwright suite
export E2E_HEALER_NVIDIA_API_KEY=nvapi-...
e2e-healer                              # heal the whole suite, in place
e2e-healer tests/login.spec.ts --dry-run   # or preview a single spec, write nothing
```

The CLI reads config from `E2E_HEALER_*` env vars (or a `.env` in the project dir), runs
`npx playwright test` in the current directory, and exits `0` when everything is healed —
so it drops into a real repo with no per-project setup. Re-run `uv tool install --force
/path/to/this/repo` to pick up new changes.

## Usage (CLI)

```bash
# Heal the WHOLE suite — run every test, then repair each failing file (aggregate summary):
uv run e2e-healer

# Heal a single failing test (with no --log, the tool runs it to capture the failure):
uv run e2e-healer tests/example.spec.ts

# Preview only — run the loop but write nothing:
uv run e2e-healer tests/example.spec.ts --dry-run

# Feed a pre-captured log and a PR-scoped diff (the CI path):
uv run e2e-healer tests/example.spec.ts --log playwright.log --diff-base origin/main --json

# Enable live-DOM selector verification against a running app:
uv run e2e-healer tests/example.spec.ts --app-url http://localhost:4173
```

Exit code is `0` when the test is healed, non-zero otherwise. `--json` prints a
machine-readable `RepairSummary` to stdout (human output goes to stderr) so CI can branch
on it.

## Usage (CI / GitHub Action)

Run the suite and auto-heal on failure, opening a patch PR for review:

```yaml
- name: E2E self-heal
  id: heal
  uses: Lee-Dongwook/E2E-Self-Heal@v0.2.0
  with:
    test-path: tests/example.spec.ts
    nvidia-api-key: ${{ secrets.NVIDIA_API_KEY }}
    diff-base: ${{ github.event.pull_request.base.sha }}
    app-url: http://localhost:4173 # optional: enables live selector verification

- name: Open patch PR
  if: steps.heal.outputs.outcome == 'healed'
  uses: peter-evans/create-pull-request@v6
  with:
    body-path: ${{ steps.heal.outputs.summary-path }}
    branch: e2e-self-heal/${{ github.run_id }}
```

The action's `outcome` output is `passed` \| `healed` \| `unhealed`. For a Playwright suite
in a subdirectory, pass `working-directory:`. A **runnable self-demo** that heals this repo's
own `examples/` project lives in [`ci/github-workflow.example.yml`](ci/github-workflow.example.yml).

## Configuration

All settings use the `E2E_HEALER_` prefix (see [`.env.example`](.env.example)):

| Variable                       | Default                               | Purpose                                        |
| ------------------------------ | ------------------------------------- | ---------------------------------------------- |
| `E2E_HEALER_NVIDIA_API_KEY`    | —                                     | NVIDIA NIM API key                             |
| `E2E_HEALER_NVIDIA_BASE_URL`   | `https://integrate.api.nvidia.com/v1` | OpenAI-compatible endpoint                     |
| `E2E_HEALER_NVIDIA_MODEL`      | `openai/gpt-oss-120b`                 | Structured-Outputs-capable model               |
| `E2E_HEALER_NVIDIA_MAX_TOKENS` | `4096`                                | Completion token cap (headroom for reasoning)  |
| `E2E_HEALER_MAX_LOOPS`         | `3`                                   | Repair loop cap                                |
| `E2E_HEALER_PLAYWRIGHT_CMD`    | `npx playwright test`                 | Playwright invocation                          |
| `E2E_HEALER_VERIFY_SELECTORS`  | `true`                                | Toggle live-DOM selector verification          |
| `E2E_HEALER_APP_URL`           | —                                     | URL the Selector Verifier loads (empty = skip) |
| `E2E_HEALER_NODE_CMD`          | `node`                                | Node executable for the verifier               |
| `E2E_HEALER_SANDBOX_MODE`      | `relaxed`                             | `strict`, `relaxed`, or `off`                  |
| `E2E_HEALER_WORKSPACE_ROOT`    | `.`                                   | Root for strict path checks                    |
| `E2E_HEALER_WRITE_GLOBS`       | `*.spec.js,...`                       | Writable test-file globs                       |
| `E2E_HEALER_DENY_GLOBS`        | `.env,.git/**,...`                    | Paths blocked by the sandbox                   |
| `E2E_HEALER_ALLOW_TEMP_HELPER` | `true`                                | Permit selector verifier helper file           |

> The `--app-url` CLI flag overrides `E2E_HEALER_APP_URL`. To actually run selector
> verification locally, the Playwright project needs browsers installed
> (`npm install && npx playwright install`).

## Development

```bash
make install    # uv sync --extra dev
make check      # ruff + pyright
make test       # pytest
```

See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Limitations

- Fixes selectors and waits only — never assertions or control flow.
- The JSX/TSX diff analyzer is a regex heuristic in v0.1 (tree-sitter upgrade planned).
- The Selector Verifier checks the **entry-page state** at `APP_URL` in v1. Elements that
  only appear after clicks/navigation aren't verified here; the Test Runner remains the final
  arbiter (failure-time snapshot capture is planned).
- Healing quality depends on the LLM and the clarity of the `git diff`.

## License

[MIT](LICENSE)
