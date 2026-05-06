# ARM Security Architecture — 개요

## 학습 플랜
- **레벨**: Intermediate (BootROM Secure EL3 실무 + Secure Boot 지식 기반)
- **목표**: ARM Exception Level, TrustZone, 보안 상태 전환을 화이트보드에 그리며 Secure Boot와 연결하여 설명할 수 있는 수준

## 사전 지식 / 선수 학습
| 주제 | 필수/권장 | 참고 자료 |
|------|----------|----------|
| **SoC Secure Boot 기본** | 필수 | `soc_secure_boot_ko/` — Chain of Trust, Boot Stage, 서명 검증 |
| ARM 기본 아키텍처 | 필수 | AArch64 레지스터, 명령어 기본 (MOV, LDR/STR, BL/RET) |
| 가상 메모리 / 페이지 테이블 | 권장 | `mmu_ko/` — VA→PA 번역, TLB 기본 |
| 암호학 기초 | 권장 | `soc_secure_boot_ko/03_crypto_in_boot.md` — RSA/ECDSA, 해시, 대칭키 |
| AMBA 버스 기초 | 권장 | `amba_protocols_ko/` — APB/AXI 트랜잭션 기본 (TZPC/TZASC 이해에 필요) |

## 핵심 용어집 (Glossary)

### Exception Level & 권한

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **EL** | Exception Level | ARM CPU 권한 수준 (EL0~EL3, 숫자가 높을수록 높은 권한) |
| **EL0/1/2/3** | — | App / OS Kernel / Hypervisor / Secure Monitor |
| **S-EL, NS-EL** | Secure / Non-Secure EL | TrustZone의 Secure/Normal World에서의 EL |

### TrustZone & 월드 분리

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **TrustZone** | ARM TrustZone | Secure/Non-Secure 월드를 HW로 격리하는 아키텍처 |
| **NS bit** | Non-Secure Bit | 버스 트랜잭션마다 HW가 강제 태깅하는 보안 상태 비트 |
| **TEE** | Trusted Execution Environment | Secure World에서 동작하는 격리 실행 환경 (OP-TEE 등) |
| **TA** | Trusted Application | TEE 내에서 실행되는 신뢰 앱 (결제, 키 관리 등) |

### EL 전환 메커니즘

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **SVC** | Supervisor Call | EL0→EL1 시스템 콜 |
| **HVC** | Hypervisor Call | EL1→EL2 하이퍼바이저 요청 |
| **SMC** | Secure Monitor Call | Any→EL3 월드 전환 (Secure↔Normal) |
| **ERET** | Exception Return | 상위 EL에서 하위 EL로 복귀 |
| **VBAR** | Vector Base Address Register | Exception 발생 시 점프할 벡터 테이블 기준 주소 |
| **FF-A** | Firmware Framework for Arm | Secure Partition 간 표준 통신 프레임워크 (ARMv8.4+) |

### SoC 보안 인프라

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **TZPC** | TrustZone Protection Controller | APB 주변장치를 Secure/Non-Secure로 분류 |
| **TZASC** | TrustZone Address Space Controller | DRAM 영역을 Secure/Non-Secure로 분할 |
| **SMMU** | System MMU | DMA Master별 주소 변환 + 접근 제어 |
| **GIC** | Generic Interrupt Controller | 인터럽트 분배 및 Secure/Non-Secure 분류 |

### Secure Enclave & TEE 계층

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **Secure Enclave** | — | CPU와 독립된 전용 프로세서+RAM의 격리 실행 환경. TrustZone보다 높은 보안 레벨 |
| **SEP** | Secure Enclave Processor | Apple의 Internal Secure Enclave 구현 |
| **SSP** | Samsung Security Processor | Samsung의 Internal Secure Enclave 구현 |
| **DRM** | Digital Rights Management | 디지털 컨텐츠 저작권 보호. TEE의 대표적 활용 사례 |
| **TZMP** | TrustZone Multimedia Play | ARM의 TrustZone 기반 Protected Media Pipeline |

### 핵심 레지스터

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **SCR_EL3** | Secure Configuration Register | EL3의 보안 정책 제어 (NS bit 설정 등) |
| **SPSR** | Saved Processor Status Register | Exception 발생 시 PSTATE 저장 |
| **ELR** | Exception Link Register | Exception 발생 시 복귀 주소 저장 |
| **TTBR** | Translation Table Base Register | 페이지 테이블 기준 주소 |

### Boot & 검증

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **BL1/BL2/BL31/BL32/BL33** | Boot Loader stages | BootROM / FSBL / Secure Monitor / TEE OS / Normal BL |
| **ATF** | ARM Trusted Firmware | ARM의 EL3 Secure Monitor 오픈소스 구현 |
| **OP-TEE** | Open Portable TEE | 오픈소스 TEE OS |
| **PSCI** | Power State Coordination Interface | 전원 관리용 SMC 인터페이스 |

### 공격 기법

| 약어 | 풀네임 | 설명 |
|------|--------|------|
| **TOCTOU** | Time-of-Check-Time-of-Use | 검증 시점과 사용 시점 사이에 데이터를 변조하는 공격 |
| **Cache Side Channel** | — | 캐시 타이밍 차이로 비밀 정보를 유출하는 공격 (Flush+Reload 등) |

---

## 컨셉 맵

```
     +-----------------------------------------------+
     |          ARM Security Architecture             |
     |                                                |
     |  +-------------------+  +-------------------+  |
     |  | Secure World      |  | Non-Secure World  |  |
     |  | (TrustZone)       |  | (Normal World)    |  |
     |  |                   |  |                   |  |
     |  | EL3: Secure Mon.  |  |                   |  |
     |  | S-EL2: Sec Hyp.   |  | NS-EL2: Hypervisor|  |
     |  | S-EL1: TEE OS     |  | NS-EL1: OS       |  |
     |  | S-EL0: Trusted App|  | NS-EL0: User App  |  |
     |  +-------------------+  +-------------------+  |
     |         ↕ SMC (EL3 경유)        ↕              |
     |  +-------------------------------------------+ |
     |  | EL 전환: SVC / HVC / SMC / ERET           | |
     |  | 벡터 테이블: VBAR_ELn                      | |
     |  | 메모리 번역: TTBR / VTTBR / Stage 1&2     | |
     |  +-------------------------------------------+ |
     |                                                |
     |  +-------------------------------------------+ |
     |  | SoC 보안 인프라 (HW 격리)                  | |
     |  | TZPC / TZASC / SMMU / GIC / Cache NS-bit  | |
     |  +-------------------------------------------+ |
     |                                                |
     |  +-------------------------------------------+ |
     |  | Secure Enclave (TrustZone 너머)            | |
     |  | Internal (Key Box, Crypto) /               | |
     |  | External (별도 IC, Root of Trust)           | |
     |  | 상호 불신 / DRM Pipeline                    | |
     |  +-------------------------------------------+ |
     |                                                |
     |  +-------------------------------------------+ |
     |  | 부팅 보안                                  | |
     |  | Anti-Rollback / Measured Boot / Attestation| |
     |  +-------------------------------------------+ |
     +-----------------------------------------------+
```

## 학습 단위

| # | 단위 | 핵심 질문 | 주요 추가 내용 |
|---|------|----------|---------------|
| 1 | **Exception Level & TrustZone** | 4개 EL과 Secure/Non-Secure 분리는 어떻게 동작하는가? | EL 전환 메커니즘(SVC/HVC/SMC/ERET), VBAR, 메모리 번역 체계, FF-A |
| 2 | **보안 상태 전환 & SoC 보안 인프라** | 월드 간 전환은 어떻게 이루어지고, 버스/메모리 보안은 어떻게 적용되는가? | SMMU, GICv3, Cache NS-bit 태깅, 월드 간 통신 |
| 2A | **Secure Enclave & TEE 계층 구조** | TrustZone 너머의 보안 계층은 무엇이고, 왜 필요한가? | Internal/External Secure Enclave, 다층 TEE 상호 불신, DRM Pipeline |
| 3 | **Secure Boot에서의 보안 레벨 적용** | BootROM부터 OS까지 보안 레벨이 어떻게 변화하는가? | Anti-Rollback, Measured Boot, DV 검증 방법론, SVA, 실제 공격 사례 |

## 이력서 연결

| 이력서 항목 | 관련 Unit | 면접 시 활용 |
|------------|----------|-------------|
| BootROM (Secure EL3) | Unit 1, 3 | 최고 권한에서 동작하는 이유 |
| Secure Boot Flow | Unit 3 | EL 전환과 Boot Stage 연결 |
| 보안 공격/방어 | Unit 2 | TrustZone이 방어하는 공격 |
| OTP/JTAG 보안 | Unit 2 | SoC 보안 인프라와 연결 |
