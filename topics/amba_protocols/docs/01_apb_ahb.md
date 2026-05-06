# Unit 1: APB & AHB

<div class="learning-meta">
  <span class="meta-badge meta-level-intermediate">📊 Intermediate</span>
</div>

!!! objective "학습 목표"
    이 모듈을 마치면:

    - **Distinguish** APB와 AHB의 핸드셰이크/성능/용도 차이를 구분할 수 있다.
    - **Trace** APB 트랜잭션의 SETUP → ACCESS → IDLE 흐름과 AHB의 ADDRESS → DATA 파이프라인을 시퀀스 다이어그램으로 그릴 수 있다.
    - **Implement** AHB-to-APB Bridge의 동작 원리를 코드 또는 의사코드로 설명할 수 있다.
    - **Identify** APB 버전 진화(APB3 → APB4 → APB5)에서 추가된 신호와 그 동기를 매핑할 수 있다.

!!! info "사전 지식"
    - 디지털 회로 기본 (클럭, 동기 FSM)
    - Read/Write 트랜잭션의 일반적 의미
    - SoC top-level 구조에 대한 감각 (CPU ↔ 인터커넥트 ↔ peripheral)

## 왜 이 모듈이 중요한가

**APB는 SoC 레지스터 접근의 사실상 표준**입니다. 거의 모든 IP의 control/status 레지스터는 APB로 노출됩니다. AHB는 ARM 초창기 인터커넥트로 레거시 IP 통합 시 자주 만나며, 단순한 dual-port memory access의 이해 모델로 가치가 있습니다. **둘을 함께 이해하면 AHB-to-APB Bridge라는 SoC 통합의 표준 패턴을 자연스럽게 익힐 수 있습니다**.

## APB (Advanced Peripheral Bus)

### 핵심 개념
**APB = AMBA에서 가장 간단한 버스. 저속 주변장치(레지스터, 타이머, UART, OTP 등)의 설정/상태 접근에 사용. 파이프라인 없음, 단일 트랜잭션.**

### 신호

| 신호 | 방향 (Master→Slave) | 역할 |
|------|-------------------|------|
| PCLK | - | 클럭 |
| PRESETn | - | 리셋 (Active Low) |
| PSEL | M→S | Slave 선택 |
| PENABLE | M→S | 전송 활성화 (2번째 phase) |
| PWRITE | M→S | 1=Write, 0=Read |
| PADDR | M→S | 주소 |
| PWDATA | M→S | 쓰기 데이터 |
| PRDATA | S→M | 읽기 데이터 |
| PREADY | S→M | Slave 준비 (Wait State 삽입) |
| PSLVERR | S→M | 에러 응답 |

### 전송 타이밍

```
         Setup Phase    Access Phase
         (PSEL=1,       (PENABLE=1,
          PENABLE=0)     PREADY로 완료)

PCLK:    ─┐  ┌──┐  ┌──┐  ┌──┐
          └──┘  └──┘  └──┘  └──

PSEL:    ────────────────────
              ┌──────────────

PENABLE: ─────────┌──────────
                   (Access)

PADDR:   ─────XXXX┤ ADDR ├──
PWDATA:  ─────XXXX┤ DATA ├──

PREADY:  ─────────────┐      (1 cycle later = no wait)
                       └──
              또는 여러 cycle 후 = wait state

Write: PSEL + PADDR + PWDATA → PENABLE → PREADY → 완료
Read:  PSEL + PADDR → PENABLE → PREADY + PRDATA → 완료
```

### Wait State (PREADY)

```
No Wait:     Setup → Access(PREADY=1 즉시) → 완료 (2 cycle)
With Wait:   Setup → Access(PREADY=0) → ... → PREADY=1 → 완료

PREADY가 0인 동안 Access Phase가 연장됨
→ 느린 Slave가 시간을 벌 수 있음
```

### DV 검증 포인트

| 항목 | 시나리오 |
|------|---------|
| 기본 R/W | 모든 레지스터 Write → Read Back |
| Wait State | PREADY 지연 → 데이터 정확 |
| Error | PSLVERR 응답 → 올바른 처리 |
| 리셋 | Reset 후 레지스터 기본값 |
| 연속 접근 | Back-to-back 트랜잭션 |

---

## APB 버전 진화: APB3 → APB4 → APB5

### APB3 (AMBA 3, 2003)
원래 APB(AMBA 2)에는 PREADY/PSLVERR이 없었다. APB3에서 추가:
- **PREADY**: Slave가 wait state 삽입 가능 → 느린 Slave 지원
- **PSLVERR**: 에러 응답 가능 → 잘못된 접근 탐지

### APB4 (AMBA 4, 2010) — 현재 가장 많이 사용

| 추가 신호 | 역할 |
|----------|------|
| **PPROT[2:0]** | Protection 정보: [0]=Normal/Privileged, [1]=Secure/Non-Secure, [2]=Data/Instruction |
| **PSTRB[N-1:0]** | Write Byte Strobe: 바이트 단위 쓰기 마스크 (AXI의 WSTRB과 동일 개념) |

```
PSTRB 예시 (32-bit 데이터 버스):
  PSTRB = 4'b1111 → 4바이트 모두 쓰기 (Full Word)
  PSTRB = 4'b0011 → 하위 2바이트만 쓰기 (Half Word)
  PSTRB = 4'b0001 → 최하위 1바이트만 쓰기 (Byte)
  PSTRB = 4'b1100 → 상위 2바이트만 쓰기

PPROT 예시:
  PPROT = 3'b000 → Normal, Secure, Data access
  PPROT = 3'b001 → Privileged, Secure, Data access
  PPROT = 3'b010 → Normal, Non-Secure, Data access

→ TrustZone 기반 SoC에서 Secure/Non-Secure 접근 구분에 필수
```

### APB5 (AMBA 5, 2021)

| 추가 신호 | 역할 |
|----------|------|
| **PWAKEUP** | 저전력 모드에서 트랜잭션 전에 Slave 깨우기 (Clock Gating과 연동) |
| **PAUSER** | User-defined 사이드밴드 (주소 phase) |
| **PWUSER** | User-defined 사이드밴드 (쓰기 데이터 phase) |
| **PRUSER** | User-defined 사이드밴드 (읽기 데이터 phase) |
| **PBUSER** | User-defined 사이드밴드 (응답 phase) |

> **면접 포인트**: "APB4와 APB5의 차이?"
> → APB5는 저전력(PWAKEUP)과 사이드밴드(xUSER)가 핵심. IoT/모바일 SoC의 전력 관리 요구를 반영.

---

## AHB (Advanced High-performance Bus)

### 핵심 개념
**AHB = APB보다 고성능, AXI보다 단순한 중간 버스. 파이프라인(주소/데이터 분리), Burst 전송 지원. 레거시 IP 연결, 단순 DMA에 사용.**

### 신호 (AHB-Lite, 단일 Master)

| 신호 | 방향 | 역할 |
|------|------|------|
| HCLK | - | 클럭 |
| HRESETn | - | 리셋 |
| HADDR | M→S | 주소 |
| HTRANS | M→S | 전송 타입 (IDLE/BUSY/NONSEQ/SEQ) |
| HWRITE | M→S | 1=Write, 0=Read |
| HSIZE | M→S | 전송 크기 (byte/half/word) |
| HBURST | M→S | Burst 타입 (SINGLE/INCR/WRAP) |
| HWDATA | M→S | 쓰기 데이터 (이전 cycle의 주소에 대응) |
| HRDATA | S→M | 읽기 데이터 |
| HREADY | S→M | Slave 준비 (0=Wait) |
| HRESP | S→M | 응답 (OKAY/ERROR) |

### AHB 파이프라인 — APB와의 핵심 차이

```
APB: 주소와 데이터가 같은 phase
AHB: 주소 phase와 데이터 phase가 1 cycle 겹침 (파이프라인)

HCLK:  ─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─
         └─┘ └─┘ └─┘ └─┘ └─┘

HADDR: ─┤A1├─┤A2├─┤A3├─────────  Address Phase
HWDATA:──────┤D1├─┤D2├─┤D3├───  Data Phase (1 cycle 뒤)

  T1: Address A1
  T2: Address A2 + Data D1 ← 파이프라인 겹침!
  T3: Address A3 + Data D2
  T4:            + Data D3

→ 매 cycle 주소와 데이터가 동시 전송 = 대역폭 2배 (APB 대비)
```

### HTRANS (전송 타입)

| 값 | 이름 | 의미 |
|---|------|------|
| 2'b00 | IDLE | 전송 없음 |
| 2'b01 | BUSY | Burst 중이지만 이번 cycle은 전송 안 함 |
| 2'b10 | NONSEQ | Burst의 첫 번째 전송 (또는 단독) |
| 2'b11 | SEQ | Burst의 연속 전송 |

### Burst 타입

| HBURST | 이름 | 동작 |
|--------|------|------|
| 3'b000 | SINGLE | 단일 전송 |
| 3'b001 | INCR | 무한 길이 증가 |
| 3'b010 | WRAP4 | 4-beat 래핑 |
| 3'b011 | INCR4 | 4-beat 증가 |
| 3'b100 | WRAP8 | 8-beat 래핑 |
| 3'b101 | INCR8 | 8-beat 증가 |
| 3'b110 | WRAP16 | 16-beat 래핑 |
| 3'b111 | INCR16 | 16-beat 증가 |

### HRESP 2-Cycle 에러 응답 프로토콜

AHB 에러 응답은 APB와 달리 **2 cycle**이 필요하다. 이유: 파이프라인 때문에 Master가 이미 다음 주소를 발행한 상태이므로, 에러를 알리면서 동시에 파이프라인을 안전하게 취소해야 한다.

```
HCLK:   ─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─
          └─┘ └─┘ └─┘ └─┘ └─┘

HTRANS: ─┤NONSEQ├─┤  SEQ  ├─┤IDLE├─────────
HADDR:  ─┤  A1  ├─┤  A2  ├─┤ -- ├─────────

HREADY: ─────────┘         └─────┘    ┌────  ← Cycle1: HREADY=0 (stall)
                                       └────  ← Cycle2: HREADY=1 (완료)

HRESP:  ─┤OKAY├──┤ ERROR ├──┤ERROR├────────
                  ↑ Cycle 1   ↑ Cycle 2
                  HREADY=0    HREADY=1

동작 순서:
  Cycle 1: Slave가 HRESP=ERROR + HREADY=0 → Master에 에러 알림 + 파이프라인 스톨
           → Master는 이때 이미 발행한 A2 를 취소할 준비
  Cycle 2: Slave가 HRESP=ERROR + HREADY=1 → 에러 전송 완료
           → Master는 A2를 취소하고 IDLE로 전환 (또는 재시도)

왜 2 cycle인가?
  → 파이프라인 구조에서 1 cycle만으로 에러를 알리면
    Master가 이미 발행한 다음 주소(A2)를 처리할 시간이 없음.
    Cycle 1에서 HREADY=0으로 파이프라인을 멈추고,
    Cycle 2에서 에러를 확정하여 안전하게 복구.
```

### WRAP Burst 주소 계산 — 상세 예제

WRAP burst는 캐시 라인 로드에서 critical-word-first를 구현할 때 사용된다.

```
설정: HBURST=WRAP4, HSIZE=Word(4byte), 시작 주소=0x0C

Step 1: Wrap Boundary 계산
  Wrap Size = Beat수 × Beat크기 = 4 × 4 = 16 bytes
  Wrap Boundary = 시작 주소를 Wrap Size로 정렬
  Lower Boundary = 0x0C & ~(16-1) = 0x0C & 0xFFFFFFF0 = 0x00
  Upper Boundary = Lower + Wrap Size = 0x00 + 0x10 = 0x10

Step 2: 주소 시퀀스
  Beat 0: 0x0C  (시작 — critical word)
  Beat 1: 0x0C + 4 = 0x10 → 경계(0x10) 도달 → Wrap → 0x00
  Beat 2: 0x00 + 4 = 0x04
  Beat 3: 0x04 + 4 = 0x08

  최종 순서: 0x0C → 0x00 → 0x04 → 0x08
  (0x00~0x0F 범위의 16바이트를 0x0C부터 순환하며 모두 읽음)

INCR4와 비교:
  INCR4: 0x0C → 0x10 → 0x14 → 0x18 (경계를 넘어감!)
  WRAP4: 0x0C → 0x00 → 0x04 → 0x08 (경계 내에서 순환)

다른 예: WRAP8, HSIZE=Word, 시작 주소=0x24
  Wrap Size = 8 × 4 = 32 bytes (0x20)
  Lower Boundary = 0x24 & ~(0x20-1) = 0x20
  Upper Boundary = 0x20 + 0x20 = 0x40
  순서: 0x24 → 0x28 → 0x2C → 0x30 → 0x34 → 0x38 → 0x3C → 0x20
                                                           ↑ Wrap!
```

### HPROT (Protection Control)

| 비트 | 의미 |
|------|------|
| HPROT[0] | 0=Opcode fetch, 1=Data access |
| HPROT[1] | 0=User mode, 1=Privileged mode |
| HPROT[2] | 0=Non-bufferable, 1=Bufferable |
| HPROT[3] | 0=Non-cacheable, 1=Cacheable |

> APB4의 PPROT과 유사하지만 4비트. Interconnect에서 접근 권한 필터링에 사용.

### DV 검증 포인트

| 항목 | 시나리오 |
|------|---------|
| 파이프라인 | 연속 전송에서 주소/데이터 정렬 정확 |
| Burst | INCR/WRAP 주소 계산 정확 |
| Wait State | HREADY=0 중 파이프라인 유지 (주소/데이터 변하지 않음) |
| Error | HRESP=ERROR 시 2-cycle 응답: Cycle1(HREADY=0)+Cycle2(HREADY=1) |
| IDLE/BUSY | Burst 중 BUSY 삽입 시 동작 |
| WRAP 경계 | Wrap 주소 계산이 경계에서 정확히 순환하는지 |

---

## AHB-to-APB Bridge

SoC에서 AHB와 APB 사이를 연결하는 필수 컴포넌트.

```
AHB Master → AHB Bus → [AHB-APB Bridge] → APB Bus → APB Slaves
                              │
                    프로토콜 변환 수행:
                    1. AHB 파이프라인 → APB 2-phase
                    2. AHB Burst → APB 단일 전송 분해
                    3. HREADY ↔ PREADY 매핑
                    4. HRESP ↔ PSLVERR 매핑

동작 예시 (AHB Write → APB Write):
  T1: AHB Address Phase (HADDR=0x100, HWRITE=1)
  T2: AHB Data Phase (HWDATA=0xFF) + Bridge가 APB Setup 시작 (PSEL=1, PADDR=0x100)
  T3: Bridge가 APB Access (PENABLE=1, PWDATA=0xFF)
  T4: APB Slave가 PREADY=1 → Bridge가 AHB에 HREADY=1 반환

→ 최소 1 cycle의 추가 latency 발생
→ AHB Burst는 Bridge 내부에서 개별 APB 전송으로 분해
```

---

## APB vs AHB 비교

| 항목 | APB | AHB |
|------|-----|-----|
| 복잡도 | 가장 단순 | 중간 |
| 파이프라인 | 없음 (2-phase) | 있음 (주소/데이터 겹침) |
| Burst | 없음 | INCR/WRAP 지원 |
| 최대 대역폭 | 낮음 | 중간 |
| Wait 메커니즘 | PREADY | HREADY |
| 용도 | 설정 레지스터 | DMA, 레거시 IP |
| SoC 위치 | 말단 Slave | Bridge 뒤 중간 |

---

## Q&A

**Q: APB가 왜 존재하는가? AHB나 AXI로 통일하면 안 되나?**
> "게이트 비용이다. APB는 PSEL/PENABLE/PREADY 몇 개 신호로 동작하여 HW 면적이 극히 작다. 타이머, UART, GPIO 같은 저속 주변장치에 AXI를 붙이면 인터페이스 로직이 IP 자체보다 클 수 있다. SoC는 수십~수백 개의 레지스터 인터페이스가 있으므로 APB의 면적 절약이 누적적으로 크다."

**Q: AHB 파이프라인의 주의점은?**
> "주소와 데이터가 1 cycle 차이로 겹치므로, HREADY=0(Wait State) 때 파이프라인 스톨이 발생한다. 이때 현재 주소와 이전 데이터가 모두 유지되어야 한다. DV에서 가장 흔한 버그는 Wait State 중 데이터가 갱신되거나 주소가 바뀌는 경우이다."

**Q: AHB HRESP 에러가 왜 2 cycle인가?**
> "AHB 파이프라인 구조 때문이다. Master가 에러 응답을 받을 때 이미 다음 주소를 발행한 상태이므로, Cycle 1에서 HREADY=0으로 파이프라인을 멈추고 Master에 에러를 알리고, Cycle 2에서 HREADY=1로 에러를 확정하며 Master가 다음 주소를 취소할 시간을 준다. 1 cycle만으로는 파이프라인에 이미 들어간 다음 전송을 안전하게 취소할 수 없다."

**Q: APB4에서 PSTRB이 추가된 이유는?**
> "APB3까지는 byte 단위 쓰기가 불가능했다. 32-bit 레지스터의 특정 바이트만 수정하려면 Read-Modify-Write가 필요했는데, 이는 원자성 문제(status 레지스터의 W1C 비트 등)와 성능 문제를 유발했다. PSTRB으로 byte-level write가 가능해져 이 문제가 해결되었다."

---

## 연습문제

### 문제 1: AHB WRAP4 주소 계산

**문제**: AHB WRAP4 burst, HSIZE=Half-Word(2 byte), 시작 주소 0x06일 때 4개 beat의 주소 시퀀스를 구하라.

**사고 과정**:
1. Wrap Size를 먼저 계산한다: Beat수 × Beat크기 = 4 × 2 = 8 bytes
2. Wrap Boundary를 구한다: Lower = 0x06 & ~(8-1) = 0x06 & 0xF8 = 0x00, Upper = 0x08
3. 각 beat에서 주소를 +2하되, Upper Boundary(0x08) 도달 시 Lower(0x00)로 wrap

**Dry Run**:
```
Beat 0: 0x06 (시작)
Beat 1: 0x06 + 2 = 0x08 → Upper(0x08) 도달 → Wrap → 0x00
Beat 2: 0x00 + 2 = 0x02
Beat 3: 0x02 + 2 = 0x04

답: 0x06 → 0x00 → 0x02 → 0x04
```

### 문제 2: AHB 파이프라인 타이밍

**문제**: AHB Master가 3개 연속 Write(A1=0x00/D1, A2=0x04/D2, A3=0x08/D3)를 수행하는데, A2의 Data Phase에서 Slave가 HREADY=0을 1 cycle 삽입한다. 각 cycle에서 HADDR, HWDATA, HREADY 값을 추적하라.

**사고 과정**:
1. AHB 파이프라인에서 Address Phase는 Data Phase보다 1 cycle 앞선다
2. HREADY=0이면 현재 cycle이 연장되고, 모든 신호가 유지된다
3. Data Phase의 stall은 다음 Address Phase도 함께 stall시킨다

**Dry Run**:
```
Cycle  | HADDR | HWDATA | HREADY | 설명
-------|-------|--------|--------|----
  T1   |  A1   |   -    |   1    | A1 Address Phase
  T2   |  A2   |  D1    |   0    | A2 Addr + D1 Data → Slave가 HREADY=0 (stall)
  T3   |  A2   |  D1    |   1    | stall 유지: A2, D1 모두 변하지 않음!
  T4   |  A3   |  D2    |   1    | stall 해제 → A3 Addr + D2 Data
  T5   |  --   |  D3    |   1    | D3 Data Phase

핵심: T2→T3에서 HREADY=0이면 HADDR(A2)와 HWDATA(D1) 모두 유지.
이것을 틀리면(T3에서 A3로 바꾸면) → 가장 흔한 AHB 버그.
```

### 퀴즈

1. APB에서 PREADY가 항상 1이면 모든 전송은 몇 cycle에 완료되는가?
   <details><summary>정답</summary>2 cycle (Setup + Access). Wait state 없는 최소 전송 시간.</details>

2. AHB HRESP ERROR가 1 cycle이 아닌 2 cycle인 이유를 한 문장으로 설명하라.
   <details><summary>정답</summary>파이프라인에 이미 진입한 다음 전송(주소)을 안전하게 취소할 시간이 필요하기 때문.</details>

3. APB4의 PPROT[1]=1이 의미하는 것은?
   <details><summary>정답</summary>Non-Secure access. TrustZone에서 Secure 영역 접근이 차단되어야 하는 트랜잭션.</details>

4. AHB WRAP8, HSIZE=Word(4byte), 시작 주소 0x14일 때 Wrap Boundary의 Lower/Upper는?
   <details><summary>정답</summary>Wrap Size = 8×4 = 32(0x20). Lower = 0x14 & ~0x1F = 0x00, Upper = 0x20.</details>

5. AHB-to-APB Bridge에서 AHB INCR4 burst는 APB 측에서 어떻게 처리되는가?
   <details><summary>정답</summary>4개의 독립적인 APB 단일 전송으로 분해된다. APB는 burst를 지원하지 않으므로.</details>

---

## 핵심 정리

- **APB는 단순함이 무기**: SETUP→ACCESS 2단계, PSEL/PENABLE/PREADY만으로 동작 → 게이트 비용 최소
- **AHB는 파이프라인**: 주소-데이터 1 cycle 차이. HREADY=0 시 stall — 모든 신호 유지가 핵심 (가장 흔한 버그가 stall 중 신호 변경)
- **AHB-to-APB Bridge**: AHB burst를 APB 단일 전송 N개로 분해. 면적과 성능의 trade-off
- **버전 진화**: APB3에서 PREADY/PSLVERR 정식화, APB4에서 PSTRB(byte write)/PPROT, APB5에서 wakeup/user/parity
- **DV pitfall**: AHB Wait State 중 HADDR/HWDATA 변경, APB SETUP 단계에서 PSEL=0, HRESP ERROR 1-cycle 처리

## 다음 단계

- 📝 [**Module 01 퀴즈**](quiz/01_apb_ahb_quiz.md) — 5문항으로 이해도 점검
- ➡️ [**Module 02 — AXI**](02_axi.md) — 5채널 / Burst / Outstanding의 핵심

<div class="chapter-nav">
  <a class="nav-prev" href="../">
    <div class="nav-label">◀ 이전</div>
    <div class="nav-title">코스 홈</div>
  </a>
  <a class="nav-next" href="../02_axi/">
    <div class="nav-label">다음 ▶</div>
    <div class="nav-title">AXI (Advanced eXtensible Interface)</div>
  </a>
</div>
