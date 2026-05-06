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
