# Quiz — Module 01: UFS Protocol Stack

[← Module 01 본문으로 돌아가기](../01_ufs_protocol_stack.md)

---

## Q1. (Remember)

UFS 프로토콜 스택의 5계층을 위에서 아래로 나열하세요.

??? answer "정답 / 해설"
    1. **Application** (SCSI command)
    2. **UTP / UPIU** (transport, UFS frame)
    3. **UniPro** (link/network/transport, MIPI 표준)
    4. **M-PHY** (physical, MIPI 표준)
    5. **Storage media** (NAND flash)

## Q2. (Understand)

UFS와 NVMe의 가장 큰 차이는?

??? answer "정답 / 해설"
    - **UFS**: SCSI command 기반, queue depth 32, MIPI M-PHY (시리얼)
    - **NVMe**: register 기반, 수많은 queue (HW 제한 내), PCIe (시리얼)

    UFS는 모바일/임베디드 (전력 효율), NVMe는 서버/PC (높은 throughput).

## Q3. (Apply)

UFS 4.0의 HS Gear-5 throughput은?

??? answer "정답 / 해설"
    HS Gear-5 = 23.32 Gb/s per lane. UFS는 보통 2 lane (TX 2 + RX 2) → **약 46 Gb/s = 5.8 GB/s** raw. UPIU overhead 제외 후 실효 약 4-5 GB/s.

## Q4. (Analyze)

UPIU 형식이 SCSI CDB를 그대로 사용하지 않고 캡슐화하는 이유는?

??? answer "정답 / 해설"
    1. **UFS-specific 명령 추가**: Query (descriptor read/write), NOP, Reject 등 SCSI 외 명령
    2. **Task Tag 추가**: queue depth 32 식별
    3. **Header 표준화**: LUN, command set type, flags 등 UFS 단위에서 필요한 메타데이터
    4. **Future extension**: EHS (Extra Header Segment)로 확장 여지

## Q5. (Evaluate)

UFS가 eMMC를 대체한 가장 결정적 이유는?

??? answer "정답 / 해설"
    **Full-duplex + Command Queuing**. eMMC는 half-duplex (TX/RX 시분할), command queuing 없음 (command 1개씩 처리). UFS는 동시 32 command + TX/RX 분리 → 모바일 워크로드의 IOPS와 latency 모두 ↑. 추가로 시리얼 인터페이스로 EMI/PCB 라우팅 유리.
