# AMBA Protocols 용어집

핵심 용어 ISO 11179 형식 정의.

---

## A — AHB / AXI / AXI-Stream / APB / Active

### AHB (Advanced High-performance Bus)

**Definition.** ARM AMBA의 중급 성능 버스로, 주소-데이터 파이프라인과 burst 전송을 지원하며 단일 master 또는 multi-master 환경에서 동작.

**Source.** ARM IHI 0033 (AMBA AHB Protocol Spec).

**Related.** AHB-to-APB Bridge, HREADY, HRESP, INCR/WRAP burst.

**Example.** AHB Master ↔ AHB-to-APB Bridge ↔ peripheral.

**See also.** [Module 01](01_apb_ahb.md)

### AXI (Advanced eXtensible Interface)

**Definition.** ARM AMBA의 고성능 인터커넥트 프로토콜로, 5개 독립 채널(AW/W/B/AR/R), Burst, Outstanding, ID 기반 OoO를 통해 최대 대역폭을 제공.

**Source.** ARM IHI 0022 (AMBA AXI4 Protocol Spec).

**Related.** AW/W/B/AR/R 채널, AxLEN, AxSIZE, AxBURST, ID, OoO, WSTRB.

**Example.** CPU ↔ NoC ↔ Memory Controller, GPU ↔ DMA, AI accelerator IP.

**See also.** [Module 02](02_axi.md)

### AXI-Stream

**Definition.** AXI 계열의 단방향 점대점 데이터 전송 프로토콜로, 주소 없이 패킷/프레임을 TLAST로 표시하며 DSP/AI/네트워크 데이터 패스에 사용.

**Source.** ARM IHI 0051 (AMBA 4 AXI-Stream Protocol Spec).

**Related.** TVALID, TREADY, TLAST, TKEEP, TID, TDEST, TUSER.

**Example.** AI accelerator weight stream, Ethernet packet flow.

**See also.** [Module 03](03_axi_stream.md)

### APB (Advanced Peripheral Bus)

**Definition.** ARM AMBA의 가장 단순한 저속 버스로, SETUP→ACCESS 2단계 핸드셰이크로 레지스터 접근을 처리하며 게이트 비용이 가장 작음.

**Source.** ARM IHI 0024 (AMBA APB Protocol Spec).

**Related.** PSEL, PENABLE, PREADY, PSLVERR, PSTRB(APB4+), PPROT.

**Example.** UART/Timer/GPIO 같은 peripheral의 control/status 레지스터.

**See also.** [Module 01](01_apb_ahb.md)

---

## B — Burst

### Burst

**Definition.** 단일 트랜잭션 내에서 연속된 여러 beat의 데이터를 전송하는 메커니즘으로, AXI는 FIXED/INCR/WRAP, AHB는 INCR/WRAP을 지원.

**Source.** AMBA AXI/AHB Spec.

**Related.** AxLEN (beat 수, AXI4 최대 256), AxSIZE (beat 폭), AxBURST (타입).

**Example.** AXI INCR burst 16-beat × 64-bit = 128 bytes 한 번에 전송.

**See also.** [Module 02](02_axi.md)

---

## H — Handshake

### VALID/READY Handshake

**Definition.** AXI/AXI-Stream의 핵심 흐름 제어 메커니즘으로, Source가 VALID, Sink가 READY를 assert하면 클럭 엣지에서 데이터 전송이 발생.

**Source.** AMBA AXI Spec, §A3.

**Related.** Deadlock prevention, Stall.

**Rule.** **VALID는 READY를 기다리지 않고 올라가야 한다** (데드락 방지). READY는 자유롭게 올렸다 내릴 수 있음. VALID=1 동안 데이터 신호는 변경 금지.

**Example.**
```
VALID  ___|‾‾‾‾‾‾‾‾‾‾‾|___
READY  _______|‾‾‾|________
                 ↑ 전송 발생
```

**See also.** [Module 02](02_axi.md), [Module 03](03_axi_stream.md)

---

## O — OoO / Outstanding

### Outstanding Transaction

**Definition.** 응답이 도착하기 전에 새로운 요청을 발행할 수 있는 능력으로, 인터커넥트의 효율성을 좌우.

**Source.** AMBA AXI Spec.

**Related.** OoO, Throughput, ID.

**Example.** Master가 AW0, AW1, AW2를 연속 발행하고 응답 B0, B1, B2를 비동기 수신.

### Out-of-Order (OoO)

**Definition.** 같은 ID 내에서는 in-order이지만 ID 간에는 응답 순서가 발행 순서와 다를 수 있는 AXI의 특성.

**Source.** AMBA AXI Spec, §A5.

**Related.** ID, Outstanding, Scoreboard per-ID queue.

**See also.** [Module 02](02_axi.md)

---

## W — WSTRB

### WSTRB (Write Strobe)

**Definition.** AXI Write에서 각 byte의 write 유효성을 비트 단위로 표시하는 신호로, byte-level write를 가능하게 함.

**Source.** AMBA AXI Spec, §A2.

**Related.** Narrow Transfer, byte mask, AHB와의 차이.

**Example.** 32-bit data에 WSTRB=4'b0011 → 하위 2 bytes만 write, 상위 2 bytes는 보존.

**See also.** [Module 02](02_axi.md)

---

## 추가 약어

| 약어 | 풀네임 | 의미 |
|------|--------|------|
| **AMBA** | Advanced Microcontroller Bus Architecture | ARM의 SoC 인터커넥트 표준군 |
| **NoC** | Network-on-Chip | 패킷 스위칭 기반 SoC 인터커넥트 |
| **AxLEN** | — | Burst length (AXI3: 1-16, AXI4: 1-256) |
| **AxSIZE** | — | Beat 단위 폭 (1, 2, 4, 8, 16, 32, 64, 128 bytes) |
| **AxBURST** | — | Burst 타입 (FIXED=00, INCR=01, WRAP=10) |
| **AxCACHE** | — | Modifiable / Bufferable 등 캐시 속성 |
| **AxPROT** | — | Privileged/Non-secure/Instruction 보호 속성 |
| **AxQOS** | — | QoS 우선순위 (4-bit, AXI4부터) |
| **TLAST** | — | AXI-Stream 패킷 종료 표시 |
| **TKEEP** | — | AXI-Stream byte-level 유효성 마스크 |

---

## 추가 항목 (Phase 2 검수 완료)

### APB4 (AMBA 4 APB)

**Definition.** ARM AMBA 4 패밀리(2010)의 APB 리비전으로, PSTRB(byte enable) 와 PPROT(액세스 보호 속성) 를 추가해 보안/메모리 보호 기반 액세스를 지원한다.

**Source.** ARM IHI 0024C — AMBA APB Protocol Specification.

**Related.** APB, PSTRB, PPROT, AMBA 4.

**See also.** [Module 01](01_apb_ahb.md)

### HPROT (Protection Control)

**Definition.** AHB 의 4-bit 사이드밴드 신호로, transfer 의 cacheable / bufferable / privileged / data-vs-instruction 속성을 표현한다.

**Source.** ARM IHI 0033 — AMBA AHB Protocol Specification.

**Related.** AWPROT/ARPROT (AXI), Cacheable, Bufferable.

**See also.** [Module 01](01_apb_ahb.md)



### AMBA (Advanced Microcontroller Bus Architecture)

**Definition.** ARM 이 정의한 SoC 인터커넥트 프로토콜 패밀리의 총칭으로, APB / AHB / AXI / AXI-Stream / ACE / CHI 를 포함한다.

**Source.** ARM AMBA Specification.

**Related.** APB, AHB, AXI, ACE, CHI.

**See also.** [Module 01](01_apb_ahb.md)

### HREADY / HRESP (AHB Handshake & Response)

**Definition.** AHB 의 핵심 사이드밴드 — HREADY 는 slave 가 현재 transfer 를 완료할 수 있는지를 master 에 알리고, HRESP 는 OKAY / ERROR 결과를 반환한다.

**Source.** ARM IHI 0033 — AMBA AHB Protocol Specification.

**Related.** HTRANS, HBURST, AHB pipeline.

**See also.** [Module 01](01_apb_ahb.md)

### AXI3 vs AXI4

**Definition.** AXI3 는 burst 최대 16 beat + WID 신호 보유, AXI4 는 burst 최대 256 beat (단, INCR 만) + WID 제거 + QoS / Region / USER 신호 추가.

**Source.** ARM IHI 0022 — AMBA AXI Protocol Specification.

**Related.** WID, AxLEN, QoS.

**See also.** [Module 02](02_axi.md)
