---
title: "Quiz — Module 03: AXI-Stream"
---

[← Module 03 본문으로 돌아가기](../../03_axi_stream/)

---

## Q1. (Remember)

AXI-Stream에서 패킷의 마지막 beat를 표시하는 신호는?

- [ ] A. TVALID
- [ ] B. TREADY
- [ ] C. TLAST
- [ ] D. TKEEP

<details>
<summary>정답 / 해설</summary>

**C**. TLAST=1은 현재 beat가 패킷/프레임의 마지막임을 의미.

AXI-Stream은 주소가 없는 프로토콜이므로, 수신 측이 데이터의 경계를 알 수 있는 유일한 수단이 TLAST입니다. TVALID(A)는 Source가 유효한 데이터를 내보내고 있음을 나타내고, TREADY(B)는 Sink가 수신 가능함을 나타내는 흐름 제어 신호입니다. TKEEP(D)는 beat 내에서 어느 byte가 유효한지를 표시하는 byte-level 마스크입니다. 이 세 신호 중 어느 것도 패킷/프레임의 종료를 나타내지 않으며, 오직 TLAST만이 "이 beat가 패킷의 끝"임을 수신 측에 알려줍니다.

</details>
## Q2. (Understand)

AXI(memory-mapped)와 AXI-Stream의 가장 큰 본질적 차이는?

<details>
<summary>정답 / 해설</summary>

**주소(address)의 유무**. AXI는 메모리 매핑 모델이라 모든 트랜잭션에 주소가 있음. AXI-Stream은 주소가 없는 단방향 점대점 데이터 흐름. 따라서 AXI는 read/write가 의미 있고, AXI-Stream은 그 구분 자체가 없음.

AXI(memory-mapped)는 "어디에 쓰고, 어디서 읽을지"를 지정하는 주소 채널(AW, AR)이 존재하기 때문에, 임의 위치에 대한 read와 write를 각각 독립적으로 수행할 수 있습니다. 반면 AXI-Stream은 파이프처럼 데이터가 한 방향으로 흘러가는 모델이어서 주소 채널이 없고, 그에 따라 "읽기/쓰기"라는 개념 자체가 성립하지 않습니다. 이 근본적인 차이 때문에 AXI는 CPU/DMA처럼 "특정 주소의 데이터를 가져오거나 기록"하는 곳에, AXI-Stream은 AI accelerator weight feed나 Ethernet packet 처리처럼 "연속 데이터 흐름"이 있는 곳에 적합합니다.

</details>
## Q3. (Apply)

512-bit (64-byte) AXI-Stream에서 1500-byte Ethernet 프레임을 전송하려면 몇 beat가 필요한가? 그리고 마지막 beat의 TKEEP은?

<details>
<summary>정답 / 해설</summary>

- Beat 수: ceil(1500 / 64) = **24 beats**
- 마지막 beat 유효 바이트: 1500 - (23 × 64) = **28 bytes**
- 마지막 beat TKEEP: 하위 28 bit가 1, 상위 36 bit가 0

계산 절차를 단계별로 따라가면 이해하기 쉽습니다. 512-bit = 64-byte 버스로 1500-byte 프레임을 전송하면 1500 ÷ 64 = 23.4375이므로, 마지막 부분 beat까지 포함하면 총 24 beats가 필요합니다. 앞의 23 beats는 64 × 23 = 1472 bytes를 소모하고, 24번째 beat에는 1500 − 1472 = 28 bytes만 유효합니다. TKEEP은 beat 내 각 byte의 유효성을 1 bit씩 표시하는 64-bit 마스크이므로, 유효한 하위 28 byte에 해당하는 하위 28 bit는 1, 나머지 상위 36 bit는 0이 됩니다. 마지막 beat에는 동시에 TLAST=1이 함께 올라가서 이 beat가 패킷의 끝임을 알립니다.

</details>
## Q4. (Analyze)

Master가 TVALID=1로 데이터를 보내는 중 Slave가 TREADY=0으로 stall했다. 이 상태에서 Master가 TDATA를 변경해도 되는가?

<details>
<summary>정답 / 해설</summary>

**안 된다**. TVALID=1이 유지되는 동안 TDATA, TLAST, TKEEP 등 모든 신호는 그대로 유지. TREADY=1이 되어 전송이 완료된 후에야 다음 데이터로 전환 가능. 가장 흔한 protocol 위반.

VALID/READY 핸드셰이크 규칙에 따르면, 전송은 TVALID=1이면서 동시에 TREADY=1인 클럭 엣지에서 단 한 번 성립합니다. TREADY=0인 동안은 Sink가 아직 데이터를 받아들이지 못한 상태이므로, Source는 이전에 내보낸 데이터를 그대로 유지해야 합니다. 이 상태에서 TDATA를 변경하면 Sink는 "아직 수신하지 않은 이전 데이터" 대신 "새 데이터"를 받게 되어 패킷이 손상됩니다. 이 규칙은 TDATA뿐만 아니라 TLAST, TKEEP, TUSER 등 TVALID와 함께 동행하는 모든 사이드밴드 신호에 동일하게 적용됩니다.

</details>
## Q5. (Evaluate)

다음 시나리오에서 적절한 인터페이스를 고르세요.

| 시나리오 | AXI MM | AXI-Stream |
|----------|--------|------------|
| (a) CPU → DRAM 읽기/쓰기 | ? | ? |
| (b) AI accelerator weight stream | ? | ? |
| (c) Ethernet packet processing | ? | ? |
| (d) Peripheral 레지스터 설정 | ? | ? |

<details>
<summary>정답 / 해설</summary>

- (a) **AXI MM** — 임의 주소 접근, read/write 양방향
- (b) **AXI-Stream** — 연속된 weight 흐름, 주소 불필요
- (c) **AXI-Stream** — 가변 길이 패킷 + TLAST
- (d) **APB** — 단순 레지스터 access

핵심 결정 기준: "주소 기반 access인가 vs 연속 data flow인가".

프로토콜 선택은 "어떤 접근 패턴인가"로 결정됩니다. (a) CPU↔DRAM은 임의 주소에 read/write를 모두 수행하므로 AW/AR 채널이 있는 AXI MM이 필요합니다. (b) AI accelerator의 weight는 순차적으로 흘러들어가는 데이터 스트림이고 주소 지정이 불필요하므로 AXI-Stream이 적합합니다. (c) Ethernet 패킷은 가변 길이이고 TLAST로 패킷 경계를 표시할 수 있는 AXI-Stream이 자연스럽습니다. (d) 주변 장치 레지스터 설정은 접근 빈도가 낮고 단순한 read/write만 필요하므로, 가장 면적이 작은 APB가 최선입니다.

</details>
