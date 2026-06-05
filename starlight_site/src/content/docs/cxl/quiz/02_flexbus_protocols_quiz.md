---
title: "Quiz — Module 02: Flex Bus & 3 프로토콜"
---

[← Module 02 본문으로 돌아가기](../../02_flexbus_protocols/)

---

## Q1. (Remember)

CXL.cache의 두 방향 채널 그룹으로 올바른 것은?

- [ ] A. M2S / S2M
- [ ] B. D2H / H2D
- [ ] C. TX / RX
- [ ] D. Req / Cpl

<details>
<summary>정답 / 해설</summary>

**B**. CXL.cache는 D2H(Device-to-Host)와 H2D(Host-to-Device) 채널로 동작하며, 각각 Req/Rsp/Data로 세분됩니다. M2S/S2M(A)은 CXL.mem의 채널입니다. "가속기가 호스트 메모리를 캐싱"하므로 디바이스가 요청 주체(D2H Req)입니다.

</details>
## Q2. (Understand)

CXL 4계층 스택에서 ARB/MUX 계층의 역할을 설명하라.

<details>
<summary>정답 / 해설</summary>

ARB/MUX는 .io / .cache / .mem 세 프로토콜을 **단일 Flex Bus 물리 링크에 시분할로 다중화**하는 계층입니다. vLSM이 프로토콜별 가상 링크 상태를 독립 관리하고, Arbiter가 Round-robin/WRR로 프로토콜 우선순위를 정하며, Multiplexer가 Flit을 물리 계층에 실어 보냅니다. 물리 링크는 하나지만 각 프로토콜이 자기 상태를 갖도록 가상화하는 것이 핵심입니다.

</details>
## Q3. (Apply)

"호스트가 가속기의 로컬 메모리에 데이터를 읽는다." 어느 프로토콜·어느 채널로 흐르며, 데이터는 어떤 응답으로 오는가?

- [ ] A. CXL.cache, D2H Req → H2D Data
- [ ] B. CXL.mem, M2S Req → S2M DRS
- [ ] C. CXL.io, MemRd TLP → Cpl
- [ ] D. CXL.cache, H2D Req → D2H Data

<details>
<summary>정답 / 해설</summary>

**B**. 가속기의 로컬 메모리(HDM)를 호스트가 접근하므로 **CXL.mem**입니다. 호스트(Master)가 M2S Req로 요청하고, 디바이스 메모리(Subordinate)가 데이터를 **S2M DRS(Data Response)** 로 돌려줍니다(데이터 없는 응답이면 S2M NDR). A/D처럼 .cache는 가속기가 *호스트* 메모리를 캐싱하는 반대 방향입니다.

</details>
## Q4. (Analyze)

CXL.cache의 Req/Rsp/Data 채널이 분리되어 있고 GO(Global Observation)가 별도 응답으로 오는 설계가, 디바이스의 데이터 사용 시점에 어떤 제약을 만드는지 분석하라.

<details>
<summary>정답 / 해설</summary>

응답(GO)과 데이터가 **다른 채널**로 오므로, 디바이스는 둘을 모두 받아야 cacheline을 안전하게 사용할 수 있습니다. GO는 "이 트랜잭션이 시스템 전체에서 일관성 있게 관측되었다"는 보장이며, **GO 수신 전에 데이터를 사용하면 프로토콜 위반**입니다. 만약 데이터(H2D Data)만 먼저 도착하고 GO(H2D Rsp)를 못 받은 상태에서 데이터를 쓰면, 다른 캐시와의 일관성이 깨질 수 있습니다. 따라서 검증에서 "GO 이전 데이터 사용"은 대표적 protocol checker 항목입니다.

</details>
## Q5. (Evaluate)

CXL 디바이스를 꽂았는데 링크가 PCIe Native로만 올라왔다. 가능한 원인과 확인 순서를 평가하라.

<details>
<summary>정답 / 해설</summary>

- **원인 후보**: (1) 한쪽이 CXL 미지원(TS1/TS2의 CXL Capable bit 미설정), (2) 8 GT/s 이상 진입 실패로 자동 폴백, (3) 보드 신호 무결성 문제로 고속 진입 불가.
- **확인 순서**: LTSSM 로그에서 (a) 수정된 TS1/TS2 Ordered Set 교환과 CXL Capable bit → (b) 속도 협상이 8 GT/s 이상 도달 여부 → (c) Recovery 단계의 폴백 분기.

Flex Bus는 8 GT/s 이상 진입 성공이 CXL 모드의 전제이므로, 속도 진입 실패가 가장 흔한 폴백 트리거입니다. 상위 프로토콜을 보기 전에 협상 단계부터 확인해야 합니다.

</details>
## Q6. (Analyze)

68B Flit과 256B Flit(CXL 3.0+)의 차이 중, 256B Flit이 FEC 필드를 포함하는 이유를 분석하라.

<details>
<summary>정답 / 해설</summary>

256B Flit은 CXL 3.0+에서 쓰이고, 이 세대는 64 GT/s 달성을 위해 **PAM4 시그널링**을 도입합니다. PAM4는 전압을 4단계로 나눠 신호 마진(SNR)이 좁아져 비트 오류 확률이 높아집니다. 재전송(LLR)만으로 이를 감당하면 지연·대역폭 손실이 크므로, 수신 측에서 재전송 없이 오류를 자체 정정하는 **FEC(Forward Error Correction)** 가 필수가 됩니다. 그래서 256B Flit에 FEC 필드(2B)가 포함됩니다. 68B Flit은 NRZ 환경(≤CXL 2.0)이라 FEC 없이 CRC + LLR로 충분했습니다.

</details>
