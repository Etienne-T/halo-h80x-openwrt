#!/usr/bin/env python3
# SPDX-FileCopyrightText: Etienne-T
# SPDX-License-Identifier: MIT-0
"""Controle hors appareil : FIT/initramfs et tar/SquashFS, sans executer leur code.

Usage Linux : python3 verify_wpa2_images.py ARBRE_OPENWRT DOSSIER_SOURCES DOSSIER_SORTIE
Requiert unsquashfs. Les cles sont generees au boot, jamais extraites ici.
"""
import hashlib
import json
import lzma
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tarfile
import zlib


def fit_kernel(blob):
    header = struct.unpack_from('>10I', blob)
    assert header[0] == 0xd00dfeed
    pos, strings = header[2], header[3]
    nodes = []
    while True:
        token, = struct.unpack_from('>I', blob, pos)
        pos += 4
        if token == 1:
            end = blob.index(b'\0', pos)
            nodes.append(blob[pos:end].decode())
            pos = (end + 4) & ~3
        elif token == 2:
            nodes.pop()
        elif token == 3:
            size, offset = struct.unpack_from('>II', blob, pos)
            pos += 8
            end = blob.index(b'\0', strings + offset)
            name = blob[strings + offset:end]
            value = blob[pos:pos + size]
            pos = (pos + size + 3) & ~3
            if nodes[-2:] == ['images', 'kernel-1'] and name == b'data':
                return lzma.decompress(value)
        elif token == 4:
            continue
        else:
            raise ValueError('Donnees kernel-1 absentes du FIT')


def initramfs_files(kernel, wanted):
    # Le noyau initramfs peut contenir une archive newc compressee en Zstandard.
    start = 0
    while True:
        start = kernel.find(b'070701', start)
        if start < 0:
            raise ValueError('Archive initramfs newc introuvable')
        pos, found = start, {}
        try:
            while kernel[pos:pos + 6] in (b'070701', b'070702'):
                fields = [int(kernel[pos + 6 + i * 8:pos + 14 + i * 8], 16)
                          for i in range(13)]
                size, namesize = fields[6], fields[11]
                name = kernel[pos + 110:pos + 109 + namesize].decode()
                pos = (pos + 110 + namesize + 3) & ~3
                if name == 'TRAILER!!!':
                    if wanted <= found.keys():
                        return found
                    break
                if name.removeprefix('./') in wanted:
                    found[name.removeprefix('./')] = kernel[pos:pos + size]
                pos = (pos + size + 3) & ~3
        except (ValueError, UnicodeDecodeError):
            pass
        start += 6


def kernel_files(kernel, wanted, root):
    zstd = shutil.which('zstd') or str(root / 'staging_dir/host/bin/zstd')
    offset = 0
    while True:
        offset = kernel.find(b'\x28\xb5\x2f\xfd', offset)
        if offset < 0:
            return initramfs_files(kernel, wanted)
        # zstd peut signaler les donnees de fin du noyau apres la frame valide.
        unpacked = subprocess.run([zstd, '-dc'], input=kernel[offset:],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            return initramfs_files(unpacked.stdout, wanted)
        except ValueError:
            offset += 4


def main():
    root, sources, output = (Path(p).expanduser().resolve() for p in sys.argv[1:])
    output.mkdir(parents=True, exist_ok=True)
    binaries = root / 'bin/targets/qualcommax/ipq50xx'
    prefix = 'openwrt-qualcommax-ipq50xx-mercusys_h80x-v1-'
    fit = binaries / (prefix + 'initramfs-uImage.itb')
    upgrade = binaries / (prefix + 'squashfs-sysupgrade.bin')
    expected = {
        'etc/uci-defaults/' + p.name: p.read_bytes()
        for p in (sources / 'install/uci-defaults').iterdir() if p.is_file()
    }
    expected['lib/upgrade/nand.sh'] = (root / 'package/base-files/files/lib/upgrade/nand.sh').read_bytes()
    expected['lib/upgrade/platform.sh'] = (root / 'target/linux/qualcommax/ipq50xx/base-files/lib/upgrade/platform.sh').read_bytes()
    ram = kernel_files(fit_kernel(fit.read_bytes()), set(expected), root)
    with tarfile.open(upgrade) as archive:
        members = [m for m in archive.getmembers() if m.name.endswith('/root')]
        assert len(members) == 1
        squash = output / 'sysupgrade-root.squashfs'
        squash.write_bytes(archive.extractfile(members[0]).read())
    flash = {name: subprocess.check_output(['unsquashfs', '-cat', str(squash), name])
             for name in expected}
    for image in (ram, flash):
        for name, data in expected.items():
            assert image[name] == data, f'Contenu inattendu : {name}'
        assert b'set -o pipefail' in image['lib/upgrade/nand.sh']
        case = image['lib/upgrade/platform.sh'].split(b'mercusys,h80x-v1)', 1)[1].split(b'\n\t\t;;', 1)[0]
        assert b'if nand_do_flash_file "$1"; then' in case
        assert b'else\n' in case and b'nand_do_upgrade_failed' in case
    result = {
        'images': {p.name: {'size': p.stat().st_size,
                          'crc32': f'{zlib.crc32(p.read_bytes()):08x}',
                          'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                   for p in (fit, upgrade)},
        'files_identical_in_both_images': {
            name: hashlib.sha256(data).hexdigest() for name, data in expected.items()},
        'upgrade_guards_present': True,
    }
    (output / 'image-verification.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
