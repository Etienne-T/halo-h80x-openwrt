<!-- SPDX-FileCopyrightText: Etienne-T -->
<!-- SPDX-License-Identifier: CC0-1.0 -->

# Contributor instructions

Read the README and the installation limits before changing the port.
Never distribute device backups, factory identifiers, calibration data,
private keys, network configuration, BDFs or images containing them.
Use masked MACs and public firmware references in documentation.

Hardware access and flash writes require explicit owner authorization.
Test in RAM first. Preserve the bootloader and device-specific partitions.
Keep Wi-Fi disabled with WPA2 configured, and verify that LAN DHCP and RA
servers are disabled before connecting to an existing network.
Do not unload ath11k at runtime. Do not publish changes without owner approval.
Keep text in UTF-8 without BOM and with LF endings. Preserve file licenses.
