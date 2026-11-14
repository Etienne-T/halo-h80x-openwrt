#!/usr/bin/env python3
# SPDX-FileCopyrightText: Etienne-T
# SPDX-License-Identifier: MIT-0
"""Décompile un DTB en texte façon DTS (lecture seule, sans dtc).

Usage : python -I dtb2dts.py <fichier.dtb> [sortie.dts]
Les phandles restent numériques (pas de labels) ; les chaînes sont détectées
automatiquement, le reste est affiché en cellules 32 bits ou en octets.
"""
import struct
import sys

d = open(sys.argv[1], "rb").read()
magic, total, off_struct, off_str, off_rsv, ver, _, _, sz_str, sz_struct = struct.unpack(">10I", d[:40])
assert magic == 0xD00DFEED


def sname(o):
    return d[off_str + o:d.index(b"\0", off_str + o)].decode()


def fmt(name, v):
    if not v:
        return f"{name};"
    if v[-1] == 0 and all(32 <= c < 127 or c == 0 for c in v) and b"\0\0" not in v and v[0] != 0:
        strs = v[:-1].split(b"\0")
        return f"{name} = " + ", ".join('"' + s.decode() + '"' for s in strs) + ";"
    if len(v) % 4 == 0:
        cells = struct.unpack(f">{len(v) // 4}I", v)
        return f"{name} = <" + " ".join(f"0x{c:x}" for c in cells) + ">;"
    return f"{name} = [" + " ".join(f"{c:02x}" for c in v) + "];"


out, depth, p = [], 0, off_struct
while True:
    tok = struct.unpack(">I", d[p:p + 4])[0]
    p += 4
    if tok == 1:  # BEGIN_NODE
        e = d.index(b"\0", p)
        nm = d[p:e].decode() or "/"
        p = (e + 4) & ~3
        out.append("\t" * depth + nm + " {")
        depth += 1
    elif tok == 2:  # END_NODE
        depth -= 1
        out.append("\t" * depth + "};")
    elif tok == 3:  # PROP
        ln, no = struct.unpack(">II", d[p:p + 8])
        v = d[p + 8:p + 8 + ln]
        p = (p + 8 + ln + 3) & ~3
        out.append("\t" * depth + fmt(sname(no), v))
    elif tok == 4:
        continue
    elif tok == 9:
        break
    else:
        raise ValueError(f"jeton inconnu {tok} @ {p}")

text = "\n".join(out) + "\n"
if len(sys.argv) > 2:
    open(sys.argv[2], "w", encoding="utf-8").write(text)
    print(f"{len(out)} lignes -> {sys.argv[2]}")
else:
    sys.stdout.write(text)
