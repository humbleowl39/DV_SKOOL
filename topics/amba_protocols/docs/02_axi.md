# Unit 2: AXI (Advanced eXtensible Interface)

## 핵심 개념
**AXI = AMBA에서 가장 고성능인 버스. 5개 독립 채널(AW/W/B/AR/R), Out-of-Order 완료, Burst, Outstanding 트랜잭션으로 최대 대역폭 달성. CPU↔MC, IP↔IP 고성능 연결의 사실상 표준.**

---

## 5채널 구조

```
           Master                          Slave
     +------+------+              +------+------+
     |              |              |              |
AW:  | Write Addr  |──────────→  | Write Addr  |  Write Address Channel
     |              |              |              |
W:   | Write Data  |──────────→  | Write Data  |  Write Data Channel
     |              |              |              |
B:   | Write Resp  |←──────────  | Write Resp  |  Write Response Channel
     |              |              |              |
AR:  | Read Addr   |──────────→  | Read Addr   |  Read Address Channel
     |              |              |              |
R:   | Read Data   |←──────────  | Read Data   |  Read Data/Response Channel
     +------+------+              +------+------+

각 채널이 독립 → Read와 Write 동시 가능 = Full-Duplex
```

### 각 채널 핵심 신호

| 채널 | 핵심 신호 | 역할 |
|------|----------|------|
| **AW** | AWADDR, AWLEN, AWSIZE, AWBURST, AWID, AWVALID/AWREADY | Write 주소+제어 |
| **W** | WDATA, WSTRB, WLAST, WVALID/WREADY | Write 데이터 |
| **B** | BRESP, BID, BVALID/BREADY | Write 응답 |
| **AR** | ARADDR, ARLEN, ARSIZE, ARBURST, ARID, ARVALID/ARREADY | Read 주소+제어 |
| **R** | RDATA, RRESP, RLAST, RID, RVALID/RREADY | Read 데이터+응답 |

---

## VALID/READY 핸드셰이크 — AXI의 근본 메커니즘

```
전송이 발생하는 조건: VALID && READY 동시에 HIGH인 클럭 엣지

Case 1: VALID first
  VALID ──────┐           ┌──
              └───────────┘
  READY ─────────────┐    ┌──
                     └────┘
                     ↑ 전송 발생

Case 2: READY first
  VALID ─────────┐        ┌──
                 └────────┘
  READY ──────┐            ┌──
              └────────────┘
              ↑ 전송 발생 (VALID 올라올 때)

Case 3: 동시
  VALID ──────┐       ┌──
              └───────┘
  READY ──────┐       ┌──
              └───────┘
              ↑ 전송 발생

핵심 규칙:
  1. VALID를 올린 후에는 READY가 올 때까지 내리면 안 됨
  2. READY는 자유롭게 올리고 내릴 수 있음
  3. VALID을 올리기 전에 READY를 기다리면 안 됨 (데드락 방지)
     → Source는 READY와 무관하게 VALID을 assert해야 함
```

### 데드락 방지 규칙

```
절대 금지:
  Master: "READY가 올 때까지 VALID 안 올리겠다"
  Slave:  "VALID가 올 때까지 READY 안 올리겠다"
  → 양쪽 다 대기 → 데드락!

AXI 규칙:
  Source(VALID 주인)는 Destination(READY 주인)을 기다리지 않고
  데이터가 준비되면 VALID을 올려야 한다.
  
  Destination은 VALID을 기다려도 되고, 미리 READY를 올려도 된다.
```

---

## Burst 전송

### Burst 파라미터

| 신호 | 의미 |
|------|------|
| AxLEN[7:0] | Burst 길이 = AxLEN + 1 (1~256 beats) |
| AxSIZE[2:0] | Beat 크기: 2^AxSIZE bytes (1/2/4/8/16/32/64/128 bytes) |
| AxBURST[1:0] | Burst 타입: FIXED/INCR/WRAP |

### Burst 타입

```
FIXED (2'b00):
  모든 beat가 같은 주소 → FIFO 접근에 사용
  A, A, A, A

INCR (2'b01):
  주소가 beat마다 증가 → 가장 일반적
  A, A+4, A+8, A+12  (32-bit 기준)

WRAP (2'b10):
  주소가 증가하다가 경계에서 랩 → 캐시 라인 로드에 사용
  예: 주소 0x0C, 4-beat WRAP → 0x0C, 0x00, 0x04, 0x08
  (0x10 경계에서 랩)
```

---

## Outstanding & Out-of-Order

### Outstanding 트랜잭션

```
AHB: 요청1 → 응답1 → 요청2 → 응답2 (순차, 대기)
AXI: 요청1 → 요청2 → 요청3 → 응답1 → 응답2 → 응답3 (파이프라인)

  AR → AR → AR → ...
              R ← R ← R ← ...

  응답을 기다리지 않고 다음 요청 발행 → 대역폭 극대화
  Outstanding 깊이: 동시에 발행 가능한 미완료 트랜잭션 수
```

### Out-of-Order 완료

```
ID 기반 순서 관리:

  ID=0: 요청 A → 요청 B → 응답 A → 응답 B (같은 ID는 순서 보장)
  ID=1: 요청 C → 응답 C (ID=1은 독립)

  다른 ID 간: 순서 보장 없음 (Out-of-Order 허용)
  같은 ID 간: 순서 보장

  → Slave가 빠른 응답부터 반환 → 느린 Slave가 전체를 블로킹하지 않음
```

---

## WSTRB (Write Strobe) — 바이트 단위 쓰기 제어

```
WSTRB[N-1:0]에서 N = (데이터 버스 폭 / 8)

예: 32-bit 데이터 버스 → WSTRB[3:0]
    64-bit 데이터 버스 → WSTRB[7:0]
    128-bit 데이터 버스 → WSTRB[15:0]

각 WSTRB 비트가 1이면 해당 바이트 레인이 유효 (Slave가 저장해야 함)
각 WSTRB 비트가 0이면 해당 바이트는 무시

32-bit 버스 예시:
  WDATA = 0xAABBCCDD
  
  WSTRB = 4'b1111 → [AA][BB][CC][DD] 모두 쓰기 (Word Write)
  WSTRB = 4'b0011 → [--][--][CC][DD] 하위 2바이트만 (Half-word Write)
  WSTRB = 4'b0001 → [--][--][--][DD] 최하위 바이트만 (Byte Write)
  WSTRB = 4'b1100 → [AA][BB][--][--] 상위 2바이트만
  WSTRB = 4'b0100 → [--][BB][--][--] Byte 2만 (비정렬 접근)

  바이트 레인 매핑:
  WSTRB[0] → WDATA[7:0]   (Byte 0, 주소 offset +0)
  WSTRB[1] → WDATA[15:8]  (Byte 1, 주소 offset +1)
  WSTRB[2] → WDATA[23:16] (Byte 2, 주소 offset +2)
  WSTRB[3] → WDATA[31:24] (Byte 3, 주소 offset +3)
```

> **DV 포인트**: WSTRB=0인 바이트 위치의 메모리 값이 변경되지 않는지 반드시 검증. 가장 흔한 버그: WSTRB 무시하고 전체 word를 덮어쓰는 Slave.

---

## Exclusive Access (AxLOCK + EXOKAY)

멀티 프로세서 시스템에서 atomic Read-Modify-Write를 구현하는 메커니즘.

```
사용 시나리오: 뮤텍스, 세마포어, atomic counter 등

동작 플로우:
  1. Master A: Exclusive Read  (ARLOCK=1, ARADDR=0x100) → 데이터 읽기 + 모니터 등록
  2. Master A: Exclusive Write (AWLOCK=1, AWADDR=0x100, WDATA=new_value)
  3. Slave 응답:
     - BRESP=EXOKAY (2'b01): 성공 — 아무도 이 주소를 건드리지 않았음 → 쓰기 완료
     - BRESP=OKAY   (2'b00): 실패 — 다른 Master가 중간에 이 주소에 Write → 쓰기 무시

Exclusive Monitor:
  ┌─────────────────────────────────────────────┐
  │ Interconnect / Slave 내부에 Exclusive Monitor │
  │                                               │
  │ Exclusive Read 시:                            │
  │   Monitor에 {Master ID, Address} 등록         │
  │                                               │
  │ Exclusive Write 시:                           │
  │   Monitor에 해당 {ID, Addr} 있으면 → EXOKAY  │
  │   없거나 다른 Master가 Write했으면 → OKAY     │
  │                                               │
  │ 어떤 Master든 해당 주소에 Write하면:          │
  │   Monitor에서 해당 주소 항목 제거             │
  └─────────────────────────────────────────────┘

AXI3: AxLOCK[1:0] = 2'b01 (Exclusive), 2'b10 (Locked — 버스 독점, 비권장)
AXI4: AxLOCK[0]   = 1'b1  (Exclusive만, Locked 제거)
```

> **면접 포인트**: "Exclusive Access와 Locked Access의 차이?"
> → Locked는 버스 전체를 독점하여 다른 Master 차단(성능 저하). Exclusive는 Monitor 기반으로 버스를 차단하지 않고 낙관적 동시성 제어. AXI4에서 Locked는 제거됨.

---

## Narrow Transfer

데이터 버스 폭보다 작은 크기의 전송. WSTRB로 유효 바이트를 표시.

```
예: 64-bit(8-byte) 데이터 버스에서 32-bit(4-byte) 전송

AWADDR = 0x00, AWSIZE = 3'b010 (4 bytes), AWLEN = 3 (4 beats), AWBURST = INCR

Beat 0: ADDR=0x00 → WSTRB=8'b0000_1111 (하위 4바이트)
Beat 1: ADDR=0x04 → WSTRB=8'b1111_0000 (상위 4바이트)
Beat 2: ADDR=0x08 → WSTRB=8'b0000_1111 (하위 4바이트)
Beat 3: ADDR=0x0C → WSTRB=8'b1111_0000 (상위 4바이트)

  64-bit 데이터 버스:
  |  Byte7  |  Byte6  |  Byte5  |  Byte4  |  Byte3  |  Byte2  |  Byte1  |  Byte0  |
  
  Beat 0: [  ----   ][  ----   ][  ----   ][  ----   ][ DATA3  ][ DATA2  ][ DATA1  ][ DATA0  ]
  Beat 1: [ DATA7  ][ DATA6  ][ DATA5  ][ DATA4  ][  ----   ][  ----   ][  ----   ][  ----   ]

→ WSTRB 비트가 beat마다 이동하면서 유효 바이트 레인을 가리킴
→ Slave는 반드시 WSTRB을 확인해야 정확한 바이트에 쓸 수 있음
```

> **DV 포인트**: Narrow Transfer에서 WSTRB 패턴이 올바르게 이동하는지, Slave가 WSTRB=0인 바이트를 건드리지 않는지 검증.

---

## 추가 제어 신호: AxCACHE, AxPROT, AxQOS

### AxCACHE[3:0] — 메모리 속성

| 비트 | AXI4 이름 | 의미 |
|------|----------|------|
| [0] | Bufferable | 1이면 Interconnect가 Write를 버퍼링 가능 (응답을 먼저 반환) |
| [1] | Modifiable | 1이면 Interconnect가 전송을 분할/병합/캐싱 가능 |
| [2] | Read-Allocate | 1이면 Read miss 시 캐시에 할당 |
| [3] | Write-Allocate | 1이면 Write miss 시 캐시에 할당 |

```
흔한 조합:
  4'b0000 — Device, Non-bufferable: MMIO 레지스터 (순서/사이드이펙트 보장 필수)
  4'b0011 — Normal, Non-cacheable, Bufferable: DMA 버퍼
  4'b1111 — Write-Back, Read/Write Allocate: 일반 메모리 (최고 성능)

→ Device 메모리에 Modifiable=1을 쓰면 Interconnect가 전송을 재정렬할 수 있어 위험!
```

### AxPROT[2:0] — 접근 보호

| 비트 | 의미 |
|------|------|
| [0] | 0=Unprivileged, 1=Privileged |
| [1] | 0=Secure, 1=Non-Secure |
| [2] | 0=Data, 1=Instruction |

> APB4 PPROT, AHB HPROT과 동일 개념. TrustZone에서 Secure/Non-Secure 영역 분리에 사용.

### AxQOS[3:0] — Quality of Service (AXI4 추가)

```
0x0 = 최저 우선순위, 0xF = 최고 우선순위
Interconnect가 QoS 값을 기반으로 중재(arbitration) 우선순위 결정

예: CPU의 실시간 트래픽(QoS=0xF) > DMA의 백그라운드 전송(QoS=0x0)
→ Interconnect에서 높은 QoS 트랜잭션이 먼저 통과
```

---

## AXI3 vs AXI4 핵심 차이

| 항목 | AXI3 | AXI4 |
|------|------|------|
| Burst 길이 | AxLEN[3:0] → 최대 16 beats | AxLEN[7:0] → **최대 256 beats** |
| Write Interleaving | 지원 (WID 신호) | **제거** (WID 삭제) |
| Locked Access | AxLOCK[1:0], LOCKED 지원 | AxLOCK[0], **Exclusive만** |
| QoS | 없음 | **AxQOS[3:0] 추가** |
| Region | 없음 | **AxREGION[3:0] 추가** |
| AWUSER/ARUSER | 없음 | **User 사이드밴드 추가** |

```
Write Interleaving (AXI3에서 존재, AXI4에서 제거):

AXI3 허용:
  AW(ID=0) → AW(ID=1) → W(ID=0,beat0) → W(ID=1,beat0) → W(ID=0,beat1) → W(ID=1,beat1)
  → 서로 다른 ID의 Write Data가 인터리브됨 (WID로 구분)

AXI4:
  AW(ID=0) → AW(ID=1) → W(beat0,beat1) → W(beat0,beat1)
  → Write Data는 AW 순서대로 완전히 전송 후 다음 트랜잭션
  → WID 신호 불필요 → 제거

제거 이유: Interconnect 설계 복잡도 ↑↑ 대비 실질 성능 이득 미미.
           대부분의 Slave가 interleaving을 지원하지 않아 결국 재정렬 필요.
```

---

## AXI Ordering 규칙 요약

| 규칙 | 설명 |
|------|------|
| 같은 ID, 같은 채널 | 순서 보장 |
| 같은 ID, Write | AW→W→B 순서 보장 |
| 같은 ID, Read | AR→R 순서 보장 |
| 다른 ID | 순서 보장 **없음** |
| Write→Read (같은 ID) | 순서 보장 없음 (별도 채널) |
| W는 AW 없이 불가 | AW가 먼저 (또는 동시) |
| WLAST | 마지막 Write beat 표시 필수 |
| RLAST | 마지막 Read beat 표시 필수 |

---

## AXI 응답 코드

| RESP | 이름 | 의미 |
|------|------|------|
| 2'b00 | OKAY | 정상 완료 |
| 2'b01 | EXOKAY | Exclusive Access 성공 |
| 2'b10 | SLVERR | Slave 에러 (주소 유효하지만 처리 불가) |
| 2'b11 | DECERR | Decode 에러 (해당 Slave 없음) |

---

## DV 핵심 검증 포인트

| 항목 | 시나리오 |
|------|---------|
| 핸드셰이크 | VALID/READY 모든 타이밍 조합 (V first, R first, 동시) |
| 데드락 | VALID이 READY를 기다리지 않는지 |
| Burst | INCR/WRAP/FIXED 주소 계산 정확 |
| Outstanding | 복수 미완료 트랜잭션 + 정확한 ID 매칭 |
| Out-of-Order | 다른 ID 응답 순서 변경 → 데이터 정합 |
| WSTRB | 바이트 마스크 정확 (부분 쓰기) |
| WLAST/RLAST | 정확한 위치에서 LAST 신호 |
| Error 응답 | SLVERR/DECERR 시 정상 처리 |

---

## Q&A

**Q: AXI가 AHB보다 고성능인 핵심 이유는?**
> "세 가지: (1) 5채널 독립 — Read/Write가 동시 가능(Full-Duplex). AHB는 하나의 버스를 공유. (2) Outstanding — 응답을 기다리지 않고 다음 요청 발행 가능. AHB는 순차. (3) Out-of-Order — ID별로 독립 처리하여 느린 Slave가 전체를 블로킹하지 않음. 이 세 가지가 대역폭을 수 배~수십 배 향상시킨다."

**Q: AXI 데드락은 어떻게 발생하는가?**
> "Master가 READY를 기다린 후 VALID을 올리고, Slave가 VALID을 기다린 후 READY를 올리면 양쪽이 무한 대기한다. AXI 프로토콜은 이를 방지하기 위해 'Source는 Destination의 READY를 기다리지 않고 VALID을 assert해야 한다'는 규칙을 명시한다. DV에서는 이 의존성을 검증하는 것이 핵심 프로토콜 체크 항목이다."

**Q: AXI3에서 AXI4로 바뀌며 Write Interleaving이 제거된 이유는?**
> "Write Interleaving은 서로 다른 ID의 Write Data를 섞어 보내는 기능인데, 이를 지원하려면 Interconnect와 Slave 모두에서 WID 기반 재정렬 버퍼가 필요하다. 실제로 대부분의 Slave IP가 interleaving을 지원하지 않았고, Interconnect에서 결국 재정렬해야 해서 성능 이득이 미미했다. 복잡도 대비 이득이 없어 AXI4에서 WID와 함께 제거되었다."

**Q: AxCACHE의 Bufferable과 Modifiable 차이는?**
> "Bufferable은 Interconnect가 Write 응답을 Slave 도달 전에 미리 반환할 수 있다는 의미(버퍼링). Modifiable은 더 강력하여 Interconnect가 전송을 분할, 병합, 캐싱할 수 있다. Device 레지스터(MMIO)에는 둘 다 0이어야 한다 — 사이드이펙트가 있는 접근은 정확히 1회, 원래 크기대로 Slave에 도달해야 하므로."

---

## 연습문제

### 문제 1: WSTRB 계산

**문제**: 64-bit(8-byte) 데이터 버스에서, 주소 0x03에 2-byte(half-word) Write를 할 때 WSTRB[7:0] 값은?

**사고 과정**:
1. 주소 0x03의 버스 내 offset = 0x03 % 8 = 3
2. Half-word = 2 bytes → byte 3, byte 4에 해당
3. WSTRB의 bit 3과 bit 4를 1로 설정

**Dry Run**:
```
64-bit 버스의 바이트 레인:
  Byte:   | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
  WSTRB:  | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 |

답: WSTRB = 8'b0001_1000 = 0x18
```

### 문제 2: Outstanding + Out-of-Order 시나리오 추적

**문제**: AXI Master가 다음 순서로 Read 요청을 발행한다. Slave의 응답이 ID=1이 먼저 도착한다면, Master가 받는 응답 순서는?

```
요청 순서: AR(ID=0, ADDR=0x100) → AR(ID=1, ADDR=0x200) → AR(ID=0, ADDR=0x300)
```

**사고 과정**:
1. 같은 ID 간에는 순서 보장: ID=0의 0x100 응답이 0x300 응답보다 먼저 와야 함
2. 다른 ID 간에는 순서 보장 없음: ID=1은 ID=0과 독립
3. Slave가 ID=1을 먼저 반환 가능

**Dry Run**:
```
가능한 응답 순서 (모두 유효):
  ① R(ID=1, 0x200) → R(ID=0, 0x100) → R(ID=0, 0x300)  ← ID=1 먼저
  ② R(ID=0, 0x100) → R(ID=1, 0x200) → R(ID=0, 0x300)  ← 발행 순서대로
  ③ R(ID=0, 0x100) → R(ID=0, 0x300) → R(ID=1, 0x200)  ← ID=1 마지막

불가능한 순서:
  ✗ R(ID=0, 0x300) → R(ID=0, 0x100) → ...  ← 같은 ID=0 내 순서 위반!

핵심: ID=0끼리는 0x100 → 0x300 순서 고정. ID=1은 어디에든 끼어들 수 있음.
```

### 문제 3: Exclusive Access 성공/실패 판단

**문제**: Master A와 Master B가 동시에 주소 0x80에 접근한다. 다음 시퀀스에서 각 Master의 Exclusive Write 결과는?

```
T1: Master A → Exclusive Read  (ADDR=0x80)
T2: Master B → Exclusive Read  (ADDR=0x80)
T3: Master A → Exclusive Write (ADDR=0x80, DATA=0x11)
T4: Master B → Exclusive Write (ADDR=0x80, DATA=0x22)
```

**Dry Run**:
```
T1: Monitor에 {A, 0x80} 등록
T2: Monitor에 {B, 0x80} 등록 (A 항목도 유지 — 주소 같지만 ID 다름)
T3: Master A의 Exclusive Write
    → Monitor에 {A, 0x80} 있음 → BRESP = EXOKAY (성공!)
    → 메모리에 0x11 쓰기 완료
    → 0x80 주소에 대한 다른 항목({B, 0x80}) 무효화
T4: Master B의 Exclusive Write
    → Monitor에 {B, 0x80} 이미 무효화됨 → BRESP = OKAY (실패!)
    → 메모리에 쓰기 안 함 (0x80은 여전히 0x11)

결론: Master A 성공(EXOKAY), Master B 실패(OKAY).
Master B는 OKAY를 받으면 다시 Exclusive Read부터 재시도해야 함 (CAS 루프).
```

### 퀴즈

1. AXI Write에서 WSTRB이 모두 0인 beat는 어떤 의미인가?
   <details><summary>정답</summary>해당 beat에서 어떤 바이트도 쓰지 않음. 유효한 전송이지만 실질적 쓰기가 없음. Burst 중 특정 beat를 skip하고 싶을 때 사용 가능.</details>

2. AXI4에서 WID 신호가 없는 이유는?
   <details><summary>정답</summary>Write Interleaving이 제거되었기 때문. AXI4는 AW 순서대로 W 데이터가 와야 하므로 WID로 구분할 필요 없음.</details>

3. AxCACHE=4'b0000인 트랜잭션을 Interconnect가 두 개로 분할할 수 있는가?
   <details><summary>정답</summary>불가. Modifiable=0이면 Interconnect가 전송을 수정(분할/병합/재정렬)할 수 없음. Device 레지스터 접근에 필수적인 속성.</details>

4. Exclusive Read 없이 Exclusive Write만 보내면?
   <details><summary>정답</summary>Monitor에 해당 {ID, Address} 항목이 없으므로 항상 OKAY(실패) 응답. Exclusive는 반드시 Read → Write 쌍으로 사용해야 함.</details>

5. AXI4 INCR burst에서 AxLEN=0xFF이면 총 전송 바이트 수는? (AxSIZE=3'b011, 8 bytes)
   <details><summary>정답</summary>(0xFF + 1) × 8 = 256 × 8 = 2048 bytes = 2KB. AXI4에서 단일 burst로 전송 가능한 최대량.</details>
