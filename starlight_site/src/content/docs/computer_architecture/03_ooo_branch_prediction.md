---
title: "Module 03 — OoO 실행 & 분기 예측"
---

:::tip[학습 목표]
이 모듈을 마치면:

- **Explain** in-order 실행이 첫 해저드에서 멈추는 한계와, OoO(out-of-order) 실행이 명령 윈도우에서 준비된 명령부터 issue 하는 원리를 설명할 수 있다.
- **Describe** Tomasulo 알고리즘의 세 메커니즘(Reservation Station, Common Data Bus, Register Renaming)이 어떻게 협력하는지 기술할 수 있다.
- **Differentiate** ROB 가 execution 의 out-of-order 와 retirement 의 in-order 를 분리해 precise exception 과 speculation 을 가능케 함을 구분할 수 있다.
- **Compare** 정적/동적 분기 예측기(2-bit, local/global history, tournament, TAGE)를 정확도·비용 기준으로 비교할 수 있다.
- **Evaluate** speculative execution 이 성능을 주면서 동시에 Spectre/Meltdown 류 side-channel 을 낳는 trade-off 를 평가할 수 있다.
:::
:::note[사전 지식]
- [Module 02 — Pipeline & Hazard](../02_pipeline_hazard/) (RAW/WAR/WAW, 분기 페널티)
- [Module 01 — ISA & RISC-V](../01_isa_riscv/) (architectural state, retire)
:::
---

## 1. Why care? — execution 순서와 retirement 순서를 혼동하면 기대값이 틀린다

### 1.1 시나리오 — "결과가 순서 없이 나왔다"는 착각

OoO 코어를 검증할 때 가장 흔한 함정은 _실행 순서_ 와 _완료(retire) 순서_ 를 혼동하는 것입니다. OoO 코어는 명령을 program order 와 다르게 실행하지만, architectural state(레지스터·메모리의 관찰 가능한 값)는 반드시 program order 대로 갱신합니다. reference model 을 만들 때 "OoO 니까 결과도 순서 없이 비교하자"고 하면, 정상 동작을 mismatch 로 신고하게 됩니다. 올바른 기대값은 항상 _retire 순서 = program order_ 기준입니다.

또 다른 함정은 분기 예측과 speculation 입니다. 코어가 예측 경로의 명령을 미리 실행했다가 misprediction 으로 squash 하면, 그 명령들은 architectural state 를 _절대_ 바꾸지 않아야 합니다. 만약 squash 가 불완전해 speculative 결과가 새어 나가면 silent corruption 이 됩니다. 더 나아가, squash 된 speculative load 가 캐시 타이밍 흔적을 남기는 것이 바로 Spectre/Meltdown 의 뿌리입니다.

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

### 왜 이 구조인가 — Design rationale

in-order 파이프라인은 첫 해저드(예: cache miss 로 한 load 가 100 사이클 대기)에서 _뒤따르는 모든 명령_ 이 멈춥니다 — 설령 그 명령들이 독립적이라도. OoO 가 필요한 세 요구는 이렇습니다. 첫째, 멈춘 명령을 건너뛰고 독립적인 명령을 먼저 실행해 functional unit 을 놀리지 않는다 → Reservation Station + 윈도우. 둘째, WAR/WAW 같은 가짜 의존성(이름만 같은 레지스터)이 OoO 를 방해하지 않게 한다 → Register Renaming. 셋째, 그렇게 뒤섞어 실행해도 예외/인터럽트 시 정확한 상태를 복원해야 한다 → ROB 의 in-order retire. 이 셋이 곧 Tomasulo + ROB 의 디자인 결정입니다.

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
**(2) CDB 는 "완료 결과 + tag" 를 방송한다.** 그 tag 를 기다리던 모든 RS 가 동시에 operand 를 채운다 — M05 의 broadcast(analysis port)와 닮은 publish/subscribe 구조.
:::
---

## 4. 일반화 — Tomasulo, ROB, 분기 예측 계층

### 4.1 Tomasulo 의 세 메커니즘

Tomasulo 알고리즘(원래 IBM System/360 FPU 용)은 세 부품으로 OoO 를 구현합니다. **Reservation Station(RS)** 은 각 functional unit 앞의 대기 슬롯으로, dispatch 된 명령은 소스 operand 가 준비되거나 생산 명령의 tag 로 표시된 채 RS 에서 기다립니다. **Common Data Bus(CDB)** 는 functional unit 이 완료 시 결과와 tag 를 방송하는 버스로, 그 tag 를 감시하던 모든 RS 가 값을 capture 해 operand 를 ready 로 표시합니다. **Register Renaming** 은 물리 레지스터를 architectural 레지스터보다 많이 두고, rename 단계에서 각 목적 architectural 레지스터를 빈 물리 레지스터에 매핑해 rename 경계에서 WAW/WAR 해저드를 _제거_ 합니다.

| 메커니즘 | 해결하는 문제 | 비유 |
|---|---|---|
| Reservation Station | 멈춘 명령이 뒤를 막지 않게 | 재료 대기 주문 슬롯 |
| Common Data Bus | 결과를 기다리는 모든 명령에 동시 전달 | 주방 호출 방송 |
| Register Renaming | 이름만 같은 가짜 의존성(WAR/WAW) 제거 | 같은 이름 손님에 다른 번호표 |

### 4.2 ROB — precise exception 과 speculation

현대 프로세서는 **Reorder Buffer(ROB)** 를 더해 precise exception 과 speculative execution 을 지원합니다. 명령은 dispatch 시 _순서대로_ ROB 에 들어가고 _순서대로_ retire(commit)합니다 — 중간의 실행만 out-of-order 입니다. 분기 misprediction 이나 예외가 발생하면 ROB 에서 그 명령 _이후_ 의 모든 것을 squash 해 architectural state 의 일관성을 유지합니다.

```d2
direction: right

ROB: "**ROB (순환 큐)**" {
  head: "head → retire(in-order)"
  mid: "middle: 실행 완료/진행 중(OoO)"
  tail: "tail ← dispatch(in-order)"
}
EXC: "예외/misprediction"
EXC -> ROB: "offending 이후 전부 squash"
```

### 4.3 분기 예측 — 정확도 사다리

분기를 잘못 예측하면 파이프라인을 flush 해야 하고(현대 깊은 파이프라인에서 페널티 10–20 사이클), 그래서 정확한 예측이 IPC 유지의 핵심입니다.

| 예측기 | 원리 | 대략 정확도 |
|---|---|---|
| Static (predict not/taken) | 항상 한 방향; 컴파일러 힌트 | ~60–70% |
| 2-bit saturating counter | 분기별 2-bit 상태기(SN→WN→WT→ST); 1회 오답에 안 뒤집힘 | 단일 anomaly 내성 |
| Local / Global history | BHR(최근 N 분기 결과) + PHT 인덱싱 | 패턴 의존 분기 포착 |
| Tournament (hybrid) | local/global 두 sub-predictor 가 경쟁, meta-predictor 가 분기별 선택 | DEC Alpha 21264 |
| TAGE | 기하급수적 history length 의 다중 태그 테이블 | SPEC CPU >95% |

```d2
direction: right

SN: "Strongly\nNot Taken"
WN: "Weakly\nNot Taken"
WT: "Weakly\nTaken"
ST: "Strongly\nTaken"

SN -> WN: "taken"
WN -> SN: "not taken"
WN -> WT: "taken"
WT -> WN: "not taken"
WT -> ST: "taken"
ST -> WT: "not taken"
```

2-bit saturating counter 의 핵심 가치는 _한 번의 예외적 결과로 예측을 뒤집지 않는_ 것입니다 — 대부분 taken 인 루프 분기가 마지막 iteration 에서 한 번 not-taken 이어도 예측을 유지해, 다음 루프 진입 시 다시 옳게 맞춥니다.

### 4.4 Speculative execution

깊은 OoO 파이프라인과 분기 예측으로, 프로세서는 _미해결 분기 너머_ 의 명령을 예측이 맞다는 가정하에 실행합니다. 결과는 ROB 에 보관되고 분기가 옳게 해결될 때만 commit 됩니다. 예측이 틀리면 misprediction 이 branch resolution(EX 또는 전용 분기 유닛)에서 검출되고, ROB 의 해당 분기 이후 명령이 모두 squash 되며, fetch 가 올바른 target 부터 재개됩니다.

---

## 5. 디테일 — squash 의 정확성, side-channel, DV 관점

### 5.1 squash 가 architectural state 를 건드리면 안 되는 이유

speculative 명령은 ROB 에 결과를 _격리_ 한 채 commit 전까지 architectural state(레지스터 파일·메모리)를 바꾸지 않아야 합니다. 그래야 misprediction 시 단순히 ROB 항목만 버리면(squash) 상태가 깨끗이 복원됩니다. 만약 speculative store 가 메모리에 일찍 반영되거나 speculative 결과가 architectural 레지스터에 새면, 잘못된 경로의 효과가 영구화되어 silent corruption 이 됩니다. 검증에서는 "misprediction 직후 architectural state 가 분기 직전과 동일한가"를 반드시 확인해야 합니다.

### 5.2 Spectre/Meltdown — speculation 의 어두운 면

같은 squash-on-misprediction 메커니즘이 side-channel 취약점의 뿌리입니다. squash 된 speculative load 라도 그 데이터를 캐시에 끌어왔다면 _캐시 타이밍 흔적_ 은 지워지지 않습니다. 공격자는 이 타이밍 차이로 squash 된 명령이 만진 비밀 값을 역추론합니다. 즉 architectural state 는 복원되어도 micro-architectural state(캐시 점유)는 복원되지 않는다는 비대칭이 핵심입니다.

### 5.3 DV 관점 — OoO 코어 검증의 기대값 모델

OoO 코어 검증에서 reference model 은 항상 **retire 순서 = program order** 로 architectural state 를 갱신해야 하며, scoreboard 는 실행 완료 순서가 아니라 retire 순서로 비교합니다. WAR/WAW 가 renaming 으로 제거되었는지, CDB forwarding 이 올바른 tag 로 깨우는지, misprediction squash 가 완전한지가 핵심 coverage 입니다. 이는 OoO 응답을 가진 프로토콜의 scoreboard(예: AXI ID 별 큐, [UVM M05](../../uvm/05_tlm_scoreboard_coverage/))와 동일한 사고 — "도착(완료) 순서로 비교하지 말고 의미 있는 순서(retire/ID)로 매칭하라".

---

## 6. 흔한 오해 와 DV 디버그 체크리스트

### 흔한 오해

:::danger[❓ 오해 1 — 'OoO 코어는 결과(architectural state)도 순서 없이 내보낸다']
**실제**: execution(issue/완료)은 out-of-order 지만 **retire(commit)는 in-order**. architectural state 는 program order 대로 갱신됩니다. reference model 은 retire 순서로 비교해야 하며, 완료 순서로 비교하면 정상을 mismatch 로 신고합니다.<br>
**왜 헷갈리는가**: "out-of-order" 라는 이름이 _모든 것_ 이 순서 없다고 오해하게 만들어서.
:::
:::danger[❓ 오해 2 — 'misprediction 이면 그냥 fetch 만 다시 하면 된다']
**실제**: fetch 재개뿐 아니라 ROB 의 해당 분기 _이후_ 모든 speculative 명령을 squash 하고 RS 를 drain 해야 합니다. squash 가 불완전하면 잘못된 경로 결과가 architectural state 에 새어 silent corruption.<br>
**왜 헷갈리는가**: "예측 실패 = 다시 시작" 이라는 단순 모델이 squash 범위를 과소평가해서.
:::
:::danger[❓ 오해 3 — 'speculation 이 squash 되면 흔적이 전혀 안 남는다']
**실제**: architectural state 는 복원되지만 **micro-architectural state(캐시 점유)는 복원되지 않습니다**. squash 된 speculative load 가 끌어온 캐시 라인의 타이밍 흔적이 Spectre/Meltdown 의 누출 경로입니다.<br>
**왜 헷갈리는가**: "취소 = 완전 원상복구" 라는 가정이 캐시 부수효과를 빠뜨려서.
:::
### DV 디버그 체크리스트

| 증상 | 1차 의심 | 어디 보나 |
|---|---|---|
| OoO 코어 scoreboard 무더기 mismatch | 완료 순서로 비교(retire 순서 아님) | reference model 의 commit 시점 갱신 |
| 이름만 같은 레지스터에서 가짜 의존 stall | register renaming 미동작 | rename 테이블, free list |
| CDB 로 깨워야 할 명령이 영원히 대기 | tag 매칭 오류 또는 CDB broadcast 누락 | RS tag 비교, CDB 연결 |
| misprediction 후 stale 결과가 살아남음 | squash 범위 오류(분기 이후 일부만 버림) | ROB squash 인덱스, RS flush |
| 예외 후 architectural state 부정확 | precise exception 미보장(in-order retire 깨짐) | ROB head 부터 commit, 예외 표시 |

---

## 7. 핵심 정리 (Key Takeaways)

- **OoO 핵심 불변 조건**: issue/execute 는 out-of-order, **retire 는 in-order** → architectural state 는 program order 보존.
- **Tomasulo 3 부품**: RS(멈춘 명령이 뒤를 안 막게), CDB(결과+tag 방송), Register Renaming(WAR/WAW 제거).
- **ROB** 가 OoO execution 과 in-order retire 를 분리 → precise exception + speculation 가능.
- **분기 예측 사다리**: static(60–70%) → 2-bit(anomaly 내성) → history → tournament → TAGE(>95%).
- **Speculation** 은 미해결 분기 너머를 실행; misprediction 시 ROB squash + fetch 재개.
- **squash 는 architectural state 만 복원**, micro-architectural(캐시 흔적)은 남아 Spectre/Meltdown 의 뿌리.

:::caution[실무 주의점]
- OoO 코어 reference model 은 _retire 순서_ 로 갱신 — 가장 흔한 false-mismatch 원인은 완료 순서 비교.
- misprediction squash 의 _범위 완전성_ 을 타겟 테스트로 검증(예측 오류 직후 분기 직전 상태 동일성 확인).
- AXI 등 OoO 프로토콜 scoreboard 의 per-ID 매칭(UVM M05)과 동일한 사고를 코어 검증에 적용.
:::
### 7.1 자가 점검

:::tip[🤔 Q1 — issue vs retire 순서 (Bloom: Analyze)]
OoO 코어에서 `ADD`(독립)가 cache-miss 한 `LW` 보다 먼저 _실행 완료_ 되었다. scoreboard 는 무엇을 기준으로 비교해야 하며, 그 이유는?
<details>
<summary>정답</summary>

scoreboard 는 _retire(commit) 순서_, 즉 program order 를 기준으로 architectural state 변화를 비교해야 합니다. ADD 가 LW 보다 먼저 실행 완료되어도 ROB 는 LW→ADD 순서로 retire 하므로, 레지스터 파일/메모리의 관찰 가능한 갱신은 program order 대로 일어납니다. 완료 순서로 비교하면 ADD 의 결과가 LW 보다 먼저 반영된 것처럼 보여 정상 동작을 mismatch 로 신고합니다. 이는 ISA(M01)가 architectural state 를 retire 시점 기준으로 정의하고, ROB 가 그 in-order retire 를 보장하기 때문입니다.

</details>
:::
:::tip[🤔 Q2 — speculation 의 비대칭 (Bloom: Evaluate)]
"misprediction 이 정확히 복구되는데 왜 Spectre 같은 누출이 가능한가?"를 architectural vs micro-architectural state 로 평가하라.
<details>
<summary>정답</summary>

squash 는 architectural state(레지스터·메모리의 관찰 가능한 값)만 program order 로 복원합니다 — 잘못 실행된 speculative 명령의 결과는 ROB 에서 버려져 영구화되지 않습니다. 그러나 그 명령이 실행 중 만진 micro-architectural state, 특히 캐시에 끌어온 라인은 squash 로 _제거되지 않습니다_. 공격자는 이후 캐시 hit/miss 의 타이밍 차이로 squash 된 speculative load 가 접근한 비밀 값을 역추론합니다. 즉 정확성(correctness)은 architectural 레벨에서 보장되지만 비밀성(confidentiality)은 micro-architectural 부수효과에서 깨집니다 — 성능을 위한 speculation 이 만든 보안 trade-off 입니다.

</details>
:::
### 7.2 출처

**Internal (HDG Wiki)**
- `common/computer_architecture_spec.md` §4.1 (Superscalar), §4.2 (Tomasulo / ROB), §4.3 (Branch Prediction), §4.4 (Speculative Execution / Spectre·Meltdown)

**External**
- Hennessy & Patterson, *Computer Architecture: A Quantitative Approach* — Tomasulo, ROB, dynamic branch prediction, speculation
- Seznec & Michaud, *A case for (partially) TAgged GEometric history length branch prediction* — TAGE

---

## 다음 모듈

→ [Module 04 — 메모리 계층 (Cache & DRAM)](../04_memory_hierarchy/): OoO 가 cache miss 한 load 를 _건너뛸 수_ 있어도, 그 miss 자체를 줄이는 것은 메모리 계층의 몫이다. 캐시 조직과 DRAM 의 row hit/miss 가 어떻게 Memory Wall 을 완화하는가.

[퀴즈 풀어보기 →](../quiz/03_ooo_branch_prediction_quiz/)
