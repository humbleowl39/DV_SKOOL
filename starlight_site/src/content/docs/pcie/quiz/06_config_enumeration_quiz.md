---
title: "Quiz — Module 06: Configuration Space & Enumeration"
---

[← Module 06 본문으로 돌아가기](../../06_config_enumeration/)

---

## Q1. (Remember)

BAR sizing 의 5 단계 알고리즘을 나열하라.

<details>
<summary>정답 / 해설</summary>

1. BAR n 에 `0xFFFFFFFF` write
2. BAR n read → 결과 R
3. 하위 type bit (bit 0~3) 마스크
4. `~R + 1` = 요청 size
5. SW 가 size 정렬된 base 주소 할당 후 BAR n 에 write

BAR sizing 이 작동하는 원리는 "디바이스가 변경할 수 없는 비트는 0을 돌려준다"는 규약에 있다. 모두 1을 쓰면 디바이스는 자신이 지원하는 크기에 해당하는 하위 비트들을 0으로 고정해 돌려주고, SW 는 2의 보수(`~R + 1`)로 이를 크기로 변환한다. 이 메커니즘 덕분에 OS 는 각 디바이스의 MMIO 크기를 런타임에 발견하고 충돌 없이 주소를 배분할 수 있다.

</details>
## Q2. (Understand)

Type 0 와 Type 1 Configuration Header 의 핵심 차이는?

<details>
<summary>정답 / 해설</summary>

| 항목 | Type 0 (EP) | Type 1 (Bridge / Switch port) |
|------|------------|-------------------------------|
| BAR 갯수 | BAR0..5 (6 개) | BAR0..1 (2 개) |
| Bus # 필드 | 없음 | Pri/Sec/Sub Bus # 있음 |
| Memory range forwarding | 없음 (자기 자신) | Memory Base/Limit 으로 forward |
| IO range forwarding | 없음 | IO Base/Limit 으로 forward |
| 일반 사용 | NVMe, GPU, NIC | RC Root Port, Switch Up/Downstream Port |

핵심 차이는 "이 디바이스가 자신을 위한 장치인가, 아니면 하위 버스 트래픽을 중계하는 장치인가"에 달려 있다. Type 0 는 자기 자신의 MMIO 영역(BAR 최대 6개)만 가지며 트래픽을 전달하지 않는다. Type 1 은 Primary/Secondary/Subordinate Bus 번호와 Memory Base/Limit 을 가져 하위 버스에 있는 디바이스들로 가는 TLP 를 forwarding 한다. 이 구조를 이해하면 enumeration 의 DFS(깊이 우선 탐색) 알고리즘에서 Type 1 을 만날 때 재귀 탐색이 필요한 이유가 명확해진다.

</details>
## Q3. (Apply)

64-bit BAR 를 BAR0+BAR1 으로 사용할 때 BAR2 의 값은 어떻게 되는가?

<details>
<summary>정답 / 해설</summary>

BAR2 는 **별도 BAR slot 으로 사용 가능** — 32-bit BAR 또는 또 다른 64-bit 의 시작 (BAR2+BAR3).

64-bit BAR 의 인코딩: BAR0 의 하위 4 bit type 에서 bit[2:1] = `10` 이면 다음 BAR (BAR1) 와 합쳐 64-bit 의미. SW 는 BAR0 에 lower 32-bit, BAR1 에 upper 32-bit base 주소 write.

BAR2 는 BAR1 과 **독립** — 사용 안 하면 0 / 사용하면 새 32-bit 또는 64-bit BAR.

64-bit BAR 는 인접한 두 슬롯을 "pair"로 소비하지만, 그 pair 가 끝난 다음 슬롯은 완전히 독립적이다. 따라서 BAR0+BAR1 이 64-bit 쌍으로 소비되었다면 BAR2 는 새로운 32-bit BAR 로 시작하거나, BAR2+BAR3 쌍으로 또 다른 64-bit BAR 를 구성할 수 있다. 흔히 "64-bit BAR 를 쓰면 다음 BAR 도 잠긴다"고 오해하는데, BAR1 이 pair 의 upper 절반으로 사용될 뿐 BAR2 는 전혀 영향을 받지 않는다.

</details>
## Q4. (Analyze)

Bus 0 의 enumeration 시 device 가 발견되었다면, 다음 step 의 분기 (Type 0 vs Type 1) 를 분석하라.

<details>
<summary>정답 / 해설</summary>

1. CfgRd0 의 결과로 Header Type field (offset 0x0E) 확인.
2. **bit 7 (Multi-Function)**: 1 이면 Func 0..7 모두 시도.
3. **bit 6:0 (Header Type)**:
    - = 0 → **Type 0 (Endpoint)** → BAR sizing + Capability list 순회.
    - = 1 → **Type 1 (Bridge / Switch port)** → Sec Bus # 할당 + 그 bus 로 재귀 (DFS) → 끝나면 Sub Bus # 확정.

이 DFS 가 모든 device 를 트리 형태로 발견.

Enumeration 의 분기 결정은 Header Type 필드 하나로 이루어진다. Type 0 이면 더 이상 하위 버스가 없으므로 BAR 크기를 측정하고 Capability 를 순회한 뒤 다음 디바이스로 넘어간다. Type 1 이면 아직 탐색하지 않은 하위 버스가 있다는 뜻이므로 Secondary Bus Number 를 할당하고 재귀 탐색한 뒤, 재귀가 끝나면 그 버스 아래에서 발견된 최대 버스 번호를 Subordinate Bus Number 로 확정한다. Multi-Function bit(bit 7)는 이 과정에 직교하며, 한 슬롯 안에 여러 function 이 있을 때 Function 0~7 을 모두 탐색하도록 알려준다.

</details>
## Q5. (Evaluate)

"Vendor ID = 0xFFFF 면 그 BDF 에 device 가 없는 것이다" 는 enumeration 코드의 가정을 평가하라.

<details>
<summary>정답 / 해설</summary>

**대부분 맞지만 corner case 있음**.

맞는 경우:
- 정상 enumeration 시 unconfigured BDF 에 CfgRd0 → 0xFFFF.

틀릴 수 있는 경우:
- **Link 가 unstable / Recovery 중** → CfgRd0 가 timeout 또는 corrupted → 0xFFFF 처럼 보임.
- **CRS (Configuration Request Retry Status)** 처리 안 한 SW: device 가 link up 직후 아직 ready 아니라 CRS 응답 → SW 가 이를 0xFFFF 로 잘못 해석.
- **Hot Plug 시 timing race**: device 막 들어왔는데 아직 enumeration 시점이 아닌 경우.

→ 검증 시: link 안정화 대기, CRS retry 정책, link error counter 상태 함께 확인 후 device 부재 판정.

"0xFFFF = 디바이스 없음"은 정상 경로에서는 맞는 추론이지만, 링크 불안정이나 CRS 미처리가 있으면 디바이스가 실제로 있어도 0xFFFF 가 나올 수 있다. 특히 CRS 는 디바이스가 부팅 후 아직 준비가 덜 됐을 때 보내는 retry 신호인데, SW 가 이를 올바로 처리하지 않으면 "디바이스 없음"으로 잘못 판단한다. 검증 시에는 이 세 가지 실패 경로를 시나리오로 만들어 별도로 테스트해야 한다.

</details>
