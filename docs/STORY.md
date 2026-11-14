<!-- SPDX-FileCopyrightText: Etienne-T -->
<!-- SPDX-License-Identifier: CC0-1.0 -->

# Porting OpenWrt to the Mercusys Halo H80X v1

> **About this text.** This story was written by AI agents from the project's
> journal and test reports. Other AI agents checked it claim by claim. It
> will be reviewed by the repository owner before publication. It describes
> the software work as it stood on **13 November 2026**. Owner-supplied
> photographs and disassembly details from two units were added on
> **14 November 2026**.
>
> It is **not** official OpenWrt documentation or support. The Halo H80X is not
> an OpenWrt-supported device, nothing described here has been submitted to the
> OpenWrt project, and the OpenWrt tests described here used **a single unit**.

> **Warning: serial voltage.** On the first unit, a multimeter read about
> **1.8 V** between `GND` and `TX` and **3.3 V** between `GND` and `VCC`.
> `VCC` is a supply pad, not the logic level: never connect it. The
> photographed FTDI FT232RNL adapter has its voltage jumper set to `1V8`.
> **3.3 V logic has not been validated.** Measure the pads on your own unit
> before connecting anything.

## In short

- Since 13 November 2026, OpenWrt (snapshot of `main`, Linux 6.18) runs from
  the flash of one H80X. It sits in the second firmware bank. According to the
  journal, the write targeted that bank, not the first bank that holds the
  stock firmware; the first bank was not read back after installation.

- Seen working on the hardware: Ethernet through the RTL8367S switch (three
  ports), the status and port LEDs, the reset button at the electrical level,
  both Wi-Fi radios (2.4 GHz and 5 GHz, `ath11k` driver), and the unit's own
  MAC addresses.
- The only installation route demonstrated in this project uses the serial
  console. According to static analysis, the stock web page and the
  bootloader's recovery page only accept firmware signed by the vendor.

- Main limits:
  - The Wi-Fi board data files come from the stock firmware and may not be
    redistributable, so Wi-Fi cannot be rebuilt from this repository alone.

  - 5 GHz channels 100 and above are unavailable in the tested configuration.

  - The link between the CPU and the switch runs at 1 Gbit/s.

  - Going back to the stock firmware is documented but has never been tested
    end to end.

## 1. The device and the motivation

The Halo H80X v1 is a mesh Wi-Fi unit sold by Mercusys, a TP-Link brand. Its
stock firmware is a vendor system built on OpenWrt, with Linux 4.4.60 and a
U-Boot 2016.01 bootloader built on 11 May 2022. The unit used
here was running stock version 1.1.0 (Build 20220706) in both of its firmware
banks.

Searches made on 12 and 13 November 2026 found no OpenWrt pull request
mentioning the H80X. The only OpenWrt forum thread found about it dates from
2022 and ended without a result.

The project notes give the intended end use: an OpenWrt access point with one
VLAN per Wi-Fi network (SSID). That goal has not been validated yet.

![Halo H80X v1, front panel and top vents](photos/PHOTO-01a.jpg)

![Rear panel with power connector, reset hole and three Ethernet ports](photos/PHOTO-01b.jpg)

![Underside with four feet and an opaque mask over the label](photos/PHOTO-01c.jpg)

## 2. Opening the case and the board

The owner reports the same procedure on both units:

1. Remove the four feet from the underside. Two holes contain Phillips
   screws; the other two holes are empty.
2. Remove the two screws.
3. Pry along the visible groove in the case. Opening requires force.
   The owner used plastic tools to avoid breaking the case.

A Russian-language [review on DNS Club](https://club.dns-shop.ru/review/t-280-marshrutizatoryi/85194-obzor-domashnei-wi-fi-mesh-sistemyi-mercusys-halo-h80x-kompaktno/)
shows further photographs of the device and its disassembly. Those photographs
belong to their authors and are not part of this repository.

The board can stay in the case: the UART pads are accessible once the case
is open. The owner thinks a small soldering iron could reach the pads without
removing the board. This has not been verified.

![Underside with the four feet removed, exposing the screw access holes](photos/PHOTO-02a.jpg)

![Case groove used as the prying point](photos/PHOTO-02b.jpg)

![Bottom cover removed, board still in the case, and plastic opening tools](photos/PHOTO-02c.jpg)

![Board face marked TOP, with shields and thermal pads](photos/PHOTO-03a.jpg)

![First unit with the black heat spreader fitted and the board still in the case](photos/PHOTO-03b.jpg)

![Second unit with the heat spreader fitted and the board still in the case](photos/PHOTO-03c.jpg)

![Board face marked BOT, with the exposed NAND chip and shields](photos/PHOTO-04.jpg)

## 3. The main chips

The table lists each part and how the project identified it.

| Part | What | How it was identified |
|---|---|---|
| SoC | Qualcomm IPQ5018, two cores, 512 MiB RAM; reference design AP-MP03.3 (`machid 0x8040002`) | Bootloader output and prompt (`IPQ5018#`) |
| Flash | ESMT F50D1G41LB SPI-NAND, 128 MiB, 2048-byte pages, 64-byte spare area, 4-bit ECC, a 1.8 V part, no bad blocks found | Chip marking and Linux detection for the part; bootloader output for geometry and bad-block scan |
| Switch | Realtek RTL8367S, three RJ45 ports on switch ports 0–2, CPU on port 6 | Found by the Linux `rtl8365mb` driver at MDIO address 0x1d |
| 2.4 GHz Wi-Fi | Radio built into the IPQ5018 | Stock device tree, then `ath11k` |
| 5 GHz Wi-Fi | Qualcomm QCN6122, started by the SoC's Q6 co-processor (not a PCIe device seen by Linux) | Stock device tree, then `ath11k` |

Linux detects the flash chip as an ESMT SPI-NAND, in two separate boot logs.
Early project notes attributed it to GigaDevice. The marking read on the
chip shows **ESMT F50D1G41LB**, consistent with Linux detection.
The exact switch variant (RTL8367S rather than another member of the family)
is inferred from the driver and the stock files, not read from the chip.
The IPQ5018, QCN6122 and RTL8367S are under shields with thermal pads.
There are no photographs of their chip markings.

The stock device tree also declares a slot for a third radio (a QCN9000 on
PCIe). It is disabled.

Board signals that were confirmed on the running hardware:

| Signal | GPIO |
|---|---|
| Reset button (active low) | 33 |
| Status LEDs red / green / blue | 23 / 24 / 29 |
| Port LEDs lan1 / lan2 / lan3 | 25 / 26 / 27 |

The switch reset line, GPIO 39, comes from the stock device tree. The switch
works with this setting, but its reset function was not tested on its own.

![NAND chip with the ESMT F50D1G41LB marking](photos/PHOTO-07.jpg)

## 4. The serial console

The serial console was reached with a USB-serial board using an FTDI FT232RNL
chip, attached to a Linux machine, at **115200 baud, 8N1**. Both directions work. A small script
(`tools/tx_test.py`) was used to check the transmit wire on its own.

**Logic level.** On the first unit, with the board powered, the owner
measured with a multimeter about **1.8 V** between `GND` and `TX`, with a
slight variation, and **3.3 V** between `GND` and `VCC`. A multimeter
averages the signal while the board transmits, so the variation is expected;
when the reading was taken relative to serial activity was not recorded. The
second unit was not measured. The `TX` reading matches the adapter's `1V8`
jumper setting seen in the photo. `VCC` is a supply pad, not the logic level.
No separate level adaptation is used, and **3.3 V logic has not been
validated**.

**Pinout.** Both boards have four pads labelled `GND`, `VCC`, `RX`, `TX`.
With the labels upright in the close-ups below, that is their left-to-right
order. The second view shows the pads with the board still in the case.
Do not connect the `VCC` pad or adapter VCC. Wire `GND` to `GND`, board
`TX` to adapter `RXD` and board `RX` to adapter `TXD`. Check the labels and
measure the pad voltage on your own unit before wiring it. The bench photograph documents
the equipment used; it does not verify each wire or its electrical level.

One detail matters for the device tree. On the reference design, GPIO 29
can carry the UART transmit line. On the H80X it drives the blue status LED.
For that reason the OpenWrt device tree does not set the UART pin function. It
keeps the setting made by the bootloader.

Under the stock firmware, the Linux console prints `Please press Enter to
activate this console`. According to the stock `inittab`, a login program
follows. That console was never used interactively in this project.

![First unit UART pads, labelled GND, VCC, RX, TX from left to right](photos/PHOTO-09a.jpg)

![Second unit UART pads in the case, rotated to show the same GND, VCC, RX, TX order](photos/PHOTO-09b.jpg)

![FTDI FT232RNL USB-serial adapter with the voltage jumper set to 1V8](photos/PHOTO-10.jpg)

## 5. Stopping U-Boot

At power-on, the bootloader prints `Enter magic string to stop autoboot in 1
seconds`. The magic string is **`tpl`**. Once it is accepted, you get the
`IPQ5018#` prompt.

Typing three letters in one second by hand is unreliable, so the project uses
a script, `tools/stop_uboot.py`. You start the script first and then
power-cycle the device. The script waits for the U-Boot banner, sends `tpl`
over and over for up to six seconds, and reports a failure if it sees the
kernel start instead.

Two facts from the first session shaped what came next:

- the secure boot fuse of this unit is **not** enabled (U-Boot's own check
  reports it);
- the U-Boot environment only contained `baudrate` and `has_default_mac`. The
  bank-selection variable discussed later, `tp_boot_idx`, was absent.

During the RAM-test sessions, the project rule was to change U-Boot variables
only in RAM with `setenv`, never with `saveenv`. This is a stated rule; no
complete command log proves it. The U-Boot environment was changed
persistently once, during the authorised installation of 13 November 2026,
when the upgrade script set the bank flag (section 10).

## 6. Backing up the NAND

Nothing was changed before a full copy of the flash existed. The method:

1. In U-Boot, read the 128 MiB NAND into RAM in eight 16 MiB chunks.
2. Compute a CRC32 of each chunk in U-Boot.
3. Send each chunk to a PC over TFTP (`tftpput`).

This U-Boot's TFTP client is unusual: it always talks to port 69, rejects
replies that do not come from port 69, and insists on option negotiation
(`blksize 1468`, `timeout 5`). Common TFTP servers did not cope. The project
therefore wrote its own server, `tools/tftp_server.py`, which both sends and
receives. The Linux machine attached to the UART could not
receive the transfers: its firewall could not be opened without an
interactive password. A second machine received them instead, with temporary
firewall rules.

**Checks.**

- According to the journal, the CRC32 of each of the eight chunks matched
  between U-Boot and the PC. A later check matched the files against the CRC
  values recorded by the session script. The U-Boot console output itself was
  not re-examined independently.
- The project's original `tools/verify_split.py` refused to assemble the image
  if any chunk had the wrong size or CRC. It then built the 128 MiB image, cut
  it into one file per partition, and wrote a SHA-256 manifest. That version
  contained check values specific to this backup. The public repository ships
  a generic replacement that takes a manifest supplied by the user; see
  `docs/TOOLS.md`.
- A content check confirmed that the bootloader is present in its partition
  and that the Wi-Fi calibration partition is not empty.
- A later local check matched all 18 manifest entries and the assembled
  image. In both firmware banks, the kernel image and the SquashFS root were
  identical to the public 1.1.0 package.

**Limits.**

- `nand read` returns ECC-corrected data **without the spare (OOB) area**. The
  backup is not a raw physical copy of the chip. It is intended
  for a restore from U-Boot, but that use has never been tested.

- **A restore has never been tried.** A second, independent copy of the
  backup is not documented either.
- The `factory_data` partition holds the unit's identifiers and a **private
  RSA key**. The backup therefore stays on the owner's machine. It is
  excluded from version control and is not published, quoted or summarised
  anywhere.

The flash layout, as read from the bootloader and later from Linux:

| # | Partition | Offset | Size | Role |
|---|---|---|---|---|
| 0–6 | `0:SBL1`, `0:MIBIB`, `0:BOOTCONFIG`, `0:BOOTCONFIG1`, `0:QSEE`, `0:DEVCFG`, `0:CDT` | 0x0 | 0x300000 in total | Early boot chain and configuration |
| 7 | `0:APPSBLENV` | 0x300000 | 0x80000 | U-Boot environment |
| 8 | `0:APPSBL` | 0x380000 | 0x140000 | U-Boot |
| 9 | `0:ART` | 0x4c0000 | 0x100000 | Wi-Fi calibration |
| 10 | `0:TRAINING` | 0x5c0000 | 0x80000 | Empty |
| 11 | `rootfs` | 0x640000 | 0x2a00000 | Firmware bank 0 (UBI) |
| 12 | `rootfs_1` | 0x3040000 | 0x2a00000 | Firmware bank 1 (UBI) |
| 13 | `0:ETHPHYFW` | 0x5a40000 | 0x80000 | Empty |
| 14 | `factory_data` | 0x5ac0000 | 0x900000 | Identity data, MAC address (UBIFS) |
| 15 | `runtime_data` | 0x63c0000 | 0x1100000 | Stock settings (UBIFS) |

## 7. Studying the stock firmware

### Booting the stock kernel from RAM

The first test checked the RAM-boot method itself, without any deliberate
write to the flash. The stock kernel volume was extracted from the backup with
`tools/ubi_extract.py` and loaded over TFTP to `0x44000000`. Its CRC was
checked, and it was started with `bootm 0x44000000#config@mp03.3`. The stock
system booted completely, Wi-Fi included. The kernel ran from RAM and no
firmware bank was deliberately rewritten. The stock system still mounted its
root filesystem from the flash, so internal writes by the stock firmware
cannot be ruled out. The final kernel command line contained
`swiotlb=1 coherent_pool=2M`. These two parameters come from the
`bootargs-append` property of the stock device tree, which the kernel
processes; that detail mattered later. The test also gave a
usable RAM window: images can be loaded between `0x44000000` and about
`0x4A800000`, below the relocated U-Boot at `0x4A920000`.

### What the stock files reveal

All the Wi-Fi parameters came from readable scripts and from the stock device
tree, without disassembling any driver:

- calibration data at offsets `0x1000` and `0x26800` of `0:ART`, 128 KiB each;
- board IDs `0x24` (IPQ5018) and `0x60` (QCN6122);
- board data files (BDF) in CA, DE, JP and US variants, with DE as the factory
  setting;
- start parameters for the QCN6122, including its reset line on GPIO 15.

The stock Wi-Fi firmware is `WLAN.HK.2.5.r4-00622`. The proprietary
`qca-wifi` drivers that go with it cannot be used with a 6.x kernel.
 The stock device tree was decompiled with `tools/dtb2dts.py` and
kept as a reference.

### Can it be installed without opening the case? Not with any method demonstrated so far

**The stock web page.** The local-upgrade page hands the uploaded file to the
stock updater, `nvrammanager`, which checks it and then writes it.
 Part of that updater's image check is shared with OpenWrt's
`mercusys-fwup.py`, the tool that builds installable images for the Mercusys
MR80X v2. The first hypothesis was therefore that the MR80X method would work
here too.

Static analysis of the H80X updater ruled this out. As far as that analysis
goes, writing an image requires a valid vendor RSA signature, so the MR80X
method cannot be used with the H80X installer studied. No installation of
such an image was attempted. When the updater does accept a
signed image, it writes the inactive bank and then sets `tp_boot_idx`.

**Older stock firmware.** The public versions that can be unpacked (1.0.0,
1.1.0, 1.1.1, 1.1.3) all carry the same `nvrammanager`, byte for byte.
 The updater refuses to go back to an older major or minor version,
so 1.0.0 would be refused anyway. Version 1.1.2 was published for
Singapore only. The tools and probes used could not extract its content,
which looks random. The known check of the Linux updater studied fails on the
raw file. Its updater is therefore unknown. The firmware file
published for the sister model Halo H3000X (1.1.1) is byte-identical to the
H80X 1.1.1 file, so it brings nothing new.

**The bootloader's recovery page.** Holding the reset button at power-on
starts a small web server inside U-Boot, before Linux. Static analysis ties
that button to GPIO 33, the same input Linux sees as the reset button: the
GPL source defines the recovery key as GPIO 33, and the register address
tested by the actual binary matches it. The GPL source and the strings in the
binary also agree on the page's behaviour. The page keeps the upload in RAM.
It checks an MD5 and an RSA signature (128-byte signature, so RSA-1024,
against a public key built into U-Boot) **before** any write. On failure it
shows an error and writes nothing. This recovery path has never been
exercised on the hardware. On success, it writes the bank
opposite the current one and updates `tp_boot_idx`. This is a
way back to signed stock firmware. It cannot install OpenWrt.

**Administration services on the stock firmware.** Administration components
are present in the stock image. Their actual accessibility, and any
installation route through them, have not been validated. Testing passwords
and bypassing authentication were deliberately out of scope.

**Conclusion.** A later survey of the methods used on related TP-Link and
Mercusys devices reached the same verdict. Installing without the serial
console is unlikely as things stand, though not ruled out in principle. The
only installation route demonstrated in this project uses the serial
console.

## 8. The port

### Starting point

The work is based on OpenWrt `main` at commit `30a23ae451` (r38212), with
Linux 6.18.60 and the target `qualcommax/ipq50xx`. Two devices
already supported by OpenWrt served as references:

- the **Mercusys MR80X v2**: same SoC, switch and flash, but 256 MiB of RAM.
  Its upstream support leaves Wi-Fi disabled for lack of memory;
- the **TP-Link Archer AX55 v1**: IPQ5018 with QCN6122, 512 MiB of RAM and
  two firmware banks.

The first full build took about 45 minutes on 8 cores. A single
script, `openwrt/add_h80x.py`, applies all the project's additions to an
OpenWrt tree:

- the device tree and the image recipe;
- the MAC, LED and calibration scripts and the `factory_data` mount;
- the U-Boot environment entry and the bank-switching upgrade case;
- a fix to the shared NAND upgrade helper;
- two first-boot safety scripts.

Running it twice gives the same result.

### Device tree

The device tree started from the MR80X v2 one. It was then adapted to the
H80X's own stock device tree: switch reset on GPIO 39, the button and LED GPIOs
listed above, three Ethernet ports, and no UART pin setting.

The CPU talks to the switch over SGMII at 1000 Mbit/s, set the same way on
both ends. The link was observed at 1 Gbit/s under OpenWrt. The
stock device tree configures that link as SGMII with a forced speed of
2500 Mbit/s. The speed actually used by the stock firmware was not measured.
Section 13 covers the 2.5 Gbit/s variant.

### Partitions

The flash layout is fixed in the device tree. In the installable version,
only three partitions can be written under OpenWrt's kernel: `0:APPSBLENV`
(U-Boot environment), `rootfs` and `rootfs_1` (the two firmware banks). The
other thirteen are read-only, including the whole boot chain, `0:ART` and
`factory_data`. The test version used for early RAM boots kept all sixteen
read-only. These flags do not protect against U-Boot commands or another
kernel.

The device tree appends `root=/dev/ubiblock0_1 coherent_pool=2M` to the
kernel command line. U-Boot itself supplies `ubi.mtd=rootfs` or
`ubi.mtd=rootfs_1`, depending on the bank.

### MAC addresses, read without writing

The stock firmware keeps the base MAC address in a 6-byte file,
`default-mac`, in the UBIFS volume of `factory_data`. The kernel
attaches that partition in read-only mode, because the device tree marks it
read-only. An early boot script then mounts the volume read-only and reads the
address. The project keeps the stock offsets:

| Interface | Address |
|---|---|
| LAN, `eth0`, label | base |
| WAN | base + 1 (not used: no WAN port is defined) |
| 2.4 GHz radio | base + 2 |
| 5 GHz radio | base + 3 |

The MR80X v2 uses base - 1 and base - 2 for its radios. Both conventions exist
in TP-Link's stock scripts. Before this step, OpenWrt ran with
U-Boot's placeholder address. One message is worth knowing: in
read-only mode, UBIFS reports that the `factory_data` volume "needs recovery"
and defers it. No repair was attempted.

The port LEDs follow the link state of each port through OpenWrt's `netdev`
trigger.

### Wi-Fi, board data files and `coherent_pool=2M`

The device tree enables the Q6 co-processor with the stock start parameters.
It also declares two radios: the internal 2.4 GHz radio and the QCN6122 for
5 GHz. Both use memory mode 1 and a calibration variant string specific to
the H80X. The memory addresses follow OpenWrt's standard layout for mode 1,
not the stock ones.

**The first attempt failed** with `DMA pool exhausted for pd-1`, then
`Failed to load program segments: -12`. The fix was to add
**`coherent_pool=2M`** to the kernel command line, which is the value the
stock device tree adds. The OpenWrt device tree now adds it. **Without it,
Wi-Fi does not start.**

Both radios report default identifiers over QMI (`chip_id 0`,
`board_id 0xff`). This suggests that no board identity was programmed into
their one-time-programmable area, but that area was not read in full. The
driver therefore asks for the board data by this name:

`bus=ahb,qmi-chip-id=0,qmi-board-id=255,variant=Mercusys-Halo-H80X-v1`

For the QCN6122, a debug build confirmed an exact match, with no fallback to
a generic entry.

The board data files come from the stock firmware 1.1.0. The IPQ5018 file is
`bdwlan_DE.b24`, a member of the archive `/lib/firmware/IPQ5018/fw_1.tar.gz`,
which matches hardware version 1. The QCN6122 file is
`/lib/firmware/qcn6122/bdwlan_DE.b60`, a plain file in the stock root
filesystem. Both are byte-identical to the files in the public 1.1.0 firmware
package. `openwrt/make_board2.py` packs each one, unchanged, into the
`board-2.bin` container that `ath11k` expects.
OpenWrt ships a newer Wi-Fi firmware (`WLAN.HK.2.7.0.1-01744`) than the one
these files were made for (2.5). The combination worked in the recorded tests
once `coherent_pool=2M` was added. This does not prove general compatibility.
 The per-unit calibration is a separate file, extracted at boot
from `0:ART`. It does not depend on the board data files.

**Licence.** No text consulted grants the right to republish these two
files. They are kept out of version control and will not be in the public
repository. OpenWrt has accepted board data files taken from other vendors'
stock firmware (for example the Archer AX55 v1). That precedent does not grant
any rights over the H80X files. A first upstream proposal without Wi-Fi would
follow the MR80X v2 precedent.

**Never unload `ath11k` while the system runs.** On the IPQ5018, `rmmod ath11k`
leaves the Q6 co-processor unable to restart (`failed to boot the remote
processor Q6`) until a hardware reset.

### Image recipe and upgrade path

The image recipe follows the MR80X v2:

- a FIT kernel image;
- the kernel stored inside UBI;
- no `factory.bin`, because the stock web page cannot install it (see
  section 7);
- a maximum image size equal to one bank (43008 KiB).

 The resulting `sysupgrade.bin` is a tar archive with a control
file, the kernel and the root filesystem. The U-Boot environment
settings for `fw_printenv`/`fw_setenv` match the stock configuration.

The upgrade case for the H80X, in `platform.sh`, follows this ordinary path:

1. It reads `tp_boot_idx`. If the value read is exactly `1`, the preferred
   bank is `rootfs_1` and the target is `rootfs`. Any other result makes
   `rootfs_1` the target. The current code does not distinguish a failed read
   of the environment from an absent variable.
2. It removes the stock volumes from the target bank and writes the new
   firmware.
3. **Only if the write succeeded**, it sets `tp_boot_idx` to `1`, or clears
   it when the target is `rootfs`.

OpenWrt's option to write the current bank instead is also kept in the
script. With that option, the current bank is written and the bank flag is
left unchanged.

Step 3 needed a fix in shared OpenWrt code. Two independent reviews found
that the common NAND helper (`nand_upgrade_tar` in `nand.sh`) ended with an
unconditional `return 0`. A failed volume write was therefore reported as a
success, and the bank flag would have been switched anyway. A simulation
reproduced it. The project patches the helper:

- it collects the status of each write and uses `pipefail`;
- it checks that the target volumes exist;
- it returns the real status;
- the failure path now really stops.

The integration script applies this patch. Its limit: it propagates errors
but does not read back what was written. A power cut during the write or
during `fw_setenv` stays outside its control.

### First-boot safety scripts

Two scripts run once, at first boot, before the network starts:

- `99-h80x-test-lan` turns the LAN into a DHCP **client** and disables the
  DHCP server, router advertisements and DHCPv6 on it. Section 14 explains
  why.
- `99-h80x-wifi-safe` sets every Wi-Fi interface to WPA2 (`psk2`) and
  disabled. It generates a random key per interface on the device (32 bytes
  from `/dev/urandom`, 64 hex characters) and sets the country to DE. It never
  enables Wi-Fi.

No Wi-Fi key exists in the sources or in the images.

After installation, the web interface turned out to answer on HTTP only.
The TLS library was present, but no certificate generator was included, so
`uhttpd` started without HTTPS. Installing the missing package
(`px5g-mbedtls`) fixed it: TLS 1.3 and HTTP 200 were observed. The package
was added to the recipe. **No full image has been rebuilt since**, and nobody
has checked whether the fix survives a reboot.

## 9. Testing in RAM

The initramfs images described here were booted from RAM over TFTP. The
sysupgrade images were inspected off the device, and then the WPA2 image was
installed (section 10). No deliberate write command was run during these RAM
checks. The sequence at the U-Boot prompt:

```text
setenv autoload no
dhcp
setenv serverip <address of the TFTP server>
tftpboot 0x46000000 <image>.itb
crc32 0x46000000 <size>          # compare with the CRC computed on the PC
setenv bootargs console=ttyMSM0,115200n8
bootm 0x46000000#config@mp03.3
```

Set `autoload no` before `dhcp`. Once, quoting problems between two shells
mangled the commands, and U-Boot's `dhcp` tried on its own to download a
default file name over TFTP. The file did not exist and nothing booted, but
the risk is clear. For the documented TFTP boots, the CRC
computed in U-Boot was compared with the local one.

The milestones:

- **12 November: first OpenWrt boot.** OpenWrt `r38212-30a23ae451`, Linux
  6.18.60, board name `mercusys,h80x-v1`, about 432 MB of RAM available,
  working serial console and SSH. The switch driver found the
  RTL8367S and created `lan1` to `lan3`, with an SGMII 1 Gbit/s link to the
  CPU. In U-Boot, `mii info` sees nothing on that bus. This is expected: the
  switch does not present itself as a PHY. The NAND and its 16
  partitions were detected. Nothing was attached or written. The
  LEDs were checked by eye, one by one. Each press of the reset
  button was seen on GPIO 33. During this test the reset handler was
  disabled, so that a press would not reboot the device, and it was restored
  afterwards.
- **12 November: Wi-Fi.** Both radios came up once `coherent_pool=2M` was in
  place. A phone associated to test access points protected
  with WPA2, country DE. The link readings with the phone as
  client showed 1200.9 Mbit/s on 5 GHz (HE80, MCS 11, two streams, -46 dBm)
  and 155–172 Mbit/s on 2.4 GHz (HE20, MCS 6–7, two streams). **These are PHY
  link rates, not throughput. No throughput test was run.**
- **12 November: robustness.** Ten cycles of `wifi down` and `wifi up`
  brought both radios back every time, with no `ath11k` error or recovery and
  no net memory loss. 160 MHz on channel 36 worked after the 60-second radar
  check. 40 MHz on 2.4 GHz fell back to 20 MHz because of nearby networks,
  which is normal behaviour. The CPU stayed around 50 °C. About 240 MB of RAM
  remained available with Wi-Fi loaded, and the LuCI web interface
  answered.
- **12 November: installable device tree.** The kernel's partition flags
  showed exactly three writable partitions (`0:APPSBLENV`, `rootfs`,
  `rootfs_1`). Both radios came up, the MAC addresses were correct,
  `factory_data` was mounted read-only, and `ath11k` did not crash.

- **13 November: confirmation build.** The rebuild confirmed and fixed two
  integration gaps. A wrong path in the integration script meant that the
  U-Boot environment configuration was never installed: the script printed
  "file not found, step skipped" and carried on. And the H80X case was never
  inserted into `platform.sh`, so an upgrade would have fallen back to the
  generic routine, without bank switching. Both were fixed.
- **13 November: "final" image, rated red.** Everything worked, but the
  default Wi-Fi configuration said `encryption=none`, with the interfaces
  disabled. That is OpenWrt's normal default, not an open access point. It
  still broke the project rule "always WPA2".
- **13 November: image with the NAND fix.** The running system contained
  exactly the patched `nand.sh` and `platform.sh`, checked by SHA-256 against
  the build.
- **13 November: WPA2 image.** On first boot, with no manual change: both
  interfaces in `psk2` and disabled, keys present (only their length was
  checked), country DE, no interface created, both radios present. The LAN
  protection was active, with no DHCP or DHCPv6 server socket, and the
  partition flags were as expected. An independent offline audit
  checked both images against the hashes recorded in the local build report
  and found the two first-boot scripts byte-identical to the sources. It
  accepted the images with reservations: persistence after installation was
  not proven yet, and some error paths are handled less broadly than the
  report claimed.

![Test bench with the Halo board, USB-serial adapter, Ethernet cable and power lead](photos/PHOTO-11.jpg)

## 10. Installing to flash: the A/B scheme

### How U-Boot picks a bank

Reading the GPL U-Boot source, confirmed against the binary, gives the
following rules:

- `tp_boot_idx` equal to exactly `1` boots `rootfs_1`. Absent, `0` or any
  other value boots `rootfs`.
- A different variable, `boot_idx`, takes priority if it exists. It allows a
  single attempt. The `tp_boot_idx` rule above and the retry below apply only
  when `boot_idx` is absent.
- If `boot_idx` is absent and loading the chosen bank fails inside U-Boot,
  U-Boot tries the other bank once.
- There is **no boot counter**, and U-Boot does not read `0:BOOTCONFIG` on
  this board. A kernel that starts and then crashes is not detected: the same
  bank is tried again at the next power-on.

### The installation (13 November 2026)

The journal records the owner's explicit approval for this step.
 The steps:

1. Boot the WPA2 initramfs from RAM, as in section 9.
2. Copy `sysupgrade.bin` onto it and compare its SHA-256 with the local file.
3. Run `sysupgrade -T` (image test only), which returned success.
4. Check `tp_boot_idx`. It was absent, so the target was `rootfs_1`.
5. Run `sysupgrade -n -v`. The serial log showed `ubi1: attached mtd12 (name
   "rootfs_1")` and then `sysupgrade successful`.
6. Reboot. U-Boot found the bank flag and loaded the OpenWrt kernel. The
   first boot created the persistent overlay, and `factory_data` stayed
   read-only.

After a second reboot, the overlay was found again rather than recreated. The
following was checked:

- `tp_boot_idx=1` and a SquashFS root;
- the U-Boot environment tools in place, and the NAND fix present;
- on the LAN: a DHCP client, no DHCP, DHCPv6 or router-advertisement service,
  and no socket on UDP 67 or 547. `dnsmasq` still answers DNS on port 53;
- two Wi-Fi interfaces in `psk2`, disabled, country DE, with 64-character keys
  (length only), no interface created;
- the first-boot scripts removed after running.

The journal states that the write targeted `rootfs_1`, not the stock bank
`rootfs`. The integrity of `rootfs` was not read back after the installation.

### What the A/B scheme does not protect

- The `rootfs` bank is **writable** under OpenWrt. Keeping the stock firmware
  there depends only on the bank-selection logic.
- The **next ordinary `sysupgrade`** from the installed OpenWrt will target
  `rootfs`, and so **will overwrite the stock copy**.

## 11. Going back to stock, and its limits

Three ways back are documented. **None has been tested.**

1. **U-Boot's recovery page.** Hold the reset button at power-on and upload
   the signed official firmware. The page checks the signature before
   writing (section 7). It runs before Linux, so a broken OpenWrt bank does
   not block it, as long as the bootloader partitions are intact. The address
   of the page is uncertain: the page text names one address and the
   compiled default environment contains another. Neither has been observed
   on the network. In the GPL U-Boot source studied, the
   recovery path checks that the image is compatible, but it contains no
   major or minor version comparison of the kind the Linux updater makes.
   Whether an older signed image would actually be accepted has not been
   tested.
2. **The serial console.** Clearing `tp_boot_idx` selects `rootfs` again,
   **as long as `boot_idx` is absent and that bank still holds the stock
   firmware**. This has not been tested.
3. **The NAND backup.** It is intended for a restore from U-Boot while the
   U-Boot partition is intact. That has never been tried, and the backup
   lacks the spare (OOB) area.

What is **not** guaranteed:

- an automatic return if OpenWrt starts and then crashes (there is no boot
  counter);
- the stock copy after a second OpenWrt upgrade (see above);
- recovery after a power cut while the U-Boot environment is being written.
  Its effect has not been studied on the hardware.

## 12. Current state and limits (13 November 2026)

**Tested on one unit, installed in flash since 13 November 2026.**

| Area | State |
|---|---|
| Boot from flash, A/B switch | Observed, two boots. The stock bank was not the write target; it was not read back afterwards |
| Ethernet, switch, three ports | Observed in RAM. The test link ran at 100 Mbit/s, cause not established (cable or remote port are hypotheses); gigabit on the ports was not shown |
| LEDs | Observed in RAM, checked by eye |
| Reset button | Seen electrically in RAM; on the installed system the software path was traced, but a physical press was not observed |
| Wi-Fi 2.4 / 5 GHz | Observed in RAM, including client association and HE160 on channel 36. On the installed unit, the access points are **disabled**. WPA2 association after installation, long-term stability and throughput are untested |
| MAC addresses | Observed: base, +2, +3 |
| HTTPS for the web interface | Observed after adding a package; not yet in a rebuilt image, persistence after a reboot untested |
| VLAN per SSID (the end goal) | Not tested |

**Known limits.**

- **Board data files.** Their redistribution rights are not established, so
  they are not published. Without them, Wi-Fi does not work, and an image
  rebuilt from this repository alone has no Wi-Fi.
- **5 GHz channels 100 and above.** They are disabled. Channels 36–64 work,
  with 52–64 subject to radar detection. A debug build showed that, with the
  board data file in use, the QCN6122 firmware itself announces only four
  regulatory rules at each start: 2.4 GHz, 5170–5250 MHz, 5250–5330 MHz, and
  a 6 GHz range that the radio cannot use. Setting other country codes did
  not add the upper band. At boot, the stock driver also reports only 8
  channels on 5 GHz. So the stock firmware probably does not use the upper
  band either, but that observation is partial. The other stock
  board-file variants were only compared offline: they differ in a region
  code and in power tables, and none of them was booted. The device tree's
  frequency limit and the driver options were examined in the files and offer
  no override. The effect of the other variants on the hardware remains
  untested.
- **CPU–switch link at 1 Gbit/s.** A 2.5 Gbit/s variant is drafted but not
  applied. It needs both ends set to `2500base-x` and a driver fix that was
  still under review in OpenWrt at the time. It has not been tested on the
  H80X.
- **Ports.** The three ports are all LAN. No WAN port is defined.

- **Going back to stock**: see section 11.
- **Upstream**: nothing has been submitted. Open OpenWrt pull requests touch
  the same code: a common function for `tp_boot_idx` on TP-Link and Mercusys
  boards, and the 2.5 Gbit/s link of the MR80X v2.

## 13. The 2.5 Gbit/s variant

The device tree change is small: set `2500base-x` and 2500 Mbit/s on both the
SoC side and the switch's CPU port. On a related board, a public report
describes changing only one side: most boots then failed to transmit. Even
with both sides changed, an intermittent fault (link up, no traffic) needs a
driver fix that had not been merged. The draft is kept apart from the tested
configuration.

## 14. Incidents, dead ends and lessons

**The DHCP incident (12 November).** The first OpenWrt test image came up
with OpenWrt's default LAN settings: a static address and an active DHCP
server. The unit was plugged into the home network, and that server **gave a
lease to a household device** before it was stopped. The fix has two parts:

- a first-boot script that turns the LAN into a DHCP client and disables the
  DHCP server, DHCPv6 and router advertisements;
- a standing project rule: never plug a test image into a live network
  without that protection, and check `dhcp.lan.ignore=1`.

Since 13 November the script is in the repository and installed by the
integration script. It was checked in RAM and again after installation.
 Lesson: OpenWrt's defaults assume it is the router. On
someone else's network, change the defaults before the first boot.

**Unloading the Wi-Fi driver (12 November).** To read a debug name, an agent
reloaded `ath11k` while the system ran. The Q6 co-processor would not
restart, and Wi-Fi was gone. After an unplanned reboot, the unit was running
the stock firmware from flash: a RAM image does not survive a reboot. That
console gave no shell, and there was no remote power control. To return to
U-Boot, a serial BREAK followed by SysRq `c` (crash) was used: the watchdog
rebooted the unit, with no flash write, and U-Boot could be interrupted again.
The stock SysRq mask allows only crash, power-off and minidump, and power-off
could not have been undone remotely.
 Lesson: put debug options in the image at boot, not in a
running system.

**Leftover debug settings.** The same investigation left debug options in the
shared build tree, and the journal flagged them to be cleaned before any
installation image. The tree was found clean at the next rebuild, and a later
check confirmed that the debug module was absent from the images.

**Gaps found by rebuilding and reviewing.** The rebuild confirmed and fixed
the integration-script gaps. Independent reviews of the code that writes to
flash found the false success in the NAND helper. The missing HTTPS generator
showed up after installation. Only the result of a real NAND write could not
be shown by a RAM test. Lesson: test the artefact you
will install, and review the code paths that write.

**Dead ends.**

- Installing through the stock web page with an MR80X-style image (section 7;
  ruled out by static analysis, not attempted).
- Using an older or a sister-model stock firmware as a stepping stone.

- Installing through U-Boot's recovery page, which needs a signature.

- Unlocking 5 GHz channels 100+ (section 12).
- A `factory.bin` and the `UbiFit` image layout, both dropped from the
  recipe.

**Corrections along the way.** Later analyses corrected several early
conclusions. Some historical project documents still carry the outdated
wording:

- a memory address was first attributed to the QCN6122; it belongs to the
  disabled QCN9000 slot;
- the 5 GHz limit was first blamed on the DE board file; a debug build then
  showed that the radio firmware itself announces the restricted rules
  (section 12);
- the hypothesis that the MR80X install method would work was disproved;
- "guaranteed return to stock" overstated what has been tested.

 This text uses the corrected versions.

Each rebuild produced images under a new name (`-final`, `-fix`, `-wpa2`),
recorded with their size and checksum. Each test can therefore be traced to an
exact file.

## 15. Who did what: AI agents and the human

This project relied heavily on AI agents. According to the project notes, the
owner set this organisation:

- Claude orchestrates and verifies;
- GPT-based agents and Cursor agents carry out delegated tasks;
- a separate model runs counter-checks.

A check by another model does not replace human review.

What the agents did:

- **Offline analysis on copies**: device tree, MAC addresses, Wi-Fi,
  installation, LEDs, disassembly of the stock updater and of U-Boot, older
  firmware, licence research. Each task had a written brief and a report, and
  neither touched the device.
- **Re-verification**: the orchestrating agent re-checked key findings itself,
  for example the updater disassembly and the identity of the stock
  `nvrammanager`.
- **Hardware sessions**: agents drove the serial console and the RAM tests
  through the Linux machine attached to the UART.
- **Independent reviews**: a pre-install counter-check, a targeted review of
  the flash-write path, and an audit of the WPA2 images.
- **This text**, written and checked by agents. The owner will review it
  before publication.

What the human did:

- **Physical access** to the unit. The owner reports opening both cases
  with plastic tools. The records do not identify who performed every other
  physical step (see below).
- **Explicit approval** before any flash write, as the project rules
  require.
- **Decisions**: publication, licence, scope.
- **Owner's notes** from 11–12 November report the first serial dialogue, the
  backup and the stock RAM boot.

The visual LED check and the Wi-Fi client tests with a phone were done on
the hardware. The owner has since described opening both cases. Who wired
the UART and handled the phone is not recorded in the project files.

## 16. How to reproduce

**This is a record of what was done on one unit, not a supported installation
guide.** You may lose your device, its identity data or its warranty. Read
sections 4, 6 and 11 first.

1. **Build.** You need a Linux build host and an OpenWrt tree; the work used
   `main` at `30a23ae451`. Run:

   ```sh
   python3 openwrt/add_h80x.py <openwrt-tree> openwrt/install/ipq5018-h80x-v1.dts <board-files-dir>
   ```

   Then select `mercusys_h80x-v1` in `make menuconfig`, enable the initramfs
   image, and build. **Read the script's output.** If a file or a
   pattern is not found in a newer tree, some steps print a message and
   continue instead of failing; others stop with an error.
   Without board data files, the radios will not start (section 8).
2. **Serial console.** Open the case, identify and **measure** the UART pads,
   connect at the measured voltage, 115200 8N1. Stop U-Boot with `tpl`.

3. **Back up the NAND first**, as in section 6, and keep the backup private:
   it contains your unit's private key.
4. **If the unit is on a network you share**, make sure your image includes
   the LAN protection script before the first boot.
5. **Boot the initramfs from RAM** (section 9) and check everything there:
   partition flags, radios, MAC addresses, LAN behaviour.
6. **Install** from the initramfs with `sysupgrade`, as in section 10, only
   when you accept the risks in section 11.

Useful tools in this repository: `tools/stop_uboot.py`,
`tools/tftp_server.py`, `tools/verify_split.py`, `tools/ubi_extract.py`,
`tools/dtb2dts.py`, `tools/verify_wpa2_images.py`.

The reset switch is marked `SW1` on the board. It is accessible through the
small hole on the rear panel.

![Rear reset access hole between the power connector and Ethernet ports](photos/PHOTO-12a.jpg)

![Reset switch SW1 on the board](photos/PHOTO-12b.jpg)

## 17. Licence and credits

**Licence.** On 13 November 2026 the owner chose the most open licence
possible. The repository is prepared with CC0-1.0 for documentation and
photos, MIT-0 for original code, and the original licence for files derived
from OpenWrt; see [LICENSING.md](LICENSING.md). The owner-supplied photographs
are CC0-1.0, copyright Etienne-T. Final owner review of the export remains
pending.

Files derived from OpenWrt keep their original licence. For example, the
device tree carries `GPL-2.0-or-later OR MIT`. The public
repository is meant to contain no stock firmware, no board data files and no
NAND backup; this will be checked on the final export before publication.

**Credits.**

- The OpenWrt project and the authors of the Mercusys MR80X v2 and TP-Link
  Archer AX55 v1 support, which this port builds on.
- The contributors to the OpenWrt forum thread on the MR80X v2.
- The author of the [DNS Club review](https://club.dns-shop.ru/review/t-280-marshrutizatoryi/85194-obzor-domashnei-wi-fi-mesh-sistemyi-mercusys-halo-h80x-kompaktno/) of the Halo H80X,
  for the additional device photographs.
- `ath11k-bdencoder` from qca-swiss-army-knife, used to check the board data
  container format.
- Mercusys, for publishing the GPL source of the H80X firmware.

The repository is maintained by Etienne-T. Text and code were largely
produced by AI agents under the owner's direction; see the README.
