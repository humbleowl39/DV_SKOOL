---
title: "Quiz — Module 03: 데이터센터에서의 DPU와 DV 연관"
---

[← Module 03 본문으로 돌아가기](../../03_dpu_in_datacenter_and_dv/)

---

## Q1. (Remember)

DPU의 전형적 구조에서 호스트와 DPU를 연결하는 인터페이스는?

- [ ] A. Ethernet
- [ ] B. PCIe
- [ ] C. NVMe
- [ ] D. UART

<details>
<summary>정답 / 해설</summary>

**B**. spec §3은 호스트 인터페이스를 "PCIe를 통한 서버 연결"로 정의합니다. Ethernet/InfiniBand(A)는 DPU의 _고속 네트워크 인터페이스_ 로 네트워크 쪽 연결이고, NVMe(C)는 스토리지 프로토콜, UART(D)는 무관합니다.

</details>

## Q2. (Understand)

DPU 검증의 세 층위(IP 단독 / IP 간 통합 / 시스템 계약)에서 "Layer 1만 통과하면 검증 완료"가 왜 부족한지 설명하라.

<details>
<summary>정답 / 해설</summary>

IP 단독(Layer 1)은 각 IP의 프로토콜 준수만 확인합니다. 그러나 DPU에서는 한 요청이 여러 IP를 직렬로 통과하므로(본문 §3), 데이터 패스 라우팅·DMA·큐 같은 IP 간 통합(Layer 2)과 호스트 인터페이스·격리 같은 시스템 계약(Layer 3)에서야 드러나는 통합 결함이 실제 escape의 큰 부분입니다. 따라서 프로토콜 PASS는 시작일 뿐이며 통합·시스템 층위를 별도로 검증해야 합니다.

</details>

## Q3. (Apply)

새로 검증할 RDMA 엔진 IP에 "PCIe 호스트 인터페이스 동작"과 "호스트 격리"가 요구사항으로 붙었다. 이 요구사항의 출처를 설명하라.

<details>
<summary>정답 / 해설</summary>

RDMA 엔진은 DPU의 _전용 가속기_ 한 블록으로 통합되기 때문입니다(spec §3). DPU는 호스트 인터페이스(PCIe), 데이터 패스 엔진, 가속기를 하나로 묶고 인프라 서비스를 호스트와 격리(§1)하므로, 통합되는 IP는 자신의 프로토콜뿐 아니라 _DPU 시스템 계약_ (호스트 인터페이스 동작, 격리, 데이터 패스 연결)도 상속합니다(본문 §4.1). 따라서 이 요구사항은 IP가 고립 블록이 아니라 시스템의 일부라는 사실에서 나옵니다.

</details>

## Q4. (Apply)

"호스트의 원격 메모리 read" 요청이 DPU 내부에서 통과하는 블록을 순서대로 나열하라.

- [ ] A. RDMA → PCIe → Data Path → Ethernet
- [ ] B. Host Interface(PCIe) → Data Path → RDMA → TOE/Ethernet → 암호화/DMA
- [ ] C. Ethernet → RDMA → PCIe (호스트로 바로)
- [ ] D. Data Path만 단독 처리

<details>
<summary>정답 / 해설</summary>

**B**. 본문 §3 흐름: Host Interface(PCIe)로 요청 수신 → Data Path Engine이 RDMA 엔진으로 분류·라우팅 → RDMA 엔진이 원격 메모리 접근 의미 처리 → TOE/Ethernet이 전송·프레이밍으로 네트워크 송수신 → (수신) 암호화 가속기로 필요 시 복호화 후 DMA로 호스트 메모리 전달. 한 요청이 여러 IP를 직렬로 통과하므로 통합 검증이 필요합니다.

</details>

## Q5. (Analyze)

베어메탈 서비스 구성에서 격리 위반이 특히 심각한 결함으로 분류되는 이유를 분석하라.

<details>
<summary>정답 / 해설</summary>

베어메탈 서비스는 호스트에 하이퍼바이저를 두지 않고 DPU가 관리형 네트워크·스토리지를 제공합니다(spec §5). 하이퍼바이저라는 소프트웨어 격리 계층이 없으므로 테넌트 격리를 _DPU가 단독으로_ 보장합니다(본문 §5.2). 따라서 DPU의 격리가 뚫리면 이를 막아 줄 상위 계층이 없어 테넌트가 다른 데이터·제어 경로에 접근할 수 있고, 이는 곧 심각한 보안 결함이 됩니다. 격리는 운영 정책이 아니라 검증해야 할 하드웨어 동작입니다.

</details>

## Q6. (Evaluate)

금융 서비스용 DPU와 AI 클러스터용 DPU의 검증 계획에서 깊게 봐야 할 항목이 어떻게 달라지는지 평가하라.

<details>
<summary>정답 / 해설</summary>

워크로드의 우선순위가 검증 깊이를 결정합니다(spec §6, 본문 §4.3). **금융** 은 테넌트 격리·암호화 지연이 우선이므로 Security/Virtualization 도메인과 격리(Layer 3), 암호화 가속기 동작, 접근 제어 시나리오를 깊게 봐야 합니다. **AI 클러스터** 는 GPU·스토리지 간 데이터 이동 지연·처리량이 우선이므로 RDMA/Ethernet 데이터 패스 통합(Layer 2)의 처리량·지연을 깊게 봐야 합니다. 동일한 DPU라도 활성 기능과 우선순위가 다르면 검증 자원 배분도 달라져야 합니다.

</details>
