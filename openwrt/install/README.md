<!-- SPDX-FileCopyrightText: Etienne-T -->
<!-- SPDX-License-Identifier: CC0-1.0 -->

# Installable source set

Use [BUILD.md](../../docs/BUILD.md) and [INSTALL.md](../../docs/INSTALL.md).
The installable DTS makes `rootfs`, `rootfs_1` and `0:APPSBLENV` writable and
adds the root command line. Thirteen other partitions remain read-only.
The [historical RAM DTS](../history/ipq5018-h80x-v1-ram.dts) keeps all sixteen
partitions read-only. `add_h80x.py` copies whichever DTS the caller supplies.

| File | Role |
|---|---|
| `ipq5018-h80x-v1.dts` | Installable hardware description |
| `ipq50xx.mk-h80x.txt` | Reference device profile; the Python integrator also embeds the profile |
| `platform.sh-h80x-case.txt` | H80X inactive-bank upgrade case, read by the integrator |
| `uboot-envtools-h80x.txt` | Full historical platform reference, not an extra file to install |
| `uci-defaults/99-h80x-test-lan` | DHCP client LAN; no LAN DHCP/RA server |
| `uci-defaults/99-h80x-wifi-safe` | Locally generated WPA2 keys; interfaces disabled |

The actual environment-script destination is
`package/boot/uboot-tools/uboot-envtools/files/qualcommax_ipq50xx`.
The integrator also patches network, LEDs, caldata, preinit and the shared
`package/base-files/files/lib/upgrade/nand.sh`. The full environment reference
is preserved for provenance; a future upstream patch should be minimal.

OpenWrt was installed on one unit on 13 November 2026. These sources also
include later HTTPS dependencies and have not been rebuilt as an export.
They are not a guarantee of recovery or safe alternating upgrades.
