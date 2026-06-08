---
title: "Module 07 — ISA Functional Coverage & 특수 검증 영역"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Design** 명령·레지스터·인접 조합을 의미 있게 분류한 ISA functional coverage 모델(coverpoint·cross·transition)을 설계할 수 있다.
- **Differentiate** CSR·privilege mode·interrupt·exception·MMU·memory ordering·OoO/multi-hart 각각이 _왜 별도의_ coverage·검증 전략을 요구하는지 구분할 수 있다.
- **Analyze** 한 특수 영역(예: privilege transition)에서 무엇을 coverpoint·cross 로 잡아야 escape 가 없는지 분석할 수 있다.
- **Evaluate** 주어진 검증 과제에 대해 ImperasDV·CORE-V(core-v-verif) 같은 상용·오픈 솔루션을 자체 구축과 비교해 평가할 수 있다.
- **Plan** ISA coverage 와 특수 영역을 묶은 CPU DV coverage closure 계획을 수립할 수 있다.
:::
:::note[사전 지식]
- [M05 제약 랜덤 자극](../05_riscv_dv_stimulus/), [M06 Formal](../06_riscv_formal/), [M02 Step-and-Compare](../02_step_and_compare/), [M04 UVM 코어 환경](../04_uvm_core_env/)
- functional coverage 문법(coverpoint·cross·transition·illegal_bins) — [UVM M05 TLM/Scoreboard/Coverage](../../uvm/05_tlm_scoreboard_coverage/)
- 캐시·MMU·OoO 배경 — [Computer Architecture M03 OoO](../../computer_architecture/03_ooo_branch_prediction/), [M04 Memory Hierarchy](../../computer_architecture/04_memory_hierarchy/)
:::
---

## 1. Why care? — "명령은 다 맞다"가 "CPU 가 맞다"는 아니다

### 1.1 시나리오 — 명령은 완벽한데 인터럽트가 명령을 삼킨다

[M05](../05_riscv_dv_stimulus/)의 제약 랜덤과 [M06](../06_riscv_formal/)의 formal 로 모든 명령의 _개별 정확성_ 을 증명했다고 합시다. 그래도 다음 버그가 남을 수 있습니다.

> 외부 인터럽트가 `lw`(load) 명령의 _바로 그 사이클_ 에 도착했을 때, 코어가 load 를 retire 한 것으로 처리하면서 동시에 trap 으로 진입해 `mepc` 에 _다음_ 명령 주소를 잘못 기록했다. 인터럽트 복귀 후 load 결과를 쓰는 명령이 한 번 더 실행되거나 건너뛰어진다.

이 버그는 _어떤 단일 명령도 틀리지 않습니다_. 틀린 것은 "인터럽트와 명령 retire 의 _경계 상호작용_"입니다. 명령 coverage 100% 와 명령 formal 증명으로는 이 영역이 _보이지 않습니다_. CPU 는 명령 실행기 그 이상입니다 — privilege·예외·인터럽트·메모리 순서·다중 hart 라는 _시스템 상태 기계_ 이고, 버그는 대부분 이 상태들의 _전이와 상호작용_ 에 숨습니다.

### 1.2 해법 — 특수 영역마다 별도의 coverage 와 전략

해법은 "명령 coverage"라는 한 축을 넘어, _특수 영역마다_ 무엇을 봐야 하는지를 명시적으로 설계하는 것입니다. privilege 전환은 _전이(transition)_ 로, 인터럽트는 _명령 경계와의 cross_ 로, 메모리 ordering 은 _다중 접근의 관찰 순서_ 로 — 각 영역의 버그 구조에 맞는 coverage 모델이 따로 필요합니다.

```
명령 정확성 (M05/M06)        →  "각 명령이 옳게 실행되는가"
─────────────────────────────────────────────────
특수 영역 coverage (M07)      →  "상태·경계·상호작용이 옳게 다뤄지는가"
  CSR / privilege / interrupt / exception / MMU / ordering / OoO·multi-hart
```

이 모듈을 건너뛰면 CPU 검증은 "명령은 다 맞는데 시스템은 틀린" 상태로 사인오프되고, 인터럽트 타이밍·privilege escalation·메모리 순서 같은 _가장 위험한_ 버그가 escape 합니다.

:::note[RISC-V 를 예로 들지만 영역은 ISA 공통]
CSR·privilege·exception 의 _이름_(예: `mstatus`, `mcause`)은 RISC-V 사양을 씁니다.(외부 표준 지식) 그러나 "privilege 전환·인터럽트 경계·메모리 ordering·OoO/multi-hart 를 별도 coverage 로 다룬다"는 _영역 구분과 전략_ 은 ARM 등 모든 현대 CPU 에 공통입니다. ARM 은 exception level(EL0–EL3)·`SPSR`/`ELR` 등으로 대응됩니다.(외부 표준 지식)
:::

---

## 2. Intuition — 한 줄 비유, 한 장 그림

:::tip[💡 한 줄 비유]
**ISA coverage 가 "단어를 다 썼나"라면, 특수 영역 coverage 는 "문장·문맥·대화를 다 겪었나"이다.**<br>
명령 하나하나(단어)를 다 써도, privilege 전환(문법 모드 전환)·인터럽트(끼어들기)·메모리 ordering(두 화자의 발화 순서)을 안 겪으면 _대화_ 는 검증되지 않은 것입니다. 특수 영역은 명령들이 _시스템으로 엮일 때_ 생기는 차원입니다.
:::

### 한 장 그림 — CPU coverage 의 계층

```d2
direction: down

L0: "**ISA functional coverage**\n명령 종류 · 레지스터 · 명령 인접(cross/transition)"
L1: "**상태 영역**\nCSR 접근 · privilege mode 전이\nexception 진입/복귀"
L2: "**이벤트 영역**\ninterrupt × 명령 경계\nexception × 명령 타입"
L3: "**메모리 영역**\nMMU/page table · 정렬\nmemory ordering(load/store 관찰 순서)"
L4: "**동시성 영역**\nOoO retire · multi-hart\nrace · atomic"

L0 -> L1 -> L2 -> L3 -> L4: "위로 갈수록 상호작용·전이가 핵심"
```

### 왜 이 구조인가 — Design rationale

세 가지 요구의 교집합입니다.

1. **버그 구조가 영역마다 다르다** → coverage 모델도 영역마다 달라야 한다. privilege 는 transition bins, 인터럽트는 cross(이벤트 × 명령경계), ordering 은 관찰 순서 시나리오.
2. **명령 coverage 와 특수 영역은 합집합이어야 한다** → 둘 다 같은 retire/이벤트 stream 에서 sample 하되, 의미 분류가 다른 별도 covergroup 으로.
3. **상호작용은 _조합_ 에서 터진다** → 단일 변수가 아니라 cross 가 핵심. "인터럽트가 _어느 명령 타입_ 경계에 도착했나"처럼 두 축의 곱이 진짜 corner.

---

## 3. 작은 예 — privilege transition 을 coverage 로 잡기

가장 전형적인 특수 영역인 privilege mode 전이를 작은 covergroup 으로 설계해 봅시다.

### 단계별 다이어그램

```d2
direction: down

S1: "**① 이벤트 관찰**\nretire monitor 가\nprivilege mode 변화 감지\n(M→S, S→U, trap, mret/sret)"
S2: "**② coverpoint**\ncp_mode: 현재 privilege\ncp_cause: trap 원인(mcause)"
S3: "**③ transition bins**\nM=>S, S=>U,\nU=>(trap)=>M, M=>(mret)=>S"
S4: "**④ cross**\nprivilege 전이 × trap 원인\n(어느 원인이 어느 전이를 유발했나)"
S5: "**⑤ closure**\n미커버 전이 → M05 knob 로 자극 편향"
S1 -> S2 -> S3 -> S4 -> S5
```

### 단계별 의미

| Step | 무엇을 | 왜 |
|------|--------|-----|
| ① | privilege mode 변화 이벤트를 retire/CSR monitor 가 포착 | 전이는 _순간_ 이므로 이벤트로 sample 해야 한다 |
| ② | 현재 mode·trap 원인을 coverpoint 로 | 단일 상태 도달 여부 baseline |
| ③ | 전이를 transition bins 로 | privilege 버그는 _상태_ 가 아니라 _전이_ 에서 터진다 |
| ④ | 전이 × 원인을 cross 로 | "page fault 로 인한 S→M 전이"처럼 _조합_ 이 진짜 corner |
| ⑤ | 미커버 전이를 [M05](../05_riscv_dv_stimulus/) privilege knob 로 유발 | coverage → 자극의 closed loop |

핵심은 ③ 입니다. "supervisor 모드에 _도달_ 했다"(단일 coverpoint)와 "user 에서 page fault 로 supervisor 에 _진입_ 했다가 `sret` 로 복귀했다"(transition)는 전혀 다른 검증 깊이입니다. privilege 버그(권한 체크 누락, 잘못된 `mepc`)는 거의 항상 _전이 순간_ 에 있습니다.

### coverage 모델의 형태 (개념 코드)

```systemverilog
// 개념 예시 — privilege transition coverage (CSR/retire monitor 에서 sample)
// priv_e: 현재 privilege (M/S/U), cause: trap 원인 코드
covergroup priv_cg with function sample(priv_e cur, int unsigned cause, bit is_trap);

  cp_mode: coverpoint cur {
    bins m = {PRIV_M};
    bins s = {PRIV_S};
    bins u = {PRIV_U};
  }

  // ★ 전이 — privilege 버그의 핵심
  cp_trans: coverpoint cur {
    bins m_to_s = (PRIV_M => PRIV_S);   // mret with MPP=S
    bins s_to_u = (PRIV_S => PRIV_U);
    bins u_to_m = (PRIV_U => PRIV_M);   // U-mode trap → M
    bins s_to_m = (PRIV_S => PRIV_M);   // S-mode trap → M
    // 발생하면 안 되는 전이 (예: U 가 직접 M 의 CSR 를 못 바꿈)
    illegal_bins u_escalates = (PRIV_U => PRIV_M) iff (!is_trap);
  }

  cp_cause: coverpoint cause iff (is_trap) {
    bins ecall   = {CAUSE_ECALL};
    bins illegal = {CAUSE_ILLEGAL_INSN};
    bins pgfault = {CAUSE_PAGE_FAULT};
  }

  // ★ cross — "어느 원인이 어느 전이를 유발?"
  cx_cause_trans: cross cp_cause, cp_trans;
endgroup
```

:::note[여기서 잡아야 할 두 가지]
**(1) 특수 영역은 _전이와 cross_ 가 본체다.** 단일 coverpoint(모드 도달)는 baseline 일 뿐, 버그는 전이(`cp_trans`)와 조합(`cx_cause_trans`)에 산다. `illegal_bins` 는 권한 위반 전이(U→M without trap)를 _자동 검출_ 하는 assertion 역할도 한다.<br>
**(2) coverage 와 자극은 closed loop 이다.** 미커버 전이가 보이면 [M05](../05_riscv_dv_stimulus/)의 privilege knob 으로 그 전이를 유발하는 자극을 만든다. coverage 는 _측정_ 이고 closure 는 _자극 편향_ 으로 한다.
:::

---

## 4. 일반화 — 특수 영역별 무엇을 봐야 하나

각 영역은 _고유한 버그 구조_ 가 있고, 그에 맞는 coverage 축이 다릅니다.

### 4.1 CSR (Control/Status Register)

| 무엇을 본다 | coverage 축 |
|------------|-------------|
| 각 CSR 의 read/write 접근 | coverpoint: CSR 주소 × 접근 종류 |
| access policy(RO/RW/WARL) 준수 | illegal_bins: RO 에 write 가 effect, 예약 비트 set |
| side-effect·ordering(write 후 즉시 의존) | transition: CSR write => dependent insn |
| privilege 별 접근 권한 | cross: CSR × privilege mode |

CSR 은 RAL 로도 다루는 영역입니다 — 레지스터 모델·mirror·access policy 검증은 [UVM M07 RAL](../../uvm/07_register_layer_ral/)과 직접 연결됩니다. CPU 의 CSR 은 단순 레지스터가 아니라 _privilege·예외와 얽힌_ 상태이므로, RAL 검증 위에 privilege cross 를 얹어야 합니다.

### 4.2 Privilege mode & Exception

3 장의 transition 모델이 본체입니다. 추가로 exception 은 _진입 architectural state_ 를 본다: trap 진입 시 `mcause`/`mepc`/`mtval`/`mstatus`(MPP/MPIE) 가 spec 대로 기록됐는가. step-and-compare([M02](../02_step_and_compare/))가 이 CSR 들을 ISS 와 대조해 _값_ 을, coverage 가 _전이 발생_ 을 측정합니다.

### 4.3 Interrupt — 명령 경계와의 cross 가 핵심

```d2
direction: right
INT: "interrupt 도착"
B1: "load 경계"
B2: "store 경계"
B3: "branch 경계"
B4: "CSR 명령 경계"
INT -> B1: "cross"
INT -> B2
INT -> B3
INT -> B4
```

1.1 의 버그가 바로 이 영역입니다. 인터럽트는 _언제 오느냐_(어느 명령 경계)가 corner 이므로, "interrupt × 명령 타입" cross 와 "interrupt × 파이프라인 상태(stall/flush 중)" cross 를 설계합니다. 우선순위·중첩(nested) 인터럽트, 인터럽트 직후 복귀 정확성도 transition 으로 잡습니다.

### 4.4 MMU / Virtual Memory

| 무엇을 본다 | coverage 축 |
|------------|-------------|
| 주소 변환(page table walk) 성공/실패 | coverpoint: walk 결과(hit/fault) |
| page fault 종류 | bins: load/store/instruction page fault |
| 정렬·페이지 경계 횡단 접근 | coverpoint: misaligned, page-crossing |
| TLB 상태(fill/flush, `sfence`) | transition: TLB miss => fill => hit |
| permission(R/W/X, U-bit) | cross: 접근 종류 × page permission |

MMU 자극은 [M05](../05_riscv_dv_stimulus/)의 force-riscv 가 강한 영역입니다(페이지 테이블·메모리 상태 구성). 캐시·TLB 배경은 [Computer Architecture M04](../../computer_architecture/04_memory_hierarchy/)를 참조하세요.

### 4.5 Memory Ordering

memory ordering 은 단일 코어 안에서도(load/store 재정렬), 특히 multi-hart 에서 _관찰 순서_ 가 메모리 모델(RISC-V RVWMO 등)을 지키는가입니다.(외부 표준 지식) coverage 는 _값_ 이 아니라 _순서 시나리오_ 를 본다: store-load forwarding, 두 hart 의 message-passing 패턴(한 hart 가 data 후 flag 를 쓰고, 다른 hart 가 flag 후 data 를 읽는) 등이 허용된 결과만 내는가. 이 영역은 litmus test(정형화된 작은 동시성 패턴)로 자극을 만드는 것이 표준입니다.(외부 표준 지식)

### 4.6 OoO retire & Multi-hart

```d2
direction: down
OOO: "**OoO 코어**\nin-order retire 보장?\nROB·하자드·예외 정밀성(precise exception)"
MH: "**Multi-hart**\nhart 간 race\natomic(AMO/LR-SC)\n메모리 일관성"
```

OoO 코어는 내부적으로 명령을 재정렬해도 _architectural 효과는 in-order_ 여야 합니다(precise exception). coverage 는 "재정렬이 실제로 일어났고, 그래도 retire 순서/예외가 정확한가"를 봅니다. multi-hart 는 hart 간 race·atomic(LR/SC, AMO)·일관성이 추가 축입니다. OoO 배경은 [Computer Architecture M03](../../computer_architecture/03_ooo_branch_prediction/)를, scoreboard 의 OoO 매칭은 [UVM M05](../../uvm/05_tlm_scoreboard_coverage/)의 per-key 큐 패턴을 참조하세요.

---

## 5. 디테일 — 상용·오픈 솔루션, closure 계획

### 5.1 자체 구축 vs 상용·오픈 솔루션

위의 특수 영역을 모두 직접 모델링하는 것은 막대한 노동입니다. 그래서 실무는 검증된 자산을 활용합니다.(외부 표준 지식)

| 솔루션 | 무엇 | 강점 |
|--------|------|------|
| **ImperasDV** (Synopsys) | 상용 reference model + step-and-compare 환경 | 검증된 ISS, 비동기 이벤트(인터럽트)·CSR·privilege 모델이 성숙, 상용 지원 |
| **CORE-V core-v-verif** (OpenHW Group) | cv32e40* 등 코어용 오픈 UVM 검증 환경 | 실제 산업용 코어에 대한 _완성된_ UVM env·coverage·시퀀스를 오픈으로 제공 |
| **riscv-dv / riscv-formal** | 오픈 ISG / formal | 자극 생성·formal 의 오픈 표준(앞 모듈) |

ImperasDV 는 _정답 모델_ 의 품질(특히 인터럽트·CSR·privilege 의 비동기 동작)에서, CORE-V core-v-verif 는 _완성된 검증 환경의 참조 구현_ 에서 가치가 큽니다.(외부 표준 지식) 자체 구축 시에도 이들을 _기준점_ 으로 삼는 것이 효율적입니다.

### 5.2 reference model 이 특수 영역에서 더 중요해지는 이유

명령 정확성은 비교적 정적이지만, 인터럽트·예외·privilege 는 _비동기적_ 이고 _타이밍 민감_ 합니다. 이 영역에서 직접 만든 golden model 은 미묘한 spec 해석 오류를 내기 쉽습니다. 그래서 ImperasDV 처럼 _상용 검증된_ reference model 의 가치가 특히 큽니다 — step-and-compare 의 "정답"이 틀리면 검증 전체가 무의미하기 때문입니다([M02](../02_step_and_compare/)).

### 5.3 CPU DV coverage closure 계획

```
1. ISA 명령 coverage (M05 ISG)         → 명령 종류·인접 → baseline
2. CSR / privilege transition          → transition bins → 상태 영역
3. interrupt × 명령경계 cross           → 이벤트 영역 (가장 escape 多)
4. exception 진입 state (mcause/mepc)   → step-and-compare 로 값 검증
5. MMU / ordering / multi-hart          → 전용 시퀀스(litmus) + force-riscv
6. 미커버 영역 → M05 knob / directed     → closed loop
7. 국소 ISA 준수 → M06 formal 로 증명     → 완전성 보강
```

closure 의 핵심은 _영역별로_ baseline → cross/transition → directed 보완을 반복하고, 명령 정확성처럼 _국소적_ 인 것은 formal([M06](../06_riscv_formal/))로 _증명_ 해 시뮬레이션 coverage 부담을 줄이는 분업입니다.

### 5.4 escape 가 잦은 순서 (경험칙)

특수 영역 중에서도 escape 가 잦은 순서는 대략 _인터럽트 경계 → privilege 전이 → memory ordering → MMU corner_ 입니다.(추론) 모두 _비동기·동시성·전이_ 라는 공통점이 있습니다 — 즉 "단일 명령으로 분해되지 않는" 영역일수록 위험합니다. coverage 설계 우선순위를 여기에 맞추는 것이 합리적입니다.

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — '명령 coverage 100% + 명령 formal 증명이면 CPU 검증 끝']
**실제**: 그것은 명령의 _개별_ 정확성일 뿐입니다. CPU 버그의 다수는 privilege 전이·인터럽트 경계·메모리 ordering 같은 _상호작용_ 에 있고, 이는 명령 coverage 에 전혀 안 잡힙니다. 특수 영역 coverage 가 별도로 필요합니다.<br>
**왜 헷갈리는가**: CPU 를 "명령 실행기"로만 보는 단순 모델 때문에 — 실제로는 시스템 상태 기계.
:::
:::danger[❓ 오해 2 — 'privilege mode 에 도달했으면 privilege 검증됐다']
**실제**: 모드 _도달_(단일 coverpoint)과 모드 _전이_(transition)는 다릅니다. 권한 체크 누락·잘못된 `mepc` 같은 버그는 전이 _순간_ 에 있습니다. transition bins 와 cross(전이 × 원인)가 본체입니다.<br>
**왜 헷갈리는가**: "S-mode 를 봤다"가 "S-mode 진입/복귀를 다 봤다"처럼 들려서.
:::
:::danger[❓ 오해 3 — '인터럽트는 그냥 한 번 걸어보면 된다']
**실제**: 인터럽트 버그는 _언제 도착하느냐_(어느 명령 경계, 파이프라인 stall/flush 중)에 달려 있습니다. "interrupt × 명령 타입/파이프라인 상태" cross 로 도착 시점을 다양화해야 하며, 중첩·우선순위·복귀까지 봐야 합니다.<br>
**왜 헷갈리는가**: 인터럽트를 _이벤트 1 회_ 로만 보고 _타이밍 차원_ 을 놓쳐서.
:::
:::danger[❓ 오해 4 — '메모리 ordering 은 값만 맞으면 된다']
**실제**: ordering 검증은 _값_ 이 아니라 _관찰 순서가 메모리 모델을 지키는가_ 입니다. 특히 multi-hart 에서 허용/금지된 결과는 메모리 모델(RVWMO 등)이 정의하며, litmus test 로 순서 시나리오를 만들어 _허용되지 않은 결과_ 가 안 나오는지 봐야 합니다.<br>
**왜 헷갈리는가**: 단일 코어 관점의 "load 가 맞는 값을 읽었다"로 ordering 을 환원해서.
:::
:::danger[❓ 오해 5 — 'reference model 은 직접 만들면 되니 상용은 사치다']
**실제**: 명령 정확성은 자작 가능하지만, 인터럽트·예외·privilege 의 _비동기 타이밍_ 까지 spec 대로 정확한 golden model 을 만드는 것은 극히 어렵습니다. 정답 모델이 틀리면 step-and-compare 전체가 무의미하므로, ImperasDV 같은 검증된 reference 의 가치가 이 영역에서 특히 큽니다.<br>
**왜 헷갈리는가**: reference model 을 "ISS 한 줄짜리"로 과소평가해서 — 비동기 정밀성이 어려운 부분.
:::
### DV 디버그 체크리스트 (이 모듈 내용으로 마주칠 첫 실패들)

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| privilege transition bin 이 거의 0 | privilege 자극 knob off, 또는 단일 coverpoint 만 설계 | M05 privilege 시퀀스 knob, covergroup 의 transition bins |
| 인터럽트 cross bin 이 한쪽만 채워짐 | 인터럽트가 항상 같은 명령 경계에 도착(주입 타이밍 고정) | 인터럽트 주입 타이밍 무작위화, "× 명령타입" cross |
| step-and-compare 가 trap 진입에서만 mismatch | DUT 또는 ISS 의 비동기 이벤트 모델 불일치 | `mcause`/`mepc`/`mstatus` 값, ISS 인터럽트 모델 설정 |
| MMU page fault bin 이 0 | 페이지 테이블이 항상 valid/permissive 하게 생성됨 | force-riscv 페이지 설정, fault 유발 permission |
| multi-hart 에서 가끔만 mismatch (재현 어려움) | memory ordering/atomic race | litmus test 시나리오, 메모리 모델 checker |
| OoO 코어인데 예외 후 상태가 틀림 | precise exception 미보장(재정렬 후 잘못된 retire) | ROB flush·retire 순서, 예외 시 in-flight 명령 처리 |
| coverage 는 높은데 인터럽트 버그 escape | interrupt × 파이프라인상태 cross 누락 | stall/flush 중 인터럽트 도착 cross 존재 여부 |

---

## 7. 핵심 정리 (Key Takeaways)

- **명령 정확성 ≠ CPU 정확성**. CPU 는 시스템 상태 기계이고, 버그의 다수는 privilege·인터럽트·ordering 의 _전이와 상호작용_ 에 있다. 특수 영역 coverage 가 별도로 필요하다.
- **특수 영역은 전이와 cross 가 본체**. 단일 도달(coverpoint)은 baseline, 버그는 transition(privilege 전이, TLB miss→fill)과 cross(인터럽트 × 명령경계, 원인 × 전이)에 산다.
- **인터럽트는 _타이밍_ 차원**. "interrupt × 명령 타입/파이프라인 상태" cross 로 도착 시점을 다양화 — 이 영역이 escape 가 가장 잦다.
- **memory ordering 은 관찰 순서**. multi-hart 에서 메모리 모델(RVWMO 등) 준수를 litmus test 로 검증 — 값이 아니라 허용/금지 결과.
- **상용·오픈 솔루션 활용**. ImperasDV(검증된 비동기 reference model), CORE-V core-v-verif(완성된 UVM env 참조). reference model 정확성이 특수 영역에서 결정적.
- **closure 는 영역별 분업**. ISA baseline → 영역별 cross/transition → directed/litmus 보완, 국소 ISA 준수는 formal([M06](../06_riscv_formal/))로 증명해 부담 분산.

:::caution[실무 주의점]
- privilege·인터럽트는 _전이/타이밍_ coverage 가 본체 — 단일 coverpoint 로 끝내지 마라.
- 특수 영역의 step-and-compare 는 reference model 의 _비동기 정밀성_ 에 의존 — 정답 모델부터 신뢰하라(ImperasDV 등).
- memory ordering/multi-hart 는 일반 랜덤으로 거의 안 나온다 — litmus test 와 전용 시퀀스로 명시적으로 유발하라.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — privilege coverage 설계 (Bloom: Analyze)]
어떤 팀이 privilege coverage 로 "M/S/U 모드 각각에 한 번 이상 도달"만 측정해 100% 를 보고했다. 이 모델이 놓치는 버그 부류를 두 개 이상 들고, 어떤 coverage 축으로 보강해야 하는지 설명하라.
<details>
<summary>정답</summary>

단일 도달 coverpoint 는 _전이와 조합_ 을 놓칩니다.
- **놓치는 버그 (1) 전이 정확성**: `mret`/`sret` 로 잘못된 모드로 복귀(예: MPP 잘못 해석)하거나, U-mode 가 권한 없이 M-mode CSR 를 바꾸는(escalation) 버그. → `cp_trans` transition bins(M=>S, S=>U, U=>(trap)=>M)와 `illegal_bins`(권한 위반 전이)로 보강.
- **놓치는 버그 (2) 원인-전이 조합**: page fault 로 인한 S→M 전이 시 `mcause`/`mepc` 가 틀리는 버그. → `cross cp_cause, cp_trans` 로 "어느 원인이 어느 전이를 유발했나"를 측정.
- 추가로 step-and-compare 가 전이 _순간의 CSR 값_(`mepc`/`mstatus.MPP`)을 ISS 와 대조해야 _값_ 까지 검증됩니다.
- 요지: 모드 _도달_ 은 baseline 일 뿐, privilege 버그는 _전이 순간_ 에 살기 때문에 transition + cross + CSR 값 검증이 필요합니다.

</details>
:::
:::tip[🤔 Q2 — 솔루션 선택 (Bloom: Evaluate)]
인터럽트가 임의 명령 경계에 도착하는 시나리오를 검증하는데, 직접 만든 C 모델 reference 가 가끔 DUT 와 어긋난다(어느 쪽이 맞는지 불분명). ImperasDV 같은 상용 reference 로 바꾸는 것이 정당화되는가? 판단 근거는?
<details>
<summary>정답</summary>

**정당화될 가능성이 높습니다 — 단, 먼저 어긋남의 원인을 분류해야 합니다.**
- step-and-compare 의 대전제는 _reference 가 정답_ 이라는 것입니다. 인터럽트는 _비동기·타이밍 민감_ 영역이라, 직접 만든 C 모델이 인터럽트 도착 시점·`mepc` 기록·우선순위 같은 미묘한 spec 을 잘못 해석했을 가능성이 큽니다.
- "어느 쪽이 맞는지 불분명"하다는 것은 _정답 모델의 신뢰도_ 자체가 흔들린다는 신호입니다 — 이 상태로는 어떤 mismatch 도 결론 낼 수 없습니다.
- 따라서 _상용 검증된_ reference(ImperasDV)로 바꿔 정답의 기준점을 확보하는 것은 합리적입니다. 비동기 이벤트 모델이 성숙하기 때문입니다.
- 단 맹목적 전환은 금물: 먼저 어긋난 사례 한둘을 spec(RISC-V privileged manual) 으로 _직접_ 판정해 DUT 버그인지 reference 버그인지 분류하고, reference 버그 비중이 높으면 전환이 정당화됩니다.

</details>
:::
### 7.2 출처

**Internal**
- [M02 Step-and-Compare](../02_step_and_compare/) — 비동기 이벤트의 reference 대조
- [M05 제약 랜덤 자극](../05_riscv_dv_stimulus/) — privilege/예외/인터럽트 자극 knob, force-riscv(MMU)
- [M06 Formal](../06_riscv_formal/) — 국소 ISA 준수의 증명 분업
- [UVM M05 Coverage](../../uvm/05_tlm_scoreboard_coverage/) — transition/cross/illegal_bins, OoO scoreboard
- [UVM M07 RAL](../../uvm/07_register_layer_ral/) — CSR 의 레지스터 모델·access policy
- [Computer Architecture M03 OoO](../../computer_architecture/03_ooo_branch_prediction/), [M04 Memory Hierarchy](../../computer_architecture/04_memory_hierarchy/) — OoO·캐시·TLB 배경

**External**
- *RISC-V Verification: The 5 Levels of Simulation-Based Processor Hardware DV* — SemiEngineering
- *The RISC-V Instruction Set Manual, Volume II: Privileged* — CSR·privilege·trap·RVWMO 사양 (외부 표준 지식)
- ImperasDV (Synopsys) — 상용 reference model / step-and-compare 솔루션 (외부 표준 지식)
- OpenHW Group *core-v-verif* — CORE-V(cv32e40*) UVM 검증 환경 (외부 표준 지식)

---

## 다음 모듈

→ 토픽을 마쳤습니다. [용어집 (Glossary) →](../glossary/) 에서 핵심 용어를 ISO 11179 형식으로 복습하거나, [전체 퀴즈 모음 →](../quiz/) 에서 이해도를 점검하세요.

[퀴즈 풀어보기 →](../quiz/07_coverage_special_areas_quiz/)
