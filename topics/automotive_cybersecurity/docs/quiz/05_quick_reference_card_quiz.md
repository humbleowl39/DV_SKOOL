# Quiz — Module 05: Quick Reference Card

[← Module 05 본문으로 돌아가기](../05_quick_reference_card.md)

---

## Q1. (Remember)

차량 보안 4-layer 표준 스택을 순서대로 나열하라.

??? answer "정답 / 해설"
    1. **HSM** (Root of Trust, 키 보호)
    2. **SecOC** (메시지 인증 + Freshness)
    3. **Secure Gateway** (도메인 격리, 라우팅 정책)
    4. **IDS** (이상 탐지) + Cloud 검증 (선택적 5층).

## Q2. (Apply)

면접에서 "CAN 이 왜 위험한가?" 라는 질문을 받았다. 30초 내에 답하기 위한 4-요점 템플릿은?

??? answer "정답 / 해설"
    1. CAN(1983) 은 인증/암호화가 없다 (broadcast).
    2. OBD-II 로 외부 접근이 합법적으로 열려 있다.
    3. 어떤 노드든 임의 ECU 를 가장해 메시지 송신 가능 (spoof + replay + flood).
    4. 그래서 SecOC + Gateway + IDS 가 필요 — UN R155 가 OEM 에 사실상 의무화.

## Q3. (Apply)

리뷰에서 자기 ECU 에 빠진 보안 계층을 빠르게 식별하는 체크리스트는?

??? answer "정답 / 해설"
    - [ ] HSM 또는 동등한 secure element 가 있는가?
    - [ ] Secure Boot 가 마지막 stage 까지 chain of trust 를 유지하는가?
    - [ ] CAN/Ethernet 메시지에 SecOC 또는 동등 인증이 있는가?
    - [ ] 도메인 사이에 Gateway 화이트리스트/rate limit 이 있는가?
    - [ ] IDS 또는 anomaly 로그가 V-SOC 로 전달되는가?
    - [ ] OTA 패키지가 서명 검증 + 롤백 보호되는가?

## Q4. (Evaluate)

UN R155(CSMS) 와 ISO/SAE 21434 의 관계를 한 줄로 평가하라.

??? answer "정답 / 해설"
    **R155 = "WHAT" (규제 요건)**, **21434 = "HOW" (엔지니어링 방법)**. R155 가 OEM 에 CSMS 를 요구하면 그 CSMS 의 구체적 활동(TARA, 검증 등) 은 21434 에 따라 수행되는 것이 사실상의 표준 경로. 둘은 보완 관계 — 어느 하나만으로는 부족.

## Q5. (Evaluate)

이 코스를 마친 학습자가 "차량 보안 엔지니어로 즉시 실전 투입 가능" 하기 위해 추가로 학습해야 할 4영역은?

??? answer "정답 / 해설"
    1. **AUTOSAR Classic / Adaptive 실 코드** — SecOC, CryIf, KeyM 모듈의 실제 사용.
    2. **AUTOSAR · UDS · DoIP 진단 보안** — Security Access(0x27), Authentication(0x29).
    3. **Penetration testing 도구** — CANalyzer / SocketCAN / 리버스 엔지니어링 (Ghidra, IDA).
    4. **TARA 실습** — 자기 시스템에 직접 적용 + 외부 reviewer 와의 challenge 사이클 경험.
