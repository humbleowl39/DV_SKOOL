# Unit 1: Hardware Root of Trust (하드웨어 신뢰 기반)

<div class="learning-meta">
  <span class="meta-badge meta-level-advanced">📊 Advanced</span>
</div>

## 핵심 개념
**HW RoT = BootROM (변경 불가능한 코드) + OTP (ROTPK 해시 + 보안 설정)**

"누가 검증자를 검증하는가?" — 이 닭과 달걀 문제를 깨뜨리는 신뢰의 닻(Trust Anchor).

---

## 왜 하드웨어 기반인가?

| 속성 | SW RoT | HW RoT |
|------|--------|--------|
| 변조 저항성 | Flash 덮어쓰기 가능 | ROM은 물리적으로 쓰기 불가 |
| 공격 표면 | OS/부트로더 취약점 | HW 레벨 공격(FIB) 필요 |
| 신뢰 근거 | 순환: "이 SW를 누가 검증?" | 제조 시점 고정, 순환 없음 |
| Reset 후 상태 | 메모리 내용 보장 불가 | ROM/OTP 항상 동일 |

**핵심 논리**: "SW는 순환 신뢰 문제를 만든다 — 검증자를 누가 검증하나? HW RoT는 제조 시점에 고정되고 런타임에 변경 불가능하므로 이 순환을 끊는다."

---

## BootROM의 역할

```
Power-On Reset
     |
     v
+-------------------------------+
|          BootROM               |
|                                |
|  1. CPU/보안 HW 초기화          |
|     - Crypto Engine 활성화     |
|     - Security Perimeter 설정  |
|     - Watchdog 타이머 시작     |
|                                |
|  2. Boot Mode 결정             |
|     - Boot Pinstrap 읽기      |
|     - OTP Boot Config 읽기    |
|                                |
|  3. BL2 이미지 로드             |
|     - Boot Device에서 읽기     |
|     - Internal SRAM에 적재     |
|                                |
|  4. BL2 서명 검증               |
|     - OTP에서 ROTPK 해시 읽기  |
|     - 인증서의 공개키 검증      |
|     - BL2 이미지 해시 검증      |
|     - 실패 → 차순위 Boot Mode  |
|                                |
|  5. BL2로 Jump                 |
+-------------------------------+
```

### BootROM 코드의 제약

| 제약 | 이유 |
|------|------|
| 동적 메모리 할당 불가 | SRAM 크기 고정, heap 관리 복잡성 배제 |
| 외부 라이브러리 의존 불가 | ROM에 모든 코드가 자체 포함되어야 함 |
| 코드 크기 엄격 제한 (수십~수백 KB) | Mask ROM 면적 = 실리콘 비용 |
| 버그 수정 불가 | 포토마스크 고정 후 변경 불가능 |

---

## OTP 구현 기술 — eFuse vs Antifuse

OTP는 "개념"이고, eFuse와 Antifuse는 그것을 구현하는 "물리적 기술"이다.

| | eFuse | Antifuse |
|--|-------|---------|
| **동작 원리** | 전류로 퓨즈 **끊음** (blow) → 도통→차단 | 전압으로 절연층 **파괴** → 차단→도통 |
| **초기 상태** | 도통 (연결됨, 읽으면 0) | 차단 (끊어짐, 읽으면 0) |
| **프로그래밍** | 높은 전류 → 금속 라인 용융 | 높은 전압 → 산화막 절연 파괴 |
| **면적** | 상대적으로 큼 (두꺼운 금속 필요) | 작음 (게이트 산화막 활용) |
| **보안성** | 낮음 — FIB로 재연결 가능 (물리 공격) | 높음 — 파괴된 절연층 복원 불가 |
| **신뢰성** | 높음 — 성숙한 기술 | 중간 — 읽기 마진 관리 필요 |
| **비용** | 저렴 (표준 CMOS 공정) | 비쌈 (추가 공정 단계) |
| **주요 용도** | 범용 SoC, 모바일 AP | 고보안 칩, 스마트카드, 군용 |

```
eFuse (blow 전):    ────[==]────  (도통)
eFuse (blow 후):    ────[✕✕]────  (차단) ← 전류로 금속 용융

Antifuse (프로그램 전): ────| |────  (차단, 절연층)
Antifuse (프로그램 후): ────[==]────  (도통) ← 전압으로 절연 파괴
```

**면접 팁**: "OTP"라고 말할 때 eFuse인지 Antifuse인지 구분할 수 있으면 물리적 보안에 대한 깊은 이해를 보여줄 수 있다. 보안이 최우선이면 Antifuse(FIB 복원 불가), 비용/면적이 우선이면 eFuse.

---

## OTP/eFuse — 변경 불가능한 보안 저장소

| 필드 | 역할 | 비고 |
|------|------|------|
| ROTPK Hash | 최상위 공개키 해시 | 전체 Chain of Trust의 신뢰 기반 |
| Secure Boot Enable | 서명 검증 활성화 비트 | 한번 설정하면 비활성화 불가 |
| JTAG Disable | 디버그 포트 차단 | 양산 시 Blow |
| Anti-Rollback Counter | FW 다운그레이드 방지 카운터 | 버전별 증가 |
| Boot Device Config | 기본 부팅 장치 설정 | Pinstrap과 조합 |
| AES Root Key | 이미지 복호화 키 (선택) | Secure Storage |
| Chip Unique ID | 칩 고유 식별자 | Device Attestation 용 |

---

## BootROM 버그 — ROM Patch 메커니즘

Mask ROM은 제조 후 수정이 불가능하므로, 버그 발견 시 대응 수단이 반드시 사전 설계되어야 한다.

### ROM Patch 테이블 구조

```
OTP/Secure SRAM 내 패치 영역:

+------------------------------------------+
| Patch Table Header                        |
|  - Magic Number (유효성 검사)             |
|  - Patch Count (활성 패치 수)             |
|  - Signature (패치 테이블 전체 서명)       |
+------------------------------------------+
| Patch Entry #0                            |
|  - Match Address: 0x0000_1234 (원본 주소) |
|  - Redirect Address: 0x2000_0100 (패치)   |
|  - Enable Bit: 1                          |
+------------------------------------------+
| Patch Entry #1                            |
|  - Match Address: 0x0000_5678             |
|  - Redirect Address: 0x2000_0200          |
|  - Enable Bit: 1                          |
+------------------------------------------+
| ...                                       |
| Patch Entry #N-1  (보통 8~16개 슬롯)      |
+------------------------------------------+
| Patch Code Area                           |
|  - 실제 수정된 함수 코드가 저장됨          |
+------------------------------------------+
```

### 동작 원리: HW Comparator 방식

```
BootROM 실행 중:

  CPU가 PC = 0x0000_1234 를 fetch하려 할 때
       │
       v
  +------------------+
  | HW Address       |  ← 패치 테이블의 Match Address와
  | Comparator       |     PC를 HW적으로 비교 (매 fetch마다)
  +--------+---------+
           │
     Match?│
     ┌─────┴──────┐
     │ YES        │ NO
     v             v
  Redirect →    정상 ROM
  Patch Code    코드 실행
  (0x2000_0100)
```

**HW Comparator의 장점**: SW 분기문이 아닌 HW 레벨 리다이렉션이므로, ROM 코드 자체를 수정하지 않고도 특정 함수 진입점을 가로챌 수 있다.

### ROM Patch의 3가지 전략

| 전략 | 설명 | 용도 |
|------|------|------|
| **함수 리다이렉션** | 특정 함수 진입점을 통째로 교체 | 로직 버그 수정 |
| **Early BL2 탈출** | BootROM 최소 기능만 사용 후 BL2로 빠르게 점프 | 심각한 버그 회피 |
| **기능 비활성화** | 문제 있는 Boot Device/기능을 비활성화 | 특정 경로 차단 |

### ROM Patch 보안 요구사항

1. **패치 테이블 서명 필수**: 패치 자체도 ROTPK 체인으로 서명 검증 → 미검증 패치 = 공격 벡터
2. **패치 슬롯 유한**: 일반적으로 8~16개 → 슬롯 소진 시 더 이상 패치 불가
3. **패치 코드 크기 제한**: Secure SRAM의 예약 영역 크기에 의존 (보통 수 KB)
4. **Anti-Rollback**: 패치도 버전 관리 → 이전 버전 패치로 롤백 방지

**면접 킬러 포인트**: "ROM Patch는 BootROM의 보험 정책이다. 그러나 슬롯 수와 코드 크기가 유한하므로, Pre-silicon 검증의 완전성이 ROM Patch에 의존하지 않기 위한 최선의 전략이다. 이것이 BootROM DV에 Zero-Defect 목표가 설정되는 근본 이유이다."

---

## Secure Boot Lifecycle States

칩은 제조부터 폐기까지 보안 상태가 단계적으로 변화한다. **각 전환은 비가역적(OTP blow)이므로 되돌릴 수 없다.**

```
+------------------+     OTP Blow      +-------------------+
|   DEVELOPMENT    | ───────────────→  |   PROVISIONING    |
|                  |                   |                   |
| - Secure Boot OFF|                   | - ROTPK 해시 기록  |
| - JTAG 오픈      |                   | - 보안 설정 기록   |
| - 모든 Boot Mode |                   | - 테스트 키 → 양산 |
| - 디버그 자유     |                   |   키 전환          |
+------------------+                   +--------+----------+
                                                |
                                          OTP Blow (비가역)
                                                |
                                                v
+------------------+     OTP Blow      +-------------------+
|   END-OF-LIFE    | ←───────────────  |   PRODUCTION      |
|                  |                   |                   |
| - 키 전부 폐기   |                   | - Secure Boot ON  |
| - 기능 영구 차단  |                   | - JTAG Locked     |
| - 칩 재사용 불가  |                   | - Boot Mode 고정   |
+------------------+                   | - Anti-RB 활성    |
                                       +-------------------+
```

| 상태 | Secure Boot | JTAG | Boot Mode | OTP 상태 |
|------|------------|------|-----------|---------|
| **Development** | OFF | Open | 전체 허용 | Virgin (미프로그래밍) |
| **Provisioning** | ON (테스트 키) | Secure JTAG | 제한적 | ROTPK + 기본 설정 기록 |
| **Production** | ON (양산 키) | Disabled/Locked | OTP 고정 | 전체 보안 설정 완료 |
| **End-of-Life** | N/A | Permanently Off | N/A | 키 폐기 비트 Blown |

**DV 관점**: Lifecycle 전환 검증이 필수 — Development→Production 전환 시 모든 보안 기능이 올바르게 활성화되는지, Production 상태에서 JTAG/USB DL이 정확히 차단되는지 검증해야 한다. OTP Abstraction Layer로 각 Lifecycle 상태를 자동 sweep할 수 있다.

---

## PUF (Physically Unclonable Function) — eFuse/OTP의 대안

### 개념

PUF는 반도체 제조 과정의 **미세한 물리적 편차**(공정 변동, process variation)를 이용하여 칩마다 고유한 "디지털 지문"을 생성하는 기술이다. 키를 **저장**하는 eFuse/OTP와 달리, PUF는 키를 **생성**한다.

```
eFuse/OTP 방식: 키를 "저장"
  ┌──────────┐
  │  eFuse   │  KEY = 0xDEAD_BEEF_CAFE_1234
  │  (OTP)   │  ← 칩에 물리적으로 기록됨
  └──────────┘
  취약: 고급 물리 공격(FIB, 전자현미경)으로 읽기 가능

PUF 방식: 키를 "생성"
  ┌──────────┐     ┌──────────────┐
  │  PUF     │────►│ Key          │────► KEY = 0xDEAD_BEEF_CAFE_1234
  │  Circuit │     │ Derivation   │     ← 전원 켤 때마다 동일한 키 생성
  └──────────┘     │ + Error      │     ← 칩 안에 키가 저장되어 있지 않음!
                   │ Correction   │
                   └──────────────┘
  강점: 물리 공격으로 eFuse를 읽어도 키가 없음
```

### PUF의 유형

| 유형 | 원리 | 특징 |
|------|------|------|
| **SRAM PUF** | 전원 인가 시 SRAM 셀의 초기값이 칩마다 다름 | 추가 회로 불필요, 가장 보편적 |
| **Arbiter PUF** | 두 경로의 전파 지연 차이 | 경량, 모델링 공격에 취약 |
| **Ring Oscillator PUF** | 링 오실레이터 주파수 차이 | 안정적, FPGA에서도 구현 가능 |

### eFuse/OTP vs PUF 비교

| | eFuse/OTP | PUF |
|--|----------|-----|
| **키 존재 형태** | 물리적으로 기록 (퓨즈 상태) | 회로 특성에서 동적 생성 |
| **Chip Decapping** | eFuse 구조 읽기 가능 → 키 추출 | 읽을 것이 없음 → 추출 불가 |
| **키 복제** | eFuse 값을 다른 칩에 프로그래밍 가능 | 물리 편차 복제 불가 (Unclonable) |
| **공급망 공격** | 제조 시 키 주입 과정에서 유출 위험 | 키 주입 과정 자체가 불필요 |
| **환경 안정성** | eFuse 안정적, Antifuse 매우 안정적 | 온도/전압/노화에 의한 변동 → ECC 필요 |
| **추가 비용** | eFuse 저렴, Antifuse 비쌈 | SRAM PUF는 기존 SRAM 활용 → 저렴 |

### PUF의 한계

```
문제: PUF 응답은 매번 미세하게 다름 (노이즈)

  부팅 1회차: PUF → 0xA3F7_2B91
  부팅 2회차: PUF → 0xA3F7_2B90  ← 1비트 차이!
  부팅 3회차: PUF → 0xA3F7_2B91

  해결: Fuzzy Extractor (Error Correction)
  ┌──────────┐     ┌──────────────┐     ┌──────────┐
  │  PUF     │────►│ Fuzzy        │────►│ 안정된 키 │
  │  (노이즈)│     │ Extractor    │     │ (매번 동일)|
  └──────────┘     │ + Helper Data│     └──────────┘
                   └──────────────┘
                         │
                   Helper Data는 공개 가능
                   (키 자체는 노출되지 않음)
```

### HW RoT에서의 PUF 적용

```
[Unit 1의 HW RoT 구조]             [PUF 결합 시]

  BootROM + OTP(eFuse)               BootROM + PUF + OTP(보안 설정만)
     │                                  │
  OTP에 ROTPK 해시 저장               PUF가 칩 고유 키 생성
  OTP에 AES Root Key 저장             → OTP에 키를 저장할 필요 없음
     │                                  │
  키가 eFuse에 "있음"                 키가 어디에도 "없음"
  → 물리 공격으로 추출 가능           → 물리 공격으로 추출 불가
```

### 업계 적용 사례

| 벤더 | 제품 | PUF 적용 |
|------|------|---------|
| **NXP** | S32G (차량 Gateway) | SRAM PUF 기반 디바이스 고유 키 생성 |
| **Marvell** | OCTEON 10 DPU | PUF + Secure Boot 결합 |
| **Fungible** | F1 DPU | PUF + Secure Enclave 키 생성 |
| **Intrinsic ID** | QuiddiKey IP | 다수 SoC 벤더에 SRAM PUF IP 라이선스 |

---

## 흔한 오해

### 1. "BootROM이 Root of Trust이다"
- **틀림**: BootROM만으로는 RoT가 아님. BootROM(코드) + OTP(키/설정)가 **함께** HW RoT를 형성함.
- 왜? BootROM 코드만 있고 OTP에 ROTPK 해시가 없으면 서명 검증 자체가 불가능.

### 2. "OTP는 완벽하게 안전하다"
- **틀림**: OTP는 SW 변조에는 안전하지만, 물리적 공격(FIB, 레이저 Fault Injection)에 취약.
- 대응: OTP 주변에 금속 차폐(Metal Shielding) + Active Tamper Detection 회로 추가.

---

## DV 관점 — OTP 검증 전략

### OTP 검증이 어려운 이유

| 난점 | 설명 |
|------|------|
| 물리 주소 의존성 | OTP 필드의 물리 위치가 SoC마다 다름 |
| 필드 간 의존성 | Secure Boot OFF면 ROTPK 검증이 무의미 → 유효 조합 관리 필요 |
| Program-once 특성 | 레지스터와 달리 write-back 불가 → 시뮬레이션에서 force 필요 |
| 조합 폭발 | Boot Mode × Boot Device × Secure Boot × JTAG × ... → 수백 조합 |

### OTP Abstraction Layer로 해결

```
// Legacy: 물리 주소 하드코딩
force dut.otp_ctrl.mem[0x100] = 32'hDEAD_BEEF;  // 어떤 필드인지 불명확

// Abstraction Layer: 의미 기반 접근
otp_model.secure_boot_en.set(1);
otp_model.boot_device_cfg.set(UFS);
otp_model.rotpk_hash.set(expected_hash);
// → 물리 주소는 Layer가 자동 매핑
// → 유효하지 않은 조합은 자동 필터링
```

자세한 내용은 **Unit 7 (DV 방법론)**에서 다룸.

---

## Q&A

**Q: Root of Trust가 왜 하드웨어 기반이어야 하는가?**
> "Secure Boot는 각 단계가 다음 단계를 검증하는 Chain of Trust이다. 최초 검증자가 SW면 '그 SW를 누가 검증했나?'라는 무한 순환에 빠진다. HW RoT는 제조 시점에 고정되고 런타임에 변경 불가능하므로 이 순환을 끊는다. 구체적으로 BootROM(변경 불가 코드) + OTP(ROTPK 해시, 보안 설정)가 결합되어 HW RoT를 형성한다."

**Q: BootROM 버그는 어떻게 처리하는가?**
> "OTP/Secure SRAM의 ROM Patch 테이블을 사용한다. HW Address Comparator가 매 instruction fetch마다 패치 테이블의 Match Address와 PC를 비교하여, 일치하면 Patch Code 영역으로 리다이렉션한다. 패치 자체도 ROTPK 체인으로 서명 검증을 거쳐야 한다 — 그렇지 않으면 패치 메커니즘이 공격 벡터가 된다. 치명적 버그는 검증된 BL2로 Early Escape하여 워크어라운드를 적용한다. 단, 패치 슬롯은 8~16개로 유한하므로 Pre-silicon 검증의 Zero-Defect가 근본적으로 중요하다."

**Q: eFuse와 Antifuse의 차이는? 보안 관점에서 어떤 것이 유리한가?**
> "eFuse는 전류로 금속 퓨즈를 끊어서 프로그래밍한다 — 비용이 저렴하고 표준 CMOS 공정에서 구현 가능하다. Antifuse는 전압으로 절연층을 파괴하여 도통시킨다 — 면적이 작고, 파괴된 절연층은 복원 불가능하므로 FIB(Focused Ion Beam) 공격에 강하다. 보안 최우선이면 Antifuse, 비용/양산성이 우선이면 eFuse. 대부분의 모바일 AP는 eFuse + Metal Shielding 조합을 사용한다."

**Q: Secure Boot Lifecycle 전환 시 검증해야 할 핵심 포인트는?**
> "비가역적 전환이므로 세 가지를 검증한다: (1) Development→Production 전환 후 Secure Boot가 강제 활성화되는지. (2) Production 상태에서 JTAG Open/USB DL 우회가 불가능한지. (3) ROTPK가 테스트 키에서 양산 키로 올바르게 전환되었는지. 특히 전환 중간 상태 — 예를 들어 Secure Boot은 ON인데 ROTPK가 미기록인 상태 — 가 안전하게 처리되는지가 DV의 핵심 Negative 시나리오다."

<div class="chapter-nav">
  <a class="nav-prev" href="index.md">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">코스 홈</div>
  </a>
  <a class="nav-next" href="02_chain_of_trust_boot_stages.md">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">Chain of Trust & Boot Stages (신뢰 체인과 부팅 단계)</div>
  </a>
</div>
