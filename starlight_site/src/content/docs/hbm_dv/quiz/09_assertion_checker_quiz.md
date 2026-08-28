---
title: "Quiz — Ch09: Assertion · Protocol Checker"
---

[← Ch09 본문으로 돌아가기](../../09_assertion_checker/)

---

## Q1. (Remember)

규칙을 수단에 배정하는 세 성격 분류로 옳은 것은?

- [ ] A. 기능 / 성능 / 신뢰성
- [ ] B. 사이클 단위 시간 관계 / 트랜잭션 단위 대응 / 장기 상태·집합 관계
- [ ] C. 필수 / 권장 / 선택
- [ ] D. IP / Subsystem / Full-chip

<details>
<summary>정답 / 해설</summary>

**B**. 각각 **SVA / Scoreboard / 절차적 checker**에 대응합니다.

**규칙과 assertion은 1:1이 아니며**, 성격에 따라 수단이 정해집니다.

</details>

## Q2. (Understand)

Assertion을 **`bind`로 결합**하는 이유는?

- [ ] A. 시뮬레이션이 빨라진다
- [ ] B. 설계 코드를 수정하지 않는다
- [ ] C. 문법이 간단하다
- [ ] D. 커버리지가 자동 수집된다

<details>
<summary>정답 / 해설</summary>

**B**. 검증이 설계 코드를 건드리지 않는 것은 기본 원칙이며, **RTL 변경 없이 checker를 켜고 끌 수 있다**는 실용적 이점도 있습니다.

</details>

## Q3. (Apply)

다음 세 규칙에 (가) SVA / (나) Scoreboard / (다) 절차적 checker 중 무엇을 배정합니까?

> **(A)** R10 — 응답 beat 수 = `len+1`, 마지막에만 `rsp_last`
> **(B)** R11 — 응답 순서는 달라도 되나 같은 id의 beat는 순서 유지
> **(C)** R3 — `row_cmd_valid && col_cmd_valid`면 `row_pc == col_pc`

<details>
<summary>정답 / 해설</summary>

**(A) → (나) Scoreboard**, 일부는 SVA로 보강

beat 수는 **트랜잭션이 끝나야** 판정 가능합니다. monitor가 미해결 테이블에서 beat를 모으므로 완성 시점에 `rdata.size() == len+1`을 확인합니다.

*SVA 보강*: *"마지막 beat에서만 `rsp_last`"* 는 사이클 단위 성질이므로, `rsp_last` 뒤에 같은 id의 beat가 더 오는 상황을 SVA로 잡습니다. **한 규칙이 두 수단에 걸치는 사례**입니다.

**(B) → (다) 절차적**

R11은 **허용을 규정**합니다 — "순서가 달라도 된다". **허용은 assert할 것이 없습니다.**

실제로 검사할 것은 그 안에 숨은 **제약**입니다 — 같은 id의 beat 순서, 응답이 미해결 요청에 대응(R9). 둘 다 집합·테이블 관리가 필요하므로 절차적입니다.

**(C) → (가) SVA**

같은 사이클의 조건 관계이므로 SVA 한 줄로 표현됩니다. 이 IP의 핵심 규칙입니다.

> **규칙 문장에서 "~해야 한다"(제약)와 "~할 수 있다"(허용)를 구분하세요. 허용은 검사 대상이 아니며, 그 안에 숨은 제약을 찾아야 합니다.**

</details>

## Q4. (Analyze)

타이밍 기준값(`tRCD_CYC`)을 **DUT의 CSR 레지스터에서 직접 읽어** assertion에 쓰면 어떤 위험이 있습니까?

<details>
<summary>정답 / 해설</summary>

**DUT가 설정을 잘못 저장하면 assertion도 함께 틀립니다.**

`tRCD_CYC`를 16으로 썼는데 DUT가 8로 저장했다고 합시다. Assertion이 DUT의 레지스터를 참조하면 **기준도 8이 되어**, DUT가 8 간격으로 동작해도 위반이 아닙니다. **설정을 무시한 결함이 그대로 통과합니다.**

**이것은 Ch03의 함정과 같은 구조입니다** — monitor가 driver의 item을 재사용하면 DUT의 오해석을 못 잡는 것과 동일합니다. 검증 기준이 **검증 대상에서 나오면** 비교가 성립하지 않습니다.

**권장**: **테스트벤치가 기대하는 값을 주입**합니다. 그리고 *"DUT의 CSR 값이 TB 기대값과 일치하는가"* 를 **별도 항목**으로 확인합니다.

**같은 원칙의 세 형태** (코스 전체):
- Ch03 — monitor가 driver item을 재사용하면 안 된다
- Ch09 — assertion 기준값을 DUT CSR에서 읽으면 안 된다
- Ch11 — 검증 기준을 RTL에서 가져오면 안 된다

</details>

## Q5. (Analyze)

**Vacuous assertion**이란 무엇이며, 왜 위험합니까? 그리고 어떻게 방지합니까?

<details>
<summary>정답 / 해설</summary>

**전제(antecedent)가 시뮬레이션 중 한 번도 참이 되지 않아 실질적으로 평가되지 않은 채 통과로 집계되는 assertion입니다.**

**왜 위험한가**: **증상이 없습니다.** 리포트에 "0 failures"가 찍히고, 그 규칙이 검증된 것처럼 보입니다. R3처럼 **특정 동시성 조건이 필요한 규칙일수록** 위험합니다 — 시나리오가 그 조건을 만들지 못하면 assertion은 **놀고 있으면서 일하는 것처럼** 보입니다.

이것이 **assertion 판의 "조용한 통과"** 입니다.

**방지**: **모든 assertion에 전제 발생을 확인하는 cover property를 짝짓습니다.**

```systemverilog
a_ca_share: assert property (p_ca_share) else `uvm_error(...)
c_ca_share_exercised: cover property (row_cmd_valid && col_cmd_valid);
```

그리고 회귀 리포트에서 **assertion 통과와 cover 충족을 함께** 봅니다.

> **cover가 비어 있으면 V-Plan 상태는 "통과"가 아니라 "미측정"입니다** (Ch07).

</details>

## Q6. (Evaluate)

회귀 리포트입니다.

> ```
> a_req_valid_stable  PASS (12,483 hits)    c_ca_share_exercised   0%
> a_ca_share          PASS (0 hits)         c_test_mode_entered    0%
> a_trcd              PASS (8,201 hits)     c_trcd_values        100%
> a_test_mode_quiet   PASS (0 hits)
> ```

(a) 실제로 검증된 규칙은? (b) 원인은 어디에 있습니까? (c) 무엇을 해야 합니까?

<details>
<summary>정답 / 해설</summary>

**(a) R1(핸드셰이크)과 R6(tRCD) 두 가지뿐입니다.**

`a_ca_share`와 `a_test_mode_quiet`는 **PASS인데 hits가 0**이고 cover도 0%입니다. **R3와 R18은 미검증**입니다.

cover property가 없었다면 이 리포트는 *"assertion 4개 전부 통과"* 로 읽혔을 것입니다.

**(b) 원인은 assertion이 아니라 시나리오에 있습니다.**

- `c_ca_share_exercised` 0% → row/col 커맨드가 **동시에 발행되는 상황이 만들어지지 않았습니다.** 후보: 미해결 요청이 안 쌓임(driver가 blocking?), 트래픽이 한 pc에 몰림, 뱅크 다양성 부족
- `c_test_mode_entered` 0% → **테스트 모드 시나리오를 돌리지 않았습니다.** Ch08에서 예고한 "뒤로 밀리는" 시나리오가 실제로 밀린 것입니다

**Assertion은 정상입니다. 자극이 없었을 뿐입니다.**

**(c) 네 가지**

1. **V-Plan 상태를 정정한다** — R3·R18 행을 "통과"에서 **"미측정"** 으로. **이것이 가장 먼저입니다.** 잘못된 상태가 보고에 남으면 나머지 판단이 전부 어긋납니다
2. **시나리오를 만든다** — 동시 요청이 쌓이는 부하 시나리오, 두 pc 분산 트래픽, 테스트 모드 진입·복귀
3. **cover를 회귀 게이트에 넣는다** — assertion 통과만으로 통과시키지 않고 **핵심 규칙의 cover 충족을 조건으로** 겁니다
4. **`c_trcd_values` 100%도 다시 본다** — 이 cover는 "column 커맨드가 발행됨"만 확인합니다. **여러 tRCD 값에서** 발행됐는지는 알 수 없습니다. cover 정의 자체가 충분한지 점검이 필요합니다

> **Assertion을 잘 쓰는 것과 그것이 일하게 만드는 것은 다른 문제입니다.**

</details>
