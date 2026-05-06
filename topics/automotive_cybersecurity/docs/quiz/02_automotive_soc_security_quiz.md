# Quiz — Module 02: Automotive SoC Security

[← Module 02 본문으로 돌아가기](../02_automotive_soc_security.md)

---

## Q1. (Remember)

HSM, SecOC, Secure Gateway 가 각각 보호하는 대상은?

??? answer "정답 / 해설"
    - **HSM**: 키 (root key, master key, session key) — 메모리 / I/O 로 평문 키가 노출되지 않게 한다.
    - **SecOC**: 통신 메시지 (CAN 메시지의 무결성 + 발신자 인증 + replay 방어).
    - **Secure Gateway**: 도메인 경계 (Powertrain ↔ Infotainment ↔ Body 사이의 트래픽 정책).

## Q2. (Understand)

HSM 의 키 계층이 "Root → Master → Session" 의 3단인 이유는?

??? answer "정답 / 해설"
    - **Root** : 변경 불가능. 한 번 노출되면 fleet 전체 침해 → 사용 빈도를 최소화 해야 한다.
    - **Master** : Root 로 암호화되어 저장. 부팅 시에만 잠깐 사용해 Session 키를 파생.
    - **Session** : 실제 SecOC MAC 계산 등 런타임에 사용. 노출되어도 ECU 한 대만 영향.

    계층화로 **"노출 영향 반경 ↓ + 사용 빈도 ↑"** 균형을 맞춘다.

## Q3. (Apply)

Truncated MAC(예: 24bit) + 8byte CAN payload 환경에서 SecOC 를 적용하려고 한다. 디자인 시 결정해야 할 3가지 trade-off 는?

??? answer "정답 / 해설"
    1. **MAC 길이** : 길수록 보안 ↑ but payload 가용 영역 ↓. 24~32bit 가 일반적.
    2. **Freshness 폭** : 32bit 카운터 vs 짧은 truncated freshness — 길수록 wrap-around 우려 ↓.
    3. **인증 대상 메시지 선별** : 모든 메시지를 보호하면 bus load 폭증. 안전/제어 critical 만 우선 적용.

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

## Q5. (Evaluate)

Central Gateway 아키텍처와 Zonal Architecture(영역 컨트롤러) 의 보안 관점 장단점을 평가하라.

??? answer "정답 / 해설"
    **Central Gateway** : 모든 도메인 트래픽이 한 곳을 지나 → 정책/IDS 집중 관리 쉬움. but 단일 장애점(SPOF) + 트래픽 병목.

    **Zonal Architecture** : 영역별(예: 좌앞/우앞/좌뒤/우뒤) 컨트롤러가 가까운 ECU 를 묶어 처리, 영역 간은 고대역 Ethernet backbone. 보안 장점은 **격리 단위가 작아지고 와이어 길이 ↓ → tampering 표면 ↓**. 단점은 영역 컨트롤러 각자가 보안 능력(HSM/IDS) 을 갖춰야 해 비용/복잡도 ↑.

    추세는 Zonal — 차세대 E/E 아키텍처에서 표준화 중.
