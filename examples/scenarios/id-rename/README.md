# Scenario: id rename (`submit-btn` → `submit`)

A real component change breaks a real test, and the engine heals it.

- **Component:** [`../../demo-app/src/components/SubmitButton.tsx`](../../demo-app/src/components/SubmitButton.tsx) renders `<button id="submit-btn">`.
- **Spec:** [`spec.ts`](spec.ts) clicks `#submit-btn`, then asserts `Thanks!` is visible.
- **Change:** [`change.patch`](change.patch) renames the button id to `submit` — a genuine `git diff`, not a hand-crafted one.

On a clean checkout the spec is **green**: the app renders `#submit-btn` and the click
succeeds. Applying the patch renames the id in the real app, so the spec times out on
`#submit-btn` — exactly the "a UI change broke my selector" situation the engine repairs.

## 1. Reproduce the failure

Run from the `examples/` folder:

```bash
pnpm install
pnpm exec playwright install chromium

# baseline: passes against the real app
pnpm exec playwright test scenarios/id-rename

# apply the real component change and watch it break
git apply scenarios/id-rename/change.patch
pnpm exec playwright test scenarios/id-rename 2>&1 | tee scenarios/id-rename/playwright.log
```

The second run fails with `locator.click: Timeout ... waiting for locator("#submit-btn")`,
and the log is saved for the healer.

## 2. Heal it

With the healer installed (`uv sync` at the repo root) and an API key set, run from
`examples/`. The button id lives in the working tree change, so the healer's default
`git diff` already sees it — no `--diff` flag needed:

```bash
e2e-healer scenarios/id-rename/spec.ts --log scenarios/id-rename/playwright.log --dry-run
```

The engine parses the Timeout, correlates it with the `id` change in the diff, and proposes:

```diff
-  await page.click("#submit-btn");
+  await page.click("#submit");
```

`--dry-run` restores the spec afterward. Drop it to write the fix in place, then re-run
`pnpm exec playwright test scenarios/id-rename` to confirm it passes (the `Thanks!`
assertion is left untouched).

> You can also pass the change explicitly with `--diff scenarios/id-rename/change.patch`
> instead of relying on the default `git diff`.

## 3. Reset

```bash
git checkout -- demo-app/src/components/SubmitButton.tsx   # undo the applied change
git checkout -- scenarios/id-rename/spec.ts                # if you dropped --dry-run
```
