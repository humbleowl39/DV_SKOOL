# Unit 2A: Secure Enclave & TEE 계층 구조

<div class="learning-meta">
  <span class="meta-badge meta-time">⏱ 23분</span>
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

## 핵심 개념
**TrustZone은 CPU 기반 TEE이므로 Trusted OS 취약점, 캐시 공유 부채널, CPU 자원 경합의 한계가 있다. Secure Enclave는 전용 프로세서+RAM으로 이 한계를 물리적으로 제거하며, TrustZone과 상호 불신(mutually distrusting) 관계로 공존한다.**

"TZASC/SMMU/GIC가 TrustZone의 '경비원'이라면, Secure Enclave는 아예 '별도 건물' — 건물 사이에도 출입증을 검사한다."

---

## Unit 2와의 관계

```
Unit 2에서 다룬 것:
  TrustZone 격리를 SoC HW가 강제하는 메커니즘
  → TZPC(APB 주변장치), TZASC(DRAM 영역), SMMU(DMA), GIC(인터럽트), Cache NS-bit

이 유닛에서 다루는 것:
  TrustZone 너머의 보안 계층 — Secure Enclave
  → TrustZone과 별개의 독립 실행 환경
  → 다층 TEE 구조에서의 상호 불신 관계
  → TEE의 실제 활용 사례 (DRM Protected Media Pipeline)
```

---

## 1. TEE 다층 계층 구조

### 단일 TrustZone에서 다층 TEE로

Unit 1~2에서 배운 TrustZone은 Secure/Non-Secure **2개 세계**의 분리였다. 실제 SoC에는 보안 레벨이 다른 **여러 TEE**가 공존한다:

```
보안 레벨 (낮음 → 높음)
───────────────────────────────────────────────────────────

  ┌─────────────────────────────────────┐
  │           REE (Rich EE)             │  ← 보안 레벨 최하
  │  일반 OS (Linux, Android)           │     NS-EL0/NS-EL1
  └─────────────────────────────────────┘
                    │
  ┌─────────────────────────────────────┐
  │       Non-secure EL2 (Hypervisor)   │  ← VM 간 격리
  │  가상 머신 관리, VM별 리소스 분리    │     여전히 Non-secure
  └─────────────────────────────────────┘
                    │
  ┌─────────────────────────────────────┐
  │       Secure (TrustZone)            │  ← CPU 기반 TEE
  │  Trusted OS + Trusted Applications  │     S-EL0/S-EL1
  │  키 관리, 인증, FW 검증             │     (Unit 1~2 범위)
  └─────────────────────────────────────┘
                    │
  ╔═════════════════════════════════════╗
  ║    Secure Enclave (SoC Internal)    ║  ← SoC 내 최고 보안
  ║  전용 프로세서 + 전용 RAM            ║     CPU 클러스터와 독립
  ║  Key Box + Crypto Accelerator       ║
  ╚═════════════════════════════════════╝
                    │
  ╔═════════════════════════════════════╗
  ║    Secure Enclave (External IC)     ║  ← 물리적 분리
  ║  별도 보안 칩 (SPI 연결)             ║     Private Storage
  ║  사용자 비밀/프라이버시 저장          ║     최상위 Root of Trust
  ╚═════════════════════════════════════╝

───────────────────────────────────────────────────────────
```

### ARM EL과의 매핑 (Unit 1 복습 + 확장)

```
         Non-secure                    Secure
      ┌──────────────────┐    ┌──────────────────┐
EL0   │  AArch64 App     │    │  Trusted Services │
      ├──────────────────┤    ├──────────────────┤
EL1   │  AArch64 Kernel  │    │  Trusted OS       │
      ├──────────────────┤    ├──────────────────┤
EL2   │  Hypervisor      │    │  Trusted Partition│  ← Secure EL2
      │                  │    │  Manager*         │    (ARMv8.4-A~)
      ├──────────────────┴────┴──────────────────┤
EL3   │         Firmware / Secure Monitor         │  ← 양쪽 전환 담당
      └──────────────────────────────────────────┘

  ※ Secure Enclave는 이 EL 체계 밖에 존재
    → CPU와 별개의 전용 프로세서에서 독립 실행
    → ARM EL이 아닌 자체 실행 모드
```

---

## 2. Secure Enclave

### 왜 TrustZone만으로는 부족한가?

| TrustZone 한계 | 원인 | 결과 |
|---------------|------|------|
| **Trusted OS 취약점** | Secure World도 복잡한 OS를 실행 (OP-TEE 등) | Trusted OS가 뚫리면 Secure World 전체 컴프로마이즈 |
| **CPU/캐시 공유** | Secure와 Non-secure가 동일 CPU 코어 사용 | 캐시 부채널 공격 (Spectre 계열) 노출 |
| **컨텍스트 스위칭 오버헤드** | SMC로 월드 전환 시 레지스터 저장/복원 | 빈번한 보안 연산에 성능 저하 |
| **공격 표면** | Trusted App이 많아질수록 S-EL0 코드 증가 | 더 많은 공격 진입점 |

### Secure Enclave 구조

```
┌─────────────────────────────────────────┐
│            SoC                           │
│                                         │
│  ┌───────────────────┐                  │
│  │ CPU Cluster        │                  │
│  │ (TrustZone 포함)   │                  │
│  │ NS-EL0/1/2, S-EL0/1│                  │
│  └────────┬───────────┘                  │
│           │                              │
│  ═════════╪═══ System Interconnect ══════│═
│           │                              │
│  ┌────────┴───────────────────────────┐  │
│  │ Internal Secure Enclave             │  │
│  │                                     │  │
│  │  ┌──────────┐  ┌────────────────┐  │  │
│  │  │Processor │  │ Private RAM    │  │  │  ← 전용 프로세서 + 전용 메모리
│  │  │(자체 ISA)│  │ (SRAM, 수 KB~) │  │  │     시스템 DRAM 사용 안 함
│  │  └──────────┘  └────────────────┘  │  │
│  │  ┌──────────┐  ┌────────────────┐  │  │
│  │  │Key Box   │  │Crypto Accel    │  │  │  ← 전용 HW 암호 엔진
│  │  │(키 저장) │  │(AES/RSA/ECC)   │  │  │     키가 버스에 노출 안 됨
│  │  └──────────┘  └────────────────┘  │  │
│  │  ┌──────────┐  ┌────────────────┐  │  │
│  │  │Mailbox   │  │ DMA            │  │  │  ← 외부 통신은 Mailbox로만
│  │  │(APB)     │  │                │  │  │
│  │  └──────────┘  └────────────────┘  │  │
│  └─────────────────────────────────────┘  │
│           │                              │
│           │ SPI (Secure Channel)         │
│           v                              │
│  ┌─────────────────────────┐  ┌───────┐ │
│  │ External Secure Enclave │──│Storage│ │  ← 별도 IC
│  │ (보안 칩)                │  │       │ │     Root of Trust
│  └─────────────────────────┘  └───────┘ │
└─────────────────────────────────────────┘
```

### Internal vs External Secure Enclave

| | Internal Secure Enclave | External Secure Enclave |
|--|------------------------|------------------------|
| **위치** | SoC 내부 (on-die) | 별도 IC (SPI/I2C 연결) |
| **프로세서** | 전용 코어 (경량, 자체 ISA) | 자체 프로세서 |
| **메모리** | 전용 SRAM (수 KB ~ 수십 KB) | 자체 NVM + SRAM |
| **핵심 역할** | Key Box, Crypto Accelerator | Root of Trust, Private Storage |
| **부팅 주체** | 더 상위 보안 TEE가 부팅 | 자체 BootROM (자립 부팅) |
| **물리 공격 저항** | SoC die 내부 → decapping 필요 | 별도 칩 → 독립적 anti-tamper |
| **대표 구현** | Apple SEP, Samsung SSP | TPM, NXP SE050, Infineon SLE97 |

### 핵심: TrustZone과 Secure Enclave의 상호 불신

```
                    ┌─────────────┐
                    │  TrustZone  │
                    │  (Secure    │
                    │   World)    │
                    └──────┬──────┘
                           │
                    서로 신뢰하지 않음
                    (mutually distrusting)
                           │
              ┌────────────┴────────────┐
              │                         │
     ┌────────┴────────┐     ┌─────────┴────────┐
     │ Internal Secure  │     │ External Secure   │
     │ Enclave          │     │ Enclave           │
     └─────────────────┘     └──────────────────┘
```

**왜 상호 불신인가?**

| 관계 | 위협 시나리오 | 상호 불신의 효과 |
|------|-------------|---------------|
| TrustZone → Enclave | Trusted OS에 RCE 취약점 → Secure World 전체 장악 | Enclave는 TrustZone 요청도 Mailbox + 인증으로만 수용 |
| Enclave → TrustZone | Enclave FW 버그로 잘못된 응답 반환 | TrustZone은 Enclave 응답의 무결성을 독립 검증 |
| Internal ↔ External | External IC가 물리적으로 교체/변조될 수 있음 | Secure Channel Protocol (SPI 위에 암호화+인증) |

→ Secure Boot의 Chain of Trust에서 "BL2가 BL3를 검증하듯" 각 TEE가 상대방을 검증하는 구조

### Unit 2 개념과의 매핑

Unit 2에서 배운 HW 인프라가 Secure Enclave에서도 동일하게 적용된다:

| Unit 2 HW 인프라 | Secure Enclave에서의 적용 |
|-----------------|-------------------------|
| **TZASC** (DRAM 영역 보호) | Enclave 전용 메모리 리전 → TZASC가 TrustZone 접근도 차단하도록 설정 가능 |
| **SMMU** (DMA 접근 제어) | Enclave DMA의 SMMU 설정은 Enclave 자체가 관리 → 외부 변경 불가 |
| **Cache NS-bit** | Enclave 메모리는 캐시 불가(Non-cacheable)로 설정하거나, 전용 캐시 사용 |
| **GIC** | Enclave 인터럽트 → Group 0 (EL3) 또는 Enclave 전용 IRQ |
| **TZPC** | Enclave의 Mailbox/APB 레지스터 → 적절한 보안 레벨만 접근 |

### Processing Element의 보안 원칙

Secure Enclave 내부의 Processing Element(전용 프로세서)가 외부와 통신할 때:

```
  Processing Element → 외부 메모리 기록 시:
  
  ┌─────────────────────────────────┐
  │ Enclave Processing Element      │
  │                                 │
  │  비밀 데이터 (평문)              │
  │       │                         │
  │       v                         │
  │  Crypto Accelerator             │  ← 내부에서 암호화 후
  │       │                         │
  │       v                         │
  │  AXI Master (AxPROT=Secure)     │  ← 암호화된 데이터만 외부로
  └────────┬────────────────────────┘
           │ 암호문만 DRAM에 기록
           v
        [DRAM]  ← 물리 덤프해도 평문 없음

  ※ 비밀 데이터가 버스/DRAM에 평문으로 절대 노출되지 않음
     → DRAM Protector + 암호화의 이중 방어
```

---

## 3. TEE 활용 사례: DRM Protected Media Pipeline

DRM(Digital Rights Management)은 TEE의 가장 직관적인 활용 사례다. **복호화된 컨텐츠가 Non-secure World에 절대 노출되지 않아야** 한다.

### ARM TZMP (TrustZone Multimedia Play) 흐름

```
┌─────────────┐   ┌──────────────┐   ┌──────────────────────────────────────┐
│ Non-secure  │   │   Secure     │   │       Protected Media Pipeline       │
│ World       │   │   World      │   │       (Secure 전용 HW 파이프라인)     │
│             │   │              │   │                                      │
│ ┌─────────┐ │   │ ┌──────────┐│   │ ┌──────┐ ┌────────┐ ┌────────────┐  │
│ │Encrypted│─┼──►│ │ Decrypt  ││──►│ │Decode│→│Picture │→│  Display   │──►Panel/
│ │Stream   │ │   │ │          ││   │ │      │ │Quality │ │  Engine    │  HDMI
│ └─────────┘ │   │ └──────────┘│   │ └──────┘ └────────┘ └────────────┘  │
│             │   │              │   │                                      │
│ ┌─────────┐ │   │              │   │  ※ 파이프라인의 모든 버퍼 메모리가   │
│ │Metadata │─┼─ ─┼─ ─ ─ ─ ─ ─ ─┼──►│    TZASC에 의해 Secure 전용으로 보호 │
│ └─────────┘ │   │              │   │    Non-secure 접근 시 DECERR         │
│             │   │              │   │                                      │
│ ┌─────────┐ │   │              │   │  Display Engine도 Secure Master로    │
│ │  OSD    │─┼─ ─┼─ ─ ─ ─ ─ ─ ─┼──►│  설정 → HDMI까지 보안 체인 유지     │
│ └─────────┘ │   │              │   │                                      │
└─────────────┘   └──────────────┘   └──────────────────────────────────────┘
```

### HW 보안 인프라의 역할 (Unit 2 연결)

| 단계 | 보호 메커니즘 | Unit 2 대응 |
|------|-------------|------------|
| 복호화 키 저장 | Secure Enclave Key Box | — (이 유닛 신규) |
| 복호화 실행 | TrustZone Secure World | S-EL1 TEE OS |
| 복호화된 스트림 메모리 | TZASC Secure Region | Unit 2 TZASC |
| 비디오 디코더 DMA | SMMU Secure Stream | Unit 2 SMMU |
| 캐시된 비디오 데이터 | Cache NS-bit | Unit 2 Cache NS-bit |
| Display Engine 접근 | TZPC Secure Peripheral | Unit 2 TZPC |

### TEE 없이 DRM을 하면?

```
TEE 미적용:

  Encrypted Stream → [SW Decrypt in Normal World] → 메모리에 평문!
                                                          │
                                                    루트 권한 획득 시
                                                    /dev/mem로 평문 추출 가능

TEE 적용:

  Encrypted Stream → [Secure World Decrypt] → [TZASC Secure Region]
                                                      │
                                               Non-secure 접근 → DECERR
                                               메모리 덤프 → 평문 없음
                                               Display까지 Secure 파이프라인
```

### SoC 보안과의 연결

DRM Pipeline은 다음과 동일한 원리를 공유한다:

| DRM 시나리오 | SoC 보안 대응 |
|-------------|-------------|
| 복호화된 영상이 메모리에 평문 노출 | Secure Boot에서 복호화된 FW가 SRAM에만 존재하는 것과 동일 |
| Display까지 보안 파이프라인 유지 | Chain of Trust에서 BL1→BL33까지 검증 체인 유지와 동일 |
| 복호화 키를 Enclave에 저장 | ROTPK를 OTP에 저장하는 것과 동일 원리 |

---

## 대표 문제

### Q1. "TrustZone이 있는데 왜 별도의 Secure Enclave가 필요한가?"

**사고 과정:**

1. TrustZone은 CPU 기반 TEE다 — CPU 코어에서 Secure World를 실행한다.
2. TrustZone의 한계를 구체적으로 떠올린다:
   - Trusted OS(OP-TEE)에 취약점이 있으면 Secure World 전체가 컴프로마이즈
   - CPU/캐시를 공유하므로 Spectre 계열 캐시 부채널 공격에 노출
   - Secure World 진입/퇴출 시 컨텍스트 스위칭 오버헤드 (SMC + 레지스터 저장/복원)
3. Secure Enclave는 **물리적으로 분리된 전용 프로세서**:
   - TrustZone이 뚫려도 Enclave는 영향 없음 (상호 불신)
   - 전용 RAM → 공유 캐시 부채널 없음
   - 전용 Crypto Accelerator → 키가 시스템 버스에 노출되지 않음
4. 대신 Enclave의 한계도 있다:
   - 저성능 프로세서 (범용 연산 불가)
   - 제한된 통신 (Mailbox 기반)
   - 비용/면적 증가

**Dry run — 공격 시나리오 비교:**

```
공격: Trusted OS에 RCE 취약점 발견

TrustZone만 있는 SoC:
  Step 1: 공격자가 NS-EL1에서 Trusted App의 입력 검증 버그를 발견
  Step 2: SMC 호출로 악성 입력 전달 → OP-TEE 버퍼 오버플로
  Step 3: S-EL1에서 임의 코드 실행 → Secure World 전체 장악
  Step 4: TZASC 설정 변경? → 불가 (EL3 권한 필요)
          하지만 S-EL1의 키/데이터 접근 → 가능!
  결과: Secure World에 저장된 모든 키, 인증 정보 유출

TrustZone + Secure Enclave:
  Step 1~3: 동일 — S-EL1 장악
  Step 4: 마스터 키는 Enclave Key Box에 저장
          S-EL1에서 Enclave에 키 요청 → Mailbox 통신
          Enclave가 요청의 인증 토큰 검증 → 실패 (공격자는 토큰 없음)
  결과: Trusted OS는 뚫렸지만, 마스터 키는 Enclave에서 안전
```

**핵심 답변**: "TrustZone은 CPU 기반이라 범용 Trusted Application을 실행할 수 있지만, CPU/캐시 공유로 부채널 노출 + Trusted OS 취약점 시 전체 위험이 있다. Secure Enclave는 전용 프로세서/RAM으로 이 약점을 물리적으로 제거하되, 범용성을 포기한다. 둘은 대체가 아닌 **보완** 관계 — TrustZone이 인증/검증 같은 범용 작업, Enclave가 마스터 키/Secure Boot RoT 같은 최고 기밀 작업을 담당하는 분업 구조다."

### Q2. "DRM Pipeline에서 TZASC 설정이 잘못되면 어떤 공격이 가능한가?"

**사고 과정:**

1. DRM Pipeline에서 복호화된 비디오 버퍼가 TZASC의 Secure Region에 할당된다.
2. TZASC 설정 오류: 해당 Region이 Non-secure로 설정되면?
3. Non-secure Master(GPU, CPU)가 비디오 버퍼에 접근 가능해진다.
4. Unit 2에서 배운 SMMU가 추가 방어를 제공하는가? → DMA Master별 제어이므로 GPU에는 SMMU가 차단할 수 있지만, CPU 직접 접근은 TZASC가 유일한 방어.

**Dry run:**

```
정상 설정:
  비디오 버퍼: 0x4000_0000 ~ 0x40FF_FFFF
  TZASC Region: Security = Secure
  NS CPU LDR → TZASC → DECERR (차단)

잘못된 설정:
  비디오 버퍼: 0x4000_0000 ~ 0x40FF_FFFF
  TZASC Region: Security = Non-Secure (설정 오류!)
  
  Step 1: NS CPU LDR R0, [0x4000_0000] → TZASC → 허용!
  Step 2: 복호화된 YUV 프레임 데이터가 Non-secure에 반환
  Step 3: 공격자가 /dev/mem으로 비디오 버퍼를 연속 읽기
  Step 4: 복호화된 영상 컨텐츠 완전 탈취
  
  DV 검증 포인트:
  → TZASC 보안 설정의 Negative Test 필수
  → "Secure로 설정되어야 할 리전에 NS 접근 시 DECERR" SVA assertion
```

**핵심 답변**: "TZASC 설정 하나의 오류로 DRM 보안 체인 전체가 무력화된다. Non-secure에서 Secure 비디오 버퍼에 접근 가능해지므로, 메모리 덤프로 복호화된 컨텐츠를 탈취할 수 있다. 이것이 DV에서 Security Configuration의 Negative Test가 필수인 이유 — 'TZASC가 NS 접근을 차단하는가'를 검증하지 않으면, 한 비트의 설정 오류가 수백만 달러의 라이선스 위반으로 이어진다."

---

## 확인 퀴즈

### Quiz 1. Secure Enclave가 CPU 클러스터와 물리적으로 분리됨으로써 방어할 수 있는 공격 2가지를 설명하라.

<details>
<summary>정답 보기</summary>

**1. 캐시 부채널 공격 (Spectre/Meltdown 계열)**
TrustZone은 CPU를 공유하므로 LLC(Last Level Cache)도 공유한다. NS-bit 태깅이 직접 접근은 차단하지만, Spectre 계열의 투기적 실행(speculative execution) 공격은 캐시 타이밍 차이를 통해 Secure 데이터를 간접적으로 유출할 수 있다. Secure Enclave는 전용 프로세서 + 전용 SRAM을 사용하므로, CPU 캐시를 아예 공유하지 않아 이 공격 벡터 자체가 존재하지 않는다.

**2. Trusted OS 취약점을 통한 키 탈취**
TrustZone의 S-EL1에서 실행되는 Trusted OS(OP-TEE 등)에 버퍼 오버플로 등 RCE 취약점이 있으면, 공격자가 Secure World에서 임의 코드를 실행하여 S-EL1 메모리의 모든 키에 접근할 수 있다. Secure Enclave에 마스터 키를 저장하면, S-EL1이 장악되더라도 Enclave의 키에는 접근 불가하다 — Mailbox + 인증 토큰을 통한 간접 접근만 가능하고, 인증 없이는 Enclave가 거부한다.
</details>

### Quiz 2. DRM Protected Media Pipeline에서, 복호화 키 → 스트림 복호화 → 비디오 디코딩 → 디스플레이 출력까지의 보안 체인에서 Unit 2의 어떤 HW 인프라가 각 단계를 보호하는지 매핑하라.

<details>
<summary>정답 보기</summary>

| 단계 | 보호 HW | 역할 |
|------|---------|------|
| **복호화 키 저장** | Secure Enclave Key Box | TrustZone도 직접 접근 불가, Mailbox 요청으로만 사용 |
| **복호화 키를 Crypto Engine에 전달** | TZPC (Crypto Engine = Secure Only) | NS에서 Crypto Engine의 키 레지스터 접근 차단 |
| **복호화된 스트림 → DRAM 버퍼** | TZASC (Secure Region) | 비디오 버퍼를 Secure 영역에 할당, NS 접근 차단 |
| **비디오 디코더(HW) DMA 접근** | SMMU (Secure Stream) | 디코더 DMA가 Secure 버퍼에만 접근하도록 페이지 테이블 설정 |
| **캐시에 올라간 비디오 데이터** | Cache NS-bit | Secure 데이터의 캐시 라인은 NS 접근에 불가시 |
| **Display Engine → HDMI 출력** | TZPC + SMMU | Display Engine을 Secure Peripheral로 설정, Secure 버퍼만 읽도록 제한 |
| **Secure 인터럽트 (디코딩 완료 등)** | GIC Group 0/1S | 디코딩 완료 인터럽트를 NS에서 마스킹/가로채기 불가 |

핵심: 단일 HW 인프라가 아니라 **TZASC + SMMU + TZPC + GIC + Cache NS-bit** 전체가 협력하여 파이프라인의 모든 지점을 보호한다. 하나라도 설정이 빠지면 해당 지점에서 보안 체인이 끊긴다.
</details>

### Quiz 3. Internal Secure Enclave와 External Secure Enclave 사이에 Secure Channel Protocol이 필요한 이유를 설명하라. SPI 버스에 어떤 위협이 있는가?

<details>
<summary>정답 보기</summary>

Internal과 External Secure Enclave는 SPI 버스로 연결되는데, SPI는 SoC 외부 PCB 트레이스를 거치므로 **물리적 도청과 변조가 가능**하다.

**위협:**
1. **도청(Eavesdropping)**: 오실로스코프/로직 분석기로 SPI MOSI/MISO 신호를 캡처 → 평문 통신이면 키/비밀 데이터 유출
2. **재전송(Replay)**: 과거 정상 통신을 녹화 후 재전송 → 인증 없이 Enclave가 수용
3. **변조(Tampering)**: SPI 신호를 물리적으로 변조하여 명령/응답 위조
4. **IC 교체**: External 보안 칩 자체를 공격자가 제어하는 칩으로 물리 교체

**Secure Channel Protocol의 역할:**
- **암호화**: SPI 페이로드를 AES 등으로 암호화 → 도청 무력화
- **인증**: MAC(CMAC/HMAC)으로 메시지 무결성 + 발신자 인증 → 변조/IC 교체 감지
- **Freshness**: 세션 키 + 시퀀스 번호로 재전송 방어
- **상호 인증**: 양쪽이 서로의 정체를 검증 → 한쪽이 교체되면 인증 실패

이것은 차량 보안의 SecOC(CAN 메시지에 MAC + Freshness)와 동일한 원리를 물리 인터페이스 레벨에 적용한 것이다.
</details>

<div class="chapter-nav">
  <a class="nav-prev" href="02_world_switch_soc_infra.md">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">보안 상태 전환 & SoC 보안 인프라</div>
  </a>
  <a class="nav-next" href="03_secure_boot_connection.md">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">Secure Boot에서의 보안 레벨 적용</div>
  </a>
</div>
