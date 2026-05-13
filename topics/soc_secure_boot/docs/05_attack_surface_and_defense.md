# Module 05 — Attack Surface & Defense

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="soc">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🔐</span>
    <span class="chapter-back-text">SoC Secure Boot</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 05</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-이-모듈이-왜-필요한가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-비유와-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-한-건의-fault-injection-fail-log-에서-defense-까지">3. 작은 예 — Fault Injection 1 cycle</a>
  <a class="page-toc-link" href="#4-일반화-공격-카테고리와-defense-in-depth">4. 일반화 — 공격 카테고리 + Defense in Depth</a>
  <a class="page-toc-link" href="#5-디테일-공격-별-원리-방어-negative-test">5. 디테일 — 공격별 원리 / 방어 / Negative Test</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-dv-디버그-체크리스트">6. 흔한 오해 + DV 디버그 체크리스트</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Identify** Secure Boot 의 공격 표면 카테고리 (Fault Injection, Side-Channel, Rollback, TOCTOU, JTAG, supply chain) 를 식별할 수 있다.
    - **Apply** 다층 방어 (HW: glitch detector / SRAM lock, SW: 이중 검증 / anti-rollback, 설계: key hierarchy / crypto agility) 를 적용할 수 있다.
    - **Trace** 실제 공격 사례 (Glitchy Descriptor on iPhone, FROST attack 등) 의 흐름을 추적할 수 있다.
    - **Plan** Threat model 을 작성해 우선순위를 결정할 수 있다.
    - **Decompose** 한 verify-then-execute 함수 안에서 어디가 글리치 surface, 어디가 TOCTOU surface, 어디가 side-channel surface 인지 분해할 수 있다.

!!! info "사전 지식"
    - [Module 01-04](01_hardware_root_of_trust.md) — RoT, chain, crypto, boot device
    - 보안 취약점 / 공격 모델 일반 (CIA triad)

---

## 1. Why care? — 이 모듈이 왜 필요한가

### 1.1 시나리오 — _Fault Injection_ 으로 _RSA verify_ 우회

2017: 한 SoC 의 RSA signature verify 가 _glitch 공격_ 으로 우회됨.

공격:
1. BootROM 이 RSA verify 실행 중.
2. 정확한 시점에 _전원 라인_ 에 _glitch_ (~ns 단위 voltage spike).
3. _Verify result branch_ instruction 에서 _NOP_ 되거나 _wrong branch_.
4. _Invalid signature_ 인데도 _OK 처리_ → 임의 image load.

**Fault injection 의 본질**: _alle algorithm_ 정확해도 _실행 환경_ 이 _공격당하면_ 결과 corruption. 검증 시 _silicon spec_ 만 검증 ≠ 보안.

방어:
- **Double verify**: verify 후 _다시 verify_, 두 결과 비교 → glitch 한 번에 둘 다 우회 어려움.
- **Random delay**: glitch timing 예측 못하게.
- **Hardware glitch detector**: voltage / clock monitor.

검증 시 _이런 negative scenario_ 를 _명시적으로_ 시뮬에 inject 해야 _진짜 보안_.

Module 01-04 는 _정상적으로_ chain 이 동작하는 모습이었습니다. 이번 모듈은 그 chain 에 _공격자가 끼어들 자리_ 가 어디인지를 봅니다 — 그리고 그 자리마다 **DV 가 reproducible 한 negative scenario 로 미리 두드려야** 합니다. 그러지 않으면 spec 만 맞춘 검증 = false sense of security.

이후 Module 07 (DV 방법론) 의 _Active UVM Driver / 5 covergroup / Negative scenario framework_ 가 모두 이 모듈에서 본 surface 를 기반으로 설계됩니다. 즉 Module 05 = 공격자 관점 모델, Module 07 = 그것을 검증으로 환원한 결과.

---

## 2. Intuition — 비유와 한 장 그림

!!! tip "💡 한 줄 비유"
    **Attack Surface** ≈ **성벽의 모든 출입구 + 약점**.<br>
    정문 (API), 후문 (JTAG), 비밀통로 (side-channel), 망루 사각지대 (TOCTOU), 시간 차 (rollback). 한 군데만 막으면 다른 데로 들어옵니다 — 그래서 **defense in depth** 가 유일한 답.

### 한 장 그림 — Boot flow 위에 공격자가 끼어들 수 있는 자리

```
   Power-On
       │
       │ ① Fault Injection (전압/EM/레이저 글리치)  ◀── boot 전 / 검증 분기 중
       ▼
   ┌─────────────┐
   │  BootROM    │── ② ROM exploit (코드 취약점)         ◀── 매우 어려움
   │             │── ③ Side-channel (전력/EM/timing)     ◀── 키 비트 추론
   └──────┬──────┘
          │
   ┌──────┴──────┐
   │  OTP/eFuse  │── ④ 물리 공격 (FIB probing, decap)    ◀── nation-state
   │             │── ⑤ Rollback (구버전 강제)            ◀── ARC 우회
   └──────┬──────┘
          │
   ┌──────┴──────┐
   │ Boot Device │── ⑥ Flash 교체 (악성 image)           ◀── verify 가 잡음
   │             │── ⑦ JTAG/Debug port                   ◀── debug 권한
   └──────┬──────┘
          │
   ┌──────┴──────┐
   │ BL2/BL3...  │── ⑧ SW exploit (buffer overflow)      ◀── BL 자체 버그
   │             │── ⑩ TOCTOU (verify ↔ jump 사이 변조) ◀── 가장 미묘
   └─────────────┘

   배경 ── ⑨ 공급망 공격 (제조 시점 변조)                ◀── 검증 불가에 가까움
```

### 왜 이렇게 분류하는가 — Design rationale

세 가지 기준으로 surface 를 나눕니다.

1. **공격자 자원 수준** — 글리치/Flash 교체 = $300 ChipWhisperer 로도 가능, FIB/레이저 = $100K+, Nation-state = 무한.
2. **공격 시점** — boot 전 (FI), boot 중 (TOCTOU), boot 후 (rollback) 가 각자 다른 방어 메커니즘 필요.
3. **방어 가능성** — 가능 (SW 분기, 이중 검증) / 어려움 (side-channel) / 거의 불가능 (공급망) — 어디에 자원을 쓸지 결정.

DV 관점에서는 _가능_ 영역의 모든 surface 를 reproducible scenario 로 만들 수 있느냐가 sign-off 의 의미.

---

## 3. 작은 예 — 한 건의 Fault Injection, Fail log 에서 Defense 까지

가장 단순한 시나리오. 단일 분기 verify-then-execute 코드가 글리치로 우회되는 1 cycle, 그리고 이중 검증으로 어떻게 막는지.

### 공격 단계 추적

```
   Time             공격자                         BootROM (취약 코드)              관찰
   ────             ──────                          ──────────────                  ────
   t0  POR                                          BL2 image + cert load          OK
   t1  ChipWhisperer arm                            verify_bl2() 시작
   t2                                                SHA-256, RSA verify           OK
   t3                                                ret = SUCCESS or FAIL?        ret = FAIL
   t4  ★ glitch trigger (전압 강하 5 ns)            cmp ret, SUCCESS  ◀── 분기  CPU mis-execute
   t5                                                je halt   ◀── _이 jump 가 건너뛰어짐_
   t6                                                fall-through → jump BL2_entry  ★★ 우회 성공
   t7                                                BL2 entry 실행 시작            악성 image
                                                                                    실행 됨
```

| Step | 누가 | 무엇을 | 의미 |
|---|---|---|---|
| t0 | SoC | POR + cert 로드 | 정상 |
| t1 | 공격자 | trigger 준비 | scope 로 boot phase 동기 |
| t2 | BootROM | hash, RSA verify | crypto 자체는 정상 동작 |
| t3 | BootROM | ret = FAIL (image 가 변조됐으니까) | 정상 분기는 halt 로 |
| t4 | 공격자 | VDD 글리치 5 ns | CPU 의 cmp 결과 비트 flip 또는 skip |
| t5 | BootROM | je halt 명령이 _건너뛰어짐_ | 단일 분기 = 단일 surface |
| t6 | BootROM | fall-through → BL2 jump | _공격 성공_ |
| t7 | (악성 BL2) | EL3 권한으로 임의 코드 | chain 전체 무효화 |

### 방어 — 이중 검증 + Flow Integrity

```c
// 취약 (단일 분기 — t4 의 한 글리치로 우회 가능)
if (verify_bl2(cert, bl2) != SUCCESS) halt();
jump_to_bl2();

// 안전 (이중 검증 + flow integrity magic)
status_t r1 = verify_bl2(cert, bl2);
status_t r2 = verify_bl2(cert, bl2);          // ◀ 독립 재검증
if (r1 != SUCCESS) halt();
if (r2 != SUCCESS) halt();
if (r1 != r2)      halt();                    // ◀ 두 결과 교차 비교

// flow integrity magic — 검증 단계 도달 증거
if (flow_magic_after_verify != FLOW_MAGIC)  halt();

jump_to_bl2();                                // ◀ 단일 글리치로 모두 우회 ≈ 불가능
```

| 방어 layer | 어떻게 막나 | 비용 |
|---|---|---|
| 이중 검증 (`r1`, `r2`) | 한 글리치 = 한 분기만 영향. 두 분기 동시 우회 ≈ 불가능 | 검증 시간 2배 |
| 결과 교차 비교 (`r1 == r2`) | r1, r2 가 다르면 abort — 글리치가 한 쪽만 flip 한 경우 잡음 | 분기 1개 추가 |
| Flow integrity magic | 검증 함수 내부의 specific path 통과 증거 | 분기 1개 + 변수 |
| HW glitch detector | 전압/클럭 이상 → 자동 reset/lockdown | 별도 sensor IP |

!!! note "여기서 잡아야 할 두 가지"
    **(1) 단일 if 분기는 단일 글리치 surface** — verify-then-execute 의 _분기_ 자체가 공격 surface 이지, verify 함수 안의 hash/RSA 계산이 surface 가 아닙니다.<br>
    **(2) 방어는 _중복 (redundancy)_ 이지 _복잡성_ 이 아니다** — 한 번의 글리치로 _모든 방어_ 를 동시에 무력화 어렵게 만드는 것이 핵심. 이중 검증 + 결과 교차 + flow magic + HW detector 가 _OR 가 아니라 AND_ 로 동작.

---

## 4. 일반화 — 공격 카테고리와 Defense in Depth

### 4.1 공격 표면 맵

```
+--------------------------------------------------------+
|                  공격 표면 맵                            |
|                                                         |
|  Power-On                                               |
|    |  (1) Fault Injection (Glitch, Laser, EM)           |
|    v                                                    |
|  BootROM --- (2) ROM Exploit (코드 취약점)               |
|    |  (3) Side-Channel (전력/EM 분석)                    |
|    v                                                    |
|  OTP/eFuse - (4) 물리적 공격 (FIB probing)              |
|    |  (5) Rollback Attack (취약한 FW로 다운그레이드)      |
|    v                                                    |
|  Boot Dev -- (6) Flash 교체 (악성 이미지)                |
|    |  (7) JTAG/Debug Port 접근                           |
|    v                                                    |
|  BL2/BL3 -- (8) SW Exploit (버퍼 오버플로 등)            |
|                                                         |
|  (9) 공급망 공격 (제조 과정 변조)                        |
|  (10) TOCTOU (검증 시점과 사용 시점 차이)                |
+--------------------------------------------------------+
```

### 4.2 Defense in Depth — 3 계층

| 계층 | 메커니즘 | 예시 |
|---|---|---|
| **HW** | sensor + lock | glitch detector, SRAM lock-down, key isolation, anti-tamper mesh |
| **SW** | 중복 + 검증 | 이중 verify, flow magic, anti-rollback counter, secure storage |
| **설계** | architecture | key hierarchy (피해 범위 제한), crypto agility (PQC 전환), threat modeling |

한 계층만 의존하면 그 계층의 공격에 모두 노출. 셋이 직교적으로 동작해야 attacker 가 하나를 우회해도 다른 계층이 잡습니다.

### 4.3 Threat Model — 누가 공격자인가

| 공격자 | 자원 | 대표 surface |
|---|---|---|
| Production attacker | $300 ChipWhisperer, off-the-shelf | Glitch, JTAG probing, Flash swap, Rollback |
| Targeted attacker | $100K+ FIB, EM lab | Side-channel, FIB probing, Decapping |
| Nation-state | 무한 자원 + 공급망 접근 | 공급망 변조, 제조 시점 backdoor, 0-day |

DV 의 일반 책임 영역은 _Production attacker_ 까지. Targeted/Nation-state 는 별도 보안팀.

---

## 5. 디테일 — 공격별 원리 / 방어 / Negative Test

### 5.1 (1) Fault Injection (글리치 공격)

#### 공격 원리

```
정상 부팅:
  if (signature_verify(BL2) == SUCCESS)
      jump_to(BL2);    ← 정상 실행
  else
      boot_abort();

글리치 공격:
  if (signature_verify(BL2) == SUCCESS)  ← 이 비교 시점에
      jump_to(BL2);                         전압 글리치 주입!
  else                                      CPU가 비교를 건너뜀
      boot_abort();                         → 무조건 점프

  결과: 서명 검증 없이 악성 BL2가 실행됨!
```

#### 공격 방법

| 방법 | 원리 | 장비 | 정밀도 |
|------|------|------|--------|
| 전압 글리치 | 순간적 VDD 강하/스파이크 → CPU 오동작 | ChipWhisperer (~$300) | 중간 |
| EM Fault | EM 펄스로 특정 회로 교란 | EM 프로브 + 펄스 발생기 | 높음 |
| 레이저 Fault | 레이저로 특정 트랜지스터 플립 | 레이저 스테이션 ($100K+) | 매우 높음 |

#### 방어 (다층)

```
1. 이중 검증 (SW 레벨)
   result1 = verify(image);
   result2 = verify(image);   // 재검증
   if (result1 == OK && result2 == OK && result1 == result2)
       jump_to(BL2);
   → 단일 글리치로는 두 검증을 동시에 무력화할 수 없음

2. Flow Integrity 검사
   - 각 부팅 단계에서 Magic Value 기록
   - Jump 전에 모든 Magic Value 검증
   - 불일치 → 중단

3. HW 레벨 방어
   - 전압/클럭 글리치 감지기
   - 이상 감지 → 칩 리셋 또는 Lockdown
   - Active Metal Shield (레이저 방어)
   - 실행 타이밍 랜덤화

4. Secure Boot 카운터
   - 부팅 시도 횟수 카운트, 비정상 반복 감지
   - 과도한 재시도 → 영구 Lockdown
```

**면접 키포인트**: "Fault Injection 방어의 핵심은 중복성 (redundancy) — 이중 검증, 결과 교차 확인, 별도의 Flow Integrity 검사. 단일 글리치로는 모든 방어를 동시에 무력화할 수 없다."

### 5.2 (5) Rollback Attack (다운그레이드 공격)

#### 공격 원리

```
v1.0 --- 취약점 발견! --→ v2.0 (패치됨)

공격자:
  1. 정당하게 서명된 v1.0 이미지 보관
  2. v2.0 배포 후, Flash를 v1.0으로 교체
  3. v1.0은 유효한 서명 보유 → Secure Boot PASS!
  4. v1.0 취약점 악용

  → 서명은 "누가 만들었는가"만 보장, "최신인가"는 보장하지 않음
```

#### 방어: Anti-Rollback Counter

```
OTP Anti-Rollback Counter (ARC):
  bit[0] bit[1] bit[2] bit[3] ...
    1      1      1      0    0
    ← blown →     ← intact →
  현재 최소 버전 = 3

검증 로직 (BootROM):
  img_version = cert.version;
  otp_min     = count_blown_bits;
  if (img_version < otp_min)
      REJECT! // 롤백 시도
  else
      proceed with verify;

FW 업데이트:
  - 새 FW 설치 성공 후 ARC 비트 Blow
  - Blow 후에는 이전 버전 부팅이 영구적으로 불가능

한계:
  - OTP 비트 수 = 최대 업데이트 횟수 (32 bit → 32개 메이저 버전)
  - RPMB를 보조 카운터로 사용 (물리적 소진 없음)
```

### 5.3 (3) Side-Channel Attack (부채널 공격)

#### 공격 원리

```
RSA 검증 시 전력 소비 패턴:
  키 비트 = 1: xxxxxxxx  (곱셈 + 제곱 → 높은 전력)
  키 비트 = 0: xxxx      (제곱만 → 낮은 전력)

공격자: 오실로스코프로 전력 측정 → 키 비트 추론
```

| 유형 | 측정 대상 | 장비 |
|------|----------|------|
| SPA (Simple Power Analysis) | 전력 파형 패턴 | 오실로스코프 |
| DPA (Differential Power Analysis) | 통계적 전력 차이 | + 수천 회 측정 |
| EMA (EM Analysis) | EM 방사 | EM 프로브 |
| Timing Attack | 연산 시간 차이 | 정밀 타이머 |

#### 방어

| 기법 | 원리 |
|------|------|
| Constant-time 구현 | 키 값과 무관하게 동일한 연산 시간 |
| 전력 균형화 | 더미 연산 추가로 전력 패턴 균등화 |
| 마스킹 | 중간값에 랜덤 마스크 적용 |
| HW Crypto Engine | 위 모든 방어를 하드웨어로 구현 |

**이것이 BootROM 이 HW Crypto Engine 을 사용해야 하는 이유** — SW RSA/ECDSA 구현은 부채널 방어가 극히 어렵습니다.

### 5.4 (7) JTAG / Debug Port 공격

```
방어 수준 (점진적):

Level 0: JTAG 오픈 (개발 전용)
Level 1: 패스워드 보호 → JTAG 접근 전 인증
Level 2: Secure JTAG → Challenge-Response 인증
Level 3: 영구 비활성화 → OTP Blow, 물리적 차단
         → 양산 후 어떤 디버그도 절대 불가

트레이드오프: Level 3 = 현장 디버그 완전 불가
              → 보통 Level 2 + Secure JTAG 선호
```

### 5.5 (10) TOCTOU (Time-of-Check-to-Time-of-Use)

#### 공격 원리

```
정상:
  (1) Check: verify(SRAM의 BL2) → PASS
  (2) Use:   jump_to(SRAM의 BL2)

TOCTOU 공격:
  (1) Check: verify(SRAM의 BL2) → PASS
      | 검증과 사용 사이에 DMA가 SRAM 내용을 악성 코드로 교체!
  (2) Use:   jump_to(SRAM의 악성 코드)
```

#### 방어

| 방어 | 설명 |
|------|------|
| SRAM Lock | 검증 후 HW 적으로 메모리 영역 쓰기 보호 |
| DMA 비활성화 | 부팅 중 DMA 컨트롤러 비활성화로 외부 접근 차단 |
| Verify-in-place | 보안 메모리로 복사 후, 그곳에서만 검증+실행 |
| Hash 재검사 | Jump 직전에 해시 재계산 (이중 검증) |

**면접 킬러 포인트**: "TOCTOU 방어를 위해 BootROM 은 BL2 를 Internal SRAM 에 로드하고, 검증 후 HW 적으로 해당 영역을 쓰기 보호한다. External DRAM 은 DMA 를 통한 TOCTOU 에 취약하지만, Internal SRAM 접근은 버스 패브릭 레벨에서 차단할 수 있다."

### 5.6 종합 공격 & 방어 테이블

| 공격 | 대상 | 난이도 | 방어 | DV 검증 방법 |
|------|------|--------|------|-------------|
| Fault Injection | 검증 로직 | 중간 | 이중 검증, 글리치 감지기 | verify 결과 force flip → abort 확인 |
| Rollback | FW 버전 | 낮음 | Anti-Rollback Counter (OTP/RPMB) | 구버전 이미지 로드 → reject 확인 |
| Side-Channel | Crypto 키 | 높음 | HW Crypto, Constant-time | HW 레벨 (보통 별도 팀) |
| JTAG | 전체 시스템 | 낮음 | OTP 비활성화, Secure JTAG | JTAG disable 비트 설정 → 접근 시도 → 차단 확인 |
| TOCTOU | 검증된 이미지 | 높음 | SRAM Lock, DMA 비활성화 | 검증 후 메모리 쓰기 시도 → 차단 확인 |
| Flash 교체 | 부팅 이미지 | 낮음 | 서명 검증 | 변조 이미지 로드 → verify fail → abort 확인 |
| ROM Exploit | BootROM 코드 | 매우 높음 | 코드 최소화, ROM Patch | 코드 리뷰 + 정형 검증 |

### 5.7 Negative Test 시나리오 프레임워크

공격 카테고리별로 정리하면 면접에서 구조적 답변이 가능:

#### 카테고리 1: 서명/인증 실패

- 잘못된 서명의 BL2 이미지 → verify fail → boot abort
- 유효하지 않은 인증서 (만료, 잘못된 키) → reject
- ROTPK 해시 불일치 (OTP vs 인증서) → reject

#### 카테고리 2: Rollback/버전

- FW 버전이 Anti-Rollback Counter 미만 → reject
- 카운터 엣지 케이스: 카운터 최대값 도달 시 동작

#### 카테고리 3: Fault/Tamper

- verify 결과 Force-flip → 이중 검증이 포착
- 전압 글리치 시뮬레이션 → 글리치 감지기 응답
- 검증 후 메모리 변조 (TOCTOU) → SRAM Lock 이 쓰기 차단

#### 카테고리 4: 부팅 장치/입력

- 손상된 부팅 이미지 (불완전, 잘린 이미지, CRC 에러) → 정상적 실패 처리
- 부팅 장치 무응답 → 타임아웃 후 Fallback
- 비정상 크기 이미지 (0 bytes, 초과 크기) → 버퍼 오버플로 없음

#### 카테고리 5: 설정

- Secure Boot 활성화 + 미서명 FW → 무조건 reject
- JTAG 비활성화 + JTAG 접근 시도 → 차단
- 유효하지 않은 Boot Mode OTP 설정 → Safe State 진입

**면접 팁**: "Negative 시나리오 3개 이상 나열하세요" 라는 질문에 단순히 나열하지 말고 카테고리화. "서명 카테고리에서 2개, Rollback 1개, Fault 2개, 입력 1개 — 총 6개입니다." 구조적 사고 = 시니어 엔지니어 인상.

### 5.8 DV 관점 — UVM force/release 로 보안 공격 재현

#### Active Driver 의 force/release 활용

기존 Legacy 환경에서는 Negative 시나리오마다 수동으로 force 문을 작성. UVM Active Driver 는 이를 체계적으로 관리:

```
// Active Driver: 공격을 Sequence Item으로 추상화
class security_attack_seq extends uvm_sequence;
  task body();
    security_attack_item item;

    // Fault Injection: verify 결과 force-flip
    item = security_attack_item::type_id::create("fi_attack");
    item.attack    = FAULT_INJECTION;
    item.target    = "dut.boot_ctrl.verify_result";
    item.inject_at = VERIFY_COMPLETE;  // 검증 완료 시점
    item.value     = PASS;             // FAIL을 PASS로 강제
    start_item(item); finish_item(item);

    // 기대 결과: 이중 검증이 불일치를 감지하여 abort
  endtask
endclass
```

#### 주요 공격별 DV 구현 방법

| 공격 | force 대상 | 주입 시점 | 검증 포인트 |
|------|-----------|----------|------------|
| FI (verify 우회) | verify 결과 레지스터 | 검증 완료 직후 | 이중 검증 불일치 → abort |
| TOCTOU | SRAM 데이터 영역 | 검증 후 ~ jump 전 | SRAM Lock 이 쓰기 차단 |
| JTAG 공격 | JTAG enable 신호 | 부팅 중 아무 때나 | OTP disable 시 접근 차단 |
| Crypto 출력 변조 | HW Crypto 출력 | Crypto 연산 완료 시 | 검증 실패 → abort |
| Anti-RB 우회 | OTP 카운터 값 | 부팅 초기 | force 불가 또는 검증 실패 |

**핵심**: Passive 모니터링으로는 "공격 시 DUT 가 올바르게 방어하는가?" 를 검증할 수 없습니다. Active Driver 가 **공격자 역할** 을 하여 방어 메커니즘을 능동적으로 검증.

자세한 Active Driver 아키텍처는 [Module 07 (DV 방법론)](07_bootrom_dv_methodology.md) 에서.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'JTAG 만 disable 하면 충분'"
    **실제**: JTAG 외에 boundary scan, debug bus, scan chain, observation pin 등 다축. Side-channel (power, EM, timing) 도 별도 영역. 전체 debug surface 의 _목록_ 을 먼저 만들고 각각을 OTP fuse 로 닫아야 안전.<br>
    **왜 헷갈리는가**: "가시적 인터페이스만 차단" 이라는 직관. 실제 attack 은 무수한 sub-channel.

!!! danger "❓ 오해 2 — '서명 검증 = TOCTOU 안전'"
    **실제**: TOCTOU 는 _서명 검증 후_ jump 사이의 race. verify 가 아무리 정확해도 검증된 SRAM 영역이 잠겨 있지 않으면 DMA 로 swap 가능. SRAM Lock + DMA disable 가 별도로 있어야 안전.<br>
    **왜 헷갈리는가**: "verify 통과 = 안전" 의 단순화 — 시간 축을 보지 않음.

!!! danger "❓ 오해 3 — 'Constant-time 구현이면 side-channel 안전'"
    **실제**: Constant-time 은 _timing_ side-channel 만. 전력/EM/cache/branch-predictor 는 별도. 그리고 컴파일러 최적화로 constant-time 이 사라질 수도 있음 (`-O2` 가 short-circuit 최적화).<br>
    **왜 헷갈리는가**: "constant-time" 이라는 단어가 모든 side-channel 을 막는 것처럼 들림.

!!! danger "❓ 오해 4 — 'HW glitch detector 가 있으면 FI 안전'"
    **실제**: Glitch detector 는 _큰_ 전압/클럭 이상만 잡음. 정밀한 EM/laser FI 는 detector 가 못 봄. SW 이중 검증 + flow integrity 가 _쌍_ 으로 있어야 safe. 그리고 detector 자체가 글리치당하면? — 이중 sensor 도 같이 있어야.<br>
    **왜 헷갈리는가**: "HW = 항상 SW 보다 강함" 의 직관.

!!! danger "❓ 오해 5 — 'BootROM 검증 = 정상 boot 만 확인'"
    **실제**: 추가로 ROM patch 적용 후 chain 재검증, fail-safe boot, error path, JTAG isolation, side-channel 등 광범위. 보안에서는 abnormal path 가 attack surface 입니다.<br>
    **왜 헷갈리는가**: "정상 boot 만 본다" 는 sim mindset.

### DV 디버그 체크리스트 (공격 재현 / 방어 검증에서 자주 보는 실패)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| FI 시뮬에서 이중 검증인데 우회 가능 | 두 검증이 _동시_ 에 실행 (parallel) — 한 글리치로 둘 다 영향 | verify 함수 호출 순서 — 시간 차 보장되나 |
| TOCTOU 재현 시 SRAM lock 동작 안 함 | lock 활성화 시점이 jump 후 | lock register write 의 trigger ↔ verify 완료 시점 |
| JTAG disable 후에도 접근 가능 | `jtag_lock` fuse 가 안 blown | OTP[JTAG_LOCK] dump + TAP IDCODE 응답 vs spec |
| Glitch detector reset 무한 반복 | detector threshold 가 너무 민감, 정상 PVT 도 트리거 | detector threshold register vs PVT corner test |
| Constant-time memcmp 가 컴파일러로 사라짐 | `-O2` 또는 link-time-opt | 최종 binary 의 분기 패턴 (objdump) |
| Active Driver 가 verify 결과 force 했는데 boot 진행 | force release 시점이 너무 빨라 검증 분기 후 | force-release 시간 vs verify 함수 분기 시점 |
| FI 가 HW 에서는 나는데 sim 에서는 재현 안 됨 | sim 의 zero-time race 가 force-release 를 흡수 | sim 의 #1 delay + nonblocking assignment 사용 |
| Rollback 시뮬에서 image 가 통과 | ARC 검증 단계가 secure boot disable path 에서 skip | secure boot ON/OFF 양쪽에서 ARC check 모두 동작하는지 |

!!! warning "실무 주의점 — JTAG 가 production 출하 시 disable 되지 않음"
    **현상**: 양산 chip 을 거꾸로 분석해 보니 JTAG TAP 이 살아 있어 debug 권한으로 SRAM/레지스터에 접근, 부팅 중간 단계의 키 / 검증 결과를 읽거나 강제로 덮어쓸 수 있다.

    **원인**: JTAG disable 이 OTP fuse 의 `jtag_lock` 비트와 연결돼 있는데, 양산 라인에서 해당 fuse 를 blow 하지 않거나, BootROM 이 fuse 값을 읽어 TAP controller 를 잠그는 시퀀스를 누락. Test/bring-up 편의 때문에 default 가 "open" 으로 남는 경우가 흔함.

    **점검 포인트**: production OTP profile 에서 JTAG 가 닫혔는가 (TAP IDCODE 외 응답 차단), 그리고 secure boot 실패 시 fail-secure 로 JTAG 가 닫힌 채 정지하는가 (debug 우회 금지).

---

## 7. 핵심 정리 (Key Takeaways)

- **공격 표면 = 다축**: Fault Injection (전압/클럭 글리치, 레이저), Side-Channel (전력/EM/timing), Rollback (이전 버전), TOCTOU (verify ↔ use 사이 race), JTAG (debug port).
- **방어 = Defense in Depth (HW + SW + 설계)** — 한 계층 의존 = 그 계층 공격에 모두 노출.
- **단일 분기 = 단일 글리치 surface** — 이중 검증 + flow magic + HW detector 가 _쌍_ 으로 있어야 안전.
- **TOCTOU 방어 = SRAM Lock + DMA disable** — verify 가 정확해도 시간 축이 열리면 swap 가능.
- **Threat model 로 자원 분배** — Production attacker (DV 책임) vs Targeted (별도 보안팀) vs Nation-state.

!!! warning "실무 주의점 (요약)"
    - 컴파일러 최적화로 constant-time / 이중 검증이 사라질 수 있음 — final binary 분기 패턴 검사.
    - Glitch detector 자체도 글리치 surface — duplicate sensor 권장.
    - Negative scenario 는 _카테고리_ 화 — 단순 나열 X. 5 카테고리 (Crypto / Rollback / Fault / Input / Config) 가 default.

### 7.1 자가 점검

!!! question "🤔 Q1 — 글리치 surface 식별 (Bloom: Apply)"
    `if (signature_verify(img) == OK) jump(img);` 코드를 글리치 관점에서 _최소 2 가지_ 약점은?
    ??? success "정답"
        글리치 surface:
        1. **분기 자체**: `==` 비교 결과를 글리치로 OK 로 위조 → jump 강제.
        2. **단일 호출**: `signature_verify` 가 1 회 → return value 만 위조하면 됨.
        - **방어**: 이중 호출 + flow magic + HW glitch detector → 셋이 일치해야 jump.
        - 추가: `signature_verify` 내부의 memcmp 도 글리치 surface — constant-time + double-check.

!!! question "🤔 Q2 — TOCTOU 본질 (Bloom: Analyze)"
    Verify-then-execute 가 _이미_ 수행됐는데도 TOCTOU 공격이 가능한 이유?
    ??? success "정답"
        TOCTOU = Time-Of-Check ↔ Time-Of-Use:
        - Verify 시점: image hash A 가 검증됨.
        - Use 시점 (jump): 그 사이에 DMA / 다른 마스터가 SRAM 의 image 를 B 로 swap → B 가 실행됨.
        - **방어**: verify 완료 후 SRAM region lock + 모든 DMA disable → use 까지 region 불변.
        - 비유: 보안 검색대 통과 후 raw bag 으로 바뀌면 무의미 — 검색 후 sealed bag 으로 유지해야 함.

### 7.2 출처

**Internal (Confluence)**
- `Secure Boot Threat Model` — FI/SCA/Rollback/TOCTOU 매트릭스
- `Negative Scenario Catalog` — 5 카테고리 분류

**External**
- Common Criteria *AVA_VAN* (Vulnerability Analysis) — attack potential 평가
- *The Hardware Hacker* (Andrew Huang) — FI / SCA 실제 사례
- NIST SP 800-90B — 엔트로피 / 글리치 검출

## 다음 단계

- 📝 [**Module 05 퀴즈**](quiz/05_attack_surface_and_defense_quiz.md)
- ➡️ [**Module 06 — Quick Reference Card**](06_quick_reference_card.md): 위 다섯 모듈을 한 페이지 치트시트로 응축.

<div class="chapter-nav">
  <a class="nav-prev" href="../04_boot_device_and_boot_mode/">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">Boot Device & Boot Mode (부팅 장치와 부팅 모드)</div>
  </a>
  <a class="nav-next" href="../06_quick_reference_card/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">SoC Secure Boot Flow — Quick Reference Card</div>
  </a>
</div>


--8<-- "abbreviations.md"
--8<-- "_inc/topic_abbr.md"
