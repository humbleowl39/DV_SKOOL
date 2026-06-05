---
title: "HW/SW Interaction 용어집"
---

이 페이지는 본 코스에서 사용되는 하드웨어/소프트웨어 상호작용 핵심 용어 정의 모음입니다. 항목은 ISO 11179 형식을 따릅니다 (**Definition / Source / Related / Example / See also**).

:::tip[검색 활용]
상단 검색창에 용어를 입력하면 본문에서의 사용처도 함께 찾을 수 있습니다.
:::
---

## D — Device Register / Doorbell

### Device Register

**Definition.** 소프트웨어에게 고정된 버스 주소로 노출되어, 디바이스의 동작을 제어하거나 상태를 보고하는 하드웨어 저장 위치.

**Source.** Linux Device Drivers 3rd Ed. Ch. 9 (§I/O Ports and I/O Memory, p.235).

**Related.** Control register, Status register, MMIO, Programming model.

**Example.** `CTRL`(control), `STATUS`(status), `INT_ENABLE`(interrupt), `DATA_IN`(data), `DESC_BASE_ADDR`(pointer).

**See also.** [01 — 디바이스 레지스터 & MMIO/PMIO](../01_registers_mmio_pmio/)

### Doorbell

**Definition.** 소프트웨어가 잘 알려진 메모리 위치에 데이터를 둔 뒤 다른 메모리 위치에 write하여 하드웨어 디바이스에게 처리할 일이 있음을 알리는 메커니즘.

**Source.** Wikipedia, *Interrupt* — Doorbell.

**Related.** Descriptor ring, Tail pointer, Memory barrier, Interrupt(역방향).

**Example.** NIC 드라이버가 디스크립터를 DRAM에 큐잉하고 `wmb()` 후 tail 포인터를 도어벨 레지스터에 write.

**See also.** [03 — 인터럽트](../03_interrupts/)

---

## E — Edge-triggered Interrupt

### Edge-triggered Interrupt

**Definition.** 디바이스가 신호선에 순간적인 전이(상승 또는 하강 edge) 펄스를 발생시켜 요청을 알리고 곧 선을 해제하는 인터럽트 트리거 방식.

**Source.** Wikipedia, *Interrupt* — Triggering methods.

**Related.** Level-triggered interrupt, Interrupt status register, Missed edge.

**Example.** MSI는 메시지가 순간 이벤트이므로 edge-triggered처럼 동작한다.

**See also.** [03 — 인터럽트](../03_interrupts/)

---

## I — Interrupt / IPI / Interrupt Storm

### Interrupt

**Definition.** 이벤트를 적시에 처리하도록 프로세서에게 현재 실행 중인 코드를 중단하고 인터럽트 핸들러를 실행하라고 요청하는 신호.

**Source.** Wikipedia, *Interrupt*.

**Related.** ISR, Level/Edge trigger, MSI, Masking, Interrupt controller.

**Example.** 가속기가 작업을 끝내면 완료 인터럽트를 올려 드라이버를 깨운다.

**See also.** [03 — 인터럽트](../03_interrupts/)

### IPI (Inter-Processor Interrupt)

**Definition.** 멀티코어 시스템에서 한 프로세서 코어가 다른 코어에게 신호를 보내기 위해 인터럽트 컨트롤러를 통해 발생시키는 인터럽트.

**Source.** Wikipedia, *Interrupt*; ARM GIC Architecture Specification (IHI0069).

**Related.** Interrupt controller, GIC, APIC, Multi-core.

**Example.** 한 코어가 다른 코어에게 TLB shootdown을 요청할 때 IPI를 사용.

**See also.** [03 — 인터럽트](../03_interrupts/)

### Interrupt Storm

**Definition.** 과도한 인터럽트 처리 시간으로 전체 시스템 성능이 심각하게 저하되는 현상.

**Source.** Wikipedia, *Interrupt* — Performance issues.

**Related.** Interrupt coalescing, RSS, Polling, NAPI.

**Example.** 고율 패킷 수신 시 패킷마다 인터럽트가 발생해 CPU가 ISR 처리만 하다 throughput이 붕괴.

**See also.** [04 — 폴링 & 하이브리드](../04_polling_hybrid_dv/)

---

## L — Level-triggered Interrupt

### Level-triggered Interrupt

**Definition.** 디바이스가 신호선을 active 레벨로 구동하고 서비스될 때까지 그 레벨을 유지하여 요청을 알리는 인터럽트 트리거 방식.

**Source.** Wikipedia, *Interrupt* — Triggering methods.

**Related.** Edge-triggered interrupt, Wired-OR, Acknowledge, Stuck interrupt.

**Example.** wired-OR 공유 선에서 여러 디바이스가 level로 신호하고, ISR이 각 디바이스를 폴링해 소스를 찾는다.

**See also.** [03 — 인터럽트](../03_interrupts/)

---

## M — Memory Barrier / MMIO / MSI / Masking

### Memory Barrier

**Definition.** 배리어 이전의 메모리 연산이 이후의 연산보다 먼저 완료·가시화되도록 강제하여 컴파일러 또는 CPU의 재정렬을 막는 동기화 구문.

**Source.** Linux Device Drivers 3rd Ed. Ch. 9 (§I/O Ports and I/O Memory, p.237).

**Related.** `barrier()`(컴파일러만), `rmb()`, `wmb()`, `mb()`(full), Reordering, Doorbell.

**Example.**
```c
desc->len = pkt_len;
wmb();                       /* 디스크립터 write가 도어벨보다 먼저 */
writel(tail, regs + DOORBELL);
```

**See also.** [02 — Side-effect & 메모리 배리어](../02_side_effects_barriers/)

### MMIO (Memory-Mapped I/O)

**Definition.** 주 메모리와 I/O 디바이스를 동일한 통합 주소 공간에 두어, 표준 CPU load/store 명령으로 디바이스 레지스터에 접근하는 방식.

**Source.** Wikipedia, *Memory-mapped I/O and port-mapped I/O*.

**Related.** PMIO, Address hole, BAR, ioremap, Uncached.

**Example.** `void __iomem *r = ioremap(0xFED00000, 0x1000); u32 v = readl(r + 0x04);`

**See also.** [01 — 디바이스 레지스터 & MMIO/PMIO](../01_registers_mmio_pmio/)

### MSI (Message-Signaled Interrupt)

**Definition.** 물리 인터럽트 선 대신 통신 매체(주로 컴퓨터 버스)로 짧은 메시지를 보내 서비스를 요청하는 인터럽트 방식.

**Source.** Wikipedia, *Interrupt* — Message-signaled interrupts.

**Related.** PCIe, Edge-triggered, INTx, Interrupt vector.

**Example.** PCI Express는 INTx 물리 선이 없어 MSI를 전적으로 사용하며, 인터럽트 정체는 메시지 payload에 실린다.

**See also.** [03 — 인터럽트](../03_interrupts/)

### Masking

**Definition.** mask 레지스터의 비트로 특정 인터럽트 소스를 선택적으로 비활성화하는 동작.

**Source.** Wikipedia, *Interrupt* — Masking.

**Related.** NMI, Pending interrupt, INT_ENABLE.

**Example.** mask된 소스의 인터럽트는 무시되거나 펜딩으로 보류되며, NMI는 마스킹할 수 없다.

**See also.** [03 — 인터럽트](../03_interrupts/)

---

## N — NMI

### NMI (Non-Maskable Interrupt)

**Definition.** 소프트웨어가 마스킹할 수 없어 항상 처리되는 인터럽트.

**Source.** Wikipedia, *Interrupt* — Masking.

**Related.** Masking, Watchdog, Power-loss warning.

**Example.** 워치독 timeout이나 전원 손실 경고처럼 무시할 수 없는 이벤트에 NMI를 사용.

**See also.** [03 — 인터럽트](../03_interrupts/)

---

## P — PMIO / Polling

### PMIO (Port-Mapped I/O)

**Definition.** RAM과 분리된 전용 I/O 주소 공간에 디바이스를 두고, `in`/`out` 같은 전용 CPU 명령으로 접근하는 방식.

**Source.** Wikipedia, *Memory-mapped I/O and port-mapped I/O*.

**Related.** MMIO, Isolated I/O, `in`/`out`, EAX.

**Example.** x86의 `inl(0x04)`는 I/O 포트 0x04의 값을 EAX로 읽는다(32비트 cap).

**See also.** [01 — 디바이스 레지스터 & MMIO/PMIO](../01_registers_mmio_pmio/)

### Polling

**Definition.** 클라이언트 프로그램이 외부 디바이스의 상태를 동기적으로 능동 샘플링하여 준비 여부를 확인하는 I/O 방식.

**Source.** Wikipedia, *Polling (computer science)*.

**Related.** Busy-wait, Polling cycle, Interrupt, Hybrid polling.

**Example.** `while (readl(regs + STATUS) & STATUS_BUSY) cpu_relax();`

**See also.** [04 — 폴링 & 하이브리드](../04_polling_hybrid_dv/)

---

## S — Side Effect / Status Register

### Side Effect (I/O)

**Definition.** I/O 레지스터 접근이 단순한 값 저장·반환을 넘어 디바이스의 상태나 동작을 변화시키는 부수 효과.

**Source.** Linux Device Drivers 3rd Ed. Ch. 9 (§I/O Registers and Conventional Memory, p.236).

**Related.** Read-to-clear, W1C, Memory barrier, Uncached.

**Example.** clear-on-read status를 두 번 읽으면 두 번째 read는 이미 클리어된 0을 반환한다.

**See also.** [02 — Side-effect & 메모리 배리어](../02_side_effects_barriers/)

### Status Register

**Definition.** 디바이스의 현재 상태를 소프트웨어에게 보고하는 디바이스 레지스터.

**Source.** Linux Device Drivers 3rd Ed. Ch. 9; HDG `hw_sw_interaction_spec.md` §2.

**Related.** Control register, BUSY/READY bit, Polling, Read-to-clear.

**Example.** 폴링 루프가 `STATUS`의 `BUSY` 비트가 클리어될 때까지 반복 read한다.

**See also.** [04 — 폴링 & 하이브리드](../04_polling_hybrid_dv/)
