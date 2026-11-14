<!-- SPDX-FileCopyrightText: Etienne-T -->
<!-- SPDX-License-Identifier: CC0-1.0 -->

# Wi-Fi board data: provenance and private reproduction

Both radios worked during private RAM tests. This repository supplies no BDF,
`board.bin`, `board-2.bin`, vendor archive or image containing those files.
Redistribution permission has not been established. Public availability,
repackaging and the license of the wrapper script do not grant such permission.
These instructions make no legal assurance about extraction or use.

## Public source identified on 13 November 2026

The [official H80X v1 download page](https://www.mercusys.com/en/download/halo-h80x/v1/)
lists EU v1 firmware `1.1.0 Build 20220706` (published 14 October 2022).
The source archive is
[Halo_H80X(EU)_V1.0_22070620221014092447.zip](https://static.mercusys.com/software/Halo_H80X(EU)_V1.0_22070620221014092447.zip).
Only the fw_1 / DE combination below was traced; other regions and revisions
are not validated. The local publication study compared these public bytes
with the historical private containers; this export did not repeat extraction.

| Public object | Bytes | SHA-256 |
|---|---:|---|
| Official ZIP | 26576072 | `702e67db6f9380a5e54ee64356713d945ff0dcad0f9623caa4a7c8fb9cb114d7` |
| Firmware member | 28973693 | `39ce407bc84f4e7ea61fcf5a3c3defd6df3710f727e90e505b3a3bb0a84aec60` |
| Reconstructed SquashFS | 23192454 | `71460b52b739025eb86a957c60359c85a4b31cd67112d898aecc3c6aaee5da29` |
| IPQ5018 fw_1.tar.gz | 4217323 | `8731b6331116dbef66229238fc6e4d978f1c3d2a7240e95f5e4c12cad07d7b50` |
| IPQ5018 BDF | 131072 | `4f64ccef434cd929c6b25d561f9bb0d99feae861c5689731bbddcbc770d72ae9` |
| QCN6122 BDF | 131072 | `b1bb3066586da04dc2f5e12289ada379cef2f62fdb2b81864542b100302fe508` |

The firmware member is
`h80x-SP1-up-ver1-1-0-P1[20220706-rel76062]_2022-07-07_08.51.24.bin`.

- IPQ5018: rootfs `/lib/firmware/IPQ5018/fw_1.tar.gz`, member `./bdwlan_DE.b24`.
- QCN6122: rootfs `/lib/firmware/qcn6122/bdwlan_DE.b60`, a direct file, outside
  that tar archive.

The GPL PDF included by the vendor does not establish a BDF license. Qualcomm
radio executable firmware licenses do not automatically cover these OEM files.
Device-specific ART calibration is separate and must never be published.

## Advanced private workflow

1. Obtain the exact official ZIP yourself. Work locally without executing any
   vendor program. Check the ZIP and firmware member against the public hashes.
2. Recover the SquashFS with reviewed offline tools. For the traced image, UBI
   starts at `0x1814`, eraseblocks are `0x20000` bytes, and rootfs is volume 1
   with 184 consecutive logical blocks. Verify the complete reconstructed
   SquashFS hash before reading the two paths above. No complete hardened
   ZIP-to-BDF extractor is provided here; the legacy `ubi_extract.py` alone
   does not validate this entire chain or reject all ambiguous volumes.
3. With `unsquashfs`, read only the identified paths, and extract only the named
   member from the IPQ5018 tar. Check both raw BDF hashes and lengths. Do not use
   NAND backups or ART dumps as BDF inputs. Keep all outputs private.
4. From this repository, run the historical wrapper on those two local files:

   ```sh
   python3 openwrt/make_board2.py private-input/bdwlan_DE.b24      private-input/bdwlan_DE.b60 private-board-files
   ```

   Use a new private output directory. The script overwrites existing outputs
   and does not authenticate inputs. It creates the historical eight aliases
   per radio plus an API 1 `board.bin` fallback. The observed exact API 2 match
   is `bus=ahb,qmi-chip-id=0,qmi-board-id=255,variant=Mercusys-Halo-H80X-v1`.
   Generic aliases are historical compatibility choices, not validated IDs for
   other boards. This is not the future bounded, single-entry extractor.
5. Pass `private-board-files` as the optional third argument of `add_h80x.py`
   for a private build. The generated files and all images containing them
   remain excluded from publication, regardless of `.gitignore` coverage.

For comparison only, the historical eight-entry `board-2.bin` containers each
had 1049228 bytes. Their public-data-derived SHA-256 values are:

- IPQ5018: `f0b9f1fd35d2662cef7220c586d19b8f37fccc1dcc2e62d995d6e4ce9f1b0e22`
- QCN6122: `2a73b1cb89302191b22bea838200ced2378ec1eb8e2e6ae6cca3919078bb7a71`

The wrapper license covers its code, not those outputs. Do not substitute BDFs
from similar routers. The firmware's high-band restriction remained after
country changes; offline BDF comparisons did not amount to boot-testing every
regional variant. Use only the regulatory settings lawful for your location;
the historical defaults use DE and are not a recommendation for every country.
