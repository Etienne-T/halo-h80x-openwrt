#!/usr/bin/env python3
# SPDX-FileCopyrightText: Etienne-T
# SPDX-License-Identifier: MIT-0
"""Envoie des commandes au prompt U-Boot du Halo et affiche les réponses.

Usage : python3 uboot_cmd.py "help" "nand info" ...
Le Deco doit déjà être arrêté au prompt IPQ5018#.
"""
import sys
import time

import serial

PROMPT = b"IPQ5018# "
s = serial.Serial("/dev/ttyUSB0", 115200, timeout=0.05)


def run(cmd, timeout=int(__import__("os").environ.get("UBOOT_TIMEOUT", "30"))):
    s.reset_input_buffer()
    s.write(cmd.encode() + b"\r")
    buf = b""
    end = time.time() + timeout
    while time.time() < end:
        buf += s.read(4096)
        if buf.rstrip().endswith(PROMPT.rstrip()) and len(buf) > len(cmd) + 4:
            break
    return buf


s.write(b"\x03\r")  # Ctrl+C : interrompt une commande en cours (ex. tftpput)
time.sleep(0.5)
first = s.read(4096)
if PROMPT.rstrip() not in first:
    print("[!] Pas de prompt U-Boot :", repr(first[-300:]))
    sys.exit(1)
for c in sys.argv[1:]:
    print(f"===== {c}")
    print(run(c).decode(errors="replace").replace("\r", ""))
s.close()
