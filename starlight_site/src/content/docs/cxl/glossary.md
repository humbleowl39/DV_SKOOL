---
title: "CXL 용어집"
---

이 페이지는 본 코스에서 사용되는 CXL 핵심 용어 정의 모음입니다. 항목은 ISO 11179 형식을 따릅니다 (**Definition / Source / Related / Example / See also**).

:::tip[검색 활용]
상단 검색창에 용어를 입력하면 본문에서의 사용처도 함께 찾을 수 있습니다.
:::
---

## A — ALMP / ARB-MUX

### ALMP

**Definition.** ARB/MUX 계층이 양 끝단의 가상 링크 상태(vLSM)를 동기화하기 위해 교환하는 1 DWORD 크기의 링크 관리 패킷.

**Source.** CXL 3.1 Specification, §5 (ARB/MUX).

**Related.** ARB/MUX, vLSM, L1/L2/L0p 상태.

**Example.** Status.Active, Request.L1, Request.L2, Request.L0p 메시지로 전이 전 양단 상태를 합의합니다.

**See also.** [Module 04 — ARB/MUX & 패브릭](../04_arbmux_fabric/)

### ARB/MUX

**Definition.** CXL.io / CXL.cache / CXL.mem 세 프로토콜을 단일 Flex Bus 물리 링크에 시분할로 다중화하고 가상 링크 상태를 관리하는 계층.

**Source.** CXL 3.1 Specification, §5.

**Related.** vLSM, Arbiter, Multiplexer, Flit.

**Example.** Arbiter가 Round-robin/WRR로 프로토콜 우선순위를 정하고 Multiplexer가 Flit을 물리 계층에 실어 송출합니다.

**See also.** [Module 04](../04_arbmux_fabric/)

---

## B — Bias / BISnp

### Bias (Bias-based Coherency)

**Definition.** Type 2 디바이스 메모리의 소유권을 Host Bias(CPU 소유)와 Device Bias(가속기 소유) 두 상태로 동적으로 전환해 일관성과 성능을 조정하는 메커니즘.

**Source.** CXL 3.1 Specification, §3 (Coherence); HDG `CXL Overview` §2.3.

**Related.** Type 2, HDM-D, HDM-DB, BISnp.

**Example.** GPU 학습에서 데이터 로드는 Host Bias, 연산은 Device Bias, 결과 회수는 다시 Host Bias로 전환합니다.

**See also.** [Module 03 — 디바이스 타입 & Coherency](../03_device_types_coherency/)

### BISnp (Back-Invalidate Snoop)

**Definition.** Type 2 디바이스가 Bias 전환 또는 데이터 무결성 보호를 위해 S2M 채널로 호스트 캐시를 무효화하는 CXL 3.0+ 메커니즘.

**Source.** CXL 3.1 Specification, §3; HDG `CXL Overview` §3.3.

**Related.** S2M, HDM-DB, Device Bias, GO.

**Example.** 호스트 캐시라인이 Modified면 `BISnp Rsp + Modified Data`로 데이터까지 회수하고, clean이면 `BISnp Rsp (Ack)`만 받습니다.

**See also.** [Module 03](../03_device_types_coherency/)

---

## C — CXL.io / CXL.cache / CXL.mem

### CXL.io

**Definition.** PCIe TLP/DLLP를 그대로 사용해 enumeration, configuration, 인터럽트, DMA를 처리하는 CXL의 기반 프로토콜.

**Source.** CXL 3.1 Specification, §3; HDG `CXL Overview` §3.1.

**Related.** PCIe TLP, Flex Bus, PBR TLP Header.

**Example.** 부팅 시 디바이스 발견과 BAR 설정은 CXL.io로 수행됩니다.

**See also.** [Module 02 — Flex Bus & 3 프로토콜](../02_flexbus_protocols/)

### CXL.cache

**Definition.** 가속기(Device)가 호스트 메모리를 일관성을 유지하며 캐싱하기 위해 D2H/H2D 채널로 동작하는 CXL 프로토콜.

**Source.** CXL 3.1 Specification, §3; HDG `CXL Overview` §3.2.

**Related.** D2H, H2D, GO, snoop, Type 1/Type 2.

**Example.** 디바이스가 D2H Req(RdShared)로 요청하면 호스트가 H2D Rsp(GO-S) + H2D Data로 응답합니다.

**See also.** [Module 02](../02_flexbus_protocols/)

### CXL.mem

**Definition.** 호스트(Master)가 디바이스의 로컬 메모리(HDM)를 Load/Store로 접근하기 위해 M2S/S2M 채널로 동작하는 CXL 프로토콜.

**Source.** CXL 3.1 Specification, §3; HDG `CXL Overview` §3.1, §3.

**Related.** M2S, S2M, HDM, Type 2/Type 3, NDR/DRS.

**Example.** 호스트가 M2S Req로 읽기를 요청하면 디바이스 메모리가 S2M DRS(Data Response)로 데이터를 돌려줍니다.

**See also.** [Module 02](../02_flexbus_protocols/)

---

## D — DCD

### DCD (Dynamic Capacity Device)

**Definition.** Fabric Manager를 통해 메모리 용량을 온디맨드로 할당(Add)하고 회수(Release)하는 CXL 3.0+ 메모리 디바이스.

**Source.** CXL 3.1 Specification, §7; HDG `CXL Overview` §7.1.

**Related.** Fabric Manager, Memory Pooling, HDM, G-FAM.

**Example.** 호스트가 +64GB를 요청하면 FM이 Add Capacity(Region X)를 발행하고, workload 종료 후 Release로 풀에 반환합니다.

**See also.** [Module 04 — ARB/MUX & 패브릭](../04_arbmux_fabric/)

---

## F — Flex Bus / Flit

### Flex Bus

**Definition.** PCIe Electricals/Connector/Retimer를 재사용하면서 부팅 시 협상으로 PCIe 또는 CXL 모드를 선택하는 CXL의 물리 인터페이스.

**Source.** CXL 3.1 Specification, §6; HDG `CXL Overview` §1.2.

**Related.** LTSSM, TS1/TS2 OS, Alternate Protocol Negotiation, Fallback.

**Example.** 2.5 GT/s에서 시작해 수정된 TS1/TS2 OS로 CXL Capable을 확인하고, 8 GT/s 이상 진입 성공 시 CXL 모드로 동작합니다.

**See also.** [Module 02 — Flex Bus & 3 프로토콜](../02_flexbus_protocols/)

### Flit

**Definition.** CXL.cachemem 링크 계층이 데이터를 패킹하는 고정 크기 전송 단위 (68B 또는 256B).

**Source.** CXL 3.1 Specification, §4; HDG `CXL Overview` §4.1.

**Related.** CRC, FEC, LLR, 256B Latency-Optimized.

**Example.** 68B Flit은 16-bit Proto ID + 4개 16B Slot + 16-bit CRC로 구성되며, 256B Flit(CXL 3.0+)은 FEC 필드를 포함합니다.

**See also.** [Module 02](../02_flexbus_protocols/)

---

## G — GO

### GO (Global Observation)

**Definition.** 해당 트랜잭션이 시스템 전체에서 일관성 있게 관측되었음을 보장하는 CXL.cache의 응답 신호.

**Source.** CXL 3.1 Specification, §3; HDG `CXL Overview` §3.2.

**Related.** CXL.cache, H2D Rsp, coherency.

**Example.** 디바이스는 H2D Rsp로 GO-S(Shared)를 받기 전까지 데이터를 안전하게 사용할 수 없습니다.

**See also.** [Module 02](../02_flexbus_protocols/)

---

## H — HDM

### HDM (Host-managed Device Memory)

**Definition.** 디바이스의 로컬 메모리를 호스트 주소 공간에 노출해 호스트가 관리하거나 공유하는 CXL 메모리 모델 (HDM-H / HDM-D / HDM-DB).

**Source.** CXL 3.1 Specification, §2; HDG `CXL Overview` §2.2.

**Related.** Type 2, Type 3, Bias, BISnp.

**Example.** HDM-H는 Host-only(Type 3), HDM-D는 Device-managed(Type 2), HDM-DB는 Bias 공유 + BISnp(Type 2)입니다.

**See also.** [Module 03 — 디바이스 타입 & Coherency](../03_device_types_coherency/)

---

## L — LLR / LTSSM

### LLR (Link Layer Retry)

**Definition.** 전송 오류 발생 시 송신 측 Retry Buffer에 보관된 Flit을 재전송하는 CXL 링크 계층의 하드웨어 수준 복구 메커니즘.

**Source.** CXL 3.1 Specification, §4; HDG `CXL Overview` §4.2.

**Related.** Flit, CRC, Retry Buffer, ACK.

**Example.** Receiver가 CRC Mismatch를 감지하면 RETRY.Req를 보내고, Sender는 해당 Flit부터 재전송한 뒤 ACK를 받으면 버퍼에서 제거합니다.

**See also.** [Module 02 — Flex Bus & 3 프로토콜](../02_flexbus_protocols/)

### LTSSM

**Definition.** PCIe의 Link Training and Status State Machine으로, CXL은 이를 확장해 Flex Bus 모드 협상을 수행한다.

**Source.** PCI Express Base Specification; CXL 3.1 Specification §6.

**Related.** Flex Bus, TS1/TS2 OS, Recovery, Fallback.

**Example.** Polling에서 TS1/TS2 OS를 교환해 CXL Capable bit을 확인하고, Recovery에서 8 GT/s 이상 성공 시 CXL 모드로 분기합니다.

**See also.** [Module 02](../02_flexbus_protocols/)

---

## M — MLD

### MLD (Multi Logical Device)

**Definition.** 단일 물리 디바이스를 여러 Logical Device(최대 16)로 논리 분할해 다중 호스트가 나눠 쓰게 하는 CXL 2.0+ 기능.

**Source.** CXL 3.1 Specification, §9; HDG `CXL Overview` §2.4.

**Related.** Memory Pooling, G-FAM, PBR, Fabric.

**Example.** 큰 메모리 확장기 하나를 16개 LD로 나눠 16개 호스트가 각자 자기 몫을 사용합니다.

**See also.** [Module 04 — ARB/MUX & 패브릭](../04_arbmux_fabric/)

---

## P — PAM4 / PBR / Poison

### PAM4

**Definition.** 전압을 4단계로 나눠 한 심볼에 2비트를 전송하는 변조 방식으로, CXL 3.0+에서 64 GT/s 달성을 위해 도입된다.

**Source.** CXL 3.1 Specification, §6; HDG `CXL Overview` §6.3.

**Related.** NRZ, FEC, 256B Flit, SNR.

**Example.** PAM4는 NRZ 대비 동일 Baud rate에서 2배 전송하지만 SNR 마진이 줄어 FEC가 필수입니다.

**See also.** [Module 05 — 세대 비교 & DV 관점](../05_generations_dv/)

### PBR (Port-Based Routing)

**Definition.** CXL 스위치의 multi-hop 통과를 위한 라우팅 메커니즘으로, CXL 3.1 패브릭 확장의 기반이다.

**Source.** CXL 3.1 Specification, §9; HDG `CXL Overview` §2.4, §3.1.

**Related.** PBR TLP Header(PTH), Multi-Level Switch, G-FAM.

**Example.** CXL 3.1에서 여러 단계 스위치를 캐스케이딩해 패킷을 멀티홉으로 라우팅합니다.

**See also.** [Module 04](../04_arbmux_fabric/)

### Poison

**Definition.** 데이터 오류 감지 시 해당 캐시라인에 부착되어 소비자가 읽을 때 에러를 보고하게 하는 CXL RAS 태그.

**Source.** CXL 3.1 Specification, §12; HDG `CXL Overview` §8.

**Related.** Viral, AER, RAS, Error Reporting.

**Example.** Poison은 데이터 경로를 따라 전파되어 최초 오류 지점부터 최종 소비자까지 추적 가능합니다.

**See also.** [Module 04 — ARB/MUX & 패브릭](../04_arbmux_fabric/)

---

## V — vLSM / Viral

### vLSM (Virtual Link State Machine)

**Definition.** 하나의 물리 링크 위에서 각 프로토콜이 독립된 링크 상태(Active/L1/L2/Retrain/L0p)를 갖는 것처럼 가상화하는 ARB/MUX의 상태 기계.

**Source.** CXL 3.1 Specification, §5; HDG `CXL Overview` §5.2.

**Related.** ARB/MUX, ALMP, L0p, 전력 상태.

**Example.** .io는 L1(절전), .cachemem은 Active처럼 프로토콜별로 독립 상태를 가지며 ALMP로 양단을 동기화합니다.

**See also.** [Module 04 — ARB/MUX & 패브릭](../04_arbmux_fabric/)

### Viral

**Definition.** Poison 전파가 통제 불가능할 때 링크를 정지시켜 오염 확산을 차단하는 CXL RAS의 최후 방어 메커니즘.

**Source.** CXL 3.1 Specification, §12; HDG `CXL Overview` §8.

**Related.** Poison, RAS, Error Reporting.

**Example.** Poison이 시스템 전체로 확산될 위험이 있을 때 링크를 viral 상태로 전환해 정상 컴포넌트를 보호합니다.

**See also.** [Module 04](../04_arbmux_fabric/)

---

## 추가 약어

| 약어 | 풀네임 | 한 줄 의미 |
|------|--------|-----------|
| **D2H / H2D** | Device-to-Host / Host-to-Device | CXL.cache의 두 방향 채널 |
| **M2S / S2M** | Master-to-Subordinate / Subordinate-to-Master | CXL.mem의 두 방향 채널 |
| **NDR / DRS** | No-Data Response / Data Response | S2M 응답 종류 (데이터 없음/있음) |
| **G-FAM** | Global-Fabric-Attached Memory | 패브릭 전역 거대 메모리 풀 (CXL 3.1) |
| **L0p** | — | Active 내 부분 폭 축소 (CXL 3.0+ 동적 폭 조절) |
| **FEC** | Forward Error Correction | 재전송 없이 수신 측 자체 오류 정정 (PAM4 필수) |
| **IDE** | Integrity & Data Encryption | AES-GCM 256 암호화 + MAC 무결성 |
| **FM** | Fabric Manager | DCD 메모리 할당/회수 중개자 |
