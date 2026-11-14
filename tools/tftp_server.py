#!/usr/bin/env python3
# SPDX-FileCopyrightText: Etienne-T
# SPDX-License-Identifier: MIT-0
"""Mini serveur TFTP pour U-Boot : envoi (RRQ, tftpboot) et réception (WRQ, tftpput).

Usage : python3 tftp_server.py --serve <dossier> [--recv <dossier>] [--port 69]
- n'envoie que des fichiers du dossier --serve (pas de chemins) ;
- reçoit seulement si --recv est donné, sans jamais écraser ;
- options RFC 2347 (blksize, timeout, tsize) avec OACK ;
- répond depuis le port d'écoute (le TFTP d'U-Boot l'exige) ;
- numéro de bloc 16 bits rebouclé.
TFTP_DEBUG=1 pour tracer. Ctrl+C pour arrêter.
"""
import argparse
import os
import socket
import struct
import time

ap = argparse.ArgumentParser()
ap.add_argument("--serve")
ap.add_argument("--recv")
ap.add_argument("--port", type=int, default=69)
args = ap.parse_args()
DEBUG = bool(os.environ.get("TFTP_DEBUG"))


def log(msg):
    print(msg, flush=True)


def err(sock, addr, code, msg):
    sock.sendto(struct.pack("!HH", 5, code) + msg.encode() + b"\0", addr)


def parse_req(pkt):
    parts = pkt[2:].split(b"\0")
    name = parts[0].decode(errors="replace")
    mode = parts[1].decode(errors="replace").lower()
    opts = {}
    for i in range(2, len(parts) - 1, 2):
        if parts[i]:
            opts[parts[i].decode(errors="replace").lower()] = parts[i + 1].decode(errors="replace")
    return name, mode, opts


def negotiate(opts, tsize=None):
    """(taille_bloc, octets d'OACK ou None)."""
    acc, blksize = {}, 512
    if "blksize" in opts:
        blksize = max(8, min(int(opts["blksize"]), 1468))
        acc["blksize"] = str(blksize)
    if "timeout" in opts:
        acc["timeout"] = opts["timeout"]
    if "tsize" in opts:
        acc["tsize"] = str(tsize) if tsize is not None else opts["tsize"]
    if not acc:
        return blksize, None
    return blksize, struct.pack("!H", 6) + b"".join(
        k.encode() + b"\0" + v.encode() + b"\0" for k, v in acc.items())


def wait_ack(sock, addr, want, resend, tries=15):
    """Attend l'ACK `want` ; renvoie `resend` à chaque délai. Retourne le nouvel addr ou None."""
    for _ in range(tries):
        sock.sendto(resend, addr)
        end = time.time() + 1.0
        while time.time() < end:
            sock.settimeout(max(0.01, end - time.time()))
            try:
                pkt, a = sock.recvfrom(65536)
            except socket.timeout:
                break
            if a[0] != addr[0] or len(pkt) < 4:
                continue
            op, blk = struct.unpack("!HH", pkt[:4])
            if op == 4 and a == addr and blk == want:
                return addr
            if op == 5:
                log(f"[!] erreur client : {pkt[4:-1].decode(errors='replace')}")
                return None
    log(f"[!] pas d'ACK {want}, abandon")
    return None


def send_file(name, opts, addr, sock):
    path = os.path.join(args.serve or "", os.path.basename(name))
    if not args.serve or not os.path.isfile(path):
        err(sock, addr, 1, "file not found")
        log(f"[!] {name} introuvable")
        return
    data = open(path, "rb").read()
    blksize, oack = negotiate(opts, len(data))
    log(f"[*] envoi de {name} ({len(data)} octets, options {opts}, blksize {blksize})")
    t0 = time.time()
    if oack and wait_ack(sock, addr, 0, oack) is None:
        return
    nblocks = len(data) // blksize + 1  # dernier bloc < blksize (éventuellement vide)
    for n in range(1, nblocks + 1):
        chunk = data[(n - 1) * blksize:n * blksize]
        if wait_ack(sock, addr, n & 0xFFFF, struct.pack("!HH", 3, n & 0xFFFF) + chunk) is None:
            return
    dt = time.time() - t0
    log(f"[+] {name} envoye en {dt:.1f} s ({len(data) / max(dt, 1e-3) / 1024:.0f} Ko/s)")


def recv_file(name, opts, addr, sock):
    if not args.recv:
        err(sock, addr, 2, "write disabled")
        return
    os.makedirs(args.recv, exist_ok=True)
    path = os.path.join(args.recv, os.path.basename(name))
    if os.path.exists(path):
        err(sock, addr, 6, "file exists")
        log(f"[!] {path} existe deja, refuse")
        return
    if os.path.exists(path + ".part"):
        # Conserver un transfert interrompu : ne jamais ecraser un .part existant.
        err(sock, addr, 6, "partial file exists")
        log(f"[!] {path}.part existe deja, refuse (deplacer ou supprimer a la main)")
        return
    blksize, oack = negotiate(opts)
    reply = oack or struct.pack("!HH", 4, 0)
    log(f"[*] reception de {name} (options {opts}, blksize {blksize})")
    sock.settimeout(10)
    expected, total, t0 = 1, 0, time.time()
    with open(path + ".part", "xb") as f:
        sock.sendto(reply, addr)
        while True:
            try:
                pkt, a = sock.recvfrom(65536)
            except socket.timeout:
                log(f"[!] timeout pendant {name} ({total} octets)")
                return
            if len(pkt) < 4 or a[0] != addr[0]:
                continue
            op, blk = struct.unpack("!HH", pkt[:4])
            if op == 2 and expected == 1:
                addr = a
                sock.sendto(reply, addr)
                continue
            if a != addr or op != 3:
                continue
            if blk == expected & 0xFFFF:
                d = pkt[4:]
                f.write(d)
                total += len(d)
                expected += 1
                sock.sendto(struct.pack("!HH", 4, blk), addr)
                if len(d) < blksize:
                    break
            else:
                sock.sendto(struct.pack("!HH", 4, blk), addr)
    os.replace(path + ".part", path)
    dt = time.time() - t0
    log(f"[+] {name}: {total} octets recus en {dt:.1f} s")


srv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
srv.bind(("0.0.0.0", args.port))
log(f"[*] Ecoute UDP {args.port} | envoi depuis {args.serve} | reception vers {args.recv}")
while True:
    srv.settimeout(None)
    pkt, addr = srv.recvfrom(65536)
    if len(pkt) < 4:
        continue
    op = struct.unpack("!H", pkt[:2])[0]
    if op not in (1, 2):
        if DEBUG:
            log(f"    [dbg] ignore op={op} de {addr}")
        continue
    name, mode, opts = parse_req(pkt)
    if mode != "octet":
        err(srv, addr, 0, "octet only")
        continue
    (send_file if op == 1 else recv_file)(name, opts, addr, srv)
