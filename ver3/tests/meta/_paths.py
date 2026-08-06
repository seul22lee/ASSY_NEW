"""Shared locations and loaders for the meta-tests.

Kept deliberately small. A test helper that grows logic starts hiding the thing
the test is supposed to assert.
"""

import ast
import os
from typing import Dict, Iterator, List, Tuple

import yaml

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
VER3 = os.path.join(REPO_ROOT, "ver3")
ASSY_V3 = os.path.join(VER3, "assy_v3")
CONTRACTS = os.path.join(VER3, "contracts")
BENCHMARKS = os.path.join(VER3, "benchmarks")

FORBIDDEN_YAML = os.path.join(VER3, "FORBIDDEN_LEGACY_DEPENDENCIES.yaml")
RETIREMENT_YAML = os.path.join(VER3, "RETIREMENT_MATRIX.yaml")

CONTRACT_FILES = [
    "DESIGN_STATE_CONTRACT.yaml",
    "STAGE_PATCH_CONTRACT.yaml",
    "STAGE_OWNERSHIP_MATRIX.yaml",
    "STATUS_SEMANTICS.yaml",
    "PROVENANCE_CONTRACT.yaml",
    "MODEL_RUN_RECORD_CONTRACT.yaml",
    "BENCHMARK_RESULT_CONTRACT.yaml",
    "GENERATED_ASSURANCE_PACKAGE_CONTRACT.yaml",
    "STAGE_PROGRESSION_CONTRACT.yaml",
]

STAGE_IDS = ["s%02d" % n for n in range(1, 13)]


def load_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def contract(name: str) -> dict:
    return load_yaml(os.path.join(CONTRACTS, name))


def assy_v3_sources() -> Iterator[Tuple[str, str]]:
    """Yield (relative_path, source_text) for every .py file under assy_v3."""
    for dirpath, dirnames, filenames in os.walk(ASSY_V3):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for fn in sorted(filenames):
            if not fn.endswith(".py"):
                continue
            full = os.path.join(dirpath, fn)
            with open(full, "r", encoding="utf-8") as fh:
                yield os.path.relpath(full, REPO_ROOT), fh.read()


def parsed_assy_v3() -> Iterator[Tuple[str, str, ast.Module]]:
    for rel, src in assy_v3_sources():
        yield rel, src, ast.parse(src, filename=rel)


def docstring_nodes(tree: ast.Module) -> set:
    """Identify the string Constant nodes that are docstrings.

    Docstrings are prose. The naming and pattern rules apply to code, and a
    comment explaining why a name is forbidden must not be the thing that trips
    the check on that name.
    """
    out = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        body = getattr(node, "body", None)
        if not body:
            continue
        first = body[0]
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) \
                and isinstance(first.value.value, str):
            out.add(id(first.value))
    return out


def docstring_line_numbers(tree: ast.Module) -> set:
    """Every source line occupied by a docstring.

    Used to exempt prose from the raw-source pattern scan. A module that explains
    why ``or "mm"`` is forbidden must be able to write it down.
    """
    docs = docstring_nodes(tree)
    lines = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) in docs:
            start = getattr(node, "lineno", 0)
            end = getattr(node, "end_lineno", start)
            lines.update(range(start, end + 1))
    return lines


def code_strings(tree: ast.Module) -> List[Tuple[int, str]]:
    """Every string literal that is NOT a docstring, with its line number."""
    docs = docstring_nodes(tree)
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docs:
            out.append((getattr(node, "lineno", 0), node.value))
    return out


def identifiers(tree: ast.Module) -> List[Tuple[int, str]]:
    """Every name the code defines or uses: variables, attributes, args, imports."""
    out = []
    for node in ast.walk(tree):
        line = getattr(node, "lineno", 0)
        if isinstance(node, ast.Name):
            out.append((line, node.id))
        elif isinstance(node, ast.Attribute):
            out.append((line, node.attr))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.append((line, node.name))
        elif isinstance(node, ast.arg):
            out.append((line, node.arg))
        elif isinstance(node, ast.alias):
            out.append((line, node.name))
            if node.asname:
                out.append((line, node.asname))
        elif isinstance(node, ast.keyword) and node.arg:
            out.append((line, node.arg))
    return out


def import_roots(tree: ast.Module) -> List[Tuple[int, str]]:
    """Top-level module name of every import, with line number.

    A relative import (``from .status import X``) has no root and is not a
    dependency on anything outside the package, so it is skipped.
    """
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.append((node.lineno, alias.name.split(".")[0]))
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                continue
            if node.module:
                out.append((node.lineno, node.module.split(".")[0]))
    return out
