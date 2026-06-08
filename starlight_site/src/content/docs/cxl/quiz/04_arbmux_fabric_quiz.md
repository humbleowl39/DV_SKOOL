---
title: "Quiz — Module 04: ARB/MUX & 패브릭"
---

[← Module 04 본문으로 돌아가기](../../04_arbmux_fabric/)

---

## Q1. (Remember)

ALMP(ARB/MUX Link Management Packet)의 주된 용도는?

- [ ] A. Flit의 CRC 검증
- [ ] B. 양 끝단의 vLSM 상태 동기화
- [ ] C. 메모리 주소 변환
- [ ] D. 암호화 키 교환

<details>
<summary>정답 / 해설</summary>

**B**. ALMP는 1 DWORD(4 byte) 크기의 패킷으로, Status.Active / Request.L1 / Request.L2 / Request.L0p 같은 메시지를 통해 양 끝단의 vLSM 상태를 동기화합니다. 전이 전 양단이 상태를 합의해야 안전한 전이가 가능합니다.

</details>
## Q2. (Understand)

물리 링크가 하나인데도 CXL이 프로토콜별 vLSM을 두는 이유를 설명하라.

<details>
<summary>정답 / 해설</summary>

두 vLSM 그룹(.io / .cachemem)은 서로 다른 활성도를 가질 수 있습니다. 예를 들어 .io는 idle이라 절전(L1)하고 싶은데 .cachemem은 한창 활발할 수 있습니다. 물리 링크 하나의 단일 전력 상태로 모두 묶으면 한쪽을 재우려 다른 쪽도 재워야 하거나(성능 저하), 한쪽이 활성이라 다른 쪽이 절전 못 합니다(전력 낭비). vLSM은 "물리는 공유, 전력/상태는 독립"을 가능케 하는 가상화입니다. .cache와 .mem은 공통 LL을 쓰므로 하나의 vLSM(.cachemem)을 공유합니다.

</details>
## Q3. (Apply)

호스트가 DCD에서 받은 Region X를 반환하려 한다. 올바른 동작 순서는?

- [ ] A. Remove Capacity → 매핑 해제 → Release
- [ ] B. 매핑 해제 → Release → Remove Capacity
- [ ] C. Release → 매핑 해제 → Remove Capacity
- [ ] D. Add Capacity → Release

<details>
<summary>정답 / 해설</summary>

**B**. workload 종료 후 호스트가 (1) Region X **매핑 해제**(페이지 테이블/HDM에서 제거) → (2) Fabric Manager에 **Release** → (3) FM이 DCD에 **Remove Capacity**. 매핑이 살아있는데 물리 회수(Remove Capacity)를 먼저 하면 호스트가 유효하다고 믿는 주소가 회수돼 사용 중 메모리 손실/오접근이 발생합니다.

</details>
## Q4. (Analyze)

MLD(Multi Logical Device)가 "물리적 분할"이 아니라 "논리적 분할"이라는 점이 다중 호스트 환경에서 갖는 의미를 분석하라.

<details>
<summary>정답 / 해설</summary>

MLD는 하나의 물리 디바이스(예: 큰 메모리 확장기)를 최대 16개 Logical Device로 **논리적으로 파티셔닝**합니다. 물리적으로 자르는 것이 아니라 자원을 분할해 16개 호스트가 각자 자기 몫(LD)을 가진 것처럼 보이게 합니다. 의미: (1) 단일 물리 디바이스를 여러 호스트가 격리된 채 공유 → 비용 효율, (2) 검증 관점에서 "어느 LD/어느 호스트의 트랜잭션인가"를 식별하는 것이 scoreboard의 전제가 됩니다. 물리 분할이 아니므로 LD 간 격리(보안/일관성)가 올바른지가 검증 포인트입니다.

</details>
## Q5. (Analyze)

vLSM 상태 전이(예: Active → L1) 시 양 끝단이 ALMP로 합의하지 않으면 어떤 문제가 생기는지 분석하라.

<details>
<summary>정답 / 해설</summary>

양 끝단의 가상 링크 상태가 어긋난 채 전이하면, 한쪽은 절전(L1)으로 데이터를 받을 준비가 안 됐는데 다른 쪽은 Active로 Flit을 보내는 불일치가 생깁니다. 결과적으로 전이 직후 데이터 유실이나 링크 hang이 발생할 수 있습니다. ALMP(Status.Active, Request.L1 등)로 전이 전 양단이 상태를 합의해야 안전합니다. 따라서 L1/L2 전이 후 데이터 유실 같은 증상은 ALMP 교환 순서/합의 누락을 먼저 의심해야 합니다.

</details>
## Q6. (Evaluate)

RAS의 Poison과 Viral이 각각 다른 수준의 방어임을 평가하라.

<details>
<summary>정답 / 해설</summary>

- **Poison**: 데이터 오류 감지 시 해당 캐시라인에 태그를 붙여 소비자가 읽을 때 에러를 보고하게 합니다. 데이터 경로를 따라 전파되어 **최초 오류 지점부터 최종 소비자까지 추적 가능**한, 세밀하고 국소적인 방어입니다.
- **Viral**: Poison 전파가 통제 불가능할 때 **링크 전체를 정지**시켜 오염 확산을 차단하는 최후의 방어선입니다.

즉 Poison은 "오염을 표시하고 추적"하는 일상적 메커니즘, Viral은 "확산을 막기 위해 링크를 희생"하는 비상 조치입니다. 두 수준이 함께 있어야 국소 오류는 추적하고 광역 오염은 차단하는 완결적 RAS가 됩니다.

</details>
