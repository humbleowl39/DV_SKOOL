---
title: "Quiz — 07: Hands-on 즉석 작성"
pagefind: false
---

본 모듈의 핵심 개념 이해도를 점검합니다. 정답은 펼치면 보입니다.

[← 07장 본문으로 돌아가기](../../07_handson_writing/)

---

## Q1. (Understand)

즉석 작성 구간에서 실제로 채점되는 것 네 가지는? 그리고 가장 흔한 실패는?

<details>
<summary>정답 / 해설</summary>

**채점 항목**: ① **순서**(구조를 먼저 잡는가) ② **근거**(각 줄이 무엇을 막는지 말하는가) ③ **누락 인지**(다 못 써도 "여기에 X가 더 필요합니다"를 말하는가) ④ **자기 검토**(다 쓰고 스스로 구멍을 찾는가).

**가장 흔한 실패**: **침묵하며 코드만 치는 것.** 면접관은 화면이 아니라 설명을 듣고 있다. 한 블록 쓸 때마다 한 문장씩 말해야 한다. 세미콜론이 빠지는 것보다 침묵이 훨씬 큰 감점이다.

</details>

## Q2. (Analyze)

다음 assertion만 작성하고 끝냈을 때의 문제와, 반드시 함께 써야 할 것은?

```systemverilog
a_ca_share: assert property (
  @(posedge clk) disable iff (!rst_n)
  (row_cmd_valid && col_cmd_valid) |-> (row_pc == col_pc)
);
```

<details>
<summary>정답 / 해설</summary>

**문제**: `row_cmd_valid && col_cmd_valid`가 시뮬레이션 중 **한 번도 참이 되지 않으면** 이 assertion은 전부 통과로 집계된다(**vacuous pass**). 로그에 실패가 없고 assertion 개수도 늘어나지만 실제로는 아무것도 검사하지 않았다.

**함께 써야 할 것** — 선행 조건에 대한 cover property:

```systemverilog
c_ca_share_exercised: cover property (
  @(posedge clk) disable iff (!rst_n) (row_cmd_valid && col_cmd_valid)
);
```

원칙: **assertion 하나에 cover property 하나.** 이게 없으면 assertion 개수는 안심의 근거가 되지 못한다.

</details>

## Q3. (Apply)

"ACT 이후 tRCD 동안 같은 뱅크에 column 커맨드가 오면 안 된다"를 SVA로 쓸 때, `$past` 대신 **local variable**을 쓰는 이유는?

<details>
<summary>정답 / 해설</summary>

`$past`로 과거 값을 되짚으면 **시점이 어긋나기 쉽다** — 평가 시점이 시퀀스 진행에 따라 이동하므로 어느 클럭의 값을 참조하는지 추론이 어려워진다. Local variable은 **선행 조건이 성립한 그 순간의 값을 캡처**해 고정한다.

```systemverilog
property p_trcd;
  bit [BANK_W-1:0] b;
  @(posedge clk) disable iff (!rst_n)
  (act_valid, b = act_bank) |=> (!(col_valid && col_bank == b))[*TRCD-1];
endproperty
```

덧붙일 것 — cover는 **경계값**(정확히 tRCD 후)이 실제로 발생했는지를 본다. 여유 있게만 돌면 규칙이 검증된 것이 아니다.

</details>

## Q4. (Evaluate)

채널 동시성 covergroup을 설계할 때, **채널 인덱스만으로 bin을 나누면** 왜 부족한가? 무엇을 축으로 잡아야 하는가?

<details>
<summary>정답 / 해설</summary>

16채널을 각각 bin으로 두면 "모든 채널을 다 써봤다"는 100%가 나온다. 그러나 실제 결함은 **CA 버스를 공유하는 pseudo-channel 쌍의 동시 요청**에서 발생하며, **동시성 축이 bin에 없으면 그 조합은 원리적으로 관측되지 않는다.**

따라서 **동시성 자체를 축으로** 잡는다:

```systemverilog
cp_concur: coverpoint {row_v, col_v} {
  bins none = {2'b00}; bins row_only = {2'b10};
  bins col_only = {2'b01}; bins both = {2'b11};   // ← 결함이 사는 곳
}
```

그리고 동시 발행일 때의 pc 쌍을 `iff`로 한정해 cross한다. `iff`를 안 걸면 의미 없는 조합이 채워진다. 순서 의존 결함을 위해 **전이 bin**`(CMD_ROW => CMD_COL)`도 넣는다.

</details>

## Q5. (Analyze)

다음 제약에서 `solve size before addr`이 **없으면** 분포가 어떻게 편향되는가?

```systemverilog
constraint c_size  { size inside {1, 2, 4, 8}; }
constraint c_align { addr % size == 0; }
```

<details>
<summary>정답 / 해설</summary>

**size가 1로 쏠린다.** solver가 addr을 먼저 정하면, 정해진 addr이 홀수일 때 `addr % size == 0`을 만족하는 size는 1밖에 없다. addr 값의 절반이 홀수이므로 size=1의 확률이 급격히 커진다. 4나 8 같은 큰 전송은 거의 나오지 않아 해당 corner가 검증되지 않는다.

`solve size before addr`은 solver에게 **size를 먼저 균등하게 고르고 그에 맞는 addr을 찾으라**고 지시해 이 편향을 제거한다.

"분포가 편향돼서"까지는 많이 말하지만 **왜 그 방향으로** 편향되는지를 해 공간으로 설명하는 지원자는 드물다 — 여기서 확실히 구분된다.

</details>

## Q6. (Create)

두 pseudo-channel의 CA 버스 경합 시나리오를 만드는 virtual sequence의 **핵심 한 줄**은 무엇이며, 그와 함께 반드시 덧붙여야 할 설명은?

<details>
<summary>정답 / 해설</summary>

**핵심 한 줄**: `fork ... join` 으로 두 시퀀스를 동시에 기동하는 것.

```systemverilog
fork
  row_s.start(p_sequencer.row_sqr);
  col_s.start(p_sequencer.col_sqr);
join
```

순차로 돌리면 **아무리 시드를 늘려도** 동시 요청은 만들어지지 않는다.

**반드시 덧붙일 설명**: "판정은 이 시퀀스가 하지 않습니다. **self-checking은 scoreboard와 assertion**에 둡니다. 시퀀스 안에서 비교하면 그 검사는 이 시나리오에서만 동작하고 재사용되지 않습니다."

*"체크를 시퀀스에 넣지 않는 이유"* 는 거의 반드시 나오는 꼬리질문이다.

</details>
