# SoC Secure Boot 용어집

핵심 용어 ISO 11179 형식 정의.

---

## A — Anti-Rollback / Attestation

### Anti-Rollback

**Definition.** Image의 이전 버전으로 downgrade를 차단하는 메커니즘으로, OTP fuse counter를 통해 minimum acceptable version을 강제.

**Source.** Secure Boot literature.

**Related.** Version counter, OTP fuse, security patch.

### Attestation

**Definition.** Device가 자신의 boot state를 외부에 증명하는 메커니즘으로, TPM PCR 또는 secure enclave가 서명한 measurement를 사용.

**Source.** TPM 2.0 spec.

**Related.** Measured Boot, PCR, remote attestation.

---

## B — BootROM / BL1-3

### BootROM

**Definition.** SoC에 mask ROM으로 고정된 첫 실행 코드로, 변경 불가능한 trust anchor 역할.

**Source.** SoC architecture.

**Related.** HW RoT, mask ROM, BL1.

### BL1 / BL2 / BL31 / BL33

**Definition.** ARM Trusted Firmware의 boot loader 단계 — BootROM → BL1 (trusted boot init) → BL2 (DRAM init + BL31/33 load) → BL31 (EL3 secure monitor) → BL33 (U-Boot/non-secure).

**Source.** ARM Trusted Firmware.

**See also.** [Module 02](02_chain_of_trust_boot_stages.md)

---

## C — Chain of Trust / Crypto Agility

### Chain of Trust

**Definition.** 각 boot 단계가 다음 단계의 서명을 검증한 후에만 control을 넘기는 신뢰 전파 패턴.

**Source.** Verified Boot architectures.

**Related.** Verify-then-execute, HW RoT.

**See also.** [Module 02](02_chain_of_trust_boot_stages.md)

### Crypto Agility

**Definition.** 암호 알고리즘을 변경 가능하게 설계하는 원칙으로, RSA → PQC (Post-Quantum Cryptography) 같은 마이그레이션 대비.

**Source.** NIST PQC standardization.

---

## E — eFuse / ECDSA

### eFuse

**Definition.** Electrically programmable fuse로, OTP 메모리의 한 형태. 한 번 blow하면 영구적으로 1.

**Source.** Silicon technology.

**Related.** OTP, immutable storage.

### ECDSA

**Definition.** Elliptic Curve Digital Signature Algorithm. RSA보다 작은 key/signature 크기로 동등 보안 제공.

**Source.** FIPS 186.

**Common curves.** P-256, P-384, secp256k1.

---

## F — Fault Injection

### Fault Injection (FI)

**Definition.** 전압 글리치, 클럭 글리치, 레이저, X-ray 등으로 의도적 hardware fault를 유발해 signature 검증을 우회하는 공격 기법.

**Source.** Hardware security research.

**Related.** Glitch detector, FROST, Glitchy Descriptor attack.

**See also.** [Module 05](05_attack_surface_and_defense.md)

---

## H — HSM / HW RoT

### HSM (Hardware Security Module)

**Definition.** 암호 키 생성/저장/사용을 안전한 hardware 안에서만 수행하는 외부 module로, Production private key 관리에 필수.

**Source.** FIPS 140-2/3.

### HW RoT (Hardware Root of Trust)

**Definition.** Boot 신뢰의 출발점으로 mask ROM (BootROM) + OTP (ROTPK hash + 보안 설정)로 구성.

**Source.** Secure Boot literature.

**See also.** [Module 01](01_hardware_root_of_trust.md)

---

## M — Measured Boot

### Measured Boot

**Definition.** 각 boot 단계의 image hash를 TPM PCR (Platform Configuration Register)에 누적하여 OS가 boot history를 검증할 수 있게 하는 기법.

**Source.** TPM 2.0 spec.

**Related.** PCR, attestation, Verified Boot 비교.

**See also.** [Module 02](02_chain_of_trust_boot_stages.md)

---

## O — OTP

### OTP (One-Time Programmable)

**Definition.** 1회만 쓰기 가능한 비휘발성 메모리로, ROTPK hash + 보안 설정 + lifecycle state 저장.

**Source.** Silicon technology.

**Related.** eFuse, mask ROM, ROTPK.

**See also.** [Module 01](01_hardware_root_of_trust.md)

---

## R — ROTPK / RSA

### ROTPK (Root of Trust Public Key)

**Definition.** Boot 검증의 최상위 public key로, hash가 OTP에 저장되어 BootROM이 비교 검증.

**Source.** Trusted Firmware spec.

**See also.** [Module 01](01_hardware_root_of_trust.md)

### RSA

**Definition.** Rivest-Shamir-Adleman 비대칭 암호 알고리즘. Boot signature에 RSA-2048/4096 사용.

**Source.** PKCS #1, RFC 8017.

**Related.** PKCS#1 v1.5, PSS padding.

---

## S — SHA / Side-Channel

### SHA-256 / SHA-384

**Definition.** Secure Hash Algorithm 2 family. Boot image hash + signature 계산에 사용.

**Source.** FIPS 180-4.

### Side-Channel Attack

**Definition.** Power consumption, EM emission, timing 측정으로 키나 secret를 추출하는 공격.

**Source.** Cryptographic literature.

**Related.** Constant-time crypto, masking, blinding.

**See also.** [Module 05](05_attack_surface_and_defense.md)

---

## V — Verified Boot

### Verified Boot

**Definition.** Boot 시 signature 검증으로 image의 인증성을 확인하고, 실패 시 boot를 차단하는 enforcement 기법.

**Source.** Verified Boot architectures.

**Related.** Measured Boot 비교, anti-rollback.

**See also.** [Module 02](02_chain_of_trust_boot_stages.md)

---

## 추가 약어

| 약어 | 풀네임 | 의미 |
|------|--------|------|
| **POR** | Power-On Reset | 시스템 첫 reset |
| **TEE** | Trusted Execution Environment | secure 영역 (TrustZone, SGX 등) |
| **TPM** | Trusted Platform Module | x86 표준 보안 chip |
| **PCR** | Platform Configuration Register | TPM의 hash accumulator |
| **PQC** | Post-Quantum Cryptography | 양자 컴퓨터 대응 암호 |
| **TOCTOU** | Time-of-Check to Time-of-Use | verify와 use 사이 race 공격 |
| **JTAG** | Joint Test Action Group | debug interface (보안 위협 포함) |

---

## 추가 항목 (Phase 2 검수 완료)

### BootROM

**Definition.** SoC 의 첫 부팅 단계로 동작하는 immutable 코드 영역으로, RoT 검증의 시작점이 되며 fuse / OTP 에 기록된 공개키 해시로 다음 단계 이미지의 서명을 검증한다.

**Source.** ARM Trusted Firmware-A (BL1); SoC vendor BootROM specs.

**Related.** RoT, eFuse, OTP, BL1, secure boot.

**See also.** [Module 01](01_hardware_root_of_trust.md)

### JTAG

**Definition.** IEEE 1149.1 기반 boundary-scan 디버그 인터페이스로, secure boot 환경에서는 fuse 또는 인증 challenge 로 비활성화/제한해야 하는 잠재적 공격면이다.

**Source.** IEEE Std 1149.1; SoC vendor security guides.

**Related.** Debug Authentication, JTAG locking, attack surface.

**See also.** [Module 01](01_hardware_root_of_trust.md), [Module 05](05_attack_surface_and_defense.md)

### PUF (Physically Unclonable Function)

**Definition.** 칩 제조 변동성에서 비롯되는 고유한 물리 응답을 키 또는 식별자로 추출하는 회로로, 평문 키를 메모리에 저장하지 않아도 chip-unique secret 을 복원할 수 있다.

**Source.** Suh & Devadas, "Physical Unclonable Functions for Device Authentication", DAC 2007; SoC vendor security IP.

**Related.** HUK, eFuse, key provisioning.

**See also.** [Module 01](01_hardware_root_of_trust.md)

### TOCTOU (Time-of-Check-to-Time-of-Use)

**Definition.** 검증(Time of Check)과 사용(Time of Use) 사이에 공격자가 대상을 변경해 검증 결과를 무력화하는 취약점 클래스.

**Source.** McPhee, "Operating System Integrity in OS/VS2", IBM Systems Journal 1974.

**Related.** Race condition, double-fetch, secure copy-then-verify.

**See also.** [Module 05](05_attack_surface_and_defense.md)

### EL1 (Exception Level 1)

**Definition.** ARMv8 / ARMv9 의 4-level 예외 모델 중 OS 커널이 동작하는 레벨로, Normal World 에선 Linux/RTOS 가, Secure World 에선 Trusted OS 가 위치한다.

**Source.** ARM ARM (Architecture Reference Manual) — Exception Levels.

**Related.** EL0, EL2, EL3, TrustZone, S-EL1.

**See also.** [Module 02](02_chain_of_trust_boot_stages.md)

### EL3 (Exception Level 3)

**Definition.** ARMv8/v9 최상위 예외 레벨로, Secure Monitor (TF-A 의 BL31) 가 동작하며 Normal World ↔ Secure World 전환을 중재한다.

**Source.** ARM ARM — Exception Levels; ARM Trusted Firmware-A.

**Related.** Secure Monitor, BL31, SMC, TrustZone.

**See also.** [Module 02](02_chain_of_trust_boot_stages.md)

### DSA (Digital Signature Algorithm)

**Definition.** NIST FIPS 186 에 정의된 이산대수 기반 서명 알고리즘 군의 총칭으로, 본 강의에서는 RSA / ECDSA / ML-DSA(PQC) 의 상위 카테고리로 사용한다.

**Source.** NIST FIPS 186-5 — Digital Signature Standard.

**Related.** RSA, ECDSA, ML-DSA, signing, verification.

**See also.** [Module 03](03_crypto_in_boot.md)

### PQC (Post-Quantum Cryptography)

**Definition.** 양자 컴퓨팅 공격에 견디도록 설계된 공개키 알고리즘 군으로, NIST 표준화에서는 ML-KEM(키 교환), ML-DSA(서명) 가 채택되었다.

**Source.** NIST PQC Standardization; FIPS 203, 204, 205.

**Related.** ML-DSA, ML-KEM, SLH-DSA, lattice-based crypto.

**See also.** [Module 03](03_crypto_in_boot.md)

### RPMB (Replay Protected Memory Block)

**Definition.** eMMC / UFS 디바이스의 인증 키 기반 영역으로, host 와 공유 secret 으로 read/write 인증을 수행해 rollback / replay 공격을 막는다.

**Source.** JEDEC eMMC 5.1 (JESD84-B51); UFS Spec — RPMB.

**Related.** Secure storage, anti-rollback, monotonic counter.

**See also.** [Module 04](04_boot_device_and_boot_mode.md)

### FIP (Firmware Image Package)

**Definition.** ARM TF-A 가 사용하는 단일 binary container 포맷으로, BL2 / BL31 / BL33 등 부팅 단계별 이미지를 묶고 각각의 무결성 인증서를 포함한다.

**Source.** ARM Trusted Firmware-A documentation, *Firmware Design — FIP*.

**Related.** TF-A, BL2, BL31, BL33, certificate.

**See also.** [Module 04](04_boot_device_and_boot_mode.md)

### PCR (Platform Configuration Register)

**Definition.** TPM 또는 동등한 측정 저장소 내의 누적 해시 레지스터로, 부팅 단계마다 측정값을 extend 하여 Attestation / Sealed Storage 의 기준값으로 사용된다.

**Source.** TCG TPM 2.0 Library Specification.

**Related.** TPM, Measured Boot, Attestation, Extend operation.

**See also.** [Module 02](02_chain_of_trust_boot_stages.md)

### BL31 (TF-A Boot Loader stage 3-1)

**Definition.** ARM Trusted Firmware-A 에서 EL3 에 상주하는 Secure Monitor 단계로, BL2 가 로드한 후 부팅 종료 시점까지 SMC 핸들링과 Power State Coordination(PSCI) 을 담당한다.

**Source.** ARM Trusted Firmware-A documentation.

**Related.** Secure Monitor, BL2, BL33, PSCI, SMC.

**See also.** [Module 02](02_chain_of_trust_boot_stages.md)

### BL33 (TF-A Boot Loader stage 3-3)

**Definition.** TF-A 에서 BL31 다음으로 실행되는 Non-secure bootloader 단계로, 일반적으로 U-Boot / EDK2 가 위치하여 OS loader 까지 인계한다.

**Source.** ARM Trusted Firmware-A documentation.

**Related.** U-Boot, EDK2, BL31, BL32, OS loader.

**See also.** [Module 02](02_chain_of_trust_boot_stages.md)



### TPM (Trusted Platform Module)

**Definition.** TCG 표준이 정의한 보안 코프로세서 / 펌웨어로, 키 보관·서명·attestation·PCR-based measured boot 를 제공한다.

**Source.** TCG TPM 2.0 Library Specification.

**Related.** PCR, Attestation, Sealed Storage.

**See also.** [Module 02](02_chain_of_trust_boot_stages.md)

### NIST FIPS 시리즈 (203 / 204 / 205)

**Definition.** NIST 가 제정한 PQC 표준 — FIPS 203 ML-KEM (key encapsulation), FIPS 204 ML-DSA (signature, lattice), FIPS 205 SLH-DSA (signature, hash-based).

**Source.** NIST FIPS 203, 204, 205 (2024).

**Related.** ML-KEM, ML-DSA, SLH-DSA, PQC.

**See also.** [Module 03](03_crypto_in_boot.md)

### BL32 (Trusted OS, e.g. OP-TEE)

**Definition.** TF-A 의 Secure World OS 단계로, BL31 이 진입점을 호출하면 EL1S 에서 Trusted Application 을 호스팅한다 (대표 구현: OP-TEE).

**Source.** ARM Trusted Firmware-A documentation; OP-TEE documentation.

**Related.** OP-TEE, S-EL1, BL31, TEE.

**See also.** [Module 02](02_chain_of_trust_boot_stages.md)

### NS bit (Non-Secure Bit, TrustZone)

**Definition.** ARM TrustZone 의 핵심 비트로, AXI / AHB transaction 의 보안 도메인 (Secure / Non-Secure) 을 표현하며 TZ aware peripheral 의 접근 권한 결정에 사용된다.

**Source.** ARM TrustZone Architecture; AMBA NSAID extension.

**Related.** TrustZone, S/NS, NSAID.

**See also.** [Module 02](02_chain_of_trust_boot_stages.md)
