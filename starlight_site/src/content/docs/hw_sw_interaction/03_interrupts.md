---
title: "03 — 인터럽트 (level / edge / MSI / doorbell / IPI)"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** 인터럽트가 무엇이며, 하드웨어/소프트웨어 인터럽트와 fault/trap/abort가 어떻게 구분되는지 설명할 수 있다.
- **Differentiate** level 트리거와 edge 트리거의 동작·공유·missed-edge 위험을 구분할 수 있다.
- **Explain** MSI가 물리 IRQ 선을 메시지로 대체하는 방식과, 도어벨이 인터럽트의 *역방향*인 이유를 설명할 수 있다.
- **Differentiate** 마스킹/NMI, 공유 선, IPI, 그리고 인터럽트 스톰과 그 완화(coalescing/RSS)를 구분할 수 있다.
:::
:::note[사전 지식]
- [01 — 디바이스 레지스터](../01_registers_mmio_pmio/) (interrupt 분류: INT_ENABLE/STATUS/CLEAR)
- [02 — Side-effect & 배리어](../02_side_effects_barriers/) (status read-to-clear, 도어벨 순서)
:::
---

## 1. Why care? — "디바이스가 다 됐다는 걸 CPU는 어떻게 아나?"

### 1.1 시나리오 — 인터럽트가 사라졌다, 혹은 멈추지 않는다

가속기가 작업을 끝내면 인터럽트를 올려 드라이버를 깨워야 합니다. 두 가지 흔한 사고가 있습니다.

- **사라진 인터럽트(missed)**: 디바이스가 edge(짧은 펄스)로 신호하는데, 마침 그 순간 드라이버가 인터럽트를 마스킹해 두었습니다. status 래치가 없으면 그 펄스는 영영 사라지고, 드라이버는 영원히 완료를 기다립니다.
- **멈추지 않는 인터럽트(stuck)**: 디바이스가 level(지속 레벨)로 신호하는데, ISR이 디바이스의 INT_STATUS를 acknowledge(클리어)하지 않으면 선이 계속 active로 남아 ISR이 무한 재진입합니다.

두 사고의 뿌리는 똑같습니다 — **트리거 방식(level/edge)과 acknowledge 핸드셰이크를 정확히 이해하지 못한 것**. 검증 엔지니어에게 이것은 RTL의 인터럽트 출력 로직과 INT_STATUS/INT_CLEAR 레지스터의 동작을 검증하는 일이며, 가장 silent하고 위험한 버그가 여기서 나옵니다.

### 1.2 인터럽트란 무엇인가

> "*An interrupt is a request for the processor to suspend currently executing code so that an event can be processed in a timely manner. When accepted, the processor saves its state and executes a function called an interrupt handler (or ISR) to address the event.*" — Wikipedia, *Interrupt*

LDD3는 디바이스 쪽 관점으로 같은 것을 말합니다 — "*there must be a way for a device to let the processor know when something has happened. That way ... is interrupts.*" (LDD3 §intro, p.258). 역사적으로 인터럽트는 "*폴링 루프의 비생산적 대기를 없애기 위한 최적화*"로 발명되었습니다(DYSEAC, 1954) — 즉 인터럽트의 존재 이유 자체가 폴링(4장)의 낭비를 줄이기 위함입니다.

---

## 2. Intuition — 초인종 두 종류, 한 장 그림

:::tip[💡 한 줄 비유]
**Level 트리거** ≈ **누르고 있는 동안 계속 울리는 초인종**. 손을 떼야(=ISR이 원인을 처리·클리어해야) 멈춥니다. 여러 사람이 한 줄(wired-OR)을 공유할 수 있지만, 누가 눌렀는지는 일일이 확인해야 합니다.<br>
**Edge 트리거** ≈ **딩동 한 번 울리고 마는 초인종**. 그 순간을 놓치면(마스킹 중) 래치가 없는 한 영영 못 듣습니다.<br>
**도어벨** ≈ **반대 방향 초인종** — 이번엔 *소프트웨어가* 하드웨어에게 "일감 있다"고 누릅니다.
:::

### 한 장 그림 — 디바이스 → CPU, 그리고 그 역방향

```d2
direction: right

DEVS: "**Devices**\n(여러 소스)"
IC: "**Interrupt Controller**\nGIC / PLIC / APIC\n다수 소스 → 코어의 1~2 입력\nIPI도 중개" { style.fill: "#aed6f1" }
CPU: "**CPU core**\n명령 경계에서 수락\n→ ISR 실행"
ISR: "ISR\n원인 확인 + acknowledge(INT_CLEAR)\nbottom-half로 긴 일 위임"

DEVS -> IC: "IRQ 선 / MSI 메시지"
IC -> CPU: "인터럽트 신호"
CPU -> ISR: "vector → handler"
ISR -> DEVS: "acknowledge / INT_CLEAR" { style.stroke-dash: 4 }

DOORBELL: "**Doorbell (역방향)**\nSW가 디바이스에 알림\n디스크립터 준비 후 tail write" { style.fill: "#f9e79f" }
CPU -> DOORBELL: "writel(tail)"
DOORBELL -> DEVS: "디바이스 깨움 / 자기 인터럽트"
```

핵심: 디바이스는 인터럽트 컨트롤러를 거쳐 CPU에 신호하고(많은 소스 → 적은 코어 입력으로 집약), ISR은 짧게 acknowledge한 뒤 긴 작업은 bottom-half로 넘깁니다. 그리고 **도어벨**은 같은 그림의 *역방향* — 소프트웨어가 하드웨어를 깨우는 알림입니다.

---

## 3. 작은 예 — level vs edge에서 같은 "완료" 신호 처리하기

### 단계별 다이어그램

```d2
direction: down

LEVEL: "**Level 트리거**" {
  direction: down
  L1: "① 디바이스가 IRQ 선을 active로 올림\n(완료될 때까지 유지)"
  L2: "② CPU가 명령 경계에서 ISR 진입"
  L3: "③ ISR이 INT_STATUS 확인 → 원인 처리\n→ INT_CLEAR로 acknowledge"
  L4: "④ acknowledge로 선이 deassert\n안 하면 ISR 무한 재진입"
  L1 -> L2 -> L3 -> L4
}

EDGE: "**Edge 트리거**" {
  direction: down
  E1: "① 디바이스가 펄스(상승/하강 edge) 발생 후 선 해제"
  E2: "② 펜딩 인터럽트가 status 레지스터에 *래치*됨"
  E3: "③ ISR이 래치된 status로 원인 확인 → 처리"
  E4: "④ 마스킹 중 도착한 edge도 래치에 남음\n(래치 없으면 분실!)"
  E1 -> E2 -> E3 -> E4
}
```

### 단계별 의미

| 측면 | Level | Edge |
|------|-------|------|
| 신호 형태 | 지속 레벨, 처리 전까지 유지 | 순간 펄스 후 해제 |
| 공유 | wired-OR로 다수 공유 용이(ISR이 각 디바이스 폴) | 가능하나 래치/관리 필요 |
| 놓침 위험 | 거의 없음(유지되므로) | 마스킹 길면 **missed edge** — 래치 없으면 영구 분실 |
| 멈춤 조건 | acknowledge로 deassert 안 하면 **stuck**(무한 재진입) | 펄스라 자동 해제(하지만 status는 클리어 필요) |
| 단점 | wired-OR 기생 용량으로 spurious 가능 | 미스 edge 위험 |

### acknowledge 핸드셰이크 코드(개념)

```c
/* ISR — top-half는 짧게 */
irqreturn_t my_isr(int irq, void *dev_id) {
    u32 st = readl(regs + INT_STATUS);   /* 어떤 소스인지 확인 */
    if (!(st & MY_SOURCES)) return IRQ_NONE; /* 공유 선: 내 것 아니면 패스 */
    writel(st & MY_SOURCES, regs + INT_CLEAR); /* acknowledge — W1C 관용구 */
    schedule_work(&my_bh);               /* 긴 일은 bottom-half로 */
    return IRQ_HANDLED;
}
```

:::note[여기서 잡아야 할 두 가지]
**(1) level은 "acknowledge로 deassert"가 필수**, **edge는 "status 래치"가 필수**. 각 방식의 실패 모드(stuck / missed)는 정반대 지점에서 나옵니다.<br>
**(2) 공유 선에서는 ISR이 "내 인터럽트인지"부터 확인**해야 합니다 — INT_STATUS를 읽어 자기 소스가 아니면 `IRQ_NONE`을 반환.
:::

---

## 4. 일반화 — 인터럽트의 분류와 메커니즘

### 4.1 하드웨어 vs 소프트웨어, fault/trap/abort

인터럽트는 하드웨어 소스(외부 디바이스의 IRQ 선 또는 내장 타이머 — CPU 클럭에 비동기, 명령 경계에서만 처리)와 소프트웨어 소스(`int 0x80`/`syscall`/`svc` 같은 명령, 또는 0 나눗셈·페이지 폴트 같은 예외 조건)로 나뉩니다 (Wikipedia, *Interrupt*).

x86은 예외를 셋으로 구분합니다:

| 종류 | 복귀 주소 | 재시작 | 용도 |
|------|-----------|--------|------|
| **Fault** | faulting 명령 | 가능 | page fault, GP fault |
| **Trap** | 다음 명령 | 가능 | `int n`, breakpoint, syscall |
| **Abort** | 미정의/불가 | 불가 | machine check, 심각한 HW 에러 |

ARM은 이 모두를 *exception*으로 묶고, RISC-V는 외부를 *interrupt*, 내부를 *exception*으로 부릅니다.

### 4.2 MSI — IRQ 선을 메시지로

> "*A message-signaled interrupt does not use a physical interrupt line. Instead, a device signals its request for service by sending a short message over some communications medium, typically a computer bus.*" — Wikipedia, *Interrupt*

MSI는 edge처럼 동작합니다(메시지는 순간 이벤트). 인터럽트의 *정체*가 메시지 payload 비트에 실려 있어, 물리 선 수보다 훨씬 많은 인터럽트를 다중화할 수 있습니다. **PCI Express는 MSI를 전적으로 사용** — 순수 PCIe 링크에는 INTx 물리 선이 없고, 레거시 호환은 in-band 메시지로 emulated INTx를 만듭니다.

### 4.3 도어벨 — 인터럽트의 역방향

도어벨은 소프트웨어가 하드웨어에게 일감을 알리는 메커니즘입니다 — "*place data in some well-known ... memory locations and 'ring the doorbell' by writing to a different memory location.*" (Wikipedia, *Interrupt*). 도어벨 영역은 (1) 디바이스가 폴링하는 메모리거나, (2) 실제 레지스터로 write-through되거나, (3) 디바이스 레지스터에 직결되어 디바이스 자체 CPU에 인터럽트를 일으킵니다. NIC/NVMe/RDMA/가속기의 표준 패턴: 호스트가 디스크립터를 DRAM에 큐잉하고 tail 포인터를 도어벨에 씁니다(2장의 디스크립터→도어벨 순서가 여기서 중요).

### 4.4 마스킹, NMI, 공유, IPI, 스톰

- **마스킹**: mask 레지스터의 각 비트가 한 소스를 disable. disable된 인터럽트는 무시되거나 펜딩으로 보류. **NMI(non-maskable)** 는 마스킹 불가 — 워치독, 전원 손실 경고 등 무시할 수 없는 이벤트.
- **공유 선**: 다수 디바이스가 한 물리 IRQ를 공유하면 한 디바이스의 spurious가 다른 디바이스에 영향을 주고, ISR 부하가 공유자 수에 비례.
- **인터럽트 컨트롤러**: ARM GIC / RISC-V PLIC / x86 APIC가 많은 소스를 코어의 1~2 입력으로 집약하고, **IPI(inter-processor interrupt)** 로 한 코어가 다른 코어에 신호하도록 중개.
- **인터럽트 스톰**: 저부하에서 낮은 latency·오버헤드지만 고율에서 급격히 악화 — "*overall system performance is severely hindered by excessive processing time spent handling interrupts ... an interrupt storm.*" 완화책: **coalescing**(N 이벤트 또는 T μs까지 인터럽트 지연), **RSS**(flow tuple 해시로 코어 분산), 소프트웨어 **RPS/RFS**.

---

## 5. 디테일 — 드라이버 API와 DV로의 환산

### 5.1 Linux 드라이버 API(LDD3, illustrative)

인터럽트 선은 한정된 자원이라 모듈은 사용 전 요청하고 끝나면 해제해야 합니다 (LDD3 §Installing an Interrupt Handler, p.259). 2.6.10 시대 API는 `request_irq(irq, handler, flags, dev_name, dev_id)` / `free_irq(irq, dev_id)`이며 플래그 `SA_INTERRUPT`(fast handler), `SA_SHIRQ`(공유 가능), `SA_SAMPLE_RANDOM`(엔트로피)을 가졌습니다. 현재 커널은 이를 `IRQF_*`로 개명하고 MSI/MSI-X 변종을 더했지만, **계약의 형태 — handler 등록 → 짧은 top-half에서 IRQ 처리 → 긴 일은 bottom-half/softirq로 위임 — 는 불변**입니다.

### 5.2 DV 관점 — 인터럽트를 레지스터·드라이버 레벨에서 검증

| 검증 대상 | 무엇을 확인 | 어떻게 |
|-----------|-------------|--------|
| level deassert | acknowledge(INT_CLEAR) 후 IRQ 출력이 내려가는가 | 자극: 인터럽트 유발 → INT_CLEAR write → IRQ 신호 deassert 관찰(SVA) |
| edge 래치 | 마스킹 중 도착한 edge가 INT_STATUS에 남는가 | mask set → edge 유발 → unmask → status 비트 존재 확인 |
| acknowledge 핸드셰이크 | INT_STATUS read/INT_CLEAR write 동작이 W1C 스펙대로 | RAL access seq + directed: 클리어 후 재발생 시 다시 set |
| MSI 발행 | 트리거 시 올바른 address/data로 메시지 write | scoreboard가 MSI write 트랜잭션의 payload 검증 |
| 도어벨 | tail write 시 디바이스가 디스크립터 소비 + 순서 | 디스크립터 자극 → 도어벨 write → 소비된 디스크립터 내용 비교(2장 순서 의존) |
| 마스킹/NMI | mask된 소스는 IRQ 안 냄, NMI는 mask 무시 | INT_ENABLE 조합 sweep, illegal_bins로 금지 조합 검출 |

인터럽트 출력의 deassert/래치 타이밍은 SVA(SystemVerilog Assertion)로 연속 검증하기에 적합한 대표 대상입니다 — "INT_CLEAR write 후 N 클럭 내 IRQ deassert" 같은 시간 속성이 그 예입니다. 자극 시퀀스·scoreboard·coverage의 조립은 [UVM TLM/Scoreboard/Coverage](../../uvm/05_tlm_scoreboard_coverage/)와 결합됩니다.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'level이든 edge든 인터럽트 처리 방식은 같다']
**실제**: level은 ISR이 원인을 처리하고 *acknowledge로 deassert*해야 멈추고, edge는 펄스가 자동 해제되지만 *status 래치*가 없으면 마스킹 중 도착한 신호를 영영 놓칩니다. 실패 모드가 정반대(stuck vs missed)라 처리 로직이 다릅니다.<br>
**왜 헷갈리는가**: 둘 다 "인터럽트"라 동일해 보여서.
:::
:::danger[❓ 오해 2 — 'MSI는 특별한 인터럽트 선이 따로 있다']
**실제**: MSI는 물리 IRQ 선을 *쓰지 않습니다*. 디바이스가 버스로 짧은 메시지를 보내고, 인터럽트의 정체는 메시지 payload에 실립니다. PCIe는 INTx 물리 선이 아예 없어 MSI를 전적으로 씁니다.<br>
**왜 헷갈리는가**: "인터럽트=물리 선"이라는 고전적 모델 때문에.
:::
:::danger[❓ 오해 3 — '도어벨도 인터럽트의 일종이다(디바이스→CPU)']
**실제**: 도어벨은 *역방향* — 소프트웨어가 하드웨어에게 "일감 있다"고 알리는 것입니다. 디스크립터를 DRAM에 둔 뒤 tail을 도어벨에 write합니다(2장의 wmb 순서가 필수).<br>
**왜 헷갈리는가**: 둘 다 "알림"이라 방향을 혼동해서.
:::
:::danger[❓ 오해 4 — '인터럽트는 항상 폴링보다 좋다']
**실제**: 저부하에선 인터럽트가 낮은 오버헤드·latency를 주지만, 고율에서는 인터럽트 스톰으로 시스템이 붕괴할 수 있습니다. 그래서 coalescing/RSS나 인터럽트 후 폴링 하이브리드(4장)를 씁니다.<br>
**왜 헷갈리는가**: "인터럽트가 폴링의 낭비를 없앤다"는 역사적 동기만 기억해서.
:::

### DV 디버그 체크리스트 (이 장 내용으로 마주칠 첫 실패들)

| 증상 | 1차 의심 | 어디 보나 |
|------|----------|-----------|
| ISR이 무한 재진입 | level인데 acknowledge(INT_CLEAR) 후 deassert 안 됨 | RTL IRQ 출력 로직, INT_CLEAR→IRQ 경로 SVA |
| 완료 인터럽트가 가끔 사라짐 | edge인데 마스킹 중 도착, status 래치 없음 | INT_STATUS 래치 로직, mask 타이밍 |
| MSI가 엉뚱한 vector로 감 | MSI address/data 레지스터 설정 오류 | MSI capability 레지스터, 발행 payload scoreboard |
| 도어벨 울렸는데 디바이스가 옛 디스크립터 읽음 | 디스크립터 write가 도어벨보다 늦음(wmb 누락) | 자극 시퀀스 write 순서, 2장 배리어 |
| 공유 선에서 다른 디바이스 인터럽트까지 IRQ_HANDLED | ISR이 INT_STATUS로 자기 소스 확인 안 함 | ISR의 source 매칭, IRQ_NONE 반환 |
| NMI가 mask로 막힘 | NMI를 maskable 경로에 연결 | 인터럽트 컨트롤러의 NMI 경로 |

---

## 7. 핵심 정리 (Key Takeaways)

- **인터럽트 = 디바이스가 CPU의 주의를 요청하는 신호**. 폴링 낭비를 없애기 위한 최적화로 출발.
- **level(지속, acknowledge로 deassert, stuck 위험) vs edge(펄스, status 래치 필요, missed 위험)** — 실패 모드가 정반대.
- **MSI = 물리 선 대신 메시지**(payload에 정체). PCIe는 MSI 전용. **도어벨 = 역방향**(SW→HW 알림, 디스크립터→도어벨 순서 필수).
- **마스킹/NMI/공유 선/IPI**: 컨트롤러(GIC/PLIC/APIC)가 다수 소스를 집약하고 IPI를 중개. NMI는 마스킹 불가.
- **인터럽트 스톰**: 고율에서 붕괴 → coalescing/RSS/RPS·RFS, 그리고 인터럽트 후 폴링 하이브리드(4장).
- **DV 환산**: deassert/래치/acknowledge/MSI payload/도어벨 순서를 SVA + directed + scoreboard로 검증.

:::caution[실무 주의점]
- level은 INT_CLEAR로 *반드시* deassert 확인 — 빠지면 무한 재진입.
- edge는 마스킹 구간에서도 status 래치 보존을 검증 — missed edge가 가장 silent.
- 도어벨 전 `wmb()`(2장) — 디스크립터 유효성 보장.
:::

### 7.1 자가 점검

:::tip[🤔 Q1 — level vs edge 실패 모드 (Bloom: Analyze)]
완료 인터럽트가 *간헐적으로* 사라져 드라이버가 가끔 멈춘다. 트리거가 level일 가능성이 높은가, edge일 가능성이 높은가? 근거는?
<details>
<summary>정답</summary>

**edge** 가능성이 높습니다. edge는 순간 펄스라, 마침 그 시점에 인터럽트가 마스킹되어 있고 status 래치가 없으면 신호가 영영 분실됩니다(missed edge) — "간헐적 소실"의 전형. level은 처리 전까지 선을 유지하므로 사라지기보다는 stuck(무한 재진입)이 문제입니다. 따라서 INT_STATUS 래치가 마스킹 구간에도 펜딩을 보존하는지 검증해야 합니다.

</details>
:::
:::tip[🤔 Q2 — 인터럽트 vs 도어벨 방향 (Bloom: Evaluate)]
설계 리뷰에서 누군가 "도어벨도 인터럽트니까 인터럽트 컨트롤러에 연결하자"고 한다. 이 제안의 문제를 평가하라.
<details>
<summary>정답</summary>

도어벨과 인터럽트는 *방향이 반대*입니다. 인터럽트는 디바이스→CPU(주의 요청)이고, 도어벨은 SW→디바이스(일감 알림)입니다. 도어벨은 보통 디바이스의 MMIO 레지스터 write로 구현되어 디바이스를 깨우며, 호스트 CPU의 인터럽트 컨트롤러와는 무관합니다(도어벨이 디바이스 *자체* CPU에 인터럽트를 일으킬 수는 있음). 따라서 호스트 인터럽트 컨트롤러에 연결한다는 발상은 방향을 혼동한 것입니다. 다만 디바이스가 작업을 끝낸 뒤 *완료 인터럽트*를 호스트로 올리는 것은 별개의 정상 경로입니다.

</details>
:::

### 7.2 출처

**Internal (HDG)**
- `common/hw_sw_interaction_spec.md` §4 (Interrupts: 4.1~4.8)

**External**
- Wikipedia, *Interrupt* (CC-BY-SA 4.0) — hardware/software, level/edge, MSI, doorbell, masking/NMI, storm/coalescing
- Corbet, Rubini, Kroah-Hartman, *Linux Device Drivers 3rd Ed.* Ch. 10 (§Installing an Interrupt Handler, p.258–260)
- ARM *GIC Architecture Specification* (IHI0069) — interrupt controller / IPI

---

## 다음 모듈

→ [04 — 폴링 & 하이브리드 + DV 관점](../04_polling_hybrid_dv/): 인터럽트의 대안인 폴링, 둘의 trade-off, 인터럽트 후 임계 폴링 하이브리드, 그리고 이 코스 전체를 레지스터·드라이버 레벨에서 검증하는 법.

[퀴즈 풀어보기 →](../quiz/03_interrupts_quiz/)
