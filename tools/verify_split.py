#!/usr/bin/env python3
# SPDX-FileCopyrightText: Etienne-T
# SPDX-License-Identifier: MIT-0
"""Verify and concatenate local chunks using a user-supplied JSON manifest.

No device hashes or partition layout are built in. See docs/TOOLS.md.
All chunk data is verified before an exclusively created output directory is
written. Input files and the manifest must be trusted, local regular files.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import zlib


def integer(value, name, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(f'{name} must be an integer >= {minimum}')
    return value


def digest(value, digits, name):
    if not isinstance(value, str) or not re.fullmatch(rf'[0-9a-fA-F]{{{digits}}}', value):
        raise ValueError(f'{name} must contain {digits} hexadecimal digits')
    return value.lower()


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def is_link(path):
    return path.is_symlink() or path.is_junction()


def load_image(manifest, max_bytes):
    if is_link(manifest) or not manifest.is_file():
        raise ValueError('manifest must be a regular file, not a link')
    # The small JSON manifest is independent of the potentially large chunks.
    if manifest.stat().st_size > 1024 * 1024:
        raise ValueError('manifest exceeds 1 MiB')
    spec = json.loads(manifest.read_text(encoding='utf-8'), object_pairs_hook=unique_keys)
    if not isinstance(spec, dict):
        raise ValueError('manifest must be a JSON object')
    total = integer(spec.get('total_size'), 'total_size', 1)
    if total > max_bytes:
        raise ValueError('total_size exceeds --max-bytes')
    chunks = spec.get('chunks')
    if not isinstance(chunks, list) or not chunks:
        raise ValueError('chunks must be a nonempty list')
    base = manifest.parent.resolve()
    seen = set()
    data = bytearray()
    for number, chunk in enumerate(chunks, 1):
        if not isinstance(chunk, dict):
            raise ValueError('chunk must be an object')
        filename = chunk.get('file')
        if not isinstance(filename, str) or not filename or '\\' in filename or ':' in filename:
            raise ValueError('chunk file must be a relative path using forward slashes')
        relative = Path(filename)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('chunk file must stay within the manifest directory')
        path = base / relative
        if any(is_link(p) for p in [path, *path.parents] if p == base or base in p.parents):
            raise ValueError('chunk paths must not contain links or junctions')
        resolved = path.resolve(strict=True)
        if not resolved.is_relative_to(base) or not resolved.is_file() or resolved in seen:
            raise ValueError('chunk must be a unique regular file below the manifest directory')
        seen.add(resolved)
        size = integer(chunk.get('size'), 'chunk size', 1)
        expected_sha = digest(chunk.get('sha256'), 64, 'chunk sha256')
        if len(data) + size > total or path.stat().st_size != size:
            raise ValueError(f'chunk {number}: size mismatch')
        with path.open('rb') as stream:
            content = stream.read(size + 1)
        if len(content) != size or hashlib.sha256(content).hexdigest() != expected_sha:
            raise ValueError(f'chunk {number}: length or SHA-256 mismatch')
        if 'crc32' in chunk:
            expected_crc = digest(chunk['crc32'], 8, 'chunk crc32')
            if f'{zlib.crc32(content):08x}' != expected_crc:
                raise ValueError(f'chunk {number}: CRC32 mismatch')
        data.extend(content)
    if len(data) != total:
        raise ValueError('combined size does not match total_size')
    if 'image_sha256' in spec:
        expected = digest(spec['image_sha256'], 64, 'image_sha256')
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError('combined SHA-256 mismatch')
    parts = spec.get('partitions', [])
    if not isinstance(parts, list):
        raise ValueError('partitions must be a list')
    validated = []
    names = {'nand_full'}
    for part in parts:
        if not isinstance(part, dict):
            raise ValueError('partition must be an object')
        name = part.get('name')
        if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', name):
            raise ValueError('partition name must be 1–64 letters, digits, underscores or hyphens')
        folded = name.lower()
        if folded in names or re.fullmatch(r'(con|prn|aux|nul|com[0-9]|lpt[0-9])', folded):
            raise ValueError('duplicate or reserved partition name')
        names.add(folded)
        offset = integer(part.get('offset'), 'partition offset')
        size = integer(part.get('size'), 'partition size', 1)
        if offset + size > total:
            raise ValueError('partition extends beyond the image')
        if any(offset < end and start < offset + size for _, start, end in validated):
            raise ValueError('partition ranges overlap')
        validated.append((name, offset, offset + size))
    return data, validated


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('output', type=Path, help='new private output directory')
    parser.add_argument('--max-bytes', type=int, default=256 * 1024 * 1024)
    args = parser.parse_args(argv)
    try:
        integer(args.max_bytes, 'max-bytes', 1)
        data, partitions = load_image(args.manifest.absolute(), args.max_bytes)
        args.output.mkdir(exist_ok=False)
        # New output directory plus exclusive file creation: never overwrite.
        with (args.output / 'nand_full.bin').open('xb') as stream:
            stream.write(data)
        for name, start, end in partitions:
            with (args.output / (name + '.bin')).open('xb') as stream:
                stream.write(memoryview(data)[start:end])
    except (OSError, ValueError, KeyError, TypeError, RecursionError) as error:
        # Do not expose manifest values or file contents in routine diagnostics.
        print(f'Verification failed: {type(error).__name__}', file=sys.stderr)
        return 1
    print(f'Verified {len(data)} bytes; wrote full image and {len(partitions)} partitions.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
