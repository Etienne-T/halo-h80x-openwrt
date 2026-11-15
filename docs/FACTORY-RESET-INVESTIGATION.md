<!-- SPDX-FileCopyrightText: Etienne-T -->
<!-- SPDX-License-Identifier: CC0-1.0 -->

# Factory-reset investigation: no installation without UART demonstrated

## Scope and evidence

On 14–15 November 2026, the owner investigated whether a factory-reset Halo
H80X could be accessed and installed through software alone, without opening
the case. A third, unopened unit was used for the network tests; it advertised
stock firmware 1.1.3 Build 20240326 Rel. 15953. The owner's report also records
two units already installed through UART. The earlier sections of the
[project story](STORY.md) describe the original, single-unit work.

This note summarises the owner's private report, `BILAN.md`, supplied on
15 November. Its results were not independently reproduced when this note
was prepared. Packet captures, firmware extractions and application code
were not reanalysed for this documentation update. No system session,
authorised-key installation or firmware-image write resulted from the
reported access attempts. No installation without UART was demonstrated.

## Factory reset is not bootloader recovery

The tested factory setup state exposed an open setup Wi-Fi network, DHCP
and discovery services. Internet could be relayed when the WAN was connected.
The web interface remained session-protected. A reset to this state did not
provide a shell or authorise unsigned firmware.

This is distinct from the U-Boot recovery page entered at power-on with the
reset button. The earlier static analysis of that page found vendor-signature
verification; these later setup tests did not establish a bypass of it.

## Investigated paths and reported outcomes

| Path | Outcome and limit |
|---|---|
| TDP discovery, UDP 20002/20004 | Replies and descriptive device information were obtained. Decoding discovery data did not produce a login. |
| Dropbear, TCP 20001 | An adapted client completed key exchange with the short RSA host key. Group-key authentication, the application fallback password with the tested accounts, and a limited set of common root passwords were rejected. No shell opened. |
| TMP pairing commands | Static analysis placed the full command service on TCP 20002 bound to loopback, behind the SSH tunnel. The network-facing UDP discovery path did not relay the full command table. |
| TDDP, UDP 1040 | The tested group-writing command was refused. The report attributes the refusal to a production-mode requirement, distinct from ordinary factory setup. |
| Web setup and country parameter | The inspected settings and upgrade handlers required an administration session. The country-parameter injection route was not found in the examined Halo versions, including 1.0.0. |
| Older firmware | The report's static analysis indicates that manual 1.1.3-to-1.1.0 upload does not compare version numbers at the web-controller layer, unlike group synchronisation. It still requires a web session and does not establish a signature bypass or a tested downgrade installation. |
| Bluetooth | The inspected Halo setup screen in Mercusys Android 2.4.921 did not call the Bluetooth pairing path used by other products. A scan did not reveal a usable pairing route. |

According to the firmware comparison in the report, the root hash, account
file, Dropbear binary and relevant Dropbear configuration were unchanged
between the examined 1.1.0 and 1.1.3 files. The inspected cloud-account path
did not provide a root credential. These file-level findings do not establish
the effective credentials of every device or every possible configuration.

## What the radio captures show

The first two captures had material limitations: one adapter could not decode
the required unicast traffic; another capture used unsuitable monitor flags.
The corrected third capture showed discovery exchanges and readable unicast
responses. Analysis classified 150 discovery packets as 147 repeated phone
requests and three device announcements. No local TCP session to port 20001
or 22 was observed while the application completed setup.

This observation supports the conclusion that no local SSH login was visible
in that capture. It does not prove that none occurred outside the captured
traffic or that no other setup path exists. A WAN/cloud continuation is the
report's interpretation; its exchanges were not captured or decoded here.

## Remaining questions

The report leaves WAN-side management, exhaustive first-run web-form checks,
an operator DHCP-option path and detailed review of a newly seen TDDP
model-name command unresolved. They are research questions, not demonstrated
installation methods. A server host key identifies the server; possession
of it does not by itself grant client authentication.

The result is therefore limited and useful: factory setup did not unlock
the tested paths. UART, a RAM boot and an authorised sysupgrade remain the
installation route demonstrated in this project. This is not a proof that
every software-only route is impossible.

No passwords, hashes, private keys, device identifiers, local addresses,
setup SSIDs or raw captures from the private investigation are included here.
