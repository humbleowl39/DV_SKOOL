# Unit 2: Chain of Trust & Boot Stages (신뢰 체인과 부팅 단계)

<div class="learning-meta">
  <span class="meta-badge meta-time">⏱ 16분</span>
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

## 핵심 개념
**Chain of Trust = 각 단계가 다음 단계를 인증한 후에만 제어권을 넘긴다. 신뢰는 전파되는 것이지, 생성되는 것이 아니다. 어떤 단계가 침해되면 그 이후의 모든 것은 무효.**

---

## 왜 단계를 나누는가?

| 이유 | 설명 |
|------|------|
| 메모리 제약 | BL1은 SRAM만 사용 (DRAM 미초기화). 크기 제한 → 최소 기능만 |
| 보안 경계 | 각 단계마다 다른 권한 레벨 (Secure → Non-Secure 전환) |
| 업데이트 유연성 | BL1(ROM) 변경 불가, 그러나 BL2/BL3는 Flash에서 업데이트 가능 |
| 장애 격리 | BL2 문제 → BL1이 복구 가능. 단일체 → 완전 벽돌(brick) |

---

## ARM Trusted Firmware 부팅 단계

```
+----------------------------------------------+
| BL1 (BootROM)          | 저장: Mask ROM      |
|                         | 메모리: Internal SRAM|
| - CPU 초기화            | 권한: Secure EL3    |
| - 보안 HW 초기화        | 크기: 수십~수백 KB  |
| - Boot Device 접근      |                     |
| - BL2 로드 + 검증       | ← ROTPK 사용       |
| - BL2로 Jump            |                     |
+------------+------------+---------------------+
             |
             v
+----------------------------------------------+
| BL2 (FSBL)             | 저장: Flash/UFS     |
|                         | 메모리: SRAM → DRAM |
| - DRAM 컨트롤러 초기화  | 권한: Secure EL1    |
| - 추가 HW 초기화        | 크기: 수 MB까지     |
| - BL31/32/33 로드+검증  |                     |
| - Secure World 설정     |                     |
+-----+--------+---------+---------------------+
      |        |         |
      v        v         v
+---------+--------+---------+
| BL31    | BL32   | BL33    |
| Secure  | Secure | Non-Sec |  모두 DRAM에서 실행
| Monitor | OS(TEE)| Bootldr |
| (ATF)   | OP-TEE | U-Boot  |
| EL3     | S-EL1  | NS-EL1/2|
+---------+--------+----+----+
                        |
                        v
                  +-----------+
                  | OS (Linux,|  Normal World
                  |  Android) |  NS-EL1
                  +-----------+
```

---

## 단계별 요약 테이블

| 단계 | 저장 위치 | 실행 메모리 | Exception Level | 핵심 역할 | 업데이트? |
|------|----------|-----------|-----------------|----------|----------|
| BL1 | Mask ROM | Internal SRAM | Secure EL3 | HW 초기화 + BL2 인증 | 불가 (ROM Patch만) |
| BL2 | Flash/UFS | SRAM → DRAM | Secure EL1 | DRAM 초기화 + BL3x 인증 | 가능 |
| BL31 | Flash/UFS | DRAM | Secure EL3 | Secure Monitor (SMC) | 가능 |
| BL32 | Flash/UFS | DRAM | Secure EL1 | TEE OS (OP-TEE) | 가능 |
| BL33 | Flash/UFS | DRAM | Non-Secure EL1/2 | Normal 부트로더 | 가능 |

**메모리 흐름 한줄 정리**:
```
BL1 ---- BL2 ---- BL31 + BL32 + BL33
init     DRAM     Secure  TEE   Normal
+auth    +auth    Monitor OS    Bootloader
(ROM)   (SRAM→DRAM) (EL3) (S-EL1) (NS-EL1)
```

---

## 인증서 체인 — 인증 전파 구조

```
OTP (eFuse)
  |  ROTPK Hash
  v
Root Certificate        ← ROTPK로 서명됨
  |  Root Key가 검증
  v
Trusted Key Certificate ← Root Key로 서명됨
  |       |
  v       v
BL2 Cert  BL3 Cert     ← 각각의 키로 서명됨
(BL2 해시) (BL33 해시)
```

### BL2 검증 시퀀스 (상세)

1. OTP에서 ROTPK 해시 읽기
2. Root Certificate의 공개키를 해시 → OTP 해시와 비교
3. 일치 → Root Key로 Trusted Key Certificate의 서명 검증
4. Trusted Key로 BL2 Content Certificate의 서명 검증
5. Certificate 내의 BL2 해시와 실제 BL2 이미지 해시 비교
6. 모두 통과 → BL2 실행 허용

**왜 다중 계층 인증서인가?** 키 교체(Key Rotation)와 폐기(Revocation)를 위해서. ROTPK가 직접 이미지를 서명하면, 키 침해 시 OTP를 변경해야 하는데 이는 불가능하다. 중간 키를 두면 ROTPK를 건드리지 않고도 키를 교체할 수 있다.

---

## 침해 시 영향 범위 (Blast Radius)

```
BL1 침해  → 전체 시스템 (최악의 경우)
BL2 침해  → Secure + Non-Secure 전부
BL31 침해 → Secure Monitor → TrustZone 붕괴
BL32 침해 → TEE만 영향 (Normal World 안전)
BL33 침해 → Normal World만 (Secure World 안전)

앞 단계일수록 = 높은 보안 요구사항
→ 그래서 BL1이 ROM에 있는 것!
```

**핵심 원리**: Chain of Trust는 단방향이다. Stage N이 침해되면 N+1 이후 모든 단계가 신뢰할 수 없게 된다 — 검증자 자체가 오염되었기 때문. 그러나 N 이전 단계는 안전하다. 이것이 단계 분리의 또 다른 이유 — 피해 범위 제한.

---

## Secure Boot vs Verified Boot vs Measured Boot

면접에서 자주 혼동되는 세 가지 부팅 보안 개념. **서로 다른 것을 보장한다.**

| | Secure Boot | Verified Boot | Measured Boot |
|--|-------------|--------------|---------------|
| **핵심 질문** | "이 코드가 **신뢰할 수 있는가?**" | "이 코드가 **예상한 것인가?**" | "이 코드가 **무엇인지 기록했는가?**" |
| **동작** | 서명 검증 실패 → **부팅 중단** | 해시 검증 실패 → **부팅 중단 또는 경고** | 해시를 측정하여 **기록만 함** (중단 안 함) |
| **판단 시점** | 부팅 시 (로컬) | 부팅 시 (로컬) | 부팅 후 (원격 검증자가 판단) |
| **신뢰 근거** | 서명 키 소유자 (제조사) | 기대 해시값 (dm-verity 등) | 외부 검증자 (Remote Attestation) |
| **실패 시** | 부팅 거부 (hard fail) | 부팅 거부 또는 경고 (설정에 따라) | 부팅은 진행, 원격 서비스가 거부 가능 |
| **대표 구현** | ARM TF Secure Boot, UEFI Secure Boot | Android Verified Boot (AVB), Chrome OS | TPM PCR, ARM PSA Attestation, DICE |

```
Secure Boot:    [서명 검증] → PASS → 실행 | FAIL → 중단!
                 "인가된 코드만 실행"

Verified Boot:  [해시 검증] → PASS → 실행 | FAIL → 중단 또는 경고
                 "변조되지 않은 코드만 실행"

Measured Boot:  [해시 측정] → 기록(PCR) → 항상 실행
                 "무엇이 실행되었는지 증명 가능"
                      ↓
                 Remote Attestation: 외부가 PCR 값으로 신뢰 판단
```

### 실무에서는 조합하여 사용

```
BL1 (BootROM)  → Secure Boot (서명 검증, 실패 시 중단)
BL2 (FSBL)     → Secure Boot + Measured Boot (검증 + 측정 기록)
BL33 (U-Boot)  → Verified Boot (dm-verity로 파티션 무결성)
OS (Linux)     → Measured Boot (IMA/TPM으로 런타임 측정)
```

**면접 답변 프레임**: "Secure Boot는 '실행 자격'을 검증하고, Verified Boot는 '무결성'을 검증하며, Measured Boot는 '무엇이 실행되었는지'를 기록한다. 실무에서는 이 셋을 계층적으로 조합한다."

---

## Measured Boot & Remote Attestation

### Measured Boot — TPM PCR (Platform Configuration Register)

```
부팅 과정에서 각 단계를 "측정"하여 TPM의 PCR에 기록:

  BL1 실행 전:
    PCR[0] = SHA-256(BL1 코드)

  BL2 실행 전:
    PCR[1] = SHA-256(PCR[1]_old || SHA-256(BL2 코드))
                       ↑ Extend 연산: 이전 값과 연쇄
                       → 개별 측정값 위조 불가 (해시 체인)

  BL3x 실행 전:
    PCR[2] = Extend(PCR[2], SHA-256(BL31))
    PCR[3] = Extend(PCR[3], SHA-256(BL32))

  OS 실행 후:
    PCR[4..7] = OS 커널, 드라이버, 설정 등
```

### PCR Extend가 중요한 이유

| 방식 | 동작 | 문제 |
|------|------|------|
| 단순 덮어쓰기 | PCR = Hash(BL2) | 공격자가 나중에 원하는 값으로 교체 가능 |
| **Extend** | PCR = Hash(PCR_old ∥ new_data) | 이전 값에 의존 → 과거 측정을 위조할 수 없음 |

### Remote Attestation — 원격 신뢰 판단

```
디바이스                              검증 서버 (Verifier)
   |                                      |
   | 1. Attestation 요청                   |
   | <──────────────────────────────────── |
   |                                      |
   | 2. TPM이 PCR 값에 서명 (AIK 키 사용)  |
   |    Quote = Sign(PCR[0..7], Nonce)     |
   |                                      |
   | 3. Quote 전송                         |
   | ──────────────────────────────────→   |
   |                                      |
   |    4. 서버가 PCR 값을 "기대 값"과 비교  |
   |       일치 → "이 디바이스는 정상 부팅"  |
   |       불일치 → 서비스 접근 거부         |
```

### DICE (Device Identifier Composition Engine) — 경량 대안

TPM이 없는 경량 IoT 디바이스를 위한 TCG 표준:

| | TPM 기반 | DICE 기반 |
|--|---------|----------|
| HW 요구사항 | TPM 칩 (별도 IC) | 소량의 HW 로직 (UDS + CDI 도출) |
| 비용 | 높음 | 낮음 |
| 적합 대상 | PC, 서버, 고급 SoC | IoT, MCU, 저가 SoC |
| 측정 방식 | PCR Extend | CDI (Compound Device Identifier) 체인 |

```
DICE 동작:
  UDS (Unique Device Secret) ← HW에 고정 (OTP/PUF)
       │
       v
  CDI_BL1 = KDF(UDS, Hash(BL1))   ← BL1의 ID
       │
       v
  CDI_BL2 = KDF(CDI_BL1, Hash(BL2))  ← BL1+BL2의 ID
       │
       v
  각 단계의 CDI가 이전 단계에 의존 → 체인 무결성
```

---

## BL2의 DRAM Training — 왜 복잡한가?

BL2의 가장 중요한 역할은 DRAM 컨트롤러 초기화이다. 이것이 왜 별도 단계가 필요할 만큼 복잡한지 이해해야 한다.

### DRAM Training이란?

```
DRAM 컨트롤러 ←── 고속 데이터 버스 ──→ DRAM 칩 (DDR4/5, LPDDR4/5)
                  수 GHz 동작
                  ↑
        이 버스의 타이밍을 정밀하게 맞추는 과정 = Training
```

### 왜 Training이 필요한가?

| 요인 | 문제 | 영향 |
|------|------|------|
| **PVT 변동** | 공정(Process), 전압(Voltage), 온도(Temperature) 편차 | 칩마다 최적 타이밍이 다름 |
| **보드 레이아웃** | PCB 배선 길이, 임피던스 불일치 | 신호 도달 시간 편차 |
| **DRAM 칩 편차** | 제조사/로트별 특성 차이 | 동일 설계여도 타이밍 마진 다름 |
| **고속 동작** | DDR5 4800MT/s → 1비트 = ~208ps | 수십 ps 오차도 데이터 손상 |

### Training 시퀀스 (간략화)

```
BL2 DRAM 초기화 단계:

1. DRAM 컨트롤러 레지스터 기본 설정
   - 주파수, CAS Latency, Bank 구조 등

2. ZQ Calibration
   - 출력 임피던스를 기준 저항에 맞춤
   - PVT 보상의 첫 단계

3. Write Leveling
   - DQS (스트로브)와 CK (클럭) 정렬
   - 보드 배선 차이 보상

4. Read/Write Training (Gate Training, Eye Training)
   - 데이터 eye의 중심을 찾아 샘플링 포인트 최적화
   - 각 바이트 레인별 독립 수행
   +-----------+
   |  ╱╲  ╱╲  |  ← Data Eye Diagram
   | ╱  ╲╱  ╲ |     중심에서 샘플링해야 안정적
   |←─ margin─→|
   +-----------+

5. CA (Command/Address) Training
   - 명령/주소 버스 타이밍 정렬

6. VREF Training
   - 기준 전압 최적화 (DDR4/5의 Decision Feedback EQ)

소요 시간: 수십~수백 ms (부팅 시간의 상당 부분 차지)
```

### 왜 BootROM(BL1)에서 하지 않는가?

| 이유 | 설명 |
|------|------|
| **코드 크기** | Training 코드만 수십~수백 KB → ROM 면적 부담 |
| **DRAM 종류 다양성** | DDR4, LPDDR4, DDR5, LPDDR5 각각 다른 Training → ROM에 모두 포함 불가 |
| **버그 수정 불가** | Training 알고리즘 버그 → ROM 수정 불가 = 실리콘 재작업 |
| **업데이트 필요** | 새 DRAM 벤더/칩 지원을 위해 Training 파라미터 업데이트 필요 |

**핵심 정리**: "DRAM Training은 PVT 변동과 보드 특성을 보상하여 수 GHz 데이터 버스의 타이밍 마진을 확보하는 과정이다. 코드 크기와 업데이트 필요성 때문에 BL1(ROM)이 아닌 BL2(Flash, 업데이트 가능)에서 수행한다."

---

## Exception Level과 보안 아키텍처

```
+----------------------------------------------------+
|                  ARM Exception Levels               |
|                                                     |
|  EL3 (Secure Monitor)                               |
|    - 최고 권한, Secure/Non-Secure 전환 관리          |
|    - BL1(BootROM), BL31(ATF) 실행                   |
|    - SMC (Secure Monitor Call)로 진입                |
|                                                     |
|  EL2 (Hypervisor)                                   |
|    - VM 관리 (Non-Secure 측)                        |
|    - Secure EL2는 ARMv8.4-A부터 지원               |
|                                                     |
|  S-EL1 (Secure OS)        | NS-EL1 (Normal OS)     |
|    - BL32 (OP-TEE)        | - Linux, Android       |
|    - Trusted App 실행     | - BL33 (U-Boot)        |
|                                                     |
|  S-EL0 (Secure App)       | NS-EL0 (User App)      |
|    - TA (Trusted App)     | - 일반 앱              |
+----------------------------------------------------+
```

**면접 팁**: 화이트보드에 Boot Stage를 그릴 때 Exception Level(EL3/S-EL1/NS-EL1)을 반드시 함께 표시하라. 대부분의 지원자가 이를 생략하는데, 포함하면 ARM 보안 아키텍처에 대한 깊은 이해를 즉시 보여줄 수 있다.

---

## Q&A

**Q: BL1에서 직접 OS를 로드하지 않는 이유는?**
> "BL1은 SRAM에서만 실행된다 — DRAM이 초기화되지 않은 상태이기 때문이다. SRAM은 수십~수백 KB로 제한된다. DRAM 초기화에는 복잡한 Training 시퀀스가 필요하므로, 별도의 BL2 단계가 이를 처리한다."

**Q: Chain of Trust의 한 단계가 침해되면?**
> "Chain of Trust는 단방향이다. Stage N이 침해되면 N+1 이후 모든 단계가 신뢰할 수 없다 — 검증자 자체가 오염되었으므로. 그러나 N 이전 단계는 안전하다. 이것이 단계 분리의 또 다른 이유 — 피해 범위(Blast Radius) 제한."

**Q: 왜 화이트보드에 Exception Level을 그려야 하는가?**
> "ARM 보안 아키텍처에 대한 이해를 보여준다. 대부분의 지원자가 EL을 생략하는데, EL3/S-EL1/NS-EL1을 포함하면 보안 경계와 권한 분리를 이해하고 있음을 즉시 증명한다."

**Q: Secure Boot와 Measured Boot의 차이는?**
> "Secure Boot는 '실행 자격'을 검증한다 — 서명이 유효하지 않으면 부팅을 중단한다. Measured Boot는 '무엇이 실행되었는지'를 TPM PCR에 기록만 하고 부팅은 진행한다 — 나중에 Remote Attestation으로 외부 검증자가 신뢰를 판단한다. 실무에서는 BootROM(BL1)에서 Secure Boot로 강제 검증하고, 이후 단계에서 Measured Boot를 추가로 수행하여 두 방식을 조합한다."

**Q: BL2에서 DRAM Training을 수행하는 이유는?**
> "DRAM Training은 PVT 변동과 보드 배선 차이를 보상하여 수 GHz 데이터 버스의 타이밍 마진을 확보하는 과정이다. 코드만 수십~수백 KB에 달하고, DRAM 종류(DDR4/5, LPDDR4/5)별로 알고리즘이 다르며, 새 DRAM 벤더 지원을 위해 업데이트가 필요하다. BL1(ROM)에 넣으면 크기 부담 + 버그 수정 불가이므로, BL2(Flash, 업데이트 가능)에서 수행한다."

<div class="chapter-nav">
  <a class="nav-prev" href="01_hardware_root_of_trust.md">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">Hardware Root of Trust (하드웨어 신뢰 기반)</div>
  </a>
  <a class="nav-next" href="03_crypto_in_boot.md">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">Secure Boot 암호학 — 서명 검증과 키 관리</div>
  </a>
</div>
