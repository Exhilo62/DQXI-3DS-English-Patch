#!/usr/bin/env python3
"""Expand Nintendo backward-LZ77 files used by DQXI 3DS PACA archives."""

from __future__ import annotations

import argparse
import struct
from pathlib import Path


def decompress(blob: bytes) -> bytes:
    if len(blob) < 8:
        raise ValueError("input is too small")
    top_bottom, extra_size = struct.unpack_from("<II", blob, len(blob) - 8)
    footer_size = top_bottom >> 24
    compressed_size = top_bottom & 0xFFFFFF
    if footer_size < 8 or footer_size > len(blob):
        raise ValueError(f"invalid footer size: {footer_size}")
    if compressed_size < footer_size or compressed_size > len(blob):
        raise ValueError(f"invalid compressed size: {compressed_size}")

    source_index = len(blob) - footer_size - 1
    reverse_position = 0
    compressed_end = compressed_size - footer_size
    output = bytearray(len(blob) + extra_size)
    output_index = len(output) - 1
    history = bytearray()

    def read_reverse() -> int:
        nonlocal source_index, reverse_position
        if source_index < 0:
            raise ValueError("compressed stream ran past the start of the file")
        value = blob[source_index]
        source_index -= 1
        reverse_position += 1
        return value

    def emit(value: int) -> None:
        nonlocal output_index
        if output_index < 0:
            raise ValueError("decompressed stream exceeds declared output size")
        output[output_index] = value
        output_index -= 1
        history.append(value)

    code = read_reverse()
    bits_left = 8
    while reverse_position < compressed_end:
        if bits_left == 0:
            code = read_reverse()
            bits_left = 8
        bits_left -= 1
        if ((code >> bits_left) & 1) == 0:
            emit(read_reverse())
            continue
        byte1 = read_reverse()
        byte2 = read_reverse()
        length = (byte1 >> 4) + 3
        displacement = (((byte1 & 0x0F) << 8) | byte2) + 3
        if displacement > len(history):
            raise ValueError(
                f"invalid displacement {displacement} with {len(history)} bytes decoded"
            )
        for _ in range(length):
            emit(history[-displacement])

    while source_index >= 0:
        emit(read_reverse())
    if output_index != -1:
        raise ValueError(f"output is short by {output_index + 1} bytes")
    return bytes(output)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--pack-magic",
        action="store_true",
        help="change leading PACA magic to PACK after decompression",
    )
    args = parser.parse_args()
    result = bytearray(decompress(args.source.read_bytes()))
    if args.pack_magic and result[:4] == b"PACA":
        result[:4] = b"PACK"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(result)
    print(f"expanded {args.source} to {len(result)} bytes")


if __name__ == "__main__":
    main()
