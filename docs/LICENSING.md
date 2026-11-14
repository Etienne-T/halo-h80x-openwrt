<!-- SPDX-FileCopyrightText: Etienne-T -->
<!-- SPDX-License-Identifier: CC0-1.0 -->

# Licensing and acknowledgements

| Material | SPDX expression |
|---|---|
| Original prose, including the project story | CC0-1.0 |
| Owner-supplied photographs in `docs/photos/` | CC0-1.0 |
| Original Python tools and local safe defaults | MIT-0 |
| OpenWrt-derived integrator and platform/profile fragments | GPL-2.0-only |
| Two DTS files | GPL-2.0-or-later OR MIT |

Official SPDX license texts are in [LICENSES](../LICENSES/). The DTS alternative
MIT license retains its notice requirements. The OpenWrt
[COPYING at the historical base](https://github.com/openwrt/openwrt/blob/30a23ae451602aa8cdaa8532c19855162c3e2de1/COPYING)
uses GPL-2.0-only unless a component carries another license. The integrator
contains substantial derived shell fragments; its Python wrapper does not
make the entire file MIT-0. See [pinned source references](PROVENANCE.md).

Local annotations use `SPDX-FileCopyrightText: Etienne-T`, the pseudonym of
the repository owner. The owner confirmed that the original code, including
the Python tools in `tools/`, the BDF wrapper and the safe-default scripts, was
written by an AI agent (Codex) within this project, under the owner's
direction. This annotation does not replace existing source notices or
identify an AI model as a rights holder. AI assistance is disclosed
in the [README](../README.md).

The platform-case fragment is annotated in `REUSE.toml` because the integrator
requires its case label as the first line. The existing OpenWrt.org NAND notice
is retained as a source acknowledgement in `add_h80x.py`. The absence of another
local notice is not evidence of original authorship.

No license here covers BDFs, vendor firmware, device calibration or private
backups. Those are excluded. The owner-supplied photographs in `docs/photos/`
are CC0-1.0, with copyright attributed to Etienne-T in `REUSE.toml`.
The published files are cropped and masked where needed, and carry no EXIF
or XMP metadata. Third-party photos, figures or code retain their own terms.
