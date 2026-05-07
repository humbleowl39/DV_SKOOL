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

## Q2. (Understand)

Phase 1 와 Phase 2 의 EQ 차이는?

??? answer "정답 / 해설"
    - **Phase 1**: **Downstream Port (DP) 의 Tx FFE** 를 Upstream Port (UP) 의 Rx 가 협상해 변경. DP→UP 방향의 BER 최적화.
    - **Phase 2**: **Upstream Port (UP) 의 Tx FFE** 를 DP 의 Rx 가 협상해 변경. UP→DP 방향의 BER 최적화.

    즉 양 방향을 따로 EQ. Phase 0 = preset 합의, Phase 3 = 안정 확인.

## Q3. (Apply)

Lane 0 의 polarity 가 board 에서 inverted 된 보드를 가지고 link 가 정상 동작하려면?

??? answer "정답 / 해설"
    **PCIe spec 가 자동 처리**.

    Polarity Inversion 검출은 PHY 의 Polling 단계에서 자동 수행:

    - Receiver 가 TS1 ordered set 의 K28.5 symbol 의 disparity 를 검사.
    - Inverted 면 internal 에서 + / - 를 swap.
    - 이후 link 는 정상 동작.

    Board designer 의 편의를 위해 routing 시 inversion 가능 → spec 가 부담을 PHY 로 흡수.

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
