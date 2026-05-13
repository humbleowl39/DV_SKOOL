# Module 01 — Hardware Root of Trust

<!-- DV-SKOOL-CH-CTX:start -->
<div class="chapter-context" data-cat="soc">
  <a class="chapter-back" href="../">
    <span class="chapter-back-arrow">←</span>
    <span class="chapter-back-icon">🔐</span>
    <span class="chapter-back-text">SoC Secure Boot</span>
  </a>
  <span class="chapter-divider">›</span>
  <span class="chapter-marker">Module 01</span>
</div>
<!-- DV-SKOOL-CH-CTX:end -->

<!-- DV-SKOOL-CH-TOC:start -->
<div class="page-toc">
  <span class="page-toc-label">목차</span>
  <a class="page-toc-link" href="#1-why-care-이-모듈이-왜-필요한가">1. Why care?</a>
  <a class="page-toc-link" href="#2-intuition-비유와-한-장-그림">2. Intuition</a>
  <a class="page-toc-link" href="#3-작은-예-rotpk-hash-한-슬롯의-제조-부팅-검증-여정">3. 작은 예 — ROTPK 한 슬롯 추적</a>
  <a class="page-toc-link" href="#4-일반화-rot-구성-요소와-lifecycle">4. 일반화 — RoT 구성 요소와 Lifecycle</a>
  <a class="page-toc-link" href="#5-디테일-구현-기술-패치-puf-검증-전략">5. 디테일 — 구현 기술/패치/PUF/검증 전략</a>
  <a class="page-toc-link" href="#6-흔한-오해-와-dv-디버그-체크리스트">6. 흔한 오해 + DV 디버그 체크리스트</a>
  <a class="page-toc-link" href="#7-핵심-정리-key-takeaways">7. 핵심 정리</a>
</div>
<!-- DV-SKOOL-CH-TOC:end -->

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Define** Hardware Root of Trust (HW RoT) 와 그 구성 요소 (BootROM, OTP, eFuse, secure key storage) 를 정의할 수 있다.
    - **Trace** ROTPK (Root of Trust Public Key) hash 가 OTP 에 어떻게 저장되고 boot 시 verification 에 어떻게 쓰이는지 추적할 수 있다.
    - **Distinguish** OTP / eFuse / Antifuse / Mask ROM 을 immutability 와 보안 속성 관점에서 구별할 수 있다.
    - **Identify** HW RoT 의 trust anchor 가 깨졌을 때 발생하는 보안 영향 (chain 무효화, 공격 surface 확대) 을 식별할 수 있다.
    - **Justify** 왜 Root of Trust 가 SW 가 아닌 HW 기반이어야 하는지 — 순환 신뢰 (chicken-and-egg) 문제를 들어 설명할 수 있다.

!!! info "사전 지식"
    - 암호 해시 (SHA-256) 의 입출력 크기와 collision resistance 의 직관
    - 비대칭 키 (public/private) — 누가 무엇을 가지고 무엇을 검증하는가
    - SoC 의 power-on reset → boot fetch 흐름 (general)

---

## 1. Why care? — 이 모듈이 왜 필요한가

### 1.1 시나리오 — _신뢰_ 의 _첫 source_ 는 어디?

당신은 Apple iPhone 의 secure boot 설계자. 모든 후속 단계 (BL1 → BL2 → kernel) 가 _서명 검증_ 으로 다음 단계 인증. 그런데:

**문제: 첫 번째 검증자는 _누가_ 검증하나?**

만약 BL1 (첫 boot loader) 도 _공격자가 교체_ 가능하면 → BL1 이 _가짜 서명 검증_ 통과시키고 _임의 OS_ 로드 → 전체 보안 무효.

**해법: HW RoT (Hardware Root of Trust)**:
- **BootROM**: 칩 제조 시점에 _마스크 ROM_ 으로 박힘. _수정 절대 불가능_ — 실리콘 회로 자체.
- **OTP (One-Time Programmable) fuse**: ROTPK (Root of Trust Public Key) 의 _hash_ 만 저장. _한 번 프로그램 후 변경 불가_.
- BootROM 이 _OTP 의 ROTPK hash_ 를 _읽고_ BL1 서명 검증.

**Immutability 의 근거**:
- BootROM 코드 변경 → 칩 자체 교체 필요 (실리콘 수준).
- OTP fuse 변경 → fuse 가 _영구 blown_, 물리적 변경 불가.

이 _hardware 수준의 immutability_ 가 _신뢰의 anchor_. SW 만으로는 _절대_ 만들 수 없는 신뢰.

이후 모든 secure boot 모듈은 **"제조 시점에 한 번 박아 둔 anchor 가 변하지 않는다"** 라는 한 가정에서 출발합니다. ROTPK hash, anti-rollback counter, JTAG lock, secure boot enable bit — 이 모든 것이 _immutable_ 이라는 약속이 깨지면 chain of trust, 서명 검증, 공격 방어가 차례로 무너집니다.

이 모듈을 건너뛰면 이후의 모든 spec/검증 결정이 "그냥 외워야 하는 규칙" 으로 보입니다. 반대로 RoT = BootROM + OTP 결합과 그 immutability 의 _근거_ 를 잡고 나면, 이후 단계에서 만나는 디테일 (왜 ROTPK 는 OTP 에 hash 만 저장하는가, 왜 fallback 경로가 OTP 에 미리 박혀야 하는가) 이 _이유_ 로 보입니다.

---

## 2. Intuition — 비유와 한 장 그림

!!! tip "💡 한 줄 비유"
    **HW RoT** ≈ **황실 옥새 + 공인 인장 규정집**.<br>
    옥새 (BootROM) 는 제조 시점에 주조되어 누구도 모양을 바꿀 수 없다. 인장 규정집 (OTP) 은 발행 후 변경 불가한 도장으로 — "어떤 문서 (image) 에 어떤 옥새 (key) 가 유효한가" 를 영구 기록한다. 이 둘이 결합할 때 비로소 위조 불가능한 신뢰의 출발점이 된다.

### 한 장 그림 — Power-on 직후 trust 가 시작되는 자리

```d2
direction: down

POR: "Power-On Reset"
ROT: "HW RoT (변경 불가 영역)" {
  direction: right
  BROM: "BootROM\nMask ROM (제조 layout 고정)\n- reset vector\n- HW init / crypto enable\n- boot mode 결정\n- BL2 image load + verify\n- sign-fail → halt / fallback"
  OTP: "OTP / eFuse\nROTPK Hash (32 B)\nSecure Boot Enable\nJTAG Lock\nAnti-Rollback Counter\nBoot Device Config\nAES Root Key (선택)"
  BROM -> OTP: "read"
}
NEXT: "BL2 jump (검증 통과 시)\n→ chain of trust 의 다음 link"
POR -> ROT
ROT -> NEXT
```

### 왜 이렇게 설계됐는가 — Design rationale

세 가지 요구가 동시에 풀려야 했습니다.

1. **누가 검증자를 검증하는가?** — SW 만으로 출발하면 무한 순환 (chicken-and-egg). 제조 시점 고정 = 순환을 끊는 유일한 방법.
2. **runtime 변조에 노출되면 안 된다** — Flash 는 덮어쓰기 가능, RAM 은 휘발. ROM 은 물리적으로 쓰기 불가, OTP 는 1회 쓰기 후 비가역.
3. **그래도 약간의 정책은 칩마다 달라야 한다** — ROTPK, JTAG lock, boot device 등은 silicon 별로 다름. 그래서 BootROM (전 칩 공통 코드) 와 OTP (칩별 설정) 가 _분리_.

이 세 요구의 교집합이 BootROM + OTP 이중 구조입니다.

---

## 3. 작은 예 — ROTPK hash 한 슬롯의 제조-부팅 검증 여정

가장 단순한 시나리오. ROTPK 한 슬롯이 (1) 제조 라인에서 OTP 에 박히고, (2) 첫 부팅 시 BootROM 이 그 슬롯을 읽어 BL2 인증서 검증에 사용하는 1 cycle 을 따라갑니다.

```d2
direction: right

PROV: "Provisioning (양산 라인, 1회)" {
  direction: down
  P1: "① 빌드 서버: ROTPK_pub 생성"
  P2: "② SHA-256(ROTPK_pub) = h_rotpk (32 B)"
  P3: "③ OTP write tool\nblow(OTP[ROTPK_HASH], h_rotpk)\nblow(OTP[SECURE_BOOT_EN], 1)"
  P4: "④ ROTPK_HASH 영역 → READ-ONLY 잠금\n(이후 OTP write block)"
  P1 -> P2
  P2 -> P3
  P3 -> P4
}
BOOT: "매 부팅 (현장)" {
  direction: down
  B5: "⑤ POR → BootROM 진입"
  B6: "⑥ Flash 에서 BL2 + cert 를 SRAM 으로 로드"
  B7: "⑦ cert 안의 PK 추출"
  B8: "⑧ SHA-256(PK) 계산"
  B9: "⑨ OTP[ROTPK_HASH] 읽기"
  B10: "⑩ 두 값 == 비교"
  B11: "⑪ 일치 → cert.sig 검증\n불일치 → halt / abort"
  B5 -> B6
  B6 -> B7
  B7 -> B8
  B8 -> B9
  B9 -> B10
  B10 -> B11
}
PROV -> BOOT { style.stroke-dash: 4 }
```

| Step | 누가 | 무엇을 | 의미 |
|---|---|---|---|
| ① | Build server | RSA/ECDSA key pair 생성 | private key 는 HSM, public key (ROTPK) 만 양산 라인으로 전달 |
| ② | Provisioning tool | `h_rotpk = SHA-256(ROTPK_pub)` | 256 B (RSA) 또는 64 B (ECDSA) 키를 32 B hash 로 압축 — OTP 공간 절약 |
| ③ | OTP burner HW | eFuse blow (높은 전류 또는 전압) | 물리적으로 비가역. 한 비트 blow 면 다시 못 돌림 |
| ④ | Provisioning tool | OTP write protection 잠금 | 이후 OTP 영역 자체를 freeze — 양산 칩이 받는 마지막 OTP 명령 |
| ⑤ | SoC HW | Power-on reset → BootROM fetch | reset vector 는 mask ROM 안 — 변경 불가 |
| ⑥ | BootROM | DMA / SPI / UFS 로 BL2 + cert 로드 | 정확한 device 는 OTP[BOOT_DEV_CFG] 가 결정 |
| ⑦ | BootROM | cert parse → PK 필드 추출 | cert format 은 ARM TF-A 의 X.509 변형 등 |
| ⑧ | HW Crypto | SHA-256 (PK) | constant-time, side-channel 방어된 HW |
| ⑨ | BootROM | `read OTP[ROTPK_HASH]` | OTP read 는 단순 mem-mapped read |
| ⑩ | BootROM | 32 B 비교 — _byte-wise constant-time_ | timing leak 방어. 한 byte 라도 다르면 fail |
| ⑪ | BootROM | match → 다음 검증 단계, mismatch → halt | mismatch 시 fallback 도 OTP 정책에 따라 결정 |

```c
// ⑥~⑪ 의 BootROM 측 의사코드. 실제 production 코드는 constant-time 비교 + glitch 이중 검증.
status_t verify_rotpk(const uint8_t *cert_pk, size_t pk_len) {
    uint8_t h_calc[32];
    uint8_t h_otp[32];
    crypto_hw_sha256(cert_pk, pk_len, h_calc);   // ⑧
    otp_read(OTP_ROTPK_HASH_OFFSET, h_otp, 32);  // ⑨
    if (constant_time_memcmp(h_calc, h_otp, 32) != 0) {  // ⑩
        log_event(ROTPK_MISMATCH_ERR);
        return FAIL;                                       // ⑪ → halt
    }
    return SUCCESS;
}
```

!!! note "여기서 잡아야 할 두 가지"
    **(1) OTP 에는 PK 자체가 아니라 PK 의 _hash_ 가 들어간다** — 32 B 고정 = OTP 공간 효율 + 알고리즘 (RSA/ECDSA) 변경에도 OTP 폭이 안 늘어남.<br>
    **(2) 비교는 한 번이 아니라 _두 번_ 한다** (production 코드) — glitch attack 으로 한 번의 == 분기를 건너뛰는 것을 막기 위해. 단일 글리치로 두 번의 독립 검증을 동시에 무력화하기는 매우 어렵다.

---

## 4. 일반화 — RoT 구성 요소와 Lifecycle

### 4.1 HW RoT 의 핵심 등식

> **HW RoT = BootROM (변경 불가능한 코드) + OTP (변경 불가능한 키/설정)**

하나라도 빠지면 trust anchor 성립 불가:

- BootROM 만 있고 OTP 가 비어 있으면 → 검증할 기준 (ROTPK hash) 이 없음.
- OTP 만 있고 BootROM 이 변경 가능하면 → 공격자가 검증 함수를 nop 으로 패치 가능.

### 4.2 SW vs HW RoT — 왜 HW 가 필수인가

| 속성 | SW RoT | HW RoT |
|------|--------|--------|
| 변조 저항성 | Flash 덮어쓰기 가능 | ROM 은 물리적으로 쓰기 불가 |
| 공격 표면 | OS / 부트로더 취약점 | HW 레벨 공격 (FIB) 필요 |
| 신뢰 근거 | 순환: "이 SW 를 누가 검증?" | 제조 시점 고정, 순환 없음 |
| Reset 후 상태 | 메모리 내용 보장 불가 | ROM/OTP 항상 동일 |

**핵심 논리**: SW 는 순환 신뢰 문제를 만든다 — _검증자를 누가 검증하나?_ HW RoT 는 제조 시점에 고정되고 runtime 변경 불가능하므로 이 순환을 끊는다.

### 4.3 Secure Boot Lifecycle 4 상태

칩은 제조부터 폐기까지 보안 상태가 단계적으로 변화. **각 전환은 비가역적 (OTP blow)** 이므로 되돌릴 수 없습니다.

```d2
direction: right

INITIAL { shape: circle; style.fill: "#333" }
INITIAL -> DEVELOPMENT
DEVELOPMENT -> PROVISIONING: "OTP Blow"
PROVISIONING -> PRODUCTION: "OTP Blow (비가역)"
PRODUCTION -> END_OF_LIFE: "OTP Blow"
# unparsed: DEVELOPMENT : DEVELOPMENT
# unparsed: DEVELOPMENT : - Secure Boot OFF
# unparsed: DEVELOPMENT : - JTAG 오픈
# unparsed: DEVELOPMENT : - 모든 Boot Mode
# unparsed: DEVELOPMENT : - 디버그 자유
# unparsed: PROVISIONING : PROVISIONING
# unparsed: PROVISIONING : - ROTPK 해시 기록
# unparsed: PROVISIONING : - 보안 설정 기록
# unparsed: PROVISIONING : - 테스트 키 → 양산 키 전환
# unparsed: PRODUCTION : PRODUCTION
# unparsed: PRODUCTION : - Secure Boot ON
# unparsed: PRODUCTION : - JTAG Locked
# unparsed: PRODUCTION : - Boot Mode 고정
# unparsed: PRODUCTION : - Anti-RB 활성
# unparsed: END_OF_LIFE : END-OF-LIFE
# unparsed: END_OF_LIFE : - 키 전부 폐기
# unparsed: END_OF_LIFE : - 기능 영구 차단
# unparsed: END_OF_LIFE : - 칩 재사용 불가
```

| 상태 | Secure Boot | JTAG | Boot Mode | OTP 상태 |
|------|------------|------|-----------|---------|
| **Development** | OFF | Open | 전체 허용 | Virgin (미프로그래밍) |
| **Provisioning** | ON (테스트 키) | Secure JTAG | 제한적 | ROTPK + 기본 설정 기록 |
| **Production** | ON (양산 키) | Disabled/Locked | OTP 고정 | 전체 보안 설정 완료 |
| **End-of-Life** | N/A | Permanently Off | N/A | 키 폐기 비트 Blown |

이 4 상태 + 전환 비가역성이 곧 OTP 검증의 핵심 invariant — provisioning 중간 상태에서 칩이 양산 라인을 빠져나가면 절대 회복 불가.

---

## 5. 디테일 — 구현 기술 / 패치 / PUF / 검증 전략

### 5.1 BootROM 의 책임과 제약

```d2
direction: down

POR: "Power-On Reset"
S1: "1. CPU/보안 HW 초기화\n- Crypto Engine 활성화\n- Security Perimeter 설정\n- Watchdog 타이머 시작"
S2: "2. Boot Mode 결정\n- Boot Pinstrap 읽기\n- OTP Boot Config 읽기"
S3: "3. BL2 이미지 로드\n- Boot Device에서 읽기\n- Internal SRAM에 적재"
S4: "4. BL2 서명 검증\n- OTP에서 ROTPK 해시 읽기\n- 인증서의 공개키 검증\n- BL2 이미지 해시 검증\n- 실패 → 차순위 Boot Mode"
S5: "5. BL2로 Jump"
POR -> S1
S1 -> S2
S2 -> S3
S3 -> S4
S4 -> S5
```

#### BootROM 코드의 제약

| 제약 | 이유 |
|------|------|
| 동적 메모리 할당 불가 | SRAM 크기 고정, heap 관리 복잡성 배제 |
| 외부 라이브러리 의존 불가 | ROM 에 모든 코드가 자체 포함되어야 함 |
| 코드 크기 엄격 제한 (수십~수백 KB) | Mask ROM 면적 = 실리콘 비용 |
| 버그 수정 불가 | 포토마스크 고정 후 변경 불가능 |

### 5.2 OTP 구현 기술 — eFuse vs Antifuse

OTP 는 "개념" 이고, eFuse 와 Antifuse 는 그것을 구현하는 "물리적 기술" 입니다.

| | eFuse | Antifuse |
|--|-------|---------|
| **동작 원리** | 전류로 퓨즈 **끊음** (blow) → 도통→차단 | 전압으로 절연층 **파괴** → 차단→도통 |
| **초기 상태** | 도통 (연결됨, 읽으면 0) | 차단 (끊어짐, 읽으면 0) |
| **프로그래밍** | 높은 전류 → 금속 라인 용융 | 높은 전압 → 산화막 절연 파괴 |
| **면적** | 상대적으로 큼 (두꺼운 금속 필요) | 작음 (게이트 산화막 활용) |
| **보안성** | 낮음 — FIB 로 재연결 가능 (물리 공격) | 높음 — 파괴된 절연층 복원 불가 |
| **신뢰성** | 높음 — 성숙한 기술 | 중간 — 읽기 마진 관리 필요 |
| **비용** | 저렴 (표준 CMOS 공정) | 비쌈 (추가 공정 단계) |
| **주요 용도** | 범용 SoC, 모바일 AP | 고보안 칩, 스마트카드, 군용 |

```
eFuse (blow 전):    ────[==]────  (도통)
eFuse (blow 후):    ────[✕✕]────  (차단) ← 전류로 금속 용융

Antifuse (프로그램 전): ────| |────  (차단, 절연층)
Antifuse (프로그램 후): ────[==]────  (도통) ← 전압으로 절연 파괴
```

**면접 팁**: "OTP" 라고 말할 때 eFuse 인지 Antifuse 인지 구분하면 물리적 보안에 대한 깊은 이해를 보여줄 수 있습니다. 보안이 최우선이면 Antifuse (FIB 복원 불가), 비용/면적이 우선이면 eFuse.

### 5.3 OTP/eFuse 의 표준 필드

| 필드 | 역할 | 비고 |
|------|------|------|
| ROTPK Hash | 최상위 공개키 해시 | 전체 Chain of Trust 의 신뢰 기반 |
| Secure Boot Enable | 서명 검증 활성화 비트 | 한번 설정하면 비활성화 불가 |
| JTAG Disable | 디버그 포트 차단 | 양산 시 Blow |
| Anti-Rollback Counter | FW 다운그레이드 방지 카운터 | 버전별 증가 |
| Boot Device Config | 기본 부팅 장치 설정 | Pinstrap 과 조합 |
| AES Root Key | 이미지 복호화 키 (선택) | Secure Storage |
| Chip Unique ID | 칩 고유 식별자 | Device Attestation 용 |

### 5.4 BootROM 버그 — ROM Patch 메커니즘

Mask ROM 은 제조 후 수정이 불가능하므로, 버그 발견 시 대응 수단이 반드시 _사전 설계_ 되어야 합니다.

#### ROM Patch 테이블 구조

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

#### 동작 원리: HW Comparator 방식

```d2
direction: down

PC: "CPU 가 PC = 0x0000_1234 를 fetch"
CMP: "HW Address Comparator\n(패치 테이블의 Match Address 와\nPC 를 HW 적으로 비교 — 매 fetch 마다)"
YES: "Redirect → Patch Code\n(0x2000_0100)"
NO: "정상 ROM 코드 실행"
PC -> CMP
CMP -> YES: "Match? YES"
CMP -> NO: "Match? NO"
```

**HW Comparator 의 장점**: SW 분기문이 아닌 HW 레벨 리다이렉션이므로, ROM 코드 자체를 수정하지 않고도 특정 함수 진입점을 가로챌 수 있습니다.

#### ROM Patch 의 3가지 전략

| 전략 | 설명 | 용도 |
|------|------|------|
| **함수 리다이렉션** | 특정 함수 진입점을 통째로 교체 | 로직 버그 수정 |
| **Early BL2 탈출** | BootROM 최소 기능만 사용 후 BL2 로 빠르게 점프 | 심각한 버그 회피 |
| **기능 비활성화** | 문제 있는 Boot Device/기능을 비활성화 | 특정 경로 차단 |

#### ROM Patch 보안 요구사항

1. **패치 테이블 서명 필수**: 패치 자체도 ROTPK 체인으로 서명 검증 → 미검증 패치 = 공격 벡터
2. **패치 슬롯 유한**: 일반적으로 8~16개 → 슬롯 소진 시 더 이상 패치 불가
3. **패치 코드 크기 제한**: Secure SRAM 의 예약 영역 크기에 의존 (보통 수 KB)
4. **Anti-Rollback**: 패치도 버전 관리 → 이전 버전 패치로 롤백 방지

**면접 킬러 포인트**: "ROM Patch 는 BootROM 의 보험 정책이다. 그러나 슬롯 수와 코드 크기가 유한하므로, Pre-silicon 검증의 완전성이 ROM Patch 에 의존하지 않기 위한 최선의 전략이다. 이것이 BootROM DV 에 Zero-Defect 목표가 설정되는 근본 이유다."

### 5.5 PUF (Physically Unclonable Function) — eFuse/OTP 의 대안

PUF 는 반도체 제조 과정의 **미세한 물리적 편차** (process variation) 를 이용하여 칩마다 고유한 "디지털 지문" 을 생성하는 기술입니다. 키를 **저장** 하는 eFuse/OTP 와 달리, PUF 는 키를 **생성** 합니다.

```d2
direction: right

EFUSE: "eFuse/OTP 방식: 키를 저장" {
  direction: right
  EF: "eFuse (OTP)\nKEY = 0xDEAD_BEEF_CAFE_1234\n(칩에 물리적으로 기록됨)"
  EFNOTE: "취약: 고급 물리 공격\n(FIB, 전자현미경) 으로 읽기 가능"
  EF -> EFNOTE { style.stroke-dash: 4 }
}
PUF: "PUF 방식: 키를 생성" {
  direction: right
  PC: "PUF Circuit"
  KD: "Key Derivation\n+ Error Correction"
  KOUT: "KEY = 0xDEAD_BEEF_CAFE_1234\n(전원 켤 때마다 동일한 키 생성\n칩 안에 키가 저장되어 있지 않음)"
  PNOTE: "강점: 물리 공격으로\neFuse 를 읽어도 키가 없음"
  PC -> KD
  KD -> KOUT
  KOUT -> PNOTE { style.stroke-dash: 4 }
}
```

#### PUF 의 유형

| 유형 | 원리 | 특징 |
|------|------|------|
| **SRAM PUF** | 전원 인가 시 SRAM 셀의 초기값이 칩마다 다름 | 추가 회로 불필요, 가장 보편적 |
| **Arbiter PUF** | 두 경로의 전파 지연 차이 | 경량, 모델링 공격에 취약 |
| **Ring Oscillator PUF** | 링 오실레이터 주파수 차이 | 안정적, FPGA 에서도 구현 가능 |

#### eFuse/OTP vs PUF 비교

| | eFuse/OTP | PUF |
|--|----------|-----|
| **키 존재 형태** | 물리적으로 기록 (퓨즈 상태) | 회로 특성에서 동적 생성 |
| **Chip Decapping** | eFuse 구조 읽기 가능 → 키 추출 | 읽을 것이 없음 → 추출 불가 |
| **키 복제** | eFuse 값을 다른 칩에 프로그래밍 가능 | 물리 편차 복제 불가 (Unclonable) |
| **공급망 공격** | 제조 시 키 주입 과정에서 유출 위험 | 키 주입 과정 자체가 불필요 |
| **환경 안정성** | eFuse 안정적, Antifuse 매우 안정적 | 온도/전압/노화에 의한 변동 → ECC 필요 |
| **추가 비용** | eFuse 저렴, Antifuse 비쌈 | SRAM PUF 는 기존 SRAM 활용 → 저렴 |

#### PUF 의 한계 — 노이즈와 Fuzzy Extractor

```d2
direction: right

PUF: "PUF\n(노이즈)\n부팅 1회차: 0xA3F7_2B91\n부팅 2회차: 0xA3F7_2B90 (1비트 차이)\n부팅 3회차: 0xA3F7_2B91"
FE: "Fuzzy Extractor\n+ Helper Data"
KEY: "안정된 키\n(매번 동일)"
NOTE: "Helper Data 는 공개 가능\n(키 자체는 노출되지 않음)"
PUF -> FE
FE -> KEY
FE -> NOTE { style.stroke-dash: 4 }
```

#### HW RoT 에서의 PUF 적용

```d2
direction: right

NORMAL: "일반 SoC 의 HW RoT 구조" {
  direction: down
  N1: "BootROM + OTP(eFuse)"
  N2: "OTP 에 ROTPK 해시 저장\nOTP 에 AES Root Key 저장"
  N3: "키가 eFuse 에 있음\n→ 물리 공격으로 추출 가능"
  N1 -> N2
  N2 -> N3
}
WITHPUF: "PUF 결합 시" {
  direction: down
  P1: "BootROM + PUF + OTP(보안 설정만)"
  P2: "PUF 가 칩 고유 키 생성\n→ OTP 에 키를 저장할 필요 없음"
  P3: "키가 어디에도 없음\n→ 물리 공격으로 추출 불가"
  P1 -> P2
  P2 -> P3
}
```

#### 업계 적용 사례

| 벤더 | 제품 | PUF 적용 |
|------|------|---------|
| **NXP** | S32G (차량 Gateway) | SRAM PUF 기반 디바이스 고유 키 생성 |
| **Marvell** | OCTEON 10 DPU | PUF + Secure Boot 결합 |
| **Fungible** | F1 DPU | PUF + Secure Enclave 키 생성 |
| **Intrinsic ID** | QuiddiKey IP | 다수 SoC 벤더에 SRAM PUF IP 라이선스 |

### 5.6 DV 관점 — OTP 검증 전략

#### OTP 검증이 어려운 이유

| 난점 | 설명 |
|------|------|
| 물리 주소 의존성 | OTP 필드의 물리 위치가 SoC 마다 다름 |
| 필드 간 의존성 | Secure Boot OFF 면 ROTPK 검증이 무의미 → 유효 조합 관리 필요 |
| Program-once 특성 | 레지스터와 달리 write-back 불가 → 시뮬레이션에서 force 필요 |
| 조합 폭발 | Boot Mode × Boot Device × Secure Boot × JTAG × ... → 수백 조합 |

#### OTP Abstraction Layer 로 해결

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

자세한 내용은 [Module 07 (DV 방법론)](07_bootrom_dv_methodology.md) 에서 다룹니다.

#### Lifecycle 전환 검증의 우선순위

DV 관점에서 lifecycle 전환은 모두 비가역이므로, 다음을 직접 검증해야 합니다.

- Development → Production 전환 후 모든 보안 기능이 강제 활성화되는가
- Production 상태에서 JTAG / USB DL 우회가 닫혀 있는가
- ROTPK 가 테스트 키 → 양산 키로 정확히 전환되는가
- 전환 _중간_ 상태 (예: Secure Boot ON 인데 ROTPK 미기록) 가 안전하게 처리되는가

마지막 항목이 §6 의 "ROTPK 미기록 + Secure Boot 활성" 디버그 케이스로 이어집니다.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

!!! danger "❓ 오해 1 — 'BootROM 이 Root of Trust 다'"
    **실제**: BootROM 만으로는 RoT 가 아닙니다. BootROM (코드) + OTP (키/설정) 가 **함께** HW RoT 를 형성. BootROM 코드만 있고 OTP 에 ROTPK hash 가 없으면 서명 검증 자체가 불가능합니다.<br>
    **왜 헷갈리는가**: 화이트보드에 그릴 때 BootROM 한 박스만 그리는 관행 + "ROM = root" 라는 단어 연상 때문.

!!! danger "❓ 오해 2 — 'OTP 는 완벽하게 안전하다'"
    **실제**: OTP 는 SW 변조에는 안전하지만, 물리적 공격 (FIB, 레이저 fault injection, decapping + 전자현미경) 에 취약. 대응: OTP 주변에 metal shielding + active tamper detection 회로 추가, eFuse 보다 antifuse 채택.<br>
    **왜 헷갈리는가**: "한번 쓰면 못 바꾼다 = 못 읽는다" 의 혼동. immutability 와 confidentiality 는 다른 속성.

!!! danger "❓ 오해 3 — 'Secure Boot 가 켜지면 안전하다'"
    **실제**: Secure Boot 는 boot chain 무결성만 보장. runtime 보호 (ASLR, kernel hardening, IO 보안), Side-channel 방어, fault injection 방어는 별도. boot 만으로 끝나지 않습니다.<br>
    **왜 헷갈리는가**: marketing 의 "secure boot = full security" 단순화.

!!! danger "❓ 오해 4 — 'PUF 가 있으면 OTP 는 필요 없다'"
    **실제**: PUF 는 _키 생성_ 만 대체합니다. Secure Boot Enable, JTAG Lock, Anti-Rollback Counter 같은 _설정 비트_ 는 여전히 OTP 가 필요합니다. PUF 응답은 부팅마다 동일해야 하지만 응답 자체에 정책 비트를 인코딩할 수 없음.<br>
    **왜 헷갈리는가**: PUF 마케팅이 "키리스 SoC" 로 단순화.

### DV 디버그 체크리스트 (HW RoT 검증에서 자주 보는 실패)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| `ROTPK_MISMATCH` 인데 cert 의 PK 는 정상 | OTP[ROTPK_HASH] 가 0 또는 미프로그래밍 | OTP dump → 32 B 가 all-zero 인지 / hash 가 build server 의 expected 와 일치하는지 |
| OTP write 직후 read 값 불일치 | program-once 특성 — write 안 됨 또는 voltage margin | OTP IP 의 program-pulse log + read margin register |
| BL2 verify FAIL 인데 image 는 골든 | ROTPK 가 _다른 슬롯_ 의 hash 를 가리킴 (multi-slot) | OTP[ROTPK_SLOT_INDEX] vs cert.slot_id |
| Provisioning 중간 상태로 양산 출하 | Secure Boot EN=1 + ROTPK=0 (양산 사고) | 라인 OTP profile log → blow 순서 검증 |
| ROM patch 적용 후 cert 검증 PASS 인데 사실 mismatch | patch 가 ROTPK 캐시를 갱신 안 함 | patch entry vs ROTPK reload 시점 (Module 07 §5 ROM patch 참조) |
| JTAG 가 살아 있어 OTP write 가능 | JTAG disable fuse 가 안 blown | OTP[JTAG_DISABLE] dump + TAP IDCODE response |
| Lifecycle 전환 후 fall-back 으로 dev mode 진입 | dev path 가 Production fuse 검사 누락 | (boot mode × OTP secure flag × pinstrap) 매트릭스 — Module 04 §6 참조 |
| PUF 응답이 부팅마다 다름 | helper data 손상 / Fuzzy Extractor margin | helper-data CRC, ECC syndrome, temperature log |

이 체크리스트는 이후 모듈 (특히 Module 04 boot device, Module 07 DV 방법론) 에서 더 정교한 형태로 다시 나옵니다.

!!! warning "실무 주의점 — ROTPK 미기록 상태에서 Secure Boot 활성화"
    **현상**: OTP 에서 Secure Boot Enable 비트는 blown 됐지만 ROTPK hash 가 기록되지 않은 상태로 칩이 출고된다. 부팅 시 BootROM 이 ROTPK 를 읽어 all-zero 와 비교하여 임의 서명이 통과되거나 즉시 halt 된다.

    **원인**: Lifecycle 전환 스크립트에서 Secure Boot Enable eFuse 와 ROTPK blow 순서가 분리되어 있고, 중간 단계 검증 없이 진행 시 ROTPK 미기록 상태가 양산 칩에 고착된다. OTP 는 재시도 불가이므로 해당 칩은 폐기 대상.

    **점검 포인트**: DV Negative 시나리오에 ROTPK=0 + Secure Boot EN=1 조합을 명시적으로 추가. BootROM 로그에서 `ROTPK_READ` 이후 `ROTPK_ZERO_ERR` 코드 확인. Lifecycle 전환 스크립트의 blow 순서를 ROTPK → Secure Boot Enable 순으로 고정하고 중간 읽기 검증 단계를 삽입.

---

## 7. 핵심 정리 (Key Takeaways)

- **HW RoT = BootROM + OTP** — 둘 중 하나라도 빠지면 trust anchor 성립 불가.
- **OTP 에는 PK 자체가 아니라 hash (32 B)** — 알고리즘/키 크기에 무관한 고정 폭, OTP 공간 절약.
- **eFuse vs Antifuse** — 비용 우선이면 eFuse, FIB 저항 우선이면 antifuse. 둘 다 immutable 이지만 _물리 보안 강도_ 가 다름.
- **PUF 는 키 _생성_, OTP 는 키/설정 _저장_** — PUF 가 와도 OTP 는 정책 비트로 남음.
- **Lifecycle 4 상태의 전환은 모두 비가역** — provisioning 중간 상태가 양산 라인을 빠져나가면 회복 불가, 그래서 lifecycle 검증은 DV 의 1순위.

!!! warning "실무 주의점 (요약)"
    - "ROM Patch 슬롯 8~16 개 = 검증 마지막 보험" — pre-silicon 검증이 ROM Patch 에 의존하지 않게 zero-defect 목표.
    - OTP read protection (lock) 자체도 OTP fuse 로 거는 경우가 많음 — lock fuse 가 안 blown 이면 production 칩에서 OTP 재기록 시도 가능.
    - DV 환경에서 OTP 를 force 로 매번 다른 값을 박는 시나리오는 OTP Abstraction Layer 가 program-once 위반을 자동 차단해야 안전.

### 7.1 자가 점검

!!! question "🤔 Q1 — Hash 저장 이유 (Bloom: Analyze)"
    OTP 에 PK 자체 대신 _hash_ 만 저장하는 결정적 이유 1 가지?
    ??? success "정답"
        **OTP 공간 절약 + 알고리즘 독립성**:
        - RSA-3072 PK 는 384 B, ECC-P256 은 64 B — 알고리즘별로 가변.
        - SHA-256 hash 는 _항상_ 32 B 고정.
        - OTP 영역은 mm² 단위 면적 비용 → 고정 32 B 가 ROI 최적.
        - 추가 이점: PK 알고리즘 변경 시 hash 만 갱신, OTP 레이아웃 불변.

!!! question "🤔 Q2 — Lifecycle 비가역성 (Bloom: Evaluate)"
    Lifecycle 의 4 상태 전환이 모두 _비가역_ 인 설계 결정. 양산 ROI 관점에서 정당화하라.
    ??? success "정답"
        비가역의 정당화:
        - **공격 모델**: 공격자가 Production → Debug 로 _되돌릴 수_ 있으면 모든 보안 무력화.
        - **양산 yield 비용**: 비가역 정책 위반 시 칩 폐기 → DV 단계에서 ROTPK=0 + SecBoot=1 같은 fatal 조합을 _반드시_ 음성 시나리오로 검출해야 폐기율 0 화.
        - **trade-off**: provisioning 실수 = 칩 1 개 손실 vs 가역성 허용 = 전체 fleet 해킹 가능. 후자 손실이 압도적으로 큼.

### 7.2 출처

**Internal (Confluence)**
- `Secure Boot DV Strategy` — BootROM + OTP 검증 사례
- `Lifecycle State Machine` — 4 상태 전환 음성 시나리오

**External**
- NIST SP 800-193 *Platform Firmware Resiliency Guidelines* — RoT 정의
- ARM *Trusted Board Boot Requirements* (TBBR-CLIENT) — ROTPK / OTP / lifecycle 명세

## 다음 단계

- 📝 [**Module 01 퀴즈**](quiz/01_hardware_root_of_trust_quiz.md)
- ➡️ [**Module 02 — Chain of Trust**](02_chain_of_trust_boot_stages.md): trust anchor 위에서 BL1 → BL2 → BL3x → OS 가 신뢰를 어떻게 _전파_ 하는가.

<div class="chapter-nav">
  <a class="nav-prev" href="../">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">코스 홈</div>
  </a>
  <a class="nav-next" href="../02_chain_of_trust_boot_stages/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">Chain of Trust & Boot Stages (신뢰 체인과 부팅 단계)</div>
  </a>
</div>


--8<-- "abbreviations.md"
--8<-- "_inc/topic_abbr.md"
