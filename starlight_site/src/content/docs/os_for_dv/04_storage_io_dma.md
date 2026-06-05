---
title: "Module 04 — Mass Storage · I/O 시스템 · DMA"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Differentiate** HDD(seek/rotational)와 NVM/SSD(NAND/FTL/wear leveling)의 물리·스케줄링 차이를 구분할 수 있다.
- **Explain** memory-mapped I/O 의 네 가지 control register(data-in/out, status, control)와 polling handshake 의 busy/command-ready bit 동작을 설명할 수 있다.
- **Trace** DMA 전송이 command block 생성 → DMA-request/acknowledge → 완료 interrupt 까지 진행되는 경로를 추적할 수 있다.
- **Implement** polling 기반 write handshake 와 interrupt handler 의 raise→catch→dispatch→clear 흐름을 코드로 구성할 수 있다.
- **Evaluate** polling vs interrupt vs DMA 를 throughput·CPU 점유 기준으로 비교해 어느 상황에 무엇을 쓸지 판단할 수 있다.
:::
:::note[사전 지식]
- [Module 01](../01_os_overview/) — interrupt/trap, system call
- [Module 03](../03_memory_paging_tlb/) — physical vs virtual 주소(DMA 가 어느 쪽을 쓰는가)
- bus·register·FIFO 의 기본 개념
- (출처) Silberschatz, *Operating System Concepts* 10th ed., Ch.11–12
:::
---

## 1. Why care? — 이 모듈이 곧 우리가 검증하는 그 메커니즘이다

이 모듈은 DV 엔지니어에게 가장 직접적입니다. 우리가 검증하는 거의 모든 IP — DMA 엔진, NIC, 스토리지 컨트롤러 — 가 여기서 다루는 **controller·memory-mapped I/O·interrupt·DMA** 구도 그대로이기 때문입니다. 레지스터에 값을 쓰는 것이 곧 MMIO 이고, 명령 완료를 알리는 것이 곧 interrupt 이며, 대량 전송을 떠넘기는 것이 곧 DMA 입니다.

책은 첫 문장에서 *"The two main jobs of a computer are I/O and computing"* 이라며 I/O 가 연산과 대등함을 못박습니다(Ch.12.1). testbench 를 설계할 때 polling 으로 status 를 기다릴지, interrupt 를 기다릴지, DMA 완료를 기다릴지는 검증 사고의 핵심입니다. 이 세 제어 방식의 자리매김을 이해하면, DUT 의 동작이 spec 의 어느 handshake 단계에 해당하는지 즉시 짚을 수 있습니다.

---

## 2. Intuition — 한 줄 비유와 한 장 그림

:::tip[💡 한 줄 비유]
세 가지 제어 방식 ≈ **택배를 기다리는 세 가지 방법**.<br>
**Polling** = 문 앞에 서서 1초마다 내다보기(CPU 가 status bit 반복 읽기). **Interrupt** = 초인종을 달아 두고 딴 일 하기(controller 가 CPU 를 불러줌). **DMA** = 택배 기사에게 "직접 창고에 넣어 두고 다 되면 알려 달라"(전용 controller 가 메모리로 직접 옮기고 끝나면 interrupt).
:::
### 한 장 그림 — host 와 controller 의 대화 구도

```d2
direction: right

CPU: "**CPU (host)**\nload/store 로 register 접근"
CTRL: "**Device Controller**\ndata-in/out · status · control\nregister + FIFO"
DEV: "Device\n(disk / NIC / ...)"
DMA: "**DMA Controller**\ncommand block 으로\nmemory 직접 전송"
MEM: "Main Memory"

CPU -> CTRL: "① MMIO (control/data-out write)"
CTRL -> CPU: "② status read (polling) / interrupt"
CTRL -> DEV: "물리 신호"
CPU -> DMA: "③ command block 주소만"
DMA -> MEM: "④ 직접 전송 (cycle stealing)"
DMA -> CPU: "⑤ 완료 interrupt"
```

### 왜 이 디자인인가 — Design rationale

device 는 mouse 부터 disk·network 까지 속도·기능이 천차만별이라 kernel 이 일일이 감당할 수 없습니다. 그래서 device 쪽 복잡성을 **controller** 가 떠안고(bad-sector mapping·prefetching·caching 등), host 는 controller 와 약속된 방식으로만 대화합니다(Ch.12.2). 그 "대화법"이 점점 발전해, register 직접 제어(MMIO)에서 → CPU 를 안 묶는 interrupt → 대량 전송을 통째로 넘기는 DMA 로 이어집니다 — 각 단계는 *CPU 를 단순 복사에서 해방*하려는 같은 동기에서 나옵니다(Ch.12.7).

---

## 3. 작은 예 — polling 기반 write handshake

host 와 controller 가 두 개의 bit 으로 손발을 맞추는 가장 단순한 handshake 입니다(Ch.12.2.2). controller 는 status register 의 **busy bit** 로 자기 상태를(일하는 중=set), host 는 command register 의 **command-ready bit** 로 뜻을(명령 준비됨=set) 전합니다.

### 단계별 다이어그램

```d2
direction: down

A: "① host: busy bit clear 될 때까지\nstatus 반복 읽기 (polling)"
B: "② host: 명령 + data-out write\ncommand-ready bit set"
C: "③ controller: busy set\n명령 실행"
D: "④ controller: command-ready·error clear\n마지막으로 busy clear"
A -> B -> C -> D
```

### 코드 (개념적 polling write)

```c
// memory-mapped I/O: controller register 가 CPU 주소공간에 매핑됨
volatile uint8_t *STATUS  = (uint8_t *)0xFEE00000; // status (busy bit = bit0)
volatile uint8_t *CONTROL = (uint8_t *)0xFEE00001; // control (command-ready = bit0)
volatile uint8_t *DATAOUT = (uint8_t *)0xFEE00002; // data-out

void pio_write(uint8_t value) {
    while (*STATUS & 0x1) { /* busy-wait: busy bit 이 clear 될 때까지 */ }
    *DATAOUT = value;          // data-out register 에 출력 기록
    *CONTROL |= 0x1;           // command-ready set → controller 에 명령 전달
    // 이후 controller 가 busy set → 실행 → busy clear (완료 신호)
}
```

### 단계별 의미

| Step | 누가 | 무엇을 | 왜 |
|---|---|---|---|
| ① | host | busy clear 까지 status 반복 읽기 | controller 가 다음 명령 받을 준비됐는지 확인 (Ch.12.2.2) |
| ② | host | data-out write + command-ready set | 명령과 데이터 전달 |
| ③ | controller | busy set 후 명령 실행 | "지금 일하는 중" 표시 |
| ④ | controller | command-ready·error clear, busy clear | 완료 신호 (busy clear 가 끝남을 알림) |

:::note[여기서 잡아야 할 두 가지]
**(1) 한 번의 polling 은 값싸다** — register read + status bit logical-AND + 분기, 세 instruction 이면 됩니다(Ch.12.2.2). 문제는 device 가 좀처럼 준비 안 되는데 계속 들여다볼 때, 그 사이 CPU 가 할 다른 일이 밀린다는 점입니다.<br>
**(2) 이 낭비를 줄이려 "device 가 준비됐을 때 controller 가 CPU 를 불러주는" 발상이 interrupt** 입니다(§4). DV 관점에서 busy/command-ready bit 의 set/clear 순서가 protocol checker 로 검증할 핵심 시퀀스입니다.
:::
---

## 4. 일반화 — 네 가지 제어 방식과 저장장치

### 4.1 Memory-Mapped I/O 와 control register (Ch.12.2.1)

controller 는 register 몇 개를 두고 CPU 가 bit 패턴을 읽고 쓰며 대화합니다. register 에 닿는 길은 둘 — 전용 **I/O instruction** 과, device register 를 CPU physical address 공간에 끼워 넣어 평범한 load/store 로 접근하는 **memory-mapped I/O** 입니다. 후자가 더 빠르고 다루기 쉬워, 책은 *"most I/O is performed by device controllers using memory-mapped I/O"* 라고 적습니다.

| register | 방향 | 역할 |
|----------|------|------|
| **data-in** | host read | 입력 받기 |
| **data-out** | host write | 출력 보내기 |
| **status** | host read | busy·command 완료·error 표시 |
| **control** | host write | 명령 시작·mode 변경 |

data register 가 보통 1–4 byte 로 작아서, 일부 controller 는 burst 를 담을 **FIFO chip** 을 둡니다.

### 4.2 Interrupt: 비동기 알림 (Ch.12.2.3)

CPU 는 매 instruction 을 마칠 때마다 **interrupt-request line** 을 살핍니다. controller 가 신호를 걸면 CPU 는 상태를 저장하고 **interrupt handler** 로 점프, 처리 후 복귀합니다.

```d2
direction: right
R: "device: raise\n(request line 신호)"
C: "CPU: catch\n(상태 저장)"
D: "dispatch\n(vector → handler)"
H: "handler: 처리\n→ clear"
R -> C -> D -> H
```

현대 시스템이 더하는 것: request line 이 **nonmaskable**(복구 불가 memory error 등 절대 무시 금지)과 **maskable**(device 용, 중요 구간 잠시 차단 가능)로 나뉨; **interrupt vector**(handler 주소 표)를 번호로 인덱싱; device 가 많으면 한 칸이 리스트를 가리키는 **interrupt chaining**; **priority level** 로 높은 interrupt 가 낮은 것 preempt. 비싼 처리는 **FLIH**(빠른 큐잉)와 **SLIH**(실제 처리)로 쪼갬. interrupt 는 device 전용이 아니라 system call·page fault·0 나누기도 같은 길로 들어옵니다(M01·M03 연결).

### 4.3 DMA: 대량 전송 떠넘기기 (Ch.12.2.4)

CPU 가 byte 를 하나씩 미는 **programmed I/O(PIO)** 는 값비싼 processor 를 단순 복사에 묶는 낭비입니다. 그래서 **DMA controller** 전용 processor 에 떠넘깁니다.

전송 흐름: host 가 메모리에 **DMA command block**(source 주소, destination 주소, byte 수)을 만들고, CPU 는 그 *주소만* DMA controller 에 적어주고 다른 일로 넘어갑니다. 흩어진 여러 구간을 한 command 로 모으는 것이 **scatter–gather** 입니다. 이후 device controller 와 DMA controller 가 **DMA-request·DMA-acknowledge** 두 wire 로 손발을 맞춰 전송하고, 모두 끝나면 DMA controller 가 CPU 에 **interrupt** 를 겁니다.

DMA 가 bus 를 점유하는 동안 CPU 는 잠깐 main memory 에 못 닿지만 cache 안 데이터는 계속 씁니다 — bus 사이클을 조금씩 훔치는 이것이 **cycle stealing** 입니다. 주소 방식도 갈립니다: physical address 를 그대로 쓰거나, virtual address 를 변환해 쓰는 **DVMA(direct virtual memory access)** 를 둬 두 memory-mapped device 간 직접 전송도 합니다(M03 의 주소 번역과 연결).

### 4.4 저장장치: HDD vs NVM/SSD (Ch.11.1)

| | **HDD** | **NVM/SSD** |
|---|---------|-------------|
| 방식 | 기계적(platter 회전, head 이동) | 전기적(NAND flash die + controller) |
| 지연 | seek time + rotational latency | 없음 |
| 스케줄링 | head 이동 최소화 (FCFS/SCAN/C-SCAN) | FCFS 충분 (Linux NOOP: 인접 병합만) |
| 성능 | 수백 IOPS | 수십만 IOPS |
| 연결 | SATA 등 | NVMe(PCI bus 직결) |

NAND 의 까다로움: page 단위로 읽고 쓰지만 덮어쓸 수 없어 먼저 **block 단위 erase** 필요(erase 가 가장 느림); erase 반복하면 닳아(약 10만 P/E cycle) 수명을 **DWPD** 로 잼. controller 가 이를 가립니다 — 유효 데이터 위치를 추적하는 **FTL(flash translation layer)**, block 을 비우는 **garbage collection**, 여유 공간을 빼두는 **over-provisioning**(보통 20%), 닳음을 고르게 하는 **wear leveling**. garbage collection 이 내부 read/write 를 유발해 한 write 가 여러 I/O 로 부푸는 **write amplification** 이 성능을 깎을 수 있습니다(Ch.11.1.2, §11.3). 저장장치도 host controller(HBA)·MMIO·DMA 구도 그대로이고, 상위에서는 **LBA(logical block address)** 로 다룹니다(Ch.11.1.4–11.1.5).

### 4.5 오류 검출·정정 (Ch.11.4)

**parity bit**(단일 bit 검출), **checksum**·**CRC**(다중 bit 검출), **ECC**(검출 넘어 *정정*; disk per-sector, flash per-page). 몇 bit 만 틀리면 controller 가 바로잡아 **soft error**, 한계 넘으면 **hard error** 보고. ECC 는 DRAM·datapath 보호에도 쓰입니다.

---

## 5. 디테일 — 세 제어 방식의 자리매김과 kernel I/O subsystem

### 5.1 polling vs interrupt vs DMA — 언제 무엇을 (Ch.12.2.3, §12.7)

```
평상시        → interrupt (CPU 를 안 묶음, 책: "now much more common than polling")
초고속 구간   → polling (interrupt 오버헤드보다 빠를 때, high-throughput I/O)
대량 전송      → DMA (CPU 를 단순 복사에서 해방)
```

책은 *"Interrupt-driven I/O is now much more common than polling, with polling being used for high-throughput I/O. Sometimes the two are used together"* 라고 정리합니다(Ch.12.2.3). device driver 가 I/O rate 에 따라 둘을 오가기도 합니다. I/O 성능의 일반 원칙(Ch.12.7): context switch 줄이기, 데이터 복사 줄이기, 단순 복사를 **DMA 를 아는 controller/channel 로 offload**.

| 방식 | CPU 점유 | 적합 |
|------|---------|------|
| Polling | 높음(busy-wait) | 초고속·짧은 대기 |
| Interrupt | 낮음 | 일반적 비동기 device |
| DMA | 매우 낮음(cycle stealing 만) | 대량 전송 |

### 5.2 Kernel I/O subsystem (Ch.12.3–12.4)

kernel 은 controller 차이를 표준 인터페이스 뒤로 숨기는 **device driver** 를 두어 새 peripheral 을 OS 재작성 없이 붙입니다. 그 위에 서비스를 더합니다: **I/O scheduling**(device 별 wait queue 재정렬, device-status table 로 추적), **buffering**(속도/전송단위/복사의미 차이 흡수), **caching**(빠른 메모리에 *사본*), **spooling/device reservation**(직렬화), **error handling & I/O protection**.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'interrupt 가 항상 polling 보다 빠르고 좋다']
**실제**: 처리량이 매우 높은 구간에서는 interrupt 오버헤드(context switch·handler dispatch)가 오히려 손해라, polling 이 빠릅니다(Ch.12.2.3). 그래서 둘을 함께 쓰고 driver 가 I/O rate 에 따라 오갑니다.<br>
**왜 헷갈리는가**: "busy-wait = 낭비"라는 인상 때문 — 짧고 빈번한 완료에는 polling 이 이김.
:::
:::danger[❓ 오해 2 — 'DMA 가 끝났는지는 CPU 가 계속 확인해야 한다']
**실제**: DMA 의 요점은 CPU 를 *놓아주는* 것입니다. CPU 는 command block 주소만 적어주고 다른 일을 하다가, 전송이 모두 끝나면 DMA controller 가 거는 **완료 interrupt** 로 통보받습니다(Ch.12.2.4).<br>
**왜 헷갈리는가**: polling mental model 을 DMA 에 그대로 적용해서 — 그러면 DMA 의 이점이 사라짐.
:::
:::danger[❓ 오해 3 — 'OS 가 SSD 의 wear leveling·FTL 을 직접 관리한다']
**실제**: OS 는 복잡성을 모른 채 그저 **logical block(LBA)** 을 읽고 씁니다. FTL·garbage collection·wear leveling·over-provisioning 은 모두 device controller 가 가립니다(Ch.11.1.2).<br>
**왜 헷갈리는가**: "OS 가 저장장치를 관리"라는 큰 그림 때문 — 실제 NAND 관리는 controller 몫.
:::
:::danger[❓ 오해 4 — 'DMA 는 항상 physical address 를 쓴다']
**실제**: physical 을 그대로 쓰는 구조도 있지만, virtual address 를 변환해 쓰는 **DVMA** 도 있습니다(Ch.12.2.4). 어느 쪽인지가 IOMMU 검증의 핵심 — device 가 내는 주소를 누가 번역·보호하는가(M03 연결).<br>
**왜 헷갈리는가**: "device 는 물리 주소만 안다"는 단순화 때문.
:::
### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| polling write 후 명령이 실행 안 됨 | busy/command-ready bit set/clear 순서 위반 | status·control register 상태 머신, handshake 시퀀스 |
| DMA 완료 후 interrupt 가 안 옴 | 완료 interrupt raise 누락 | DMA controller 의 done→interrupt 경로 |
| DMA 전송 byte 수 불일치 | command block 의 length 필드 처리 | source/dest/count 파싱, scatter-gather 리스트 |
| DMA 중 CPU 가 stale 데이터를 봄 | cycle stealing 중 cache 일관성 | I/O coherency, snoop (M05 메모리 모델과 연결) |
| device 가 IOMMU 밖 메모리에 접근 | DVMA 주소 변환/보호 누락 | IOMMU page table, device 주소 번역 |
| ECC 정정 한계 넘었는데 hard error 미보고 | soft/hard error 임계 처리 | per-sector/per-page ECC 재계산 비교 |

---

## 7. 핵심 정리 (Key Takeaways)

- **controller 가 device 복잡성을 떠안고, host 는 register 로 대화한다.** memory-mapped I/O 의 네 register: data-in/out, status, control.
- **세 제어 방식.** polling(busy-wait, 초고속 구간) → interrupt(raise→catch→dispatch→clear, 일반적) → DMA(command block, cycle stealing, 완료 interrupt; 대량 전송). 원칙: 단순 복사는 DMA 로 offload.
- **interrupt 는 device 전용이 아니다** — system call·page fault·trap 도 같은 길. nonmaskable/maskable, vector, chaining, priority, FLIH/SLIH.
- **저장장치는 controller·MMIO·DMA 구도 그대로.** HDD(seek/rotational, SCAN)는 NVM/SSD(NAND/FTL/wear leveling, FCFS, NVMe 직결)와 물리·스케줄링이 다르다. 상위는 LBA.
- **ECC 가 정정까지** — soft/hard error, DRAM·datapath 보호에도.

:::caution[실무 주의점]
- DMA 검증에서 완료 interrupt·byte count·cycle stealing 중 cache 일관성을 반드시 체크하세요 — silent 데이터 손상이 가장 위험합니다.
- DMA 가 physical 인지 DVMA(virtual)인지 spec 에서 먼저 확인하고, IOMMU 가 device 주소를 번역·보호하는지 테스트하세요.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — DMA 경로 추적 (Bloom: Trace)]
host 가 disk 에서 4 KB 를 메모리로 읽으려 한다. DMA 를 쓸 때 CPU 가 직접 하는 일과, 그 후 일어나는 일을 순서대로 짚어라.
<details>
<summary>정답</summary>

(Ch.12.2.4):
1. CPU(host)가 메모리에 **DMA command block** 작성 — source(disk LBA 관련), destination(메모리 주소), byte 수(4 KB).
2. CPU 는 command block 의 *주소만* DMA controller 에 적어주고 → **다른 일로 넘어감**(여기서 CPU 해방).
3. device controller ↔ DMA controller 가 **DMA-request/acknowledge** wire 로 손발 맞춰 전송, bus 점유는 **cycle stealing**.
4. 전송 완료 시 DMA controller 가 CPU 에 **interrupt** → 완료 통보.
- DV 포인트: 2(주소만 전달), 4(완료 interrupt)가 핵심 검증 지점.

</details>
:::
:::tip[🤔 Q2 — 제어 방식 선택 (Bloom: Evaluate)]
초당 수십만 개의 작은 완료 이벤트가 발생하는 초고속 NVMe 워크로드에서, interrupt-driven 보다 polling 이 유리할 수 있는 이유는?
<details>
<summary>정답</summary>

- 각 완료마다 interrupt 를 걸면 **context switch + handler dispatch** 오버헤드가 이벤트 수만큼 곱해져 CPU 가 오히려 더 바빠진다.
- 완료가 매우 빈번하고 빠르면, CPU 가 status 를 **polling** 하는 비용(register read + AND + 분기, 3 instruction)이 interrupt 오버헤드보다 작아진다(Ch.12.2.3, "polling being used for high-throughput I/O").
- 실제로는 driver 가 I/O rate 에 따라 둘을 오가며("Sometimes the two are used together"), 저부하엔 interrupt, 고부하엔 polling.
- 평가: "interrupt 가 항상 우월"이 아니라 *부하 의존* — throughput 기준 trade-off.

</details>
:::
### 7.2 출처

**Internal (HDG)**
- `os_io_systems_spec.md` — controller/MMIO, polling handshake, interrupt, DMA/scatter-gather/cycle stealing/DVMA, kernel I/O subsystem (Ch.12 정독 요약)
- `os_mass_storage_spec.md` — HDD vs NVM/SSD, FTL/wear leveling, NVMe, LBA, ECC (Ch.11 정독 요약)
- `os_concepts_guide.md` — 시리즈 3~4번 "어디에 남는가 / 어떻게 나르는가"

**External**
- Silberschatz et al. *Operating System Concepts*, 10th ed. — **Ch.11 Mass-Storage Structure**(§11.1 HDD/NVM, §11.2–3 스케줄링, §11.4 ECC), **Ch.12 I/O Systems**(§12.2.1 MMIO, §12.2.2 polling, §12.2.3 interrupt, §12.2.4 DMA, §12.3–4 kernel I/O, §12.7 성능)

---

## 다음 모듈

→ [Module 05 — 동기화 · 메모리 모델 · 데드락](../05_sync_memory_model_deadlock/): 여러 흐름(그리고 DMA 같은 동시 행위자)이 같은 메모리를 만질 때의 race 와, 그것을 막는 atomic·barrier·lock, 그리고 잘못 쓰면 빠지는 deadlock.

[퀴즈 풀어보기 →](../quiz/04_storage_io_dma_quiz/)
