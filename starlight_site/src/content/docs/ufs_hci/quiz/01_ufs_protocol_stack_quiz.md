---
title: "Quiz — Module 01: UFS Protocol Stack"
---

[← Module 01 본문으로 돌아가기](../../01_ufs_protocol_stack/)

---

## Q1. (Remember)

UFS 프로토콜 스택의 5계층을 위에서 아래로 나열하세요.

<details>
<summary>정답 / 해설</summary>

1. **Application** (SCSI command)
2. **UTP / UPIU** (transport, UFS frame)
3. **UniPro** (link/network/transport, MIPI 표준)
4. **M-PHY** (physical, MIPI 표준)
5. **Storage media** (NAND flash)

이 순서가 정답인 이유는 각 계층이 "위 계층 서비스를 아래 계층에게 위임"하는 계층적 캡슐화 원칙을 따르기 때문입니다. Application은 SCSI 명령만 알면 되고, 그 명령이 어떻게 전선을 타는지 알 필요가 없습니다. 반대로 M-PHY는 상위 명령의 내용은 모르고 비트 스트림만 처리합니다. 이 분리 덕분에 각 계층을 독립적으로 검증하거나 교체할 수 있어 DV 전략을 계층별로 분할하는 근거가 됩니다.

</details>
## Q2. (Understand)

UFS와 NVMe의 가장 큰 차이는?

<details>
<summary>정답 / 해설</summary>

- **UFS**: SCSI command 기반, queue depth 32, MIPI M-PHY (시리얼)
- **NVMe**: register 기반, 수많은 queue (HW 제한 내), PCIe (시리얼)

UFS는 모바일/임베디드 (전력 효율), NVMe는 서버/PC (높은 throughput).

두 프로토콜의 가장 근본적인 차이는 명령 모델과 물리 인터페이스입니다. UFS는 SCSI 명령 체계를 UPIU로 감싸는 방식을 채택해 기존 모바일 소프트웨어 스택과의 호환성을 유지하며, M-PHY는 저전압 시리얼 신호로 모바일 배터리 환경에 맞게 설계되었습니다. NVMe는 PCIe 대역폭을 직접 활용해 레지스터 기반으로 수천 개의 queue를 운용하므로 서버·PC의 고처리량 환경에 적합합니다. 따라서 적용 분야가 다른 것이지 어느 쪽이 우월하다고 단정할 수 없으며, DV 관점에서도 검증 대상 인터페이스와 command set이 완전히 달라집니다.

</details>
## Q3. (Apply)

UFS 4.0의 HS Gear-5 throughput은?

<details>
<summary>정답 / 해설</summary>

HS Gear-5 = 23.32 Gb/s per lane. UFS는 보통 2 lane (TX 2 + RX 2) → **약 46 Gb/s = 5.8 GB/s** raw. UPIU overhead 제외 후 실효 약 4-5 GB/s.

Gear-5가 23.32 Gb/s인 이유는 M-PHY HS-G5 Series B의 심볼 레이트에서 8b10b 또는 scrambling overhead를 제외한 값이기 때문입니다. 여기에 lane 수(2)를 곱하면 raw 대역폭이 나오지만, UPIU 헤더·UniPro 프레이밍 오버헤드가 존재하므로 실제 데이터 처리량은 raw 값보다 낮습니다. DV 시 대역폭 측정 테스트를 작성할 때는 이 overhead를 감안한 실효 목표치(4~5 GB/s)를 기준으로 coverage goal을 설정해야 합니다.

</details>
## Q4. (Analyze)

UPIU 형식이 SCSI CDB를 그대로 사용하지 않고 캡슐화하는 이유는?

<details>
<summary>정답 / 해설</summary>

1. **UFS-specific 명령 추가**: Query (descriptor read/write), NOP, Reject 등 SCSI 외 명령
2. **Task Tag 추가**: queue depth 32 식별
3. **Header 표준화**: LUN, command set type, flags 등 UFS 단위에서 필요한 메타데이터
4. **Future extension**: EHS (Extra Header Segment)로 확장 여지

SCSI CDB 자체는 명령 opcode와 LBA·길이 정보만 포함하며, 동시 큐잉을 위한 태그나 UFS 자체 관리 명령(Query, NOP 등)을 표현하는 필드가 없습니다. UPIU 캡슐화는 SCSI 레거시를 유지하면서도 UFS에 필요한 메타데이터를 헤더에 추가하는 방식으로 이 문제를 해결합니다. 예를 들어 Task Tag 없이는 32개 명령이 동시에 진행 중일 때 어떤 응답이 어떤 명령에 대한 것인지 식별할 수 없어 silent corruption이 발생합니다. EHS는 미래 확장을 위해 헤더를 고정 크기로 제한하지 않는 설계이기도 합니다.

</details>
## Q5. (Evaluate)

UFS가 eMMC를 대체한 가장 결정적 이유는?

<details>
<summary>정답 / 해설</summary>

**Full-duplex + Command Queuing**. eMMC는 half-duplex (TX/RX 시분할), command queuing 없음 (command 1개씩 처리). UFS는 동시 32 command + TX/RX 분리 → 모바일 워크로드의 IOPS와 latency 모두 ↑. 추가로 시리얼 인터페이스로 EMI/PCB 라우팅 유리.

eMMC의 근본적 한계는 버스를 TX와 RX가 공유하는 half-duplex 구조와 단일 큐 모델에 있습니다. 스마트폰에서 동영상 촬영(쓰기)과 앱 로딩(읽기)이 동시에 발생하는 상황을 생각하면, eMMC는 두 작업이 버스를 번갈아 사용해야 하므로 각각의 latency가 올라갑니다. UFS는 TX/RX 경로를 물리적으로 분리하고 최대 32개 명령을 동시에 큐잉하므로 이러한 혼재 워크로드에서 실질적인 성능 차이가 납니다. 시리얼 인터페이스로의 전환은 핀 수 절감과 PCB 설계 단순화라는 부가적인 이점도 제공합니다.

</details>
