"""Explicit, opt-in workbook schema migrations.

Migrations are registered by application code. This module never guesses how
user data should be transformed and never rewrites a package on its own.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Callable

from .package import XLSLFormatError

Migration = Callable[[dict[str, Any]], dict[str, Any] | None]


@dataclass(frozen=True)
class MigrationResult:
    workbook: dict[str, Any]
    applied: tuple[tuple[int, int], ...]
    dry_run: bool


class MigrationRegistry:
    """Registry of explicit, directed schema-version migration functions."""

    def __init__(self) -> None:
        self._steps: dict[tuple[int, int], Migration] = {}

    def register(self, from_version: int, to_version: int, transform: Migration) -> None:
        if (not isinstance(from_version, int) or isinstance(from_version, bool)
                or not isinstance(to_version, int) or isinstance(to_version, bool)
                or from_version < 1 or to_version <= from_version):
            raise ValueError("Migration versions must be positive integers and move forward")
        if not callable(transform):
            raise TypeError("Migration transform must be callable")
        key = (from_version, to_version)
        if key in self._steps:
            raise ValueError(f"Migration {from_version} -> {to_version} is already registered")
        self._steps[key] = transform

    def plan(self, from_version: int, to_version: int) -> tuple[tuple[int, int], ...]:
        """Return the shortest deterministic migration path or raise."""
        if from_version == to_version:
            return ()
        frontier: list[tuple[int, tuple[tuple[int, int], ...]]] = [(from_version, ())]
        visited = {from_version}
        while frontier:
            version, path = frontier.pop(0)
            for edge in sorted((e for e in self._steps if e[0] == version), key=lambda e: e[1]):
                next_path = path + (edge,)
                if edge[1] == to_version:
                    return next_path
                if edge[1] not in visited and edge[1] < to_version:
                    visited.add(edge[1])
                    frontier.append((edge[1], next_path))
        raise XLSLFormatError(f"No registered migration path from schema {from_version} to {to_version}")

    def migrate(
        self, workbook: dict[str, Any], target_version: int, *, dry_run: bool = True
    ) -> MigrationResult:
        """Apply a registered path to a copy; persist only when the caller chooses."""
        from .validation import validate_workbook

        source_version = workbook.get("schema_version", 1)
        if not isinstance(source_version, int) or isinstance(source_version, bool):
            raise XLSLFormatError(f"Invalid source schema version: {source_version!r}")
        path = self.plan(source_version, target_version)
        candidate = deepcopy(workbook)
        for from_version, to_version in path:
            transformed = self._steps[(from_version, to_version)](candidate)
            if transformed is not None:
                if not isinstance(transformed, dict):
                    raise XLSLFormatError("Migration must return a workbook object or None")
                candidate = transformed
            candidate["schema_version"] = to_version
            valid, report = validate_workbook(candidate)
            if not valid:
                raise XLSLFormatError(
                    f"Migration {from_version} -> {to_version} produced an invalid workbook: "
                    f"{report['errors']}"
                )
        return MigrationResult(workbook=candidate, applied=path, dry_run=dry_run)
