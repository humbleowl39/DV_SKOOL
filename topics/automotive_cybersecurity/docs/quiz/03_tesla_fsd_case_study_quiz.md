# Quiz — Module 03: Tesla FSD Case Study

[← Module 03 본문으로 돌아가기](../03_tesla_fsd_case_study.md)

---

## Q1. (Remember)

2023 Pwn2Own Tesla FSD 탈옥의 출발점이 된 두 약점은?

??? answer "정답 / 해설"
    1. **CAN 통신의 무인증** — 내부 메시지에 SecOC 미적용.
    2. **로컬 Feature Flag 의존** — FSD 활성화 여부를 차량 내 NVRAM 의 플래그로 결정 → 변조 가능.

## Q2. (Understand)

SCS(보안 칩) 가 있어도 탈옥이 가능했던 이유는?

??? answer "정답 / 해설"
    SCS 가 보호한 영역은 **Secure Boot · OTA 검증 · Cloud 인증** 등 "외부 경계" 였고, **CAN 인증** 은 SCS 의 적용 범위 밖에 있었다. 즉, 보안 IP 가 있다는 사실 자체보다 **"어디에 적용되어 있는가"** 가 결정적이다.

## Q3. (Apply)

자기 회사의 ECU 한 종류를 골라 Tesla 사례를 적용해 위협 모델을 만들 때 던져야 할 5가지 질문은?

??? answer "정답 / 해설"
    1. 부팅 검증은 어디까지 이어지는가? (Stage 별 chain of trust)
    2. 런타임 통신(CAN/Ethernet) 도 인증되는가, 아니면 부팅만 보호되는가?
    3. 정책(Feature Flag, mode switch) 이 로컬에 저장되는가, 클라우드 서명/대조가 있는가?
    4. 외부 신호(GPS, V2X) 를 단독 보안 통제로 쓰고 있지는 않은가?
    5. AUTOSAR 등 표준 스택을 안 쓴다면, 같은 기능을 자체 구현했는지 확인했는가?

## Q4. (Analyze)

Tesla 탈옥 체인의 단계를 ① 기술적 결함 ② 정책적 결함 ③ 아키텍처 결함으로 분류하라.

??? answer "정답 / 해설"
    - **기술적 결함** : CAN 메시지 무인증, GPS spoofing 가능성.
    - **정책적 결함** : "이 지역에서는 FSD 비활성" 같은 통제가 로컬 플래그로 결정됨, OTA 후 검증이 차량 내부에 머무름.
    - **아키텍처 결함** : 외부 경계만 SCS 로 보호하고 내부 경계(CAN) 를 신뢰함. AUTOSAR 생태계 밖에서 자체 SW 스택 사용 → SecOC 누락.

    이 3축을 모두 갖추지 못하면 보안 IP 만으로는 부족하다.

## Q5. (Evaluate)

같은 사건이 SecOC + Cloud 검증 기반 OEM 에서 발생할 수 있는가? 평가하라.

??? answer "정답 / 해설"
    **가능성 ↓ (그러나 0은 아님)**.
    - SecOC 가 있으면 외부 노드의 CAN 주입이 거의 불가능 (MAC 검증 실패).
    - Cloud 검증이 있으면 차량 내부 플래그만 바꿔도 서버 측 정책과 충돌해 거부 가능.

    그러나:
    - **합법 ECU 가 침해되면** SecOC 도 통과 가능 → IDS + 키 회수 정책 필요.
    - **Cloud 통신 자체가 가용성 의존** → 통신 단절 시 정책 fallback 의 보수성 점검 필요.

    결론: 다층 방어가 있으면 같은 종류의 단순 탈옥은 막히지만, 공격자는 다른 surface 로 이동한다 — 보안은 끝이 없다.
