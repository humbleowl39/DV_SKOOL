# Quiz — Module 06: Configuration Space & Enumeration

[← Module 06 본문으로 돌아가기](../06_config_enumeration.md)

---

## Q1. (Remember)

BAR sizing 의 5 단계 알고리즘을 나열하라.

??? answer "정답 / 해설"
    1. BAR n 에 `0xFFFFFFFF` write
    2. BAR n read → 결과 R
    3. 하위 type bit (bit 0~3) 마스크
    4. `~R + 1` = 요청 size
    5. SW 가 size 정렬된 base 주소 할당 후 BAR n 에 write

## Q2. (Understand)

Type 0 와 Type 1 Configuration Header 의 핵심 차이는?

??? answer "정답 / 해설"
    | 항목 | Type 0 (EP) | Type 1 (Bridge / Switch port) |
    |------|------------|-------------------------------|
    | BAR 갯수 | BAR0..5 (6 개) | BAR0..1 (2 개) |
    | Bus # 필드 | 없음 | Pri/Sec/Sub Bus # 있음 |
    | Memory range forwarding | 없음 (자기 자신) | Memory Base/Limit 으로 forward |
    | IO range forwarding | 없음 | IO Base/Limit 으로 forward |
    | 일반 사용 | NVMe, GPU, NIC | RC Root Port, Switch Up/Downstream Port |

## Q3. (Apply)

64-bit BAR 를 BAR0+BAR1 으로 사용할 때 BAR2 의 값은 어떻게 되는가?

??? answer "정답 / 해설"
    BAR2 는 **별도 BAR slot 으로 사용 가능** — 32-bit BAR 또는 또 다른 64-bit 의 시작 (BAR2+BAR3).

    64-bit BAR 의 인코딩: BAR0 의 하위 4 bit type 에서 bit[2:1] = `10` 이면 다음 BAR (BAR1) 와 합쳐 64-bit 의미. SW 는 BAR0 에 lower 32-bit, BAR1 에 upper 32-bit base 주소 write.

    BAR2 는 BAR1 과 **독립** — 사용 안 하면 0 / 사용하면 새 32-bit 또는 64-bit BAR.

## Q4. (Analyze)

Bus 0 의 enumeration 시 device 가 발견되었다면, 다음 step 의 분기 (Type 0 vs Type 1) 를 분석하라.

??? answer "정답 / 해설"
    1. CfgRd0 의 결과로 Header Type field (offset 0x0E) 확인.
    2. **bit 7 (Multi-Function)**: 1 이면 Func 0..7 모두 시도.
    3. **bit 6:0 (Header Type)**:
        - = 0 → **Type 0 (Endpoint)** → BAR sizing + Capability list 순회.
        - = 1 → **Type 1 (Bridge / Switch port)** → Sec Bus # 할당 + 그 bus 로 재귀 (DFS) → 끝나면 Sub Bus # 확정.

    이 DFS 가 모든 device 를 트리 형태로 발견.

## Q5. (Evaluate)

"Vendor ID = 0xFFFF 면 그 BDF 에 device 가 없는 것이다" 는 enumeration 코드의 가정을 평가하라.

??? answer "정답 / 해설"
    **대부분 맞지만 corner case 있음**.

    맞는 경우:
    - 정상 enumeration 시 unconfigured BDF 에 CfgRd0 → 0xFFFF.

    틀릴 수 있는 경우:
    - **Link 가 unstable / Recovery 중** → CfgRd0 가 timeout 또는 corrupted → 0xFFFF 처럼 보임.
    - **CRS (Configuration Request Retry Status)** 처리 안 한 SW: device 가 link up 직후 아직 ready 아니라 CRS 응답 → SW 가 이를 0xFFFF 로 잘못 해석.
    - **Hot Plug 시 timing race**: device 막 들어왔는데 아직 enumeration 시점이 아닌 경우.

    → 검증 시: link 안정화 대기, CRS retry 정책, link error counter 상태 함께 확인 후 device 부재 판정.
