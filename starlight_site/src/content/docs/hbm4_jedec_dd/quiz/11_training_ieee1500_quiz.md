---
title: "Quiz — 11: 트레이닝과 IEEE 1500"
description: 트레이닝 순서·WOSC·DERR 모드·테스트 포트 이해도 점검
---

[← 11장 본문으로 돌아가기](../../11_training_ieee1500/)

---

## Q1. (Remember) ★

네 가지 트레이닝의 순서 제약을 쓰고 근거 조문을 밝혀라.

<details>
<summary>정답 / 해설</summary>

```
① Rx Offset Calibration (RXoffC, MR8 OP1)
② DCA / DCM             (MR11·MR10 / MR6 OP[7:6])
③ VREFD                 (MR14)
④ WDQS-to-CK Alignment  (MR8 OP3)
```

**근거 두 조문**:
> Rx offset calibration은 DRAM write 캘리브레이션 트레이닝에 영향을 주므로 **`VREFD` 트레이닝과 WDQS-to-CK 정렬보다 먼저** 수행되어야 한다. — §6.12.1

> **duty cycle 조정은 WDQS-to-CK 정렬 트레이닝보다 먼저** 수행되어야 한다 (DCM 시퀀스 유무와 무관). — §6.11.1

**이유**: 각 트레이닝이 뒤 단계의 **전제를 바꾼다.** Rx offset은 **수신기의 판정 기준점**을 옮기고, DCA는 **WDQS의 듀티 자체**를 바꾼다.

</details>

## Q2. (Apply)

정상 동작 중 온도가 올라 WOSC 계수값이 트레이닝 시점 대비 크게 벗어났다. Rx offset calibration을 다시 수행했다. 그다음에 해야 할 일은?

<details>
<summary>정답 / 해설</summary>

**`VREFD` 트레이닝과 WDQS-to-CK 정렬을 다시 수행해야 한다.**

순서가 강제된다는 것은 **앞 단계를 다시 하면 뒤 단계의 전제가 바뀐다**는 뜻이다. Rx offset은 수신기의 판정 기준점을 옮기므로, 그 위에서 잡았던 `VREFD` 값과 위상 정렬이 더 이상 유효하지 않다.

**검증 결론**: 검사해야 할 것은 "순서를 지켰는가"가 아니라 **"앞 단계를 다시 했을 때 뒤 단계도 다시 했는가"** 다. 순서만 보는 checker는 `RXoffC → VREFD → W2C → RXoffC` 를 통과시키는데, 마지막 재수행 때문에 앞의 두 결과가 이미 무효다.

```systemverilog
if (retrain_from == TR_RXOFFC)
  {vrefd_valid_q, w2c_valid_q, dca_valid_q} <= '0;
```

Rx offset만 다시 하고 끝내면 **잘못된 `VREFD`·위상으로 동작**한다.

</details>

## Q3. (Understand)

WOSC가 채널·클럭과 무관하게 동작한다는 것이 무슨 뜻이며, `RESET_n`과 `WRST_n`은 각각 어떤 영향을 주는가?

<details>
<summary>정답 / 해설</summary>

**독립성**(§6.10.1):
- **어떤 채널에도 속하지 않으며** 채널의 동작 주파수나 상태(bank active/idle, power-down, self refresh)와 무관하게 동작한다.
- **계수 중 `CK`·`WDQS`·`WRCK` 어떤 클럭도 필요하지 않다.** 내부 링 오실레이터가 **WDQS 클럭 트리의 복제본**을 통과하는 전파 횟수를 센다.

즉 메모리가 저전력 상태에 있어도 측정할 수 있고, **정상 동작을 방해하지 않고 재트레이닝 필요를 감지**할 수 있다.

**두 리셋의 영향**:
- **`RESET_n`을 LOW로 당기면** 오실레이터가 중단되고 `WOSC_COUNT_VALID`가 **0(무효)** 으로 남는다.
- **`WRST_n`을 LOW로 당기는 것은 오실레이터 동작에 영향을 주지 않는다.**

[03장](../../03_init_reset_power/)의 **두 리셋 비대칭**이 여기서 다시 확인된다.

</details>

## Q4. (Evaluate)

WOSC 측정 시간을 길게 잡을수록 좋은가?

<details>
<summary>정답 / 해설</summary>

**어느 지점까지만 그렇다.**

```
Granularity Error = 2 × (WDQS 지연) / (Run Time)
Accuracy          = 1 − Granularity Error − Matching Error
```

- **길게 돌릴수록 granularity error가 줄어** 정확해진다.
- 다만 **오버플로 한계**(2²⁴ − 1) 안에 있어야 한다. 넘으면 `WOSC_COUNT_VALID`가 0이 된다.
- **`Matching Error`는 아무리 길게 돌려도 줄지 않는다.** WDQS 트레이닝 회로와 실제 클럭 트리의 차이이며 **벤더 지정**이다.

**결론**: 정확도에 **상한**이 있으므로 측정 시간을 무작정 늘릴 이유가 없다. **granularity error가 matching error보다 충분히 작아지는 지점**에서 멈추는 것이 합리적이며, matching error 값은 **벤더 데이터시트**에서 얻어야 한다.

</details>

## Q5. (Analyze) ★

컨트롤러가 `MR6` OP6(DCM)을 1로 두고 측정 중인데 `DERR1`이 HIGH로 관측됐다. 데이터 패리티 오류인가?

<details>
<summary>정답 / 해설</summary>

**아니다 — 그리고 애초에 이 상황이 만들어지면 안 된다.**

DCM 활성 시 `DERR1`은 **DWORD1(PC1)의 WDQS 듀티 사이클 측정 결과**이며 HIGH는 **듀티 ≥ 50%** 를 뜻한다(Table 75).

`DERR`는 **세 가지 의미**를 갖는다.
```
MR6 OP6 == 1   →  듀티 사이클 측정 결과      (11장)
MR8 OP3 == 1   →  위상 검출기 판독           (05장)
그 외          →  데이터 패리티 오류         (08장)
```

**게다가** DCM 모드에서 허용되는 커맨드는 **`REFab`·`REFpb`·`RFMab`·`RFMpb`·`RNOP`·`CNOP`·`MRS`뿐**이다(§6.11.3). **write 커맨드 자체가 허용되지 않는다.**

**설계 결론 둘**:
1. `DERR` 해석은 `MR6` OP6와 `MR8` OP3를 보고 **모드별로 분기**한다.
2. 트레이닝 모드 진입 시 **정상 트래픽을 차단**한다. 허용 목록 밖의 커맨드가 나가면 그 자체가 규격 위반이다.

</details>

## Q6. (Evaluate) ★

양산 테스트에서 `MR8` OP0을 1로 써서 DA 포트를 잠갔다. 이후 디버그가 필요해졌다. `RESET_n`을 당기면 열리는가?

<details>
<summary>정답 / 해설</summary>

**열리지 않는다.**

§13.1.1은 잠금이 **전원이 제거되지 않는 한 유지**되며 다음 어떤 것으로도 해제되지 않는다고 명시한다.
- `RESET_n`을 LOW로 당기는 칩 리셋
- IEEE1500 **`HBM_RESET`** 명령
- `MRS`로 **0을 쓰기**
- `MODE_REGISTER_DUMP_SET`으로 0을 쓰기

**유일한 해제 방법은 전원 제거**다.

**대안**: DA 포트가 잠겨 있어도 **IEEE 1500 포트는 살아 있다.** 둘은 `DA12`로 선택되는 별개 경로이며 잠금은 DA 쪽만 닫는다. 따라서 `MBIST`·`SELF_REP`·`MODE_REGISTER_DUMP_SET` 등 표준 명령으로 하는 디버그는 여전히 가능하다. 잃는 것은 **벤더 지정 테스트 기능**이다.

**검증 주의**: `MR8` OP0은 **채널 0 또는 4에만 정의**된 비트다. 그리고 **MR 이미지 랜덤화에서 반드시 제외**해야 한다 — 랜덤이 1을 만들면 **자극이 검증 환경 자신의 관측 경로를 영구히 닫는다.** 잠금 검증은 격리된 테스트로 두고, **네 해제 경로를 모두** 시험해야 의미가 있다.

</details>
