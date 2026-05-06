# Quiz — Module 04: Ethernet & DCMAC Quick Reference

[← Module 04 본문으로 돌아가기](../04_quick_reference_card.md)

---

## Q1. (Recall)

100GbE의 lane 구성 옵션 2가지는?

??? answer "정답 / 해설"
    - **4 × 25G** (NRZ) — 전통적 구성
    - **2 × 50G** (PAM4) — 새로운 구성, lane 수 ↓ + lane 당 BW ↑

## Q2. (Recall)

RS(528,514)의 correction capability는?

??? answer "정답 / 해설"
    Symbol 단위로 **최대 7 symbol error 복원**. 14 parity symbols / 2 = 7. 7 초과면 detect만 가능 (uncorrectable), frame drop.

## Q3. (Apply)

Pause vs PFC의 적합 사용 시나리오는?

??? answer "정답 / 해설"
    - **Pause (802.3x)**: 단일 트래픽 클래스 환경 — buffer overflow 임박 시 일괄 정지. 단순.
    - **PFC (802.1Qbb)**: QoS 차등 환경 — RDMA over Converged Ethernet (RoCE) 같은 lossless 트래픽만 pause, best-effort는 계속.

## Q4. (Apply)

Frame이 100GbE link에서 어떻게 4 lane으로 분배되는가?

??? answer "정답 / 해설"
    PCS layer가 64b/66b 인코딩 후 **bit/symbol 단위로 4 lane에 round-robin 분배**. RX에서 lane align (alignment marker로 동기) → 원래 순서로 재구성. Lane skew compensation이 필요.

## Q5. (Evaluate)

다음 중 DCMAC 검증의 가장 큰 도전은?

- [ ] A. Multi-channel + RS-FEC 동시 동작
- [ ] B. AXI-Stream protocol compliance
- [ ] C. VLAN tagging
- [ ] D. Frame size enforcement

??? answer "정답 / 해설"
    **A**. Multi-channel은 lane mapping/alignment, RS-FEC는 codeword 처리 — 둘 다 동시에 동작하면서 라인 레이트 throughput 유지가 가장 어려움. Lane fail + FEC corner case + multi-channel ordering의 조합 시나리오가 silent bug의 sweet spot.
