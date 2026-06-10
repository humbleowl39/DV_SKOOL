---
title: "Quiz — Module 08: Tomasulo & ROB"
---

[← Module 08 본문으로 돌아가기](../../08_tomasulo_rob/)

---

## Q1. (Remember)

Tomasulo 알고리즘의 세 가지 핵심 메커니즘은?

- [ ] A. L1/L2/L3 캐시
- [ ] B. Reservation Station, Common Data Bus, Register Renaming
- [ ] C. IF, ID, EX
- [ ] D. TLB, PTW, page fault

<details>
<summary>정답 / 해설</summary>

**B**. Reservation Station(RS, functional unit 앞의 operand 대기 슬롯), Common Data Bus(CDB, 완료 결과+tag 를 RS 들에 방송), Register Renaming(물리 레지스터 ≥ architectural 레지스터로 WAR/WAW 가짜 의존성 제거)입니다. A 는 메모리 계층(M10–M12), C 는 파이프라인 단계(M06), D 는 주소 변환(M12)으로 모두 Tomasulo 와 무관합니다.

</details>
## Q2. (Analyze)

가짜 의존성이 전혀 없는 독립 명령들인데도 dispatch 가 멈췄다. ROB 에는 빈 자리가 있다. 무엇을 의심해야 하는가?

- [ ] A. 분기 예측 실패
- [ ] B. 물리 레지스터 파일(PRF) free list 고갈
- [ ] C. 캐시 용량 부족
- [ ] D. 클럭 주파수 저하

<details>
<summary>정답 / 해설</summary>

**B**. renaming 은 목적 레지스터마다 free list 에서 물리 레지스터를 하나 꺼내 쓰고, 그 레지스터는 _이전 매핑을 덮어쓴 명령이 retire 될 때_ 에야 반환됩니다. long-latency 명령(예: cache miss)이 ROB head 를 오래 붙잡으면 그 뒤 명령들이 retire 를 못 해 물리 레지스터를 반환하지 못하고, free list 가 비면 ROB 에 자리가 남아도 새 명령이 목적 레지스터를 못 받아 rename/dispatch 가 멈춥니다. stall 원인이 _의존성_ 이 아니라 _자원 고갈_ 인 경우입니다.

</details>
## Q3. (Understand)

ROB(Reorder Buffer)가 precise exception 을 보장하는 원리를 설명하라.

<details>
<summary>정답 / 해설</summary>

ROB 는 명령을 dispatch 시 _순서대로_ 받아 retire 도 head 부터 _순서대로_ 합니다 — 중간의 실행만 out-of-order 입니다. 예외/인터럽트는 그 명령이 ROB head 에 도달했을 때만 처리하므로, 그 시점에 _그 명령 직전까지_ 의 모든 명령은 이미 retire 되어 architectural state 에 확정 반영됐고, _이후_ 명령은 아직 commit 되지 않아 squash 하면 됩니다. 따라서 예외 처리기는 "정확히 offending 명령 직전" 상태를 보게 되어 precise exception 이 성립합니다. ROB 없이 OoO 결과가 곧바로 architectural state 를 갱신하면 예외 시점의 상태가 뒤섞여 imprecise 해집니다.

</details>
## Q4. (Apply)

`store [x1]` 다음에 `load [x2]` 가 온다. 이 둘의 의존성을 왜 일반 Reservation Station 으로 판정할 수 없고 LSQ 가 필요한지 적용해 설명하라.

<details>
<summary>정답 / 해설</summary>

ALU 명령의 의존성은 _레지스터 번호_ 로 명령 진입(rename) 시점에 즉시 알 수 있어 RS 의 tag 매칭으로 충분합니다. 그러나 store/load 의 충돌 여부는 x1·x2 가 가리키는 _실제 메모리 주소_ 가 같은지에 달렸고, 그 주소는 명령이 실행되며 늦게 계산됩니다 — 진입 시점에는 알 수 없습니다. 그래서 메모리 명령은 LSQ(LDQ/STQ)에서 프로그램 순서로 추적되며 주소가 확정되는 대로 충돌을 판정(memory disambiguation)하고, 같은 주소면 STQ 에서 load 로 직접 넘기는 store-to-load forwarding 까지 처리합니다. 주소 의존성의 _지연된 확정_ 이 일반 RS 와 LSQ 를 가르는 핵심입니다.

</details>
