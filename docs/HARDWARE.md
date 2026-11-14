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
| NAND | 128 MiB SPI NAND; the chip marking confirms ESMT F50D1G41LB, consistent with Linux detection; 2048-byte pages; 64-byte OOB; ECC 4 bits/512 bytes. A third-party review reports a GigaDevice NAND on another unit (see below); only the ESMT part was tested |
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

### Antenna mounting

The photographs show two rectangular green PCB antennas, one on each of
two opposite inner side walls beside the rear power and Ethernet openings.
Their broad faces are parallel to the walls. Their long edges run from the
case opening towards the closed end of the shell. Moulded plastic guides
overlap their edges. Adhesive behind the antennas cannot be confirmed.

One thin black coaxial cable is soldered to each antenna. The cables loop
into the case and stay connected to the lifted board. Small metal tabs hold
them near two gold-coloured board connectors. The connectors look like
miniature snap-on RF connectors; their exact U.FL/IPEX type is unconfirmed.
The photographs do not establish which antenna serves 2.4 GHz or 5 GHz.

Disconnect power before lifting the board. Support it near the shell and
watch both cables. Stop before either cable becomes taut. Do not pull on
the cables, solder joints or connectors. Keep the coloured UART leads free
as well; the loose-board photograph shows their black Dupont connectors.

![Board and two cabled PCB antennas outside the case; handwritten and ambiguous stamped marks are masked](photos/PHOTO-13a.jpg)

![Lifted board with both coaxial cables still connected to the antennas in the shell; a handwritten mark is masked](photos/PHOTO-13b.jpg)

![Antenna positions and moulded edge guides on opposite inner side walls, beside the rear openings](photos/PHOTO-13c.jpg)

### Chip access

The IPQ5018, QCN6122 and RTL8367S are under shields with thermal pads. Their
chip markings are not photographed here. A Russian-language
[DNS Club review](https://club.dns-shop.ru/review/t-280-marshrutizatoryi/85194-obzor-domashnei-wi-fi-mesh-sistemyi-mercusys-halo-h80x-kompaktno/) shows a board with the
shields removed; its author reports a GigaDevice NAND (written `5F1GQ5REY1G`)
and Zentel `A3T4GF40BBF-HP` RAM on that unit. This project has not checked
those markings. The flash chip may vary between batches; check the
bootloader's flash identification before any write on a unit with a
different chip. The NAND marking is visible in the
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
[bench view](photos/PHOTO-11.jpg). On the first unit, with the board powered,
the owner measured with a multimeter about **1.8 V** between `GND` and `TX`
(slight variation) and **3.3 V** between `GND` and `VCC`. The second unit was
not measured. `VCC` is a supply pad, not the logic level: do not connect it.
No separate level adaptation is used. **3.3 V logic has not been validated.**
Use the device's own power supply; do not connect an adapter power output to
the board. Wiring: `GND` to `GND`, board `TX` to adapter `RXD`, board `RX` to
adapter `TXD`.

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
