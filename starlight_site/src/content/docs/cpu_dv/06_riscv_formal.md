---
title: "Module 06 — Formal Processor Verification (riscv-formal)"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** 시뮬레이션이 "많은 프로그램을 돌려본다"면 formal 은 "모든 가능한 입력에 대해 증명한다"는 근본 차이를, 그리고 이 차이가 CPU 검증에서 왜 중요한지 설명할 수 있다.
- **Describe** RVFI(RISC-V Formal Interface)가 코어에서 무엇을 노출하며, riscv-formal 이 그 신호로 어떻게 명령별 properties 를 검사하는지 기술할 수 있다.
- **Differentiate** bounded model checking 의 "k 사이클 내 반례 탐색"과 시뮬레이션의 "특정 자극 실행"이 보장하는 것의 차이를 구분할 수 있다.
- **Analyze** riscv-formal 의 명령별 formal model(ISA spec 인코딩)을 코어의 RVFI 출력과 대조하는 검사 구조를 분석할 수 있다.
- **Evaluate** 주어진 검증 목표에 대해 formal 과 simulation 중 어느 것이 적합한지, 둘을 어떻게 상보적으로 쓸지 평가할 수 있다.
:::
:::note[사전 지식]
- [M02 Step-and-Compare](../02_step_and_compare/), [M03 RVFI/RVVI](../03_rvfi_rvvi/), [M05 제약 랜덤 자극](../05_riscv_dv_stimulus/)
- formal 기본·SVA — [Formal Verification M01 Fundamentals](../../formal_verification/01_formal_fundamentals/), [M02 SVA](../../formal_verification/02_sva/)
- ISA 기본 — [Computer Architecture M01 ISA](../../computer_architecture/01_isa_riscv/)
:::
---

## 1. Why care? — 시뮬레이션은 "본 것"만 보장한다

### 1.1 시나리오 — 깊은 corner 가 시뮬레이션을 빠져나간다

[M05](../05_riscv_dv_stimulus/)에서 제약 랜덤 ISG 로 수천 시드를 돌렸다고 합시다. coverage 는 95% 를 넘었고 step-and-compare 도 깨끗합니다. 그런데 실리콘에서 다음 같은 버그가 남았습니다.

> `ADD` 의 결과가 destination 레지스터가 `x0` 일 때 — RISC-V 에서 `x0` 는 항상 0 이어야 하는데, 특정 forwarding 경로에서 `x0` 에 쓴 값이 _바로 다음_ 명령에 forward 되어 0 이 아닌 값으로 읽혔다.

이 버그가 발현하려면 (a) destination 이 `x0` 이고 (b) 다음 명령이 즉시 `x0` 를 읽으며 (c) 특정 forwarding muxing 조건이 맞아야 합니다. 제약 랜덤이 이 _세 조건의 동시 발생_ 을 시드 다양성만으로 만들 확률은 극히 낮습니다. 시뮬레이션은 _실제로 실행한 자극_ 에 대해서만 정답을 보장합니다 — 실행하지 않은 입력 조합은 보장 밖입니다.

### 1.2 해법 — "모든 입력"을 수학으로 덮는다

Formal verification 은 자극을 _실행_ 하지 않습니다. 대신 코어의 동작을 수학적 모델로 보고, "이런 property 를 위반하는 입력 시퀀스가 존재하는가?"를 _솔버_ 가 탐색합니다. 위반 시퀀스가 없으면 그 property 는 _증명_ 됩니다. 있으면 솔버가 _최소 반례_(counterexample) 파형을 내놓습니다.

```
시뮬레이션:  특정 프로그램 실행 → 그 실행에 대해 PASS/FAIL
Formal:      property 정의 → "위반 입력 존재?" 솔버 탐색 → 증명 or 반례
```

`riscv-formal`(YosysHQ)은 이 접근을 RISC-V 코어에 특화한 오픈 프레임워크입니다. RVFI 라는 검증 인터페이스로 코어가 _retire 한 명령의 정보_ 를 노출하면, riscv-formal 은 ISA spec 을 인코딩한 properties 로 그 정보를 _모든 도달 가능한 상태_ 에 대해 검사합니다.(외부 표준 지식)

이 모듈을 건너뛰면 CPU 검증은 "본 것만 보장"하는 시뮬레이션에만 의존하게 되고, 위 `x0` forwarding 같은 _확률적으로 거의 안 나오는_ 코너가 영원히 escape 할 수 있습니다.

:::note[RISC-V 를 예로 들지만 방법론은 ISA 중립]
RVFI·riscv-formal 은 RISC-V 생태계 도구입니다. 그러나 "코어가 retire 정보를 검증 인터페이스로 노출 → formal property 로 모든 입력을 증명"이라는 방법론은 ARM 등 다른 ISA 코어에도 동일하게 적용됩니다. 상용 영역에는 ARM 코어용 formal 자산이 존재합니다.(외부 표준 지식)
:::

---

## 2. Intuition — 한 줄 비유, 한 장 그림

:::tip[💡 한 줄 비유]
**Simulation** ≈ **표본 조사**, **Formal** ≈ **전수 증명**.<br>
시뮬레이션은 모집단(모든 가능한 명령 시퀀스)에서 _표본_(실행한 프로그램)을 뽑아 검사합니다 — 표본에 없으면 못 봅니다. Formal 은 "이 property 를 위반하는 표본이 모집단 어딘가에 있는가?"를 솔버가 _전수 탐색_ 합니다 — 없으면 증명, 있으면 그 한 표본을 콕 집어 보여줍니다.
:::

### 한 장 그림 — riscv-formal 의 검사 구조

```d2
direction: right

CORE: "**RTL CPU Core**\n(DUT)" {
  RVFI: "**RVFI 출력**\nrvfi_valid\nrvfi_insn / rvfi_pc\nrvfi_rd_addr/wdata\nrvfi_mem_*"
}
SPEC: "**ISA Formal Model**\n(명령별 spec 인코딩)\n예: ADD 결과 = rs1+rs2"
CHK: "**Check (assertion)**\nRVFI 출력 == spec 결과?\n(insn_check, pc_fwd, reg, ...)"
SOLVER: "**SMT Solver**\n(Yosys/SymbiYosys)\nbounded model check"
RESULT: "**결과**\nPASS(증명)\nor 반례 trace(VCD)"

CORE -> CHK: "retire 정보"
SPEC -> CHK: "기대값"
CHK -> SOLVER: "property"
SOLVER -> RESULT
```

### 왜 이 구조인가 — Design rationale

세 가지 요구의 교집합입니다.

1. **코어 내부 구조에 독립적으로 검사해야 한다** → RVFI 라는 _표준화된 retire 인터페이스_ 만 보면 됨. 파이프라인 깊이·forwarding 방식이 달라도 RVFI 가 같으면 같은 properties 를 재사용.
2. **"정답"은 ISA spec 이어야 한다** → 명령별 formal model 이 ISA 사양(예: `ADD rd = rs1+rs2`)을 인코딩. 코어의 RVFI 출력을 이 spec 과 대조.
3. **모든 입력을 덮어야 한다** → 시뮬레이션처럼 자극을 실행하는 게 아니라, 솔버가 k 사이클 내 _위반 가능한 입력 시퀀스_ 를 탐색(bounded model checking). 없으면 그 깊이까지 증명.

---

## 3. 작은 예 — `ADD` 명령 하나를 formal 로 검사하기

가장 단순한 property 하나로 흐름을 봅시다: "코어가 `ADD` 를 retire 하면, 기록된 결과는 두 source 의 합이어야 한다."

### 단계별 다이어그램

```d2
direction: down

S1: "**① RVFI 관찰**\nrvfi_valid=1\nrvfi_insn=ADD x3,x1,x2\nrvfi_rs1_rdata / rs2_rdata\nrvfi_rd_wdata"
S2: "**② spec 계산**\nexpected = rs1_rdata + rs2_rdata\n(ISA model 이 정의)"
S3: "**③ assertion**\nassert(rvfi_rd_wdata == expected)\n(단, rd != x0)"
S4: "**④ 솔버 탐색**\nk 사이클 내 위반 입력 존재?\n없음 → 증명\n있음 → 반례 VCD"
S1 -> S2 -> S3 -> S4
```

### 단계별 의미

| Step | 누가 | 무엇을 | 왜 |
|------|------|--------|-----|
| ① | RVFI | 코어가 retire 한 ADD 의 source/dest 값을 노출 | 내부 구조 무관하게 "무엇이 retire 됐나"만 본다 |
| ② | ISA formal model | `rs1+rs2` 라는 _기대 결과_ 계산 | 정답은 코어가 아니라 spec 이 정의 |
| ③ | assertion | `rvfi_rd_wdata == expected` (단 `rd==x0` 이면 결과 0) | spec 과 실제의 동치를 property 로 표현 |
| ④ | SMT 솔버 | 이 assertion 을 깨는 입력 시퀀스를 k 사이클 내 탐색 | 표본이 아니라 _전수_(bounded) 탐색 |

이 한 property 만으로도 1.1 의 `x0` forwarding 버그가 잡힙니다: `rd==x0` 인 ADD 의 결과가 다음 명령에서 0 이 아닌 값으로 보이는 입력 시퀀스를, 솔버가 _존재한다_ 고 찾아내 반례 파형을 내놓습니다. 시뮬레이션이 우연히 마주치길 기다릴 필요가 없습니다.

### property 의 형태 (개념 SVA)

riscv-formal 은 명령별 check 를 SystemVerilog assertion 으로 표현합니다. 아래는 _개념적_ 형태입니다(실제 매크로/신호명은 riscv-formal repo 의 `insns/` 모델 참조 — (외부 표준 지식)).

```systemverilog
// 개념 예시 — ADD 명령 formal check (실제 신호명은 riscv-formal 정의 따름)
// RVFI 가 valid 한 사이클에, 디코드된 명령이 ADD 이면
property add_correct;
  @(posedge clk) disable iff (!resetn)
  (rvfi_valid && is_add(rvfi_insn)) |->
    // x0 는 항상 0, 그 외엔 합
    (rvfi_rd_addr == 0) ? (rvfi_rd_wdata == 0)
                        : (rvfi_rd_wdata == (rvfi_rs1_rdata + rvfi_rs2_rdata));
endproperty
assert property (add_correct);
```

:::note[여기서 잡아야 할 두 가지]
**(1) 검사 대상은 코어 내부가 아니라 _RVFI 출력_ 이다.** 파이프라인이 몇 단이든, forwarding 을 어떻게 하든, "retire 된 ADD 의 결과가 spec 과 같은가"만 본다. 그래서 같은 property 가 여러 코어에 재사용된다.<br>
**(2) "증명"은 _bounded_ 다.** 솔버는 보통 k 사이클(예: 20~30) 깊이까지 위반을 탐색한다. k 내에 반례가 없으면 _그 깊이까지_ 증명된 것 — 무한 깊이 증명(unbounded)은 별도 기법(induction)이 필요하다. 이 한계를 아는 것이 formal 을 올바로 쓰는 핵심이다.
:::

---

## 4. 일반화 — RVFI, riscv-formal 의 check 종류, BMC 의 의미

### 4.1 RVFI — 코어가 노출하는 retire 정보

RVFI 는 코어가 _명령을 retire 할 때마다_ 그 명령의 architectural 정보를 한 묶음으로 내보내는 인터페이스입니다.(외부 표준 지식) 대표 채널은 다음과 같습니다.

| RVFI 채널(개념) | 의미 |
|-----------------|------|
| `rvfi_valid` | 이 사이클에 명령 하나가 retire 됨 |
| `rvfi_insn` | retire 한 명령의 인코딩(32-bit) |
| `rvfi_pc_rdata` / `rvfi_pc_wdata` | 이 명령의 PC / 다음 PC |
| `rvfi_rs1_addr` / `rvfi_rs1_rdata` 등 | source 레지스터 번호/읽은 값 |
| `rvfi_rd_addr` / `rvfi_rd_wdata` | destination 레지스터 번호/쓴 값 |
| `rvfi_mem_addr` / `rvfi_mem_rdata` / `rvfi_mem_wdata` | 메모리 접근 정보 |

핵심은 RVFI 가 _구현 무관_ 이라는 점입니다. 코어 입장에서는 "내가 무엇을 했는지"를 약속된 형식으로 보고하는 것뿐이고, riscv-formal 은 그 보고만으로 ISA 준수를 검사합니다. 이 인터페이스를 더 넓은 DV 서브시스템으로 묶는 draft 표준이 RVVI(RISC-V Verification Interface)입니다 — [M03](../03_rvfi_rvvi/)에서 다룹니다.

### 4.2 riscv-formal 의 check 종류

riscv-formal 은 명령 정확성만 보는 게 아니라 여러 _부류_ 의 properties 를 제공합니다.(외부 표준 지식)

```d2
direction: down

C1: "**Instruction checks**\n명령별 결과 == ISA spec\n(insns/*.v 모델)"
C2: "**Register check**\n레지스터 파일 일관성\n(쓴 값이 다음에 그대로 읽힘)"
C3: "**PC checks**\npc_fwd / pc_bwd\n순차 PC 와 분기 타겟 정확성"
C4: "**Liveness check**\n코어가 영원히 멈추지 않음\n(retire 가 결국 일어남)"
C5: "**Memory consistency**\nload/store 주소·값 일관성"
C6: "**CSR / 기타**\n구현에 따라 추가"
```

이들이 합쳐져 "코어가 RISC-V ISA 를 _구조적으로_ 준수하는가"를 다각도로 증명합니다. 명령 결과(C1)만 맞아도 PC 가 틀리거나(C3) 멈춰버리면(C4) 코어는 틀린 것이므로, check 부류를 함께 돌리는 것이 핵심입니다.

**consistency vs completeness — "결과 비교"를 넘는 부분.** 여기서 riscv-formal 의 핵심이 단순한 "결과값 비교"가 아니라는 점을 짚어야 합니다. step-and-compare(M02)가 "retire 된 명령의 _결과_ 가 맞나"를 본다면, riscv-formal 의 여러 check 는 그 전에 **"_무엇이_ retire 됐는가" 자체의 consistency** 를 증명합니다.

- **consistency check** — RVFI 채널들이 _서로 모순 없이_ 한 명령을 일관되게 기술하는가. 예: `rvfi_insn` 이 ADD 인데 `rvfi_rd_addr` 가 디코드와 다르면 모순. 또 `causal` 류 check 는 "한 명령이 읽은 레지스터 값(`rs_rdata`)이 _그 레지스터를 마지막으로 쓴 앞선 명령의 결과_ 와 일치하는가"를 봐서, 레지스터 데이터 흐름이 인과적으로 일관됨을 증명합니다. `unique` 류는 "각 retire 가 고유한 `rvfi_order` 를 가져 중복/누락이 없는가"를 봅니다.
- **completeness 관점** — liveness(C4)는 "코어가 _결국_ 명령을 retire 하는가"로, 아무것도 retire 하지 않는(그래서 어떤 결과 비교도 trivially 통과하는) 코어를 잡습니다.

왜 중요한가: 결과값만 비교하면 "_틀린 명령_ 을 retire 해놓고 그 틀린 명령의 결과는 자기 spec 과 일치"하는 코어를 통과시킬 수 있습니다. consistency check 가 "올바른 명령을, 올바른 순서로, 올바른 입력값으로 retire 했다"는 _프레임_ 을 먼저 못박기 때문에, 그 위에서 결과 비교가 의미를 갖습니다. 즉 riscv-formal 은 "결과가 맞나"(완전성의 한 축)와 "기술이 일관되나"(consistency)를 함께 증명해 ISA 준수를 _구조적으로_ 보장합니다.

### 4.3 Bounded Model Checking 이 보장하는 것

riscv-formal 의 기본 엔진은 BMC(bounded model checking)입니다.(외부 표준 지식) BMC 는 "reset 으로부터 k 사이클 이내에 property 를 위반하는 실행이 존재하는가?"를 SAT/SMT 솔버로 푼다는 의미입니다.

```
BMC(k):
  존재? ∃ 입력 시퀀스 길이 ≤ k : property 위반
  → 존재하면 그 시퀀스가 반례(최소 길이)
  → 없으면 "k 사이클까지는 위반 없음" (k 깊이 증명)
```

여기서 두 가지를 명확히 해야 합니다.

- BMC 가 PASS 라고 _모든 깊이_ 에서 안전한 것은 아닙니다. k=20 에서 깨끗해도 k=21 에 숨은 버그가 있을 수 있습니다. 그래서 k 를 충분히 키우거나, _unbounded_ 증명을 위해 k-induction 을 씁니다.
- BMC 가 FAIL 이면 _확실히_ 버그입니다. 솔버가 실제 위반 입력 시퀀스를 구성했기 때문입니다 — false positive 가 없습니다.

**k-induction 은 어떻게 무한 깊이를 닫는가.** BMC 가 "reset 부터 k 까지"를 보는 데 그친다면, k-induction 은 두 단계로 _모든 깊이_ 를 증명합니다.

1. **Base case**: reset 으로부터 처음 k 사이클 동안 property 가 성립한다(이건 BMC 와 같음).
2. **Inductive step**: _임의의_ 연속된 k 사이클에서 property 가 성립했다고 가정하면, 그 다음 한 사이클에서도 성립한다.

두 단계가 모두 닫히면, 수학적 귀납법처럼 _모든_ 사이클로 성질이 전파되어 unbounded 증명이 됩니다. 그런데 inductive step 이 _그냥은 잘 안 닫힙니다_. 이유는, inductive step 은 "임의의 k-윈도우"에서 시작하므로 솔버가 _reset 으로 도달할 수 없는 비현실적 상태_ 까지 시작점으로 가정하기 때문입니다 — 그런 상태에서 출발하면 property 가 깨지는 시퀀스가 _존재할 수 있고_, 솔버는 이를 반례로 제시합니다(실제로는 도달 불가능한데도). 이것이 **spurious CEX(가짜 반례)** 입니다.

해결은 **강한 invariant(보조 성질)** 를 추가하는 것입니다. "도달 가능한 상태라면 반드시 참인" 성질(예: "ROB 의 valid 비트와 tail 포인터가 항상 일관")을 invariant 로 함께 assume/assert 하면, 솔버의 시작 상태 공간이 _도달 가능한 쪽_ 으로 좁혀져 spurious CEX 가 사라지고 induction 이 닫힙니다. 그래서 실무에서 k-induction 을 닫는 작업의 대부분은 "어떤 보조 invariant 가 빠졌나"를 찾아 채우는 일입니다 — induction 이 안 닫히면 그 spurious 반례가 _어떤 invariant 가 필요한지_ 를 알려줍니다.

formal 기본 개념(induction, 도달 가능성, abstraction)은 [Formal Verification M01](../../formal_verification/01_formal_fundamentals/)에서 더 자세히 다룹니다.

### 4.4 Formal vs Simulation — 무엇을 보장하나

| 측면 | Simulation (M05) | Formal (riscv-formal) |
|------|------------------|----------------------|
| 입력 범위 | 실행한 자극만 | k 사이클 내 _모든_ 입력 |
| 보장 | 본 것에 대해 PASS | 위반 입력이 _없음_ 을 증명(bounded) |
| 실패 시 산출 | 실패 시드+ELF | 최소 반례 파형(VCD) |
| 확장성 한계 | coverage 곡선 평탄화 | state space 폭발(깊은 파이프·캐시) |
| 강점 | 시스템 레벨·긴 시나리오·성능 | 깊은 corner·증명·완전성 |
| 약점 | 확률 낮은 corner escape | 큰 블록·긴 시퀀스에 비현실적 |

---

## 5. 디테일 — 흐름, 한계, 상보적 사용

### 5.1 riscv-formal 을 코어에 붙이는 흐름

일반적 흐름은 다음과 같습니다.(외부 표준 지식)

1. **RVFI 구현**: 코어가 retire 시점에 `rvfi_*` 신호를 정확히 내도록 wrapper 를 작성. 이것이 코어가 _검증 가능_ 해지는 전제.
2. **check 선택/구성**: riscv-formal 의 명령 모델(`insns/`)과 check 부류(reg/pc/liveness 등)에서 코어가 지원하는 ISA 에 맞는 것을 고름.
3. **SymbiYosys 실행**: 각 check 를 SymbiYosys(`sby`) 태스크로 돌림. 엔진은 BMC(또는 cover/induction).
4. **결과 분석**: PASS → 그 check 가 k 깊이까지 증명. FAIL → 반례 VCD 를 열어 _첫 위반 사이클_ 의 RVFI 값과 코어 내부 신호를 대조.

### 5.2 반례(counterexample)가 디버그를 끝내준다

formal 디버그의 강력함은 반례가 _최소이며 결정론적_ 이라는 데 있습니다. 솔버는 property 를 위반하는 _가장 짧은_ 입력 시퀀스를 찾으므로, 반례 VCD 는 군더더기 없는 재현 시나리오입니다. 시뮬레이션의 "수만 명령 프로그램 중 어디서 틀어졌나"를 좁히는 노력이, formal 에서는 "k 사이클짜리 반례를 처음부터 본다"로 대체됩니다.

```
시뮬 디버그:  실패 ELF → 수만 명령 → 첫 divergence 명령 추적 (좁혀가기)
formal 디버그: 반례 VCD → 보통 수~수십 사이클 → 첫 위반 사이클 즉시 (이미 최소)
```

### 5.3 State space 폭발 — formal 의 현실적 한계

formal 이 만능이 아닌 이유는 _상태 공간 폭발_ 입니다. 파이프라인이 깊고 캐시·예측기·큰 레지스터 파일이 붙으면, 솔버가 탐색해야 할 상태가 지수적으로 커져 k 를 크게 키우기 어렵습니다. 그래서 실무는 다음 전략을 씁니다.

| 전략 | 내용 |
|------|------|
| 작은 k 로 시작 | 얕은 깊이에서 빠르게 명백한 버그를 잡고 점차 k 증가 |
| abstraction | 메모리·캐시를 추상 모델로 단순화해 state 축소 |
| 명령 단위 분해 | 전체 코어가 아니라 명령별 check 를 독립적으로 |
| k-induction | unbounded 증명이 필요한 핵심 property 에만 적용 |

**abstraction 의 구체 기법.** "추상 모델로 단순화"는 추상적이니, 실제로 무엇을 하는지 봅시다.

- **data abstraction** — 32/64-bit 데이터 경로의 _값 자체_ 는 명령 정확성 증명에 대부분 무관합니다(forwarding 이 옳으면 어떤 값이든 옳게 전달). 그래서 데이터 폭을 1~2 비트로 _좁혀_ 같은 제어 구조를 증명하면 state 가 급감합니다 — 제어 흐름은 보존하되 datapath 폭만 줄입니다.
- **free input(자유 입력)** — 메모리/캐시가 돌려주는 load 데이터를 _구체적으로 모델링하지 않고_ "솔버가 임의로 고를 수 있는 자유 값"으로 둡니다. 그러면 "어떤 메모리 값이 와도 코어가 옳게 처리하는가"를 한 번에 덮어, 메모리 서브시스템 전체 상태를 탐색에서 제거합니다.
- **blackboxing** — 곱셈기·나눗셈기·캐시 같은 큰 서브블록을 _내부를 비우고_ 인터페이스만 남깁니다(출력은 free input 처럼 둠). 코어 제어 로직을 증명할 때 그 블록 내부까지 솔버가 풀 필요가 없어집니다.

이들의 trade-off는 **sound 와 complete 의 균형**입니다. free input·blackboxing 은 _실제보다 더 많은_ 행동을 허용하므로(over-approximation), "그래도 property 가 성립"하면 _실제 코어에서도 성립_ 함이 보장됩니다(증명이 sound). 다만 그 자유가 _실제론 불가능한_ 입력까지 포함해 spurious CEX 를 만들 수 있어, 그땐 해당 입력을 제약하는 assumption 을 더해 좁혀야 합니다(아래 5.5 의 over-constraint 위험과 직결).

이런 이유로 formal 은 _명령 정확성·forwarding·CSR 같은 국소적 property_ 에 특히 강하고, _긴 시스템 시나리오·성능_ 은 시뮬레이션이 맡습니다.

### 5.5 assume/restrict 와 over-constraint — false PASS 의 함정

formal 의 가장 위험한 함정은 FAIL 이 아니라 _조용한_ PASS 입니다. 그 근원이 **over-constraint(과잉 제약)** 입니다. 솔버에게 "이런 입력만 고려하라"고 주는 input assumption(`assume`)·`restrict` 가 _너무 강하면_, 실제로는 도달 가능한 상태를 탐색에서 _배제_ 해버립니다. 그 배제된 영역에 버그가 있어도 솔버는 보지 못하고 PASS 를 냅니다 — 증명이 _공허(vacuous)_ 해지는 것입니다.

```
정상 assume:   비현실적/불법 입력만 배제 → 탐색이 실제 도달 영역과 일치
over-constraint: 실제 가능한 입력까지 배제 → 버그 영역이 탐색에서 사라짐 → false PASS
```

전형적 예: "메모리는 항상 정렬된 주소만 반환한다"는 assume 을 걸면, misaligned 경로의 버그가 영원히 안 잡힙니다 — 그 경로 자체가 탐색에서 빠졌으니까요. BMC FAIL 에 false positive 가 없는 것과 대조적으로, **PASS 는 assumption 이 옳을 때만 의미**가 있습니다.

진단 방법:

- **vacuity check / cover** — property 의 선행조건(antecedent)이 _실제로 만족 가능한지_ 를 cover 로 확인합니다. "ADD 가 retire 되는 상태에 도달 가능한가?"가 cover 로 안 닿으면, 그 assert 는 한 번도 _발동하지 않은_ 공허한 PASS 입니다.
- **assumption 최소화** — 꼭 필요한(비현실/불법 입력 배제용) assume 만 남기고, 의심스러운 강한 assume 은 제거해 FAIL 이 나는지 봅니다. 제거하니 FAIL 이 나면 그 assume 이 버그를 가리고 있던 것입니다.
- **assume 를 다른 모듈에선 assert 로 교차검증** — 한 블록의 입력 assume 을, 그 입력을 _생성하는_ 블록에서는 assert 로 검사해, assumption 이 실제로 보장되는지 확인합니다.

요점: formal 의 PASS 는 "솔버가 못 깼다"가 아니라 "_올바른 가정 아래_ 솔버가 못 깼다"입니다 — assumption 의 타당성 검증이 formal sign-off 의 필수 단계입니다.

### 5.4 상보적 사용 — formal 과 simulation 의 분업

```d2
direction: right

PROP: "명령 정확성\nforwarding\nx0/PC 일관성\n→ **Formal**" 
SIM: "긴 프로그램\nOS 부팅\n인터럽트 폭주\n성능·시스템\n→ **Simulation**"
SIGN: "**Sign-off**\n둘의 합집합"
PROP -> SIGN
SIM -> SIGN
```

성숙한 CPU 검증은 둘을 _상보적_ 으로 씁니다. formal 로 ISA 준수의 _국소적 완전성_ 을 증명하고, 시뮬레이션으로 _긴 시나리오와 시스템 통합_ 을 커버합니다. 어느 한쪽만으로는 sign-off 근거가 부족합니다. step-and-compare 시뮬레이션([M02](../02_step_and_compare/))과 formal 은 경쟁이 아니라 분업입니다.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'formal 이 PASS 면 그 명령은 완벽히 검증됐다']
**실제**: 기본 엔진 BMC 의 PASS 는 _k 사이클 깊이까지_ 위반이 없다는 뜻입니다. k=20 에서 깨끗해도 더 깊은 시퀀스에 버그가 있을 수 있습니다. "완전 증명"은 unbounded(예: k-induction)일 때만이며, 그것도 솔버가 induction 을 닫았을 때입니다.<br>
**왜 헷갈리는가**: "formal=증명=완벽"이라는 단순화 때문에 — 실무 대부분은 bounded.
:::
:::danger[❓ 오해 2 — 'formal 이 있으면 시뮬레이션은 필요 없다']
**실제**: formal 은 state space 폭발 때문에 긴 시스템 시나리오·OS 부팅·성능을 다루기 비현실적입니다. 반대로 시뮬레이션은 확률 낮은 corner 를 놓칩니다. 둘은 _분업_ 이지 대체가 아닙니다.<br>
**왜 헷갈리는가**: "증명이 표본보다 강하다"는 명제가 "모든 상황에서 더 낫다"로 과확장돼서.
:::
:::danger[❓ 오해 3 — 'RVFI 만 붙이면 코어가 자동으로 검증된다']
**실제**: RVFI 는 _검증을 가능하게 하는 인터페이스_ 일 뿐, RVFI 출력 자체가 _틀리면_ 검사도 틀립니다. RVFI wrapper 가 retire 정보를 정확히 내는지부터 검증해야 하며, 잘못된 RVFI 는 거짓 PASS 또는 거짓 FAIL 을 만듭니다.<br>
**왜 헷갈리는가**: "인터페이스만 붙이면 끝"이라는 plug-and-play 기대 때문에.
:::
:::danger[❓ 오해 4 — 'formal 의 반례는 시뮬레이션 실패처럼 길고 해석이 어렵다']
**실제**: BMC 반례는 _최소 길이_ 입니다 — 보통 수~수십 사이클. property 를 위반하는 가장 짧은 시퀀스이므로, 시뮬레이션의 수만 명령 추적보다 오히려 해석이 쉽습니다.<br>
**왜 헷갈리는가**: "formal 은 어렵다"는 막연한 인상이 디버그 단계까지 투사돼서.
:::
:::danger[❓ 오해 5 — 'BMC 가 FAIL 인데 그냥 가짜 경보일 수 있다']
**실제**: BMC FAIL 은 솔버가 _실제로 위반하는 입력 시퀀스를 구성_ 한 것이라 false positive 가 없습니다. 가짜처럼 보인다면 십중팔구 property 자체가 잘못 작성됐거나(over-constrained 누락), RVFI 출력이 부정확한 것입니다 — 반례는 진짜입니다.<br>
**왜 헷갈리는가**: 시뮬레이션의 환경 버그(false fail) 경험이 formal 에도 그대로 투사돼서.
:::
### DV 디버그 체크리스트 (이 모듈 내용으로 마주칠 첫 실패들)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| 모든 check 가 즉시 FAIL (사이클 0~1) | reset/assumption 누락 → 초기 상태가 비현실적 | `disable iff` reset, 초기 상태 assume |
| 명령 check 만 FAIL, 반례가 그럴듯 | RVFI wrapper 가 source/dest 값을 잘못 보고 | RVFI `rs*_rdata`/`rd_wdata` 매핑 |
| check 가 영원히 안 끝남(타임아웃) | k 가 너무 크거나 state space 폭발 | k 축소, abstraction, 블록 분해 |
| liveness check 만 FAIL | 코어가 특정 입력에서 hang(retire 정지) | 반례에서 stall 신호·핸드셰이크 추적 |
| PASS 인데 시뮬에선 버그 발견 | k 가 너무 얕아 깊은 corner 미도달 | k 증가 또는 해당 property 를 induction 으로 |
| 반례는 나오는데 RTL 에선 재현 안 됨 | RVFI 가 RTL 실제 동작과 불일치(wrapper 버그) | RVFI wrapper 의 retire 시점·값 정합성 |
| ISA 확장 명령이 안 잡힘 | 해당 명령 formal model 미포함 | riscv-formal `insns/` 에 해당 명령 모델 |

---

## 7. 핵심 정리 (Key Takeaways)

- **Simulation=표본, Formal=전수(bounded)**. 시뮬은 실행한 자극만 보장, formal 은 k 사이클 내 모든 입력에 대해 위반 부재를 증명한다.
- **RVFI = 구현 무관 retire 인터페이스**. 코어가 retire 정보를 약속된 형식으로 노출하면, riscv-formal 이 ISA spec 인코딩 property 로 검사한다. 같은 property 가 여러 코어에 재사용.
- **riscv-formal 의 check 부류**: 명령 정확성·레지스터·PC·liveness·메모리 일관성. 결과만 맞아도 PC 틀리거나 hang 하면 틀린 코어이므로 함께 돌린다.
- **BMC 의 의미**: PASS=k 깊이까지 증명(완전 증명 아님), FAIL=확실한 버그(최소 반례, false positive 없음). unbounded 는 k-induction.
- **반례가 디버그를 끝낸다**. 최소 길이 결정론적 반례 VCD → 첫 위반 사이클 즉시. 시뮬의 수만 명령 추적과 대비.
- **formal 과 simulation 은 분업**. 국소적 ISA 준수는 formal, 긴 시스템 시나리오·성능은 simulation. 둘의 합집합이 sign-off.

:::caution[실무 주의점]
- formal PASS 를 "완벽"으로 읽지 마라 — k 깊이를 명시하고, 핵심 property 는 induction 으로 unbounded 를 노려라.
- RVFI wrapper 의 정확성부터 검증하라 — 잘못된 RVFI 는 거짓 PASS/FAIL 의 근원.
- state space 폭발 시 k 축소·abstraction·명령 단위 분해로 대응 — 전체 코어를 한 번에 풀려 하지 마라.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — BMC PASS 의 의미 (Bloom: Analyze)]
riscv-formal 의 `add_correct` check 가 k=24 BMC 에서 PASS 했다. "이 코어의 ADD 는 완전히 검증됐다"고 말해도 되는가? 정확히 무엇이 보장되었는가?
<details>
<summary>정답</summary>

**"완전히"라고 말하면 안 됩니다.** 보장된 것은 _reset 으로부터 24 사이클 이내_ 에 `add_correct` property 를 위반하는 입력 시퀀스가 _없다_ 는 것뿐입니다.
- 25 사이클 이상 깊은 곳에 숨은 위반은 이 BMC 가 탐색하지 않았습니다.
- "모든 깊이"를 증명하려면 k-induction 으로 unbounded proof 를 닫아야 합니다(귀납 단계가 성립함을 솔버가 증명).
- 또한 이 property 는 ADD 의 _결과값_ 만 봅니다 — PC 갱신·예외 상호작용 등은 다른 check 가 따로 덮어야 합니다.
- 정확한 표현: "ADD 결과 정확성이 k=24 깊이까지 bounded-증명되었다."

</details>
:::
:::tip[🤔 Q2 — formal vs simulation 선택 (Bloom: Evaluate)]
"리눅스를 부팅시켜 인터럽트·페이지폴트가 섞인 1억 사이클 워크로드에서 코어가 hang 하지 않음"을 검증하고 싶다. formal 과 simulation 중 무엇이 적합하고, 왜인가?
<details>
<summary>정답</summary>

**Simulation 이 적합합니다.**
- 1억 사이클·OS 부팅 같은 _긴 시스템 시나리오_ 는 formal 의 state space 폭발 한계 때문에 비현실적입니다. BMC 로 1억 사이클 깊이를 푸는 것은 불가능에 가깝습니다.
- 시뮬레이션은 긴 시나리오를 실제 실행하므로 이런 시스템 통합·성능·복합 인터럽트 시퀀스에 강합니다.
- 단, "hang 하지 않음(liveness)"의 _국소적_ 보장은 formal 의 liveness check 로 _짧은 깊이_ 에서 보강할 수 있습니다(예: "어떤 상태에서도 결국 retire 한다").
- 따라서 올바른 답: 긴 워크로드 전체는 simulation, 그 안의 _국소적 liveness/명령 정확성_ 은 formal 로 분업. 둘을 상보적으로 쓰는 것이 sign-off 근거입니다.

</details>
:::
### 7.2 출처

**Internal**
- [M02 Step-and-Compare](../02_step_and_compare/) — 시뮬레이션 기반 reference 대조(formal 과 분업)
- [M03 RVFI/RVVI](../03_rvfi_rvvi/) — RVFI 인터페이스와 RVVI 표준
- [Formal Verification M01 Fundamentals](../../formal_verification/01_formal_fundamentals/), [M02 SVA](../../formal_verification/02_sva/) — BMC·induction·assertion 기초

**External**
- `riscv-formal` (YosysHQ) — RVFI 기반 RISC-V 코어 formal verification 프레임워크
- *RISC-V Verification: The 5 Levels of Simulation-Based Processor Hardware DV* — SemiEngineering (formal 의 위치)
- SymbiYosys / Yosys (YosysHQ) — open formal 엔진 (외부 표준 지식)
- *The RISC-V Instruction Set Manual* — 명령 spec 의 근거 (외부 표준 지식)

---

## 다음 모듈

→ [Module 07 — ISA Functional Coverage & 특수 영역](../07_coverage_special_areas/): 명령 정확성을 넘어 CSR·privilege·인터럽트·예외·MMU·메모리 ordering·OoO/multi-hart 같은 _특수 검증 영역_ 의 coverage 를 어떻게 설계하고, 상용·오픈 솔루션(ImperasDV·CORE-V)이 이를 어떻게 다루는지 봅니다.

[퀴즈 풀어보기 →](../quiz/06_riscv_formal_quiz/)
