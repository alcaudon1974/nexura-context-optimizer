"""Deterministic, bounded and exactly reversible context transformations."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

_DEFAULT_SEPARATOR = "\n\n"
_MAX_REPEAT_COUNT = 100_000
_MAX_RESTORED_CHARACTERS = 50_000_000
_REPEAT_V1_PATTERN = re.compile(
    r"^\[\[CTX_REPEAT_V1 nonce=([0-9a-f]{32}) count=([1-9][0-9]*) "
    r"id=([0-9a-f]{64})\]\]\r?\n(.*)$",
    re.DOTALL,
)


@dataclass(frozen=True)
class PackedContext:
    """A model-facing context plus metadata required for safe restoration."""

    text: str
    dictionary: dict[str, str]
    namespace: str | None = None
    separator: str = _DEFAULT_SEPARATOR


def _content_id(block: str) -> str:
    return hashlib.sha256(block.encode("utf-8")).hexdigest()


def _choose_namespace(text: str) -> str:
    """Choose a deterministic namespace that cannot collide with source text."""
    counter = 0
    while True:
        material = f"ctx-envelope-v1:{counter}:{text}".encode("utf-8")
        namespace = hashlib.sha256(material).hexdigest()[:32]
        if namespace not in text:
            return namespace
        counter += 1


def _detect_separator(text: str) -> str:
    """Preserve the document's paragraph line-ending convention."""
    crlf_index = text.find("\r\n\r\n")
    lf_index = text.find("\n\n")
    if crlf_index >= 0 and (lf_index < 0 or crlf_index <= lf_index):
        return "\r\n\r\n"
    return _DEFAULT_SEPARATOR


def aggregate_repeated_runs(
    text: str, minimum_block_chars: int = 80, minimum_run: int = 3
) -> PackedContext:
    """Run-length encode consecutive identical paragraph-sized blocks.

    Only profitable repeated runs are transformed. A collision-free envelope
    namespace distinguishes generated control markers from literal user data.
    """
    if minimum_block_chars < 0:
        raise ValueError("minimum_block_chars must be non-negative")
    if minimum_run < 2:
        raise ValueError("minimum_run must be at least 2")

    separator = _detect_separator(text)
    line_break = "\r\n" if separator == "\r\n\r\n" else "\n"
    blocks = text.split(separator)
    runs: list[tuple[str, int]] = []
    index = 0
    while index < len(blocks):
        block = blocks[index]
        end = index + 1
        while end < len(blocks) and blocks[end] == block:
            end += 1
        runs.append((block, end - index))
        index = end

    namespace = _choose_namespace(text)
    transformable: list[bool] = []
    for block, count in runs:
        content_id = _content_id(block)
        encoded = (
            f"[[CTX_REPEAT_V1 nonce={namespace} count={count} id={content_id}]]"
            f"{line_break}{block}"
        )
        original_length = len(separator.join([block] * count))
        transformable.append(
            count >= minimum_run
            and len(block) >= minimum_block_chars
            and len(encoded) < original_length
        )

    if not any(transformable):
        return PackedContext(
            text=text, dictionary={}, namespace=None, separator=separator
        )

    packed_blocks = [f"[[CTX_ENVELOPE_V1 nonce={namespace}]]"]
    dictionary: dict[str, str] = {}
    for (block, count), should_transform in zip(runs, transformable, strict=True):
        if not should_transform:
            packed_blocks.extend([block] * count)
            continue
        content_id = _content_id(block)
        packed_blocks.append(
            f"[[CTX_REPEAT_V1 nonce={namespace} count={count} id={content_id}]]"
            f"{line_break}{block}"
        )
        dictionary[content_id] = block

    packed_text = separator.join(packed_blocks)
    if len(packed_text) >= len(text):
        return PackedContext(
            text=text, dictionary={}, namespace=None, separator=separator
        )
    return PackedContext(
        text=packed_text,
        dictionary=dictionary,
        namespace=namespace,
        separator=separator,
    )


def restore_repeated_runs(
    packed: PackedContext,
    *,
    max_repeat_count: int = _MAX_REPEAT_COUNT,
    max_restored_characters: int = _MAX_RESTORED_CHARACTERS,
) -> str:
    """Restore a generated envelope with strict integrity and resource limits."""
    if packed.namespace is None:
        return packed.text
    if max_repeat_count < 1 or max_restored_characters < 1:
        raise ValueError("restoration limits must be positive")

    blocks = packed.text.split(packed.separator)
    expected_header = f"[[CTX_ENVELOPE_V1 nonce={packed.namespace}]]"
    if not blocks or blocks[0] != expected_header:
        raise ValueError("invalid or missing CTX envelope")

    restored: list[str] = []
    restored_characters = 0
    for block in blocks[1:]:
        match = _REPEAT_V1_PATTERN.fullmatch(block)
        if not match:
            restored.append(block)
            restored_characters += len(block)
        else:
            namespace, count_text, content_id, content = match.groups()
            if namespace != packed.namespace:
                restored.append(block)
                restored_characters += len(block)
                continue
            if packed.dictionary.get(content_id) != content or _content_id(content) != content_id:
                raise ValueError("CTX content integrity check failed")
            count = int(count_text)
            if count > max_repeat_count:
                raise ValueError("repeat count exceeds configured limit")
            projected = restored_characters + len(content) * count
            if restored:
                projected += len(packed.separator) * count
            else:
                projected += len(packed.separator) * max(0, count - 1)
            if projected > max_restored_characters:
                raise ValueError("restored context exceeds configured size limit")
            restored.extend([content] * count)
            restored_characters = projected

        if restored_characters > max_restored_characters:
            raise ValueError("restored context exceeds configured size limit")

    result = packed.separator.join(restored)
    if len(result) > max_restored_characters:
        raise ValueError("restored context exceeds configured size limit")
    return result

