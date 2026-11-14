#!/usr/bin/env python3
# SPDX-FileCopyrightText: Etienne-T
# SPDX-License-Identifier: MIT-0
"""Envoie quelques Entrée sur l'UART et affiche ce que le Halo répond (test du fil TX)."""
import sys
import time

import serial

s = serial.Serial("/dev/ttyUSB0", 115200, timeout=0.05)
s.reset_input_buffer()
got = b""
for _ in range(3):
    s.write(b"\r")
    end = time.time() + 1.5
    while time.time() < end:
        got += s.read(1024)
s.close()
print(repr(got[-2000:]))
print("[RESULTAT] reponse recue" if got.strip() else "[RESULTAT] aucune reponse")
