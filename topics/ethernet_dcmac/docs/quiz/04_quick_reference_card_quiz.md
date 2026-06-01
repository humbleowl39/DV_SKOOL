# Quiz — Module 04: Ethernet & DCMAC Quick Reference

[← Module 04 본문으로 돌아가기](../04_quick_reference_card.md)

---

## Q1. (Recall)

100GbE의 lane 구성 옵션 2가지는?

??? answer "정답 / 해설"
    - **4 × 25G** (NRZ) — 전통적 구성
    - **2 × 50G** (PAM4) — 새로운 구성, lane 수 ↓ + lane 당 BW ↑

    **해설.** 100GbE는 도입 시점에 4×25G NRZ 구성이 표준이었으나, 이후 PAM4 변조 기술의 성숙으로 2×50G 구성이 추가되었다. lane 수를 절반으로 줄이면 PCB 배선 복잡성과 connector 핀 수가 줄어드는 장점이 있지만, PAM4 수신기는 SNR 여유가 NRZ 대비 훨씬 작아 signal integrity 설계가 어렵다. "100GbE는 무조건 4 lane"이라는 오답은 첫 번째 구성만 기억하는 데서 비롯되며, 실제 현장에서는 시스템 설계 조건에 따라 두 구성 중 하나를 선택한다.

## Q2. (Recall)

RS(528,514)의 correction capability는?

??? answer "정답 / 해설"
    Symbol 단위로 **최대 7 symbol error 복원**. 14 parity symbols / 2 = 7. 7 초과면 detect만 가능 (uncorrectable), frame drop.

    **해설.** RS(528,514)에서 패리티 symbol은 528 − 514 = 14개다. Reed-Solomon 코드의 수정 능력 t = (패리티 수)/2 = 7이므로, codeword당 최대 7개 symbol까지 오류가 있어도 원래 데이터로 복원된다. 경계 조건인 "정확히 7 symbol error"는 복원 가능하고, "8 symbol error"는 detect만 되고 복원 불가로 프레임이 drop된다. "14 symbol까지 수정 가능"이라는 오답은 패리티 수를 그대로 수정 능력으로 혼동한 것이며, 검증에서는 7 이하(within), 8 이상(beyond) 두 경계를 모두 테스트해야 한다.

## Q3. (Apply)

Pause vs PFC의 적합 사용 시나리오는?

??? answer "정답 / 해설"
    - **Pause (802.3x)**: 단일 트래픽 클래스 환경 — buffer overflow 임박 시 일괄 정지. 단순.
    - **PFC (802.1Qbb)**: QoS 차등 환경 — RDMA over Converged Ethernet (RoCE) 같은 lossless 트래픽만 pause, best-effort는 계속.

    **해설.** 선택의 기준은 트래픽 이질성이다. 동일한 우선순위의 트래픽만 흐르는 단순 환경에서는 Pause frame이 구현 비용이 낮고 동작이 예측 가능하다. 반면 RoCE(RDMA over Converged Ethernet)처럼 패킷 loss에 절대적으로 민감한 트래픽과 일반 TCP 트래픽이 공존하는 환경에서는, Pause frame을 사용하면 lossless가 필요한 트래픽을 보호하기 위해 TCP 트래픽까지 불필요하게 중단된다. PFC는 이 문제를 해결하지만 deadlock(우선순위 간 순환 의존) 위험이 생겨 주의가 필요하다. "RoCE 환경에서는 무조건 PFC가 필요하다"는 핵심 원칙으로 기억해 두면 된다.

## Q4. (Apply)

Frame이 100GbE link에서 어떻게 4 lane으로 분배되는가?

??? answer "정답 / 해설"
    PCS layer가 64b/66b 인코딩 후 **bit/symbol 단위로 4 lane에 round-robin 분배**. RX에서 lane align (alignment marker로 동기) → 원래 순서로 재구성. Lane skew compensation이 필요.

    **해설.** 100GbE에서 단일 lane 125G를 구현하기 어렵기 때문에 PCS는 데이터를 여러 lane에 나누어 보낸다. 64b/66b 인코딩 단위로 round-robin 분배하면 각 lane은 25G만 처리하면 된다. 문제는 물리적으로 4개 lane의 전파 지연(skew)이 다를 수 있다는 점이다. RX side PCS는 alignment marker(각 lane에 주기적으로 삽입되는 패턴)를 감지해 lane별 지연을 측정하고, 가장 느린 lane 기준으로 빠른 lane을 지연시켜 정렬한 뒤 원래 순서로 재조립한다. "MAC layer가 lane 분배를 담당한다"는 오답은 MAC/PCS 책임 경계를 혼동한 것으로, lane level 처리는 전적으로 PCS의 역할이다.

## Q5. (Evaluate)

다음 중 DCMAC 검증의 가장 큰 도전은?

- [ ] A. Multi-channel + RS-FEC 동시 동작
- [ ] B. AXI-Stream protocol compliance
- [ ] C. VLAN tagging
- [ ] D. Frame size enforcement

??? answer "정답 / 해설"
    **A**. Multi-channel은 lane mapping/alignment, RS-FEC는 codeword 처리 — 둘 다 동시에 동작하면서 라인 레이트 throughput 유지가 가장 어려움. Lane fail + FEC corner case + multi-channel ordering의 조합 시나리오가 silent bug의 sweet spot.

    **해설.** B(AXI-Stream protocol compliance), C(VLAN tagging), D(frame size enforcement)는 모두 단독으로 동작할 때는 비교적 straightforward한 검증이다. A가 가장 어려운 이유는 multi-channel과 RS-FEC가 상호작용하기 때문이다. 4개 채널 각각의 lane alignment, 각 채널 내 FEC codeword 처리, 채널 간 ordering 일관성, 그리고 이 모든 것이 라인 레이트로 동시에 돌아가야 하는 조건이 중첩된다. 특히 채널 하나에 FEC 에러가 발생할 때 다른 채널의 throughput이 영향받지 않아야 한다는 격리 요구사항은 단일 채널 테스트에서는 절대 발견할 수 없는 종류의 버그를 만들어낸다.
