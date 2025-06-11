"""Utilities for analyzing the repository's source code."""

from __future__ import annotations

import os
import ast
from typing import List, Dict, Any

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def list_python_files() -> List[str]:
    """Return a list of all Python files in the repository."""
    py_files: List[str] = []
    for root, _, files in os.walk(REPO_ROOT):
        for name in files:
            if name.endswith(".py") and name != os.path.basename(__file__):
                path = os.path.relpath(os.path.join(root, name), REPO_ROOT)
                py_files.append(path)
    return sorted(py_files)


def read_file(path: str) -> str:
    """Return the contents of ``path`` relative to the repository root."""
    full = os.path.join(REPO_ROOT, path)
    with open(full, "r", encoding="utf-8") as f:
        return f.read()


def search_code(pattern: str) -> List[Dict[str, Any]]:
    """Search all Python files for ``pattern`` and return matching lines."""
    matches: List[Dict[str, Any]] = []
    for file in list_python_files():
        full = os.path.join(REPO_ROOT, file)
        with open(full, "r", encoding="utf-8") as f:
            for lineno, line in enumerate(f, 1):
                if pattern in line:
                    matches.append(
                        {"file": file, "line": lineno, "text": line.rstrip()}
                    )
    return matches


def summarize_codebase() -> Dict[str, Any]:
    """Return a summary of functions and classes in each Python file."""
    summary: Dict[str, Any] = {}
    for file in list_python_files():
        full = os.path.join(REPO_ROOT, file)
        with open(full, "r", encoding="utf-8") as f:
            try:
                tree = ast.parse(f.read(), filename=file)
            except SyntaxError:
                continue
        funcs = [
            n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
        ]  # noqa: E501
        classes = [
            n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)
        ]  # noqa: E501
        summary[file] = {
            "functions": funcs,
            "classes": classes,
        }
    return summary
