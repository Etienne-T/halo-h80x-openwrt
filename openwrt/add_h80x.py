#!/usr/bin/env python3
# SPDX-FileCopyrightText: Etienne-T
# SPDX-License-Identifier: GPL-2.0-only
"""Apply the H80X port to the historical OpenWrt base; see docs/BUILD.md.

Usage: python3 openwrt/add_h80x.py OPENWRT_TREE DTS [PRIVATE_BOARD_DIRECTORY]
The selected DTS controls partition protection. The optional third argument
copies locally supplied board-2.bin and board.bin into the private image.
Missing anchors can leave a partially modified tree: inspect all output.
"""
# Portions adapted from OpenWrt nand.sh: Copyright (C) 2014 OpenWrt.org
# See docs/PROVENANCE.md for pinned source references.
import pathlib
import re
import shutil
import sys

root = pathlib.Path(sys.argv[1]).expanduser()
dts_src = pathlib.Path(sys.argv[2]).expanduser()
boards = pathlib.Path(sys.argv[3]).expanduser() if len(sys.argv) > 3 else None
q = root / "target/linux/qualcommax"

# 1) DTS
shutil.copy(dts_src, q / "dts/ipq5018-h80x-v1.dts")
print("DTS copie")

# 2) Définition de l'appareil (remplacée à chaque passage)
DEVICE = """
define Device/mercusys_h80x-v1
	$(call Device/FitImageLzma)
	DEVICE_VENDOR := MERCUSYS
	DEVICE_MODEL := Halo H80X
	DEVICE_VARIANT := v1
	SOC := ipq5018
	DEVICE_DTS_CONFIG := config@mp03.3
	BLOCKSIZE := 128k
	PAGESIZE := 2048
	NAND_SIZE := 128m
	KERNEL_IN_UBI := 1
	IMAGE_SIZE := 43008k
	DEVICE_PACKAGES := kmod-dsa-rtl8365mb ath11k-firmware-ipq5018-qcn6122 libustream-mbedtls px5g-mbedtls
endef
TARGET_DEVICES += mercusys_h80x-v1
"""
mk = q / "image/ipq50xx.mk"
text = mk.read_text()
text = re.sub(r"\ndefine Device/mercusys_h80x-v1\n.*?endef\nTARGET_DEVICES \+= mercusys_h80x-v1\n",
              "", text, flags=re.S)
mk.write_text(text.rstrip("\n") + "\n" + DEVICE)
print("ipq50xx.mk : appareil (re)defini")

# 3) Réseau : les 3 ports dans br-lan (pas de WAN dédié pour le test)
net = q / "ipq50xx/base-files/etc/board.d/02_network"
text = net.read_text()
if "mercusys,h80x-v1" not in text:
    # Nouveau cas inséré juste après le premier 'case $board in' qui précède
    # l'entrée du MR80X (et non au milieu d'une liste « a|b|c) »).
    anchor = text.index("\tmercusys,mr80x-v2|\\\n")
    case_line = "\tcase $board in\n"
    pos = text.rindex(case_line, 0, anchor) + len(case_line)
    text = (text[:pos] + "\tmercusys,h80x-v1)\n\t\tucidef_set_interface_lan \"lan1 lan2 lan3\"\n\t\t;;\n"
            + text[pos:])
    net.write_text(text)
    print("02_network : appareil ajoute")

# 4) Calibration Wi-Fi depuis 0:ART (offsets du script d'origine read_caldata_to_fs.sh)
cal = q / "ipq50xx/base-files/etc/hotplug.d/firmware/11-ath11k-caldata"
text = cal.read_text()
if "mercusys,h80x-v1" not in text:
    for fw, off in (("ath11k/IPQ5018/hw1.0/cal-ahb-c000000.wifi.bin", "0x1000"),
                    ("ath11k/QCN6122/hw1.0/cal-ahb-b00a040.wifi.bin", "0x26800")):
        head = f'"{fw}")\n\tcase "$board" in\n'
        assert head in text, f"section {fw} introuvable"
        text = text.replace(head, head + f'\tmercusys,h80x-v1)\n\t\tcaldata_extract "0:ART" {off} 0x20000\n\t\t;;\n', 1)
    cal.write_text(text)
    print("11-ath11k-caldata : appareil ajoute")

# 4b) MAC des radios depuis factory_data/default-mac (valeurs d'origine :
#     2,4 GHz = base + 2, 5 GHz = base + 3 ; wifi_init_wifi_mac du firmware stock)
text = cal.read_text()
for off, add in (("0x1000", 2), ("0x26800", 3)):
    old = f'\tmercusys,h80x-v1)\n\t\tcaldata_extract "0:ART" {off} 0x20000\n\t\t;;\n'
    new = (f'\tmercusys,h80x-v1)\n\t\tcaldata_extract "0:ART" {off} 0x20000\n'
           f'\t\tlabel_mac=$(get_mac_binary "/tmp/factory_data/default-mac" 0)\n'
           f'\t\t[ -n "$label_mac" ] && ath11k_patch_mac "$(macaddr_add "$label_mac" {add})" 0\n'
           f'\t\tath11k_set_macflag\n\t\t;;\n')
    text = text.replace(old, new, 1)
cal.write_text(text)
print("11-ath11k-caldata : MAC radios (base+2 / base+3)")

# 4c) MAC LAN / conduit depuis factory_data (fonction ipq50xx_setup_macs)
text = net.read_text()
if "# MAC d'usine : 6 octets bruts dans factory_data" not in text:
    fn = text.index("ipq50xx_setup_macs()")
    case_line = "\tcase $board in\n"
    pos = text.index(case_line, fn) + len(case_line)
    text = (text[:pos]
            + "\tmercusys,h80x-v1)\n"
              "\t\t# MAC d'usine : 6 octets bruts dans factory_data/default-mac,\n"
              "\t\t# monté en lecture seule au preinit (09_mount_factory_data)\n"
              "\t\tlabel_mac=$(get_mac_binary \"/tmp/factory_data/default-mac\" 0)\n"
              "\t\t[ -n \"$label_mac\" ] || return\n"
              "\t\tucidef_set_interface_macaddr \"lan\" \"$label_mac\"\n"
              "\t\tucidef_set_label_macaddr \"$label_mac\"\n"
              "\t\tucidef_set_network_device_mac \"eth0\" \"$label_mac\"\n"
              "\t\t;;\n"
            + text[pos:])
    net.write_text(text)
    print("02_network : MAC H80X ajoutee")

# 4d) Montage en lecture seule de factory_data au preinit
pre = q / "ipq50xx/base-files/lib/preinit/09_mount_factory_data"
text = pre.read_text()
if "mercusys,h80x-v1" not in text:
    func = ('preinit_mount_factory_data_ro() {\n'
            '\t# ubiattach est dans /usr/sbin, absent du PATH du preinit\n'
            '\tlocal PATH="/usr/sbin:/usr/bin:$PATH"\n'
            '\tlocal mtd_num ubi_num\n\n'
            '\tmtd_num=$(find_mtd_index factory_data)\n'
            '\t[ -n "$mtd_num" ] || return\n'
            '\t# partition read-only dans le DTS : UBI s\'attache en lecture seule\n'
            '\tubi_num=$(ubiattach -m "$mtd_num" 2>/dev/null | \\\n'
            '\t\tsed -n \'s/.*device number \\([0-9]*\\).*/\\1/p\')\n'
            '\t[ -n "$ubi_num" ] || return\n'
            '\tmkdir -p /tmp/factory_data\n'
            '\tmount -t ubifs -o ro,noatime "ubi${ubi_num}:ubi_factory_data" \\\n'
            '\t\t/tmp/factory_data 2>/dev/null\n'
            '}\n\n')
    text = text.replace("preinit_mount_factory_data() {", func + "preinit_mount_factory_data() {", 1)
    text = text.replace("\tcase $(board_name) in\n",
                        "\tcase $(board_name) in\n\tmercusys,h80x-v1)\n\t\tpreinit_mount_factory_data_ro\n\t\t;;\n", 1)
    pre.write_text(text)
    print("09_mount_factory_data : appareil ajoute")

# 4e) LED des ports (lien + activité)
leds = q / "ipq50xx/base-files/etc/board.d/01_leds"
text = leds.read_text()
if "mercusys,h80x-v1" not in text:
    block = "mercusys,h80x-v1)\n" + "".join(
        f'\tucidef_set_led_netdev "lan{i}" "LAN{i}" "green:lan-{i}" "lan{i}" "tx rx link"\n'
        for i in (1, 2, 3)) + "\t;;\n"
    text = text.replace("mercusys,mr80x-v2)\n", block + "mercusys,mr80x-v2)\n", 1)
    leds.write_text(text)
    print("01_leds : appareil ajoute")

# 4f) uboot-envtools : fw_printenv/fw_setenv (tp_boot_idx) doit lire 0:APPSBLENV.
#     Même valeurs que /etc/fw_env.config d'origine (mtd7, 0x0, 0x40000, 0x20000).
env = root / "package/boot/uboot-tools/uboot-envtools/files/qualcommax_ipq50xx"
if not env.exists():  # ancien emplacement selon la version de l'arbre
    alt = root / "package/boot/uboot-envtools/files/qualcommax_ipq50xx"
    env = alt if alt.exists() else env
if env.exists():
    text = env.read_text()
    if "mercusys,h80x-v1" not in text:
        # Rejoint le groupe "0:APPSBLENV" majuscules / 0x40000 (archer-ax55-v1)
        anchor = "tplink,archer-ax55-v1|\\\n"
        assert anchor in text, "groupe archer-ax55-v1 introuvable dans uboot-envtools"
        text = text.replace(anchor, "mercusys,h80x-v1|\\\n" + anchor, 1)
        env.write_text(text)
        print("uboot-envtools : appareil ajoute")
else:
    print("uboot-envtools : fichier introuvable, etape ignoree")

# 4g) sysupgrade A/B : cas mercusys,h80x-v1 de platform.sh (banque inactive +
#     tp_boot_idx). Source unique : install/platform.sh-h80x-case.txt. Sans ce
#     cas, platform_do_upgrade tombe sur default_do_upgrade (pas d'A/B).
case_src = pathlib.Path(__file__).resolve().parent / "install/platform.sh-h80x-case.txt"
plat = q / "ipq50xx/base-files/lib/upgrade/platform.sh"
if case_src.exists():
    block = case_src.read_text()
    assert block.startswith("\tmercusys,h80x-v1)\n") and block.endswith("\n\t\t;;\n"), \
        "platform.sh-h80x-case.txt : format inattendu"
    text = plat.read_text()
    # Retire une version précédente du cas (fin = première ligne « \t\t;; » seule)
    text = re.sub(r"\tmercusys,h80x-v1\)\n.*?\n\t\t;;\n", "", text, count=1, flags=re.S)
    anchor = "\tmercusys,mr80x-v2)\n"
    assert text.count(anchor) == 1, "cas mercusys,mr80x-v2 introuvable dans platform.sh"
    text = text.replace(anchor, block + anchor, 1)
    plat.write_text(text)
    print("platform.sh : cas A/B (re)pose")
else:
    print(f"platform.sh : {case_src} introuvable, etape ignoree")

# 4h) nand.sh (helper commun upstream) : propager le statut des ecritures de
#     volumes. Sans cela, nand_upgrade_tar fait un `return 0` inconditionnel et
#     le cas H80X bascule tp_boot_idx apres une ecriture echouee. On ajoute
#     aussi `exit 1` a nand_do_upgrade_failed. Idempotent.
nand = root / "package/base-files/files/lib/upgrade/nand.sh"
_NAND_OLD1 = (
    '\t\t\tdd if=/dev/zero bs=4096 count=1 2> /dev/null | \\\n'
    '\t\t\t\tmtd write - "$CI_KERNPART"\n'
)
_NAND_NEW1 = (
    '\t\t\tdd if=/dev/zero bs=4096 count=1 2> /dev/null | \\\n'
    '\t\t\t\tmtd write - "$CI_KERNPART" || return 1\n'
)
_NAND_OLD2 = (
    '\tif [ "$rootfs_length" ]; then\n'
    '\t\tlocal ubidev="$( nand_find_ubi "${CI_ROOT_UBIPART:-$CI_UBIPART}" )"\n'
    '\t\tlocal root_ubivol="$( nand_find_volume $ubidev "$CI_ROOTPART" )"\n'
    '\t\t$cmd < "$tar_file" | tar xOf - "$board_dir/root" | \\\n'
    '\t\t\tubiupdatevol /dev/$root_ubivol -s "$rootfs_length" -\n'
    '\tfi\n'
    '\tif [ "$kernel_length" ]; then\n'
    '\t\tif [ "$kernel_mtd" ]; then\n'
    '\t\t\tif [ "$jffs2_markers" = 1 ]; then\n'
    '\t\t\t\tflash_erase -j "/dev/mtd${kernel_mtd}" 0 0\n'
    '\t\t\t\t$cmd < "$tar_file" | tar xOf - "$board_dir/kernel" | \\\n'
    '\t\t\t\t\tnandwrite "/dev/mtd${kernel_mtd}" -\n'
    '\t\t\telse\n'
    '\t\t\t\t$cmd < "$tar_file" | tar xOf - "$board_dir/kernel" | \\\n'
    '\t\t\t\t\tmtd write - "$CI_KERNPART"\n'
    '\t\t\tfi\n'
    '\t\telse\n'
    '\t\t\tlocal ubidev="$( nand_find_ubi "${CI_KERN_UBIPART:-$CI_UBIPART}" )"\n'
    '\t\t\tlocal kern_ubivol="$( nand_find_volume $ubidev "$CI_KERNPART" )"\n'
    '\t\t\t$cmd < "$tar_file" | tar xOf - "$board_dir/kernel" | \\\n'
    '\t\t\t\tubiupdatevol /dev/$kern_ubivol -s "$kernel_length" -\n'
    '\t\tfi\n'
    '\tfi\n'
    '\n'
    '\treturn 0\n'
    '}\n'
)
_NAND_NEW2 = (
    '\tlocal rc=0\n'
    '\tset -o pipefail\n'
    '\tif [ "$rootfs_length" ]; then\n'
    '\t\tlocal ubidev="$( nand_find_ubi "${CI_ROOT_UBIPART:-$CI_UBIPART}" )"\n'
    '\t\tlocal root_ubivol="$( nand_find_volume $ubidev "$CI_ROOTPART" )"\n'
    '\t\tif [ -z "$root_ubivol" ]; then\n'
    '\t\t\techo "cannot find rootfs volume"\n'
    '\t\t\trc=1\n'
    '\t\telse\n'
    '\t\t\t$cmd < "$tar_file" | tar xOf - "$board_dir/root" | \\\n'
    '\t\t\t\tubiupdatevol /dev/$root_ubivol -s "$rootfs_length" - || rc=$?\n'
    '\t\tfi\n'
    '\tfi\n'
    '\tif [ "$rc" -eq 0 ] && [ "$kernel_length" ]; then\n'
    '\t\tif [ "$kernel_mtd" ]; then\n'
    '\t\t\tif [ "$jffs2_markers" = 1 ]; then\n'
    '\t\t\t\tflash_erase -j "/dev/mtd${kernel_mtd}" 0 0 || rc=$?\n'
    '\t\t\t\tif [ "$rc" -eq 0 ]; then\n'
    '\t\t\t\t\t$cmd < "$tar_file" | tar xOf - "$board_dir/kernel" | \\\n'
    '\t\t\t\t\t\tnandwrite "/dev/mtd${kernel_mtd}" - || rc=$?\n'
    '\t\t\t\tfi\n'
    '\t\t\telse\n'
    '\t\t\t\t$cmd < "$tar_file" | tar xOf - "$board_dir/kernel" | \\\n'
    '\t\t\t\t\tmtd write - "$CI_KERNPART" || rc=$?\n'
    '\t\t\tfi\n'
    '\t\telse\n'
    '\t\t\tlocal ubidev="$( nand_find_ubi "${CI_KERN_UBIPART:-$CI_UBIPART}" )"\n'
    '\t\t\tlocal kern_ubivol="$( nand_find_volume $ubidev "$CI_KERNPART" )"\n'
    '\t\t\tif [ -z "$kern_ubivol" ]; then\n'
    '\t\t\t\techo "cannot find kernel volume"\n'
    '\t\t\t\trc=1\n'
    '\t\t\telse\n'
    '\t\t\t\t$cmd < "$tar_file" | tar xOf - "$board_dir/kernel" | \\\n'
    '\t\t\t\t\tubiupdatevol /dev/$kern_ubivol -s "$kernel_length" - || rc=$?\n'
    '\t\t\tfi\n'
    '\t\tfi\n'
    '\tfi\n'
    '\tset +o pipefail\n'
    '\treturn "$rc"\n'
    '}\n'
)
_NAND_OLD3 = (
    '\techo "sysupgrade failed"\n'
    '\t# Should we reboot or bring up some failsafe mode instead?\n'
    '\tumount -a\n'
    '\treboot -f\n'
    '}\n'
)
_NAND_NEW3 = (
    '\techo "sysupgrade failed"\n'
    '\t# Should we reboot or bring up some failsafe mode instead?\n'
    '\tumount -a\n'
    '\treboot -f\n'
    '\texit 1\n'
    '}\n'
)
if nand.exists():
    ntext = nand.read_text()
    if "\tlocal rc=0\n\tset -o pipefail\n" in ntext:
        print("nand.sh : deja patche")
    else:
        ok = True
        for old, new in ((_NAND_OLD1, _NAND_NEW1), (_NAND_OLD2, _NAND_NEW2), (_NAND_OLD3, _NAND_NEW3)):
            if ntext.count(old) != 1:
                ok = False
                break
            ntext = ntext.replace(old, new, 1)
        if ok:
            nand.write_text(ntext)
            print("nand.sh : statut des ecritures propage")
        else:
            print("nand.sh : motif upstream inattendu, etape ignoree (verifier manuellement)")
else:
    print("nand.sh : fichier introuvable, etape ignoree")

# 4i) Configuration sure du premier demarrage, source versionnable unique.
# boot genere wireless avant uci-defaults ; le script Wi-Fi attend aussi les
# deux sections par defaut. Ne jamais fournir de cle dans l'image.
defaults_src = pathlib.Path(__file__).resolve().parent / "install/uci-defaults"
defaults_dst = root / "files/etc/uci-defaults"
defaults_dst.mkdir(parents=True, exist_ok=True)
for name in ("99-h80x-test-lan", "99-h80x-wifi-safe"):
    shutil.copyfile(defaults_src / name, defaults_dst / name)
    (defaults_dst / name).chmod(0o755)
print("uci-defaults : LAN sans DHCP/RA et Wi-Fi WPA2 desactive copies")

# 5) Fichiers de carte (BDF d'origine, variante DE) dans l'image via files/
if boards:
    for chip in ("IPQ5018", "QCN6122"):
        dst = root / f"files/lib/firmware/ath11k/{chip}/hw1.0"
        dst.mkdir(parents=True, exist_ok=True)
        for f in ("board-2.bin", "board.bin"):
            shutil.copy(boards / chip / "hw1.0" / f, dst / f)
    print("board-2.bin / board.bin copies dans files/")
