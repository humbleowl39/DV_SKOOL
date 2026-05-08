# Module 06 — BootROM DV Methodology

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="soc">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🔐</span>
    <span class="chapter-back-text">SoC Secure Boot</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 06</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#핵심-개념">핵심 개념</a>
  <a class="page-toc-link" href="#legacy-환경의-문제-왜-바꿔야-했는가">Legacy 환경의 문제 — 왜 바꿔야 했는가</a>
  <a class="page-toc-link" href="#uvm-프레임워크-전환-아키텍처">UVM 프레임워크 전환 — 아키텍처</a>
  <a class="page-toc-link" href="#otp-abstraction-layer-ral-모델링">OTP Abstraction Layer — RAL 모델링</a>
  <a class="page-toc-link" href="#active-uvm-driver-결정론적-보안-테스트">Active UVM Driver — 결정론적 보안 테스트</a>
  <a class="page-toc-link" href="#dpi-c-hwsw-co-verification">DPI-C HW/SW Co-verification</a>
  <a class="page-toc-link" href="#coverage-driven-검증-전략">Coverage-Driven 검증 전략</a>
  <a class="page-toc-link" href="#환경-포팅-전략-applemeta-프로젝트">환경 포팅 전략 — Apple/Meta 프로젝트</a>
  <a class="page-toc-link" href="#post-silicon-연결-pre-silicon-검증이-bring-up을-가속하는-이유">Post-Silicon 연결 — Pre-silicon 검증이 Bring-up을 가속하는 이유</a>
  <a class="page-toc-link" href="#면접-종합-qa">면접 종합 Q&A</a>
  <a class="page-toc-link" href="#핵심-정리">핵심 정리</a>
  <a class="page-toc-link" href="#코스-마무리">코스 마무리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Design** BootROM DV 환경 (UVM env + virtual sequencer + functional coverage)
    - **Apply** Boot scenario matrix (boot mode × OTP config × image variant) 닫는 전략
    - **Implement** Golden image + corrupted/unsigned image error injection
    - **Plan** Coverage-driven verification으로 Zero-Defect Silicon 달성

!!! info "사전 지식"
    - [Module 01-05](01_hardware_root_of_trust.md)
    - [UVM](../../uvm/), [AMBA](../../amba_protocols/)

!!! tip "💡 이해를 위한 비유"
    **BootROM DV** ≈ **발전소 검수원 — 모든 부팅 path 를 stopwatch 로 검증, 한 path 라도 빠지면 sign-off X**

    ROM 은 변경 불가이므로 검증이 마지막 chance. ROTPK fuse, anti-rollback, fall-back path, ROM patch 등 모든 path 검증.

---

## 핵심 개념
**BootROM 검증 = 이론(Unit 1~5)을 실제 실리콘 품질로 전환하는 엔지니어링. Legacy SV 환경의 한계를 UVM 프레임워크로 극복하고, Coverage-Driven 방법론으로 Zero-Defect Silicon을 달성하는 과정.**

!!! danger "❓ 흔한 오해"
    **오해**: BootROM 검증 = 정상 boot 만 확인

    **실제**: 추가로 ROM patch 적용 후 chain 재검증, fail-safe boot, error path, JTAG isolation, side-channel 등 광범위.

    **왜 헷갈리는가**: "정상 boot 만 본다" 는 sim mindset. 보안에서는 abnormal path 가 attack surface.
---

## Legacy 환경의 문제 — 왜 바꿔야 했는가

### 기존 환경 (Legacy SystemVerilog TB)

```
Legacy BootROM TB:

  +--------------------+
  | Testbench Top      |
  |                    |
  |  DUT (BootROM SoC) |
  |       |            |
  |  Passive Monitor   |  ← 신호만 관찰, 능동적 제어 불가
  |       |            |
  |  Manual force/     |  ← 테스트마다 수동으로 force 문 삽입
  |  release 삽입      |     (OTP 값, 부팅 설정, 에러 주입 등)
  |       |            |
  |  $display 기반     |  ← 체계적 비교/검증 없음
  |  디버그            |
  +--------------------+
```

### 3가지 근본 문제

| 문제 | 증상 | 근본 원인 |
|------|------|----------|
| **1-2개월 검증 병목** | FW 전달 지연으로 검증 시작 불가 | FW 지연이 아닌, 환경 재사용성 부족이 진짜 원인 |
| **Passive 모니터링의 한계** | 보안 공격 시나리오 재현 불가 | 능동적 자극(stimulus) 생성 능력 없음 |
| **수동 force 문 삽입** | 새 테스트마다 force 문 수작업 → 에러 빈발 | OTP/보안 설정의 추상화 부재 |

**핵심 인사이트**: "병목의 진짜 원인은 FW 지연이 아니라 환경의 재사용성과 추상화 부족이었다." — 이 분석 자체가 면접에서 문제 해결 능력을 보여주는 강력한 포인트.

---

## UVM 프레임워크 전환 — 아키텍처

### 전환 후 환경 구조

```
+------------------------------------------------------------------+
|                    UVM BootROM Verification Env                    |
|                                                                   |
|  +------------------+  +------------------+  +------------------+ |
|  | OTP Agent        |  | Boot Device Agent|  | Security Agent   | |
|  |                  |  |                  |  |                  | |
|  | OTP Abstraction  |  | UFS Driver       |  | Active Driver    | |
|  | Layer (RAL 방식) |  | eMMC Driver      |  | (force/release)  | |
|  |                  |  | USB Driver       |  |                  | |
|  | - Field 접근     |  | SDMMC Driver     |  | - FI 시뮬레이션  | |
|  | - Config sweep   |  |                  |  | - TOCTOU 재현    | |
|  | - 물리주소 은닉  |  | - 정상 이미지    |  | - JTAG 시도      | |
|  |                  |  | - 변조 이미지    |  | - 결과 flip      | |
|  +--------+---------+  +--------+---------+  +--------+---------+ |
|           |                     |                      |          |
|           v                     v                      v          |
|  +------------------------------------------------------------+  |
|  |              Virtual Sequence (시나리오 조합)                |  |
|  |  예: OTP(Secure Boot ON) + UFS(정상 이미지) + FI(글리치)    |  |
|  +------------------------------------------------------------+  |
|           |                                                       |
|           v                                                       |
|  +------------------------------------------------------------+  |
|  |                    Scoreboard / Checker                      |  |
|  |  - Boot 성공/실패 판정                                      |  |
|  |  - 예상 동작 vs 실제 동작 비교                               |  |
|  |  - DPI-C Reference Model 연동                               |  |
|  +------------------------------------------------------------+  |
|           |                                                       |
|           v                                                       |
|  +------------------------------------------------------------+  |
|  |              Functional Coverage Model                       |  |
|  |  - Boot Mode × Boot Device 교차 커버리지                    |  |
|  |  - Secure Boot ON/OFF × 이미지 유형 (정상/변조)             |  |
|  |  - 공격 카테고리별 Negative 시나리오 커버리지                 |  |
|  +------------------------------------------------------------+  |
+------------------------------------------------------------------+
```

### Legacy → UVM 전환 효과

| 항목 | Legacy SV | UVM Framework |
|------|-----------|---------------|
| 새 테스트 추가 | 전체 force 문 재작성 (수 일) | Sequence 조합만 변경 (수 시간) |
| OTP 설정 변경 | 물리 주소 하드코딩 수정 | Abstraction Layer 필드명으로 접근 |
| 보안 공격 시나리오 | 수동 force 삽입, 비결정론적 | Active Driver로 결정론적 재현 |
| 검증 완료 판정 | 엔지니어 주관적 판단 | Coverage 수치 기반 객관적 판정 |
| 다른 프로젝트 포팅 | 전면 재작성 (수 주) | Config 변경 + Agent 재사용 (수 일) |
| 검증 병목 | 1-2개월 | **1개월 이상 단축** |

---

## OTP Abstraction Layer — RAL 모델링

### 왜 필요한가?

```
문제: OTP 물리 주소 직접 참조

  // Legacy: 테스트마다 이런 코드
  force dut.otp_ctrl.mem[0x100] = 32'hDEAD_BEEF;  // ROTPK hash[0]
  force dut.otp_ctrl.mem[0x104] = 32'h1234_5678;  // ROTPK hash[1]
  ...
  force dut.otp_ctrl.mem[0x200] = 32'h0000_0001;  // Secure Boot Enable
  force dut.otp_ctrl.mem[0x204] = 32'h0000_0003;  // Boot Device = UFS

  → OTP 맵이 바뀌면? 모든 테스트의 주소를 수동 수정
  → 주소 오타 하나면? 잘못된 필드에 값 설정 → 디버그 지옥
```

### 해결: OTP Abstraction Layer

```
+----------------------------------------------+
|          OTP Abstraction Layer                 |
|                                               |
|  OTP Map Parser (OTP 맵 데이터 파싱)           |
|    입력: OTP Map 문서/CSV/JSON                |
|    출력: 필드별 Sequence Item 자동 생성        |
|                                               |
|  +------------------------------------------+ |
|  | OTP Field Model (RAL 스타일)              | |
|  |                                          | |
|  |  rotpk_hash[7:0]    : 256-bit 해시       | |
|  |  secure_boot_en     : 1-bit 플래그        | |
|  |  boot_device_cfg    : 3-bit 열거형        | |
|  |  jtag_disable       : 1-bit 플래그        | |
|  |  anti_rollback_cnt  : 32-bit 카운터       | |
|  |  ...                                     | |
|  +------------------------------------------+ |
|                                               |
|  사용법:                                      |
|    otp_model.secure_boot_en.set(1);           |
|    otp_model.boot_device_cfg.set(UFS);        |
|    otp_model.rotpk_hash.set(expected_hash);   |
|    → 물리 주소 자동 매핑, 테스트는 의미만 기술 |
+----------------------------------------------+
```

### OTP Abstraction의 핵심 가치

| 가치 | 설명 |
|------|------|
| 물리 주소 은닉 | 테스트가 주소를 몰라도 됨 → OTP 맵 변경에 면역 |
| 필드 레벨 접근 | `secure_boot_en`처럼 의미 있는 이름으로 접근 |
| 자동 sweep | Boot Mode × Boot Device × Secure Boot 조합 자동 생성 |
| 재사용성 | OTP 맵만 교체하면 다른 SoC에 즉시 적용 (Apple/Meta 포팅의 핵심) |
| 실수 방지 | 잘못된 주소 접근을 컴파일 타임에 검출 가능 |

### 면접 답변 준비

**Q: OTP Abstraction Layer를 왜 RAL 방식으로 설계했나?**
> "UVM RAL이 레지스터 주소를 추상화하듯, OTP의 물리적 비트 위치를 추상화했다. OTP는 레지스터와 달리 read/write가 아닌 program-once 특성이 있고, 필드 간 의존성(예: Secure Boot Enable이 OFF면 ROTPK Hash가 무의미)이 복잡하다. Abstraction Layer가 이 의존성을 모델링하여, 유효한 OTP 설정 조합만 자동으로 생성하게 했다. 이로 인해 OTP 맵이 변경되어도 테스트 코드 수정 없이 맵 파서만 업데이트하면 된다."

---

## Active UVM Driver — 결정론적 보안 테스트

### Passive vs Active 비교

```
Passive (Legacy):
  Monitor ← DUT 신호 관찰만
  "무엇이 일어났는지"만 확인 가능
  보안 공격을 "재현"할 수 없음

Active (UVM):
  Driver → DUT에 능동적으로 자극 주입
  "특정 공격 벡터를 정확히 재현" 가능
  결정론적 → 같은 시나리오를 반복 재현 가능
```

### Active Driver의 force/release 메커니즘

```
+--------------------------------------------------+
|  Security Agent — Active Driver                   |
|                                                   |
|  Sequence Item 예시:                              |
|                                                   |
|  class security_attack_item extends uvm_seq_item; |
|    attack_type_e  attack;     // FI, TOCTOU, etc |
|    int            target_time; // 공격 시점       |
|    string         target_path; // force 대상 경로 |
|    logic [31:0]   force_value; // 주입 값         |
|  endclass                                         |
|                                                   |
|  Driver 동작:                                     |
|    1. 시퀀스에서 공격 아이템 수신                  |
|    2. target_time까지 대기                        |
|    3. force(target_path, force_value) 실행        |
|    4. 지정된 사이클 후 release                     |
|    5. DUT 반응 관찰 (abort? lockdown? 정상?)      |
+--------------------------------------------------+
```

### 재현 가능한 보안 시나리오 예시

| 시나리오 | Active Driver 동작 | 예상 결과 |
|---------|-------------------|----------|
| Fault Injection (verify 우회) | verify 결과 레지스터를 force로 PASS 강제 | 이중 검증이 불일치 감지 → abort |
| TOCTOU 시뮬레이션 | 검증 완료 후 SRAM 내용 force로 변경 | SRAM Lock이 쓰기 차단 |
| JTAG 공격 | JTAG disable 상태에서 JTAG 신호 force | 접근 차단 확인 |
| Crypto 결과 변조 | HW Crypto 출력을 force로 오류값 주입 | 검증 실패 → boot abort |
| Anti-Rollback 우회 시도 | OTP 카운터 값을 force로 리셋 | OTP 특성상 불가, 또는 검증 실패 |

**면접 키포인트**: "Legacy 환경에서는 보안 공격 시나리오를 수동 force 문으로 하나하나 작성해야 했고, 비결정론적이어서 재현이 어려웠다. Active UVM Driver를 통해 공격 벡터를 Sequence Item으로 추상화하여, 결정론적으로 복잡한 보안 시나리오를 체계적으로 재현할 수 있게 되었다."

---

## DPI-C HW/SW Co-verification

### 왜 필요한가?

```
BootROM 검증의 특수성:
  - BootROM 코드는 C로 작성된 FW → Mask ROM에 구움
  - 보안 핸드셰이크는 HW + FW 협력으로 동작
  - FW 로직을 RTL 시뮬레이션만으로 검증하기 어려움

문제:
  - FW 전달 지연 → 검증 시작 불가 (기존 병목의 또 다른 원인)
  - 복잡한 보안 프로토콜의 Expected Value 계산이 TB에서 어려움
```

### DPI-C 통합 구조

```
+----------------------------------------------+
|            UVM Testbench                       |
|                                               |
|  Sequence → Driver → DUT (BootROM RTL)        |
|                         |                     |
|                    Bus Monitor                 |
|                         |                     |
|              +----------v-----------+         |
|              |    Scoreboard        |         |
|              |                      |         |
|              |  DUT 출력  vs  기대값 |         |
|              |              ^       |         |
|              +--------------|-------+         |
|                             |                 |
|              +--------------+--------+        |
|              | DPI-C Interface       |        |
|              |  import "C" function  |        |
|              +--------------+--------+        |
|                             |                 |
+------------------------------|----------------+
                               |
              +----------------v--------+
              | C Reference Model       |
              |                         |
              | - 보안 핸드셰이크 로직   |
              | - 키 교환 프로토콜       |
              | - 해시/서명 검증 결과    |
              | - Boot Flow 상태 머신   |
              +-------------------------+
```

### 인터칩 키 교환 프로토콜 검증 (Meta/Apple)

```
칩 간 보안 통신 시나리오:

  Host SoC (BootROM)          Partner Chip
       |                           |
       |  1. Challenge 생성/전송    |
       |  ---------------------->  |
       |                           |
       |  2. Response 수신          |
       |  <----------------------  |
       |                           |
       |  3. 키 도출 + 검증         |
       |                           |

DPI-C로 검증하는 이유:
  - Challenge/Response 계산은 C 코드로 이미 존재 (FW에서 가져옴)
  - RTL에서 같은 로직을 재구현 → 동일 버그 재현 위험
  - C Reference Model = 독립적 Golden Model
  - Pre-silicon에서 FW 수준 보안 핸드셰이크를 완전히 검증 가능
```

### DPI-C 적용 영역

| 영역 | C Model 역할 | 검증 대상 |
|------|-------------|----------|
| 키 교환 프로토콜 | Challenge/Response 기대값 계산 | HW가 올바른 키를 도출하는지 |
| 해시 계산 | SHA-256 Golden Reference | HW Crypto Engine 출력 정확성 |
| 인증서 파싱 | Certificate 구조 해석 기대값 | BootROM의 Certificate 처리 로직 |
| Boot Flow 상태 | 상태 전이 기대값 | 각 단계의 전이 조건 만족 여부 |

**면접 답변 준비**:

**Q: DPI-C로 HW/SW Co-verification을 어떻게 수행했나?**
> "BootROM FW의 C 코드를 DPI-C로 UVM Scoreboard에 연동하여 Golden Reference Model로 사용했다. 특히 인터칩 키 교환 프로토콜(Meta/Apple 협업)에서 Challenge-Response 기대값을 C 모델이 계산하고, DUT의 HW 출력과 비트 단위로 비교했다. 이를 통해 FW 전달 전에도 보안 핸드셰이크의 Pre-silicon 검증이 가능했고, 기존 1-2개월의 FW 대기 병목을 해소했다."

---

## Coverage-Driven 검증 전략

### BootROM Coverage Model 구조

```
+----------------------------------------------------------+
|              BootROM Functional Coverage                   |
|                                                           |
|  [CG1] Boot Configuration Coverage                        |
|    - cp_secure_boot: {ON, OFF}                            |
|    - cp_boot_device: {UFS, eMMC, SDMMC, USB, SPI}        |
|    - cp_boot_mode:   {Normal, Recovery, DL}               |
|    - cross: secure_boot × boot_device × boot_mode         |
|    → 모든 OTP 설정 조합이 검증되었는가?                    |
|                                                           |
|  [CG2] Secure Boot Verification Coverage                  |
|    - cp_verify_result:  {PASS, FAIL}                      |
|    - cp_failure_reason: {BAD_SIG, BAD_CERT, ROTPK_MISMATCH,|
|                          ROLLBACK, TIMEOUT}                |
|    - cp_image_type:     {NORMAL, TAMPERED, TRUNCATED,     |
|                          OVERSIZED, ZERO_SIZE}             |
|    - cross: verify_result × failure_reason                 |
|    → 모든 실패 사유가 검증되었는가?                        |
|                                                           |
|  [CG3] Attack Scenario Coverage                            |
|    - cp_attack_type: {FI, ROLLBACK, TOCTOU, JTAG,         |
|                       FLASH_REPLACE}                       |
|    - cp_defense_response: {ABORT, LOCKDOWN, FALLBACK,     |
|                            RETRY}                          |
|    - cross: attack_type × defense_response                 |
|    → 모든 공격-방어 조합이 검증되었는가?                   |
|                                                           |
|  [CG4] Boot Device Fallback Coverage                       |
|    - cp_primary_result:   {SUCCESS, FAIL_INIT, FAIL_LOAD, |
|                            FAIL_VERIFY}                    |
|    - cp_fallback_device:  {eMMC, USB, NONE}               |
|    - cp_fallback_result:  {SUCCESS, FAIL}                  |
|    - cross: primary_result × fallback_device               |
|    → 모든 Fallback 경로가 검증되었는가?                    |
|                                                           |
|  [CG5] Anti-Rollback Coverage                              |
|    - cp_image_version:    {BELOW_MIN, EQUAL_MIN, ABOVE}   |
|    - cp_counter_state:    {ZERO, MID, MAX}                |
|    - cross: image_version × counter_state                  |
+----------------------------------------------------------+
```

### Coverage Closure 전략

| 단계 | 방법 | 목표 |
|------|------|------|
| 1. Directed Smoke (seed=0) | 기본 부팅 경로 확인 | 데이터 경로 정상 동작 |
| 2. Configuration Sweep | OTP Abstraction Layer로 설정 조합 자동 생성 | CG1 교차 커버리지 100% |
| 3. Negative Scenario | Active Driver로 공격 시나리오 주입 | CG2, CG3 커버리지 |
| 4. Constrained Random (100+ seeds) | 랜덤 OTP/이미지/공격 조합 | 코너 케이스 발견 |
| 5. Fallback Path | 에러 주입으로 Fallback 강제 | CG4 커버리지 |
| 6. Edge Case | Anti-Rollback 경계값, 이미지 크기 극단값 | CG5 + 경계 조건 |

---

## 환경 포팅 전략 — Apple/Meta 프로젝트

### 왜 빠른 포팅이 가능했는가?

```
모듈형 UVM 아키텍처의 3가지 분리 원칙:

1. DUT 독립적 Agent 설계
   - OTP Agent: OTP 인터페이스 프로토콜만 처리
   - Boot Device Agent: 표준 프로토콜(UFS/eMMC) 준수
   → DUT가 바뀌어도 Agent 재작성 불필요

2. Config Object 기반 동작 변경
   - boot_device_type, otp_map_file, secure_boot_mode
   → 파라미터만 변경하면 다른 SoC에 적용

3. OTP Abstraction Layer의 맵 교체
   - 새 SoC의 OTP 맵 파일만 교체
   → 물리 주소 의존성 없으므로 테스트 코드 변경 없음
```

### 포팅 체크리스트

| 항목 | 작업 | 소요 시간 |
|------|------|----------|
| OTP 맵 파일 교체 | 새 SoC의 OTP 맵 CSV/JSON 적용 | 수 시간 |
| 인터페이스 어댑터 | DUT 포트 매핑 업데이트 | 1-2일 |
| Boot Device 설정 | 지원 장치 목록 Config Object에 반영 | 수 시간 |
| 보안 프로토콜 차이 | DPI-C C-model 교체 (칩별 키 교환 프로토콜) | 1-2일 |
| Coverage Model 업데이트 | 새 SoC의 설정 조합에 맞게 bin 조정 | 1일 |
| **총 포팅 소요** | | **3-5일** (Legacy: 수 주) |

**면접 답변 준비**:

**Q: Apple/Meta 프로젝트에 환경을 어떻게 포팅했나?**
> "UVM 프레임워크를 모듈형으로 설계했기 때문에 가능했다. 핵심은 세 가지 분리: (1) DUT 독립적 Agent — 프로토콜만 처리하므로 DUT가 바뀌어도 재사용. (2) Config Object — SoC별 차이를 파라미터로 흡수. (3) OTP Abstraction Layer — 맵 파일만 교체하면 물리 주소 변경에 면역. 결과적으로 수 주 걸리던 포팅을 3-5일로 단축하여 촉박한 일정 내에서 즉시 검증 지원을 제공했다."

---

## Post-Silicon 연결 — Pre-silicon 검증이 Bring-up을 가속하는 이유

### Pre-silicon에서 100% 기능 무결성 확보의 의미

```
Post-silicon Bring-up 시나리오:

  칩 전원 ON → BootROM 실행 → BL2 로드 시도 → ???

  Case 1: Pre-silicon 검증 불완전
    → 부팅 실패 시 원인 특정 불가
    → "BootROM 버그? Boot Device 문제? OTP 프로그래밍 오류?"
    → 각각 디버그 → 수 주 소요

  Case 2: Pre-silicon 검증 완전 (100% 기능 무결성)
    → 부팅 실패 시 BootROM을 원인에서 즉시 배제
    → "BootROM은 검증 완료 → 문제는 비-ROM 영역"
    → 디버그 범위 대폭 축소 → 수 일로 단축
```

### 검증 완전성 → Post-silicon 디버그 가속

| Pre-silicon 검증 항목 | Post-silicon 디버그 기여 |
|---------------------|------------------------|
| 모든 Boot Mode × Device 조합 검증 | 특정 조합 실패 시 HW 문제로 즉시 분류 |
| 모든 Negative 시나리오 검증 | 보안 기능 정상 동작 확인 → 공격 방어 검증 불필요 |
| DPI-C로 FW 로직 사전 검증 | FW 버그 vs HW 버그 분리 용이 |
| Fallback 경로 전수 검증 | Fallback 실패 시 HW 연결 문제로 분류 |

---

## 면접 종합 Q&A

**Q: BootROM 검증 환경을 어떻게 설계했는가?**
> "Legacy SV 환경을 UVM 프레임워크로 전면 전환했다. 핵심 3가지: (1) OTP Abstraction Layer — RAL 방식으로 OTP 물리 주소를 추상화하여 테스트에서 의미 기반으로 접근하게 함. (2) Active UVM Driver — force/release 시퀀스를 체계적으로 관리하여 보안 공격 벡터를 결정론적으로 재현. (3) DPI-C C-model — 보안 핸드셰이크의 Golden Reference를 FW C 코드에서 직접 가져와 Scoreboard에 연동. 이로 인해 검증 TAT를 1개월 이상 단축하고, 여러 프로젝트에 빠르게 포팅할 수 있는 재사용 가능한 환경을 만들었다."

**Q: Coverage-Driven 검증 전략을 구체적으로 설명하라.**
> "5개 Covergroup으로 구성했다: (1) Boot Config — OTP 설정 조합 교차 커버리지 (Secure Boot × Boot Device × Boot Mode). (2) Verify Result — 서명 검증 결과 × 실패 사유. (3) Attack Scenario — 공격 유형 × 방어 응답. (4) Fallback Path — Primary 실패 원인 × Fallback 장치 × Fallback 결과. (5) Anti-Rollback — 이미지 버전 × 카운터 상태. Directed → Sweep → Negative → Random → Edge Case 순으로 점진적으로 Coverage를 높여 Closure를 달성했다."

**Q: 1-2개월 검증 병목을 어떻게 해결했는가?**
> "먼저 근본 원인을 분석했다 — 병목은 FW 전달 지연으로 여겨졌지만, 실제로는 환경의 재사용성 부족이 진짜 원인이었다. 해결: (1) UVM 전환으로 테스트 추가 시간을 수 일 → 수 시간으로 단축. (2) OTP Abstraction Layer로 OTP 맵 변경에 면역. (3) DPI-C로 FW 전달 전에도 검증 시작 가능. 결과적으로 TAT 1개월 이상 단축, SoC Tape-out 일정을 직접 가속했다."

**Q: Zero-Defect Silicon을 어떻게 달성했는가?**
> "Coverage-Driven 방법론과 구조적 Negative Test 전략의 조합이다. Positive(정상 부팅) 100%는 기본이고, 5개 공격 카테고리(Crypto, Rollback, Fault, Input, Config)별 Negative 시나리오를 체계적으로 커버했다. 결과적으로 Post-silicon Bring-up에서 BootROM 관련 이슈 제로를 달성하여, 비-ROM 이슈의 빠른 Root Cause 분리를 가능하게 했다."

---
!!! warning "실무 주의점 — ROM patch 적용 후 ROTPK 체인 재검증 누락"
    **현상**: BootROM patch (ROM-RAM remap / hot-fix) 를 적용한 다음, 후속 stage 의 서명 검증이 patch 이전 버전의 ROTPK 로 통과해 버린다. 결과적으로 patch 가 의도한 키 교체가 우회된다.

    **원인**: Patch 진입 후에도 ROTPK 핸들 / hash 캐시가 patch-pre 값으로 남아 있고, DV scenario matrix 가 (patch on/off) × (ROTPK 변형) 교차를 cover 하지 않아 회귀에서 잡히지 않음.

    **점검 포인트**: patch 적용 직후 ROTPK 가 재로드되어 image signature 검증에 사용되는가, 그리고 reference model 이 patch 경로의 expected ROTPK 와 검증 결과를 정확히 예측하는지 scoreboard 에서 확인하는가.

## 핵심 정리

- **BootROM DV의 특수성**: BootROM은 silicon에 mask로 fixed → bug = silicon revision (수억 원). Defect Zero가 절대 목표.
- **Scenario matrix**: Boot mode (eMMC/UFS/QSPI/USB) × OTP config (security on/off, ROTPK 변형) × Image (golden/corrupted/unsigned/version mismatch).
- **Reference model**: Golden image의 expected boot path를 SystemVerilog/Python으로 모델링.
- **Error injection**: 서명 corrupted, version old, ROTPK mismatch, image truncated, fail-over trigger.
- **Coverage-driven**: 모든 시나리오가 covered + 모든 fail path가 expected behavior. Sign-off의 핵심.

## 코스 마무리

- 📝 [**Module 06 퀴즈**](quiz/07_bootrom_dv_methodology_quiz.md)
- 다음: [퀴즈 인덱스](../quiz/) · [용어집](../glossary/) · 다른 토픽: [ARM Security](../../arm_security/), [UVM](../../uvm/)

<div class="chapter-nav">
  <a class="nav-prev" href="../06_quick_reference_card/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">SoC Secure Boot Flow — Quick Reference Card</div>
  </a>
  <a class="nav-next" href="../quiz/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">퀴즈로 이동</div>
  </a>
</div>


--8<-- "abbreviations.md"
--8<-- "_inc/topic_abbr.md"
