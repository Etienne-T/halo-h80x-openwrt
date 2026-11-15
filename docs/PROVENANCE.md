<!-- SPDX-FileCopyrightText: Etienne-T -->
<!-- SPDX-License-Identifier: CC0-1.0 -->

# Source provenance and open issues

This local port was developed on OpenWrt
`30a23ae451602aa8cdaa8532c19855162c3e2de1`. Historical hardware outcomes below
are reported from private project records dated 12–13 November 2026. Those
records are intentionally not exported. No new hardware test was performed.

## Upstream foundations

- [MR80X v2 DTS](https://github.com/openwrt/openwrt/blob/30a23ae451602aa8cdaa8532c19855162c3e2de1/target/linux/qualcommax/dts/ipq5018-mr80x-v2.dts): declared DTS foundation, switch and NAND profile; H80X RAM and GPIOs differ.
- [AX55 v1 DTS](https://github.com/openwrt/openwrt/blob/30a23ae451602aa8cdaa8532c19855162c3e2de1/target/linux/qualcommax/dts/ipq5018-archer-ax55-v1.dts): 512 MiB, two radios, UBIFS MAC data and dual-bank precedent.
- [AX55 support commit](https://github.com/openwrt/openwrt/commit/8ac63a1c3551fcb3a903ec347e84c1fd1ad6142a): support landed through this commit; PR 24197 was closed without being merged.
- [RE700X support](https://github.com/openwrt/openwrt/commit/a20047f6ee25725a97063af0517aa5c254931a8b): source of the pre-existing factory-data preinit helper; EAP650-Outdoor also informed NAND geometry and the environment group.
- [Device profiles](https://github.com/openwrt/openwrt/blob/30a23ae451602aa8cdaa8532c19855162c3e2de1/target/linux/qualcommax/image/ipq50xx.mk), [network setup](https://github.com/openwrt/openwrt/blob/30a23ae451602aa8cdaa8532c19855162c3e2de1/target/linux/qualcommax/ipq50xx/base-files/etc/board.d/02_network), [caldata](https://github.com/openwrt/openwrt/blob/30a23ae451602aa8cdaa8532c19855162c3e2de1/target/linux/qualcommax/ipq50xx/base-files/etc/hotplug.d/firmware/11-ath11k-caldata), [preinit](https://github.com/openwrt/openwrt/blob/30a23ae451602aa8cdaa8532c19855162c3e2de1/target/linux/qualcommax/ipq50xx/base-files/lib/preinit/09_mount_factory_data), [LED setup](https://github.com/openwrt/openwrt/blob/30a23ae451602aa8cdaa8532c19855162c3e2de1/target/linux/qualcommax/ipq50xx/base-files/etc/board.d/01_leds), and [environment setup](https://github.com/openwrt/openwrt/blob/30a23ae451602aa8cdaa8532c19855162c3e2de1/package/boot/uboot-tools/uboot-envtools/files/qualcommax_ipq50xx): OpenWrt platform code adapted by the integrator.
- [platform.sh](https://github.com/openwrt/openwrt/blob/30a23ae451602aa8cdaa8532c19855162c3e2de1/target/linux/qualcommax/ipq50xx/base-files/lib/upgrade/platform.sh) and [nand.sh](https://github.com/openwrt/openwrt/blob/30a23ae451602aa8cdaa8532c19855162c3e2de1/package/base-files/files/lib/upgrade/nand.sh): upgrade logic adapted locally. The substantial NAND excerpts retain the source notice, `Copyright (C) 2014 OpenWrt.org`.

The current integrator copies the chosen DTS, adds network and MAC handling,
reads separate ART calibration, mounts factory data read-only, installs LEDs
and environment setup, patches A/B upgrades and NAND error propagation, and
copies the two safe-default scripts. The standalone environment reference
contains other upstream boards; it should become a minimal diff for a future
contribution. See [licensing details](LICENSING.md).

## Upgrade risks still requiring review

[OpenWrt PR 26616](https://github.com/openwrt/openwrt/pull/26616), reviewed locally
at head `80ebee625ea90309b8ce9bcdbe1b7c1ea37d6bf2` on 13 November 2026, proposes
handling an invalid environment CRC by preserving a compatible `bootcmd` during
environment creation. The exported historical H80X case still calls
`fw_setenv` directly and does not incorporate that helper. An absent variable
does not prove an invalid CRC. The case also interprets a failed
`fw_printenv -n` like an absent variable, which can misidentify the active bank.
It also derives the active bank from `tp_boot_idx` alone and assumes that
`boot_idx`, which U-Boot reads first, is absent; it does not check this.
Stop on environment read errors; a complete code fix and stub tests remain
future work. The historical first installation does not
validate every environment state or both alternating bank directions.

The NAND patch propagates write command failures and gates bank switching on
success. It performs no post-write volume readback and does not cover power
loss. A future helper integration must preserve failure propagation and the
intentional deletion of `tp_boot_idx` for `rootfs`.

[PR 26597](https://github.com/openwrt/openwrt/pull/26597) and
[PR 25153](https://github.com/openwrt/openwrt/pull/25153) propose different
UNIPHY/switch ordering changes relevant to a possible 2.5 Gbit/s CPU link.
Neither is integrated or tested here. Do not stack them without review.
Newer base-files refactors can invalidate the integrator's textual anchors.

The stock web recovery path was analysed but never restored end to end.
No blanket stock parity, recovery guarantee, long-term stability or tested
2.5 Gbit/s support is claimed. Hardware, HTTPS and flash validation need
separate, explicitly authorized sessions.
