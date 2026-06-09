---
title: "Module 01 — 왜 CPU DV는 어려운가"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** 프로세서 검증의 난이도가 상태 공간·파이프라인·예외·메모리 오더링의 네 축에서 어떻게 폭발하는지 설명할 수 있다.
- **Differentiate** directed test 만으로 PASS 를 본 코어와 실제로 검증된 코어가 왜 다른지 구분할 수 있다.
- **Classify** 한 CPU 버그가 상태 공간/파이프라인/예외/오더링 중 어느 축에서 비롯됐는지 분류할 수 있다.
- **Recall** simulation-based processor DV 의 5 단계와 각 단계가 어떤 신뢰도를 더하는지 나열할 수 있다.
- **Justify** 프로세서 검증이 reference model 기반 비교를 요구하는 이유를 무한 상태 공간 관점에서 정당화할 수 있다.
:::
:::note[사전 지식]
- [Computer Architecture M01–M03](../../computer_architecture/01_isa_riscv/) — ISA, 파이프라인/hazard, OoO/retirement, 예외
- [UVM M01](../../uvm/01_architecture_and_phase/) — 검증 환경의 기본 구조
- RISC-V 또는 ARM 명령 집합에 대한 기초 감각 (load/store/branch/CSR)
:::
---

## 1. Why care? — directed test 100개가 다 PASS 인데 코어가 틀렸다

### 1.1 시나리오 — "테스트 다 통과했는데 실리콘에서 죽었다"

신규 RISC-V 코어를 검증하는 팀이 컴파일러 회귀 테스트, 부트로더, 몇 개의 벤치마크를 directed test 로 돌려 모두 PASS 를 받았습니다. 자신감을 갖고 tape-out 했는데, 실리콘에서 특정 OS 커널이 간헐적으로 죽습니다. 추적해 보니 원인은 이랬습니다.

```asm
# 두 명령이 같은 레지스터를 연달아 건드린다 (RAW + WAR 가 겹치는 경로)
lw    x5, 0(x10)      # x5 = mem[x10]  — load-use
add   x6, x5, x7      # x5 를 즉시 사용 (load-use hazard)
csrrw x0, mstatus, x6 # 그 결과를 CSR 에 write — privilege side-effect
```

이 세 명령이 _특정 파이프라인 정렬_ 로 겹치면서, load-use forwarding 이 한 사이클 어긋난 값을 CSR 에 쓰는 버그였습니다. directed test 들은 이 명령 _조합_ 과 _타이밍_ 을 우연히도 한 번도 만들지 않았습니다. 명령 자체는 각각 수천 번 실행됐지만, "load 직후 그 값을 CSR 에 쓰는, 그것도 특정 stall 정렬에서" 라는 _조합_ 이 빠졌던 것입니다.

이것이 프로세서 검증의 본질입니다. CPU 의 버그는 명령 하나에 있는 경우보다 **명령들의 조합과 마이크로아키텍처 상태의 조합**에 숨어 있는 경우가 압도적입니다. directed test 는 그 조합 공간의 극히 일부만 의도적으로 짚을 수 있을 뿐입니다.

### 1.2 그래서 무엇이 필요한가

이 모듈을 건너뛰면 "테스트가 PASS 했으니 됐다"는 위험한 자신감에 빠집니다. CPU DV 가 요구하는 것은 두 가지입니다. 첫째, 무한에 가까운 상태 공간을 _효율적으로_ 훑는 자극(제약 랜덤 + 코너 케이스 타겟). 둘째, 그 많은 자극의 결과를 사람이 일일이 채점할 수 없으므로 _자동 채점관_ — ISA 를 정확히 구현한 reference model 과의 비교. 이 두 가지가 이후 모듈 전체의 뼈대입니다.

---

## 2. Intuition — 네 개의 무한 + 한 장 그림

:::tip[💡 한 줄 비유]
**CPU 검증** ≈ **네 개의 손잡이가 달린 자물쇠를 푸는 일**.<br>
각 손잡이(상태 공간, 파이프라인 정렬, 예외 타이밍, 메모리 오더링)는 거의 무한한 위치를 가지고, 버그는 _네 손잡이의 특정 조합_ 에서만 열립니다. directed test 는 손잡이를 손으로 몇 개 위치에 맞춰 보는 것이고, 제약 랜덤 + reference model 은 손잡이를 빠르게 돌리며 _열렸는지 자동으로 확인_ 하는 것입니다.
:::

### 한 장 그림 — 난이도를 만드는 네 축

```d2
direction: down

CPU: "**CPU DV 난이도**\n= 네 축의 곱(조합)"

SS: "**① 상태 공간**\nPC × 32 레지스터 × CSR × 메모리\n→ 사실상 무한"
PIPE: "**② 파이프라인 정렬**\nstall / forward / flush 의\n타이밍 조합"
EXC: "**③ 예외 / 인터럽트**\n임의 명령 경계에서 발생\n→ precise 복구 필요"
ORD: "**④ 메모리 오더링**\nload/store 재정렬,\n멀티코어 일관성"

CPU -> SS
CPU -> PIPE
CPU -> EXC
CPU -> ORD

SS -> BUG: "조합"
PIPE -> BUG
EXC -> BUG
ORD -> BUG: "조합"
BUG: "**버그는 네 축의\n특정 _조합_ 에 숨는다**\n→ directed 로는 못 닿음"
```

### 왜 이 네 축인가 — Design rationale

프로세서가 다른 DUT 보다 어려운 이유는 이 네 축이 _서로 곱해지기_ 때문입니다.

1. **상태 공간이 곱셈으로 폭발한다** → PC, 32 개 레지스터, 수십 개 CSR, 메모리가 각각 독립적으로 변하므로 상태 수는 곱으로 늘어납니다. directed 로 의미 있는 점들을 다 짚는 것은 불가능 → 제약 랜덤 + coverage 가 필요.
2. **같은 명령도 파이프라인 정렬에 따라 다른 버그를 깨운다** → 명령 자체는 맞아도 forwarding/stall 의 특정 조합에서만 틀릴 수 있음 → 단순 ISA 모델만으로는 부족, 타이밍을 흔드는 자극 필요.
3. **예외는 임의 경계에서 터진다** → 어느 명령에서든 page fault·illegal instruction·인터럽트가 가능하고, precise exception 을 위해 추측 실행을 정확히 되돌려야 함 → 예외 주입 자극 + reference model 의 동일 예외 산출 필요.
4. **메모리 오더링은 정답이 여럿이다** → load/store 재정렬이 합법인 경우가 많아, "틀린 순서"와 "허용된 재정렬"을 구분하려면 ISA 의 메모리 모델을 아는 reference 가 필요.

이 네 요구가 곧 **"제약 랜덤 자극 + reference model 비교 + ISA coverage"** 라는 CPU DV 의 표준 구조의 근거입니다.

---

## 3. 작은 예 — 같은 명령, 다른 정렬, 다른 결과

가장 단순한 시나리오로 "왜 directed 로는 못 닿는가"를 봅시다. load-use hazard 한 가지가 파이프라인 정렬에 따라 어떻게 다른 경로를 타는지입니다.

### 단계별 다이어그램

```d2
direction: right

A: "**Case A — 간격 있음**\nlw x5,..\nnop\nadd x6,x5,..\n→ forward 불필요\n(정상 경로)"
B: "**Case B — 인접**\nlw x5,..\nadd x6,x5,..\n→ load-use forward\n(1-bubble 경로)"
C: "**Case C — 인접 + stall**\n(앞단 stall 으로\n정렬이 한 칸 밀림)\n→ forward 타이밍 코너"

A -> RESULT: "PASS"
B -> RESULT: "PASS"
C -> RESULT: "여기서 버그가\n깨어날 수 있음" { style.stroke: "#c0392b" }
RESULT: "같은 두 명령,\n다른 마이크로아키텍처 정렬"
```

### 단계별 의미

| Case | 자극 | 활성화되는 마이크로아키텍처 경로 | directed 로 닿나? |
|---|---|---|---|
| A | lw, nop, add | forwarding 불필요 (값이 이미 WB) | 쉽게 닿음 |
| B | lw, add (인접) | load-use forwarding + 1 bubble | 의도하면 닿음 |
| C | lw, add (인접) + 앞단 stall | forwarding 이 stall 과 겹치는 _드문_ 정렬 | 거의 못 닿음 — 우연 필요 |

핵심: **세 케이스의 명령은 거의 같지만, 코어 내부에서 타는 경로가 다릅니다.** Case C 의 정렬은 앞쪽 명령의 cache miss·structural hazard 등 _다른 명령_ 에 의해 만들어지므로, 그것을 directed 로 재현하려면 사실상 전체 파이프라인 상태를 손으로 맞춰야 합니다. 제약 랜덤이 다양한 앞단 명령을 섞어 돌리면 이런 정렬이 _확률적으로_ 발생합니다.

### 채점은 누가? — reference model

Case A/B/C 모두에서 "결과가 맞는가"를 사람이 판단할 수는 없습니다. 그래서 ISA 를 정확히 구현한 reference model(ISS) 이 같은 명령 스트림을 실행해 expected architectural state 를 산출하고, 코어의 결과와 retire 시점에 비교합니다. 이 메커니즘이 [Module 02 의 step-and-compare](../02_step_and_compare/) 입니다.

```c
// 개념적 pseudo code — reference model 이 채점관 역할
// (실제 구현은 Spike 같은 ISS 를 DPI-C 로 연동; Module 04 참조)
while (rtl_core.has_retired_instruction()) {
    retire_t rtl = rtl_core.get_retired();   // RTL 이 retire 한 명령 + 상태변화
    iss.step();                              // reference model 한 스텝 진행
    if (rtl.arch_state != iss.arch_state())  // architectural state 비교
        flag_divergence(rtl);                // 첫 불일치 = 버그 후보
}
```

---

## 4. 일반화 — simulation-based processor DV 의 5 단계

프로세서 검증은 보통 신뢰도가 점증하는 다섯 단계로 구성됩니다. 각 단계는 앞 단계가 닿지 못한 상태 공간을 추가로 메웁니다.

```d2
direction: down

L1: "**Level 1 — Sanity / Bring-up**\n부팅, 단순 명령 directed\n→ 기본 데이터패스 살아있나"
L2: "**Level 2 — Directed ISA test**\n명령별 기능 directed\n→ 각 명령이 단독으로 맞나"
L3: "**Level 3 — Constrained Random**\nriscv-dv 등으로 명령 stream 랜덤\n→ 조합/정렬 코너 케이스"
L4: "**Level 4 — Step-and-Compare**\nreference model 과 retire 비교\n→ 모든 명령의 architectural 정합"
L5: "**Level 5 — Coverage + Formal**\nISA coverage closure + riscv-formal\n→ 닿지 못한 상태까지 증명/측정"

L1 -> L2 -> L3 -> L4 -> L5
```

| Level | 기법 | 더해 주는 신뢰도 | 본 코스 연결 |
|---|---|---|---|
| 1 | Sanity / bring-up | 데이터패스·부팅이 산다 | — |
| 2 | Directed ISA test | 각 명령이 단독으로 맞다 | M01 |
| 3 | Constrained random | 명령 조합·파이프라인 정렬 코너 | [M05](../05_riscv_dv_stimulus/) |
| 4 | Step-and-compare | 모든 명령의 architectural 정합 | [M02](../02_step_and_compare/) · [M04](../04_uvm_core_env/) |
| 5 | Coverage + formal | 미도달 상태의 측정·증명 | [M06](../06_riscv_formal/) · [M07](../07_coverage_special_areas/) |

이 5 단계 모델은 RISC-V 도구 생태계를 배경으로 자주 인용되지만, **ARM·MIPS·x86 코어에도 그대로 적용됩니다.** ISS 의 이름(Spike vs ARM Fast Models 등)과 자극 generator 만 달라질 뿐, "directed → constrained random → reference model lockstep → coverage/formal" 의 골격은 동일합니다.

---

## 5. 디테일 — 네 축이 만드는 구체적 버그 유형

### 5.1 상태 공간 — 왜 "곱"인가

architectural state 는 PC, x0–x31, 구현된 CSR, 그리고 메모리입니다. 이들이 _독립적으로_ 변하므로 가능한 상태 수는 더해지는 게 아니라 곱해집니다. 32 비트 레지스터 32 개만 따져도 이미 $2^{32 \times 32}$ 라는 천문학적 수이고, 여기에 CSR·메모리·파이프라인 상태가 곱해집니다. directed test 가 짚을 수 있는 점의 수는 이에 비하면 0 에 수렴합니다. 그래서 "특정 점을 짚는" directed 가 아니라 "넓게 뿌리고 채워진 영역을 측정하는" 제약 랜덤 + coverage 로 전환할 수밖에 없습니다.

하지만 이 천문학적 수가 곧 "검증 불가능"을 뜻하지는 않습니다. 핵심은 **그 상태의 절대다수가 reachable 하지 않다**는 점입니다 — 예컨대 임의의 비트 패턴 $2^{32\times32}$ 중 실제 프로그램이 도달하는 레지스터 조합은 극히 일부이고, 도달 불가능한 상태에 버그가 있어도 그것은 영원히 발현되지 않습니다. 그래서 검증은 _전체_ 상태가 아니라 _reachable_ 상태에만 집중하면 됩니다. 여기서 두 가지 추상화(abstraction) 기법이 상태 공간을 더 줄입니다. 첫째 **symmetry**: "레지스터 x5 에서 나는 forwarding 버그"는 x6, x7 에서도 같은 메커니즘이므로, 32 개 레지스터를 일일이가 아니라 _대표 몇 개_ 만 짚어도 같은 버그 부류를 덮습니다(coverage 모델이 레지스터 인덱스를 개별 bin 이 아닌 그룹으로 묶는 근거). 둘째 **data abstraction**: 32-bit 값 전체가 아니라 "0 / 최대값 / 부호 경계 / 임의" 같은 _동치류(equivalence class)_ 로 축약하면 의미 있는 자극만 남습니다. 이 "reachable 만, 대칭은 묶어서, 값은 동치류로" 라는 사고가 formal 검증(M06)이 무한 상태를 다루는 출발점이기도 합니다 — formal 은 명시적으로 reachable 집합을 invariant 로 좁혀 증명합니다.

### 5.2 파이프라인 정렬 — 같은 명령, 숨은 경로

데이터패스가 맞아도 hazard 처리(forwarding, stall, flush)의 _타이밍 조합_ 에서 버그가 납니다. load-use bubble, branch misprediction flush 직후의 forwarding, structural hazard 로 인한 stall 이 다른 명령과 겹치는 경우 등은 _앞뒤 명령의 종류와 간격_ 이 만듭니다. 그래서 자극은 명령 _종류_ 만이 아니라 명령 _사이의 간격·의존성_ 까지 랜덤화해야 합니다 (M05 의 dependency 제약).

### 5.3 예외 / 인터럽트 — 임의 경계의 precise 복구

예외(illegal instruction, misaligned access, page fault)와 비동기 인터럽트는 _어느 명령 경계에서든_ 발생할 수 있습니다. 코어는 [precise exception](../../computer_architecture/03_ooo_branch_prediction/) 을 보장해야 하므로, 예외 시점 이전 명령은 모두 commit 되고 이후 추측 실행은 모두 폐기되며 CSR(mepc/mcause/mstatus) 이 정확히 갱신돼야 합니다. 이 복구가 _특정 명령이 파이프라인의 특정 단계에 있을 때_ 인터럽트가 들어오는 경우에 깨지기 쉽습니다. reference model 은 같은 시점에 같은 예외를 산출해야 비교가 성립하므로, 인터럽트 타이밍을 RTL 과 ISS 가 _합의_ 하는 메커니즘이 필요합니다 (M04).

### 5.4 메모리 오더링 — "틀림"과 "허용된 재정렬"의 구분

ISA 의 메모리 일관성 모델(RISC-V 의 RVWMO, ARM 의 weak ordering)은 load/store 재정렬을 상당 부분 _허용_ 합니다. 따라서 관찰된 순서가 프로그램 순서와 다르다고 해서 버그가 아닙니다. scoreboard 는 ISA 메모리 모델이 허용하는 순서 집합과 비교해야 하며, 단순 in-order 비교를 쓰면 정상 동작을 false fail 로 잡습니다. 이는 [UVM M05 의 out-of-order scoreboard](../../uvm/05_tlm_scoreboard_coverage/) 와 같은 사고방식입니다 — 순서가 여러 개 정답일 수 있는 DUT 의 비교 전략.

### 5.5 채점관(ISS)과 측정자(coverage)의 종류

위 네 축을 다루는 두 도구 — reference model 과 coverage — 는 사실 _한 종류_ 가 아닙니다. 어느 종류를 쓰느냐가 무엇을 잡고 무엇을 놓치는지를 가릅니다.

**reference model(ISS)의 정확도 등급.** "ISS" 라고 통칭하지만 실제로는 모델링 범위가 다릅니다.

| 종류 | 모델링 범위 | step-and-compare 에서의 역할 |
|---|---|---|
| **functional / architectural ISS** (예: Spike) | ISA 의미만 — 명령이 architectural state 를 어떻게 바꾸는가. 사이클·파이프라인은 모름 | retire 단위 architectural 비교에 _충분_. step-and-compare 의 표준 |
| **cycle-approximate / cycle-accurate model** | 위 + 타이밍(몇 사이클, stall 횟수)까지 근사/정확 모델링 | 성능 검증·타이밍 회귀용. 느리고 코어별 튜닝 필요 |

step-and-compare(M02)가 functional ISS 로 _충분_ 한 이유는, 비교 단위가 사이클이 아니라 **retire 라는 논리적 사건**이기 때문입니다(오해 3 참조). RTL 이 명령을 몇 사이클에 끝냈든, retire 시점의 architectural state 만 맞으면 됩니다 — 타이밍은 ISS 가 아니라 SVA·coverage·waveform 의 몫입니다. 그래서 느리고 코어 의존적인 cycle-accurate 모델은 step-and-compare 의 _채점관_ 으로는 과합니다.

**coverage 의 종류.** "ISA coverage" 한 단어 뒤에는 성격이 다른 두 부류가 있습니다.

- **code coverage** — RTL 코드 _자체_ 가 얼마나 실행됐나: line, toggle(각 신호가 0↔1 둘 다 됐나), FSM state/transition, branch. _자동 추출_ 되며 "건드리지도 않은 로직"을 드러냅니다.
- **functional coverage** — 설계 _의도_ 가 검증됐나: 사람이 작성한 covergroup(opcode × privilege × hazard 같은 cross). _자동이 아니므로_ 빠진 시나리오는 측정조차 안 됩니다.

이 둘의 분업이 "code coverage 90% 인데 버그"의 정체를 가릅니다. code coverage 100% 는 "모든 줄이 한 번씩 실행됐다"일 뿐, _어떤 조합_ 에서 실행됐는지는 말하지 않습니다 — load-use forwarding 로직이 실행은 됐지만(line covered) "stall 과 겹친 정렬"(functional cross)에서는 한 번도 안 탔을 수 있습니다. 그래서 두 종류를 모두 닫아야 하며, 특히 functional cross bin 이 조합 공간 도달의 진짜 지표입니다(M07).

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'directed test 가 전부 PASS 면 코어는 검증됐다']
**실제**: directed test 는 의도한 명령·시나리오만 짚습니다. CPU 버그의 다수는 _명령 조합 × 파이프라인 정렬 × 예외 타이밍_ 의 곱 공간에 숨어 있어, directed 가 그 조합을 우연히 만들지 않으면 silent 하게 통과합니다.<br>
**왜 헷갈리는가**: "모든 명령을 테스트했다 = 모든 경우를 테스트했다" 로 착각하기 때문 — 명령 단위 커버리지와 조합 커버리지는 전혀 다릅니다.
:::
:::danger[❓ 오해 2 — '코어 결과는 execution 순서대로 비교하면 된다']
**실제**: OoO 코어는 명령을 순서 없이 execute 하지만 architectural state 는 **retire(commit) 시점에 in-order 로** 확정됩니다. 비교는 반드시 retire 단위로, 프로그램 순서로 해야 합니다. execution 시점 값을 비교하면 추측 실행·되돌릴 값까지 보게 되어 무수한 false mismatch 가 납니다.<br>
**왜 헷갈리는가**: "실행 = 결과 확정" 이라는 in-order 멘탈 모델 때문 — OoO 에서는 둘이 분리됩니다.
:::
:::danger[❓ 오해 3 — 'reference model(ISS) 이 타이밍까지 맞춰 준다']
**실제**: ISS 는 ISA _의미_ 만 모델링합니다 — 명령이 몇 사이클 걸렸는지, stall 이 몇 번 났는지는 모릅니다. 그래서 비교는 사이클이 아니라 _retire 라는 논리적 사건_ 단위로 합니다. 타이밍 정합은 ISS 가 아니라 SVA·coverage·waveform 의 몫입니다.<br>
**왜 헷갈리는가**: "골든 모델이니 모든 걸 안다" 고 기대하기 때문 — ISS 는 architectural 정합만 보장합니다.
:::
:::danger[❓ 오해 4 — '메모리 접근 순서가 프로그램과 다르면 버그다']
**실제**: ISA 메모리 모델이 재정렬을 허용하는 경우가 많아, 다른 순서가 곧 버그는 아닙니다. 합법적 재정렬 집합 안에 있으면 PASS 여야 합니다. 단순 in-order 비교는 정상 재정렬을 false fail 로 만듭니다.<br>
**왜 헷갈리는가**: 단일코어·강한 순서 모델의 직관을 약한 메모리 모델에 그대로 적용하기 때문.
:::

### DV 디버그 체크리스트 (이 모듈 내용으로 마주칠 첫 의문들)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| directed 다 PASS 인데 실리콘/long-run 에서만 실패 | 조합/정렬 코너 미커버 | constrained random + ISA coverage 리포트의 cross bin |
| 비교가 명령마다 mismatch (전부 틀림) | execution 시점 비교 또는 retire 정렬 어긋남 | 비교를 retire 시점·프로그램 순서로 하는지 |
| 예외 후부터 모든 명령 mismatch | precise exception 복구 또는 CSR 갱신 불일치 | mepc/mcause/mstatus, 예외 시점 RTL↔ISS 합의 |
| 멀티코어/약한 모델에서 산발적 false fail | scoreboard 가 in-order 비교 | ISA 메모리 모델 허용 순서로 비교하는지 |
| coverage 90%+ 인데 새 버그 계속 | coverage 모델이 조합(cross)을 안 봄 | covergroup 에 opcode×privilege×hazard cross 존재 여부 |

---

## 7. 핵심 정리 (Key Takeaways)

- **CPU DV 난이도 = 네 축의 곱**: 상태 공간, 파이프라인 정렬, 예외 타이밍, 메모리 오더링. 버그는 단일 축이 아니라 _조합_ 에 숨는다.
- **directed test PASS ≠ 검증 완료**: 명령 단위 커버리지와 조합 커버리지는 전혀 다르다. 무한 상태 공간은 제약 랜덤 + coverage 로 메운다.
- **채점관은 reference model(ISS)**: 사람이 결과를 일일이 채점할 수 없으므로 ISA 를 정확히 구현한 모델과 비교한다.
- **비교는 retire(commit) 시점·프로그램 순서**: OoO 라도 architectural state 는 retire 에서 in-order 로 확정된다. ISS 는 architectural 의미만 보장하고 타이밍은 모른다.
- **simulation-based DV 5 단계**: sanity → directed → constrained random → step-and-compare → coverage/formal. 각 단계가 앞이 못 닿은 상태를 메운다.
- **RISC-V 는 예제일 뿐**: 방법론(reference-model lockstep, retire monitor, ISA coverage)은 ARM 등 모든 ISA 에 동일하게 적용된다.

:::caution[실무 주의점]
- "테스트가 PASS" 와 "상태 공간이 커버됨" 을 혼동하지 말 것 — 커버리지 리포트의 _cross bin_ 으로 조합 도달을 확인.
- 비교 정렬은 항상 _retire 시점_. execution 시점 값을 보면 false mismatch 폭발.
- 메모리 오더링 비교는 ISA 모델의 허용 순서 집합과 — 단순 in-order 비교 금지.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — directed vs 조합 (Bloom: Analyze)]
모든 RISC-V 정수 명령을 각각 100 번씩 directed 로 실행해 전부 PASS 했다. 그럼에도 놓칠 수 있는 버그의 _부류_ 를 한 가지 들고, 왜 directed 로 못 잡는지 설명하라.
<details>
<summary>정답</summary>

**명령 _조합·정렬_ 버그** (예: load-use forwarding 이 앞단 stall 과 특정하게 겹치는 정렬에서만 어긋나는 값).
- 각 명령을 단독으로 100 번 실행해도, 그 명령이 _다른 특정 명령과 특정 간격·의존성으로 인접_ 한 상황은 만들어지지 않을 수 있음.
- directed 는 "명령 X 를 실행한다"는 의도는 표현하지만 "명령 X 가 명령 Y 뒤 1 사이클, 그것도 앞단 cache miss stall 정렬에서" 라는 마이크로아키텍처 조합을 의도적으로 만들기는 사실상 불가능.
- 대응: 명령 _간격·의존성_ 을 랜덤화하는 제약 랜덤(M05) + 조합을 측정하는 cross coverage(M07).

</details>
:::
:::tip[🤔 Q2 — retire 시점 비교 (Bloom: Evaluate)]
어떤 팀이 OoO 코어를 검증하며 "명령이 execute unit 에서 결과를 낸 시점"에 RTL 값과 ISS 값을 비교하도록 scoreboard 를 짰다. 이 설계의 문제와 올바른 비교 시점을 평가하라.
<details>
<summary>정답</summary>

**문제: execution 시점에는 추측 실행·되돌릴 값이 섞여 있어 비교가 무의미하다.**
- OoO 는 분기 추측·메모리 추측으로 _나중에 폐기될 수도 있는_ 결과를 execute 단계에서 만든다. ISS 는 추측을 하지 않으므로 이 시점 값들은 구조적으로 어긋난다 → false mismatch 폭발.
- architectural state 는 **retire(commit) 시점에 프로그램 순서로** 확정된다. 따라서 비교도 retire 시점·in-order 로 해야 RTL 과 ISS 가 같은 의미의 상태를 비교하게 된다.
- 올바른 설계: retire monitor 가 retire 사건마다 architectural 변화를 샘플 → 그 순간에 ISS 를 한 스텝 진행시켜 비교 (M02 step-and-compare).

</details>
:::
### 7.2 출처

**Internal**
- [Computer Architecture M03 — OoO & 분기 예측](../../computer_architecture/03_ooo_branch_prediction/) — retirement·precise exception 의 1차 원리
- [UVM M05 — TLM/Scoreboard/Coverage](../../uvm/05_tlm_scoreboard_coverage/) — out-of-order 비교 전략

**External**
- *RISC-V Verification: The 5 Levels of Simulation-Based Processor Hardware DV* — SemiEngineering (semiengineering.com)
- *The RISC-V Instruction Set Manual, Volume II: Privileged Architecture* — 예외·CSR·privilege 모델 (외부 표준 지식)
- OpenHW CORE-V `core-v-verif` 환경 문서 — docs.openhwgroup.org

---

## 다음 모듈

→ [Module 02 — Step-and-Compare Lockstep](../02_step_and_compare/): 무한 상태 공간을 _자동으로 채점_ 하는 핵심 메커니즘 — reference model 과 RTL 을 retire 시점에 나란히 비교해 첫 divergence 를 잡는다.

[퀴즈 풀어보기 →](../quiz/01_why_cpu_dv_quiz/)
