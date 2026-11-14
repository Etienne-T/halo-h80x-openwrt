<!-- SPDX-FileCopyrightText: Etienne-T -->
<!-- SPDX-License-Identifier: CC0-1.0 -->

# Hardware and MAC allocation

Runtime observations concern one Halo H80X v1 tested on 12–13 November 2026.
Owner-supplied photographs and disassembly observations cover two units.
Other regions and hardware revisions have not been validated.

| Component | Observed specification |
|---|---|
| Platform | Qualcomm IPQ5018, two cores, AP-MP03.3, machid `0x8040002` |
| RAM | 512 MiB |
| NAND | 128 MiB SPI NAND; the chip marking confirms ESMT F50D1G41LB, consistent with Linux detection; 2048-byte pages; 64-byte OOB; ECC 4 bits/512 bytes |
| Switch | Realtek RTL8367S, MDIO address 29, driver `rtl8365mb` |
| Ethernet | Three RJ45 ports; DSA `lan1`/`lan2`/`lan3`; switch ports 0/1/2; CPU port 6 |
| CPU link | SGMII 1 Gbit/s in the tested port; 2.5 Gbit/s untested |
| Wi-Fi | IPQ5018 2.4 GHz and QCN6122 5 GHz, ath11k; memory mode 1 |
| UART | 115200 baud, 8N1; U-Boot interruption string `tpl` |
| GPIO | Reset button SW1, GPIO 33 active low; switch reset 39; QCN6122 reset 15 |
| LEDs | Red/green/blue: 23/24/29; port LEDs: 25/26/27 |

## Case and chip access

The owner reports the same opening procedure on both units. Remove the four
feet from the underside. Two holes contain Phillips screws; the other two
are empty. Remove the two screws, then pry along the visible case groove.
Opening requires force. The owner used plastic tools to avoid breaking the
case. The UART pads are accessible with the board still in the case.
The owner thinks a small soldering iron could reach them without removing
the board; this has not been verified.

The IPQ5018, QCN6122 and RTL8367S are under shields with thermal pads. Their
chip markings are not photographed. The NAND marking is visible in the
[close-up](photos/PHOTO-07.jpg). Reset switch `SW1` is accessible through the
small hole on the rear panel, between the power connector and Ethernet ports.
See the [disassembly and board photographs](STORY.md#2-opening-the-case-and-the-board).

## UART photographs and voltage limits

Both boards have four pads labelled `GND`, `VCC`, `RX`, `TX`. With the labels
upright in the published [first-unit](photos/PHOTO-09a.jpg) and
[second-unit](photos/PHOTO-09b.jpg) close-ups, that is their left-to-right order.
The second close-up shows the pads with the board still in the case.
These labels document the physical pad order; they do not measure voltage.

The photographed USB-serial adapter has an FTDI FT232RNL chip and a voltage
jumper set to `1V8`; see the [adapter detail](photos/PHOTO-10.jpg) and
[bench view](photos/PHOTO-11.jpg). The UART pad voltage has **not been measured**.
No separate level adaptation is documented. **3.3 V operation has not been
validated.** Neither the jumper setting nor the NAND voltage establishes the
UART pad voltage. Use the device's own power supply; do not connect an adapter
power output to the board.

## MAC relationships

Let `B` be the six-byte value from `factory_data/default-mac`, read at offset 0.
All octets below are masked, including the vendor prefix. Addition applies to
the complete 48-bit address, including carry; no real device suffix is shown.

| Interface | Address shown without device data | Relationship |
|---|---|---|
| LAN / `br-lan` / `eth0` conduit / label | `xx:xx:xx:xx:xx:xx` | `B` |
| IPQ5018 2.4 GHz | `xx:xx:xx:xx:xx:xx` | `B + 2` |
| QCN6122 5 GHz | `xx:xx:xx:xx:xx:xx` | `B + 3` |

There is no dedicated WAN port in this experimental bridge profile. No role
is assigned here to `B + 1`. The preinit helper mounts `factory_data` read-only.
Per-device radio calibration is read separately from `0:ART`: 128 KiB at
`0x1000` for IPQ5018 and 128 KiB at `0x26800` for QCN6122.

Two 42 MiB firmware banks start at `0x0640000` (`rootfs`) and `0x3040000`
(`rootfs_1`). Only those banks and `0:APPSBLENV` are writable in the installable
DTS. Bootloader, calibration and factory partitions must be preserved.
