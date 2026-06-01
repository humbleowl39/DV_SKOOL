# Quiz — Module 05: PHY & LTSSM

[← Module 05 본문으로 돌아가기](../05_phy_ltssm.md)

---

## Q1. (Remember)

LTSSM 의 11 state 중 정상 동작 상태와 저전력 상태를 구분하라.

??? answer "정답 / 해설"
    - **정상 동작**: `L0`
    - **저전력**: `L0s` (짧은 idle), `L1`, `L1.1`, `L1.2`, `L2` (가장 깊음)
    - **Bring-up**: `Detect`, `Polling`, `Configuration`
    - **Recovery / Test**: `Recovery`, `Disabled`, `Loopback`, `Hot Reset`

    정상 데이터 전송이 가능한 상태는 오직 L0 뿐이다. L0s 는 짧은 idle 이 감지될 때 빠르게 진입하고 빠르게 복귀하는 얕은 절전 상태이며, L1 계열로 갈수록 더 많은 회로가 꺼지고 복귀 지연(exit latency)이 길어진다. Detect~Configuration 은 링크가 처음 켜질 때 한 번 거치는 bring-up 경로이고, Recovery 는 링크 오류나 재훈련이 필요할 때 L0 에서 잠시 벗어나 문제를 해결하고 다시 돌아오는 경로다.

## Q2. (Understand)

Phase 1 와 Phase 2 의 EQ 차이는?

??? answer "정답 / 해설"
    - **Phase 1**: **Downstream Port (DP) 의 Tx FFE** 를 Upstream Port (UP) 의 Rx 가 협상해 변경. DP→UP 방향의 BER 최적화.
    - **Phase 2**: **Upstream Port (UP) 의 Tx FFE** 를 DP 의 Rx 가 협상해 변경. UP→DP 방향의 BER 최적화.

    즉 양 방향을 따로 EQ. Phase 0 = preset 합의, Phase 3 = 안정 확인.

    Equalization 은 채널이 신호를 왜곡하는 방식을 양쪽이 협력해 보정하는 과정이다. Phase 1 과 Phase 2 가 대칭적으로 다른 방향을 담당하는 이유는 신호 경로가 양방향으로 독립적이기 때문이다. 즉 DP→UP 방향의 채널 특성과 UP→DP 방향의 채널 특성이 다를 수 있으므로 각 방향의 Tx 를 별도로 최적화해야 한다. Phase 0 이 초기 preset 을 합의하고 Phase 3 에서 결과를 안정 확인하는 것을 포함하면 4-phase 전체 구조가 된다.

## Q3. (Apply)

Lane 0 의 polarity 가 board 에서 inverted 된 보드를 가지고 link 가 정상 동작하려면?

??? answer "정답 / 해설"
    **PCIe spec 가 자동 처리**.

    Polarity Inversion 검출은 PHY 의 Polling 단계에서 자동 수행:

    - Receiver 가 TS1 ordered set 의 K28.5 symbol 의 disparity 를 검사.
    - Inverted 면 internal 에서 + / - 를 swap.
    - 이후 link 는 정상 동작.

    Board designer 의 편의를 위해 routing 시 inversion 가능 → spec 가 부담을 PHY 로 흡수.

    차동 쌍(differential pair)의 극성이 보드 레이아웃 실수로 뒤집혀도 링크가 동작하도록 PCIe 스펙은 PHY 가 Polling 단계에서 자동으로 검출하고 내부적으로 교정하도록 규정한다. 보드 설계자는 극성을 맞추지 않아도 되므로 라우팅 자유도가 높아진다. 검출 원리는 TS1 의 K28.5 콤마 심볼의 running disparity 방향을 분석하는 것이며, 이 경량 처리가 PHY 실리콘 안에서 자동으로 일어난다.

## Q4. (Analyze)

"Link 가 Recovery 에서 자주 빠진다" 는 증상에서 가능한 원인 3가지를 분석하라.

??? answer "정답 / 해설"
    1. **PHY signal integrity 악화**: BER 임계 초과 → DLL 의 NAK 빈발 → Replay Buffer overflow → DLL 이 link retrain trigger.
        - 점검: AER 의 correctable error counter, replay number rollover 카운터.
    2. **EQ preset 이 채널에 안 맞음**: Phase 1/2/3 의 결과가 매번 일관성 없음.
        - 점검: LTSSM trace, EQ phase 의 결과 분석.
    3. **온도 / 전원 노이즈**: 온도 변화로 SerDes margin 변동, 전원 droop.
        - 점검: 운영 환경의 정상 / 부하 / 고온 조건에서 비교.

    추가: SW 가 일부러 retrain 시킬 수도 있음 (Gen 변경, ASPM 진입 후 wakeup).

    Recovery 진입 자체는 정상 메커니즘이지만 빈발한다면 근본 원인이 있다는 신호다. 세 가지 원인은 인과 관계가 다르므로 구분이 중요하다. PHY 품질 문제라면 AER correctable count 가 함께 올라가고, EQ 불안정이라면 Recovery 가 반복될 때마다 같은 preset 이 합의되지 않아 LTSSM trace 에서 패턴이 보인다. 온도/전원 노이즈는 특정 부하 조건이나 온도 구간에서만 발생하므로 환경 변수와 상관관계를 보는 것이 핵심이다.

## Q5. (Evaluate)

"Gen6 PAM4 의 BER 이 Gen5 NRZ 보다 6 자릿수 높지만 FEC 가 보정한다" 는 spec 결정의 의미를 평가하라.

??? answer "정답 / 해설"
    **합리적 trade-off**.

    - PAM4 = 1 symbol 에 2 bit → throughput 2× without 2× clock.
    - 이를 위해 4-level 의 좁은 eye → BER 증가 (≈ 1e-6).
    - **FEC (Forward Error Correction)** + **FLIT mode** + **CRC/retry** 의 layered 보호로 effective BER 1e-12 미만 달성.

    **결정의 의미**:

    1. **물리 한계 회피**: NRZ 64 GT/s 는 채널 / connector 에서 가능 안 함.
    2. **Layered reliability**: FEC (즉시 보정) + ACK/NAK retry (마지막 보루) 의 결합으로 사용자 visible reliability 유지.
    3. **검증 복잡도 ↑**: PAM4 EQ + FEC + FLIT 모두 검증 영역 추가.
    4. **Migration cost**: 기존 packet trace 도구 / 디버그 노하우가 일부 obsolete.

    PCIe spec 이 PAM4 를 받아들인 시점이 산업 표준의 큰 분기점. 이후 모든 high-speed serial (Ethernet, OIF) 도 같은 방향.

    이 결정이 "합리적"인 핵심 근거는, BER 이 높아지더라도 FEC 가 하드웨어 수준에서 실시간으로 보정하여 사용자 관점의 effective BER 은 충분히 낮게 유지된다는 계층적 보호 설계에 있다. NRZ 로 64 GT/s 를 달성하려면 물리적으로 채널 손실을 극복할 수 없어 PAM4 가 유일한 실용적 경로였다. 검증 관점에서는 PAM4 EQ, FEC, FLIT mode 가 모두 새로운 검증 대상이 되므로 기존 Gen5 DV 경험을 Gen6 에 그대로 적용할 수 없다는 점에 주의해야 한다.
