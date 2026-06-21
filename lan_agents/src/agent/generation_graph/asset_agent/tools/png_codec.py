"""Small RGBA PNG helpers used by Asset Agent tests and fallbacks."""

from __future__ import annotations

import binascii
import struct
import zlib
from pathlib import Path
from typing import Callable

RGBA = tuple[int, int, int, int]

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def write_png_rgba(
    path: Path,
    width: int,
    height: int,
    pixel_at: Callable[[int, int], RGBA],
) -> None:
    """Write a simple non-interlaced 8-bit RGBA PNG."""
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for x in range(width):
            rows.extend(_clamp_channel(channel) for channel in pixel_at(x, y))
    chunks = [
        _chunk(
            b"IHDR",
            struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0),
        ),
        _chunk(b"IDAT", zlib.compress(bytes(rows), level=6)),
        _chunk(b"IEND", b""),
    ]
    path.write_bytes(PNG_SIGNATURE + b"".join(chunks))


def read_png_info(path: Path) -> dict[str, int]:
    """Return width, height and color type from a PNG IHDR chunk."""
    data = path.read_bytes()
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError("not a PNG file")
    offset = len(PNG_SIGNATURE)
    while offset < len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        chunk_data = data[offset + 8 : offset + 8 + length]
        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, _, _, _ = struct.unpack(
                ">IIBBBBB", chunk_data
            )
            if bit_depth != 8:
                raise ValueError("unsupported PNG bit depth")
            return {"width": width, "height": height, "color_type": color_type}
        offset += 12 + length
    raise ValueError("PNG IHDR chunk not found")


def _chunk(chunk_type: bytes, data: bytes) -> bytes:
    crc = binascii.crc32(chunk_type + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)


def _clamp_channel(value: int) -> int:
    return max(0, min(255, int(value)))
