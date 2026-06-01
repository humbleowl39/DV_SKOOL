# Quiz — Module 02: Automotive SoC Security

[← Module 02 본문으로 돌아가기](../02_automotive_soc_security.md)

---

## Q1. (Remember)

HSM, SecOC, Secure Gateway 가 각각 보호하는 대상은?

??? answer "정답 / 해설"
    - **HSM**: 키 (root key, master key, session key) — 메모리 / I/O 로 평문 키가 노출되지 않게 한다.
    - **SecOC**: 통신 메시지 (CAN 메시지의 무결성 + 발신자 인증 + replay 방어).
    - **Secure Gateway**: 도메인 경계 (Powertrain ↔ Infotainment ↔ Body 사이의 트래픽 정책).

    세 컴포넌트가 서로 다른 대상을 보호하는 이유는 보안 위협이 발생하는 지점이 각기 다르기 때문입니다. HSM은 "키가 메모리에 평문으로 존재하는 순간"을 없애는 하드웨어 경계를 만들고, SecOC는 "버스 위를 흐르는 메시지"를 위조·재전송으로부터 보호하며, Secure Gateway는 "도메인 간 이동"을 정책으로 통제합니다. 한 컴포넌트가 다른 것의 역할을 대체할 수 없습니다. 예를 들어 HSM이 있어도 Gateway가 없으면 Infotainment에서 Powertrain으로 임의 메시지를 전달하는 경로가 열리고, SecOC가 있어도 HSM이 없으면 키 자체가 소프트웨어로 노출될 수 있습니다.

## Q2. (Understand)

HSM 의 키 계층이 "Root → Master → Session" 의 3단인 이유는?

??? answer "정답 / 해설"
    - **Root** : 변경 불가능. 한 번 노출되면 fleet 전체 침해 → 사용 빈도를 최소화 해야 한다.
    - **Master** : Root 로 암호화되어 저장. 부팅 시에만 잠깐 사용해 Session 키를 파생.
    - **Session** : 실제 SecOC MAC 계산 등 런타임에 사용. 노출되어도 ECU 한 대만 영향.

    계층화로 **"노출 영향 반경 ↓ + 사용 빈도 ↑"** 균형을 맞춘다.

    3단 계층이 필요한 근본 이유는 "가장 중요한 키일수록 가장 적게 사용해야 한다"는 보안 원칙 때문입니다. Root Key가 직접 MAC 계산에 쓰인다면 매초 수백 번 사용되는 동안 side-channel 공격이나 메모리 오류로 노출될 위험이 생깁니다. 대신 Root Key는 Master Key를 봉인하는 데만 쓰이고 거의 사용되지 않으며, Master Key는 부팅 시 단 한 번 Session Key를 파생하고 다시 잠깁니다. Session Key가 노출되더라도 그 ECU 한 대에만 영향이 미치고, 공격자는 Master나 Root에 접근할 수 없으므로 fleet 전체로 피해가 확산되지 않습니다.

## Q3. (Apply)

Truncated MAC(예: 24bit) + 8byte CAN payload 환경에서 SecOC 를 적용하려고 한다. 디자인 시 결정해야 할 3가지 trade-off 는?

??? answer "정답 / 해설"
    1. **MAC 길이** : 길수록 보안 ↑ but payload 가용 영역 ↓. 24~32bit 가 일반적.
    2. **Freshness 폭** : 32bit 카운터 vs 짧은 truncated freshness — 길수록 wrap-around 우려 ↓.
    3. **인증 대상 메시지 선별** : 모든 메시지를 보호하면 bus load 폭증. 안전/제어 critical 만 우선 적용.

    이 세 가지가 trade-off인 이유는 8바이트라는 CAN 페이로드 제약이 모든 선택을 연결하기 때문입니다. MAC을 32비트로 늘리면 Freshness에 쓸 공간이 줄고, Freshness를 넉넉히 잡으면 실제 데이터가 줄어듭니다. 또한 모든 메시지를 인증하면 ECU의 암호 연산 부담과 버스 대역 소모가 동시에 증가합니다. 따라서 설계자는 "어떤 메시지가 위조되었을 때 안전 사고로 이어지는가"를 TARA로 먼저 분류하고, 그 결과를 바탕으로 세 파라미터를 함께 결정해야 합니다.

## Q4. (Analyze)

SecOC 의 MAC + Freshness 가 막아주는 공격과 막지 못하는 공격을 구분하라.

??? answer "정답 / 해설"
    **막아주는 공격**:
    - Spoofing (MAC 검증 실패)
    - Replay (Freshness 카운터 검증)
    - 메시지 내용 tampering (MAC 검증)

    **막지 못하는 공격**:
    - **DoS** : 정상 ID 의 가짜 메시지를 flooding 하면 수신측 검증 부담만 늘어남.
    - **합법 ECU 의 침해** : 그 ECU 가 갖고 있는 키로 정상 인증 메시지를 보내므로 SecOC 통과.
    - **Side channel / 키 추출** : HSM 자체가 깨지면 SecOC 무력화.

    → SecOC 는 IDS, Gateway 와 함께 써야 의미.

    SecOC가 막지 못하는 공격들의 공통점은 "합법적인 키를 가진 주체 또는 합법적인 프레임 형태를 모방하는 상황"이라는 점입니다. DoS flooding은 SecOC가 모든 프레임을 검증해야 하므로 오히려 검증 연산 자체가 부하가 되고, 침해된 ECU는 유효한 키로 인증 메시지를 생성하므로 SecOC 관점에서는 정상 트래픽과 구분이 불가능합니다. 이 때문에 IDS는 메시지 주기·패턴 이상(비정상 빈도, 예상치 못한 시퀀스)을 행동 기반으로 탐지하고, Gateway는 침해 ECU가 접근할 수 있는 도메인을 격리함으로써 SecOC의 맹점을 보완합니다.

## Q5. (Evaluate)

Central Gateway 아키텍처와 Zonal Architecture(영역 컨트롤러) 의 보안 관점 장단점을 평가하라.

??? answer "정답 / 해설"
    **Central Gateway** : 모든 도메인 트래픽이 한 곳을 지나 → 정책/IDS 집중 관리 쉬움. but 단일 장애점(SPOF) + 트래픽 병목.

    **Zonal Architecture** : 영역별(예: 좌앞/우앞/좌뒤/우뒤) 컨트롤러가 가까운 ECU 를 묶어 처리, 영역 간은 고대역 Ethernet backbone. 보안 장점은 **격리 단위가 작아지고 와이어 길이 ↓ → tampering 표면 ↓**. 단점은 영역 컨트롤러 각자가 보안 능력(HSM/IDS) 을 갖춰야 해 비용/복잡도 ↑.

    추세는 Zonal — 차세대 E/E 아키텍처에서 표준화 중.

    Central Gateway가 단일 장애점이 되는 이유는 "모든 도메인 트래픽이 한 노드를 반드시 경유한다"는 토폴로지 자체에 있습니다. 그 노드가 침해되거나 처리 용량을 초과하면 차량 전체 통신이 영향을 받습니다. Zonal Architecture는 이 문제를 "격리 단위를 작게 쪼갠다"는 원칙으로 해결합니다. 한 영역 컨트롤러가 침해되어도 다른 영역은 독립적으로 동작하고, 영역 간은 고대역 Ethernet으로 연결되므로 전통적인 CAN 병목도 사라집니다. 다만 보안 비용이 각 영역 컨트롤러로 분산되므로, 각 컨트롤러가 독립적인 HSM과 IDS를 갖춰야 한다는 설계 요건이 추가됩니다.
