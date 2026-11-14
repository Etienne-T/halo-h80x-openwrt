#!/usr/bin/env python3
# SPDX-FileCopyrightText: Etienne-T
# SPDX-License-Identifier: MIT-0
"""Mini serveur TFTP en réception seule (WRQ), pour `tftpput` d'U-Boot.

Usage : python3 tftp_recv.py <dossier_sortie> [port=6969]
- mode octet uniquement, refuse d'écraser un fichier existant ;
- gère les options RFC 2347 (blksize, timeout, tsize) avec un OACK : le tftpput
  d'U-Boot l'exige quand il envoie des options ;
- répond depuis le port d'écoute (U-Boot ignore les réponses d'un autre port) ;
- gère le rebouclage du numéro de bloc 16 bits.
TFTP_DEBUG=1 affiche chaque paquet. Ctrl+C pour arrêter.
"""
import os
import socket
import struct
import sys
import time

OUT = sys.argv[1]
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 6969
DEBUG = bool(os.environ.get("TFTP_DEBUG"))
os.makedirs(OUT, exist_ok=True)


def log(msg):
    print(msg, flush=True)


def err(sock, addr, code, msg):
    sock.sendto(struct.pack("!HH", 5, code) + msg.encode() + b"\0", addr)


def parse_wrq(pkt):
    parts = pkt[2:].split(b"\0")
    name = parts[0].decode(errors="replace")
    mode = parts[1].decode(errors="replace").lower()
    opts = {}
    for i in range(2, len(parts) - 1, 2):
        if parts[i]:
            opts[parts[i].decode(errors="replace").lower()] = parts[i + 1].decode(errors="replace")
    return name, mode, opts


def negotiate(opts):
    """Retourne (taille_bloc, paquet de réponse : OACK si options, sinon ACK 0)."""
    accepted = {}
    blksize = 512
    if "blksize" in opts:
        blksize = max(8, min(int(opts["blksize"]), 1468))
        accepted["blksize"] = str(blksize)
    if "timeout" in opts:
        accepted["timeout"] = opts["timeout"]
    if "tsize" in opts:
        accepted["tsize"] = opts["tsize"]
    if accepted:
        body = b"".join(k.encode() + b"\0" + v.encode() + b"\0" for k, v in accepted.items())
        return blksize, struct.pack("!H", 6) + body
    return blksize, struct.pack("!HH", 4, 0)


def receive(name, opts, addr, sock):
    path = os.path.join(OUT, os.path.basename(name))
    if os.path.exists(path):
        err(sock, addr, 6, "file exists")
        log(f"[!] {path} existe deja, refuse")
        return
    tmp = path + ".part"
    if os.path.exists(tmp):
        # Conserver un transfert interrompu : ne jamais ecraser un .part existant.
        err(sock, addr, 6, "partial file exists")
        log(f"[!] {tmp} existe deja, refuse (deplacer ou supprimer a la main)")
        return
    blksize, reply = negotiate(opts)
    log(f"[*] reception de {name} (options {opts}, blksize {blksize})")
    sock.settimeout(10)
    expected, total, t0 = 1, 0, time.time()
    with open(tmp, "xb") as f:
        sock.sendto(reply, addr)
        while True:
            try:
                pkt, a = sock.recvfrom(65536)
            except socket.timeout:
                log(f"[!] timeout pendant {name} ({total} octets)")
                return
            if DEBUG:
                log(f"    [dbg] {len(pkt)} o de {a} : {pkt[:8].hex()}")
            if len(pkt) < 4 or a[0] != addr[0]:
                continue
            op, blk = struct.unpack("!HH", pkt[:4])
            if op == 2 and expected == 1:
                # WRQ répétée ou nouvelle tentative (autre port) : on suit la dernière
                addr = a
                sock.sendto(reply, addr)
                continue
            if a != addr or op != 3:
                continue
            if blk == expected & 0xFFFF:
                data = pkt[4:]
                f.write(data)
                total += len(data)
                expected += 1
                sock.sendto(struct.pack("!HH", 4, blk), addr)
                if len(data) < blksize:
                    break
            else:  # doublon : ré-acquitter
                sock.sendto(struct.pack("!HH", 4, blk), addr)
    os.replace(tmp, path)
    dt = time.time() - t0
    log(f"[+] {name}: {total} octets en {dt:.1f} s ({total / max(dt, 1e-3) / 1024:.0f} Ko/s)")


srv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
srv.bind(("0.0.0.0", PORT))
log(f"[*] En ecoute UDP {PORT}, sortie {os.path.abspath(OUT)}")
while True:
    srv.settimeout(None)
    pkt, addr = srv.recvfrom(65536)
    if len(pkt) < 4:
        continue
    op = struct.unpack("!H", pkt[:2])[0]
    if op != 2:
        if DEBUG:
            log(f"    [dbg] ignore op={op} de {addr}")
        continue
    name, mode, opts = parse_wrq(pkt)
    if mode != "octet":
        err(srv, addr, 0, "octet only")
        continue
    receive(name, opts, addr, srv)
