---
title: "Quiz — Module 04: HCI DV Methodology"
---

[← Module 04 본문으로 돌아가기](../../04_hci_dv_methodology/)

---

## Q1. (Remember)

UFS HCI 검증의 양방향 검증 두 측은?

<details>
<summary>정답 / 해설</summary>

- **Driver-side**: Register/UTRD/메모리 인터페이스
- **Device-side**: UPIU/UniPro/M-PHY 측 응답

양방향 검증이 필요한 이유는 HCI가 SW 드라이버와 UFS 장치 사이의 중재자 역할을 하기 때문입니다. Driver-side에서는 HCI가 UTRD와 레지스터를 올바르게 해석하는지를 확인하고, Device-side에서는 HCI가 UPIU를 올바르게 생성·전달하고 장치 응답을 정확히 처리하는지를 확인합니다. 어느 한 쪽만 검증하면 인터페이스 경계에서 발생하는 버그를 놓치게 되므로, 완전한 검증은 반드시 양쪽을 동시에 커버해야 합니다.

</details>
## Q2. (Understand)

UFS Device Model이 검증에서 하는 역할은?

<details>
<summary>정답 / 해설</summary>

- SCSI command를 받아 spec대로 응답 (Read/Write/Query)
- LU별 storage state 모델링 (가상 NAND 영역)
- 에러 시나리오 inject (CRC, timeout, sense data variants)
- UPIU 응답 형식 정확성 검증의 reference

Device Model이 단순히 "응답을 돌려주는 것" 이상의 역할을 하는 이유는, HCI 검증의 핵심이 HCI가 장치와 올바르게 상호작용하는지를 확인하는 것이기 때문입니다. 실제 NAND 장치를 시뮬레이션에 연결할 수 없으므로 Device Model이 스펙에 따른 참조 응답을 제공합니다. 에러 인젝션 기능이 중요한 이유는 정상 경로만으로는 HCI의 오류 복구 로직을 검증할 수 없기 때문이며, LU별 state 모델링은 데이터 정합성 검증(쓴 데이터를 다시 읽었을 때 일치하는지)의 기반이 됩니다.

</details>
## Q3. (Apply)

다음 시나리오의 검증 기법을 매핑하세요.

| 시나리오 | 기법 |
|----------|------|
| (a) UTRD field accuracy | ? |
| (b) Queue depth 32 동작 | ? |
| (c) CRC error 복구 | ? |
| (d) Linux driver 호환성 | ? |

<details>
<summary>정답 / 해설</summary>

- (a) **UTRD field assertion** + reference compare in scoreboard
- (b) **Multi-command sequence** + queue depth coverage
- (c) **Error injection** in M-PHY layer + 복구 sequence 검증
- (d) **Linux UFS driver 시뮬레이션** (real driver code on virtual SoC)

시나리오별로 검증 기법이 다른 이유는 각 문제가 다른 계층에서 발생하고 다른 방식으로 관찰되기 때문입니다. UTRD 필드 정확성은 메모리 인터페이스 레벨의 결정적 검사가 필요하므로 assertion과 scoreboard를 사용합니다. Queue depth 동작은 여러 명령이 동시에 진행 중인 상태를 만들어야 검증할 수 있으므로 multi-command sequence가 필요합니다. CRC 에러 복구는 정상 경로에서는 발생하지 않으므로 M-PHY 레이어에서 의도적으로 에러를 주입해야 합니다. Linux 드라이버 호환성은 실제 드라이버 코드를 가상 SoC 위에서 실행하는 시스템 레벨 시뮬레이션이 가장 현실적인 방법입니다.

</details>
## Q4. (Analyze)

UFS 검증에서 가장 catch 어려운 silent bug 카테고리는?

<details>
<summary>정답 / 해설</summary>

**Race condition between SW driver and HW HCI**. 예:
- SW가 doorbell ring 직후 다른 slot 업데이트 → HCI fetch 시점에 따라 다른 결과
- SW가 UTRD 작성 완료 전에 doorbell ring → HCI가 incomplete 데이터 fetch
- Multi-core SW에서 같은 slot을 두 thread가 동시 업데이트

검증: SW timing variance (delay injection), thread scheduling chaos.

이 버그가 가장 잡기 어려운 이유는 재현이 비결정적이기 때문입니다. 경쟁 조건은 SW와 HW의 상대적 타이밍이 매번 달라지는 상황에서만 나타나므로, 단일 시드의 결정적 테스트로는 절대 발견되지 않습니다. 시뮬레이션에서 HCI fetch 지연을 랜덤하게 변화시키거나 멀티코어 thread 스케줄링을 의도적으로 혼란스럽게 만드는 방법으로만 이 버그를 노출할 수 있으며, 이것이 DV에서 constrained-random 시나리오가 필수인 핵심 근거 중 하나입니다.

</details>
## Q5. (Evaluate)

다음 중 Production silicon에 가장 위험한 결함은?

- [ ] A. Performance 5% 저하
- [ ] B. Linux 5.0 driver와 5.10 driver 모두 동작하지만 5.15에서 fail
- [ ] C. CRC error 복구 50% 성공
- [ ] D. Boot LU read 1% 실패

<details>
<summary>정답 / 해설</summary>

**D**. Boot 실패는 system 자체가 부팅 안 됨 → 디바이스 brick. 1% rate라도 production scale에서 수만 대 영향. C는 복구 메커니즘이지만 부분적 fail라 silent하게 진행. A는 성능, B는 호환성으로 mitigation 가능.

D가 가장 위험한 이유는 Boot LU 읽기 실패가 시스템 전체를 사용 불능 상태로 만들기 때문입니다. 1% 실패율은 개발 환경에서 무시할 수 있어 보이지만, 수십만 대의 양산 디바이스 기준으로는 수천 대의 brick 사고를 의미합니다. 반면 A(성능 5% 저하)는 사용성에 영향을 주지만 기기 자체는 동작하고, B(특정 드라이버 버전 비호환)는 드라이버 업데이트나 버전 고정으로 mitigation이 가능합니다. C(CRC 복구 50% 성공)는 심각하지만 50%는 복구에 성공하므로 D처럼 완전한 동작 불능은 아닙니다.

</details>
