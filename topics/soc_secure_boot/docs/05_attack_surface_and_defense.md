# Module 05 — Attack Surface & Defense

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Identify** Secure Boot의 공격 표면 카테고리 (Fault Injection, Side-Channel, Rollback, TOCTOU, JTAG)
    - **Apply** 다층 방어 (HW: glitch detector / SRAM lock, SW: 이중 검증 / anti-rollback, 설계: key hierarchy / crypto agility)
    - **Trace** 실제 공격 사례 (Glitchy Descriptor on iPhone, FROST attack 등)
    - **Plan** Threat model을 작성해 우선순위 결정

!!! info "사전 지식"
    - [Module 01-04](01_hardware_root_of_trust.md)
    - 보안 취약점 / 공격 모델 일반

!!! tip "💡 이해를 위한 비유"
    **Attack Surface** ≈ **성벽의 모든 출입구 + 약점 — 정문(API), 후문(JTAG), 비밀통로(side-channel)**

    Production HW 에서 JTAG, debug bus, side-channel, fault injection, supply chain 모두 surface. Defense in depth.

---

## 핵심 개념
**Secure Boot 공격 표면은 다층적(FI, Rollback, Side-Channel, JTAG, TOCTOU)이다. 방어도 다층 접근이 필요: HW (글리치 감지, SRAM Lock) + SW (이중 검증, Anti-Rollback) + 설계 (키 계층, Crypto Agility).**

---

## 공격 표면 맵

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

---

## (1) Fault Injection (글리치 공격)

### 공격 원리
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

### 공격 방법

| 방법 | 원리 | 장비 | 정밀도 |
|------|------|------|--------|
| 전압 글리치 | 순간적 VDD 강하/스파이크 → CPU 오동작 | ChipWhisperer (~$300) | 중간 |
| EM Fault | EM 펄스로 특정 회로 교란 | EM 프로브 + 펄스 발생기 | 높음 |
| 레이저 Fault | 레이저로 특정 트랜지스터 플립 | 레이저 스테이션 ($100K+) | 매우 높음 |

### 방어 (다층)
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

**면접 키포인트**: "Fault Injection 방어의 핵심은 중복성(redundancy) — 이중 검증, 결과 교차 확인, 별도의 Flow Integrity 검사. 단일 글리치로는 모든 방어를 동시에 무력화할 수 없다."

---

## (5) Rollback Attack (다운그레이드 공격)

### 공격 원리
```
v1.0 --- 취약점 발견! --→ v2.0 (패치됨)

공격자:
  1. 정당하게 서명된 v1.0 이미지 보관
  2. v2.0 배포 후, Flash를 v1.0으로 교체
  3. v1.0은 유효한 서명 보유 → Secure Boot PASS!
  4. v1.0 취약점 악용

  → 서명은 "누가 만들었는가"만 보장, "최신인가"는 보장하지 않음
```

### 방어: Anti-Rollback Counter
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

---

## (3) Side-Channel Attack (부채널 공격)

### 공격 원리
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

### 방어

| 기법 | 원리 |
|------|------|
| Constant-time 구현 | 키 값과 무관하게 동일한 연산 시간 |
| 전력 균형화 | 더미 연산 추가로 전력 패턴 균등화 |
| 마스킹 | 중간값에 랜덤 마스크 적용 |
| HW Crypto Engine | 위 모든 방어를 하드웨어로 구현 |

**이것이 BootROM이 HW Crypto Engine을 사용해야 하는 이유** — SW RSA/ECDSA 구현은 부채널 방어가 극히 어렵다.

---

## (7) JTAG/Debug Port 공격

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

---

## (10) TOCTOU (Time-of-Check-to-Time-of-Use)

### 공격 원리
```
정상:
  (1) Check: verify(SRAM의 BL2) → PASS
  (2) Use:   jump_to(SRAM의 BL2)

TOCTOU 공격:
  (1) Check: verify(SRAM의 BL2) → PASS
      | 검증과 사용 사이에 DMA가 SRAM 내용을 악성 코드로 교체!
  (2) Use:   jump_to(SRAM의 악성 코드)
```

### 방어

| 방어 | 설명 |
|------|------|
| SRAM Lock | 검증 후 HW적으로 메모리 영역 쓰기 보호 |
| DMA 비활성화 | 부팅 중 DMA 컨트롤러 비활성화로 외부 접근 차단 |
| Verify-in-place | 보안 메모리로 복사 후, 그곳에서만 검증+실행 |
| Hash 재검사 | Jump 직전에 해시 재계산 (이중 검증) |

**면접 킬러 포인트**: "TOCTOU 방어를 위해 BootROM은 BL2를 Internal SRAM에 로드하고, 검증 후 HW적으로 해당 영역을 쓰기 보호한다. External DRAM은 DMA를 통한 TOCTOU에 취약하지만, Internal SRAM 접근은 버스 패브릭 레벨에서 차단할 수 있다."

---

## 종합 공격 & 방어 테이블

| 공격 | 대상 | 난이도 | 방어 | DV 검증 방법 |
|------|------|--------|------|-------------|
| Fault Injection | 검증 로직 | 중간 | 이중 검증, 글리치 감지기 | verify 결과 force flip → abort 확인 |
| Rollback | FW 버전 | 낮음 | Anti-Rollback Counter (OTP/RPMB) | 구버전 이미지 로드 → reject 확인 |
| Side-Channel | Crypto 키 | 높음 | HW Crypto, Constant-time | HW 레벨 (보통 별도 팀) |
| JTAG | 전체 시스템 | 낮음 | OTP 비활성화, Secure JTAG | JTAG disable 비트 설정 → 접근 시도 → 차단 확인 |
| TOCTOU | 검증된 이미지 | 높음 | SRAM Lock, DMA 비활성화 | 검증 후 메모리 쓰기 시도 → 차단 확인 |
| Flash 교체 | 부팅 이미지 | 낮음 | 서명 검증 | 변조 이미지 로드 → verify fail → abort 확인 |
| ROM Exploit | BootROM 코드 | 매우 높음 | 코드 최소화, ROM Patch | 코드 리뷰 + 정형 검증 |

---

## Negative Test 시나리오 프레임워크

공격 카테고리별로 정리하면 면접에서 구조적 답변이 가능하다:

### 카테고리 1: 서명/인증 실패
- 잘못된 서명의 BL2 이미지 → verify fail → boot abort
- 유효하지 않은 인증서 (만료, 잘못된 키) → reject
- ROTPK 해시 불일치 (OTP vs 인증서) → reject

### 카테고리 2: Rollback/버전
- FW 버전이 Anti-Rollback Counter 미만 → reject
- 카운터 엣지 케이스: 카운터 최대값 도달 시 동작

### 카테고리 3: Fault/Tamper
- verify 결과 Force-flip → 이중 검증이 포착
- 전압 글리치 시뮬레이션 → 글리치 감지기 응답
- 검증 후 메모리 변조 (TOCTOU) → SRAM Lock이 쓰기 차단

### 카테고리 4: 부팅 장치/입력
- 손상된 부팅 이미지 (불완전, 잘린 이미지, CRC 에러) → 정상적 실패 처리
- 부팅 장치 무응답 → 타임아웃 후 Fallback
- 비정상 크기 이미지 (0 bytes, 초과 크기) → 버퍼 오버플로 없음

### 카테고리 5: 설정
- Secure Boot 활성화 + 미서명 FW → 무조건 reject
- JTAG 비활성화 + JTAG 접근 시도 → 차단
- 유효하지 않은 Boot Mode OTP 설정 → Safe State 진입

**면접 팁**: "Negative 시나리오 3개 이상 나열하세요"라는 질문에 단순히 나열하지 말고 카테고리화하라. "서명 카테고리에서 2개, Rollback 1개, Fault 2개, 입력 1개 — 총 6개입니다." 구조적 사고 = 시니어 엔지니어 인상.

---

## DV 관점 — UVM force/release로 보안 공격 재현

### Active Driver의 force/release 활용

기존 Legacy 환경에서는 Negative 시나리오마다 수동으로 force 문을 작성했다. UVM Active Driver는 이를 체계적으로 관리한다:

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

### 주요 공격별 DV 구현 방법

| 공격 | force 대상 | 주입 시점 | 검증 포인트 |
|------|-----------|----------|------------|
| FI (verify 우회) | verify 결과 레지스터 | 검증 완료 직후 | 이중 검증 불일치 → abort |
| TOCTOU | SRAM 데이터 영역 | 검증 후 ~ jump 전 | SRAM Lock이 쓰기 차단 |
| JTAG 공격 | JTAG enable 신호 | 부팅 중 아무 때나 | OTP disable 시 접근 차단 |
| Crypto 출력 변조 | HW Crypto 출력 | Crypto 연산 완료 시 | 검증 실패 → abort |
| Anti-RB 우회 | OTP 카운터 값 | 부팅 초기 | force 불가 또는 검증 실패 |

**핵심**: Passive 모니터링으로는 "공격 시 DUT가 올바르게 방어하는가?"를 검증할 수 없다. Active Driver가 **공격자 역할**을 하여 방어 메커니즘을 능동적으로 검증한다.

자세한 Active Driver 아키텍처는 **Unit 7 (DV 방법론)**에서 다룸.

---

## Q&A

**Q: Secure Boot에서 Fault Injection을 어떻게 방어하는가?**
> "핵심 원리는 중복성(redundancy)이다. (1) 이중 검증 — 서명을 두 번 검증하고 결과를 교차 확인. (2) Flow Integrity — 각 단계에서 Magic Value를 기록하고 Jump 전에 모두 검증. (3) HW 글리치 감지기 — 전압/클럭 이상 감지 센서가 리셋 또는 Lockdown 트리거. (4) 타이밍 랜덤화 — 정밀한 글리치 타겟팅 방지. 단일 글리치로는 모든 층을 동시에 무력화할 수 없다."

**Q: TOCTOU란 무엇이고 어떻게 방어하는가?**
> "Time-of-Check-to-Time-of-Use — 서명 검증과 실행 사이의 시간 차이. 공격자가 이 간격에 DMA로 검증된 이미지를 악성 코드로 교체할 수 있다. 방어: 검증 후 SRAM 영역을 HW적으로 쓰기 보호, 부팅 중 DMA 비활성화, 선택적으로 Jump 전 해시 재검증."

**Q: BootROM 검증 엔지니어로서 Negative Test 전략을 설명하라.**
> "공격 유형별로 분류한다: (1) Crypto 실패 — 잘못된 서명, 불량 인증서, ROTPK 불일치. (2) 버전 공격 — Anti-RB Counter 미만으로 Rollback. (3) HW 변조 — verify 결과 Force-flip, TOCTOU 메모리 쓰기. (4) 입력 손상 — 잘린 이미지, 초과 크기 버퍼. (5) 설정 — Secure Boot ON 상태에서 미서명 FW, JTAG 비활성화 시 접근 시도. 각 시나리오에서 예상 응답(abort, fallback, lockdown)을 검증한다."

---

!!! danger "❓ 흔한 오해"
    **오해**: JTAG 만 disable 하면 충분

    **실제**: JTAG 외에 boundary scan, debug bus, scan chain, observation pin 등 다축. Side-channel (power, EM, timing) 도 별도 영역.

    **왜 헷갈리는가**: "가시적 인터페이스만 차단" 이라는 직관. 실제 attack 은 무수한 sub-channel.

!!! warning "실무 주의점 — JTAG 가 production 출하 시 disable 되지 않음"
    **현상**: 양산 chip 을 거꾸로 분석해 보니 JTAG TAP 이 살아 있어 debug 권한으로 SRAM/레지스터에 접근, 부팅 중간 단계의 키 / 검증 결과를 읽거나 강제로 덮어쓸 수 있다.

    **원인**: JTAG disable 이 OTP fuse 의 `jtag_lock` 비트와 연결돼 있는데, 양산 라인에서 해당 fuse 를 blow 하지 않거나, BootROM 이 fuse 값을 읽어 TAP controller 를 잠그는 시퀀스를 누락. Test/bring-up 편의 때문에 default 가 "open" 으로 남는 경우가 흔함.

    **점검 포인트**: production OTP profile 에서 JTAG 가 닫혔는가 (TAP IDCODE 외 응답 차단), 그리고 secure boot 실패 시 fail-secure 로 JTAG 가 닫힌 채 정지하는가 (debug 우회 금지).

## 핵심 정리

- **공격 표면**: Fault Injection (전압/클럭 글리치, 레이저), Side-Channel (전력/EM/timing), Rollback (이전 버전 강제), TOCTOU (verify ↔ use 사이 race), JTAG (debug port).
- **다층 방어**:
  - **HW**: glitch detector, SRAM lock-down, key isolation, anti-tamper mesh
  - **SW**: 이중 검증, anti-rollback counter, secure storage
  - **설계**: key hierarchy (개별 침해가 전체 영향 안 가게), crypto agility (RSA → PQC 마이그레이션 대비)
- **Threat model**: Production attacker (cheap, scalable) vs nation-state attacker (expensive, targeted) — 방어 수준 결정.
- **실 사례**: Glitchy Descriptor (iPhone bootloader bypass), Spectre/Meltdown (TEE 누출).

## 다음 단계

- 📝 [**Module 05 퀴즈**](quiz/05_attack_surface_and_defense_quiz.md)
- ➡️ [**Module 06 — BootROM DV**](07_bootrom_dv_methodology.md)

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
