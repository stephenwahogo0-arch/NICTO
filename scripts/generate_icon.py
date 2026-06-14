"""
Generate a 512x512 PNG icon for the NIKTO Electron desktop app.

Usage:
    python scripts/generate_icon.py

The icon is saved to packages/nikto-desktop/icon.png.
"""

import struct
import zlib
from pathlib import Path


def _create_png(width: int, height: int, pixels: bytes) -> bytes:
    """Create a PNG image from raw RGBA pixel data."""
    def _chunk(chunk_type: bytes, data: bytes) -> bytes:
        chunk = chunk_type + data
        return struct.pack(">I", len(data)) + chunk + struct.pack(">I", zlib.crc32(chunk) & 0xFFFFFFFF)

    signature = b"\x89PNG\r\n\x1a\n"

    # IHDR chunk
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)  # 8-bit RGBA
    ihdr = _chunk(b"IHDR", ihdr_data)

    # IDAT chunk (raw pixel data)
    raw_data = b""
    for y in range(height):
        raw_data += b"\x00"  # filter byte (none)
        row_start = y * width * 4
        raw_data += pixels[row_start:row_start + width * 4]

    compressed = zlib.compress(raw_data)
    idat = _chunk(b"IDAT", compressed)

    # IEND chunk
    iend = _chunk(b"IEND", b"")

    return signature + ihdr + idat + iend


def generate_icon(size: int = 512) -> bytes:
    """Generate a NIKTO-themed 512x512 icon as PNG bytes.

    Design: Dark background (#1a1a2e) with a glowing cyan neural
    network pattern and 'N' letter in the center.
    """
    pixels = bytearray(size * size * 4)

    center = size // 2
    radius = size * 0.42

    for y in range(size):
        for x in range(size):
            idx = (y * size + x) * 4
            dx = x - center
            dy = y - center
            dist = (dx * dx + dy * dy) ** 0.5

            # Dark background
            pixels[idx] = 0x1a      # R
            pixels[idx + 1] = 0x1a  # G
            pixels[idx + 2] = 0x2e  # B
            pixels[idx + 3] = 255   # A

            # Outer glow ring
            if radius - 10 < dist < radius:
                intensity = max(0, 1.0 - abs(dist - radius + 5) / 10)
                pixels[idx] = int(0x00 * (1 - intensity) + 0x00 * intensity)
                pixels[idx + 1] = int(0x1a * (1 - intensity) + 0xff * intensity)
                pixels[idx + 2] = int(0x2e * (1 - intensity) + 0xaa * intensity)

            # Inner circle
            if dist < radius - 12:
                # Neural blue
                pixels[idx] = 0x16
                pixels[idx + 1] = 0x2b
                pixels[idx + 2] = 0x4e
                pixels[idx + 3] = 255

            # Glowing 'N' letter approximation (simple shape)
            if dist < radius * 0.5:
                # Vertical bars of 'N'
                n_left = center - int(radius * 0.22)
                n_right = center + int(radius * 0.22)
                n_mid_x = center
                n_mid_y = center

                slope = (n_right - n_left) / (size * 0.5)  # diagonal slope

                # Left vertical bar
                left_bar = abs(x - n_left) < 6
                # Right vertical bar
                right_bar = abs(x - n_right) < 6
                # Diagonal bar
                diag_y = center + int((x - n_left) / slope) if abs(slope) > 0.01 else center
                diag_bar = abs(y - diag_y) < 6 and n_left <= x <= n_right

                if left_bar or right_bar or diag_bar:
                    pixels[idx] = 0x00
                    pixels[idx + 1] = 0xff
                    pixels[idx + 2] = 0xcc
                    pixels[idx + 3] = 255

            # Subtle connection lines (neural network pattern)
            if dist < radius * 0.7:
                for px, py, pdx, pdy in [
                    (center - int(radius * 0.3), center - int(radius * 0.3), center, center),
                    (center + int(radius * 0.3), center - int(radius * 0.3), center, center),
                    (center - int(radius * 0.3), center + int(radius * 0.3), center, center),
                    (center + int(radius * 0.3), center + int(radius * 0.3), center, center),
                ]:
                    # Simple line approximation
                    line_dist = abs((pdy - py) * x - (pdx - px) * y + pdx * py - pdy * px) / max(((pdy - py)**2 + (pdx - px)**2)**0.5, 1)
                    if line_dist < 2.0 and min(px, pdx) <= x <= max(px, pdx) and min(py, pdy) <= y <= max(py, pdy):
                        pixels[idx] = min(pixels[idx] + 40, 255)
                        pixels[idx + 1] = min(pixels[idx + 1] + 80, 255)
                        pixels[idx + 2] = min(pixels[idx + 2] + 40, 255)

    return bytes(pixels)


def main() -> None:
    size = 512
    output_path = Path(__file__).resolve().parent.parent / "packages" / "nikto-desktop" / "icon.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    pixels = generate_icon(size)
    png_data = _create_png(size, size, pixels)

    with open(output_path, "wb") as f:
        f.write(png_data)

    print(f"Icon generated: {output_path} ({len(png_data):,} bytes, {size}x{size})")


if __name__ == "__main__":
    main()
