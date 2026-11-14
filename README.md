<!-- SPDX-FileCopyrightText: Etienne-T -->
<!-- SPDX-License-Identifier: CC0-1.0 -->

# OpenWrt for the Mercusys Halo H80X v1

Experimental port for the Qualcomm IPQ5018 / QCN6122 Halo H80X v1,
target `qualcommax/ipq50xx`. This is a source and documentation repository.
It is not an official OpenWrt release or a vendor-supported installation.

## Status on 13 November 2026

Only one unit has been tested. OpenWrt was installed in the second flash bank,
`rootfs_1`, on 13 November 2026. The first bank, `rootfs`, held the stock
firmware and was not the installation target; it was not re-read afterwards.
A later OpenWrt upgrade from the second bank would target the first bank and
can overwrite stock. Two subsequent flash boots were reported with WPA2
configured, wireless interfaces disabled, and no LAN DHCP or IPv6 RA server.

Ethernet, the RTL8367S switch, three LAN ports, LEDs and factory MAC allocation
were tested in RAM. Both ath11k radios and client associations worked in RAM.
The reset GPIO was observed in RAM; the complete current button action remains
untested. PHY link rates are not throughput measurements.

The CPU-to-switch link uses SGMII at 1 Gbit/s. A 2.5 Gbit/s variant is untested.
Channels 100 and above were unavailable in the tested QCN6122 firmware rules.
Stock observations suggest a similar restriction, but strict parity is unproven.
Long-term stability, alternating upgrades and client association after flash
installation remain unverified. Never unload ath11k on a running unit: this
was reported to break Q6 operation; use a controlled reboot instead.

## Before using the port

The photographed USB-serial adapter uses an FTDI FT232RNL chip. Its voltage
jumper is set to `1V8`. On the first unit, a multimeter read about 1.8 V on
the `TX` pad and 3.3 V on the `VCC` pad, which is a supply and must not be
connected. **3.3 V logic has not been validated.** The board labels and
photographs of both units are documented in [Hardware](docs/HARDWARE.md) and
the [project story](docs/STORY.md#4-the-serial-console).

The build defaults use a DHCP client on LAN, disable DHCP/RA servers, and leave
Wi-Fi disabled with WPA2 keys generated locally. Verify these settings in your
own image before connecting it to an existing network.

No BDFs, vendor firmware archives or ready-made images are supplied.
Redistribution rights for the two board data files have not been established.
Private Wi-Fi builds used them; their absence here does not provide autonomous
Wi-Fi support. See [Wi-Fi and BDF provenance](docs/WIFI-BDF.md).

## Documentation

- [Build instructions and pinned revisions](docs/BUILD.md)
- [UART installation and recovery limits](docs/INSTALL.md)
- [Hardware and masked MAC allocation](docs/HARDWARE.md)
- [Wi-Fi board data](docs/WIFI-BDF.md)
- [Source provenance and known upgrade risks](docs/PROVENANCE.md)
- [Local tools and manifest-based verification](docs/TOOLS.md)
- [Project story](docs/STORY.md)
- [Installable source set](openwrt/install/README.md)

Text and code were largely produced by AI agents under the owner's direction,
with cross-checks by other agents. These cross-checks do not replace human
review or hardware tests. The historical observations above were taken from
local project records; preparing this export did not repeat hardware tests.
Current source includes later HTTPS dependencies and is not byte-identical to
the image installed on 13 November 2026. A fresh build remains necessary.

## Licensing

Original documentation and owner-supplied photographs are CC0-1.0; original code is marked MIT-0. Derived
OpenWrt code is GPL-2.0-only. The DTS files retain
`GPL-2.0-or-later OR MIT`. File annotations and [license texts](LICENSES/)
define the scope. Copyright annotations use the owner's pseudonym,
Etienne-T; see [licensing details](docs/LICENSING.md). None of these licenses covers BDFs.
