"""System prompt for the Patch Generator node (carries the code-integrity guardrail)."""

import json
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Mapping, TypedDict

FrameworkName = Literal["react", "vue", "svelte", "generic"]


class DomDiffEntry(TypedDict, total=False):
    """Structural type for DOM-diff entries consumed by framework detection."""

    file: str


@dataclass(frozen=True)
class SelectorPromptStrategy:
    """Framework-specific selector and wait guidance for the Patch Generator."""

    framework: FrameworkName
    guidance: str


SYSTEM_PROMPT = (
    "You repair Playwright E2E tests. You may ONLY fix failing locators (selectors) and "
    "optimize wait conditions. You must NEVER change assertions, test flow, or business "
    "logic. For each edit, return the 1-based line number, the exact original line, the "
    "replacement line, and a short reason. When the edit changes a locator, also return "
    "'selector' as a Playwright selector-engine string usable by page.locator() (e.g. "
    "'#submit', 'role=button[name=\"Submit\"]', 'text=Submit') matching the new locator, so "
    "it can be verified against the live DOM; leave 'selector' empty for non-locator edits "
    "such as wait tweaks. Respect the configured architecture boundary and never propose edits "
    "outside it. If a prior attempt is reported as rejected in the diagnosis, do NOT "
    "reuse the rejected selector - pick a different, more specific one. Return edits strictly "
    "via the provided schema; if no selector/wait fix is warranted, return an empty list."
)


SELECTOR_PROMPT_STRATEGIES: Mapping[FrameworkName, SelectorPromptStrategy] = {
    "react": SelectorPromptStrategy(
        framework="react",
        guidance=(
            "Detected framework: React. Prefer Playwright locators that reflect React UI intent: "
            "getByRole()/role= with accessible names first, then getByLabel()/getByText() when "
            "stable, then getByTestId()/data-testid for intentionally stable hooks. Avoid "
            "generated class names, CSS-module hashes, and implementation-only component markup. "
            "For React async rendering or hydration timing, prefer locator waits "
            "such as locator.waitFor() or page.waitForSelector() over arbitrary fixed timeouts."
        ),
    ),
    "vue": SelectorPromptStrategy(
        framework="vue",
        guidance=(
            "Detected framework: Vue 3. Prefer role/name locators for rendered UI, then stable "
            "data-testid or data-test attributes commonly used in Vue apps. Avoid scoped-style "
            "artifacts such as data-v-* attributes, generated classes, and transient dynamic ids. "
            "For async component updates, route changes, or transitions, prefer locator-aware "
            "Playwright waits such as locator.waitFor() instead of fixed sleeps."
        ),
    ),
    "svelte": SelectorPromptStrategy(
        framework="svelte",
        guidance=(
            "Detected framework: Svelte. Prefer accessible role/name locators, then stable "
            "data-testid or data-test hooks. Avoid compiled Svelte class names, generated "
            "attributes, transition-only state, and DOM structure that may shift during "
            "compilation. For transitions or reactive updates, prefer locator "
            "waits such as locator.waitFor() or page.waitForSelector() over arbitrary timeouts."
        ),
    ),
    "generic": SelectorPromptStrategy(
        framework="generic",
        guidance=(
            "Detected framework: generic or unknown. Prefer resilient Playwright locators in this "
            "order: role/name, label, text that reflects user-visible intent, then stable "
            "data-testid/data-test hooks. Avoid brittle CSS classes, generated ids, and DOM-depth "
            "selectors. Use locator-aware waits such as locator.waitFor() instead of fixed sleeps."
        ),
    ),
}


def normalize_framework(value: str | None) -> FrameworkName:
    """Normalize a detected framework name to one of the strategy keys."""
    normalized = (value or "").strip().lower()
    if normalized in {"react", "reactjs", "react.js", "next", "nextjs", "next.js"}:
        return "react"
    if normalized in {"vue", "vue3", "vue.js", "nuxt", "nuxtjs", "nuxt.js"}:
        return "vue"
    if normalized in {"svelte", "sveltekit", "svelte-kit"}:
        return "svelte"
    return "generic"


def selector_strategy_for(framework: str | None) -> SelectorPromptStrategy:
    """Return typed selector guidance for a framework, falling back to generic."""
    return SELECTOR_PROMPT_STRATEGIES[normalize_framework(framework)]


# Word-boundary patterns so substrings inside filenames or prose (e.g. "react" in
# "reactive-form.vue", or "next" in "the next button") do not trigger false matches.
# Bare "next" is intentionally excluded; only Next.js import-style markers count.
_VUE_PATTERN = re.compile(r"\bvue(?:js|3|\.js)?\b|\bnuxt(?:js|\.js)?\b")
_SVELTE_PATTERN = re.compile(r"\bsvelte(?:kit|-kit)?\b")
_REACT_PATTERN = re.compile(r"\breact(?:js|\.js|-dom)?\b|\bnext(?:js|\.js)\b|\bnext/")


def detect_framework(
    test_script_path: str,
    current_code: str,
    dom_diff_context: Sequence[DomDiffEntry],
) -> FrameworkName:
    """Infer the app framework from changed files, test imports, and nearby package.json files.

    Unambiguous signals (file extensions in the diff, token-aware framework names) are
    checked first, Vue/Svelte before React, so React substrings inside Vue/Svelte file
    names cannot shadow the real framework. Falls back to nearby package.json deps.
    """
    text = current_code.lower()
    diff_files = [str(item.get("file", "")).lower() for item in dom_diff_context]
    combined = f"{text} {' '.join(diff_files)}"

    if any(name.endswith(".vue") for name in diff_files) or _VUE_PATTERN.search(combined):
        return "vue"
    if any(name.endswith(".svelte") for name in diff_files) or _SVELTE_PATTERN.search(combined):
        return "svelte"
    if any(name.endswith((".jsx", ".tsx")) for name in diff_files) or _REACT_PATTERN.search(
        combined
    ):
        return "react"

    return _detect_framework_from_package_json(Path(test_script_path))


def build_system_prompt(framework: str | None) -> str:
    """Append framework-adaptive guidance without weakening the core guardrail."""
    strategy = selector_strategy_for(framework)
    return f"{SYSTEM_PROMPT}\n\nFramework-specific selector guidance:\n{strategy.guidance}"


def _detect_framework_from_package_json(test_script_path: Path) -> FrameworkName:
    start = test_script_path if test_script_path.is_dir() else test_script_path.parent
    for directory in (start, *start.parents):
        package_json = directory / "package.json"
        if not package_json.exists():
            continue
        try:
            package = json.loads(package_json.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            continue
        dependencies = {
            **package.get("dependencies", {}),
            **package.get("devDependencies", {}),
            **package.get("peerDependencies", {}),
        }
        names = {name.lower() for name in dependencies}
        if "react" in names or "react-dom" in names or "next" in names:
            return "react"
        if "vue" in names or "@vitejs/plugin-vue" in names or "nuxt" in names:
            return "vue"
        if "svelte" in names or "@sveltejs/kit" in names or "sveltekit" in names:
            return "svelte"
    return "generic"
