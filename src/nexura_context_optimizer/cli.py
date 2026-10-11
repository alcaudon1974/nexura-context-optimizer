"""Local, reversible context packages; no network or model calls."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

from .package import MAX_PACKAGE_BYTES, MAX_SOURCE_BYTES, make_package, restore_package


def _inside(path: Path, workspace: Path, label: str) -> None:
    try:
        path.relative_to(workspace)
    except ValueError as error:
        raise ValueError(f"{label} must remain inside the selected workspace") from error


def _paths(args: argparse.Namespace) -> tuple[Path, Path, Path]:
    workspace = Path(args.workspace).resolve(strict=True)
    if not workspace.is_dir():
        raise ValueError("workspace must be a directory")
    source = (workspace / args.source).resolve(strict=True)
    output = (workspace / args.output).resolve(strict=False)
    _inside(source, workspace, "source")
    _inside(output, workspace, "output")
    if not source.is_file():
        raise ValueError("source must be a regular file")
    if os.path.lexists(output):
        raise FileExistsError("output already exists and will not be overwritten")
    return source, output, workspace


def _read_bounded(source: Path, limit: int) -> bytes:
    with source.open("rb") as handle:
        data = handle.read(limit + 1)
    if len(data) > limit:
        raise ValueError("input exceeds the configured size limit")
    return data


def _write_new(output: Path, workspace: Path, data: bytes) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    parent = output.parent.resolve(strict=True)
    _inside(parent, workspace, "output directory")
    destination = parent / output.name
    created = False
    try:
        with destination.open("xb") as handle:
            created = True
            handle.write(data)
    except Exception:
        if created:
            destination.unlink(missing_ok=True)
        raise


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON field")
        result[key] = value
    return result


def _optimize(args: argparse.Namespace) -> int:
    source, output, workspace = _paths(args)
    original = _read_bounded(source, MAX_SOURCE_BYTES)
    package = make_package(
        original, minimum_block_chars=args.minimum_block_chars, minimum_run=args.minimum_run
    )
    serialized = (json.dumps(package, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if len(serialized) > MAX_PACKAGE_BYTES:
        raise ValueError("serialized package exceeds the size limit")
    _write_new(output, workspace, serialized)
    print(json.dumps({
        "source": str(source), "output": str(output),
        "original_characters": len(original.decode("utf-8")),
        "packed_characters": len(package["packed_text"]),
        "package_bytes": len(serialized),
        "dictionary_entries": len(package["dictionary"]), "round_trip_exact": True,
    }, ensure_ascii=False))
    return 0


def _restore(args: argparse.Namespace) -> int:
    source, output, workspace = _paths(args)
    data = _read_bounded(source, MAX_PACKAGE_BYTES).decode("utf-8")
    package = json.loads(data, object_pairs_hook=_unique_object)
    original = restore_package(package)
    _write_new(output, workspace, original)
    print(json.dumps({
        "source": str(source), "output": str(output),
        "restored_bytes": len(original),
        "source_sha256": hashlib.sha256(original).hexdigest(), "integrity_verified": True,
    }, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nexura-context")
    parser.add_argument("--workspace", default=str(Path.cwd()), help="allowed input/output directory")
    subparsers = parser.add_subparsers(dest="command", required=True)
    optimize = subparsers.add_parser("optimize", help="create a reversible JSON package")
    optimize.add_argument("source")
    optimize.add_argument("--output", required=True)
    optimize.add_argument("--minimum-block-chars", type=int, default=80)
    optimize.add_argument("--minimum-run", type=int, default=3)
    optimize.set_defaults(handler=_optimize)
    restore = subparsers.add_parser("restore", help="restore original UTF-8 bytes from a package")
    restore.add_argument("source")
    restore.add_argument("--output", required=True)
    restore.set_defaults(handler=_restore)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.handler(args)
    except (OSError, ValueError, UnicodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
