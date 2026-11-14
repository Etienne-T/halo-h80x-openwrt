#!/usr/bin/env python3
# SPDX-FileCopyrightText: Etienne-T
# SPDX-License-Identifier: MIT-0
"""Interrompt l'autoboot U-Boot du Halo (chaîne magique), puis ouvre miniterm.

Usage (on the serial host) :  python3 stop_uboot.py [chaine_magique]   (défaut : tpl)
Lancer le script, PUIS couper/remettre l'alimentation du Halo.
"""
import os
import sys
import time

import serial

PORT = "/dev/ttyUSB0"
BAUD = 115200
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
BATCH = "--batch" in sys.argv  # pas de miniterm à la fin, timeout d'attente
MAGIC = (ARGS[0] if ARGS else "tpl").encode()
WAIT_TIMEOUT = 300 if BATCH else None
FAIL_MARKERS = (b"Unmounting UBIFS", b"Loading kernel", b"Starting kernel")
PROMPT = b"IPQ5018# "  # prompt U-Boot attendu ; sans lui, aucun succes n'est annonce


def show(data):
    sys.stdout.write(data.decode(errors="replace"))
    sys.stdout.flush()


s = serial.Serial(PORT, BAUD, timeout=0.01)
print(f"[*] {PORT} ouvert a {BAUD}. Chaine testee : {MAGIC!r}")
print("[*] Coupe puis remets l'alimentation du Halo maintenant (Ctrl+C pour annuler)...\n", flush=True)

buf = b""
result = None
try:
    # 1) Attendre le démarrage d'U-Boot
    t0 = time.time()
    while b"U-Boot 20" not in buf:
        if WAIT_TIMEOUT and time.time() - t0 > WAIT_TIMEOUT:
            raise TimeoutError
        data = s.read(512)
        if data:
            show(data)
            buf = (buf + data)[-8192:]

    # 2) Envoyer la chaîne en boucle jusqu'au succès ou à l'échec
    print(f"\n[*] U-Boot detecte -> envoi de {MAGIC!r} en boucle", flush=True)
    start = time.time()
    while time.time() - start < 6:
        s.write(MAGIC)
        data = s.read(512)
        if data:
            show(data)
            buf = (buf + data)[-8192:]
        tail = buf.split(b"magic string", 1)[-1]
        if any(m in tail for m in FAIL_MARKERS):
            result = "echec"
            break
        time.sleep(0.02)
    else:
        # Le silence ne prouve rien : exiger le prompt U-Boot avant d'annoncer l'arret.
        s.reset_input_buffer()
        s.write(b"\r\r")  # nettoie la ligne (les "tpltpl..." donnent juste "Unknown command")
        reply = b""
        end = time.time() + 2
        while time.time() < end and PROMPT not in reply:
            data = s.read(4096)
            if data:
                show(data)
                reply += data
        result = "ok" if PROMPT in reply else "indetermine"

    if result == "ok":
        if BATCH:  # preuve qu'on est dans U-Boot : version + environnement
            for cmd in (b"version\r", b"printenv\r"):
                s.write(cmd)
                end = time.time() + 2
                while time.time() < end:
                    show(s.read(4096))
except KeyboardInterrupt:
    result = "annule"
except TimeoutError:
    result = "timeout"
finally:
    s.close()

if result == "timeout":
    print(f"\n[!] Pas de banniere U-Boot vue en {WAIT_TIMEOUT} s (pas de reboot ?).")
if result == "indetermine":
    print(f"\n[!] Aucun prompt {PROMPT!r} recu : arret d'U-Boot non confirme.")
if result == "echec":
    print(f"\n\n[!] Chaine {MAGIC!r} refusee : le noyau demarre. Essaie une autre chaine.")
if BATCH:
    print(f"\n[RESULTAT] {result}")
    sys.exit(0 if result == "ok" else 1)
elif result == "ok":
    print("\n\n[+] Autoboot apparemment interrompu. Ouverture de miniterm (quitter : Ctrl+X)...")
else:
    print("\n[*] Annule. Ouverture de miniterm (quitter : Ctrl+X)...")

os.execvp(sys.executable, [sys.executable, "-m", "serial.tools.miniterm",
                           "--eol", "CR", "--exit-char", "24", PORT, str(BAUD)])
