# Quiz — Module 05: TOE Quick Reference

[← Module 05 본문으로 돌아가기](../05_quick_reference_card.md)

---

## Q1. (Recall)

TCP 3-way handshake와 4-way close 흐름을 sequence로 답하세요.

??? answer "정답 / 해설"
    **3-way open**: SYN → SYN/ACK → ACK
    **4-way close**: FIN → ACK → FIN → ACK

    Active close 측은 TIME_WAIT 상태로 2 × MSL (Maximum Segment Lifetime) 대기.

## Q2. (Recall)

5-tuple은 어떤 필드들로 구성되나?

??? answer "정답 / 해설"
    **Source IP + Source Port + Destination IP + Destination Port + Protocol**. RSS hash, connection table key 등에 사용.

## Q3. (Apply)

MTU=1500일 때 TCP MSS는?

??? answer "정답 / 해설"
    MSS = MTU - IP header (20) - TCP header (20) = **1460 bytes**. (옵션이 있으면 더 작아짐, e.g., timestamp option 12 bytes → MSS=1448).

## Q4. (Apply)

LRO를 적용 시 latency-sensitive 워크로드에 미치는 영향은?

??? answer "정답 / 해설"
    LRO는 다수 segment를 합쳐서 SW로 한 번에 전달 → **latency 증가** (첫 segment가 다음 segment 대기). Throughput에는 유리하지만 RPC, real-time 워크로드는 LRO disable 권장.

## Q5. (Evaluate)

다음 중 Production NIC silicon에 가장 위험한 결함은?

- [ ] A. Throughput 5% 저하
- [ ] B. Connection table SRAM ECC 미적용
- [ ] C. RTO 10% 더 길게
- [ ] D. RSS distribution 약간 비균등

??? answer "정답 / 해설"
    **B**. ECC 없이 SRAM bit flip → connection state corruption → silent data integrity 사고. Production data center에서 cosmic ray + 시간 = inevitable. 검증보다 ECC 적용이 mitigation. A/C/D는 성능 영향이지만 silent 아님.
