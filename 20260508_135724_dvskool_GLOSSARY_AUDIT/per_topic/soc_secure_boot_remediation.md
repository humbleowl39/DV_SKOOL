# Remediation — soc_secure_boot

- auto-keep (added): 13
- auto-drop: 15
- manual-review: 101

## Auto-keep (added to abbr + glossary stub)

| Term | Freq | Full name (extracted) |
|---|---|---|
| **ROM** | 29 | RoT |
| **JTAG** | 28 | Level 2/3 |
| **PUF** | 14 | Physically Unclonable Function |
| **TOCTOU** | 13 | Time-of-Check-to-Time-of-Use |
| **EL1** | 11 | Secure OS |
| **EL3** | 11 | Secure Monitor |
| **DSA** | 10 | Dilithium |
| **PQC** | 10 | ML-DSA-65 |
| **RPMB** | 10 | Replay Protected Memory Block |
| **FIP** | 9 | Firmware Image Package |
| **PCR** | 7 | Platform Configuration Register |
| **BL31** | 6 | Monitor |
| **BL33** | 5 | U-Boot |

## Auto-drop

| Term | Freq | Reason |
|---|---|---|
| DV | 26 | in shared abbr |
| UVM | 22 | in shared abbr |
| DRAM | 18 | in shared abbr |
| SW | 17 | in shared abbr |
| RAL | 5 | in shared abbr |
| DMA | 3 | in shared abbr |
| ID | 3 | in shared abbr |
| CRC | 2 | in shared abbr |
| DUT | 2 | in shared abbr |
| PASS | 2 | english word |
| CPU | 1 | in shared abbr |
| FAIL | 1 | english word |
| IO | 1 | in shared abbr |
| IP | 1 | in shared abbr |
| TB | 1 | in shared abbr |

## Manual-review (need user decision)

| Term | Freq | Reason |
|---|---|---|
| FW | 25 | freq=25 len=2 |
| DL | 9 | freq=9 len=2 |
| ML | 8 | freq=8 len=2 |
| NS | 8 | freq=8 len=2 |
| KB | 5 | freq=5 len=2 |
| BL32 | 4 | freq=4 len=4 |
| EM | 4 | freq=4 len=2 |
| FIB | 4 | freq=4 len=3 |
| PHY | 4 | freq=4 len=3 |
| PVT | 4 | freq=4 len=3 |
| RB | 4 | freq=4 len=2 |
| DICE | 3 | freq=3 len=4 |
| FIPS | 3 | freq=3 len=4 |
| HMAC | 3 | freq=3 len=4 |
| MB | 3 | freq=3 len=2 |
| QSPI | 3 | freq=3 len=4 |
| SCSI | 3 | freq=3 len=4 |
| SPI | 3 | freq=3 len=3 |
| SV | 3 | freq=3 len=2 |
| TAP | 3 | freq=3 len=3 |
| TF | 3 | freq=3 len=2 |
| UUID | 3 | freq=3 len=4 |
| BL | 2 | freq=2 len=2 |
| BSI | 2 | freq=2 len=3 |
| CDI | 2 | freq=2 len=3 |
| CDR | 2 | freq=2 len=3 |
| CMOS | 2 | freq=2 len=4 |
| CRYSTALS | 2 | freq=2 len=8 |
| DDR4 | 2 | freq=2 len=4 |
| DDR5 | 2 | freq=2 len=4 |
| DPU | 2 | freq=2 len=3 |
| KEM | 2 | freq=2 len=3 |
| LPDDR4 | 2 | freq=2 len=6 |
| MCU | 2 | freq=2 len=3 |
| MMC | 2 | freq=2 len=3 |
| NAND | 2 | freq=2 len=4 |
| NSA | 2 | freq=2 len=3 |
| OP | 2 | freq=2 len=2 |
| SD | 2 | freq=2 len=2 |
| SPHINCS | 2 | freq=2 len=7 |
| TAT | 2 | freq=2 len=3 |
| VIP | 2 | freq=2 len=3 |
| AES | 1 | freq=1 len=3 |
| AMBA | 1 | freq=1 len=4 |
| AP | 1 | freq=1 len=2 |
| ASLR | 1 | freq=1 len=4 |
| AVB | 1 | freq=1 len=3 |
| BL3 | 1 | freq=1 len=3 |
| CG | 1 | freq=1 len=2 |
| CG1 | 1 | freq=1 len=3 |
| CG2 | 1 | freq=1 len=3 |
| CG3 | 1 | freq=1 len=3 |
| CG4 | 1 | freq=1 len=3 |
| CG5 | 1 | freq=1 len=3 |
| CMD0 | 1 | freq=1 len=4 |
| DPA | 1 | freq=1 len=3 |
| EEPROM | 1 | freq=1 len=6 |
| EMA | 1 | freq=1 len=3 |
| EN | 1 | freq=1 len=2 |
| F1 | 1 | freq=1 len=2 |
| FROST | 1 | freq=1 len=5 |
| GB | 1 | freq=1 len=2 |
| GPIO | 1 | freq=1 len=4 |
| IC | 1 | freq=1 len=2 |
| IDCODE | 1 | freq=1 len=6 |
| JSON | 1 | freq=1 len=4 |
| LPDDR5 | 1 | freq=1 len=6 |
| LU | 1 | freq=1 len=2 |
| LUN | 1 | freq=1 len=3 |
| MAC | 1 | freq=1 len=3 |
| NXP | 1 | freq=1 len=3 |
| OCTEON | 1 | freq=1 len=6 |
| PC | 1 | freq=1 len=2 |
| PCB | 1 | freq=1 len=3 |
| PK | 1 | freq=1 len=2 |
| PKI | 1 | freq=1 len=3 |
| POR | 1 | freq=1 len=3 |
| PSA | 1 | freq=1 len=3 |
| RAM | 1 | freq=1 len=3 |
| RNG | 1 | freq=1 len=3 |
| S32G | 1 | freq=1 len=4 |
| SK | 1 | freq=1 len=2 |
| SMC | 1 | freq=1 len=3 |
| SPA | 1 | freq=1 len=3 |
| TCG | 1 | freq=1 len=3 |
| TLS | 1 | freq=1 len=3 |
| UDS | 1 | freq=1 len=3 |
| UEFI | 1 | freq=1 len=4 |
| VDD | 1 | freq=1 len=3 |
| BL2 | 21 | no parenthetical full name in body |
| SRAM | 19 | no parenthetical full name in body |
| DPI | 18 | no parenthetical full name in body |
| UFS | 17 | no parenthetical full name in body |
| SHA | 13 | no parenthetical full name in body |
| ARM | 10 | no parenthetical full name in body |
| TPM | 7 | no parenthetical full name in body |
| NIST | 6 | no parenthetical full name in body |
| ECC | 5 | no parenthetical full name in body |
| NOR | 5 | no parenthetical full name in body |
| SLH | 5 | no parenthetical full name in body |
| TEE | 5 | no parenthetical full name in body |
