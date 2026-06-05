---
title: "Quiz — Module 03: RAS-node & Fault Injection (DV)"
---

[← Module 03 본문으로 돌아가기](../../03_ras_node_fault_injection/)

---

## Q1. (Remember)

RAS-node에서 failing address를 캡처하는 error record 레지스터(계열)와 그 전형적 access policy는?

- [ ] A. `ERR<n>ADDR`, RO (read-only)
- [ ] B. `ERR<n>STATUS`, W1C
- [ ] C. `ERR<n>CTLR`, RW
- [ ] D. `ERR<n>ADDR`, W1C

<details>
<summary>정답 / 해설</summary>

**A**. `ERR<n>ADDR`(계열)은 에러가 난 주소를 HW가 캡처하는 레지스터로, SW는 읽기만 하므로 전형적으로 **RO**입니다. `ERR<n>STATUS`(B)는 에러 type/valid 상태로 보통 **W1C**(1 write로 clear), `ERR<n>CTLR`(C)은 검출/인터럽트 enable과 fault injection enable을 담은 **RW**입니다. 정확한 비트 필드는 Arm RAS System Architecture 사양 재확인이 필요합니다.

</details>
## Q2. (Understand)

스펙이 정의하는 "fault injection"이 무엇이며, 왜 pre-silicon 검증과 post-silicon 테스트 양쪽에 유용한지 설명하라.

<details>
<summary>정답 / 해설</summary>

fault injection은 **특정 레지스터를 프로그래밍해 runtime에 가짜 에러를 주입** 하는 HW 기능입니다. 실제 물리적 고장(비트 플립, 노화)을 일으키지 않고도 내부 RAS 로직(검출), 인터럽트 경로, telemetry(error record 기록·보고)가 올바로 동작하는지 검증할 수 있게 합니다. pre-silicon에서는 시뮬레이션으로 실제 결함을 만들 수 없으므로 inject 레지스터가 RAS 경로를 자극하는 유일한 현실적 수단이고, post-silicon에서는 물리 고장을 기다릴 필요 없이 양산 칩의 RAS 기능을 즉시 점검할 수 있습니다. 핵심은 "고장 없이 RAS 대응 경로를 검증"한다는 점입니다.

</details>
## Q3. (Apply)

UVM 검증에서 ECC 에러를 주입하려 한다. 다음 두 방법 중 올바른 것을 고르고 이유를 한 줄로.
A) `force tb_top.dut.u_cache.ecc_err = 1;`
B) `model.ERRCTLR.write(status, inject_enable, .parent(this));` 후 트리거 접근

<details>
<summary>정답 / 해설</summary>

**B가 올바릅니다.** DUT가 제공하는 inject 레지스터를 RAL 시퀀스로 프로그래밍하는 시퀀스 레벨 방식이기 때문입니다. A의 RTL force는 특정 신호명·계층에 결합되어 RTL 리비전마다 깨지고, 다른 블록/프로젝트로 이식이 안 되며, 검토자가 의도를 읽기 어렵습니다. 반면 B는 버스 추상화 위에서 동작해 재사용·이식이 되고, 스펙이 정의한 fault injection 경로(레지스터 프로그래밍)를 그대로 검증합니다. 프로젝트 규칙상으로도 에러 주입은 시퀀스 레벨에서만 허용되고 RTL 수정은 금지입니다.

</details>
## Q4. (Apply)

`ERRSTATUS.UE`(W1C)를 clear하려고 RAL `update()`를 호출했는데 인터럽트가 안 내려간다. 원인과 수정은?

<details>
<summary>정답 / 해설</summary>

원인은 RAL **`update()`의 생략 동작** 입니다. `update()`는 desired ≠ mirror일 때만 버스 write를 발생시키므로, W1C 비트를 clear하기 위한 1-write가 생략되어 실제 버스 트랜잭션이 나가지 않고 HW의 W1C clear가 일어나지 않습니다 → 인터럽트가 그대로 떠 있습니다. 수정: `update` 대신 **명시적 `write`** 로 clear할 비트에 1을 직접 씁니다 — 예: `model.ERRSTATUS.write(status, 32'h4 /*UE 비트=1*/, .parent(this));`. W1C처럼 "같은 값을 다시 써야 의미가 있는" 레지스터에서는 항상 명시적 write를 사용해야 합니다.

</details>
## Q5. (Analyze)

fault injection 검증에서 "inject가 disable인데 정상 트래픽에서 error record가 기록되는가"를 확인하는 음성 케이스가 왜 중요한지 분석하라.

<details>
<summary>정답 / 해설</summary>

이 음성 케이스는 RAS 검출 로직의 **false positive(오검출)** 를 잡습니다. 만약 inject가 꺼져 있고 정상 트래픽만 흐르는데도 error record가 기록되거나 인터럽트가 올라간다면, RAS 로직이 정상 데이터를 결함으로 오인하는 것입니다. 이런 false alarm은 (1) 멀쩡한 자원을 불필요하게 offline시켜 가용성을 해치고, (2) 운영자에게 거짓 경보를 보내 telemetry 신뢰도를 떨어뜨리며, (3) poison/exception을 오발동시켜 정상 프로세스를 죽일 수 있습니다. 양성 케이스(주입→검출)만 검증하면 "에러를 잡는다"는 것만 확인할 뿐 "정상을 가만히 둔다"는 것은 확인하지 못해, 오검출이라는 escape를 놓칩니다. scoreboard의 "Unexpected error record" 분기가 이를 검출합니다.

</details>
## Q6. (Evaluate)

RAS fault injection 검증 환경에서 explicit prediction(predictor 연결)을 쓰기로 했다. 이때 반드시 함께 해야 하는 설정과, 빠뜨릴 경우의 증상을 평가하라.

<details>
<summary>정답 / 해설</summary>

반드시 **`regmodel.<map>.set_auto_predict(0)`** 를 호출해야 합니다. explicit prediction은 monitor가 관찰한 버스 트랜잭션을 predictor가 받아 mirror를 갱신하는 방식입니다. 그런데 auto_predict를 끄지 않으면, 모델이 _자신이 낸_ read/write로도 implicit하게 mirror를 갱신하고 predictor도 같은 트랜잭션을 모니터로 받아 또 갱신해 **mirror가 이중 갱신** 됩니다. 증상은 mirror 값이 가끔 두 배로 토글되거나 실제 record와 어긋나는 것이며, 이는 RAS scoreboard가 mirror를 기대값과 비교할 때 false mismatch나 false pass를 만듭니다. RAS record 레지스터는 HW가 스스로 set하고(제3의 "마스터"인 RAS 로직), W1C로 clear되는 등 모델 외 변경이 많으므로 explicit prediction이 적합하며, 그 필수 짝이 `set_auto_predict(0)`입니다([UVM M07 RAL] 참고).

</details>
