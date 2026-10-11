"""Versioned UTF-8 packages with bounded restoration and integrity checks."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from .context_optimizer import PackedContext, aggregate_repeated_runs, restore_repeated_runs

FORMAT = "nexura-context-package"
FORMAT_VERSION = 1
MAX_SOURCE_BYTES = 8 * 1024 * 1024
MAX_PACKAGE_BYTES = 32 * 1024 * 1024
_HASH = re.compile(r"[0-9a-f]{64}")
_NAMESPACE = re.compile(r"[0-9a-f]{32}")
_FIELDS = {
    "format", "format_version", "encoding", "source_sha256",
    "source_byte_length", "packed_text", "dictionary", "namespace", "separator",
}


def make_package(
    original: bytes,
    *,
    minimum_block_chars: int = 80,
    minimum_run: int = 3,
) -> dict[str, Any]:
    """Pack valid UTF-8 bytes, retaining everything needed to restore them."""
    if not isinstance(original, bytes):
        raise ValueError("source must be bytes")
    if len(original) > MAX_SOURCE_BYTES:
        raise ValueError("source exceeds the 8 MiB limit")
    text = original.decode("utf-8")
    packed = aggregate_repeated_runs(
        text, minimum_block_chars=minimum_block_chars, minimum_run=minimum_run
    )
    package: dict[str, Any] = {
        "format": FORMAT,
        "format_version": FORMAT_VERSION,
        "encoding": "utf-8",
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "source_byte_length": len(original),
        "packed_text": packed.text,
        "dictionary": packed.dictionary,
        "namespace": packed.namespace,
        "separator": packed.separator,
    }
    if restore_package(package) != original:
        raise ValueError("packing failed exact round-trip validation")
    return package


def restore_package(package: object) -> bytes:
    """Reconstruct bytes without executing content; SHA-256 is not a signature."""
    if not isinstance(package, dict) or set(package) != _FIELDS:
        raise ValueError("invalid package fields")
    if package["format"] != FORMAT:
        raise ValueError("unsupported package format")
    if type(package["format_version"]) is not int or package["format_version"] != FORMAT_VERSION:
        raise ValueError("unsupported package version")
    if package["encoding"] != "utf-8":
        raise ValueError("unsupported package encoding")
    source_size = package["source_byte_length"]
    if type(source_size) is not int or not 0 <= source_size <= MAX_SOURCE_BYTES:
        raise ValueError("invalid source byte length")
    source_hash = package["source_sha256"]
    if not isinstance(source_hash, str) or _HASH.fullmatch(source_hash) is None:
        raise ValueError("invalid source hash")
    packed_text = package["packed_text"]
    if not isinstance(packed_text, str) or len(packed_text.encode("utf-8")) > MAX_SOURCE_BYTES:
        raise ValueError("invalid or oversized packed text")
    namespace = package["namespace"]
    if namespace is not None and (
        not isinstance(namespace, str) or _NAMESPACE.fullmatch(namespace) is None
    ):
        raise ValueError("invalid namespace")
    separator = package["separator"]
    if separator not in ("\n\n", "\r\n\r\n"):
        raise ValueError("invalid paragraph separator")
    dictionary = package["dictionary"]
    if not isinstance(dictionary, dict):
        raise ValueError("invalid dictionary")
    dictionary_bytes = 0
    for content_id, content in dictionary.items():
        if not isinstance(content_id, str) or _HASH.fullmatch(content_id) is None:
            raise ValueError("invalid dictionary identifier")
        if not isinstance(content, str):
            raise ValueError("invalid dictionary content")
        content_bytes = content.encode("utf-8")
        dictionary_bytes += len(content_bytes)
        if dictionary_bytes > MAX_SOURCE_BYTES:
            raise ValueError("dictionary exceeds the size limit")
        if hashlib.sha256(content_bytes).hexdigest() != content_id:
            raise ValueError("dictionary integrity check failed")
    if namespace is None and dictionary:
        raise ValueError("dictionary requires an envelope namespace")
    if namespace is not None and not dictionary:
        raise ValueError("envelope requires a dictionary")
    restored = restore_repeated_runs(
        PackedContext(packed_text, dictionary, namespace, separator),
        max_repeat_count=100_000,
        max_restored_characters=MAX_SOURCE_BYTES,
    ).encode("utf-8")
    if len(restored) != source_size or hashlib.sha256(restored).hexdigest() != source_hash:
        raise ValueError("original integrity check failed")
    return restored
