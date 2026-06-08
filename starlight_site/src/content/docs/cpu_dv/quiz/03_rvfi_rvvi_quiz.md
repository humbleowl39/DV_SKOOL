---
title: "Quiz — Module 03: RVFI & RVVI"
---

[← Module 03 본문으로 돌아가기](../../03_rvfi_rvvi/)

---

## Q1. (Remember)

`rvfi_valid` 가 1 인 사이클이 의미하는 것은?

- [ ] A. 코어가 reset 에서 해제됐다
- [ ] B. 정확히 한 명령이 retire 됐다
- [ ] C. 메모리 접근이 발생했다
- [ ] D. 인터럽트가 도착했다

<details>
<summary>정답 / 해설</summary>

**B**. `rvfi_valid` 가 1 인 사이클은 _정확히 한 명령이 retire(commit)됐음_ 을 뜻하며, 그 사이클의 다른 RVFI 신호(`rvfi_pc_rdata`, `rvfi_rd_addr/wdata` 등)가 그 명령의 architectural 정보를 담습니다. superscalar 코어는 retire port 마다 valid 를 두어 한 사이클에 여러 명령이 retire 될 수 있습니다. C(메모리)는 `rvfi_mem_*`, D(인터럽트)는 `rvfi_intr` 이 따로 표시합니다.

</details>

## Q2. (Understand)

RVFI 와 RVVI 의 역할 경계를 한 문장으로 구분하면?

<details>
<summary>정답 / 해설</summary>

**RVFI 는 _코어 한 개_ 가 retire 마다 노출하는 신호 인터페이스("이 명령이 무엇을 했나")이고, RVVI 는 그 위에서 _DV 서브시스템 전체_(코어 + reference model + 트레이스 비교)를 묶어 서로 다른 코어·ISS 를 같은 하네스에 꽂게 하는 통합 표준입니다.** RVFI=신호 노출, RVVI=서브시스템 통합으로 계층이 다릅니다. 둘 다 "verification interface"라 헷갈리지만 범위가 다릅니다.

</details>

## Q3. (Apply)

retire monitor 를 작성할 때, 코어 내부 신호(`dut.u_core.u_rf.wr_data`) 대신 RVFI 신호를 보면 구체적으로 무엇이 좋아지는가? 두 가지를 드시오.

<details>
<summary>정답 / 해설</summary>

1. **재사용성**: RVFI 신호명·의미는 표준으로 고정되어, 코어 리비전이나 구현(in-order/OoO)이 바뀌어도 monitor 코드가 불변입니다. 내부 신호는 리비전마다 경로·이름이 바뀌어 monitor 가 즉시 깨집니다.
2. **의미의 확실성**: RVFI 는 _retire 시점의 확정값_ 을 노출하도록 약속되어 있어, `rvfi_rd_wdata` 가 추측 중간값이 아닌 commit 된 architectural 값임을 신뢰할 수 있습니다. 내부 데이터패스 신호는 추측값이 섞였는지 확신하기 어렵습니다.

(추가로 OoO 코어의 ROB·reservation station 같은 내부 복잡도가 retire 인터페이스 뒤로 숨어 monitor 가 단순해집니다.)

</details>

## Q4. (Apply)

superscalar 코어에서 한 사이클에 두 명령이 retire 될 때, scoreboard 가 _프로그램 순서_ 로 ISS 와 비교하려면 어떤 RVFI 신호를 써야 하는가?

- [ ] A. `rvfi_pc_rdata`
- [ ] B. `rvfi_order`
- [ ] C. `rvfi_trap`
- [ ] D. `rvfi_mode`

<details>
<summary>정답 / 해설</summary>

**B**. `rvfi_order` 는 프로그램 순서를 나타내는 단조 증가 번호로, retire 가 여러 port 로 나뉘어도 비교기가 _프로그램 순서_ 를 복원하게 합니다. superscalar 코어는 retire port 마다 valid 를 두므로, monitor 가 port 별 item 을 만들고 scoreboard 가 `rvfi_order` 로 정렬한 뒤 in-order ISS step 과 맞춰야 합니다. A(PC)는 명령 위치, C(trap)는 예외, D(mode)는 privilege 로 순서 복원과 무관합니다.

</details>

## Q5. (Analyze)

monitor 가 retire 를 하나도 못 보고, coverage·scoreboard 가 전부 0 이다. RVFI 관점에서 가장 먼저 의심할 원인은?

<details>
<summary>정답 / 해설</summary>

**코어가 RVFI 가드(`` `ifdef RISCV_FORMAL `` 등) 없이 빌드되어 `rvfi_valid` 가 아예 토글하지 않을 가능성** 이 가장 큽니다.
- RVFI 신호는 _검증 전용 observability_ 로, 보통 합성에서 제거하기 위해 `ifdef` 가드로 감쌉니다. 검증 빌드에서 이 가드 define 을 안 주면 RVFI 결선이 통째로 빠져 monitor 가 valid 를 영원히 못 봅니다.
- 확인 순서: (1) 코어 빌드에 RVFI define 이 들어갔는지, (2) virtual interface 가 config_db 로 제대로 전달됐는지, (3) `@(posedge clk iff rvfi_valid)` 의 신호 결선이 맞는지.
- coverage·scoreboard 가 _모두_ 0 이라는 "전면적" 증상은 특정 명령 버그가 아니라 _retire stream 자체가 안 들어온다_ 는 신호이므로, RVFI 빌드/결선부터 봅니다.

</details>

## Q6. (Evaluate)

"우리는 RVFI 만 구현하면 서로 다른 두 코어를 같은 step-and-compare 하네스에 그대로 꽂을 수 있다"는 주장을 평가하라.

<details>
<summary>정답 / 해설</summary>

**부분적으로만 맞다 — RVFI 는 신호 _노출_ 을 표준화하지만, 하네스 _통합_ 까지 표준화하는 것은 RVVI 의 역할이다.**
- RVFI 가 양쪽 코어에서 같은 모양이면 retire 정보를 _읽는_ monitor 부분은 상당히 재사용됩니다.
- 그러나 reference model(ISS) 연동 방식, 트레이스 비교 인터페이스, 코어/ISS 교체 지점은 RVFI 범위 밖이며, 이를 표준화한 것이 RVVI(RVVI-TRACE + reference-model API)입니다.
- 즉 "신호는 RVFI, 서브시스템 통합·교체성은 RVVI" — 두 코어를 _진정으로_ 같은 하네스에 마찰 없이 꽂으려면 RVVI 수준의 통합 표준이 함께 있어야 합니다. RVFI 만으로는 monitor 재사용까지이고, 그 이상의 통합은 보장되지 않습니다.

</details>
