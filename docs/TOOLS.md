<!-- SPDX-FileCopyrightText: Etienne-T -->
<!-- SPDX-License-Identifier: CC0-1.0 -->

# Local tools

The Python tools are historical utilities. Review them before using device
dumps, firmware or a serial connection. Their output can contain device data;
keep it private. Python 3 is required; the new manifest verifier needs
Python 3.12 or newer. Serial tools additionally need
`pyserial`. The image verifier needs Linux `unsquashfs` and `zstd`.

- `stop_uboot.py`, `uboot_cmd.py`, `owrt_cmd.py`, `tx_test.py`: serial helpers,
  default `/dev/ttyUSB0`, 115200 baud. They transmit commands and are not a
  read-only access boundary. They were not run during export preparation.
  `stop_uboot.py` reports success only after it receives the `IPQ5018# `
  prompt; silence after the banner gives `indetermine`. This check was added
  on 14 November 2026 and has not been run on hardware.
- `tftp_server.py`, `tftp_recv.py`: historical UDP servers. They bind all IPv4
  interfaces and have no authentication. Use only on an isolated test network
  with limited firewall access. They are not hardened public servers.
  They refuse to replace an existing final file or an existing `.part` file
  from an interrupted transfer; inspect and move that file by hand before a
  new attempt. This refusal was added on 14 November 2026 and has not been
  run against U-Boot.
- `tftp_selftest.py`, `tftp_selftest_rrq.py`: historical loopback rollover tests;
  set `TMPDIR` to keep their files in a controlled local directory. They start
  an all-interface listener despite using a loopback client.
- `ubi_extract.py`, `dtb2dts.py`: offline format helpers, not general validators
  for hostile or malformed inputs. The UBI helper can choose the newest block
  sequence and reports some CRC failures without aborting.
- `verify_wpa2_images.py`: compares safe defaults and upgrade branches inside
  locally built images. It does not prove that a NAND write will succeed.

## Manifest-based chunk verification

`verify_split.py` accepts only a manifest provided locally by the user.
It has no stored device hashes or partition map. Never publish a manifest
made from a private device. Run:

```sh
python3 tools/verify_split.py local-manifest.json new-private-output
```

The JSON object contains `total_size`, ordered `chunks` and optional
`partitions` and `image_sha256`. Each chunk supplies `file`, `size`, `sha256`
and optionally `crc32`. Filenames are relative to the manifest directory.
Partition objects supply `name`, `offset`, `size`. Numbers are JSON integers
in bytes; CRC32 is eight hexadecimal digits and SHA-256 is 64.

Chunks are concatenated in manifest order. The script verifies all lengths
and hashes before creating the new output directory, then writes
`nand_full.bin` and any requested disjoint slices as `NAME.bin`. It refuses
existing output directories, duplicate names and ranges outside the image.
Its default maximum total size is 256 MiB, adjustable with `--max-bytes`.
This is verification of local files, not a flash-writing or restoration tool.
