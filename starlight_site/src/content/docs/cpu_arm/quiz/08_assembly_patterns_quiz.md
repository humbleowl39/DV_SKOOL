---
title: "Quiz — Module 08: Assembly Patterns"
---

[← Module 08 본문으로 돌아가기](../../08_assembly_patterns/)

---

## Q1. (Remember)

AAPCS64 에서 정수 함수 인자가 전달되는 레지스터와 정수 반환값 레지스터로 옳은 것은?

- [ ] A. 인자 `X8–X15`, 반환 `X16`
- [ ] B. 인자 `X0–X7`, 반환 `X0`
- [ ] C. 인자 모두 스택, 반환 `SP`
- [ ] D. 인자 `X19–X28`, 반환 `X30`

<details>
<summary>정답 / 해설</summary>

**B**. AAPCS64 는 정수 인자 1~8 을 `X0–X7` 로 넘기고 반환값을 `X0` 에 둡니다. 9번째 인자부터만 스택을 씁니다. A 는 임의의 잘못된 레지스터, C 는 옛 스택 기반 모델과 혼동, D 는 callee-saved(X19–X28)와 LR(X30)을 인자/반환과 헷갈린 오답입니다.

</details>
## Q2. (Understand)

`stp x29, x30, [sp, #-32]!` 명령의 동작을 가장 정확히 설명한 것은?

- [ ] A. SP 를 읽기만 하고 x29/x30 을 SP 자리에 store
- [ ] B. SP 를 먼저 32 감소시킨 뒤 그 주소에 x29/x30 을 store (pre-index)
- [ ] C. x29/x30 을 store 한 뒤 SP 를 32 증가 (post-index)
- [ ] D. x29 와 x30 을 서로 교환

<details>
<summary>정답 / 해설</summary>

**B**. `[sp, #-32]!` 의 `!` 가 pre-index 표시로, **SP 를 먼저 -32 한 뒤** 그 주소에 두 레지스터(FP=x29, LR=x30)를 저장하면서 base(SP)를 갱신합니다 — 프레임 할당과 FP/LR 저장을 한 명령으로 끝냅니다. C 는 post-index(`[sp], #32`)로 epilogue 의 `ldp` 형태이고, A/D 는 동작을 잘못 설명한 오답입니다.

</details>
## Q3. (Apply)

`int wrap(int a){ return work(a+1); }` 가 `-O2` 에서 끝부분을 `bl work` 가 아니라 `b work` 로 컴파일했다. 이 선택의 효과는?

- [ ] A. work 의 반환값이 무시된다
- [ ] B. tail call — caller 프레임을 재사용하고 RAS 를 깨지 않아 스택을 아낀다
- [ ] C. work 가 인라인된다
- [ ] D. 무한 재귀가 된다

<details>
<summary>정답 / 해설</summary>

**B**. 함수 마지막에서 다른 함수를 부르고 그 결과를 그대로 반환하는 패턴은 **tail call** 로 변환됩니다. `b work` 는 새 스택 프레임을 만들지 않고 wrap 의 프레임을 재사용하며, `bl` 처럼 LR 을 갱신하지 않아 return address stack(RAS)을 깨지 않습니다. 깊은 재귀의 스택 오버플로를 피하는 핵심입니다. A 는 틀렸고(work 의 X0 가 그대로 wrap 의 반환), C/D 는 tail call 과 무관합니다.

</details>
## Q4. (Apply)

C 의 `b->f()` (가상 함수 호출)가 `ldr x1,[x0]` → `ldr x1,[x1]` → `br x1` 로 컴파일됐다. 두 번의 `ldr` 이 각각 로드하는 것은?

- [ ] A. 둘 다 함수 인자
- [ ] B. 첫 ldr = vptr(객체 안 vtable 포인터), 둘째 ldr = vtable 안의 함수 포인터
- [ ] C. 첫 ldr = 반환값, 둘째 ldr = LR
- [ ] D. 둘 다 스택 슬롯

<details>
<summary>정답 / 해설</summary>

**B**. 가상 함수 호출은 ① 객체 시작 주소(x0)에서 **vptr** 을 읽고(`ldr x1,[x0]`), ② 그 vtable 에서 해당 슬롯의 **함수 포인터** 를 읽은 뒤(`ldr x1,[x1]`), ③ `br x1` 로 indirect branch 합니다. indirect load 두 번 + indirect branch 한 번이라 direct call 보다 비싸고, 분기 예측은 M07 의 ITTAGE/BTB 에 의존합니다. devirtualization(final/단일 구현/LTO)으로 직접 호출 변환이 가능합니다. A/C/D 는 vtable 메커니즘과 무관한 오답입니다.

</details>
## Q5. (Analyze)

어떤 함수가 자주 쓰는 포인터를 `X10` 에 보관한 채 중간에 `bl helper` 를 호출했더니, 호출 후 X10 값이 깨졌다. helper 는 ABI 를 정상 준수한다. 버그는 어디에 있는가?

<details>
<summary>정답 / 해설</summary>

버그는 **caller 측** 에 있습니다. `X10` 은 `X0–X18` 범위의 **caller-saved** 레지스터로, AAPCS64 상 callee(helper)가 자유롭게 덮어써도 규약 위반이 아닙니다. 즉 helper 는 정상이고, 잘못은 "함수 호출을 가로질러 살아남아야 하는 값을 caller-saved 레지스터에 둔 것" 입니다. 올바른 수정은 그 포인터를 **callee-saved(X19–X28)** 에 두고 prologue/epilogue 에서 백업·복원하거나, 호출 직전 스택에 spill 했다가 호출 후 reload 하는 것입니다. 검증에서 이 분류(라이브러리/DUT 버그가 아니라 호출 측 ABI 오해)가 중요합니다.

</details>
## Q6. (Evaluate)

같은 AXPY 루프(`y=a*x+y`)를 NEON 으로 짠 코드와 SVE 로 짠 코드를 비교한다. 길이 `n` 이 lane 수의 배수가 아닌 일반 입력에 대해, 코드 크기·branch 측면에서 어느 쪽이 유리하며 그 근본 이유는?

<details>
<summary>정답 / 해설</summary>

**SVE 가 유리** 합니다. 근본 이유는 lane 수를 다루는 방식의 차이입니다. NEON 은 lane 수가 컴파일 타임에 **고정**(예: 4)이라, n 이 4 의 배수가 아니면 마지막 1~3개 잔여 원소를 처리하는 **별도 tail loop** 가 항상 추가 코드로 붙습니다 — 코드 크기 증가, 추가 분기, I-cache 압박. 반면 SVE 는 **VL-agnostic** 으로 `whilelo p0.s, x_i, x_n` 가 만든 predicate 가 마지막 iteration 에서 부분 lane 만 활성화하므로 **하나의 루프** 로 끝납니다 — tail loop 도, recompile 도 필요 없고, 같은 binary 가 VL 128/256/512비트 어디서든 동작합니다. 따라서 branch density 와 코드 크기, 다양한 VL 이식성 측면에서 SVE 가 우위입니다. 다만 학습 코스트는 SVE 가 높고, 단순·짧은 고정폭 루프에서는 NEON 의 직관성이 충분할 수 있다는 trade-off 도 함께 평가해야 합니다.

</details>
