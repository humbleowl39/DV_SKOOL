---
title: "Ethernet DCMAC 용어집"
---

핵심 용어 ISO 11179 형식 정의.

---

## D — DCMAC

### DCMAC

**Definition.** AMD/Xilinx의 100/200/400GbE 하드 IP MAC으로, FPGA/ASIC에 통합되어 라인 레이트 Ethernet 프레임 처리를 제공.

**Source.** AMD/Xilinx DCMAC IP product brief.

**Related.** PCS, FEC, Segmented interface, AXI-Stream.

**Example.** 단일 DCMAC 인스턴스가 4×100G 채널을 독립적으로 처리하면서 채널별로 RS-FEC on/off를 설정할 수 있다.

**See also.** [Module 02](../02_dcmac_architecture/)

---

## F — FCS / FEC

### FCS (Frame Check Sequence)

**Definition.** Ethernet 프레임 끝의 4-byte CRC-32로, 전송 중 비트 에러를 검출.

**Source.** IEEE 802.3.

**Related.** CRC-32, error detection.

**Example.** 수신측 MAC이 재계산한 CRC와 프레임의 FCS 필드가 다르면 해당 프레임을 drop하고 FCS error 카운터를 증가시킨다.

**See also.** [Module 01](../01_ethernet_fundamentals/)

### FEC (Forward Error Correction)

**Definition.** 추가 패리티 비트로 수신단에서 비트 에러를 자동 복원하는 코드. RS-FEC가 100/400GbE 표준.

**Source.** IEEE 802.3 (Reed-Solomon FEC).

**Related.** RS(528,514), KR-FEC, BER.

**Example.** RS(528,514)는 codeword당 최대 7 symbol error를 자동 복원한다. 8 symbol 이상 오류는 detect 후 프레임 drop 처리된다.

**See also.** [Module 02](../02_dcmac_architecture/)

---

## M — MAC / MII

### MAC (Media Access Control)

**Definition.** OSI L2의 sub-layer로, frame 생성/파싱/CRC를 담당.

**Source.** IEEE 802.3.

**Related.** PHY, frame, FCS.

**Example.** TX 방향으로는 payload에 DA/SA/Type 헤더와 FCS를 붙여 프레임을 완성하고, RX 방향으로는 FCS를 검증한 후 헤더를 제거해 payload를 상위 계층에 전달한다.

**See also.** [Module 01](../01_ethernet_fundamentals/)

### MII / GMII / XGMII / CGMII

**Definition.** MAC와 PHY 사이의 표준 인터페이스. MII (10/100), GMII (1G), XGMII (10G), CGMII (100G).

**Source.** IEEE 802.3.

**Related.** MAC, PHY, PCS.

**Example.** XGMII는 32-bit 데이터 버스 + 4-bit 제어 버스로 구성되며 DDR 클럭을 사용해 10GbE를 처리한다.

**See also.** [Module 01](../01_ethernet_fundamentals/)

---

## P — PCS / PHY / PFC

### PCS (Physical Coding Sublayer)

**Definition.** PHY 내부의 인코딩/디코딩, scrambling, alignment 담당 layer.

**Source.** IEEE 802.3.

**Related.** 64b/66b, RS-FEC, lane alignment.

**Example.** 100GbE PCS는 64b/66b 인코딩 후 4개 lane에 round-robin 분배하고, RX에서 alignment marker로 lane skew를 보정해 원래 순서로 재조립한다.

**See also.** [Module 02](../02_dcmac_architecture/)

### PHY

**Definition.** Physical layer — 실제 전기 신호 송수신 + PCS + FEC 통합.

**Source.** IEEE 802.3.

**Related.** PCS, FEC, SerDes, transceiver.

**See also.** [Module 01](../01_ethernet_fundamentals/)

### PFC (Priority Flow Control)

**Definition.** 802.1Qbb 표준의 우선순위별 흐름 제어로, 8개 priority 클래스마다 독립적인 pause 가능.

**Source.** IEEE 802.1Qbb.

**Related.** Pause frame, QoS, RoCE.

**Example.** RoCE 환경에서는 priority 3을 lossless로 지정해 PFC로만 pause하고, 나머지 best-effort 트래픽(priority 0)은 PFC 영향 없이 계속 흐르게 구성한다.

**See also.** [Module 01](../01_ethernet_fundamentals/)

---

## R — RS-FEC

### RS-FEC

**Definition.** Reed-Solomon FEC, 100/400GbE의 표준 FEC. RS(528,514)는 514 데이터 심볼 + 14 패리티로 구성.

**Source.** IEEE 802.3 Clause 91.

**Related.** Symbol, codeword, correction limit, FEC.

**Capability.** 최대 7 symbol error 수정.

**Example.** 검증에서는 codeword당 symbol error 수를 0, 7(경계 내), 8(경계 초과), 14(최대 패리티 수)로 parametrize해 각각 정상 수신 / 정상 수신 / drop / drop을 확인한다.

**See also.** [Module 02](../02_dcmac_architecture/)

---

## V — VLAN

### VLAN (Virtual LAN)

**Definition.** 802.1Q 표준의 가상 LAN tag로, 4-byte tag로 frame을 가상 네트워크에 분리.

**Source.** IEEE 802.1Q.

**Related.** PCP (priority), VID, EtherType.

**Example.** VLAN tag 삽입 시 프레임 길이가 4 bytes 증가하므로, 1518 byte 한도를 검증할 때 VLAN tagged 프레임의 최대는 1522 bytes임을 고려해야 한다.

**See also.** [Module 01](../01_ethernet_fundamentals/)

---

## 추가 약어

| 약어 | 풀네임 | 의미 |
|------|--------|------|
| **GbE** | Gigabit Ethernet | 1Gbps |
| **IFG** | Inter-Frame Gap | frame 사이 최소 idle 시간 (12 bytes 이상) |
| **DA / SA** | Destination/Source Address | 6-byte MAC 주소 |
| **SFD** | Start Frame Delimiter | preamble 끝 표시 (1 byte) |
| **PAM4** | 4-level Pulse Amplitude Modulation | 50G/lane 변조 방식 |
| **NRZ** | Non-Return-to-Zero | 25G/lane 이하 변조 |
| **BER** | Bit Error Rate | 전송 에러율 |
| **AN** | Auto-Negotiation | link 협상 |
| **LT** | Link Training | PCS 동기화 + lane align |
