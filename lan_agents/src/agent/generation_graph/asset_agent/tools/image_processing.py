"""Deterministic image processing helpers for Asset Agent MVP."""

from __future__ import annotations

from pathlib import Path
import struct
import zlib

from agent.generation_graph.asset_agent.tools.png_codec import (
    PNG_SIGNATURE,
    RGBA,
    write_png_rgba,
)
from agent.providers import ProviderError

MAGENTA_KEY = (255, 0, 255)


def write_mock_background(path: Path, width: int = 1280, height: int = 720) -> None:
    """Create a deterministic game-stage background fallback."""

    def pixel_at(x: int, y: int) -> RGBA:
        sky = int(180 + 45 * (1 - y / max(1, height - 1)))
        ground_line = int(height * 0.68)
        if y > ground_line:
            return (54, 132 + (x * 17 // width), 76, 255)
        if x < width * 0.16 or x > width * 0.84:
            return (48, 116, 74, 255)
        return (96, sky, 186, 255)

    write_png_rgba(path, width, height, pixel_at)


def write_mock_player_raw(path: Path, size: int = 1024) -> None:
    """Create a magenta-background sprite source for chroma-key processing."""
    center = size // 2
    radius = int(size * 0.28)

    def pixel_at(x: int, y: int) -> RGBA:
        dx = x - center
        dy = y - int(size * 0.48)
        if dx * dx + dy * dy <= radius * radius:
            return (255, 196, 86, 255)
        eye_y = int(size * 0.42)
        if abs(y - eye_y) < 18 and abs(abs(x - center) - 90) < 18:
            return (32, 40, 48, 255)
        return (255, 0, 255, 255)

    write_png_rgba(path, size, size, pixel_at)


def write_chroma_keyed_player(path: Path, size: int = 256) -> None:
    """Write a deterministic mock transparent-background player PNG."""
    center = size // 2
    radius = int(size * 0.34)

    def pixel_at(x: int, y: int) -> RGBA:
        dx = x - center
        dy = y - int(size * 0.48)
        distance = dx * dx + dy * dy
        if distance <= radius * radius:
            if abs(y - int(size * 0.42)) < 5 and abs(abs(x - center) - 26) < 5:
                return (32, 40, 48, 255)
            return (255, 196, 86, 255)
        return (0, 0, 0, 0)

    write_png_rgba(path, size, size, pixel_at)


def write_chroma_keyed_player_from_source(
    source_path: Path,
    output_path: Path,
    *,
    size: int = 256,
) -> None:
    """Remove a flat model background from a raw player image and resize to PNG."""
    image = _open_uploaded_image(source_path)
    if image is None:
        _write_png_reference_chroma_key(source_path, output_path, size)
        return
    background = _corner_background_color(image)
    keyed = _remove_near_background(image, background)
    keyed.thumbnail((size, size))
    canvas = _new_transparent_image(size, size)
    x = (size - keyed.width) // 2
    y = (size - keyed.height) // 2
    canvas.alpha_composite(keyed, (x, y))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, format="PNG")


def write_background_from_uploaded_image(
    source_path: Path,
    output_path: Path,
    *,
    width: int = 1280,
    height: int = 720,
) -> None:
    """Convert a user-provided image into the runtime background PNG."""
    image = _open_uploaded_image(source_path)
    if image is None:
        _write_png_reference_cover(source_path, output_path, width, height)
        return
    image = _resize_cover(image, width, height)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="PNG")


def write_player_from_uploaded_image(
    source_path: Path,
    output_path: Path,
    *,
    size: int = 256,
) -> None:
    """Convert a user-provided image into a centered transparent player PNG."""
    image = _open_uploaded_image(source_path)
    if image is None:
        _write_png_reference_contain(source_path, output_path, size)
        return
    image.thumbnail((size, size))
    canvas = _new_transparent_image(size, size)
    x = (size - image.width) // 2
    y = (size - image.height) // 2
    canvas.alpha_composite(image, (x, y))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, format="PNG")


def write_mock_cover(path: Path, width: int = 1280, height: int = 720) -> None:
    """Create a deterministic cover derived from the background style."""

    def pixel_at(x: int, y: int) -> RGBA:
        if y < int(height * 0.24):
            return (18, 26, 32, 235)
        if int(width * 0.18) < x < int(width * 0.82) and int(height * 0.11) < y < int(
            height * 0.15
        ):
            return (255, 194, 0, 255)
        if y > int(height * 0.68):
            return (48, 128, 74, 255)
        return (94, 184, 188, 255)

    write_png_rgba(path, width, height, pixel_at)


def _open_uploaded_image(source_path: Path):
    try:
        from PIL import Image, UnidentifiedImageError
    except ModuleNotFoundError as exc:
        if source_path.suffix.lower() == ".png":
            return None
        raise ProviderError(
            "Pillow is required to process uploaded JPG/JPEG image assets; "
            "install lan_agents dependencies with `pip install -e .`"
        ) from exc
    try:
        with Image.open(source_path) as image:
            return image.convert("RGBA")
    except FileNotFoundError as exc:
        raise ProviderError(f"Uploaded image asset not found: {source_path}") from exc
    except UnidentifiedImageError as exc:
        raise ProviderError(f"Uploaded asset is not a readable image: {source_path}") from exc
    except OSError as exc:
        raise ProviderError(f"Uploaded image asset could not be read: {source_path}") from exc


def _resize_cover(image, width: int, height: int):
    from PIL import Image

    source_ratio = image.width / max(1, image.height)
    target_ratio = width / max(1, height)
    if source_ratio > target_ratio:
        resize_height = height
        resize_width = max(width, round(height * source_ratio))
    else:
        resize_width = width
        resize_height = max(height, round(width / source_ratio))
    resized = image.resize((resize_width, resize_height), Image.Resampling.LANCZOS)
    left = max(0, (resize_width - width) // 2)
    top = max(0, (resize_height - height) // 2)
    return resized.crop((left, top, left + width, top + height))


def _new_transparent_image(width: int, height: int):
    from PIL import Image

    return Image.new("RGBA", (width, height), (0, 0, 0, 0))


def _corner_background_color(image) -> RGBA:
    corners = [
        image.getpixel((0, 0)),
        image.getpixel((max(0, image.width - 1), 0)),
        image.getpixel((0, max(0, image.height - 1))),
        image.getpixel((max(0, image.width - 1), max(0, image.height - 1))),
    ]
    channels = []
    for index in range(4):
        values = sorted(int(color[index]) for color in corners)
        channels.append(values[len(values) // 2])
    return tuple(channels)  # type: ignore[return-value]


def _remove_near_background(image, background: RGBA):
    from PIL import Image

    result = Image.new("RGBA", image.size, (0, 0, 0, 0))
    output_pixels = result.load()
    input_pixels = image.load()
    threshold = 64
    for y in range(image.height):
        for x in range(image.width):
            pixel = input_pixels[x, y]
            distance = sum(abs(int(pixel[i]) - int(background[i])) for i in range(3))
            if distance <= threshold or int(pixel[3]) < 16:
                output_pixels[x, y] = (0, 0, 0, 0)
            else:
                output_pixels[x, y] = pixel
    return result


def _write_png_reference_cover(
    source_path: Path,
    output_path: Path,
    width: int,
    height: int,
) -> None:
    source_width, source_height, pixels = _read_simple_rgba_png(source_path)
    source_ratio = source_width / max(1, source_height)
    target_ratio = width / max(1, height)
    if source_ratio > target_ratio:
        crop_height = source_height
        crop_width = max(1, round(source_height * target_ratio))
        crop_left = (source_width - crop_width) // 2
        crop_top = 0
    else:
        crop_width = source_width
        crop_height = max(1, round(source_width / target_ratio))
        crop_left = 0
        crop_top = (source_height - crop_height) // 2

    def pixel_at(x: int, y: int) -> RGBA:
        source_x = crop_left + min(crop_width - 1, x * crop_width // max(1, width))
        source_y = crop_top + min(crop_height - 1, y * crop_height // max(1, height))
        return pixels[source_y * source_width + source_x]

    write_png_rgba(output_path, width, height, pixel_at)


def _write_png_reference_contain(
    source_path: Path,
    output_path: Path,
    size: int,
) -> None:
    source_width, source_height, pixels = _read_simple_rgba_png(source_path)
    scale = min(size / max(1, source_width), size / max(1, source_height))
    draw_width = max(1, round(source_width * scale))
    draw_height = max(1, round(source_height * scale))
    left = (size - draw_width) // 2
    top = (size - draw_height) // 2

    def pixel_at(x: int, y: int) -> RGBA:
        if x < left or x >= left + draw_width or y < top or y >= top + draw_height:
            return (0, 0, 0, 0)
        source_x = min(source_width - 1, (x - left) * source_width // draw_width)
        source_y = min(source_height - 1, (y - top) * source_height // draw_height)
        return pixels[source_y * source_width + source_x]

    write_png_rgba(output_path, size, size, pixel_at)


def _write_png_reference_chroma_key(
    source_path: Path,
    output_path: Path,
    size: int,
) -> None:
    source_width, source_height, pixels = _read_simple_rgba_png(source_path)
    background = pixels[0]
    scale = min(size / max(1, source_width), size / max(1, source_height))
    draw_width = max(1, round(source_width * scale))
    draw_height = max(1, round(source_height * scale))
    left = (size - draw_width) // 2
    top = (size - draw_height) // 2

    def pixel_at(x: int, y: int) -> RGBA:
        if x < left or x >= left + draw_width or y < top or y >= top + draw_height:
            return (0, 0, 0, 0)
        source_x = min(source_width - 1, (x - left) * source_width // draw_width)
        source_y = min(source_height - 1, (y - top) * source_height // draw_height)
        pixel = pixels[source_y * source_width + source_x]
        distance = sum(abs(int(pixel[i]) - int(background[i])) for i in range(3))
        if distance <= 64 or int(pixel[3]) < 16:
            return (0, 0, 0, 0)
        return pixel

    write_png_rgba(output_path, size, size, pixel_at)


def _read_simple_rgba_png(path: Path) -> tuple[int, int, list[RGBA]]:
    data = path.read_bytes()
    if not data.startswith(PNG_SIGNATURE):
        raise ProviderError(f"Uploaded asset is not a PNG image: {path}")
    offset = len(PNG_SIGNATURE)
    width = 0
    height = 0
    compressed = bytearray()
    while offset < len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        chunk_data = data[offset + 8 : offset + 8 + length]
        offset += 12 + length
        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, _, _, _ = struct.unpack(
                ">IIBBBBB", chunk_data
            )
            if bit_depth != 8 or color_type != 6:
                raise ProviderError(
                    "PNG fallback only supports 8-bit RGBA images; install Pillow for broader image support"
                )
        elif chunk_type == b"IDAT":
            compressed.extend(chunk_data)
        elif chunk_type == b"IEND":
            break
    if not width or not height:
        raise ProviderError(f"PNG image is missing IHDR metadata: {path}")
    raw = zlib.decompress(bytes(compressed))
    row_size = width * 4
    pixels: list[RGBA] = []
    cursor = 0
    for _y in range(height):
        filter_type = raw[cursor]
        cursor += 1
        if filter_type != 0:
            raise ProviderError(
                "PNG fallback only supports unfiltered rows; install Pillow for broader image support"
            )
        row = raw[cursor : cursor + row_size]
        cursor += row_size
        for x in range(width):
            base = x * 4
            pixels.append(
                (row[base], row[base + 1], row[base + 2], row[base + 3])
            )
    return width, height, pixels
