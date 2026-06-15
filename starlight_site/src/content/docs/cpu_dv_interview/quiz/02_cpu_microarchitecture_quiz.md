---
title: "Quiz — 02: CPU 마이크로아키텍처"
---

본 모듈의 핵심 개념 이해도를 점검합니다. 정답은 펼치면 보입니다.

[← 02장 본문으로 돌아가기](../../02_cpu_microarchitecture/)

---

## Q1. (Remember)

파이프라인 해저드 3종을 올바르게 짝지은 것은?

- [ ] A. Structural / Data / Control
- [ ] B. RAW / WAR / WAW
- [ ] C. Hit / Miss / Eviction
- [ ] D. Fetch / Decode / Execute

<details>
<summary>정답 / 해설</summary>

**A**. 파이프라인 해저드는 자원 충돌인 structural, 데이터 의존인 data, 분기로 인한 control 세 종류로 분류한다. B의 RAW/WAR/WAW는 data hazard 중에서도 *의존의 종류*를 세분한 것이지 해저드 3종 분류가 아니며(RAW만 진짜 의존, WAR/WAW는 OoO에서 renaming으로 제거되는 가짜 의존), C는 캐시 동작이고 D는 파이프라인 단계명이다.

</details>

## Q2. (Understand)

ROB가 명령을 in-order로 retire하는 *근본 이유*는?

<details>
<summary>정답 / 해설</summary>

precise exception과 mispredict 복구를 위해, 아키텍처 상태를 항상 "특정 명령까지만 완료된" 일관된 지점으로 유지해야 하기 때문이다. 실행은 OoO로 뒤섞여도, 결과를 프로그램 순서대로 commit하면 예외가 난 명령의 ROB head 도달 시점에 그 이전은 전부 반영·이후는 전부 flush할 수 있다. 만약 OoO로 commit하면 "어디까지 끝났는지"를 말할 수 없어 예외 핸들러가 재개할 지점을 잃는다. 즉 *실행은 OoO, 커밋은 in-order*가 핵심이다.

</details>

## Q3. (Apply)

다음 시퀀스에서 forwarding이 *완비된* 코어가 겪는 최소 stall 사이클 수는?

```
LD  r1, [r2]
ADD r3, r1, r4
```

- [ ] A. 0
- [ ] B. 1
- [ ] C. 2
- [ ] D. 3

<details>
<summary>정답 / 해설</summary>

**B**. 일반 ALU 결과는 EX 끝에 나오지만 load 결과는 한 단계 뒤인 MEM 끝에 나온다. ADD가 EX에 들어가는 사이클에는 LD의 데이터가 아직 메모리에서 나오지 않았으므로, forwarding 배선이 있어도 *전달할 값 자체가 없어* 1 사이클을 멈춰야 한다(load-use hazard). A는 forwarding으로 모든 RAW가 0 stall이 된다는 오해이고, C/D는 forwarding이 없어 WB까지 기다리는 경우의 값이다. 핵심은 "배선 문제가 아니라 값이 늦게 생산되는 타이밍 문제"라는 점이다.

</details>

## Q4. (Apply)

OoO 코어에서 다음 코드의 (1)과 (3) 사이 의존을 제거해 동시 실행을 가능하게 하는 기법과, 제거되는 의존 종류는?

```
(1) ADD r1, r2, r3
(2) SUB r4, r1, r5
(3) MUL r1, r6, r7
```

<details>
<summary>정답 / 해설</summary>

**Register renaming**으로 **WAW**(그리고 (2)→(3) 사이의 **WAR**) 가짜 의존을 제거한다. (1)과 (3)은 데이터가 흐르지 않고 단지 r1이라는 *이름*을 재사용할 뿐이므로, 매 쓰기를 서로 다른 물리 레지스터(p10, p11…)에 매핑하면 이름 충돌이 사라진다. 그 결과 진짜 데이터 의존인 RAW((1)→(2))만 남아 스케줄러가 (1)과 (3)을 병렬로 굴릴 수 있다. (2)는 여전히 (1)의 결과를 기다려야 한다는 점도 함께 말하면 좋다.

</details>

## Q5. (Analyze)

추측 실행한 store가 *곧바로 메모리에 기록되도록* 설계했다면 어떤 정확성 문제가 생기며, 실제 코어는 이를 어떻게 막는가?

<details>
<summary>정답 / 해설</summary>

추측 store가 즉시 메모리에 써지면, 그 store를 담은 분기가 mispredict로 무효화될 때 *되돌릴 수 없는 메모리 오염*이 남는다 — 존재하지 않았어야 할 쓰기가 영구히 반영되는 것이다. 실제 코어는 store 값을 **store buffer**에 보관했다가 해당 store가 ROB에서 *retire될 때 비로소* 메모리에 반영하고, 추측이 틀리면 store buffer의 엔트리를 그냥 버린다. 이로써 retire 이전의 어떤 store도 다른 관찰자에게 보이지 않는다. 검증에서는 "store가 retire 전에는 메모리/다른 코어에 절대 안 보이는가"를 핵심 corner로 친다.

</details>

## Q6. (Analyze)

서로 다른 두 코어가 같은 캐시 라인의 *서로 다른 바이트*만 각자 쓰는데도 성능이 급락했다. 원인과, 기능 스코어보드로는 왜 못 잡는지 설명하라.

<details>
<summary>정답 / 해설</summary>

**False sharing**이다. 데이터는 논리적으로 겹치지 않지만 코히런시 프로토콜은 *라인 단위*로 동작하므로, 한 코어의 쓰기가 다른 코어의 라인을 invalidate시키는 ping-pong이 반복돼 코히런시 트래픽이 폭증한다. 결과 값 자체는 항상 정확하므로(각 코어가 자기 바이트에 올바른 값을 씀) 트랜잭션 레벨 비교를 하는 기능 스코어보드는 mismatch를 못 본다 — 이것은 성능 버그이지 기능 버그가 아니다. 따라서 코히런시 트랜잭션 카운터·성능 카운터로 과도한 invalidate를 관찰하고, "서로 다른 코어가 동일 라인 접근" cross를 coverage로 두어야 한다.

</details>

## Q7. (Evaluate)

한 팀원이 "추측 load 결과는 어차피 mispredict 시 폐기되니 추측 경로의 메모리 접근은 검증 부담이 없다"고 주장한다. 이 주장을 평가하라.

<details>
<summary>정답 / 해설</summary>

**틀렸다.** 아키텍처 상태(레지스터·메모리)는 폐기로 깨끗이 롤백되지만, 추측 load는 *마이크로아키텍처 상태*인 캐시를 바꿔 놓고, 이 변화는 명령 무효화 후에도 남는다. 공격자는 추측적으로 읽은 비밀 값에 따라 특정 캐시 라인을 건드리게 한 뒤, 어느 라인이 캐시에 올라왔는지를 타이밍으로 측정해 비밀을 복원한다 — Spectre류 취약점이다. 따라서 추측 경로의 메모리 접근이 캐시 fill·예측기 갱신 같은 *관측 가능한 부작용*을 남기는지는 정확성을 넘어 보안 검증의 핵심 대상이다. "아키텍처 상태가 롤백됐다"와 "부작용이 없다"는 다른 명제임을 구분하는 것이 평가의 핵심이다.

</details>
