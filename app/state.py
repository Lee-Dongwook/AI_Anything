"""Shared LangGraph state for the repair loop.

The state is a plain ``TypedDict`` so it stays immutable/traceable across nodes:
each node reads from it and returns a partial update dict.
"""

from typing import TypedDict


class AgentState(TypedDict):
    test_script_path: str         # path to the test file under repair
    original_code: str            # the original test script
    current_code: str             # test script as modified in the current loop
    error_log: str                # latest Playwright error log (abstracted)
    dom_diff_context: list[dict]  # DOM changes from AST parsing
    analysis_report: str          # Diagnoser's failure-cause report
    patch_instructions: dict      # Patch Generator's fix guide (line, code)
    loop_count: int               # infinite-loop guard (max: settings.max_loops)
    is_success: bool              # whether the test passed
