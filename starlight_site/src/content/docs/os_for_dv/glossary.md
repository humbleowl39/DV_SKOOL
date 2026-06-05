---
title: "OS 용어집"
---

이 페이지는 본 코스에서 사용되는 OS 핵심 용어 정의 모음입니다. 항목은 ISO 11179 형식을 따릅니다 (**Definition / Source / Related / Example / See also**). 정의는 개념이 *무엇인가*를 한 문장으로 진술하고, 예시는 별도 **Example** 필드에 둡니다.

:::tip[검색 활용]
상단 검색창에 용어를 입력하면 본문에서의 사용처도 함께 찾을 수 있습니다.
:::
---

## A — Access Matrix / Atomic Instruction / ASID

### Access Matrix

**Definition.** 행을 protection domain, 열을 object 로 두고 각 칸에 해당 domain 이 해당 object 에 수행 가능한 연산 집합을 담아 시스템의 접근 정책을 표현하는 추상 모델.

**Source.** Silberschatz *Operating System Concepts* 10th ed., §17.5.

**Related.** Domain, Access Right, Protection Ring, IOMMU.

**Example.** 행 D2(어느 device 의 domain), 열 "Mem region X" 칸에 `{read, write}` 가 있으면 그 device 는 영역 X 를 읽고 쓸 수 있고, 나머지 칸이 비면 다른 영역엔 접근 불가.

**See also.** [Module 06 — 보호·보안](../06_protection_security/)

### Atomic Instruction

**Definition.** 한 메모리 word 를 다른 흐름이 끼어들 수 없는 나눌 수 없는 단위로 검사·수정 또는 교환하는 하드웨어 명령.

**Source.** Silberschatz 10th ed., §6.4.2.

**Related.** test_and_set, compare_and_swap (CAS), Spinlock, Memory Barrier.

**Example.** x86 의 `cmpxchg` 에 `lock` prefix 를 붙여 bus 를 잠가 compare-and-swap 을 atomic 으로 수행.

**See also.** [Module 05 — 동기화](../05_sync_memory_model_deadlock/)

### ASID (Address-Space Identifier)

**Definition.** TLB entry 에 부착해 어느 process 의 주소 변환인지 구분함으로써 context switch 마다 TLB 를 비우지 않게 하는 식별자.

**Source.** Silberschatz 10th ed., §9.3.2.1.

**Related.** TLB, Context Switch, Page Table.

**Example.** 두 process 의 번역을 서로 다른 ASID 로 TLB 에 섞어 둔 채 context switch 해도, 각 entry 의 ASID 로 자기 것만 hit 되어 flush 가 불필요.

**See also.** [Module 03 — 메모리·Paging·TLB](../03_memory_paging_tlb/)

---

## C — Context Switch / Critical Section

### Context Switch

**Definition.** 한 코어를 한 process 에서 다른 process 로 넘기기 위해 현재 process 의 실행 상태를 그 PCB 에 저장하고 새 process 의 상태를 PCB 에서 복원하는 동작.

**Source.** Silberschatz 10th ed., §3.2.3.

**Related.** PCB, Dispatcher, Interrupt, Scheduling.

**Example.** interrupt 가 들어오면 OS 가 P1 의 program counter·register 를 PCB(P1)에 save 하고 PCB(P2)를 restore — 이 동안 유용한 일을 못 하는 순수 오버헤드.

**See also.** [Module 02 — 프로세스·스케줄링](../02_process_scheduling/)

### Critical Section

**Definition.** 공유 데이터를 건드리는 코드 구간으로, 한 흐름이 그 안에 있을 때 다른 어떤 흐름도 자기 critical section 에 들어오면 안 되는 영역.

**Source.** Silberschatz 10th ed., §6.2.

**Related.** Race Condition, Mutual Exclusion, Mutex, Semaphore.

**Example.** producer 의 `count++` 와 consumer 의 `count--` 가 둘 다 critical section 이며, 동시에 실행되면 race condition 으로 결과가 깨진다.

**See also.** [Module 05 — 동기화](../05_sync_memory_model_deadlock/)

---

## D — Deadlock / DMA / Domain / Dual-Mode

### Deadlock

**Definition.** 한 집합 안의 모든 thread 가 그 집합 안의 다른 thread 만이 일으킬 수 있는 사건을 기다리며 아무도 진행하지 못하는 상태.

**Source.** Silberschatz 10th ed., §8.1.

**Related.** Mutual Exclusion, Hold and Wait, No Preemption, Circular Wait, Resource-Allocation Graph.

**Example.** thread one 이 `first→second`, thread two 가 `second→first` 순으로 두 mutex 를 잡으려 하면 각자 하나씩 쥔 채 상대 것을 기다리며 멈춘다.

**See also.** [Module 05 — 동기화·데드락](../05_sync_memory_model_deadlock/)

### DMA (Direct Memory Access)

**Definition.** CPU 대신 전용 controller 가 메모리와 device 사이 대량 데이터를 직접 옮겨, 옮기는 동안 CPU 를 단순 복사에서 해방하는 I/O 전송 방식.

**Source.** Silberschatz 10th ed., §12.2.4.

**Related.** Command Block, Cycle Stealing, Scatter–Gather, Interrupt, DVMA.

**Example.** host 가 source/destination 주소·byte 수를 담은 command block 을 만들고 그 주소만 DMA controller 에 적어주면, controller 가 cycle stealing 으로 전송 후 완료 interrupt 를 건다.

**See also.** [Module 04 — Storage·I/O·DMA](../04_storage_io_dma/)

### Domain (of Protection)

**Definition.** 한 process 가 접근할 수 있는 access right(`<object, rights-set>` 쌍)의 모음으로 정의되는 보호 단위.

**Source.** Silberschatz 10th ed., §17.4.

**Related.** Access Right, Access Matrix, Protection Ring, Least Privilege.

**Example.** dual-mode 의 kernel/user 는 가장 단순한 두 domain 이며, UNIX 의 user 별·Android 의 app 별 UID 가 그 위에 더 정교한 domain 으로 얹힌다.

**See also.** [Module 06 — 보호·보안](../06_protection_security/)

### Dual-Mode

**Definition.** 하드웨어가 실행 모드를 mode bit 으로 user mode 와 kernel mode 로 구분해, privileged instruction 을 kernel mode 에서만 허용하는 보호 메커니즘.

**Source.** Silberschatz 10th ed., §1.4.2.

**Related.** Mode Bit, Privileged Instruction, System Call, Protection Ring.

**Example.** mode bit 이 user(1)일 때 I/O 제어 명령을 시도하면 하드웨어가 실행하지 않고 OS 로 trap 한다.

**See also.** [Module 01 — OS 개요](../01_os_overview/)

---

## F — FTL (Flash Translation Layer)

### FTL

**Definition.** NAND flash 의 logical block 을 어느 physical page 에 둘지 추적하고 erase·wear 제약을 host 에게 감추는 SSD controller 내부의 매핑 계층.

**Source.** Silberschatz 10th ed., §11.1.2.

**Related.** Wear Leveling, Garbage Collection, Over-provisioning, Write Amplification, LBA.

**Example.** OS 는 LBA 만 읽고 쓰고, FTL 이 garbage collection·wear leveling 으로 물리 page 배치를 알아서 관리한다.

**See also.** [Module 04 — Storage·I/O·DMA](../04_storage_io_dma/)

---

## I — Interrupt

### Interrupt

**Definition.** device 나 사건이 CPU 의 request line 에 신호를 걸어 현재 실행을 중단시키고 interrupt vector 가 가리키는 handler 로 제어를 비동기적으로 넘기는 메커니즘.

**Source.** Silberschatz 10th ed., §12.2.3.

**Related.** Interrupt Vector, Maskable/Nonmaskable, Context Switch, Trap, DMA.

**Example.** DMA 전송이 끝나면 DMA controller 가 interrupt 를 raise → CPU 가 catch → vector 로 dispatch → handler 가 처리 후 clear.

**See also.** [Module 04 — Storage·I/O·DMA](../04_storage_io_dma/)

---

## L — Least Privilege / Logical Address

### Least Privilege

**Definition.** 프로그램·사용자·시스템에 맡은 일에 꼭 필요한 만큼의 권한만 부여해 침해 시 피해를 권한 범위로 제한하는 보호 원칙.

**Source.** Silberschatz 10th ed., §17.2.

**Related.** Compartmentalization, Defense in Depth, Domain, Need-to-Know.

**Example.** 각 device 에 자기 버퍼 메모리만 IOMMU 로 매핑하면, 그 device 가 침해돼도 다른 영역에는 접근하지 못한다.

**See also.** [Module 06 — 보호·보안](../06_protection_security/)

### Logical Address

**Definition.** CPU 가 생성하는 주소로, 실행 시점 binding 에서는 MMU 가 physical address 로 번역하기 전의 가상 주소.

**Source.** Silberschatz 10th ed., §9.1.3.

**Related.** Physical Address, MMU, Relocation Register, Paging.

**Example.** relocation register 가 14000 이면 logical 346 은 physical 14346 으로 번역된다.

**See also.** [Module 03 — 메모리·Paging·TLB](../03_memory_paging_tlb/)

---

## M — Memory Barrier / Memory-Mapped I/O / MMU

### Memory Barrier

**Definition.** 이전의 모든 load/store 가 완료된 뒤에야 이후 load/store 가 수행되도록 강제해, weakly-ordered 메모리에서 변경의 가시성·순서를 보장하는 하드웨어 명령.

**Source.** Silberschatz 10th ed., §6.4.1.

**Related.** Memory Model (strongly/weakly ordered), Reordering, Atomic Instruction.

**Example.** `data = 42;` 다음·`ready = 1;` 이전에 barrier 를 넣으면 다른 core 가 `ready` 를 본 시점에 `data` 도 반드시 보인다.

**See also.** [Module 05 — 동기화](../05_sync_memory_model_deadlock/)

### Memory-Mapped I/O

**Definition.** device 의 control register 를 CPU 의 physical address 공간에 배치해 평범한 load/store 명령으로 device 를 제어하는 I/O 방식.

**Source.** Silberschatz 10th ed., §12.2.1.

**Related.** Control Register (data-in/out, status, control), Polling, Device Controller.

**Example.** status register 를 load 해 busy bit 을 확인하고, control register 에 store 해 command-ready bit 을 set 한다.

**See also.** [Module 04 — Storage·I/O·DMA](../04_storage_io_dma/)

### MMU (Memory-Management Unit)

**Definition.** 런타임에 logical/virtual address 를 physical address 로 번역하고 접근을 보호하는 하드웨어 장치.

**Source.** Silberschatz 10th ed., §9.1.3, §9.3.

**Related.** Paging, Page Table, TLB, Relocation Register, IOMMU.

**Example.** CPU 가 낸 [page number | offset] 의 page number 를 page table 로 frame number 로 바꾸고 offset 을 붙여 physical address 를 만든다.

**See also.** [Module 03 — 메모리·Paging·TLB](../03_memory_paging_tlb/)

---

## P — Paging / PCB / Privileged Instruction / Protection Ring

### Paging

**Definition.** 물리 메모리를 고정 크기 frame, 논리 메모리를 같은 크기 page 로 쪼개 process 의 page 를 임의의 빈 frame 에 흩어 담는 메모리 관리 기법.

**Source.** Silberschatz 10th ed., §9.3.1.

**Related.** Frame, Page Table, TLB, Internal Fragmentation, MMU.

**Example.** logical address 를 상위 비트(page number p)와 하위 비트(offset d)로 나눠 p 로 page table 을 인덱싱하면 external fragmentation 없이 할당이 가능하다.

**See also.** [Module 03 — 메모리·Paging·TLB](../03_memory_paging_tlb/)

### PCB (Process Control Block)

**Definition.** OS 가 한 process 의 state·program counter·register·scheduling·memory-management·I/O 정보를 담아 표현하는 자료구조.

**Source.** Silberschatz 10th ed., §3.1.3.

**Related.** Process, Context Switch, Scheduling.

**Example.** context switch 때 OS 가 현재 process 의 register 와 PC 를 PCB 에 저장하고 다음 process 의 PCB 에서 복원한다.

**See also.** [Module 02 — 프로세스·스케줄링](../02_process_scheduling/)

### Privileged Instruction

**Definition.** 시스템에 해를 끼칠 수 있어 kernel mode 에서만 실행이 허용되며 user mode 에서 시도하면 OS 로 trap 되는 명령.

**Source.** Silberschatz 10th ed., §1.4.2.

**Related.** Dual-Mode, Mode Bit, Trap, base/limit Register.

**Example.** I/O 제어·timer 관리·interrupt 관리·base/limit register 변경이 privileged instruction 에 속한다.

**See also.** [Module 01 — OS 개요](../01_os_overview/)

### Protection Ring

**Definition.** 특권을 동심원 계층으로 나눠 ring 0 이 모든 특권을 갖고 ring 사이는 정해진 gate/trap/interrupt 진입점으로만 넘어가게 하는 하드웨어 보호 모델.

**Source.** Silberschatz 10th ed., §17.3.

**Related.** Dual-Mode, Domain, Gate (syscall), Exception Level, Hypervisor.

**Example.** Intel 은 user=ring 3, kernel=ring 0, hypervisor=ring -1 을 두고, ARMv8 은 EL0(user)–EL3(secure monitor) 네 exception level 로 확장한다.

**See also.** [Module 06 — 보호·보안](../06_protection_security/)

---

## R — Race Condition

### Race Condition

**Definition.** 여러 실행 흐름이 같은 데이터를 동시에 다루고 그 최종 결과가 흐름들의 실행 순서에 좌우되는 상황.

**Source.** Silberschatz 10th ed., §6.1.

**Related.** Critical Section, Preemptive Scheduling, Mutual Exclusion, Atomic Instruction.

**Example.** `count++` 가 기계어로 load→연산→store 세 단계라, 두 흐름의 단계가 섞이면 +2 여야 할 값이 +1 만 반영된다.

**See also.** [Module 05 — 동기화](../05_sync_memory_model_deadlock/)

---

## S — System Call

### System Call

**Definition.** 사용자 프로그램이 trap(software interrupt)을 통해 kernel 의 service routine 을 호출하는, user 가 OS 기능을 요청하는 유일한 통로.

**Source.** Silberschatz 10th ed., §1.4.2, §2.3.

**Related.** Trap, API (POSIX/Win32), System-Call Interface, Dual-Mode.

**Example.** C 의 `read()` 는 libc 래퍼가 system-call interface 를 거쳐 read 번호로 테이블을 찾아 kernel 의 sys_read 를 trap 으로 호출한다.

**See also.** [Module 01 — OS 개요](../01_os_overview/)

---

## T — TLB

### TLB (Translation Look-aside Buffer)

**Definition.** 최근의 page→frame 번역을 담는 작고 빠른 associative cache 로, page table 의 메모리 접근을 회피해 주소 번역을 가속하는 하드웨어.

**Source.** Silberschatz 10th ed., §9.3.2.1.

**Related.** Paging, Page Table, ASID, Hit Ratio, MMU.

**Example.** 메모리 접근이 10 ns 일 때 TLB hit ratio 가 99% 면 실효 접근 시간이 약 10.1 ns 로 1%만 느려진다.

**See also.** [Module 03 — 메모리·Paging·TLB](../03_memory_paging_tlb/)

---

## 추가 약어

| 약어 | 풀네임 | 한 줄 의미 |
|------|--------|-----------|
| **PIO** | Programmed I/O | CPU 가 register 에 byte 를 하나씩 밀어 넣는 전송 |
| **MMIO** | Memory-Mapped I/O | device register 를 메모리 주소공간에 매핑해 load/store 로 제어 |
| **LBA** | Logical Block Address | 저장장치를 1차원 block 배열로 다루는 주소 |
| **DWPD** | Drive Writes Per Day | SSD 수명을 하루 쓰기 횟수로 나타낸 척도 |
| **CAS** | Compare-And-Swap | 기대값과 같을 때만 교환하는 atomic 명령 |
| **RAG** | Resource-Allocation Graph | thread·resource 의 request/assignment 를 그린 deadlock 판정 그래프 |
| **DVMA** | Direct Virtual Memory Access | virtual address 를 변환해 쓰는 DMA |
| **EL** | Exception Level | ARMv8 의 특권 계층(EL0 user ~ EL3 secure monitor) |
| **IOMMU** | I/O Memory Management Unit | device 가 내는 주소를 번역·보호하는 I/O 측 MMU |
