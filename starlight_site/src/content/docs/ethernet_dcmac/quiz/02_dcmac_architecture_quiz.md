---
pagefind: false
title: "Quiz — Module 02: DCMAC Architecture"
---

[← Module 02 본문으로 돌아가기](../../02_dcmac_architecture/)

---

## Q1. (Remember)

DCMAC이 통합하는 3개 layer는?

<details>
<summary>정답 / 해설</summary>

**MAC + PCS + FEC**. Frame 생성/파싱(MAC) + 인코딩/scrambling/alignment(PCS) + RS-FEC. 보통 별도 IP로 통합 → AMD DCMAC가 한 IP로 묶음.

**해설.** 전통적인 Ethernet 구현에서는 MAC, PCS, FEC가 서로 다른 IP 블록으로 분리되어 있어 인터페이스 클럭 도메인 교차, 타이밍 클로저, 보드 설계 복잡성이 높았다. DCMAC는 이 세 layer를 단일 하드 IP로 통합함으로써 이러한 시스템 설계 부담을 줄이고 라인 레이트 처리를 보장한다. "PHY"를 세 번째 layer로 답하는 오류가 흔한데, PHY는 전기 신호 송수신을 담당하는 별도 칩(Transceiver 등)으로, DCMAC 내부 IP 경계 밖에 위치한다.

</details>
## Q2. (Understand)

RS(528,514)의 의미는?

<details>
<summary>정답 / 해설</summary>

Reed-Solomon FEC code. **528 = total symbols, 514 = data symbols, 14 = parity symbols**. 패리티로 최대 **7 symbol** error 복원 가능 (parity/2).

**해설.** RS(n, k) 표기에서 n은 codeword의 전체 symbol 수, k는 그 중 실제 데이터 symbol 수를 의미한다. 나머지 n−k = 14개가 패리티 symbol이며, Reed-Solomon 코드의 수정 능력은 t = (n−k)/2 = 7이다. 즉 codeword 하나에서 최대 7개의 symbol이 오류가 나도 완전히 복원할 수 있다. "14개 symbol 오류까지 수정 가능"이라는 오답은 parity를 2로 나누지 않은 실수다. 8개 이상의 symbol error는 detect은 되지만 복원이 불가능해 프레임 drop으로 처리된다.

</details>
## Q3. (Apply)

400GbE를 8×50G PAM4로 구성할 때, 한 lane이 fail하면?

<details>
<summary>정답 / 해설</summary>

Lane redundancy 없으면 link 전체 down. PCS의 lane alignment가 깨지므로 모든 lane이 retraining 필요. RS-FEC도 lane 단위가 아닌 codeword 단위라 단일 lane fail은 spec 외 동작.

**해설.** 400GbE의 8 lane은 PCS layer에서 alignment marker를 기준으로 서로 동기화된 상태를 유지하는데, 한 lane이 신호를 잃으면 alignment 자체가 무효화된다. RS-FEC의 codeword는 여러 lane에 걸쳐 분산되어 있으므로 단일 lane 장애는 복수 codeword를 동시에 손상시켜 FEC 복원 능력을 초과하게 된다. "FEC가 1 lane 오류 정도는 커버한다"는 직관적 오답이 자주 등장하지만, FEC는 symbol error를 수정하는 것이지 lane 장애를 masking하는 설계가 아님을 이해해야 한다. 결론적으로 하나의 lane failure는 link 전체를 down시키고 전 lane retraining이 필요하다.

</details>
## Q4. (Analyze)

Auto-negotiation과 Link Training의 책임 분리는?

<details>
<summary>정답 / 해설</summary>

- **Auto-negotiation**: 두 link partner 간 capability 협상 (speed/duplex/FEC/pause). 결과: 둘 다 지원하는 최고 모드 선택.
- **Link Training**: 협상 완료 후 PCS 동기화, lane alignment, BER 측정, equalization 튜닝. 물리적 link을 실제로 작동 상태로 만듦.

**해설.** Auto-negotiation은 "무엇을 쓸 것인가"를 결정하는 협상 단계다. 두 장비가 Fast Link Pulse를 교환해 공통 능력(최대 속도, FEC 사용 여부, Pause 지원 등)을 확인하고 합의한다. Link Training은 협상이 끝난 뒤 "실제로 동작하게 만드는" 단계로, 각 lane의 equalization 계수를 조정하고 BER이 허용 범위 안에 들어올 때까지 tuning한다. 두 단계를 혼동해 "Link Training이 속도를 결정한다"고 오해하는 경우가 있는데, 속도 결정은 Auto-negotiation의 역할이고 Link Training은 그 속도에서 정상 동작하도록 물리 채널을 조정하는 것이다.

</details>
## Q5. (Evaluate)

Multi-channel (4×100G) 환경에서 가장 미묘한 silent bug는?

<details>
<summary>정답 / 해설</summary>

**Lane reorder / mismatch**. PCS가 lane을 잘못 매핑하면 데이터가 다른 channel에 흘러감 → CRC는 통과하지만 wrong destination → silent corruption (TX는 channel 0로 보냈는데 RX는 channel 1에서 받음). Lane skew compensation의 정확성이 핵심.

**해설.** Silent bug란 에러 카운터가 올라가지 않고, FCS/CRC 체크도 통과하지만 실제로는 잘못된 데이터가 전달되는 상황이다. Lane mismatch의 경우 프레임 자체는 물리적으로 손상되지 않았기 때문에 FCS는 정상 통과하지만, 수신 channel 번호가 틀려 데이터가 엉뚱한 논리 포트로 전달된다. 네트워크 레벨에서는 보안 침해나 데이터 오염으로 이어질 수 있어 모든 오류 중 가장 위험하다. "FCS 에러가 없으면 문제 없다"는 오해가 이 bug를 장기간 발견하지 못하게 만드는 원인이므로, 검증 시 channel 번호 일치 여부를 scoreboard에서 명시적으로 확인해야 한다.

</details>
