#!/usr/bin/env python3
# SPDX-FileCopyrightText: Etienne-T
# SPDX-License-Identifier: MIT-0
"""Extrait un volume UBI d'un dump de partition (sans OOB).

Usage : python -I ubi_extract.py <partition.bin> <nom_volume> <sortie> [--fit]
--fit : tronque la sortie à la taille FIT/DTB (champ totalsize de l'en-tête).
Géométrie du H80X : PEB 128 Kio, en-tête VID à 2048, données à 4096.
"""
import struct
import sys
import zlib

PEB = 0x20000
LAYOUT_VOL = 0x7FFFEFFF

src, want, out = sys.argv[1], sys.argv[2], sys.argv[3]
data = open(src, "rb").read()

lebs = {}   # vol_id -> {lnum: (sqnum, bytes)}
for off in range(0, len(data), PEB):
    peb = data[off:off + PEB]
    if peb[:4] != b"UBI#":
        continue
    vid_off, data_off = struct.unpack(">II", peb[16:24])
    vid = peb[vid_off:vid_off + 64]
    if vid[:4] != b"UBI!":
        continue  # PEB vide (seulement l'en-tête EC)
    vol_type = vid[5]
    vol_id, lnum = struct.unpack(">II", vid[8:16])
    data_size, used_ebs, data_pad, data_crc = struct.unpack(">IIII", vid[20:36])
    sqnum = struct.unpack(">Q", vid[40:48])[0]
    leb_size = PEB - data_off - data_pad
    payload = peb[data_off:data_off + (data_size if vol_type == 2 else leb_size)]
    # UBI : crc32_le(init 0xFFFFFFFF) sans inversion finale = zlib.crc32 ^ 0xFFFFFFFF
    if vol_type == 2 and (zlib.crc32(payload) ^ 0xFFFFFFFF) != data_crc:
        print(f"[!] CRC faux, PEB 0x{off:x}")
    cur = lebs.setdefault(vol_id, {}).get(lnum)
    if cur is None or sqnum > cur[0]:
        lebs[vol_id][lnum] = (sqnum, payload)

# Table des volumes (volume de layout, LEB 0)
names = {}
table = lebs[LAYOUT_VOL][0][1]
for i in range(128):
    rec = table[i * 172:(i + 1) * 172]
    if len(rec) < 172:
        break
    reserved, _align, _pad, vtype, _upd, name_len = struct.unpack(">IIIBBH", rec[:16])
    if reserved:
        names[rec[16:16 + name_len].decode()] = (i, vtype)
print("Volumes :", {n: f"id {v[0]}, {'statique' if v[1] == 2 else 'dynamique'}" for n, v in names.items()})

vol_id = names[want][0]
blob = b"".join(lebs[vol_id][n][1] for n in sorted(lebs[vol_id]))
if "--fit" in sys.argv:
    assert blob[:4] == b"\xd0\x0d\xfe\xed", "pas un FIT/DTB"
    blob = blob[:struct.unpack(">I", blob[4:8])[0]]
open(out, "wb").write(blob)
print(f"[+] {want} -> {out} : {len(blob)} octets, crc32 {zlib.crc32(blob) & 0xFFFFFFFF:08x}")
