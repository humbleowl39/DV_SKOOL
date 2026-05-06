# Quiz — Module 03: AXI-Stream

[← Module 03 본문으로 돌아가기](../03_axi_stream.md)

---

## Q1. (Remember)

AXI-Stream에서 패킷의 마지막 beat를 표시하는 신호는?

- [ ] A. TVALID
- [ ] B. TREADY
- [ ] C. TLAST
- [ ] D. TKEEP

??? answer "정답 / 해설"
    **C**. TLAST=1은 현재 beat가 패킷/프레임의 마지막임을 의미.

## Q2. (Understand)

AXI(memory-mapped)와 AXI-Stream의 가장 큰 본질적 차이는?

??? answer "정답 / 해설"
    **주소(address)의 유무**. AXI는 메모리 매핑 모델이라 모든 트랜잭션에 주소가 있음. AXI-Stream은 주소가 없는 단방향 점대점 데이터 흐름. 따라서 AXI는 read/write가 의미 있고, AXI-Stream은 그 구분 자체가 없음.

## Q3. (Apply)

512-bit (64-byte) AXI-Stream에서 1500-byte Ethernet 프레임을 전송하려면 몇 beat가 필요한가? 그리고 마지막 beat의 TKEEP은?

??? answer "정답 / 해설"
    - Beat 수: ceil(1500 / 64) = **24 beats**
    - 마지막 beat 유효 바이트: 1500 - (23 × 64) = **28 bytes**
    - 마지막 beat TKEEP: 하위 28 bit가 1, 상위 36 bit가 0

## Q4. (Analyze)

Master가 TVALID=1로 데이터를 보내는 중 Slave가 TREADY=0으로 stall했다. 이 상태에서 Master가 TDATA를 변경해도 되는가?

??? answer "정답 / 해설"
    **안 된다**. TVALID=1이 유지되는 동안 TDATA, TLAST, TKEEP 등 모든 신호는 그대로 유지. TREADY=1이 되어 전송이 완료된 후에야 다음 데이터로 전환 가능. 가장 흔한 protocol 위반.

## Q5. (Evaluate)

다음 시나리오에서 적절한 인터페이스를 고르세요.

| 시나리오 | AXI MM | AXI-Stream |
|----------|--------|------------|
| (a) CPU → DRAM 읽기/쓰기 | ? | ? |
| (b) AI accelerator weight stream | ? | ? |
| (c) Ethernet packet processing | ? | ? |
| (d) Peripheral 레지스터 설정 | ? | ? |

??? answer "정답 / 해설"
    - (a) **AXI MM** — 임의 주소 접근, read/write 양방향
    - (b) **AXI-Stream** — 연속된 weight 흐름, 주소 불필요
    - (c) **AXI-Stream** — 가변 길이 패킷 + TLAST
    - (d) **APB** — 단순 레지스터 access

    핵심 결정 기준: "주소 기반 access인가 vs 연속 data flow인가".
