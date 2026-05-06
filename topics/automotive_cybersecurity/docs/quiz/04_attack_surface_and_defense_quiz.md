# Quiz — Module 04: Attack Surface & Defense

[← Module 04 본문으로 돌아가기](../04_attack_surface_and_defense.md)

---

## Q1. (Remember)

차량의 3대 공격 surface 축은?

??? answer "정답 / 해설"
    1. **물리** — OBD-II 포트, USB, NFC, 정비 포트.
    2. **무선** — Bluetooth, WiFi, Cellular, V2X.
    3. **공급망** — ECU 펌웨어, Tier-1 부품, OTA 서버.

## Q2. (Understand)

Defense-in-Depth 가 단일 방어보다 효과적인 이유를 한 문단으로 설명하라.

??? answer "정답 / 해설"
    어떤 단일 통제도 완벽하지 않으므로(키 노출, CVE, 휴먼 에러), 한 계층이 뚫려도 다음 계층이 차단할 수 있도록 **독립적인 통제**(인증/암호화 → 도메인 격리 → IDS → Cloud 검증) 를 직렬로 배치한다. 공격자는 모든 계층을 동시에 우회해야 하므로 비용이 기하급수적으로 증가한다.

## Q3. (Apply)

Bluetooth 페어링 ECU 에 대한 공격 표면 트리를 그릴 때 leaf 노드 4개와 각각의 방어를 매핑하라.

??? answer "정답 / 해설"
    | Leaf | 방어 |
    |------|------|
    | BlueBorne 류 RCE | 펌웨어 패치, ASLR, Secure Boot |
    | Pairing PIN bruteforce | rate limit, lockout |
    | MITM during pairing | Secure Simple Pairing(SSP) + OOB 검증 |
    | 페어링 후 권한 상승(LE) | 도메인 격리 + 메시지 화이트리스트(Gateway) |

## Q4. (Analyze)

V2X 환경에서 Sybil 공격이 단일 차량으로 가능한 이유와, SCMS 가 이를 제한하는 메커니즘 3가지를 분석하라.

??? answer "정답 / 해설"
    **Sybil 가능 이유** : V2X BSM 은 자율적으로 broadcast 되며, 수신자가 송신자의 물리 존재를 직접 확인할 수 없다. 한 차량이 인증서 여러 개를 사용해 "여러 차량인 척" 가능.

    **SCMS 의 통제** :
    1. **Pseudonym Certificate 수량 제한** — 한 차량당 발급 인증서 수와 동시 활성 수를 정책으로 제한.
    2. **Linkage Authority** — 가명 인증서들이 같은 차량의 것인지 추적 가능 (프라이버시 보존 하에).
    3. **Misbehavior Detection** — 수신측이 물리 plausibility(카메라/레이더/지도) 와 대조해 의심 시 보고 → CRL 등재.

## Q5. (Evaluate)

ISO/SAE 21434 의 TARA 절차를 자기 시스템(예: 자체 ECU 한 종류) 에 적용할 때 가장 흔한 함정 두 가지는?

??? answer "정답 / 해설"
    1. **Asset 정의 누락** — "데이터" 만 보고 "기능(예: 제동력 제어)" 을 자산으로 간주하지 못하면 안전 영향이 큰 위협을 놓친다.
    2. **Likelihood 의 과소 평가** — "물리 접근이 필요하니 가능성 낮음" 으로 분류하지만, 정비소·중고차 시나리오에서 물리 접근은 상시적이다. attack feasibility 를 최신 기준으로 재평가해야 한다.

    이 두 함정이 실제 OEM TARA 가 결과적으로 동일해지는 주요 이유다 → 별도 reviewer 의 challenge 가 필수.
