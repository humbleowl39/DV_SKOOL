# Unit 3: Secure Boot에서의 보안 레벨 적용

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

## 핵심 개념
**Secure Boot = Chain of Trust(서명 검증) + Security Architecture(EL/TrustZone)의 결합. 서명 검증이 "무엇을 실행해도 되는가"를 결정하고, 보안 레벨이 "어떤 권한으로 실행하는가"를 결정. 둘이 함께 동작해야 완전한 보안.**

---

## Boot Stage별 보안 레벨 상세

```
+------------------------------------------------------------------+
| Stage | EL  | S/NS | 왜 이 레벨인가?                              |
+-------+-----+------+---------------------------------------------+
| BL1   | EL3 | S    | 최초 보안 설정(TZPC/TZASC/SCR) 권한 필요     |
|       |     |      | 다음 단계의 EL과 보안 상태를 결정해야 함      |
+-------+-----+------+---------------------------------------------+
| BL2   | S-EL1| S   | DRAM 초기화에 EL3 권한 불필요                |
|       |     |      | Secure 유지: BL3x를 Secure 메모리에 로드      |
+-------+-----+------+---------------------------------------------+
| BL31  | EL3 | S    | Secure Monitor 상주 — 런타임 월드 전환        |
|       |     |      | PSCI, SMC 처리에 EL3 필수                    |
+-------+-----+------+---------------------------------------------+
| BL32  | S-EL1| S   | TEE OS — Trusted App 관리                    |
|       |     |      | Secure 메모리/디바이스 접근 필요              |
+-------+-----+------+---------------------------------------------+
| BL33  | NS-EL1| NS | Normal 부트로더 — Secure 접근 불필요          |
|       | /EL2 |     | 이 시점에서 Secure 자원 접근 차단 시작        |
+-------+-----+------+---------------------------------------------+
| Linux | NS-EL1| NS | 일반 OS — 최소 권한 원칙                     |
+-------+-----+------+---------------------------------------------+
```

### BL1 → BL2 전환 상세

```
BL1 (BootROM, EL3):
  1. CPU Reset → PC가 BootROM 주소 → EL3 진입
  2. 보안 HW 초기화:
     - SCR_EL3 설정 (보안 정책)
     - TZPC 설정 (주변장치 보안)
     - TZASC 설정 (메모리 보안)
     - GIC 보안 설정
  3. BL2 서명 검증 (Secure Boot)
  4. BL2를 위한 환경 준비:
     - BL2 진입점 주소 설정
     - SPSR_EL3 설정 (BL2의 EL과 상태)
       SPSR_EL3.M = EL1h (S-EL1)
       SPSR_EL3.SS = Secure
     - SCR_EL3.NS = 0 유지 (Secure)
  5. ERET → S-EL1 (BL2 실행 시작)

핵심: BL1이 EL3 권한으로 SPSR/SCR을 설정하여
     BL2의 실행 EL과 보안 상태를 결정한다.
```

### BL31 → BL33 전환 (핵심 보안 경계)

```
BL31 (Secure Monitor, EL3):
  1. BL33 (U-Boot) 진입점 확인
  2. Non-Secure 전환 준비:
     - SCR_EL3.NS = 1 (Non-Secure 전환!)
     - SCR_EL3.RW = 1 (AArch64)
     - SCR_EL3.HCE = 1 (EL2 활성화, 필요 시)
     - SPSR_EL3.M = EL2h 또는 EL1h
  3. ERET → NS-EL2 또는 NS-EL1

  이 순간 이후:
    BL33/Linux는 Secure 메모리 접근 불가 (TZASC 차단)
    BL33/Linux는 Secure 디바이스 접근 불가 (TZPC 차단)
    BL33/Linux는 EL3 레지스터 접근 불가
    → SMC로 EL3에 "요청"만 가능
```

---

## Anti-Rollback — 버전 다운그레이드 방어

### 롤백 공격이란?

```
시나리오:
  FW v1.0에 취약점 발견 → v2.0에서 패치
  공격자: v1.0 이미지를 Flash에 다시 기록
  → 서명은 유효함 (v1.0도 정상 서명된 이미지)
  → Secure Boot 통과!
  → 취약한 v1.0이 다시 실행 → 공격 성공

  Secure Boot만으로는 "이전 버전" 실행을 막을 수 없음
  → 서명 = "누가 만들었는가" 검증이지, "언제 만들었는가"는 아님
```

### Monotonic Counter (Anti-Rollback Counter)

```
OTP (One-Time Programmable) 퓨즈에 단조 증가 카운터 저장:

  OTP Anti-Rollback Counter:
    +---+---+---+---+---+---+---+---+
    | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 |  = 3 (3비트 blown)
    +---+---+---+---+---+---+---+---+
    → 한번 blow된 퓨즈는 되돌릴 수 없음 (단조 증가 보장)

  부팅 시 검증:
    1. BL1(EL3)이 BL2 이미지 헤더에서 version_number 읽기
    2. OTP에서 min_version 읽기 (EL3/Secure에서만 접근 가능)
    3. if (image_version < otp_min_version) → BOOT ABORT
    4. if (image_version > otp_min_version) → OTP 카운터 업데이트
    5. 서명 검증 진행

  FW 업데이트 시:
    v2.0 → v3.0 업데이트 성공 후
    OTP 카운터: 3 → 4 (퓨즈 하나 더 blow)
    → 이후 v2.0 이하 이미지는 부팅 불가

  보안 레벨 연결:
    → OTP는 TZPC에 의해 Secure Only — NS에서 카운터 변경 불가
    → 카운터 읽기/쓰기는 EL3(BootROM)에서만 수행
    → 공격자가 NS에서 OTP 카운터를 리셋하는 것은 물리적으로 불가능
```

---

## Measured Boot & Remote Attestation

### Secure Boot vs Measured Boot

```
Secure Boot:
  검증 실패 → 실행 차단 (Gate 역할)
  "이 코드를 실행해도 되는가?" → Yes/No
  결과: 부팅 성공 또는 실패

Measured Boot:
  각 단계를 측정(해시)하여 기록 (Observer 역할)
  "어떤 코드가 실행되었는가?" → 해시 값 기록
  결과: 항상 부팅, 나중에 측정값으로 무결성 판단

  둘은 배타적이 아님 — 함께 사용:
    Secure Boot로 기본 검증 + Measured Boot로 증명 기록
```

### 측정 과정 (ARM PSA 관점)

```
Boot Stage별 측정:

  BL1 (BootROM, EL3):
    → BL1 자체는 ROM이므로 신뢰 (Immutable Root of Trust)
    → BL2 이미지의 해시 계산: H(BL2)
    → 측정값을 Secure 레지스터에 기록 (Platform Configuration)

  BL2:
    → BL31 해시 계산 → 기록: PCR = Hash(PCR_prev || H(BL31))
    → BL32 해시 계산 → 기록: PCR = Hash(PCR_prev || H(BL32))
    → BL33 해시 계산 → 기록: PCR = Hash(PCR_prev || H(BL33))

  측정값 체인:
    PCR_final = H(H(H(H(init) || H(BL2)) || H(BL31)) || H(BL32)) || H(BL33))
    → 어느 단계든 바뀌면 최종 PCR 값이 달라짐

  PCR (Platform Configuration Register):
    → TPM: 물리적 TPM 칩에 저장
    → ARM PSA: Secure World 내부 (EL3 또는 S-EL1)에 저장
    → fTPM: Firmware TPM (TEE 내에서 SW로 구현)
```

### Remote Attestation

```
서버가 디바이스의 무결성을 원격으로 검증:

  디바이스                              서버
  +------------------+                +------------------+
  | 1. 부팅 (측정)    |                |                  |
  | 2. PCR 값 확정    |                | 3. Nonce 전송    |
  |                   | ←── Nonce ──── |                  |
  | 4. Attestation    |                |                  |
  |    Token 생성:    |                |                  |
  |    Sign(PCR+Nonce |                |                  |
  |    , DeviceKey)   |                |                  |
  |                   | ──→ Token ──→  | 5. Token 검증:   |
  |                   |                |    서명 확인      |
  |                   |                |    PCR 비교      |
  |                   |                |    → 신뢰 판단   |
  +------------------+                +------------------+

  활용 사례:
    DRM: 콘텐츠 서버가 디바이스 무결성 확인 후 키 전달
    기업 보안: MDM 서버가 단말 무결성 확인 후 접속 허용
    IoT: 클라우드가 디바이스 상태 확인 후 OTA 업데이트 배포

  보안 레벨 연결:
    → DeviceKey는 Secure World(EL3 또는 S-EL1)에서만 접근 가능
    → PCR 값은 Secure 메모리에 저장 — NS에서 변조 불가
    → Token 생성은 TEE 내부에서 수행
```

---

## 보안 레벨과 공격 방어의 연결

| 공격 | 보안 레벨 방어 | 메커니즘 |
|------|-------------|---------|
| OS 해킹 → 키 탈취 | TrustZone 격리 | NS에서 Secure 메모리 접근 불가 |
| DMA 공격 | TZASC + SMMU | NS DMA가 Secure DRAM 접근 차단 |
| JTAG 디버그 | EL3 + OTP | EL3에서 JTAG 비활성화, OTP로 영구 차단 |
| Privilege Escalation | EL 계층 | EL0→EL1은 Exception만, EL1→EL3은 SMC만 |
| 악성 부트로더 | Secure Boot + EL | 서명 실패 → 실행 차단, NS 전환 전에 검증 완료 |
| TEE 앱 간 격리 | S-EL0 + S-EL1 | TEE OS가 TA 간 메모리 격리 |
| VM 탈출 | EL2 | Stage 2 Translation으로 VM 간 격리 |
| FW 롤백 | OTP Counter + EL3 | Monotonic Counter를 EL3에서 관리, 이전 버전 차단 |
| 위장 디바이스 | Measured Boot + TEE | Remote Attestation으로 무결성 증명 |

### 실제 공격 사례

```
(1) Nintendo Switch BootROM 취약점 (2018, "Fusée Gelée")
  공격: USB 복구 모드에서 BootROM의 DMA 버퍼 오버플로
    → BootROM(EL3) 코드 실행 권한 획득
    → TrustZone 설정 자체를 변경 가능 → 전체 보안 무력화
  교훈:
    → BootROM은 ROM이므로 패치 불가 — 하드웨어 리비전 필요
    → EL3 코드의 취약점 = 최고 수준 위험 (모든 보안 레벨 무력화)
    → DV 시사점: BootROM의 입력 검증 (USB, UART) 철저히 검증

(2) Qualcomm EDL (Emergency Download) 취약점 (2017~2020, 다수)
  공격: EDL 모드의 Firehose 프로그래머에서 인증 우회
    → Secure Boot 우회하여 임의 이미지 플래시
    → OTP 퓨즈 읽기까지 가능한 케이스도 존재
  교훈:
    → 복구/디버그 모드도 Secure Boot 체인에 포함해야 함
    → EDL 프로그래머의 서명 검증이 핵심
    → DV 시사점: 정상 부팅 경로뿐 아니라 복구 모드도 검증 대상

(3) ARM TrustZone 캐시 사이드 채널 (2017, "TruSpy")
  공격: Normal World에서 Flush+Reload로 Secure World 실행 패턴 관찰
    → NS-bit 태깅에도 불구하고, 타이밍 차이로 Secure 코드 실행 유추
    → AES 키 일부 비트 추출 성공
  교훈:
    → HW 격리가 타이밍 사이드 채널까지 완벽히 차단하지는 않음
    → Secure World 코드는 constant-time 구현 필요
    → DV 시사점: 실행 시간 일정성 (timing-invariant) 검증
```

---

## DV 관점 — 보안 레벨 검증

### 검증 시나리오 총괄

| # | 시나리오 | 검증 포인트 | 유형 |
|---|---------|-----------|------|
| 1 | BL1의 TZPC 초기 설정 | OTP, Crypto가 Secure Only로 설정되는가? | Positive |
| 2 | BL1의 TZASC 초기 설정 | Secure DRAM 영역이 올바르게 보호되는가? | Positive |
| 3 | BL1 → BL2 EL 전환 | SPSR_EL3가 S-EL1로 올바르게 설정되는가? | Positive |
| 4 | BL31 → BL33 NS 전환 | SCR_EL3.NS=1이 정확히 설정되는가? | Positive |
| 5 | NS에서 Secure 접근 시도 | 버스 에러 / 차단 발생하는가? | Negative |
| 6 | SMC 호출 정확성 | EL3 진입 → 서비스 처리 → 올바른 월드로 반환 | Positive |
| 7 | Anti-Rollback 검증 | 이전 버전 이미지 부팅 거부 | Negative |
| 8 | 전환 중간 상태 공격 | NS 전환 전 Secure 자원 접근 | Corner Case |
| 9 | 동시 SMC 멀티코어 | 다수 코어가 동시 SMC 호출 | Corner Case |

### 검증 방법론 상세 — Stimulus → Check → Coverage

```
시나리오 4: BL31 → BL33 NS 전환 (핵심 보안 경계)

  Stimulus:
    - BL31 코드가 BL33 entry point를 설정하고 ERET 실행
    - 테스트는 BL31의 전환 시퀀스를 트리거

  Check:
    - SCR_EL3.NS가 정확히 1로 설정되었는가?
    - SPSR_EL3.M이 NS-EL1h 또는 NS-EL2h인가?
    - ERET 후 PC가 BL33 entry point인가?
    - ERET 후 CurrentEL이 EL1 또는 EL2인가?

  Coverage:
    - cp_scr_ns_transition: {0→1, 1→0} 전환 모두 커버
    - cp_spsr_target_el: {EL1h, EL2h} 모두 커버
    - cp_bl33_entry: entry point 주소 범위 커버

시나리오 5: NS에서 Secure 접근 시도 (Negative 테스트)

  Stimulus:
    - BL33(NS-EL1) 실행 중 Secure DRAM 주소에 Load/Store 발행
    - NS DMA Master가 Secure 영역에 접근 시도
    - NS에서 TZPC-protected 레지스터 접근 시도

  Check:
    - 접근 시 버스 에러(DECERR/SLVERR) 반환되는가?
    - Data Abort Exception 발생하는가?
    - Secure 메모리 내용이 NS에 노출되지 않는가? (읽기 값 = 0 or error)
    - 시스템이 정상 계속 동작하는가? (에러가 시스템 크래시를 유발하면 안 됨)

  Coverage:
    - cp_ns_secure_access: {DRAM, OTP, Crypto, GIC_Secure} 영역별
    - cp_access_type: {Read, Write}
    - cp_response: {DECERR, SLVERR, Data_Abort}

시나리오 7: Anti-Rollback 검증

  Stimulus:
    - OTP Counter = 3인 상태에서 version=2 이미지로 부팅 시도
    - OTP Counter = 3인 상태에서 version=3 이미지로 부팅 시도 (경계값)
    - OTP Counter = 3인 상태에서 version=4 이미지로 부팅 시도

  Check:
    - version < counter: 부팅 거부 (BOOT_ABORT)
    - version == counter: 부팅 성공, OTP 변경 없음
    - version > counter: 부팅 성공, OTP 카운터 업데이트

  Coverage:
    - cp_version_vs_counter: {below, equal, above}
    - cp_otp_update: {no_update, increment}
    - cp_boot_result: {abort, success}
```

### SVA Assertion 예시

```systemverilog
// SCR_EL3.NS 전환 타이밍 검증
// NS 전환 전에 모든 Secure 초기화가 완료되었는지 확인

// TZPC 초기화 완료 전 NS 전환 금지
property p_tzpc_before_ns_switch;
  @(posedge clk) disable iff (!rst_n)
  $rose(scr_el3_ns) |-> tzpc_init_done;
endproperty
a_tzpc_before_ns: assert property (p_tzpc_before_ns_switch)
  else $error("NS switch before TZPC initialization!");

// TZASC 초기화 완료 전 NS 전환 금지
property p_tzasc_before_ns_switch;
  @(posedge clk) disable iff (!rst_n)
  $rose(scr_el3_ns) |-> tzasc_init_done;
endproperty
a_tzasc_before_ns: assert property (p_tzasc_before_ns_switch)
  else $error("NS switch before TZASC initialization!");

// NS 전환 후 Secure 메모리 접근 차단 확인
property p_ns_secure_access_blocked;
  @(posedge clk) disable iff (!rst_n)
  (scr_el3_ns && bus_req_valid && is_secure_addr(bus_req_addr))
  |-> ##[1:3] bus_resp_error;
endproperty
a_ns_blocked: assert property (p_ns_secure_access_blocked)
  else $error("NS access to Secure memory not blocked!");

// Anti-Rollback: 이전 버전 부팅 차단
property p_anti_rollback;
  @(posedge clk) disable iff (!rst_n)
  (image_version_valid && image_version < otp_min_version)
  |-> ##[1:$] boot_abort;
endproperty
a_anti_rollback: assert property (p_anti_rollback)
  else $error("Rollback image not rejected!");

// 각 assertion에 대응하는 cover property
c_ns_switch:     cover property (p_tzpc_before_ns_switch);
c_tzasc_switch:  cover property (p_tzasc_before_ns_switch);
c_ns_blocked:    cover property (p_ns_secure_access_blocked);
c_anti_rollback: cover property (p_anti_rollback);
```

---

## Q&A

**Q: Secure Boot와 TrustZone의 관계는?**
> "상호 보완적이다. Secure Boot는 '무엇을 실행해도 되는가'를 서명으로 결정한다 — 악성 코드 실행을 방지. TrustZone은 '어떤 권한으로 실행하는가'를 보안 상태로 결정한다 — 실행 중인 코드가 접근할 수 있는 범위를 제한. 둘 다 필요하다: Secure Boot 없이 TrustZone만 있으면 악성 BL32가 Secure World에서 실행될 수 있고, TrustZone 없이 Secure Boot만 있으면 검증된 코드라도 OS 해킹 시 키가 노출된다."

**Q: BL33이 Non-Secure에서 실행되는 이유는?**
> "최소 권한 원칙이다. BL33(U-Boot)과 Linux는 Secure 자원(암호 키, OTP, TEE)에 직접 접근할 필요가 없다. 필요 시 SMC로 EL3에 요청하면 된다. Non-Secure에서 실행하면 (1) OS 해킹 시 Secure 자원이 보호되고, (2) DMA/디바이스의 Secure 영역 접근이 HW적으로 차단되며, (3) 공격 표면이 최소화된다."

**Q: Anti-Rollback은 어떻게 보안 레벨과 연결되는가?**
> "OTP Monotonic Counter에 최소 허용 FW 버전을 기록한다. 이 카운터는 OTP에 저장되므로 물리적으로 되돌릴 수 없고, TZPC에 의해 Secure Only이므로 NS에서 변경이 불가능하다. BootROM(EL3)이 이미지 버전과 OTP 카운터를 비교하여 이전 버전이면 부팅을 거부한다. Secure Boot(서명 검증)가 '누가 만들었는가'를 보장하고, Anti-Rollback(버전 검증)이 '최신인가'를 보장하여 상호 보완한다."

**Q: Measured Boot와 Secure Boot의 차이는?**
> "역할이 다르다. Secure Boot는 Gate — 서명 검증 실패 시 실행을 차단한다. Measured Boot는 Observer — 각 단계의 해시를 측정하여 PCR에 누적 기록하고, 나중에 외부 서버가 이 값으로 무결성을 판단한다(Remote Attestation). Secure Boot는 로컬에서 즉시 판단하고, Measured Boot는 원격에서 사후 판단한다. 실무에서는 둘 다 적용: Secure Boot로 기본 검증 + Measured Boot로 증명 기록을 생성한다."

**Q: DV에서 보안 레벨 전환을 어떻게 검증하는가?**
> "Positive와 Negative 테스트를 모두 수행한다. Positive: BL1→BL2(S-EL1) 전환 시 SPSR_EL3, SCR_EL3 설정이 올바른지 확인. BL31→BL33 전환 시 SCR_EL3.NS=1 설정 확인. Negative: NS 전환 후 Secure 메모리/디바이스 접근 시 버스 에러 발생 확인. SVA로 '보안 초기화 완료 전 NS 전환 금지', 'NS 상태에서 Secure 접근 차단' 같은 프로토콜 규칙을 상시 모니터링한다. Corner case로 멀티코어 동시 SMC, 전환 중간 인터럽트 등을 검증한다."

---

## 확인 문제

**문제 1: Anti-Rollback 시나리오 분석**
> OTP Counter 값이 5인 디바이스에 대해, 다음 각 경우의 부팅 결과와 OTP 상태 변화를 설명하라.
> - (A) version=4 이미지로 부팅 시도
> - (B) version=5 이미지로 부팅 시도
> - (C) version=7 이미지로 부팅 시도 후 성공, 다시 version=5로 부팅 시도

<details>
<summary>풀이 과정</summary>

**사고 과정:**
Anti-Rollback 규칙: image_version < otp_counter → 거부, >= → 허용, > → 카운터 업데이트

**(A) version=4, OTP=5:**
- 4 < 5 → **부팅 거부** (BOOT_ABORT)
- OTP 변경 없음 (여전히 5)
- 이유: 취약한 이전 버전 실행 방지

**(B) version=5, OTP=5:**
- 5 == 5 → 서명 검증 진행 → 서명 유효하면 **부팅 성공**
- OTP 변경 없음 (동일 버전이므로 카운터 증가 불필요)

**(C) version=7, OTP=5 → 성공 후 version=5 재시도:**
- 7 > 5 → 부팅 성공, OTP 카운터 5 → 7로 업데이트
- 이후 version=5로 부팅 시도: 5 < 7 → **부팅 거부**
- 핵심: 한번 올라간 OTP 카운터는 되돌릴 수 없음 (OTP = One-Time Programmable)

**DV 검증 포인트:**
- 경계값 테스트: version == counter (정확히 같은 경우)
- OTP 업데이트 시 정확한 값 기록 확인
- 업데이트 중 전원 차단 → OTP 상태 일관성 (power-fail safety)
</details>

**문제 2: Secure Boot + TrustZone 결합 시나리오**
> 다음 두 공격 시나리오 각각에서, Secure Boot만 있고 TrustZone이 없는 경우와, TrustZone만 있고 Secure Boot가 없는 경우의 결과를 비교하라.
> - (A) 공격자가 서명되지 않은 악성 BL32(TEE) 이미지를 플래시에 기록
> - (B) 정상 부팅 후, Linux 커널 취약점을 통해 Secure DRAM의 암호 키를 탈취 시도

<details>
<summary>풀이 과정</summary>

**(A) 악성 BL32 이미지:**

| 방어 | 결과 |
|------|------|
| Secure Boot만 | 서명 검증 실패 → 실행 차단 (**방어 성공**) |
| TrustZone만 | 서명 검증 없음 → 악성 BL32가 S-EL1에서 실행! → Secure World 내부에서 동작하므로 **모든 Secure 자원 접근 가능** (**방어 실패**) |
| 둘 다 | 서명 실패로 실행 차단 (**방어 성공**) |

**(B) Linux 해킹 후 Secure DRAM 접근:**

| 방어 | 결과 |
|------|------|
| Secure Boot만 | 부팅 시 검증은 통과 (정상 이미지), 런타임에 커널 해킹 → Secure DRAM 직접 접근 가능 (격리 없음) (**방어 실패**) |
| TrustZone만 | NS에서 Secure DRAM 접근 → TZASC 차단 → 버스 에러 (**방어 성공**) |
| 둘 다 | TZASC 차단 (**방어 성공**) |

**핵심 결론:**
- Secure Boot = 부팅 시점 보호 (무엇을 실행하는가)
- TrustZone = 런타임 보호 (실행 중 접근 권한)
- 둘 다 있어야 완전한 보안: 부팅 시 + 런타임 모두 방어
</details>

**문제 3: DV 검증 설계 — SVA 작성**
> "NS 전환(SCR_EL3.NS rising) 후 10 사이클 이내에 NS Master가 Secure DRAM에 접근하면, 반드시 버스 에러가 발생해야 한다"는 요구사항에 대한 SVA assertion을 작성하라.

<details>
<summary>풀이 과정</summary>

**사고 과정:**
1. 트리거: SCR_EL3.NS가 0→1로 전환 ($rose)
2. 조건: 이후 NS Master가 Secure 주소에 접근
3. 체크: 접근이 있으면 에러 응답이 나와야 함
4. 시간 범위: NS 전환 후 전체 기간 (10 사이클만이 아니라 영구적)

**주의:** 문제의 "10 사이클 이내"는 트리거가 아니라 응답 지연을 의미할 수 있음. 두 가지 해석 모두 작성:

```systemverilog
// 해석 1: NS 전환 후 Secure 접근이 발생하면 반드시 에러
property p_ns_secure_access_always_blocked;
  @(posedge clk) disable iff (!rst_n)
  (scr_el3_ns && bus_req_valid && !bus_req_ns &&
   is_secure_region(bus_req_addr))
  |-> ##[1:10] bus_resp_error;
endproperty

// 해석 2: NS 전환 직후 10사이클 window에서 특히 검증
//          (전환 직후 race condition 검출 목적)
property p_ns_switch_immediate_protection;
  @(posedge clk) disable iff (!rst_n)
  $rose(scr_el3_ns) |->
    ##[1:10] (!bus_req_valid || !is_secure_region(bus_req_addr)
              || bus_resp_error)[*1:$];
endproperty

// Cover: 실제로 이 시나리오가 시뮬레이션에서 발생하는지
c_ns_access_blocked: cover property (p_ns_secure_access_always_blocked);
```

**핵심 포인트:**
- `is_secure_region()` 함수가 TZASC 설정을 반영해야 함
- `bus_req_ns` 신호로 Master의 NS 상태 확인
- 응답 지연(##[1:10])은 버스 파이프라인 딜레이 고려
- Cover property로 assertion이 vacuously true가 아닌지 확인
</details>

<div class="chapter-nav">
  <a class="nav-prev" href="02a_secure_enclave_and_tee_hierarchy.md">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">Unit 2A: Secure Enclave & TEE 계층 구조</div>
  </a>
  <a class="nav-next" href="04_quick_reference_card.md">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">ARM Security Architecture — Quick Reference Card</div>
  </a>
</div>
