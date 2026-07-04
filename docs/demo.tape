# VHS tape for the README demo GIF. Render with:  vhs docs/demo.tape
# Output: docs/demo.gif. Uses shadow functions from docs/demo.sh so it renders
# deterministically without a key, a server, or network access.

Output docs/demo.gif

Set Shell bash
Set FontSize 20
Set Width 1200
Set Height 720
Set Padding 26
Set Theme "Dracula"
Set TypingSpeed 55ms

# Load the deterministic demo functions, then clear the setup noise.
Hide
Type "source docs/demo.sh"
Enter
Type "clear"
Enter
Show

Sleep 600ms
Type "npx playwright test"
Sleep 400ms
Enter
Sleep 1.8s

Type "e2e-healer example.spec.ts --app-url http://localhost:4173"
Sleep 400ms
Enter
Sleep 3.5s
Sleep 1s
