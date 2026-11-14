#!/usr/bin/env python3
# SPDX-FileCopyrightText: Etienne-T
# SPDX-License-Identifier: MIT-0
"""Auto-test de tftp_recv.py : envoie 70 000 blocs (rebouclage 16 bits) et compare."""
import os
import socket
import struct
import subprocess
import sys
import tempfile
import time

d = tempfile.mkdtemp(dir=os.environ.get('TMPDIR'))
srv = subprocess.Popen([sys.executable, os.path.join(os.path.dirname(__file__), "tftp_recv.py"), d, "6970"])
time.sleep(0.5)
payload = os.urandom(512 * 70000 + 123)
c = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
c.settimeout(5)
c.sendto(struct.pack("!H", 2) + b"t.bin\0octet\0", ("127.0.0.1", 6970))
ack, peer = c.recvfrom(100)
assert ack == struct.pack("!HH", 4, 0), ack
blk = 1
for i in range(0, len(payload) + 1, 512):
    c.sendto(struct.pack("!HH", 3, blk & 0xFFFF) + payload[i:i + 512], peer)
    a, _ = c.recvfrom(100)
    assert struct.unpack("!HH", a) == (4, blk & 0xFFFF), a
    blk += 1
time.sleep(0.5)
srv.terminate()
got = open(os.path.join(d, "t.bin"), "rb").read()
print("SELFTEST", "OK" if got == payload else f"ECHEC {len(got)} vs {len(payload)}")
