<!-- SPDX-FileCopyrightText: Etienne-T -->
<!-- SPDX-License-Identifier: CC0-1.0 -->

# UART installation and recovery limits

This describes the historical route used on one unit on 13 November 2026.
The public export has not been rebuilt or installed. Do not apply it to an
unidentified revision. Board labels now document the UART pad order in
[HARDWARE.md](HARDWARE.md#uart-photographs-and-voltage-limits). The exact logic
voltage and complete stock restoration remain unverified. No recovery method is guaranteed.

## Preconditions

1. Identify the unit and preserve a verified private device backup before
   installation. Never upload device dumps or factory data. Backup acquisition
   and restore validation are outside this public procedure.
2. Establish safe UART wiring first. The photographed FTDI FT232RNL adapter
   has its voltage jumper set to `1V8`. On the first unit, `TX` measured about
   1.8 V and the `VCC` pad 3.3 V; 3.3 V logic was not validated. Do not connect
   the `VCC` pad or adapter VCC. Use 115200 8N1, common ground and crossed TX/RX
   only after checking the pad identities and measuring the voltage on your
   unit. See the photographs in [HARDWARE.md](HARDWARE.md#uart-photographs-and-voltage-limits).
3. Build and inspect both images as described in [BUILD.md](BUILD.md). Keep the
   bootloader and sensitive partitions protected. Use an isolated test network.
4. Configure a TFTP server for the initramfs image. The observed loader requires
   replies from UDP port 69 and option acknowledgement. The provided
   `tools/tftp_server.py` supports this. Limit host firewall access to the test
   network, and stop the server afterwards. It has no authentication.

## Boot in RAM

1. Interrupt autoboot by sending `tpl` during its one-second window.
   `tools/stop_uboot.py tpl` can assist; its default device is `/dev/ttyUSB0` and
   it needs Python `pyserial`. Inspect and adapt the serial device locally.
2. At U-Boot, use temporary variables only. Set `autoload` to `no`, obtain a
   test-network lease with `dhcp`, then set `serverip` to your TFTP host address.
   Do not use `saveenv` for this RAM test. No example home-network address is
   required.
3. Load the locally built initramfs at the address used in the historical test:

   ```text
   tftpboot 0x46000000 openwrt-qualcommax-ipq50xx-mercusys_h80x-v1-initramfs-uImage.itb
   crc32 0x46000000 ${filesize}
   setenv bootargs console=ttyMSM0,115200n8 coherent_pool=2M
   bootm 0x46000000#config@mp03.3
   ```

   Compare the transferred size and CRC32 with your own local file before
   `bootm`. Historical session CRCs are deliberately omitted. Do not reuse the
   address for a larger image without reviewing the RAM layout.
4. Verify the board identity, partition protections, switch and both radios if
   private BDFs were supplied. Confirm `dhcp.lan.ignore=1`, DHCPv6 and RA disabled,
   LAN DHCP client mode, `psk2` on every wireless interface and `disabled=1`.
   Verify no UDP 67/547 server sockets and no active AP. Do not print the keys.

## Install into the inactive bank

Stop if the bank currently running cannot be identified independently.
U-Boot reads a separate variable, `boot_idx`, first: if it exists, it takes
priority over `tp_boot_idx`. The rules below and the exported upgrade case
assume that `boot_idx` is absent. Stop if its absence is not established.
With `boot_idx` absent, `tp_boot_idx` equal to the string `1` selects
`rootfs_1`; other values or an absent variable select `rootfs`. A `fw_printenv`
error is not proof of absence.
Check the environment configuration and CRC before considering a flash write.
The exported case does not yet handle every failure; see [PROVENANCE.md](PROVENANCE.md).

The initial installation was performed while stock was selected in `rootfs`.
The upgrade case therefore targeted `rootfs_1`. It writes the inactive bank
and changes `tp_boot_idx` only after the NAND helper reports success.
It clears the variable when targeting `rootfs`. This is not an automatic
rollback mechanism. Do not request a current-bank upgrade for this route.

1. Copy your verified sysupgrade file to the running initramfs as
   `/tmp/h80x-sysupgrade.bin`, over your isolated network. Compare its SHA-256
   with the local build. Confirm that sufficient RAM is available.
2. Inspect `fw_printenv`, `/etc/fw_env.config`, the upgrade case and the patched
   NAND helper. Confirm that `boot_idx` is absent, that stock remains in
   `rootfs` and that the intended first-install target is `rootfs_1`. Stop on
   any discrepancy.
3. Run `sysupgrade -T /tmp/h80x-sysupgrade.bin` and require a successful result.
   This check alone does not prove safe partition selection or valid BDFs.
4. Only after the owner explicitly authorizes the reviewed flash operation,
   run `sysupgrade -n -v /tmp/h80x-sysupgrade.bin`. This erases configuration in
   the target bank. Do not interrupt power or overwrite bootloader partitions.
5. Observe the serial log and verify the boot bank, persistent overlay,
   read-only factory data and network defaults after boot and another reboot.
   The historical installation passed these checks; future results must be
   checked separately. Radio associations after flash remain unverified.

A later inactive-bank upgrade from `rootfs_1` targets `rootfs` and can overwrite
the preserved stock system. Both alternating directions and power-failure
cases have not been validated. The helper propagates command failures but
does not read back written volumes.

## Returning to stock

While intact, the stock first bank is a potential return route. Selecting it
requires a separately reviewed environment change and assumes that `boot_idx`
is absent; it was not tested end to end. No automatic boot counter or crash-triggered bank fallback was found.

Bootloader analysis reports a web recovery service entered with the reset
button (GPIO 33) before Linux. It checks the RSA signature and accepts only a
compatible official signed image. The exact host address, timing and a full
restore sequence were not verified. This document therefore gives no guessed
recovery URL or guaranteed rescue command. Keep a compatible signed vendor
image privately available and preserve the bootloader. A broken bootloader,
power loss or overwritten factory data can defeat the recovery route.
