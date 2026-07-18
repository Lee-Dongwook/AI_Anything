import { test, expect } from "@playwright/test";

// GREEN on checkout: the demo app renders <button id="submit-btn">, so this passes.
//
// Apply scenarios/id-rename/change.patch (renames the id to "submit") and this test
// breaks with a Timeout on `#submit-btn`. The healer correlates that failure with the
// id change in `git diff` and patches ONLY the selector below — the `Thanks!`
// assertion is left untouched.
test("submits the form", async ({ page }) => {
  await page.goto("/");
  await page.click("#submit-btn");
  await expect(page.getByText("Thanks!")).toBeVisible();
});
