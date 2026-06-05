---
title: "04 — 폴링 & 하이브리드 + DV 관점"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** 폴링(polled I/O)이 무엇이며, busy-wait 폴링과 폴링 사이클의 trade-off를 설명할 수 있다.
- **Apply** host/controller가 busy/command-ready 비트로 주고받는 표준 폴링 핸드셰이크를 단계로 적용할 수 있다.
- **Evaluate** 주어진 워크로드에 폴링·인터럽트·하이브리드(인터럽트 후 임계 폴링) 중 무엇이 적합한지 latency·CPU 비용으로 평가할 수 있다.
- **Design** side-effect·인터럽트·폴링 핸드셰이크를 레지스터·드라이버 레벨에서 검증하는 시나리오를 설계할 수 있다.
:::
:::note[사전 지식]
- [01 — 레지스터](../01_registers_mmio_pmio/), [02 — Side-effect & 배리어](../02_side_effects_barriers/), [03 — 인터럽트](../03_interrupts/)
- (검증 적용) [UVM TLM/Scoreboard/Coverage](../../uvm/05_tlm_scoreboard_coverage/), [RAL](../../uvm/07_register_layer_ral/)
:::
---

## 1. Why care? — 인터럽트를 안 쓰고 직접 들여다보기

### 1.1 시나리오 — 폴링 주기를 잘못 잡으면

스토리지 드라이버가 명령 완료를 폴링으로 기다립니다. 폴링 주기를 너무 짧게(tight loop) 잡으면 CPU가 status 레지스터만 수백만 번 읽으며 코어 하나를 통째로 태웁니다. 반대로 너무 길게 잡으면 완료를 늦게 알아채 latency가 나빠지고, 그 사이 새 이벤트를 놓칠 수도 있습니다. 게다가 2장에서 본 것처럼 MMIO가 cacheable로 매핑되어 있으면 status read가 stale 값에 갇혀 루프가 *영원히* 끝나지 않습니다.

폴링은 가장 단순한 메커니즘이지만, *언제* 폴링이 인터럽트보다 나은지, 그리고 *어떻게* 핸드셰이크를 정확히 맞추는지를 모르면 CPU를 낭비하거나 이벤트를 놓칩니다. 검증 엔지니어에게 이것은 control/status 레지스터 쌍의 핸드셰이크 — busy/command-ready 비트가 host와 controller 사이에서 올바르게 토글되는지 — 를 검증하는 일입니다.

### 1.2 폴링이란 무엇인가

> "*Polling, or interrogation, refers to actively sampling the status of an external device by a client program as a synchronous activity. It is most often used in terms of I/O, and is also referred to as polled I/O or software-driven I/O.*" — Wikipedia, *Polling*

CPU가 디바이스의 status 레지스터를 준비될 때까지 반복해서 읽습니다. 이것이 tight read loop면 **busy-wait 폴링** — 단순하지만 CPU 사이클을 낭비합니다.

---

## 2. Intuition — 냄비를 들여다볼까, 알림을 기다릴까, 한 장 그림

:::tip[💡 한 줄 비유]
**폴링** ≈ **냄비 앞에 서서 끓나 안 끓나 계속 들여다보는 것**. 끓는 즉시 알 수 있지만(낮은 latency) 그동안 다른 일을 못 합니다(CPU 낭비).<br>
**인터럽트** ≈ **타이머를 맞춰두고 자리를 뜨는 것**. 알림이 올 때까지 다른 일을 하지만, 알림 처리 비용(ISR 진입)이 있고 알림이 폭주하면(스톰) 알림 처리만 하다 끝납니다.<br>
**하이브리드** ≈ **첫 알림에 부엌으로 와서 그 뒤로는 잠깐 직접 지켜보는 것** — 한 번 깨어나면 버스트가 끝날 때까지 폴링으로 연속 처리(추가 알림 불필요).
:::

### 한 장 그림 — 세 가지 대기 전략

```d2
direction: right

POLL: "**폴링**\nstatus 반복 read\n낮은 latency, 높은 CPU\n(busy-wait)" { style.fill: "#aed6f1" }
INT: "**인터럽트**\nISR 대기\n~0 CPU idle, 고율 스톰 위험" { style.fill: "#abebc6" }
HYB: "**하이브리드**\n인터럽트로 1회 wake\n→ 큐 빌 때까지 폴링\n(NAPI / NVMe busy-poll)" { style.fill: "#f9e79f" }

LOAD: "워크로드"
LOAD -> POLL: "저지연·예측가능 요구"
LOAD -> INT: "저부하·산발 이벤트"
LOAD -> HYB: "고율 버스트"
```

세 전략은 **CPU 비용과 latency를 맞바꿉니다.** 폴링은 latency를 사고 CPU를 지불하고, 인터럽트는 idle CPU를 아끼되 고율에서 스톰으로 무너지며, 하이브리드는 둘의 장점을 버스트 구간에 결합합니다.

---

## 3. 작은 예 — 표준 폴링 핸드셰이크 (host ↔ controller)

HDG 스펙이 든 canonical 폴링 알고리즘은 host와 controller가 레지스터의 네 비트(busy / command-ready / read / write)를 두고 번갈아 동작합니다 (Wikipedia, *Polling*).

### 단계별 다이어그램

```d2
direction: down

H1: "**Host ①** busy 비트가 클리어될 때까지 read 루프"
H2: "**Host ②** command 레지스터에 명령 기록\n(write면 write 비트 set + data-out 채움)"
H3: "**Host ③** command-ready 비트 set"
C1: "**Controller ①** command-ready 보이면 busy 비트 set"
C2: "**Controller ②** 명령 read → write면 data-out을 디바이스로,\nread면 data-in을 디바이스에서 로드"
C3: "**Controller ③** command-ready clear, error clear, busy clear"
H1 -> H2 -> H3 -> C1 -> C2 -> C3
C3 -> H1: "다음 명령 (busy 풀림)"
```

### 단계별 의미

| 행위자 | 단계 | 핵심 |
|--------|------|------|
| Host | busy 폴링 | controller가 한가해질 때까지 대기 |
| Host | command + (write 시) data-out | 일감 적재 |
| Host | command-ready set | "내 명령 준비됐다" |
| Controller | busy set | 처리 시작 표시 — host의 다음 명령 차단 |
| Controller | 명령 실행 | write/read 방향에 따라 data 이동 |
| Controller | command-ready/error/busy clear | 완료 + 다음 라운드 준비 |

이것이 control/status 레지스터 쌍이 어떤 추상화 레벨에서든 구현하는 **최소 hand-off 계약**입니다.

### 폴링 루프 코드(개념)

```c
/* busy-wait 폴링 — uncached MMIO 가정(2장) */
while (readl(regs + STATUS) & STATUS_BUSY)
    cpu_relax();                 /* tight loop 완화 */
writel(cmd, regs + COMMAND);
writel(data, regs + DATA_OUT);
writel(CMD_READY, regs + STATUS);  /* command-ready */
while (!(readl(regs + STATUS) & STATUS_DONE))
    cpu_relax();
```

:::note[여기서 잡아야 할 두 가지]
**(1) busy/command-ready/done은 host와 controller가 *교대로* 소유**하는 비트입니다 — 누가 set하고 누가 clear하는지가 명확해야 deadlock이 안 납니다.<br>
**(2) 폴링은 2장의 side-effect/uncached와 직결**됩니다. status가 cacheable면 stale로 무한 루프, clear-on-read면 두 번 읽기 금지.
:::

---

## 4. 일반화 — 폴링 변종과 인터럽트와의 trade-off

### 4.1 폴링 사이클과 변종

**폴링 사이클**은 "*각 요소가 한 번씩 모니터되는 시간*"입니다. 너무 빠르면 CPU 낭비, 너무 느리면 이벤트 누락 (Wikipedia, *Polling*).

- **Roll-call 폴링**: 마스터가 고정 순서로 각 디바이스를 질의하되, 디바이스마다 timeout을 둬 lock-up을 방지.
- **Hub(token) 폴링**: 각 디바이스가 다음 디바이스를 폴링해 ring을 형성, 첫 디바이스에 닿으면 사이클 재시작.

### 4.2 폴링 vs 인터럽트

| 측면 | 폴링 | 인터럽트 |
|------|------|----------|
| idle 시 CPU 비용 | 높음(busy-wait) 또는 스캔 오버헤드 | ~0 |
| latency | 폴링 사이클에 bound | 하드웨어 bound(수 사이클 + ISR 진입) |
| 구현 | trivial: read 루프 | ISR, vector table, 컨트롤러 설정 필요 |
| 초고율에서 | 예측 가능 | [인터럽트 스톰](../03_interrupts/#4-일반화--인터럽트의-분류와-메커니즘)으로 붕괴 가능 |
| HW 구현 | 없음 — status만 노출 | IRQ 출력 / MSI 생성기 / 인터럽트 컨트롤러 필요 |

> "*An alternative to polling is the use of interrupts ... in many situations it is more efficient to use interrupts because it can reduce processor spinning and/or bandwidth consumption.*" — Wikipedia, *Polling*

### 4.3 하이브리드 — 두 세계의 결합

실무 드라이버는 둘을 *결합*합니다. 일반적인 경우는 인터럽트로 dispatch하되, ISR 오버헤드가 지배적인 고율 경로에서는 폴링으로 fall-back합니다(Linux 네트워크의 NAPI, NVMe/DPDK/SPDK의 busy-poll). 가장 널리 쓰이는 패턴은 **인터럽트 후 임계 폴링(threshold polling after interrupt)** — 디바이스가 인터럽트 한 번으로 드라이버를 깨우면, 드라이버가 status/completion 큐를 *비워질 때까지 폴링*해 버스트 동안의 추가 인터럽트를 피합니다. 이는 3장의 인터럽트 스톰 완화(coalescing/RSS)와 같은 동기 — 고율에서 인터럽트 처리 비용을 줄이려는 것입니다.

---

## 5. 디테일 — DV 관점: 코스 전체를 레지스터·드라이버 레벨에서 검증

이 장은 코스의 마무리로서, 1~4장의 각 메커니즘을 검증 환경에서 *어떻게 잡는지*를 통합합니다.

### 5.1 검증 레벨 두 축

검증은 크게 두 레벨에서 일어납니다.

- **레지스터 레벨**: control/status/interrupt/data/pointer 레지스터의 access policy, side-effect, reset 값을 RAL과 내장 시퀀스로 확인. "디바이스의 프로그래밍 모델이 스펙대로인가."
- **드라이버 레벨(시나리오)**: 실제 드라이버가 하는 순서 — busy 폴링 → 명령 적재 → command-ready → 완료 대기, 또는 디스크립터 준비 → 도어벨 → 완료 인터럽트 — 를 자극 시퀀스로 재현해 핸드셰이크 전체를 검증. "프로그래밍 모델을 *순서대로* 썼을 때 디바이스가 옳게 동작하는가."

### 5.2 메커니즘별 검증 매핑(통합)

```d2
direction: right

REG: "**레지스터 레벨**\nRAL hw_reset / bit_bash / access seq\nside-effect(W1C/RC) directed"
INTV: "**인터럽트**\nlevel deassert·edge 래치·acknowledge\nMSI payload — SVA + scoreboard"
POLLV: "**폴링**\nbusy/command-ready/done 핸드셰이크\ndeadlock·timeout directed"
COVV: "**Coverage**\n레지스터×방향×응답 cross\n인터럽트 모드×부하 시나리오"

REG -> COVV
INTV -> COVV
POLLV -> COVV
```

| 메커니즘 | 검증 항목 | UVM 도구 연결 |
|----------|-----------|----------------|
| 레지스터/MMIO(01) | 주소 디코드, reset, access policy | [RAL](../../uvm/07_register_layer_ral/) bit_bash / hw_reset / access seq |
| side-effect/순서(02) | clear-on-read, W1C, 디스크립터→도어벨 순서 | directed seq + scoreboard, RAL peek vs read |
| 인터럽트(03) | deassert, edge 래치, MSI payload, 마스킹 | SVA(시간 속성) + [scoreboard](../../uvm/05_tlm_scoreboard_coverage/) |
| 폴링(04) | busy/command-ready 핸드셰이크, deadlock/timeout | directed seq, illegal_bins로 금지 상태 검출 |
| 전체 | 모드×부하 조합 미검증 영역 | functional coverage cross + closure |

### 5.3 폴링 핸드셰이크의 대표 함정과 검증

| 함정 | 증상 | 검증 방법 |
|------|------|-----------|
| busy 비트를 controller가 clear 안 함 | host가 busy 루프에서 영원히 대기 | directed: 명령 발행 후 busy가 N 클럭 내 clear되는지 SVA |
| command-ready 소유권 혼동 | host와 controller가 동시에 토글 → 경쟁 | 상태 머신 transition coverage, illegal 전이 검출 |
| done이 set만 되고 clear 안 됨 | 다음 명령에서 즉시 done으로 오인 | clear-on-ack 동작 directed 확인 |
| stale status(2장) | 폴링 무한 루프 | DUT가 새 값 즉시 반영, uncached 가정 검증 |

### 5.4 인터럽트/폴링 모드 선택의 검증

DUT가 인터럽트 모드와 폴링 모드를 *둘 다* 지원한다면, 두 모드 모두에서 동일한 기능 결과가 나오는지 cross coverage로 확인해야 합니다 — 모드 × 부하(저/중/고) × 결과(정상/에러)의 조합이 비어 있으면 한 모드만 검증된 채 sign-off되는 escape가 생깁니다. coverage 설계·closure 전략은 [UVM Module 05](../../uvm/05_tlm_scoreboard_coverage/)의 cross/illegal_bins/closure 절을 따릅니다.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — '폴링은 항상 인터럽트보다 비효율적이다']
**실제**: 저부하·산발 이벤트에서는 인터럽트가 유리하지만, *초고율* 이벤트에서는 인터럽트가 스톰으로 무너지는 반면 폴링은 예측 가능한 비용을 유지합니다. 그래서 고율 경로(NAPI, NVMe busy-poll)는 의도적으로 폴링을 씁니다.<br>
**왜 헷갈리는가**: "인터럽트=발전, 폴링=구식"이라는 단순 서열화 때문에.
:::
:::danger[❓ 오해 2 — '폴링 주기는 짧을수록 좋다']
**실제**: 너무 짧으면 CPU를 통째로 태우고, 너무 길면 이벤트를 늦게/놓치게 됩니다. 폴링 사이클은 latency 요구와 CPU 예산 사이의 *조율* 대상입니다.<br>
**왜 헷갈리는가**: "자주 볼수록 빨리 안다"만 보고 비용을 무시해서.
:::
:::danger[❓ 오해 3 — '하이브리드는 인터럽트와 폴링을 그냥 둘 다 켜는 것이다']
**실제**: 하이브리드의 핵심은 *전환 규칙*입니다 — 인터럽트로 한 번 깨운 뒤 큐가 빌 때까지 폴링하고, 비면 다시 인터럽트 모드로. 둘을 동시에 켜면 중복 처리·경쟁이 납니다.<br>
**왜 헷갈리는가**: "결합"을 "동시 활성화"로 오해해서.
:::
:::danger[❓ 오해 4 — '검증은 레지스터 access만 맞으면 끝이다']
**실제**: 레지스터 access(RAL bit_bash 등)는 *프로그래밍 모델의 정적 검증*일 뿐, busy/command-ready 핸드셰이크나 인터럽트 deassert 같은 *순서·side-effect*는 드라이버 레벨 시나리오로 따로 검증해야 합니다.<br>
**왜 헷갈리는가**: "레지스터 다 읽고 썼으니 됐다"는 정적 시각 때문에.
:::

### DV 디버그 체크리스트 (이 장 내용으로 마주칠 첫 실패들)

| 증상 | 1차 의심 | 어디 보나 |
|------|----------|-----------|
| 폴링 시퀀스가 timeout으로 hang | busy/done 비트를 controller가 clear 안 함 | RTL status FSM, busy→clear SVA |
| 폴링 루프가 영원히 안 끝남 | status stale(MMIO cacheable, 2장) | 매핑 속성, DUT 즉시 반영 |
| 인터럽트 모드는 PASS, 폴링 모드는 FAIL | 두 모드가 다른 status 경로를 공유 안 함 | 모드별 status 갱신 로직, cross coverage 구멍 |
| 고부하 회귀에서만 mismatch | 인터럽트 스톰/큐 오버플로 미처리 | coalescing 로직, 큐 깊이, 하이브리드 전환 |
| 모드×부하 coverage가 안 참 | 한 모드만 자극 | 시나리오 시퀀스 추가, cross bin 분석 |

---

## 7. 핵심 정리 (Key Takeaways)

- **폴링 = status를 동기적으로 반복 샘플링**. busy-wait는 단순하지만 CPU 낭비. 2장 side-effect/uncached와 직결.
- **표준 핸드셰이크**: host(busy 폴링 → command → command-ready) ↔ controller(busy set → 실행 → ready/error/busy clear). 비트 소유권이 명확해야 deadlock 없음.
- **폴링 vs 인터럽트 = CPU↔latency trade-off**. 저부하는 인터럽트, 초고율은 폴링이 예측 가능.
- **하이브리드 = 인터럽트 후 임계 폴링**: 한 번 wake → 큐 빌 때까지 폴링(NAPI/NVMe). 스톰 완화와 같은 동기.
- **DV는 두 레벨**: 레지스터 레벨(RAL로 access/reset/side-effect 정적 검증) + 드라이버 레벨(핸드셰이크·순서·deassert를 directed seq + SVA + scoreboard로 검증). 모드×부하 cross로 closure.

:::caution[실무 주의점]
- 폴링 status는 *반드시* uncached 가정 + clear-on-read 두 번 읽기 금지(2장).
- busy/done의 set/clear 소유권을 SVA로 못박아 deadlock·경쟁을 잡는다.
- 인터럽트·폴링 *둘 다* 지원하면 두 모드를 cross coverage로 동등 검증 — 한 모드만 검증은 escape.
:::

### 7.1 자가 점검

:::tip[🤔 Q1 — 전략 선택 (Bloom: Evaluate)]
한 가속기가 마이크로초 단위로 완료 이벤트를 *폭주*시킨다. 순수 인터럽트 방식의 위험과, 더 나은 대안을 평가하라.
<details>
<summary>정답</summary>

순수 인터럽트는 **인터럽트 스톰** 위험이 큽니다 — 이벤트마다 ISR 진입/복귀 오버헤드가 누적되어 시스템이 인터럽트 처리만 하다 throughput이 붕괴합니다. 더 나은 대안은 **인터럽트 후 임계 폴링 하이브리드**: 첫 인터럽트로 드라이버를 한 번 깨운 뒤 completion 큐가 빌 때까지 폴링해 버스트 동안 추가 인터럽트를 막습니다(NAPI/NVMe busy-poll). 보조로 하드웨어 **interrupt coalescing**(N 이벤트/T μs까지 인터럽트 지연)도 함께 씁니다.

</details>
:::
:::tip[🤔 Q2 — 폴링 핸드셰이크 검증 설계 (Bloom: Design)]
DUT의 폴링 핸드셰이크(busy/command-ready/done)를 검증하는 시나리오를 설계하라. 어떤 자극과 어떤 체크가 필요한가?
<details>
<summary>정답</summary>

**자극(시퀀스)**: (1) busy가 0임을 확인 → (2) command/data-out 적재 → (3) command-ready set → (4) done까지 폴링. 그리고 busy 중에 host가 새 명령을 시도하는 *경쟁 시나리오*도 추가.
**체크**:
- SVA: command-ready set 후 N 클럭 내 controller가 busy set; 실행 후 done set + busy clear가 정해진 순서로.
- scoreboard: write 명령이면 data-out이 디바이스에 반영, read면 data-in이 올바른 값.
- side-effect(2장): done이 clear-on-ack인지, 두 번 읽어도 안전한지.
- coverage: 명령 방향(read/write) × 응답(정상/error) cross, busy-중-재시도 같은 transition/illegal bin.
이는 레지스터 레벨(RAL access)만으로는 못 잡는 *순서·핸드셰이크* 검증입니다.

</details>
:::

### 7.2 출처

**Internal (HDG)**
- `common/hw_sw_interaction_spec.md` §5 (Polling: 5.1~5.4), §4.7 (storm/coalescing)

**External**
- Wikipedia, *Polling (computer science)* (CC-BY-SA 4.0) — 정의, canonical 알고리즘, 변종, 폴링 vs 인터럽트
- Wikipedia, *Interrupt* (CC-BY-SA 4.0) — coalescing/RSS, 하이브리드 동기
- Corbet, Rubini, Kroah-Hartman, *Linux Device Drivers 3rd Ed.* Ch. 10 — top-half/bottom-half, NAPI 배경

---

## 다음 모듈

이 코스의 마지막 챕터입니다. 학습한 용어를 [용어집](../glossary/)에서 ISO 11179 정의로 다시 확인하고, [퀴즈 모음](../quiz/)으로 네 챕터의 이해도를 점검하세요. 검증 환경 조립으로 더 나아가려면 [UVM 코스](../../uvm/) — 특히 [RAL](../../uvm/07_register_layer_ral/)과 [TLM/Scoreboard/Coverage](../../uvm/05_tlm_scoreboard_coverage/) — 로 이어집니다.

[퀴즈 풀어보기 →](../quiz/04_polling_hybrid_dv_quiz/)
