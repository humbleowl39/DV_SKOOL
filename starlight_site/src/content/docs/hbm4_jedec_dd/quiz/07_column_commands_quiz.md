---
title: "Quiz — 07: Column 커맨드와 저전력"
description: 버스트·지연 관계식·tCCD 3택·저전력 진입 조건 점검
---

[← 07장 본문으로 돌아가기](../../07_column_commands/)

---

## Q1. (Understand)

읽기 데이터를 트리거하는 스트로브는 무엇이며, 그 이유는?

<details>
<summary>정답 / 해설</summary>

> **쓰기 스트로브(WDQS)가 읽기 데이터(DQ, DBI, ECC, SEV)와 읽기 데이터 스트로브를 트리거하는 소스**다. — §6.3.3.2

반직관적이지만 이유는 [05장](../../05_clocking_dbi/)에 있다 — **RDQS는 WDQS에서 생성**되기 때문이다.

**함의**: 컨트롤러는 **읽기 동작 중에도 WDQS를 공급**해야 하며, 그래서 READ 시 WDQS가 **4펄스 preamble + 2펄스 postamble**을 제공해야 한다는 규정이 따라온다.

</details>

## Q2. (Remember)

READ와 WRITE의 preamble/postamble 펄스 수를 스트로브별로 쓰고, 그 값들의 공통점을 지적하라.

<details>
<summary>정답 / 해설</summary>

| 동작 | 스트로브 | pre | post | 합 |
|---|---|---|---|---|
| READ | WDQS | **4** | 2 | **6** |
| READ | RDQS | 2 | 2 | **4** |
| WRITE | WDQS | 2 | 2 | **4** |

**공통점: 모두 짝수다.**

이는 우연이 아니라 [05장](../../05_clocking_dbi/)의 **`WDQS/2` 위상 보존 규칙**을 만족하도록 설계된 값이다. 규격이 preamble/postamble 개수를 **고정**한 것도 같은 이유이며, 이 값들을 임의로 바꾸면 위상이 깨진다.

**부가**: read 버스트의 **첫 데이터 비트는 RDQS의 세 번째 상승 에지**와 동기된다 — RDQS preamble이 2펄스이므로 자연스러운 귀결이다.

</details>

## Q3. (Analyze) ★

12-High 구성에서 연속 READ를 발행한다. 첫 READ는 `SID=0`·뱅크 5(Group A), 두 번째는 `SID=1`·뱅크 20(Group C)이다. 어떤 파라미터가 적용되는가?

<details>
<summary>정답 / 해설</summary>

- 뱅크 그룹: 5 → Group A, 20 → Group C. **다른 그룹**
- SID: 0 → 1. **다른 SID**

따라서 **`tCCDR`** 이 적용된다. `tCCDS`가 아니다.

**값의 성격**(§10 Note 17): `tCCDR(min)`은 **벤더 지정**이며 **`tCCDS + 1` ~ `2 nCK`** 범위이고 **주파수 의존적**이다. 즉 `tCCDS`보다 **길다.**

**함정 셋**:
1. 뱅크 그룹만 비교하는 로직은 `tCCDS`를 적용해 간격을 **과소 산정**한다.
2. 이 위반은 **서로 다른 SID로 가는 seamless READ에서만** 나타나므로 **4-High 구성 테스트에서는 재현되지 않는다.**
3. 같은 시퀀스가 **WRITE**였다면 `tCCDS`가 적용된다 — **SID 의존성은 READ에만** 있다.

</details>

## Q4. (Evaluate)

CA parity가 켜진 상태에서 `MRS`로 비활성화했다. 그 직후 발행하는 `RNOP`에 올바른 패리티를 실어야 하는가?

<details>
<summary>정답 / 해설</summary>

**실어야 한다.**

§6.3.3.4는 CA parity가 MRS로 활성화되면 *"CA parity를 **비활성화하는** MRS의 **`tMOD`가 만료될 때까지**"* 모든 후속 커맨드(**`RNOP`·`CNOP` 포함**)가 올바른 패리티로 발행되어야 한다고 규정한다.

즉 비활성화 MRS를 발행했다고 즉시 꺼지는 것이 아니라, **그 MRS의 `tMOD`가 만료된 이후**부터 패리티가 불필요해진다.

**전이가 비대칭이다**:
```
켤 때 : MRS(enable)  자신은 검사 안 됨 → 그 이후 모든 커맨드에 패리티 필요
끌 때 : MRS(disable) 자신은 패리티 필요 → tMOD 만료 후에야 불필요
```

**설계 결론**: 패리티 생성 로직의 활성 구간은 **`MRS(enable)` 다음 커맨드 ~ `MRS(disable)` + `tMOD`** 다. MRS 발행 시점과 일치시키면 양쪽 경계에서 어긋난다.

</details>

## Q5. (Apply)

컨트롤러가 `WRA`(auto-precharge write)를 발행하고 아날로그 `tWR` 시간이 경과했다. 이제 `PDE`를 발행해도 되는가?

<details>
<summary>정답 / 해설</summary>

**정보가 부족하다.** auto-precharge write의 완료 기준은 `tWR`이 **아니다.**

§6.3.4.1은 write 완료를 *"마지막 데이터 요소가 `tWR` 만족 상태로 메모리 배열에 기록 완료"* 로 정의하면서, **auto-precharge write의 경우 대신 mode register에 프로그램된 `WR` 클럭 수가 경과해야 한다**고 규정한다.

`MR3`의 `WR` 값은 `RU{tWR/tCK}` **이상**으로 프로그램되므로([04장](../../04_mode_registers/)), **아날로그 `tWR`보다 길 수 있다.**

**설계 결론**: 저전력 진입 게이팅에서 **일반 write와 auto-precharge write의 완료 조건을 분리**해야 한다. 그리고 이 판정은 **두 PC 모두**에 대해 이뤄져야 한다.

**부가**: read 완료 조건에는 **RDQS postamble까지** 포함된다. 데이터만 나갔다고 완료가 아니다.

</details>

## Q6. (Analyze)

`PDE`와 `SRE`의 진입 조건은 어떻게 다른가?

<details>
<summary>정답 / 해설</summary>

| | `PDE` (Power-Down) | `SRE` (Self Refresh) |
|---|---|---|
| 조건 | **양쪽 PC의 read/write가 완료**되어 있을 것 | **두 PC의 모든 뱅크가 precharge** + `tRP` 만족 |
| 행이 열려 있어도? | **가능** — active power-down으로 진입 | **불가** |
| refresh 진행 중? | **가능** — 다만 power-down IDD 규격이 적용되지 않음 | — |
| 진입 후 | `PDE`·`CNOP`를 `tCPDED` 유지 | **`PDE`·`CNOP`를 `tCPDED` 유지** |

**`SRE`가 훨씬 강한 조건**이다. `PDE`는 read/write만 끝나면 되지만 `SRE`는 모든 뱅크가 닫혀 있어야 한다.

**특이점**: `SRE` 진입 후에도 **`PDE` 커맨드를 유지**해야 한다(§6.3.4.2). 자기 자신과 다른 커맨드를 이어 붙이는 구조다.

그리고 `SRE` 등록 후에는 **`R0`를 LOW로 유지**해야 self refresh가 지속된다.

</details>
