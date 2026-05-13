# SoC Secure Boot Flow — 개요 및 컨셉 맵

## 학습 플랜
- **레벨**: Intermediate → Advanced (실무 경험 기반, 체계적 정리 + 면접 대비)
- **목표**: Secure Boot 전체 흐름을 화이트보드에 그리며 보안 위협과 방어를 논리적으로 설명할 수 있는 수준

## 핵심 용어집 (Glossary)

### 하드웨어 신뢰 기반

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **HW RoT** | Hardware Root of Trust | BootROM + OTP 조합의 변경 불가능한 신뢰 기초 |
| **BootROM** | — | 마스크 ROM에 고정된 변경 불가 부팅 코드 (BL1) |
| **OTP** | One-Time Programmable | 일회성 쓰기 메모리 (eFuse/Antifuse). ROTPK 해시 저장 |
| **eFuse** | Electrical Fuse | 전류로 금속 퓨즈를 끊어 프로그래밍 (저비용) |
| **Antifuse** | — | 전압으로 절연층을 파괴하여 프로그래밍 (보안 우수) |
| **SRAM** | Static RAM | BL1 실행용 고속 메모리 (DRAM 초기화 전) |

### 부팅 단계

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **Chain of Trust** | — | 각 단계가 다음 단계를 서명 검증 후 제어권을 넘기는 구조 |
| **BL1** | Boot Loader 1 | BootROM. HW/보안 초기화 + BL2 검증 (EL3) |
| **BL2** | Boot Loader 2 | FSBL. DRAM 초기화 + BL3x 검증 (S-EL1) |
| **BL31** | Boot Loader 3-1 | Secure Monitor (ATF). Secure↔Normal 전환 관리 (EL3) |
| **BL32** | Boot Loader 3-2 | TEE OS (OP-TEE). Trusted App 실행 (S-EL1) |
| **BL33** | Boot Loader 3-3 | Normal BL (U-Boot). OS 로드 (NS-EL1) |
| **FIP** | Firmware Image Package | ARM TF-A 표준 부팅 이미지 포맷 (ToC 기반) |

### 암호학

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **ROTPK** | Root of Trust Public Key | OTP에 해시로 저장된 최상위 공개키 |
| **RSA** | Rivest-Shamir-Adleman | 비대칭 암호. 검증 빠름, 키 큼 (2048/4096-bit) |
| **ECDSA** | Elliptic Curve DSA | 타원곡선 기반 서명. 키 작음, 검증 느림 |
| **SHA** | Secure Hash Algorithm | 암호학적 해시 함수 (SHA-256/384/512) |
| **HMAC** | Hash-based MAC | 키를 사용한 메시지 인증 코드 |
| **PQC** | Post-Quantum Cryptography | 양자컴퓨터에 저항하는 차세대 암호 (ML-DSA, SLH-DSA) |

### 부팅 장치

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **UFS** | Universal Flash Storage | 고속 저장장치 (2.9 GB/s), 복잡한 프로토콜 스택 |
| **eMMC** | embedded MultiMediaCard | 중간 속도 저장장치 (400 MB/s), 단순한 프로토콜 |
| **Boot LU** | Boot Logical Unit | UFS 내 부팅 전용 파티션 |
| **RPMB** | Replay Protected Memory Block | HMAC 기반 보안 저장 영역 (Anti-Rollback 카운터 등) |
| **Pinstrap** | — | PCB GPIO 풀업/다운으로 부팅 모드 선택 |

### 보안 & 공격/방어

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **Anti-Rollback** | — | OTP 단조증가 카운터로 구버전 FW 다운그레이드 방지 |
| **FI** | Fault Injection | 전압/클럭/EM 글리치로 보안 검증을 우회하는 물리 공격 |
| **SCA** | Side-Channel Attack | 전력/EM/타이밍 분석으로 암호 키를 추론하는 공격 |
| **TOCTOU** | Time-of-Check-to-Time-of-Use | 검증~사용 사이에 DMA로 메모리를 변조하는 공격 |
| **ROM Patch** | — | BootROM 버그 수정 메커니즘 (HW Address Comparator 사용) |
| **Lifecycle State** | — | Dev → Provisioning → Production → End-of-Life (비가역적) |

### 검증 관련

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **Measured Boot** | — | 부팅 단계 해시를 TPM PCR에 기록 (Remote Attestation 가능) |
| **TPM** | Trusted Platform Module | 별도 칩의 보안 저장소 (PCR, 키 관리) |
| **DICE** | Device Identifier Composition Engine | TPM 없는 경량 기기용 측정 부팅 표준 |
| **DPI-C** | Direct Programming Interface C | SystemVerilog↔C 양방향 인터페이스 (HW/SW Co-verification) |

---

## 컨셉 맵

```d2
direction: down

# unparsed: POR["Power-On Reset"]
# unparsed: HWROT["Hardware Root of Trust<br/>(eFuse/OTP + BootROM)"]
# unparsed: COT["Chain of Trust<br/>BL1 → BL2 → BL31/32/33 → OS"]
# unparsed: CRYPTO["Crypto<br/>RSA/ECC<br/>PQC"]
# unparsed: BOOTDEV["Boot Device<br/>UFS/eMMC<br/>USB/SPI"]
# unparsed: ATTACK["Attack Surface<br/>& Defense"]
POR -> HWROT
HWROT -> COT
COT -> CRYPTO
COT -> BOOTDEV
COT -> ATTACK
```

## 학습 단위 (Units)

| # | 단위 | 핵심 질문 |
|---|------|----------|
| 1 | **Hardware Root of Trust** | 신뢰의 기반은 왜 하드웨어여야 하는가? |
| 2 | **Chain of Trust & Boot Stages** | BL1→BL2→BL3x 인증 전파는 어떻게 동작하는가? |
| 3 | **Secure Boot 암호학** | 서명 검증과 키 관리는 어떻게 이루어지는가? |
| 4 | **Boot Device & Boot Mode** | 부팅 장치는 어떻게 선택되고, 각각 어떻게 초기화되는가? |
| 5 | **공격 표면과 방어** | Secure Boot에 대한 공격 유형과 방어 기법은? |
| 6 | **Quick Reference Card** | 면접 직전 빠른 복습용 요약 카드 |
| 7 | **BootROM DV 검증 방법론** | UVM 프레임워크로 Secure Boot를 어떻게 검증하고, Zero-Defect Silicon을 달성하는가? |

## 학습 의존성 흐름

```d2
direction: down

# unparsed: U1["Unit 1 (HW RoT)<br/>신뢰의 닻이 무엇인가?"]
# unparsed: U2["Unit 2 (Chain of Trust)<br/>신뢰가 어떻게 전파되는가?"]
# unparsed: U3["Unit 3 (암호학)<br/>서명/검증 원리"]
# unparsed: U4["Unit 4 (Boot Device)<br/>부팅 장치 프로토콜"]
# unparsed: U5["Unit 5 (공격/방어)<br/>위협과 대응"]
# unparsed: U7["Unit 7 (DV 방법론)<br/>이론 → 실리콘 품질"]
# unparsed: U6["Unit 6 (Quick Reference)<br/>면접 전 최종 복습"]
U1 -> U2
U1 -> U5
U2 -> U3
U2 -> U4
U2 -> U5
U3 -> U7
U4 -> U7
U5 -> U7
U7 -> U6
```

**권장 학습 순서**: Unit 1 → 2 → 3/4/5 (병렬 가능) → 7 → 6 (면접 직전 복습)

---

## 이력서 연결 포인트

| 이력서 항목 | 관련 Unit | 면접 시 활용 |
|------------|----------|-------------|
| OTP Abstraction Layer (RAL 모델링) | Unit 1, 4, **7** | OTP 추상화 + Boot Mode sweep 전략 |
| Active UVM Driver (force/release) | Unit 5, **7** | Fault Injection 시뮬레이션 + Negative 시나리오 |
| DPI-C C-model 통합 | Unit 3, **7** | HW/SW Co-verification + 보안 핸드셰이크 검증 |
| Apple/Meta 포팅 | **Unit 7** | 모듈형 UVM 아키텍처의 재사용성 + 포팅 전략 |
| BootROM Lead 3년 | **Unit 7** | 전체 검증 전략 + Coverage + Post-silicon 연결 |
| Legacy → UVM 전환 | **Unit 7** | 문제 분석 → 해결 → 성과 스토리 |
| Coverage-Driven 방법론 | **Unit 7** | 5개 Covergroup 구조 + Closure 전략 |
| Zero-Defect Silicon | **Unit 7** | Pre-silicon 완전성 → Post-silicon 디버그 가속 |


--8<-- "abbreviations.md"
--8<-- "_inc/topic_abbr.md"
