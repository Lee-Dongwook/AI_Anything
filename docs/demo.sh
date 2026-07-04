# Sourced by docs/demo.tape to render docs/demo.gif deterministically (no network/secrets).
# Defines shadow functions that reproduce the VERIFIED healer run shown in the README "Demo"
# section, so the GIF renders identically anywhere. Re-render with: vhs docs/demo.tape

PS1='$ '

_c() { printf '%b\n' "$1"; }  # print, interpreting \033 color escapes

# Stand in for `npx playwright test` — the failing run (broken selector).
npx() {
  _c ''
  _c '  \033[31m✘\033[0m  example.spec.ts:7 › submits the form'
  _c '     \033[31mTimeoutError\033[0m: page.click: Timeout 3000ms exceeded.'
  _c "       - waiting for locator('#submit-btn')"
  _c ''
}

# Stand in for the `e2e-healer` CLI — diagnose → patch → verify → re-run.
e2e-healer() {
  sleep 0.4; _c '  \033[36mdiagnoser\033[0m         #submit-btn → id renamed (from git diff)'
  sleep 0.5; _c '  \033[36mpatch_generator\033[0m   instruction_count=1'
  sleep 0.4; _c "  \033[36mselector_verify\033[0m   '#submit' resolves to \033[32m1 element\033[0m in live DOM ✓"
  sleep 0.5; _c '  \033[36mtest_runner\033[0m       \033[32mpassed\033[0m   loop_count=0'
  _c ''
  _c '  \033[31m- await page.click("#submit-btn");\033[0m'
  _c '  \033[32m+ await page.click("#submit");\033[0m   \033[2m(assertion left untouched)\033[0m'
  _c ''
  _c '  \033[1;32m✔ fixed after 0 loop(s)\033[0m'
}
