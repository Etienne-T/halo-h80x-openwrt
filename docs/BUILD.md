<!-- SPDX-FileCopyrightText: Etienne-T -->
<!-- SPDX-License-Identifier: CC0-1.0 -->

# Building the historical port

Use a Linux build host with the OpenWrt build prerequisites installed.
No build was performed while preparing this export. This recipe targets the
historical base, not an arbitrary current OpenWrt checkout.

## Revisions

OpenWrt: `30a23ae451602aa8cdaa8532c19855162c3e2de1`.
The following feed HEADs were observed on 13 November 2026. Their clean state
and identity with every earlier build were not established.

| Feed | Revision |
|---|---|
| packages | `66689386bc1f645c5926dcc48dff300fcf1b77aa` |
| luci | `326145c2399c4c07db47ea4dda41f763621ec016` |
| routing | `ea8633da9c461a9bdc62a0323439d31180762e03` |
| telephony | `9bcb6d71db03377ff49ccb099be763add9a5b059` |
| video | `97137d9e4bbf2d5b8fc74b49d2a8641f21855032` |

From a new build directory, obtain the OpenWrt source and pin these revisions:

```sh
git clone https://github.com/openwrt/openwrt.git openwrt-tree
cd openwrt-tree
git checkout --detach 30a23ae451602aa8cdaa8532c19855162c3e2de1
./scripts/feeds update -a
git -C feeds/packages checkout --detach 66689386bc1f645c5926dcc48dff300fcf1b77aa
git -C feeds/luci checkout --detach 326145c2399c4c07db47ea4dda41f763621ec016
git -C feeds/routing checkout --detach ea8633da9c461a9bdc62a0323439d31180762e03
git -C feeds/telephony checkout --detach 9bcb6d71db03377ff49ccb099be763add9a5b059
git -C feeds/video checkout --detach 97137d9e4bbf2d5b8fc74b49d2a8641f21855032
./scripts/feeds update -i
./scripts/feeds install -a
cd ..
```

Set `PORT_SOURCE` to your local copy of this repository. Apply the port using
the installable DTS:

```sh
python3 "$PORT_SOURCE/openwrt/add_h80x.py" openwrt-tree   "$PORT_SOURCE/openwrt/install/ipq5018-h80x-v1.dts"
```

For a private Wi-Fi build only, add the board directory created by the
[historical BDF workflow](WIFI-BDF.md) as the third argument. No BDF is fetched
automatically. The DTS enables radio hardware; omitting BDFs does not turn this
into a validated wired-only upstream profile. Such a profile remains separate
work and must disable the radios and their remote processor explicitly.

Read every message from the script. It can skip missing files or unexpected
anchors without failing the whole operation. Inspect its diff, including
`platform.sh`, `nand.sh` and `uboot-envtools`, before building. It modifies the
shared NAND helper, not just the H80X case. Do not run Python with `-O`, because
the script uses assertions for some checks. Review [known risks](PROVENANCE.md).

In `openwrt-tree`, use `make menuconfig`: choose Qualcomm Atheros ARM,
`qualcommax/ipq50xx`, then Mercusys Halo H80X v1. Enable the initramfs image
(`CONFIG_TARGET_ROOTFS_INITRAMFS=y`). Run `make defconfig`, then
`make -j"$(nproc)"`. The historical full `.config` is not supplied, so this
is a reconstruction recipe, not a claim of bit-for-bit image reproduction.

Expected files under `bin/targets/qualcommax/ipq50xx/`:

- `openwrt-qualcommax-ipq50xx-mercusys_h80x-v1-initramfs-uImage.itb`
- `openwrt-qualcommax-ipq50xx-mercusys_h80x-v1-squashfs-sysupgrade.bin`

The NAND upgrade file is a tar containing `CONTROL`, `kernel` and `root`;
`UbiFit` is not used. Verify the outputs before any hardware operation:

```sh
python3 "$PORT_SOURCE/tools/verify_wpa2_images.py"   . "$PORT_SOURCE/openwrt" image-check
```

This tool needs `unsquashfs` and `zstd` on Linux. It checks embedded defaults
and the error-handling branches, not NAND write success. The current profile
also includes HTTPS dependencies added after the installed WPA2 build.
There is no verified rebuild of these exported sources yet.
