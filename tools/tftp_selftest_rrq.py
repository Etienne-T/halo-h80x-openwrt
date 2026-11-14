#!/usr/bin/env python3
# SPDX-FileCopyrightText: Etienne-T
# SPDX-License-Identifier: MIT-0
"""Auto-test de l'envoi (RRQ) de tftp_server.py, avec options et rebouclage du n° de bloc."""
import os
import socket
import struct
import subprocess
import sys
import tempfile
import time

d = tempfile.mkdtemp(dir=os.environ.get('TMPDIR'))
payload = os.urandom(1468 * 66000 + 77)  # > 65535 blocs
open(os.path.join(d, "f.bin"), "wb").write(payload)
srv = subprocess.Popen([sys.executable, os.path.join(os.path.dirname(__file__), "tftp_server.py"),
                        "--serve", d, "--port", "6971"])
time.sleep(0.5)
c = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
c.settimeout(5)
c.sendto(struct.pack("!H", 1) + b"f.bin\0octet\0blksize\x001468\0tsize\x000\0", ("127.0.0.1", 6971))
oack, peer = c.recvfrom(2000)
assert oack[:2] == b"\x00\x06" and b"tsize\0" + str(len(payload)).encode() in oack, oack
c.sendto(struct.pack("!HH", 4, 0), peer)
got, expect = bytearray(), 1
while True:
    pkt, _ = c.recvfrom(2000)
    op, blk = struct.unpack("!HH", pkt[:4])
    assert op == 3 and blk == expect & 0xFFFF, (op, blk, expect)
    got += pkt[4:]
    c.sendto(struct.pack("!HH", 4, blk), peer)
    expect += 1
    if len(pkt) - 4 < 1468:
        break
time.sleep(0.3)
srv.terminate()
print("SELFTEST RRQ", "OK" if bytes(got) == payload else f"ECHEC {len(got)} vs {len(payload)}")
