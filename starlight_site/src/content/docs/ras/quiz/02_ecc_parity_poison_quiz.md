---
title: "Quiz — Module 02: ECC · Parity · Poison"
---

[← Module 02 본문으로 돌아가기](../../02_ecc_parity_poison/)

---

## Q1. (Remember)

SEC-DED ECC의 정확한 능력은?

- [ ] A. 1-bit 정정, 2-bit 정정
- [ ] B. 1-bit 정정, 2-bit 검출
- [ ] C. 1-bit 검출만, 정정 불가
- [ ] D. 모든 비트 에러 정정

<details>
<summary>정답 / 해설</summary>

**B**. SEC-DED = **Single Error Correction, Double Error Detection** — 1-bit는 정정(SEC), 2-bit는 검출만(DED) 합니다. 3-bit 이상은 보장 밖이라 오정정/미검출이 가능합니다. A는 2-bit까지 정정한다는 오해(SEC-DED는 2-bit 정정 불가), C는 parity 수준의 능력, D는 "ECC=무적"이라는 흔한 오해입니다.

</details>
## Q2. (Understand)

parity 1-bit로 보호된 데이터에서 비트가 정확히 2개 뒤집히면 왜 검출되지 않는지 설명하라.

<details>
<summary>정답 / 해설</summary>

parity는 데이터의 1의 개수가 짝수인지 홀수인지만 검사합니다. 비트 1개가 뒤집히면 1의 개수의 짝/홀이 바뀌어 parity가 어긋나므로 검출됩니다. 그러나 비트 2개가 뒤집히면 1의 개수가 짝→짝(또는 홀→홀)으로 _다시 같은 패리티_ 가 되어, parity 검사가 통과해버립니다. 결과적으로 짝수 개(2, 4, …) 비트 에러는 parity의 사각지대이며, 손상 데이터가 정상으로 통과해 SDC가 됩니다. 그래서 데이터 무결성이 중요한 메모리에는 2-bit까지 검출하는 SEC-DED ECC가 필요합니다.

</details>
## Q3. (Apply)

64-bit register file을 어떻게 보호할지 결정해야 한다. 데이터 무결성이 결정적이고 1-bit 정정이 필요하다면 무엇을 쓰는가? 매 사이클 빠른 검출만 필요한 control FSM에는?

<details>
<summary>정답 / 해설</summary>

데이터 무결성이 결정적이고 정정이 필요한 register file/캐시/메모리 인터페이스에는 **SEC-DED ECC** 를 씁니다 — 1-bit 정정 + 2-bit 검출로 무결성을 복구하고 무검출 손상을 막습니다. 반면 control path/FSM처럼 _빠른 검출만_ 필요하고 정정이 무의미한(상태는 재진입/리셋 가능) 곳에는 저비용 **parity** 가 적합합니다. parity는 1-bit/워드 오버헤드로 실시간 오동작을 검출합니다. 선택 기준은 "정정이 필요한가(→ECC)" vs "검출만으로 충분하고 비용이 중요한가(→parity)"입니다.

</details>
## Q4. (Apply)

UE 데이터에 poison이 set되어 버스로 전파됐다. 이 데이터가 끝내 어떤 실행 유닛에도 소비되지 않았다. 무슨 일이 일어나는가?

- [ ] A. 즉시 시스템 panic
- [ ] B. 아무 일도 일어나지 않음 (시스템 정상)
- [ ] C. 자동으로 ECC가 정정
- [ ] D. 무조건 해당 프로세스 종료

<details>
<summary>정답 / 해설</summary>

**B**. poison(deferred error)의 핵심은 에러 처리를 _데이터 소비 시점까지 미룬다_ 는 것입니다. exception은 poisoned 데이터가 실행 유닛(ALU/NPU)에 의해 실제로 _소비될 때_ 만 발생합니다. 끝내 소비되지 않으면 아무 일도 일어나지 않고 시스템은 정상 동작을 유지합니다. A·D는 "에러 데이터=즉시 처리"라는 오해이고, C는 UE이므로 ECC가 정정할 수 없습니다(2-bit는 검출만). 이 음성 케이스(비소비 시 무사)가 deferred error의 본질을 보여줍니다.

</details>
## Q5. (Analyze)

decoder가 syndrome을 계산했더니 0이 아니고 "단일 비트 위치"를 가리켰다. 다음에 일어나는 일과, syndrome이 "double-error 패턴"일 때의 차이를 분석하라.

<details>
<summary>정답 / 해설</summary>

syndrome은 재계산한 check bits와 저장된 check bits의 XOR로, _어느 비트가 틀렸는가_ 의 좌표 역할을 합니다. **단일 비트 위치를 가리키면(SEC)**: decoder가 그 비트만 flip해 데이터를 정정하고 Corrected Error(CE)로 처리 → 데이터 정상화, 동작 계속. **double-error 패턴이면(DED)**: 단일 비트로 환원되지 않는 syndrome이므로 정정은 포기하고 검출만 해 Uncorrectable Error(UE)로 보고 → poison 태그/exception 경로로 넘어감. 차이의 본질은 "syndrome이 단일 좌표로 해석되는가"입니다 — 단일 좌표면 정정 가능, double 패턴이면 검출만. 3-bit 이상은 SEC-DED 보장 밖이라 syndrome이 잘못된 단일 좌표를 가리켜 오정정할 위험이 있습니다.

</details>
## Q6. (Evaluate)

"ECC가 있으면 poison은 필요 없다"는 주장의 옳고 그름을 판단하라.

<details>
<summary>정답 / 해설</summary>

**틀렸습니다.** ECC와 poison은 서로 다른 기둥의 보완적 메커니즘입니다. ECC(Reliability)는 1-bit를 정정하고 2-bit를 검출하지만, 2-bit(UE)는 _정정하지 못합니다_. 정정 불가능한 UE 데이터를 어떻게 다룰 것인가에서 poison(Availability)이 등장합니다 — UE 데이터를 즉시 panic시키지 않고 태그해 전파하여, 소비 시점까지 가용성을 유지하고 영향 프로세스만 정밀 종료합니다. 즉 ECC는 _검출/정정_ 을, poison은 _정정 불가 데이터의 격리·지연_ 을 담당하므로, ECC만으로는 UE 데이터의 처리 전략(즉시 죽일지 미룰지)을 대신할 수 없습니다. 둘은 에러 한 건을 함께 처리하는 파이프라인의 다른 단계입니다.

</details>
