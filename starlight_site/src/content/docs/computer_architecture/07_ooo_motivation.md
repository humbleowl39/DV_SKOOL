---
title: "Module 07 — 왜 순서를 바꿔 실행하는가 (OoO 동기)"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** in-order 실행(명령을 프로그램 순서 그대로 실행)이 첫 해저드에서 멈추는 한계와, OoO(out-of-order, 명령을 프로그램 순서와 다르게 실행하는 기법) 실행이 명령 윈도우(아직 끝나지 않은 명령들을 모아 둔 창)에서 준비된 명령부터 issue(실행 유닛으로 내보냄)하는 원리를 설명할 수 있다.
- **Describe** dispatch(in-order) → execute(OoO) → retire(in-order)의 3단계 골격이 "실행 순서 ≠ 완료 순서"를 어떻게 분리하는지 기술할 수 있다.
- **Differentiate** execution(완료) 순서와 retirement(commit) 순서를 구분하고, 왜 검증 기대값이 항상 retire 순서를 기준으로 해야 하는지 구분할 수 있다.
:::
:::note[사전 지식]
- [Module 06 — Pipeline & Hazard](../06_pipeline_hazard/) (RAW/WAR/WAW, 분기 페널티, in-order stall)
- [Module 05 — ISA & RISC-V](../05_isa_riscv/) (architectural state, retire)
:::

:::note[이 모듈의 위치]
OoO(out-of-order) 실행은 분량이 많아 세 모듈로 나눕니다. **M07(지금)** 은 _왜_ 순서를 바꾸는지(동기와 큰 그림), **[M08](../08_tomasulo_rob/)** 은 _어떻게_(Tomasulo·ROB 의 실제 부품), **[M09](../09_branch_prediction/)** 는 그 위에서 도는 분기 예측·speculation 을 다룹니다.
:::
---

## 1. Why care? — execution 순서와 retirement 순서를 혼동하면 기대값이 틀린다

### 1.1 시나리오 — "결과가 순서 없이 나왔다"는 착각

OoO 코어를 검증할 때 가장 흔한 함정은 _실행 순서_ 와 _완료(retire) 순서_ 를 혼동하는 것입니다. OoO 코어는 명령을 program order 와 다르게 실행하지만, architectural state(레지스터·메모리의 관찰 가능한 값)는 반드시 program order 대로 갱신합니다. reference model 을 만들 때 "OoO 니까 결과도 순서 없이 비교하자"고 하면, 정상 동작을 mismatch 로 신고하게 됩니다. 올바른 기대값은 항상 _retire 순서 = program order_ 기준입니다.

또 다른 함정은 분기 예측과 speculation 입니다. 코어가 예측 경로의 명령을 미리 실행했다가 misprediction(분기 예측 실패)으로 squash(잘못 실행한 명령들을 통째로 무효화·폐기하는 것)하면, 그 명령들은 architectural state(레지스터·메모리처럼 소프트웨어가 관찰할 수 있는 공식 상태)를 _절대_ 바꾸지 않아야 합니다. 만약 squash 가 불완전해 speculative 결과가 새어 나가면 silent corruption 이 됩니다. 더 나아가, squash 된 speculative load 가 캐시 타이밍 흔적을 남기는 것이 바로 Spectre/Meltdown 의 뿌리입니다(자세히는 [M09](../09_branch_prediction/)).

이 모듈은 "execution 은 자유롭게 뒤섞여도 architectural state 는 in-order 로 보존된다"는 OoO 의 핵심 불변 조건을 세워, 검증의 기대값을 올바로 잡게 합니다.

---

## 2. Intuition — 식당 주방, 과 한 장 그림

:::tip[💡 한 줄 비유]
**OoO 실행** ≈ **재료가 준비된 요리부터 만드는 주방**.<br>
주문(program order)은 순서대로 들어오지만, 셰프는 재료(operand)가 준비된 요리부터 만든다(out-of-order issue). 그러나 _서빙_(retire)은 반드시 주문 순서대로 — 손님은 순서대로 받는다. ROB(Reorder Buffer)가 이 "만든 순서 ≠ 내보내는 순서"를 관리하는 대기 트레이다.
:::
### 한 장 그림 — dispatch(in-order) → execute(OoO) → retire(in-order)

```d2
direction: right

FE: "**Front-end**\nfetch / decode\nrename"
DISP: "**Dispatch (in-order)**\nROB 진입\nRS 배정"
RS: "**Reservation Stations**\noperand 준비된 것부터\nissue (OoO)"
FU: "**Functional Units**\nALU / FPU / LSU"
CDB: "**Common Data Bus**\nresult + tag broadcast"
ROB: "**ROB**\nretire (in-order)\narchitectural state 갱신"

FE -> DISP -> RS -> FU
FU -> CDB: "완료 broadcast"
CDB -> RS: "operand 깨움" { style.stroke-dash: 4 }
FU -> ROB: "결과 적재"
ROB -> ROB: "head 부터 in-order commit"
```

이 그림의 세 부품(RS · CDB · ROB)이 실제로 어떻게 동작하는지는 [M08](../08_tomasulo_rob/)에서 하나씩 뜯어봅니다. 여기서는 _큰 흐름_ — 들어올 땐 순서대로(dispatch), 실행은 준비된 것부터(OoO), 나갈 땐 다시 순서대로(retire) — 만 머리에 새기면 됩니다.

### 왜 이 구조인가 — Design rationale

in-order 파이프라인은 첫 해저드(예: cache miss 로 한 load 가 100 사이클 대기)에서 _뒤따르는 모든 명령_ 이 멈춥니다 — 설령 그 명령들이 독립적이라도. OoO 가 필요한 세 요구는 이렇습니다. 첫째, 멈춘 명령을 건너뛰고 독립적인 명령을 먼저 실행해 functional unit 을 놀리지 않는다 → Reservation Station + 윈도우. 둘째, WAR/WAW 같은 가짜 의존성(이름만 같은 레지스터)이 OoO 를 방해하지 않게 한다 → Register Renaming. 셋째, 그렇게 뒤섞어 실행해도 예외/인터럽트 시 정확한 상태를 복원해야 한다 → ROB 의 in-order retire. 이 셋이 곧 Tomasulo + ROB 의 디자인 결정이며, [M08](../08_tomasulo_rob/)의 주제입니다.

---

## 3. 작은 예 — cache miss 한 load 를 OoO 가 건너뛰는 과정

가장 단순한 시나리오. load 가 캐시 미스로 오래 걸릴 때, in-order 면 뒤의 독립 명령까지 멈추지만 OoO 는 그것을 먼저 실행합니다.

```systemverilog
LW  x1, 0(x2)    // cache miss → 100 사이클 대기
ADD x3, x4, x5   // x1 과 무관 — 독립적
SUB x6, x3, x7   // x3(ADD 결과)에 의존
```

### 단계별 — in-order vs OoO

```d2
direction: down

INORDER: "**In-order**" {
  a: "LW (miss) 100 cyc stall"
  b: "ADD 도 함께 멈춤 (독립인데!)"
  c: "SUB 도 멈춤"
  a -> b -> c
}
OOO: "**OoO**" {
  x: "LW (miss) → RS 에서 대기"
  y: "ADD: operand 준비됨 → 먼저 issue"
  z: "SUB: ADD 결과(CDB) 받고 issue"
  w: "LW 완료 → CDB broadcast"
  x -> w: "100 cyc 뒤"
  x -> y: "동시에 진행"
  y -> z
}
```

### 단계별 의미

| Step | 무엇이 일어나나 | 어느 메커니즘 |
|---|---|---|
| LW miss | LW 가 RS 에 머물며 데이터 대기 | Reservation Station 버퍼링 |
| ADD issue | LW 와 무관 → operand 준비 즉시 실행 | OoO issue (윈도우 스캔) |
| SUB 깨움 | ADD 가 CDB 로 `x3`+tag broadcast → SUB 의 RS 가 capture | Common Data Bus |
| retire | LW→ADD→SUB 순서로 ROB head 부터 commit | ROB in-order retire |

핵심: ADD/SUB 가 LW 보다 _먼저 실행_ 되어도, ROB 는 LW→ADD→SUB 의 program order 로 retire 하므로 architectural state 는 in-order 로 보존됩니다.

:::note[여기서 잡아야 할 두 가지]
**(1) issue 는 OoO, retire 는 in-order.** 둘을 분리하는 것이 ROB 의 존재 이유 — 검증 기대값은 항상 retire(=program) 순서.<br>
**(2) CDB 는 "완료 결과 + tag" 를 방송한다.** 그 tag 를 기다리던 모든 RS 가 동시에 operand 를 채운다 — UVM M05 의 broadcast(analysis port)와 닮은 publish/subscribe 구조.
:::
---

## 4. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 — 'OoO 코어는 결과(architectural state)도 순서 없이 내보낸다']
**실제**: execution(issue/완료)은 out-of-order 지만 **retire(commit)는 in-order**. architectural state 는 program order 대로 갱신됩니다. reference model 은 retire 순서로 비교해야 하며, 완료 순서로 비교하면 정상을 mismatch 로 신고합니다.<br>
**왜 헷갈리는가**: "out-of-order" 라는 이름이 _모든 것_ 이 순서 없다고 오해하게 만들어서.
:::
### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| OoO 코어 scoreboard 무더기 mismatch | 완료 순서로 비교(retire 순서 아님) | reference model 의 commit 시점 갱신 |
| 정상 stall 을 버그로 신고(독립 명령이 먼저 끝남) | OoO 의 정상 동작을 비정상으로 오인 | retire 순서 기준 기대 모델과 대조 |

---

## 5. 핵심 정리 (Key Takeaways)

- **OoO 핵심 불변 조건**: issue/execute 는 out-of-order, **retire 는 in-order** → architectural state 는 program order 보존.
- **3단계 골격**: dispatch(in-order) → execute(OoO) → retire(in-order). "들어올 땐 순서대로, 실행은 준비된 것부터, 나갈 땐 다시 순서대로."
- **OoO 의 동기**: in-order 가 첫 해저드(예: cache miss)에서 독립 명령까지 멈추는 낭비를 없애, functional unit 을 놀리지 않는 것.
- **검증 기대값은 항상 retire(=program) 순서** — 가장 흔한 false-mismatch 원인은 완료 순서 비교.

:::caution[실무 주의점]
OoO 코어 reference model 은 _retire 순서_ 로 architectural state 를 갱신해야 한다. 실행이 뒤섞이는 것은 정상이며, 그 자체를 버그로 신고하지 말 것 — 부품 단위의 정확성 검증은 [M08](../08_tomasulo_rob/)에서 다룬다.
:::
### 5.1 자가 점검

:::tip[🤔 Q1 — issue vs retire 순서 (Bloom: Analyze)]
OoO 코어에서 `ADD`(독립)가 cache-miss 한 `LW` 보다 먼저 _실행 완료_ 되었다. scoreboard 는 무엇을 기준으로 비교해야 하며, 그 이유는?
<details>
<summary>정답</summary>

scoreboard 는 _retire(commit) 순서_, 즉 program order 를 기준으로 architectural state 변화를 비교해야 합니다. ADD 가 LW 보다 먼저 실행 완료되어도 ROB 는 LW→ADD 순서로 retire 하므로, 레지스터 파일/메모리의 관찰 가능한 갱신은 program order 대로 일어납니다. 완료 순서로 비교하면 ADD 의 결과가 LW 보다 먼저 반영된 것처럼 보여 정상 동작을 mismatch 로 신고합니다. 이는 ISA(M05)가 architectural state 를 retire 시점 기준으로 정의하고, ROB 가 그 in-order retire 를 보장하기 때문입니다.

</details>
:::
### 5.2 출처

**External**
- Hennessy & Patterson, *Computer Architecture: A Quantitative Approach* — out-of-order execution, instruction window

---

## 다음 모듈

→ [Module 08 — Tomasulo & ROB](../08_tomasulo_rob/): 이 모듈에서 큰 그림으로 본 RS·CDB·ROB 가 실제로 어떤 부품이고, register renaming·free list·RAT·LSQ 가 어떻게 협력해 OoO 를 _정확하게_ 구현하는가.

[퀴즈 풀어보기 →](../quiz/07_ooo_motivation_quiz/)
