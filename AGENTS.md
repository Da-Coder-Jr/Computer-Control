# AGENTS.md

## 1. Overview

This file defines guidelines and context for Codex to operate effectively in this repository. Adhere to these instructions to ensure consistent, high-quality automated changes without guessing or altering unknown structures.

## 2. Development Environment

1. **Python**: 3.11.x (managed via pyenv).
2. **Dependencies**:

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
3. **Optional Tools**:

   * **pyright**: `pip install pyright`
   * **flake8**: `pip install flake8`

## 3. Setup Scripts

Scripts run before any Codex task. Use this section to install tools and dependencies:

```bash
# Install Python type checker and formatter
pip install pyright black

# Install project dependencies
dependencies="-r requirements.txt"
pip install $dependencies
```

## 4. Testing & Verification

Codex **must** validate every change with robust testing and fail-fast checks:

```bash
# 1. Run full test suite with pytest
pytest --maxfail=1 --disable-warnings -q

# 2. Run lint checks
flake8 .

# 3. (Optional) Run type checks
pyright
```

* **Always** break on first failure (`--maxfail=1`).
* **Ensure** 100% test coverage for any new functionality. Add tests if missing.
* **Report** failing tests or coverage shortfalls in the diff comments.

## 5. Coding Standards

* **Style**: Follow PEP8.
* **Formatting**: Auto-format with `black` before committing.
* **Imports**: Group imports: standard library, third-party, local.
* **Docstrings**: Mandatory for public functions and classes.
* **Type hints**: Use annotations for all function signatures.

## 6. PR & Commit Guidelines

* **Branch Name**: `feature/<short-description>` or `fix/<short-description>`.
* **Commit Message**: `<Type>(<scope>): <short summary>`

  * Types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`.
  * Example: `fix(controller): handle missing GUI gracefully`
* **PR Title**: Mirror the commit message.
* **PR Description**:

  1. **Context**: What problem is addressed?
  2. **Solution**: How is it solved?
  3. **Verification**: Test commands and results.

## 7. Agent Behavior & Constraints

* **Precision**: Only modify files/lines explicitly requested. - Unless improving code!
* **No Guessing**: If unsure of structure or intent, ask for clarification.
* **Conflict Resolution**: Never introduce Git conflict markers (`<<<<<<<`).
* **Feedback Loop**: Include test failures or lint errors in responses.
* **Always Improving**: Always improve the code in some way!
* **Bug hunter**: Always find all bugs in the code! If you don't that is fine because we all make mistakes! Try your BEST to hunt errors/bugs and fix the code.
*  **Up to date**: Always include up-to-date code edits in you code. So stay up-to-date!

## 8. Prompting Tips for Codex

* **File Paths**: Always use explicit paths in prompts.
* **Verification**: Request test and lint command results.
* **Incremental**: Break large tasks into small, testable steps.

---

*End of AGENTS.md*
