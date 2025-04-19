# Basic Code Cleanup Guidelines

This document outlines basic code cleanup practices to improve code readability, maintainability, and robustness. Apply these guidelines when refactoring existing code.

## Guidelines

1.  **Use Constants for Literals:**
    *   Identify all literal strings used in the code (e.g., `"RUNNING"`, `"start"`).
    *   **Exclude:** Literal strings used *only* within logging messages or exception messages.
    *   Refactor these literals into constants defined at the module level.
    *   Use meaningful, uppercase names for constants (e.g., `SESSION_STATE_RUNNING`, `ACTION_START`).
    *   Replace all occurrences of the literal string with the corresponding constant. This is especially important for strings that appear multiple times.

2.  **Use Constants for Magic Numbers:**
    *   Identify any "magic numbers" (numeric literals with unclear meaning) used directly in the code.
    *   Refactor these numbers into constants defined at the module level.
    *   Use meaningful, uppercase names for constants (e.g., `MAX_RETRIES = 3`, `DEFAULT_TIMEOUT_SECONDS = 60`).
    *   Replace all occurrences of the magic number with the corresponding constant.

3.  **Function Length and Decomposition:**
    *   Identify functions that are significantly longer than approximately 10-15 lines of code (excluding comments and blank lines).
    *   Break down these long functions into smaller, more focused helper functions.
    *   Each helper function should perform a single, well-defined task.
    *   Give helper functions clear, descriptive names, often prefixed with an underscore (`_`) if they are intended for internal use within the module.
    *   Call these helper functions from the original function, replacing the code blocks that were extracted.

## Constraints

*   **Preserve Functionality:** The primary goal is refactoring for clarity, not changing behavior. Ensure the code functions identically after the cleanup.
*   **Minimal Changes:** Only make changes necessary to adhere to the guidelines above. Avoid unnecessary restructuring or stylistic changes.
*   **File Scope:** Apply these changes only within the targeted file(s) unless explicitly requested otherwise. 