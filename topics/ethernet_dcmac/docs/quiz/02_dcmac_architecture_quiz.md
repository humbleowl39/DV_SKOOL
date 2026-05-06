# Quiz — Module 02: DCMAC Architecture

[← Module 02 본문으로 돌아가기](../02_dcmac_architecture.md)

---

## Q1. (Remember)

DCMAC이 통합하는 3개 layer는?

??? answer "정답 / 해설"
    **MAC + PCS + FEC**. Frame 생성/파싱(MAC) + 인코딩/scrambling/alignment(PCS) + RS-FEC. 보통 별도 IP로 통합 → AMD DCMAC가 한 IP로 묶음.

## Q2. (Understand)

RS(528,514)의 의미는?

??? answer "정답 / 해설"
    Reed-Solomon FEC code. **528 = total symbols, 514 = data symbols, 14 = parity symbols**. 패리티로 최대 **7 symbol** error 복원 가능 (parity/2).

## Q3. (Apply)

400GbE를 8×50G PAM4로 구성할 때, 한 lane이 fail하면?

??? answer "정답 / 해설"
    Lane redundancy 없으면 link 전체 down. PCS의 lane alignment가 깨지므로 모든 lane이 retraining 필요. RS-FEC도 lane 단위가 아닌 codeword 단위라 단일 lane fail은 spec 외 동작.

## Q4. (Analyze)

Auto-negotiation과 Link Training의 책임 분리는?

??? answer "정답 / 해설"
    - **Auto-negotiation**: 두 link partner 간 capability 협상 (speed/duplex/FEC/pause). 결과: 둘 다 지원하는 최고 모드 선택.
    - **Link Training**: 협상 완료 후 PCS 동기화, lane alignment, BER 측정, equalization 튜닝. 물리적 link을 실제로 작동 상태로 만듦.

## Q5. (Evaluate)

Multi-channel (4×100G) 환경에서 가장 미묘한 silent bug는?

??? answer "정답 / 해설"
    **Lane reorder / mismatch**. PCS가 lane을 잘못 매핑하면 데이터가 다른 channel에 흘러감 → CRC는 통과하지만 wrong destination → silent corruption (TX는 channel 0로 보냈는데 RX는 channel 1에서 받음). Lane skew compensation의 정확성이 핵심.
