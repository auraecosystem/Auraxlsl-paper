"""Safe reader and writer for the XLSL v1 ZIP-based package format."""
from __future__ import annotations
import json
import os
import copy
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

FORMAT_NAME = "XLSL"
FORMAT_VERSION = "1.0.0"
MANIFEST_PATH = "manifest.json"
WORKBOOK_PATH = "workbook.json"
MAX_ARCHIVE_FILES = 256
MAX_TOTAL_UNCOMPRESSED_BYTES = 32 * 1024 * 1024
MAX_MEMBER_BYTES = 16 * 1024 * 1024


class XLSLFormatError(ValueError):
    """Raised when an XLSL package is malformed or unsafe."""


@dataclass
class XLSLDocument:
    """In-memory XLSL package; logic modules are preserved, never executed."""
    workbook: dict[str, Any]
    manifest: dict[str, Any] = field(default_factory=lambda: {
        "format": FORMAT_NAME, "format_version": FORMAT_VERSION
    })
    logic_modules: dict[str, str] = field(default_factory=dict)


def _reject_constant(value: str) -> None:
    raise XLSLFormatError(f"Non-standard JSON constant is not allowed: {value}")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise XLSLFormatError(f"Duplicate JSON object key: {key}")
        result[key] = value
    return result


def _decode_json(payload: bytes, member_name: str) -> dict[str, Any]:
    try:
        value = json.loads(payload.decode("utf-8"), object_pairs_hook=_unique_object,
                           parse_constant=_reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise XLSLFormatError(f"Invalid UTF-8 JSON in {member_name}") from exc
    if not isinstance(value, dict):
        raise XLSLFormatError(f"{member_name} must contain a JSON object")
    return value


def _validate_member_name(name: str) -> None:
    if not name or "\\" in name or name.startswith("/"):
        raise XLSLFormatError(f"Unsafe archive member path: {name!r}")
    if any(part in ("", ".", "..") for part in name.split("/")):
        raise XLSLFormatError(f"Unsafe archive member path: {name!r}")


def _validate_manifest(manifest: dict[str, Any]) -> None:
    if manifest.get("format") != FORMAT_NAME:
        raise XLSLFormatError("manifest.format must be 'XLSL'")
    if manifest.get("format_version") != FORMAT_VERSION:
        raise XLSLFormatError(f"Unsupported XLSL format version: {manifest.get('format_version')!r}")


def _validate_workbook_shape(workbook: dict[str, Any]) -> None:
    sheets = workbook.get("sheets")
    if not isinstance(sheets, dict) or not sheets:
        raise XLSLFormatError("workbook.sheets must be a non-empty object")
    for sheet_name, sheet in sheets.items():
        if not isinstance(sheet_name, str) or not sheet_name.strip():
            raise XLSLFormatError("Sheet names must be non-empty strings")
        if not isinstance(sheet, dict):
            raise XLSLFormatError(f"Sheet {sheet_name!r} must be an object")
        columns, rows = sheet.get("columns"), sheet.get("rows")
        if not isinstance(columns, list):
            raise XLSLFormatError(f"Sheet {sheet_name!r} columns must be an array")
        column_names = []
        for column in columns:
            if isinstance(column, str) and column:
                column_names.append(column)
            elif isinstance(column, dict) and isinstance(column.get("name"), str) and column["name"]:
                column_names.append(column["name"])
            else:
                raise XLSLFormatError(f"Sheet {sheet_name!r} has an invalid column definition")
        if len(set(column_names)) != len(column_names):
            raise XLSLFormatError(f"Sheet {sheet_name!r} has duplicate column names")
        if not isinstance(rows, list):
            raise XLSLFormatError(f"Sheet {sheet_name!r} rows must be an array")
        for row_number, row in enumerate(rows, start=1):
            if not isinstance(row, list) or len(row) != len(columns):
                raise XLSLFormatError(
                    f"Sheet {sheet_name!r} row {row_number} must have exactly {len(columns)} values"
                )


def read_xlsl(path: str | os.PathLike[str]) -> XLSLDocument:
    """Read a native XLSL package without extracting archive members."""
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(source)
    try:
        with zipfile.ZipFile(source, "r") as archive:
            members = archive.infolist()
            if len(members) > MAX_ARCHIVE_FILES:
                raise XLSLFormatError("XLSL package contains too many archive entries")
            names: set[str] = set()
            total_size = 0
            for member in members:
                _validate_member_name(member.filename)
                if member.filename in names:
                    raise XLSLFormatError(f"Duplicate archive member: {member.filename}")
                names.add(member.filename)
                if member.flag_bits & 0x1:
                    raise XLSLFormatError("Encrypted archive members are not supported")
                if member.file_size > MAX_MEMBER_BYTES:
                    raise XLSLFormatError(f"Archive member is too large: {member.filename}")
                total_size += member.file_size
                if total_size > MAX_TOTAL_UNCOMPRESSED_BYTES:
                    raise XLSLFormatError("XLSL package exceeds the size limit")
                mode = member.external_attr >> 16
                if (mode & 0o170000) == 0o120000:
                    raise XLSLFormatError("Symbolic links are not allowed in XLSL")
            required = {MANIFEST_PATH, WORKBOOK_PATH}
            if not required.issubset(names):
                raise XLSLFormatError("XLSL package needs manifest.json and workbook.json")
            logic_names = set()
            for name in names - required:
                if not name.startswith("logic/") or not name.endswith(".xsl"):
                    raise XLSLFormatError(f"Unsupported package entry: {name}")
                logic_names.add(name)
            manifest = _decode_json(archive.read(MANIFEST_PATH), MANIFEST_PATH)
            workbook = _decode_json(archive.read(WORKBOOK_PATH), WORKBOOK_PATH)
            logic_modules = {}
            for name in sorted(logic_names):
                try:
                    logic_modules[name] = archive.read(name).decode("utf-8")
                except UnicodeDecodeError as exc:
                    raise XLSLFormatError(f"Logic module is not UTF-8: {name}") from exc
    except zipfile.BadZipFile as exc:
        raise XLSLFormatError("File is not a valid XLSL ZIP package") from exc
    _validate_manifest(manifest)
    _validate_workbook_shape(workbook)
    from .validation import validate_workbook
    valid, report = validate_workbook(workbook)
    if not valid:
        raise XLSLFormatError(f"Workbook schema validation failed: {report['errors']}")
    return XLSLDocument(manifest=manifest, workbook=workbook, logic_modules=logic_modules)


def write_xlsl(document: XLSLDocument, path: str | os.PathLike[str]) -> Path:
    """Write an XLSL package atomically; embedded logic remains inert text."""
    manifest = dict(document.manifest)
    _validate_manifest(manifest)
    _validate_workbook_shape(document.workbook)
    from .validation import validate_workbook
    valid, report = validate_workbook(document.workbook)
    if not valid:
        raise XLSLFormatError(f"Workbook schema validation failed: {report['errors']}")
    for name, source in document.logic_modules.items():
        _validate_member_name(name)
        if not name.startswith("logic/") or not name.endswith(".xsl"):
            raise XLSLFormatError("Logic module paths must be inside logic/ and end in .xsl")
        if not isinstance(source, str):
            raise XLSLFormatError(f"Logic module {name!r} must be text")
    payloads = {
        MANIFEST_PATH: json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False).encode("utf-8"),
        WORKBOOK_PATH: json.dumps(document.workbook, ensure_ascii=False, indent=2, allow_nan=False).encode("utf-8"),
    }
    payloads.update({name: source.encode("utf-8") for name, source in document.logic_modules.items()})
    if len(payloads) > MAX_ARCHIVE_FILES:
        raise XLSLFormatError("XLSL package contains too many entries")
    if any(len(payload) > MAX_MEMBER_BYTES for payload in payloads.values()):
        raise XLSLFormatError("An XLSL package entry exceeds the size limit")
    if sum(map(len, payloads.values())) > MAX_TOTAL_UNCOMPRESSED_BYTES:
        raise XLSLFormatError("XLSL package exceeds the size limit")
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_name = None
    try:
        with tempfile.NamedTemporaryFile(prefix=f".{destination.name}.", suffix=".tmp",
                                         dir=destination.parent, delete=False) as temporary:
            temporary_name = temporary.name
        with zipfile.ZipFile(temporary_name, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, payload in sorted(payloads.items()):
                archive.writestr(name, payload)
        os.replace(temporary_name, destination)
    except Exception:
        if temporary_name and os.path.exists(temporary_name):
            os.unlink(temporary_name)
        raise
    return destination



def update_xlsl(
    path: str | os.PathLike[str],
    updater: Any,
) -> XLSLDocument:
    """Apply a workbook updater and atomically replace the package on success.

    The updater receives a deep copy of the workbook. It may mutate that copy
    and return None, or return a replacement workbook dictionary.
    """
    if not callable(updater):
        raise TypeError("updater must be callable")
    source = Path(path)
    document = read_xlsl(source)
    workbook = copy.deepcopy(document.workbook)
    replacement = updater(workbook)
    if replacement is not None:
        if not isinstance(replacement, dict):
            raise XLSLFormatError("Workbook updater must return a dictionary or None")
        workbook = replacement

    updated = XLSLDocument(
        workbook=workbook,
        manifest=copy.deepcopy(document.manifest),
        logic_modules=copy.deepcopy(document.logic_modules),
    )
    temporary_name = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=f".{source.name}.", suffix=".xlsl", dir=source.parent, delete=False
        ) as temporary:
            temporary_name = temporary.name
        write_xlsl(updated, temporary_name)
        os.replace(temporary_name, source)
    except Exception:
        if temporary_name and os.path.exists(temporary_name):
            os.unlink(temporary_name)
        raise
    return updated
