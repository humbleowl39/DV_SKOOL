---
title: "Quiz — Module 01: 왜 CXL인가"
---

[← Module 01 본문으로 돌아가기](../../01_motivation/)

---

## Q1. (Remember)

CXL이 등장한 두 가지 핵심 동기로 가장 알맞은 것은?

- [ ] A. 더 높은 클럭 속도와 더 낮은 전력
- [ ] B. Memory Wall(메모리 용량 한계)과 가속기-CPU 간 일관성 비용
- [ ] C. PCIe 슬롯 수 증가와 케이블 길이 연장
- [ ] D. 디스플레이 대역폭과 USB 통합

<details>
<summary>정답 / 해설</summary>

**B**. CXL은 두 문제를 동시에 풉니다. 메인보드 DIMM 슬롯 한계로 RAM을 더 못 꽂는 Memory Wall, 그리고 가속기가 호스트 메모리를 쓸 때마다 PCIe DMA 복사와 일관성 관리에 드는 비용입니다. PCIe 슬롯을 활용해 메모리를 확장하고, .cache로 일관성을 HW가 보장하게 합니다.

</details>
## Q2. (Understand)

"CXL은 PCIe를 대체하는 차세대 버스다"라는 진술이 틀린 이유를 설명하라.

<details>
<summary>정답 / 해설</summary>

CXL은 PCIe를 대체하지 않고 그 **물리 계층(electricals, connector, retimer) 위에 얹히는 대안 프로토콜**입니다. 같은 슬롯·핀을 재사용하며, CXL.io 프로토콜 자체가 PCIe TLP/DLLP 그대로입니다. 부팅 시 Flex Bus 협상에서 CXL을 지원하면 CXL 모드, 아니면 PCIe Native 모드로 동작하고, 협상 실패 시 PCIe로 폴백합니다. CXL이 추가한 것은 그 위에 얹은 .cache와 .mem 두 coherent 프로토콜뿐입니다.

</details>
## Q3. (Apply)

가속기가 호스트 메모리의 한 cacheline을 자주, 세밀하게 읽고 쓰는 워크로드가 있다. PCIe DMA 대신 CXL.cache를 쓰면 얻는 실질적 이점은?

- [ ] A. 전송 대역폭이 무조건 2배가 된다
- [ ] B. cacheline 단위 Load/Store + HW 일관성으로 복사·SW flush 없이 공유
- [ ] C. 암호화가 자동으로 적용된다
- [ ] D. 호스트 CPU가 꺼진다

<details>
<summary>정답 / 해설</summary>

**B**. PCIe DMA는 producer-consumer 모델로, 큰 버퍼를 복사하고 SW가 flush/invalidate로 일관성을 관리해야 합니다. CXL.cache는 cacheline 단위 Load/Store에 HW가 GO/snoop으로 일관성을 자동 보장하므로, 가속기가 호스트 데이터를 복사 없이 "자기 캐시처럼" 다룹니다. 잦고 세밀한 접근에서 특히 유리합니다.

</details>
## Q4. (Analyze)

같은 외부 메모리를 PCIe DMA와 CXL.mem으로 접근할 때, 일관성 관리 책임이 각각 누구에게 있는지 분석하라.

<details>
<summary>정답 / 해설</summary>

- **PCIe DMA**: 일관성은 **소프트웨어(드라이버/OS)** 책임. 디바이스가 호스트 메모리를 복사해 가면 SW가 명시적으로 cache flush/invalidate를 호출해 stale을 막아야 합니다.
- **CXL.mem(.cache와 결합)**: 일관성은 **하드웨어** 책임. GO, snoop, 디렉토리가 호스트와 디바이스 캐시 상태를 자동 동기화하므로 SW는 Load/Store만 하면 됩니다.

이 차이 때문에 CXL은 "복사 없이 공유"가 가능하고, 잦은 세밀 접근에서 PCIe DMA보다 유리합니다.

</details>
## Q5. (Evaluate)

CXL.io가 이미 MemRd/MemWr TLP로 메모리 접근을 지원하는데, 별도로 CXL.mem을 두는 결정이 타당한지 평가하라.

<details>
<summary>정답 / 해설</summary>

타당합니다. TLP는 producer-consumer DMA 의미에 최적화되어 헤더 오버헤드와 ordering 규칙이 cacheline 단위 잦은 접근에 비효율적입니다. CXL.mem(M2S/S2M)은 메모리 컨트롤러 수준의 간결한 요청/응답으로 저지연 Load/Store를 제공해 외부 메모리를 로컬 DRAM에 가깝게 다룹니다. 또한 .mem은 .cache와 결합해 HW 일관성을 제공하지만 .io의 MemRd/MemWr는 일관성을 SW에 맡깁니다. 목적(대량 전송 vs 세밀 공유)이 달라 두 프로토콜이 공존하는 것이 합리적입니다.

</details>
