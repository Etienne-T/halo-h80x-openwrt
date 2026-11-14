#!/usr/bin/env python3
# SPDX-FileCopyrightText: Etienne-T
# SPDX-License-Identifier: MIT-0
"""Exécute des commandes dans la console série d'OpenWrt (ttyMSM0) et affiche la sortie.

Usage (on the serial host) : python3 owrt_cmd.py "uname -a" "ip addr show br-lan" ...
Chaque commande est encadrée de marqueurs pour récupérer exactement sa sortie.
OWRT_TIMEOUT=<s> pour les commandes longues (défaut 20 s).
"""
import os
import sys
import time

import serial

TIMEOUT = int(os.environ.get("OWRT_TIMEOUT", "20"))
s = serial.Serial("/dev/ttyUSB0", 115200, timeout=0.05)

# Active la console (« Please press Enter ») et vide le tampon
s.write(b"\r")
time.sleep(1.0)
s.write(b"\r")
time.sleep(0.5)
s.read(65536)

for i, cmd in enumerate(sys.argv[1:]):
    tag = f"__FIN{i}_{int(time.time())}__"
    s.write(f"{cmd}; echo {tag}\r".encode())
    buf, end = b"", time.time() + TIMEOUT
    while time.time() < end:
        buf += s.read(4096)
        if buf.count(tag.encode()) >= 2:  # écho de la commande + vraie sortie
            break
    text = buf.decode(errors="replace").replace("\r", "")
    body = text.split(tag, 1)[-1] if text.count(tag) >= 2 else text
    body = body.rsplit(tag, 1)[0]
    print(f"===== {cmd}")
    print(body.strip("\n"))
s.close()
