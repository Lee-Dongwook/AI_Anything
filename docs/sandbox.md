# Sandbox and Permission Model

Status: initial policy implemented in `app/sandbox.py`.

This project edits Playwright test files automatically, so the default security posture
should be: read enough context to diagnose a failure, write only the selected repair
targets, and execute only explicit test/verification commands.

## Goals

- Keep local and CI runs predictable.
- Prevent accidental edits to source, config, secrets, CI workflows, and release files.
- Make every write path traceable to a failing test file or a generated runtime artifact.
- Preserve the current CLI behavior: local use and CI both call `e2e-healer`.

## Default Access Policy

| Operation | Allow by default                                                                                     | Deny or require explicit opt-in                                                                                 |
| --------- | ---------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| Read      | Target test files, `--log`, `--diff`, `git diff`, `test-results/`, source paths present in the diff  | `.env`, secret/key files, private credentials, unrelated home-directory files                                   |
| Write     | The exact failing test file under repair, dry-run restore writes, temporary selector verifier helper | `.env`, `.git/`, `.github/`, `pyproject.toml`, lockfiles, CI/action files, source files outside the target test |
| Execute   | `git diff`, `E2E_HEALER_PLAYWRIGHT_CMD`, `E2E_HEALER_NODE_CMD`                                       | Arbitrary shell commands, command strings that rely on shell expansion or chaining                              |

## Path Rules

All paths should be resolved before access checks.

- Default workspace root: current working directory.
- A readable or writable path must stay inside the workspace root after `Path.resolve()`.
- Symlink escapes outside the workspace should be rejected.
- Write targets must be existing regular files unless the path is a known generated artifact.
- Directories such as `.git/`, `.venv/`, `node_modules/`, and build output should never be patched.
- The repair loop may write only files discovered from the CLI argument or parsed failing test output.

## Suggested Configuration

These environment variables are implemented via `app.config.Settings`.

```text
E2E_HEALER_SANDBOX_MODE=strict      # strict | relaxed | off
E2E_HEALER_WORKSPACE_ROOT=.         # resolved from the process cwd by default
E2E_HEALER_WRITE_GLOBS=*.spec.js,*.spec.jsx,*.spec.ts,*.spec.tsx,*.test.js,*.test.jsx,*.test.ts,*.test.tsx,**/*.spec.js,**/*.spec.jsx,**/*.spec.ts,**/*.spec.tsx,**/*.test.js,**/*.test.jsx,**/*.test.ts,**/*.test.tsx
E2E_HEALER_DENY_GLOBS=.env*,.git/**,.github/**,node_modules/**,.venv/**
E2E_HEALER_ALLOW_TEMP_HELPER=true   # permits .e2e-healer-verify.mjs during selector checks
```

Recommended modes:

- `strict`: used by the GitHub Action. Enforce workspace, write-glob, deny-glob, and
  command checks.
- `relaxed`: default for local development. Enforce write-glob, deny-glob, and command
  checks without requiring every test fixture to sit under the workspace root.
- `off`: debugging escape hatch; should print a warning.

## Implementation Notes

`app/sandbox.py` exposes small guard functions:

- `assert_read_allowed(path: Path) -> None`
- `assert_write_allowed(path: Path, reason: str) -> None`
- `assert_command_allowed(argv: list[str]) -> None`

These guards are called before `read_text()`, `atomic_write()`, selector helper creation,
and subprocess execution. Keep `subprocess.run()` shell-free; the current `shlex.split()`
approach is a good baseline because command chaining is not interpreted by a shell.

## Test Checklist

- Reject writing outside the workspace via `../`.
- Reject symlinks that resolve outside the workspace.
- Reject writes to `.env`, `.github/`, `.git/`, and lockfiles.
- Allow a targeted `*.spec.ts` or `*.test.tsx` repair file.
- Allow dry-run restoration of the original target file.
- Allow and clean up the selector verifier helper.
- Verify suite mode cannot patch files that were not reported as failing tests.
