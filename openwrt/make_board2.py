#!/usr/bin/env python3
# SPDX-FileCopyrightText: Etienne-T
# SPDX-License-Identifier: MIT-0
"""Fabrique les fichiers de carte ath11k (board-2.bin + board.bin) du Halo H80X.

Format board-2.bin (ath11k, API 2) :
  "QCA-ATH11K-BOARD\\0" aligné sur 4 octets, puis des IE {u32 id, u32 len, data alignée 4}.
  IE BOARD (0) = { IE NAME (0) : chaîne sans \\0 , IE DATA (1) : BDF }.
Historical compatibility generator: each radio receives eight aliases and an
API 1 fallback. The exact observed API 2 match is now known:
bus=ahb,qmi-chip-id=0,qmi-board-id=255,variant=Mercusys-Halo-H80X-v1.
This script only wraps user-provided files. It is not a firmware extractor or
an input validator. It does not grant rights over its inputs or outputs.
Use only a new private output directory; never commit the generated files.

Usage : python -I make_board2.py <bdwlan_ipq5018> <bdwlan_qcn6122> <dossier_sortie>
"""
import os
import struct
import sys

VARIANT = "Mercusys-Halo-H80X-v1"
MAGIC = b"QCA-ATH11K-BOARD\0"


def pad4(b):
    return b + b"\0" * (-len(b) % 4)


def ie(ie_id, data):
    return struct.pack("<II", ie_id, len(data)) + pad4(data)


def board2(bdf, names):
    out = pad4(MAGIC)
    for n in names:
        out += ie(0, ie(0, n.encode()) + ie(1, bdf))
    return out


def names_for(board_ids):
    res = []
    for chip in (0, 255):
        for bid in board_ids:
            base = f"bus=ahb,qmi-chip-id={chip},qmi-board-id={bid}"
            res += [f"{base},variant={VARIANT}", base]
    return res


ipq, qcn, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
for chip, src, ids in (("IPQ5018", ipq, (0x24, 255)), ("QCN6122", qcn, (0x60, 255))):
    bdf = open(src, "rb").read()
    d = os.path.join(outdir, chip, "hw1.0")
    os.makedirs(d, exist_ok=True)
    names = names_for(ids)
    open(os.path.join(d, "board-2.bin"), "wb").write(board2(bdf, names))
    open(os.path.join(d, "board.bin"), "wb").write(bdf)
    print(f"{chip}: BDF {os.path.basename(src)} ({len(bdf)} o) -> {len(names)} noms dans board-2.bin")
    for n in names:
        print("   ", n)
